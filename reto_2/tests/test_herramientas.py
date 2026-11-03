"""Regresiones de evaluación y calibración, sin cámara ni ventanas."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np

from reto.config import Config
from tools import calibrar, calibrar_kmeans, evaluar, preparar_videos


class EvaluacionTest(unittest.TestCase):
    def test_rechaza_video_ilegible_y_libera_captura(self):
        captura = Mock()
        captura.isOpened.return_value = False
        with patch.object(evaluar.cv2, "VideoCapture", return_value=captura):
            with self.assertRaisesRegex(ValueError, "abrir el clip"):
                evaluar.evaluar_clip(Path("roto.mp4"), Config())
        captura.release.assert_called_once()

    def test_rechaza_video_sin_frames(self):
        captura = Mock()
        captura.isOpened.return_value = True
        captura.get.return_value = 20.0
        captura.read.return_value = (False, None)
        with patch.object(evaluar.cv2, "VideoCapture", return_value=captura):
            with self.assertRaisesRegex(ValueError, "frames legibles"):
                evaluar.evaluar_clip(Path("vacio.mp4"), Config())
        captura.release.assert_called_once()

    def test_rechaza_fps_invalidos_para_no_inventar_tiempos(self):
        for fps in (0, -1, float("nan"), float("inf")):
            with self.subTest(fps=fps):
                captura = Mock()
                captura.isOpened.return_value = True
                captura.get.return_value = fps
                with patch.object(evaluar.cv2, "VideoCapture", return_value=captura):
                    with self.assertRaisesRegex(ValueError, "FPS válidos"):
                        evaluar.evaluar_clip(Path("sin_fps.mp4"), Config())
                captura.release.assert_called_once()

    def test_libera_captura_si_falla_pipeline(self):
        captura = Mock()
        captura.isOpened.return_value = True
        captura.get.return_value = 20.0
        captura.read.return_value = (True, np.zeros((4, 4, 3), np.uint8))
        with patch.object(evaluar.cv2, "VideoCapture", return_value=captura), \
                patch.object(evaluar, "procesar_frame", side_effect=ValueError("fallo")):
            with self.assertRaisesRegex(ValueError, "fallo"):
                evaluar.evaluar_clip(Path("clip.mp4"), Config())
        captura.release.assert_called_once()

    def test_resumen_usa_contadores_exactos_y_pondera_frames_con_linea(self):
        filas = [
            {"frames": 3, "_con_linea": 1, "_duracion": 0.15, "_saltos": 1,
             "_cambios_de_giro": 1, "_suma_desviacion": 0.9},
            {"frames": 20, "_con_linea": 2, "_duracion": 1.0, "_saltos": 2,
             "_cambios_de_giro": 0, "_suma_desviacion": 0.3},
        ]
        resumen = evaluar.resumir(filas)
        self.assertEqual(resumen["frames"], 23)
        self.assertEqual(resumen["saltos"], 3)
        self.assertAlmostEqual(resumen["linea_%"], 300 / 23)
        self.assertAlmostEqual(resumen["desviacion_media"], 0.4)
        self.assertAlmostEqual(resumen["zigzag_por_s"], 1 / 1.15)


class CalibracionTest(unittest.TestCase):
    def test_guardar_sin_mover_barras_conserva_ambas_franjas(self):
        config = Config()
        valores = {"bajo": config.hsv_linea[0], "alto": config.hsv_linea[1],
                   "roi": (0.10, 0.50), "apertura": 1, "cierre": 2}
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "config.json"
            calibrar.guardar(config, "linea", valores, ruta)
            cargada = Config.desde_json(ruta)
        self.assertEqual(cargada.roi_linea_cercana, config.roi_linea_cercana)
        self.assertEqual(cargada.roi_linea_lejana, config.roi_linea_lejana)

    def test_cambiar_a_senal_carga_su_roi(self):
        posiciones = {}
        with patch.object(calibrar.cv2, "setTrackbarPos",
                          side_effect=lambda nombre, _ventana, valor: posiciones.update({nombre: valor})):
            calibrar.cargar_modo(Config(), "rojo_alto")
        self.assertEqual(posiciones["ROI arriba %"], 0)
        self.assertEqual(posiciones["ROI abajo %"], 50)
        self.assertEqual(posiciones["H min"], 165)

    def test_roi_no_sale_del_frame_y_hsv_no_se_invierte(self):
        posiciones = {"H min": 170, "H max": 0, "S min": 200, "S max": 100,
                      "V min": 50, "V max": 40, "ROI arriba %": 100,
                      "ROI abajo %": 100, "Apertura": 1, "Cierre": 2}
        with patch.object(calibrar.cv2, "getTrackbarPos",
                          side_effect=lambda nombre, _ventana: posiciones[nombre]), \
                patch.object(calibrar.cv2, "setTrackbarPos"):
            valores = calibrar.leer_trackbars()
        self.assertEqual(valores["roi"], (0.99, 1.0))
        self.assertEqual(valores["bajo"], valores["alto"])

    def test_video_roto_no_produce_bucle_infinito(self):
        captura = Mock()
        captura.read.return_value = (False, None)
        with self.assertRaisesRegex(ValueError, "frames legibles"):
            calibrar.leer_video(captura)
        self.assertEqual(captura.read.call_count, 2)

    def test_carpeta_vacia_tiene_error_explicito(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with self.assertRaisesRegex(ValueError, "No hay imágenes"):
                calibrar.cargar_imagenes(Path(carpeta))

    def test_kmeans_rechaza_franja_salto_y_cantidad_invalidos(self):
        frame = np.zeros((10, 10, 3), np.uint8)
        for franja in ((0.5, 0.5), (-0.1, 0.5), (0, 1.1), (0.001, 0.002)):
            with self.subTest(franja=franja), self.assertRaises(ValueError):
                calibrar_kmeans.juntar_pixeles([frame], franja, 1)
        with self.assertRaises(ValueError):
            calibrar_kmeans.juntar_pixeles([frame], (0, 1), 0)
        with self.assertRaises(ValueError):
            calibrar_kmeans.cargar_frames(Path("video.mp4"), 0)
        with self.assertRaises(ValueError):
            calibrar_kmeans.agrupar(np.zeros((2, 3)), 3)


class PreparacionTest(unittest.TestCase):
    def test_ffmpeg_sin_salida_no_cuenta_archivo_anterior(self):
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "frame.jpg"
            destino.write_bytes(b"original")
            with patch.object(preparar_videos.subprocess, "run"):
                with self.assertRaisesRegex(ValueError, "no produjo"):
                    preparar_videos.ejecutar_salida(["ffmpeg"], destino)
            self.assertEqual(destino.read_bytes(), b"original")

    def test_rechaza_duracion_no_finita(self):
        for duracion in ("nan", "inf", "0", "-3", "N/A"):
            with self.subTest(duracion=duracion), \
                    patch.object(preparar_videos.subprocess, "run", return_value=Mock(stdout=duracion)):
                with self.assertRaises(ValueError):
                    preparar_videos.duracion_segundos(Path("video.mp4"))


if __name__ == "__main__":
    unittest.main()

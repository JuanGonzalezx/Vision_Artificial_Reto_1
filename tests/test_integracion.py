"""Regresiones de captura, reloj y cierre sin cámara física ni red."""

import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

import main
from reto.actuador import ActuadorRegistro
from reto.camara import agregar_credenciales, abrir_camara, describir_fuente, es_fuente_archivo
from reto.config import Config
from reto.overlay import mosaico
from reto.tipos import Accion, Decision, ResultadoSenal


def argumentos(fuente="prueba.mp4"):
    return argparse.Namespace(fuente=fuente, usuario=None, contrasena=None,
                              consola=False, grabar=False, sin_ventana=True, mascaras=False)


def captura_falsa(lecturas):
    captura = Mock()
    captura.read.side_effect = lecturas
    captura.get.return_value = 10.0
    return captura


class PruebasCaptura(unittest.TestCase):
    def test_credenciales_escapadas_y_archivo_intacto(self):
        url = agregar_credenciales("http://[::1]:8080/video", "a/b@c", "p:/?#")
        self.assertEqual(url, "http://a%2Fb%40c:p%3A%2F%3F%23@[::1]:8080/video")
        self.assertEqual(agregar_credenciales("clip.mp4", "admin", "clave"), "clip.mp4")
        self.assertEqual(describir_fuente(url + "?token=privado"), "http://[::1]:8080/video")
        self.assertTrue(es_fuente_archivo("clip.mp4"))
        self.assertFalse(es_fuente_archivo("0"))
        self.assertFalse(es_fuente_archivo("http://localhost/video"))

    @patch("reto.camara.cv2.VideoCapture")
    def test_timeout_se_aplica_al_abrir(self, constructor):
        config = Config()
        abrir_camara("http://localhost/video", config=config)
        constructor.assert_called_once_with("http://localhost/video", cv2.CAP_FFMPEG, [
            cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, config.tiempo_limite_camara_ms,
            cv2.CAP_PROP_READ_TIMEOUT_MSEC, config.tiempo_limite_camara_ms,
        ])

    @patch("reto.camara.cv2.VideoCapture")
    def test_error_libera_y_oculta_credenciales(self, constructor):
        constructor.return_value.isOpened.return_value = False
        with self.assertRaises(RuntimeError) as error:
            abrir_camara("http://admin:secreto@localhost/video?token=privado")
        self.assertNotIn("secreto", str(error.exception))
        self.assertNotIn("privado", str(error.exception))
        constructor.return_value.release.assert_called_once()


class PruebasSesion(unittest.TestCase):
    def setUp(self):
        self.frame = np.full((120, 160, 3), 255, dtype=np.uint8)
        self.actuador = Mock()

    def test_archivo_termina_una_vez_y_usa_reloj_del_video(self):
        captura = captura_falsa([(True, self.frame)] * 3 + [(False, None)])
        with patch.object(main, "abrir_camara", return_value=captura) as abrir, \
                patch.object(main, "crear_actuador", return_value=self.actuador), \
                patch.object(main.cv2, "imshow") as mostrar, \
                patch.object(main, "procesar_frame", wraps=main.procesar_frame) as procesar:
            self.assertEqual(main.ejecutar(argumentos(), Config()), 3)
        abrir.assert_called_once()
        mostrar.assert_not_called()
        self.assertEqual([c.kwargs["ahora"] for c in procesar.call_args_list], [0, .1, .2])
        self.assertEqual(self.actuador.aplicar.call_args.args[0].accion, Accion.PARAR)
        self.assertAlmostEqual(self.actuador.aplicar.call_args.args[1]["tiempo"], .3)
        captura.release.assert_called_once()
        self.actuador.cerrar.assert_called_once()

    def test_pare_dura_segundos_del_video_aunque_procesemos_rapido(self):
        captura = captura_falsa([(True, self.frame)] * 40 + [(False, None)])
        senal = ResultadoSenal(tipo="PARE", area=20000)
        with patch.object(main, "abrir_camara", return_value=captura), \
                patch.object(main, "crear_actuador", return_value=self.actuador), \
                patch("reto.pipeline.modulo_senales.detectar", return_value=senal):
            main.ejecutar(argumentos(), Config())
        registros = [c.args for c in self.actuador.aplicar.call_args_list[:-1]]
        paradas = [contexto["tiempo"] for decision, contexto in registros if decision.accion is Accion.PARAR]
        self.assertAlmostEqual(paradas[0], .2)
        self.assertAlmostEqual(paradas[-1], 3.1)
        self.assertEqual(len(paradas), 30)

    def test_archivo_sin_frames_es_error(self):
        captura = captura_falsa([(False, None)])
        with patch.object(main, "abrir_camara", return_value=captura), \
                patch.object(main, "crear_actuador", return_value=self.actuador):
            with self.assertRaisesRegex(RuntimeError, "no contiene frames"):
                main.ejecutar(argumentos(), Config())
        captura.release.assert_called_once()
        self.actuador.cerrar.assert_called_once()

    def test_camara_cae_parada_inmediata_y_reintentos_limitados(self):
        captura = captura_falsa([(False, None)])
        with patch.object(main, "abrir_camara", side_effect=[captura, RuntimeError(), RuntimeError()]) as abrir, \
                patch.object(main, "crear_actuador", return_value=self.actuador), \
                patch.object(main.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "agotaron"):
                main.ejecutar(argumentos("0"), Config(reintentos_camara=2))
        self.assertEqual(abrir.call_count, 3)
        self.assertEqual(self.actuador.aplicar.call_args_list[0].args[0].accion, Accion.PARAR)
        self.actuador.cerrar.assert_called_once()

    def test_reconexion_exige_frame_y_cierra_capturas_fallidas(self):
        vacia = captura_falsa([(False, None)])
        valida = captura_falsa([(True, self.frame)])
        with patch.object(main, "abrir_camara", side_effect=[vacia, valida]), \
                patch.object(main.time, "sleep"):
            captura, frame = main.reconectar(argumentos("0"), Config(reintentos_camara=2))
        self.assertIs(captura, valida)
        self.assertIs(frame, self.frame)
        vacia.release.assert_called_once()
        valida.release.assert_not_called()

    def test_error_pipeline_libera_y_para(self):
        captura = captura_falsa([(True, self.frame)])
        with patch.object(main, "abrir_camara", return_value=captura), \
                patch.object(main, "crear_actuador", return_value=self.actuador), \
                patch.object(main, "procesar_frame", side_effect=ValueError("error de prueba")):
            with self.assertRaises(ValueError):
                main.ejecutar(argumentos(), Config())
        captura.release.assert_called_once()
        self.actuador.cerrar.assert_called_once()
        self.assertEqual(self.actuador.aplicar.call_args.args[0].accion, Accion.PARAR)

    def test_codec_no_disponible_es_error(self):
        with patch.object(main.cv2, "VideoWriter") as escritor:
            escritor.return_value.isOpened.return_value = False
            with self.assertRaisesRegex(RuntimeError, "crear la grabacion"):
                main.crear_grabador(self.frame, "prueba", 30)
        escritor.return_value.release.assert_called_once()

    def test_csv_respeta_reloj_recibido(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "registro.csv"
            registro = ActuadorRegistro(ruta)
            registro.aplicar(Decision(Accion.RECTO), {"tiempo": 12.5})
            registro.cerrar()
            with ruta.open() as archivo:
                filas = list(csv.DictReader(archivo))
        self.assertEqual(filas[0]["tiempo"], "12.500")

    def test_mosaico_conserva_parte_inferior_del_frame(self):
        self.frame[-10:] = (255, 0, 0)
        vista = mosaico(self.frame, {"linea": np.zeros((20, 160), np.uint8)}, ancho_celda=160)
        self.assertEqual(vista.shape, (120, 320, 3))
        np.testing.assert_array_equal(vista[-1, :160], self.frame[-1])


if __name__ == "__main__":
    unittest.main()

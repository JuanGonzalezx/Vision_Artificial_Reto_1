"""Regresiones del contrato frame -> decisión; sin cámara ni dependencias nuevas.

    uv run python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from reto.config import Config
from reto.control import decidir
from reto.pipeline import preparar, procesar_frame, recortar, suavizar
from reto.senales import detectar, mascaras_de_color
from reto.tipos import Accion, Estado, EstadoRobot, ResultadoLinea, ResultadoSenal


def linea(desviacion: float) -> ResultadoLinea:
    return ResultadoLinea(detectada=True, centro_x=240, desviacion=desviacion, area=5000)


class PruebasConfig(unittest.TestCase):
    def test_rechaza_parametros_invalidos_antes_de_opencv(self):
        casos = {
            "ancho_proceso": (0, -1, 480.5, True),
            "kernel_gauss": (0, 4),
            "kernel_morfologico": (0, -3),
            "iteraciones_apertura": (-1,),
            "suavizado_desviacion": (2.5,),
            "frames_para_buscar": (0,),
            "frames_confirmacion_senal": (0,),
            "roi_linea_cercana": ((0.5, 0.5), (0.8, 0.3), (0, 1.1), (0,), None),
            "hsv_linea": (((0, 0), (179, 255, 255)), ((0, 0, 0), (180, 255, 255)),
                          ((40, 0, 0), (30, 255, 255))),
            "relacion_aspecto_senal": ((2.5, 0.4), (0, 1)),
            "vertices_octagono": ((3.5, 9),),
            "peso_linea_lejana": (-0.1, 1.1),
            "segundos_pare": (-1, float("nan")),
            "ganancia_giro": (float("inf"),),
            "siga_reanuda": ("false", 1),
            "tiempo_limite_camara_ms": (0,),
            "reintentos_camara": (-1,),
            "pausa_reconexion_s": (-1,),
            "fps_respaldo": (0, float("nan")),
        }
        for campo, valores in casos.items():
            for valor in valores:
                with self.subTest(campo=campo, valor=valor), self.assertRaisesRegex(ValueError, campo):
                    Config(**{campo: valor})

    def test_json_conserva_tuplas_y_valores(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "calibracion.json"
            original = Config(iteraciones_apertura=0, roi_senal=(0.1, 0.7))
            original.guardar(ruta)
            self.assertEqual(Config.desde_json(ruta), original)
            self.assertIsInstance(Config.desde_json(ruta).hsv_linea[0], tuple)

    def test_json_rechaza_objeto_incorrecto_y_claves_desconocidas(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "calibracion.json"
            for contenido in ([], {"parametro_inexistente": 1}, {"hsv_linea": 0}):
                ruta.write_text(json.dumps(contenido), encoding="utf8")
                with self.subTest(contenido=contenido), self.assertRaises(ValueError):
                    Config.desde_json(ruta)

    def test_validacion_detecta_cambios_de_calibracion(self):
        config = Config()
        config.roi_senal = (0.9, 0.2)
        with self.assertRaisesRegex(ValueError, "roi_senal"):
            config.validar()


class PruebasControl(unittest.TestCase):
    def test_perdida_breve_conserva_la_orden_completa(self):
        config = Config()
        for desviacion in (-0.9, -0.4, 0.05, 0.5, 0.9):
            with self.subTest(desviacion=desviacion):
                estado = Estado()
                anterior = decidir(estado, linea(desviacion), ResultadoSenal(), config, 0)
                for _ in range(config.frames_para_buscar - 1):
                    actual = decidir(estado, ResultadoLinea(), ResultadoSenal(), config, 0)
                    self.assertEqual((actual.accion, actual.giro), (anterior.accion, anterior.giro))
                actual = decidir(estado, ResultadoLinea(), ResultadoSenal(), config, 0)
                self.assertIs(actual.accion, Accion.BUSCAR)
                self.assertEqual(actual.giro, -1.0 if desviacion < 0 else 1.0)

    def test_recuperacion_reinicia_contador_de_perdida(self):
        config = Config()
        estado = Estado()
        for _ in range(config.frames_para_buscar):
            decidir(estado, ResultadoLinea(), ResultadoSenal(), config, 0)
        decidir(estado, linea(-0.3), ResultadoSenal(), config, 0)
        self.assertEqual(estado.frames_sin_linea, 0)
        self.assertIs(estado.estado, EstadoRobot.SIGUIENDO)

    def test_confirmacion_necesita_frames_consecutivos(self):
        config = Config()
        estado = Estado()
        pare = ResultadoSenal(tipo="PARE", area=5000)
        for senal in (pare, pare, ResultadoSenal(), pare, pare):
            decision = decidir(estado, linea(0), senal, config, 0)
            self.assertIsNot(decision.accion, Accion.PARAR)
        decision = decidir(estado, linea(0), pare, config, 0)
        self.assertIs(decision.accion, Accion.PARAR)

    def test_pare_tiene_prioridad_sobre_busqueda_y_siga_es_configurable(self):
        for reanuda in (True, False):
            with self.subTest(reanuda=reanuda):
                config = Config(siga_reanuda=reanuda, frames_confirmacion_senal=1)
                estado = Estado(estado=EstadoRobot.BUSCANDO, frames_sin_linea=20)
                pare = ResultadoSenal(tipo="PARE", area=5000)
                decision = decidir(estado, ResultadoLinea(), pare, config, 10)
                self.assertIs(decision.accion, Accion.PARAR)
                siga = ResultadoSenal(tipo="SIGA", area=5000)
                decision = decidir(estado, linea(0), siga, config, 11)
                self.assertIs(decision.accion, Accion.RECTO if reanuda else Accion.PARAR)
                decision = decidir(estado, linea(0), ResultadoSenal(), config, 13)
                self.assertIs(decision.accion, Accion.RECTO)

    def test_giro_cero_tiene_accion_recto_incluso_sin_zona_muerta(self):
        decision = decidir(Estado(), linea(0), ResultadoSenal(), Config(zona_muerta=0), 0)
        self.assertEqual((decision.accion, decision.giro), (Accion.RECTO, 0))


class PruebasVision(unittest.TestCase):
    def test_morfologia_de_senales_respeta_la_calibracion(self):
        roi = np.zeros((20, 20, 3), np.uint8)
        roi[10, 10] = (0, 0, 255)
        sin_limpieza = Config(iteraciones_apertura=0, iteraciones_cierre=0)
        self.assertEqual(np.count_nonzero(mascaras_de_color(roi, sin_limpieza)["PARE"]), 1)
        self.assertEqual(np.count_nonzero(mascaras_de_color(roi, Config())["PARE"]), 0)

    def test_octagonos_rojo_y_verde_se_detectan_en_modo_estricto(self):
        puntos = np.array(((60, 20), (120, 20), (160, 60), (160, 120),
                           (120, 160), (60, 160), (20, 120), (20, 60)), np.int32)
        for tipo, tono in (("PARE", 175), ("SIGA", 70)):
            with self.subTest(tipo=tipo):
                hsv = np.uint8([[[tono, 200, 200]]])
                color = tuple(int(c) for c in cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)[0, 0])
                roi = np.zeros((180, 180, 3), np.uint8)
                cv2.fillPoly(roi, [puntos], color)
                resultado = detectar(roi, Config(exigir_octagono=True))
                self.assertEqual(resultado.tipo, tipo)
                self.assertTrue(resultado.es_octagono)

    def test_frame_de_linea_centrada_produce_recto(self):
        frame = np.full((360, 480, 3), 240, np.uint8)
        frame[:, 230:251] = 40
        decision, depuracion = procesar_frame(frame, Estado(), Config(), ahora=0)
        self.assertTrue(depuracion["linea"].detectada)
        self.assertIsNone(depuracion["senal"].tipo)
        self.assertIs(decision.accion, Accion.RECTO)

    def test_frames_y_recortes_vacios_fallan_con_mensaje_claro(self):
        for frame in (None, np.zeros((0, 480, 3), np.uint8), np.zeros((30, 40), np.uint8)):
            with self.subTest(frame=None if frame is None else frame.shape), self.assertRaises(ValueError):
                preparar(frame, Config())
        with self.assertRaisesRegex(ValueError, "ROI"):
            recortar(np.zeros((1, 480, 3), np.uint8), (0.4, 0.58))

    def test_suavizado_no_arrastra_datos_anteriores_a_la_perdida(self):
        estado = Estado()
        config = Config()
        suavizar(linea(-0.6), estado, config)
        suavizar(linea(-0.6), estado, config)
        suavizar(ResultadoLinea(), estado, config)
        self.assertEqual(suavizar(linea(0.6), estado, config).desviacion, 0.6)


if __name__ == "__main__":
    unittest.main()

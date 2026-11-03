"""Clasificador CNN de señales: inferencia con doble y dispatch en el pipeline.

No necesita TensorFlow ni un modelo entrenado: se reemplaza `clasificar` por un
doble para probar la lógica de selección y el enganche con el pipeline.

    uv run python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

import cv2
import numpy as np

from reto import clasificador
from reto.config import Config
from reto.pipeline import detectar_senal, procesar_frame
from reto.senales import proponer_candidatos
from reto.tipos import Estado, ResultadoSenal


def roi_con_blob(color=(0, 0, 255), alto=200, ancho=300, lado=80, x=40, y=20):
    """ROI con un rectángulo de color fuerte, que el color propone como candidato."""
    roi = np.zeros((alto, ancho, 3), np.uint8)
    cv2.rectangle(roi, (x, y), (x + lado, y + lado), color, -1)
    return roi


class PruebasDeteccionCNN(unittest.TestCase):
    def test_clasifica_el_candidato_y_devuelve_su_confianza(self):
        with patch.object(clasificador, "clasificar", return_value=("ZONA_ESCOLAR", 0.9)):
            senal = clasificador.detectar(roi_con_blob(), Config())

        self.assertEqual(senal.tipo, "ZONA_ESCOLAR")
        self.assertAlmostEqual(senal.confianza, 0.9)
        self.assertGreater(senal.area, 0)
        self.assertIsNotNone(senal.centro)

    def test_descarta_por_debajo_de_la_confianza_minima(self):
        with patch.object(clasificador, "clasificar", return_value=("PARE", 0.3)):
            senal = clasificador.detectar(roi_con_blob(), Config(confianza_minima_senal=0.6))

        self.assertIsNone(senal.tipo)
        self.assertEqual(senal.confianza, 0.0)

    def test_sin_candidatos_no_llama_al_modelo(self):
        with patch.object(clasificador, "clasificar") as clasificar:
            senal = clasificador.detectar(np.zeros((100, 100, 3), np.uint8), Config())

        clasificar.assert_not_called()
        self.assertIsNone(senal.tipo)

    def test_elige_el_candidato_de_mayor_confianza(self):
        candidatos = [
            {"caja": (10, 10, 40, 40), "area": 1600.0, "centro": (30, 30), "contorno": None},
            {"caja": (100, 100, 60, 60), "area": 3600.0, "centro": (130, 130), "contorno": None},
        ]
        with patch.object(clasificador, "proponer_candidatos",
                          return_value=(candidatos, np.zeros((10, 10), np.uint8))), \
                patch.object(clasificador, "clasificar",
                             side_effect=[("PARE", 0.5), ("SIGA", 0.8)]):
            senal = clasificador.detectar(np.zeros((200, 200, 3), np.uint8), Config())

        self.assertEqual(senal.tipo, "SIGA")
        self.assertAlmostEqual(senal.confianza, 0.8)


class PruebasCandidatos(unittest.TestCase):
    def test_encuentra_el_anillo_rojo_delgado_de_velocidad_60(self):
        # El desenfoque adelgaza el anillo; la máscara lo reconecta y no lo descarta.
        roi = np.zeros((200, 200, 3), np.uint8)
        cv2.circle(roi, (100, 100), 60, (0, 0, 255), 8)

        candidatos, _ = proponer_candidatos(roi, Config())

        self.assertTrue(candidatos)
        self.assertGreater(candidatos[0]["caja"][2], 100)  # cubre el anillo, no un trazo

    def test_ignora_el_azul_del_chasis(self):
        roi = np.full((200, 200, 3), 230, np.uint8)
        cv2.rectangle(roi, (40, 40), (160, 160), (255, 0, 0), -1)  # azul, en BGR

        candidatos, _ = proponer_candidatos(roi, Config())

        self.assertEqual(candidatos, [])


class PruebasDispatch(unittest.TestCase):
    def test_usa_la_cnn_cuando_el_modelo_existe(self):
        esperado = ResultadoSenal(tipo="PARE", confianza=0.95)
        with patch.object(clasificador, "modelo_disponible", return_value=True), \
                patch.object(clasificador, "detectar", return_value=esperado) as cnn:
            senal = detectar_senal(roi_con_blob(), Config())

        cnn.assert_called_once()
        self.assertEqual(senal.tipo, "PARE")

    def test_sin_modelo_cae_al_detector_por_color(self):
        with patch.object(clasificador, "modelo_disponible", return_value=False), \
                patch.object(clasificador, "detectar") as cnn:
            senal = detectar_senal(roi_con_blob(color=(0, 0, 255)), Config(area_minima_senal=1000))

        cnn.assert_not_called()
        self.assertEqual(senal.tipo, "PARE")  # el rojo lo reconoce el detector de color

    def test_modo_color_no_toca_la_cnn(self):
        with patch.object(clasificador, "modelo_disponible") as disponible:
            detectar_senal(roi_con_blob(), Config(detector_senales="color", area_minima_senal=1000))

        disponible.assert_not_called()


class PruebasPipelineCNN(unittest.TestCase):
    def test_el_pipeline_detecta_la_senal_con_la_cnn(self):
        frame = np.full((360, 480, 3), 240, np.uint8)
        frame[:, 230:251] = 40                                    # línea oscura
        cv2.rectangle(frame, (200, 60), (280, 140), (0, 0, 255), -1)  # señal de color

        config = Config(rotacion=0)
        with patch.object(clasificador, "modelo_disponible", return_value=True), \
                patch.object(clasificador, "clasificar", return_value=("VELOCIDAD_60", 0.9)):
            _, depuracion = procesar_frame(frame, Estado(), config, ahora=0)

        self.assertEqual(depuracion["senal"].tipo, "VELOCIDAD_60")
        self.assertAlmostEqual(depuracion["senal"].confianza, 0.9)


class PruebasConfigClasificador(unittest.TestCase):
    def test_rechaza_parametros_invalidos(self):
        casos = (
            {"detector_senales": "yolo"},
            {"clase_modelo_senales": "YOLOv8"},
            {"confianza_minima_senal": 1.5},
            {"margen_candidato_senal": -0.1},
            {"max_candidatos_senal": 0},
            {"area_minima_candidato_senal": -1},
            {"tamano_entrada_senales": (0, 224)},
            {"clases_senales": ()},
            {"hsv_amarillo": ((35, 90, 90), (18, 255, 255))},
        )
        for caso in casos:
            with self.subTest(caso=caso), self.assertRaises(ValueError):
                Config(**caso)

    def test_las_clases_como_lista_se_convierten_en_tupla(self):
        config = Config(clases_senales=["PARE", "SIGA", "VELOCIDAD_60", "ZONA_ESCOLAR"])
        self.assertIsInstance(config.clases_senales, tuple)


if __name__ == "__main__":
    unittest.main()

"""La señal va sobre una barra negra: mientras tapa la franja, se mantiene el rumbo.

    uv run python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

import cv2
import numpy as np

from reto.config import Config
from reto.pipeline import procesar_frame, senal_sobre_franja
from reto.tipos import Estado, ResultadoSenal

ALTO, ANCHO = 480, 480


def cuadro(y: int, lado: int = 60) -> np.ndarray:
    """Contorno cuadrado de una señal con su borde superior en la fila y."""
    return np.array([[[200, y]], [[200 + lado, y]], [[200 + lado, y + lado]], [[200, y + lado]]],
                    dtype=np.int32)


def escena(con_senal: bool) -> np.ndarray:
    """Piso claro, línea negra vertical y, si se pide, una señal verde sobre una
    barra negra horizontal justo en la franja de la línea."""
    imagen = np.full((ALTO, ANCHO, 3), 210, np.uint8)
    cv2.rectangle(imagen, (230, 0), (260, ALTO), (30, 30, 30), -1)  # línea
    if con_senal:
        cv2.rectangle(imagen, (40, 185), (470, 210), (30, 30, 30), -1)  # barra negra
        cv2.rectangle(imagen, (300, 160), (380, 235), (60, 150, 40), -1)  # señal verde (H≈65)
    return imagen


class PruebasSenalSobreFranja(unittest.TestCase):
    def setUp(self):
        self.config = Config()  # franja cercana: 0.30-0.50 del alto -> filas 144-240

    def test_sin_senal_no_tapa(self):
        self.assertFalse(senal_sobre_franja(ResultadoSenal(), 0, ALTO, self.config))

    def test_senal_lejos_arriba_no_tapa(self):
        senal = ResultadoSenal(tipo="SIGA", area=3600, contorno=cuadro(20))
        self.assertFalse(senal_sobre_franja(senal, 0, ALTO, self.config))

    def test_senal_dentro_de_la_franja_tapa(self):
        senal = ResultadoSenal(tipo="PARE", area=3600, contorno=cuadro(150))
        self.assertTrue(senal_sobre_franja(senal, 0, ALTO, self.config))


class PruebasCongelarRumbo(unittest.TestCase):
    def test_la_barra_de_la_senal_no_mueve_el_rumbo(self):
        """Sin congelar, la barra negra desplaza el centroide; congelando, no."""
        resultados = {}

        for congelar in (False, True):
            config = Config(rotacion=0)  # la escena ya está de frente
            config.congelar_con_senal = congelar
            config.area_minima_senal = 1000
            estado = Estado()

            for t in range(5):  # rumbo limpio: la línea centrada
                procesar_frame(escena(False), estado, config, ahora=t / 30)

            _, depuracion = procesar_frame(escena(True), estado, config, ahora=0.2)
            resultados[congelar] = depuracion

        self.assertEqual(resultados[True]["senal"].tipo, "SIGA")
        self.assertTrue(resultados[True]["linea_congelada"])
        self.assertFalse(resultados[False]["linea_congelada"])
        desvio_sin = abs(resultados[False]["linea"].desviacion)
        desvio_con = abs(resultados[True]["linea"].desviacion)
        self.assertLess(desvio_con, desvio_sin)


if __name__ == "__main__":
    unittest.main()

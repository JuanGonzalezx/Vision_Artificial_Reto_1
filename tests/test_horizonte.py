"""Horizonte: el camino encadenado de cerca a lejos (linea.mirar_adelante).

    uv run python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

import cv2
import numpy as np

from reto.config import Config
from reto.linea import Horizonte, mirar_adelante
from reto.pipeline import anticipar
from reto.tipos import ResultadoLinea

ALTO, ANCHO = 480, 480
OSCURO = (30, 30, 30)


def piso() -> np.ndarray:
    return np.full((ALTO, ANCHO, 3), 210, np.uint8)


def con_linea(desde: tuple[int, int], hasta: tuple[int, int], grosor: int = 30) -> np.ndarray:
    """Piso claro con una línea oscura recta entre dos puntos."""
    imagen = piso()
    cv2.line(imagen, desde, hasta, OSCURO, grosor)
    return imagen


class PruebasHorizonte(unittest.TestCase):
    def setUp(self):
        self.config = Config()  # roi_horizonte 0.05-0.58 -> filas 24-278, 8 tramos

    def test_recta_centrada_llega_arriba_y_apunta_al_centro(self):
        h = mirar_adelante(con_linea((240, ALTO), (240, 0)), self.config, 240)
        self.assertEqual(len(h.puntos), self.config.tramos_horizonte)
        self.assertLess(abs(h.desviacion_objetivo), 0.1)
        self.assertEqual(h.sale_por, 0)

    def test_linea_que_se_va_a_la_derecha_anticipa_a_la_derecha(self):
        h = mirar_adelante(con_linea((240, ALTO), (400, 0)), self.config, 240)
        self.assertTrue(h.detectado)
        self.assertGreater(h.curvatura, 0.1)
        self.assertGreater(h.desviacion_objetivo, 0.2)

    def test_espejar_invierte_el_signo(self):
        imagen = con_linea((240, ALTO), (400, 0))
        derecha = mirar_adelante(imagen, self.config, 240)
        izquierda = mirar_adelante(cv2.flip(imagen, 1), self.config, ANCHO - 1 - 240)
        self.assertAlmostEqual(derecha.desviacion_objetivo, -izquierda.desviacion_objetivo, delta=0.02)

    def test_curva_cerrada_que_sale_por_el_borde_izquierdo(self):
        # Si la curva quedara casi horizontal, en un tramo sería tan ancha como
        # la barra de una señal y se descartaría (ancho_maximo_tramo).
        imagen = piso()
        cv2.line(imagen, (240, ALTO), (240, 200), OSCURO, 30)
        cv2.line(imagen, (240, 240), (0, 110), OSCURO, 30)
        h = mirar_adelante(imagen, self.config, 240)
        self.assertEqual(h.sale_por, -1)
        self.assertEqual(h.desviacion_objetivo, -1.0)

    def test_barra_ancha_de_la_senal_no_ancla_la_cadena(self):
        imagen = con_linea((240, ALTO), (240, 0))
        cv2.rectangle(imagen, (40, 245), (470, 275), OSCURO, -1)  # barra en el tramo más bajo
        h = mirar_adelante(imagen, self.config, 240)
        self.assertTrue(h.detectado)
        self.assertTrue(all(abs(x - 240) < 10 for x, _ in h.puntos))

    def test_mancha_lejana_separada_no_entra_en_la_cadena(self):
        imagen = piso()
        cv2.line(imagen, (100, ALTO), (100, 180), OSCURO, 30)  # la línea termina a media altura
        cv2.rectangle(imagen, (380, 30), (420, 120), OSCURO, -1)  # papel oscuro lejos, a la derecha
        h = mirar_adelante(imagen, self.config, 100)
        self.assertTrue(all(x < 200 for x, _ in h.puntos))

    def test_sin_linea_no_hay_horizonte(self):
        h = mirar_adelante(piso(), self.config)
        self.assertFalse(h.detectado)


class PruebasAnticipar(unittest.TestCase):
    def test_mezcla_ponderada(self):
        config = Config()
        config.peso_horizonte = 0.5
        linea = ResultadoLinea(detectada=True, centro_x=240, desviacion=0.2)
        horizonte = Horizonte(puntos=((240, 250), (300, 100)), desviacion_objetivo=0.6)
        self.assertAlmostEqual(anticipar(linea, horizonte, config).desviacion, 0.4)

    def test_peso_cero_o_sin_horizonte_no_cambia_nada(self):
        config = Config()
        linea = ResultadoLinea(detectada=True, centro_x=240, desviacion=0.2)
        self.assertEqual(anticipar(linea, Horizonte(), config).desviacion, 0.2)
        config.peso_horizonte = 0.0
        horizonte = Horizonte(puntos=((240, 250), (300, 100)), desviacion_objetivo=0.6)
        self.assertEqual(anticipar(linea, horizonte, config).desviacion, 0.2)


if __name__ == "__main__":
    unittest.main()

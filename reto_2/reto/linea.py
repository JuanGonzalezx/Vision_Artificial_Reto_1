"""Detección de la línea guía y cálculo de la desviación.

Dueño: Daniel.

Técnicas (todas vistas en clase, ver docs/reto/tecnicas-permitidas.md):
conversión a HSV (clase 1), segmentación por color con inRange (clase 2),
apertura y cierre para limpiar la máscara (clase 3), contorno más grande y
centroide por momentos (clase 3).

Pasos:
  1. Convertir la ROI a HSV.
  2. mascara = cv2.inRange(hsv, *config.hsv_linea)
  3. Apertura para quitar ruido y cierre para tapar huecos de la línea.
  4. Contornos; quedarse con el de mayor área si supera config.area_minima_linea.
  5. Centroide con cv2.moments: cx = M["m10"] / M["m00"].
  6. desviacion = (cx - ancho / 2) / (ancho / 2)   ->  -1 .. +1
"""

from __future__ import annotations

import cv2
import numpy as np

from .config import Config
from .tipos import ResultadoLinea


def segmentar_linea(roi, config: Config):
    """Máscara binaria de los píxeles con el color de la línea.

    Técnicas: HSV (clase 1), inRange (clase 2), apertura y cierre (clase 3).
    """
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    bajo, alto = config.hsv_linea
    mascara = cv2.inRange(hsv, np.array(bajo, np.uint8), np.array(alto, np.uint8))

    lado = config.kernel_morfologico
    kernel = np.ones((lado, lado), np.uint8)
    # Apertura: quita el ruido pequeño. Cierre: tapa los huecos de la textura de la cinta.
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel, iterations=config.iteraciones_apertura)
    return cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel, iterations=config.iteraciones_cierre)


def contorno_principal(mascara, config: Config, centro_previo: int | None = None):
    """Contorno que sigue la línea, o None si no hay uno válido.

    Válido = área >= `area_minima_linea` y no más ancho que `ancho_maximo_linea`
    (una cinta transversal no sirve de guía). Sin `centro_previo` se toma el de mayor área; con él,
    el más cercano a donde estaba la línea, para no saltar de un trozo a otro
    cuando algo la parte en dos.

    Técnicas: findContours, contourArea, boundingRect y momentos (clase 3).
    """
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ancho_mascara = mascara.shape[1]

    validos = [
        c for c in contornos
        if cv2.contourArea(c) >= config.area_minima_linea
        and cv2.boundingRect(c)[2] / ancho_mascara <= config.ancho_maximo_linea
    ]

    if not validos:
        return None

    if centro_previo is None:
        return max(validos, key=cv2.contourArea)

    def distancia_al_previo(contorno) -> float:
        centro = centro_horizontal(contorno)
        return float("inf") if centro is None else abs(centro - centro_previo)

    return min(validos, key=distancia_al_previo)


def centro_horizontal(contorno) -> int | None:
    """Coordenada x del centroide del contorno.

    Técnica: momentos de imagen, cx = m10 / m00 (clase 3).
    """
    momentos = cv2.moments(contorno)

    if momentos["m00"] == 0:
        return None

    return int(momentos["m10"] / momentos["m00"])


def detectar(roi, config: Config, centro_previo: int | None = None) -> ResultadoLinea:
    """Devuelve dónde está la línea dentro de la ROI recibida.

    Args:
        roi: recorte del frame (BGR) donde se busca la línea.
        config: parámetros de segmentación.
        centro_previo: x de la línea en el frame anterior (memoria contra saltos).
    """
    mascara = segmentar_linea(roi, config)
    contorno = contorno_principal(mascara, config, centro_previo)

    if contorno is None:
        return ResultadoLinea(mascara=mascara)

    centro_x = centro_horizontal(contorno)

    if centro_x is None:
        return ResultadoLinea(mascara=mascara)

    return ResultadoLinea(
        detectada=True,
        centro_x=centro_x,
        desviacion=desviacion_desde_centro(centro_x, roi.shape[1]),
        area=float(cv2.contourArea(contorno)),
        mascara=mascara,
    )


def desviacion_desde_centro(centro_x: int, ancho: int) -> float:
    """Normaliza la posición de la línea a -1 (izquierda) .. +1 (derecha)."""
    mitad = ancho / 2
    return (centro_x - mitad) / mitad


"""Detección de la línea guía y cálculo de la desviación.

Dueño: Juan David.

Técnicas, todas vistas en clase (ver docs/reto/tecnicas-permitidas.md):
conversión a HSV (clase 1), segmentación por color con inRange (clase 2),
apertura y cierre para limpiar la máscara (clase 3), contornos y centroide
por momentos (clase 3).

La idea en una línea: dentro de la franja que miramos, la línea es lo más
oscuro; se saca su máscara, se limpia, se toma el borrón más grande y su
centro nos dice hacia dónde corregir.
"""

from __future__ import annotations

import cv2
import numpy as np

from .config import Config
from .tipos import ResultadoLinea


def construir_mascara(roi, config: Config):
    """Devuelve la máscara binaria de la línea dentro de la ROI.

    La línea es negra sobre piso claro, así que lo que la separa es el
    brillo (V bajo) y la poca saturación, no el tono. Por eso el rango de H
    va completo: un gris oscuro no tiene tono estable.
    """
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mascara = cv2.inRange(hsv, np.array(config.hsv_linea[0]), np.array(config.hsv_linea[1]))

    kernel = np.ones((config.kernel_morfologico, config.kernel_morfologico), np.uint8)

    # Apertura: borra las motas sueltas (sombras pequeñas, suciedad del piso).
    if config.iteraciones_apertura:
        mascara = cv2.morphologyEx(
            mascara, cv2.MORPH_OPEN, kernel, iterations=config.iteraciones_apertura
        )

    # Cierre: tapa los huecos y vuelve a unir la línea si quedó partida.
    if config.iteraciones_cierre:
        mascara = cv2.morphologyEx(
            mascara, cv2.MORPH_CLOSE, kernel, iterations=config.iteraciones_cierre
        )

    return mascara


def contorno_de_la_linea(mascara, area_minima: int):
    """El contorno más grande de la máscara, si es lo bastante grande.

    Nos quedamos con el mayor porque la línea es el objeto oscuro grande de
    la franja; lo demás son sombras y ruido. El área mínima evita que, si la
    línea no está, cualquier manchita pase por línea.
    """
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contornos:
        return None

    mayor = max(contornos, key=cv2.contourArea)

    if cv2.contourArea(mayor) < area_minima:
        return None

    return mayor


def centro_del_contorno(contorno) -> int | None:
    """Centroide en x, con momentos (clase 3): cx = m10 / m00."""
    momentos = cv2.moments(contorno)

    if momentos["m00"] == 0:
        return None

    return int(momentos["m10"] / momentos["m00"])


def desviacion_desde_centro(centro_x: int, ancho: int) -> float:
    """Normaliza la posición de la línea a -1 (izquierda) .. +1 (derecha).

    Se normaliza para que el control no dependa de la resolución: con la
    webcam o con el celular, "media imagen a la derecha" vale siempre +0.5.
    """
    mitad = ancho / 2
    return (centro_x - mitad) / mitad


def detectar(roi, config: Config) -> ResultadoLinea:
    """Devuelve dónde está la línea dentro de la ROI recibida.

    Args:
        roi: recorte del frame (BGR) donde se busca la línea.
        config: parámetros de segmentación.
    """
    mascara = construir_mascara(roi, config)
    contorno = contorno_de_la_linea(mascara, config.area_minima_linea)

    if contorno is None:
        return ResultadoLinea(detectada=False, mascara=mascara)

    centro_x = centro_del_contorno(contorno)

    if centro_x is None:
        return ResultadoLinea(detectada=False, mascara=mascara)

    return ResultadoLinea(
        detectada=True,
        centro_x=centro_x,
        desviacion=desviacion_desde_centro(centro_x, roi.shape[1]),
        area=float(cv2.contourArea(contorno)),
        mascara=mascara,
    )

"""Detección de la línea guía y cálculo de la desviación.

Dueño: Daniel.

Técnicas previstas (todas vistas en clase, ver docs/reto/tecnicas-permitidas.md):
conversión a HSV (clase 1), segmentación por color con inRange (clase 2),
apertura y cierre para limpiar la máscara (clase 3), contorno más grande y
centroide por momentos (clase 3).

Plan:
  1. Convertir la ROI a HSV.
  2. mascara = cv2.inRange(hsv, *config.hsv_linea)
  3. Apertura para quitar ruido y cierre para tapar huecos de la línea.
  4. Contornos; quedarse con el de mayor área si supera config.area_minima_linea.
  5. Centroide con cv2.moments: cx = M["m10"] / M["m00"].
  6. desviacion = (cx - ancho / 2) / (ancho / 2)   ->  -1 .. +1

Mientras no esté implementado devuelve "no detectada", para que el resto del
programa se pueda correr y probar.
"""

from __future__ import annotations

from .config import Config
from .tipos import ResultadoLinea


def detectar(roi, config: Config) -> ResultadoLinea:
    """Devuelve dónde está la línea dentro de la ROI recibida.

    Args:
        roi: recorte del frame (BGR) donde se busca la línea.
        config: parámetros de segmentación.
    """
    # TODO(daniel): implementar los pasos del docstring.
    return ResultadoLinea()


def desviacion_desde_centro(centro_x: int, ancho: int) -> float:
    """Normaliza la posición de la línea a -1 (izquierda) .. +1 (derecha)."""
    mitad = ancho / 2
    return (centro_x - mitad) / mitad

"""Pruebas de la detección de línea con imágenes sintéticas (sin cámara ni ventanas).

    uv run python tools/probar_linea.py

Cubre RF-06 (signo de la desviación), RF-07 (línea no detectada) y la imagen
real datos/pruebas/linea2.jpeg si existe.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reto import linea  # noqa: E402
from reto.config import Config  # noqa: E402

ALTO, ANCHO = 128, 480
GROSOR_LINEA = 40
FONDO = (200, 200, 200)   # papel claro
COLOR_LINEA = (40, 40, 40)  # cinta oscura


def imagen_con_linea(centro_x: int | None):
    """Fondo claro con una cinta vertical oscura centrada en `centro_x`."""
    roi = np.full((ALTO, ANCHO, 3), FONDO, np.uint8)

    if centro_x is not None:
        x1, x2 = centro_x - GROSOR_LINEA // 2, centro_x + GROSOR_LINEA // 2
        roi[:, x1:x2] = COLOR_LINEA

    return roi


def verificar(nombre: str, condicion: bool, fallos: list[str]) -> None:
    print(f"  {'OK ' if condicion else 'FALLA'} {nombre}")
    if not condicion:
        fallos.append(nombre)


def main() -> int:
    config = Config()
    fallos: list[str] = []

    izquierda = linea.detectar(imagen_con_linea(ANCHO // 6), config)
    centro = linea.detectar(imagen_con_linea(ANCHO // 2), config)
    derecha = linea.detectar(imagen_con_linea(5 * ANCHO // 6), config)

    verificar("línea a la izquierda: desviación < -0.3", izquierda.detectada and izquierda.desviacion < -0.3, fallos)
    verificar("línea al centro: |desviación| < 0.1", centro.detectada and abs(centro.desviacion) < 0.1, fallos)
    verificar("línea a la derecha: desviación > +0.3", derecha.detectada and derecha.desviacion > 0.3, fallos)

    espejada = linea.detectar(cv2.flip(imagen_con_linea(ANCHO // 6), 1), config)
    verificar("espejar invierte el signo", espejada.detectada and espejada.desviacion > 0.3, fallos)

    vacia = linea.detectar(imagen_con_linea(None), config)
    verificar("ROI en blanco: no detectada, sin excepción", not vacia.detectada, fallos)

    ruido = imagen_con_linea(None)
    ruido[10:14, 10:14] = COLOR_LINEA
    verificar("solo ruido (área < mínima): no detectada", not linea.detectar(ruido, config).detectada, fallos)

    real = Path("datos/pruebas/linea2.jpeg")
    if real.exists():
        resultado = linea.detectar(cv2.imread(str(real)), config)
        print(f"  info linea2.jpeg: detectada={resultado.detectada} desviación={resultado.desviacion:+.2f}")

    print("\nTodo bien." if not fallos else f"\n{len(fallos)} prueba(s) fallaron.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())

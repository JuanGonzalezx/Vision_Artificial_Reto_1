"""HUD y vistas de depuración.

Sirve para calibrar (ver la máscara mientras se mueven los umbrales) y para
el póster: las capturas de esta ventana son las que muestran las etapas.
"""

from __future__ import annotations

import cv2
import numpy as np

from .config import Config
from .tipos import Decision, Estado, ResultadoLinea, ResultadoSenal

VERDE = (0, 255, 0)
AMARILLO = (0, 255, 255)
ROJO = (0, 0, 255)
BLANCO = (255, 255, 255)


def _texto(imagen, texto: str, x: int, y: int, color=VERDE, escala: float = 0.6) -> None:
    cv2.putText(imagen, texto, (x, y), cv2.FONT_HERSHEY_SIMPLEX, escala, color, 2, cv2.LINE_AA)


def franja_a_pixeles(alto: int, franja: tuple[float, float]) -> tuple[int, int]:
    """Convierte una franja en fracciones (0.7, 1.0) a filas del frame."""
    inicio, fin = franja
    return int(alto * inicio), int(alto * fin)


def dibujar(frame, linea: ResultadoLinea, senal: ResultadoSenal, decision: Decision,
            estado: Estado, config: Config, fps: float = 0.0, curvatura: float = 0.0):
    """Devuelve una copia del frame con la información encima."""
    salida = frame.copy()
    alto, ancho = salida.shape[:2]

    # ROI de la línea y ROI de las señales.
    y1, y2 = franja_a_pixeles(alto, config.roi_linea_cercana)
    cv2.rectangle(salida, (0, y1), (ancho - 1, y2 - 1), AMARILLO, 1)
    _texto(salida, "ROI linea", 5, y1 + 18, AMARILLO, 0.5)

    ys1, ys2 = franja_a_pixeles(alto, config.roi_senal)
    cv2.rectangle(salida, (0, ys1), (ancho - 1, ys2 - 1), BLANCO, 1)
    _texto(salida, "ROI senales", 5, ys1 + 18, BLANCO, 0.5)

    # Centro del robot y centro de la línea.
    cv2.line(salida, (ancho // 2, y1), (ancho // 2, y2), BLANCO, 1)

    if linea.detectada and linea.centro_x is not None:
        cv2.line(salida, (linea.centro_x, y1), (linea.centro_x, y2), VERDE, 2)

    # Estado y decisión.
    _texto(salida, f"{estado.estado.value} -> {decision.accion.value}", 10, 25)
    _texto(salida, decision.razon, 10, 48, AMARILLO, 0.55)

    if senal.tipo:
        color = ROJO if senal.tipo == "PARE" else VERDE
        forma = "octagono" if senal.es_octagono else f"{senal.vertices} lados"
        _texto(salida, f"{senal.tipo} ({forma}, area {senal.area:.0f})", 10, 71, color, 0.55)

    if abs(curvatura) > config.umbral_curvatura:
        lado = "derecha" if curvatura > 0 else "izquierda"
        _texto(salida, f"curva a la {lado} ({curvatura:+.2f})", 10, 94, AMARILLO, 0.5)

    _texto(salida, f"giro {decision.giro:+.2f} | FPS {fps:.1f}", 10, alto - 12, AMARILLO, 0.55)

    return salida


def mosaico(frame, mascaras: dict[str, "np.ndarray"], ancho_celda: int = 320):
    """Arma una cuadrícula con el frame y las máscaras, para calibrar.

    Las máscaras de 1 canal se pasan a BGR para poder unirlas (clase 1).
    """
    vistas = [("frame", frame)]
    vistas += [(nombre, m) for nombre, m in mascaras.items() if m is not None]

    celdas = []
    alto_celda = max(1, round(frame.shape[0] * ancho_celda / frame.shape[1]))

    for nombre, imagen in vistas:
        if imagen.ndim == 2:
            imagen = cv2.cvtColor(imagen, cv2.COLOR_GRAY2BGR)

        # Ajustar y rellenar conserva toda la imagen, incluso en ROI muy bajas.
        escala = min(ancho_celda / imagen.shape[1], alto_celda / imagen.shape[0])
        ancho = max(1, round(imagen.shape[1] * escala))
        alto = max(1, round(imagen.shape[0] * escala))
        celda = np.zeros((alto_celda, ancho_celda, 3), dtype=np.uint8)
        x, y = (ancho_celda - ancho) // 2, (alto_celda - alto) // 2
        celda[y:y + alto, x:x + ancho] = cv2.resize(imagen, (ancho, alto))
        _texto(celda, nombre, 8, 22, VERDE, 0.55)
        celdas.append(celda)

    if not celdas:
        return frame

    filas = [np.hstack(celdas[i:i + 2]) for i in range(0, len(celdas), 2)]
    ancho_comun = max(f.shape[1] for f in filas)
    filas = [
        np.hstack([f, np.zeros((f.shape[0], ancho_comun - f.shape[1], 3), np.uint8)])
        if f.shape[1] < ancho_comun else f
        for f in filas
    ]

    return np.vstack(filas)

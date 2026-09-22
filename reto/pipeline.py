"""Orquesta las etapas: de un frame a una decisión.

Dueño: Daniel.

Es el único archivo que conoce el orden completo del algoritmo. Cada etapa
vive en su propio módulo, así que aquí no hay lógica de visión, solo el flujo.
"""

from __future__ import annotations

import cv2

from . import linea as modulo_linea
from . import senales as modulo_senales
from .config import Config
from .control import decidir
from .overlay import franja_a_pixeles
from .tipos import Decision, Estado, ResultadoLinea, ResultadoSenal


def preparar(frame, config: Config):
    """Redimensiona a un ancho fijo y suaviza (clases 1 y 3).

    Procesar en pequeño es lo que mantiene los FPS, y los FPS son los que
    deciden si la corrección llega a tiempo.
    """
    alto, ancho = frame.shape[:2]

    if ancho != config.ancho_proceso:
        nuevo_alto = int(alto * config.ancho_proceso / ancho)
        frame = cv2.resize(frame, (config.ancho_proceso, nuevo_alto))

    kernel = config.kernel_gauss + (1 - config.kernel_gauss % 2)  # siempre impar
    return cv2.GaussianBlur(frame, (kernel, kernel), 0)


def recortar(frame, franja: tuple[float, float]):
    """Devuelve la franja horizontal indicada (ROI, clase 1)."""
    y1, y2 = franja_a_pixeles(frame.shape[0], franja)
    return frame[y1:y2, :], y1


def procesar_frame(frame, estado: Estado, config: Config) -> tuple[Decision, dict]:
    """Ejecuta el algoritmo completo sobre un frame.

    Devuelve la decisión y un diccionario con los resultados intermedios,
    que overlay usa para dibujar y nosotros para calibrar.
    """
    preparado = preparar(frame, config)

    roi_cercana, desplazamiento = recortar(preparado, config.roi_linea_cercana)
    linea: ResultadoLinea = modulo_linea.detectar(roi_cercana, config)

    roi_lejana, _ = recortar(preparado, config.roi_linea_lejana)
    linea_lejana: ResultadoLinea = modulo_linea.detectar(roi_lejana, config)

    roi_senal, _ = recortar(preparado, config.roi_senal)
    senal: ResultadoSenal = modulo_senales.detectar(roi_senal, config)

    linea = combinar_franjas(linea, linea_lejana, config, desplazamiento)
    decision = decidir(estado, linea, senal, config)

    depuracion = {
        "frame": preparado,
        "linea": linea,
        "linea_lejana": linea_lejana,
        "senal": senal,
        "mascaras": {"linea": linea.mascara, "senal": senal.mascara},
    }

    return decision, depuracion


def combinar_franjas(cercana: ResultadoLinea, lejana: ResultadoLinea, config: Config,
                     desplazamiento: int) -> ResultadoLinea:
    """Mezcla la franja cercana (corrige ahora) con la lejana (anticipa la curva).

    Es una de las ideas propias del equipo: ver docs/arquitectura.md, sección 6.
    """
    if not cercana.detectada:
        return cercana

    if not lejana.detectada or config.peso_linea_lejana <= 0:
        return cercana

    peso = config.peso_linea_lejana
    desviacion = (1 - peso) * cercana.desviacion + peso * lejana.desviacion

    return ResultadoLinea(
        detectada=True,
        centro_x=cercana.centro_x,
        desviacion=desviacion,
        area=cercana.area,
        mascara=cercana.mascara,
    )

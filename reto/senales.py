"""Detección de las señales PARE (octágono rojo) y SIGA (octágono verde).

Dueño: Juan David.

Técnicas previstas: HSV (clase 1), inRange con dos rangos para el rojo
(clase 2), morfología para limpiar (clase 3), findContours + approxPolyDP +
boundingRect y circularidad (clase 3).

Plan:
  1. HSV de la ROI.
  2. mascara_roja = inRange(rojo_bajo) | inRange(rojo_alto)   # el rojo está en
     los dos extremos de H
     mascara_verde = inRange(verde)
  3. Apertura + cierre en cada máscara.
  4. Por cada contorno con área >= config.area_minima_senal:
       - aproximar con approxPolyDP (epsilon = precision_poligono * perímetro)
       - octágono: entre 7 y 9 vértices
       - relación de aspecto de boundingRect cercana a 1
       - circularidad 4*pi*area / perimetro**2 por encima del mínimo
  5. Devolver la señal de mayor área (la más cercana).

Ojo: contar vértices no distingue un círculo de un octágono, por eso también
se mira la circularidad (ver docs/clases/clase3.md, sección 7.6).

Mientras no esté implementado devuelve "sin señal".
"""

from __future__ import annotations

import math

from .config import Config
from .tipos import ResultadoSenal


def detectar(roi, config: Config) -> ResultadoSenal:
    """Busca un octágono rojo o verde en la ROI recibida."""
    # TODO(juan): implementar los pasos del docstring.
    return ResultadoSenal()


def circularidad(area: float, perimetro: float) -> float:
    """1.0 en un círculo, ~0.95 en un octágono, 0.785 en un cuadrado."""
    if perimetro <= 0:
        return 0.0
    return 4 * math.pi * area / (perimetro ** 2)


def es_octagono(vertices: int, ancho: int, alto: int, area: float, perimetro: float,
                config: Config) -> bool:
    """Aplica los tres filtros de forma sobre un contorno candidato."""
    minimo, maximo = config.vertices_octagono

    if not minimo <= vertices <= maximo:
        return False

    if alto == 0:
        return False

    relacion = ancho / alto
    minima, maxima = config.relacion_aspecto_octagono

    if not minima <= relacion <= maxima:
        return False

    return circularidad(area, perimetro) >= config.circularidad_minima

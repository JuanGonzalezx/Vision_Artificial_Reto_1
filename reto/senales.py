"""Detección de las señales PARE (octágono rojo) y SIGA (octágono verde).

Dueño: Daniel. Esta es una implementación base para comparar y mejorar.

Técnicas, todas vistas en clase (ver docs/reto/tecnicas-permitidas.md):
HSV (clase 1), inRange con dos rangos para el rojo (clase 2), morfología
para limpiar (clase 3), findContours + approxPolyDP + boundingRect y
circularidad (clase 3).

La detección va en dos capas:

1. **Color, área y posición** deciden si hay una señal. Es lo que manda.
2. **La forma** (octágono) suma confianza, pero no descarta.

Por qué en ese orden: medimos las señales de los videos de ensayo del
profesor y no dan 8 vértices. Están inclinadas y a veces tapadas, así que
`approxPolyDP` devuelve 4 o 5 vértices y la circularidad queda en 0.58-0.72,
lejos del 0.95 de un octágono de frente. Si exigiéramos la forma, no
detectaríamos ninguna de las señales de sus propios videos. Con
`config.exigir_octagono = True` se puede volver estricto cuando la señal se
vea de frente.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

from .config import Config
from .tipos import ResultadoSenal


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


def _limpiar(mascara, config: Config):
    """Apertura para quitar motas y cierre para tapar huecos (clase 3)."""
    kernel = np.ones((config.kernel_morfologico, config.kernel_morfologico), np.uint8)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel, iterations=1)
    return cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel, iterations=2)


def mascaras_de_color(roi, config: Config) -> dict:
    """Una máscara por señal: roja (dos rangos de H) y verde.

    El rojo está partido en los dos extremos del círculo de H, así que se
    unen los dos rangos con un OR (clase 2).
    """
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    roja = cv2.inRange(hsv, np.array(config.hsv_rojo_bajo[0]), np.array(config.hsv_rojo_bajo[1]))
    roja |= cv2.inRange(hsv, np.array(config.hsv_rojo_alto[0]), np.array(config.hsv_rojo_alto[1]))
    verde = cv2.inRange(hsv, np.array(config.hsv_verde[0]), np.array(config.hsv_verde[1]))

    return {"PARE": _limpiar(roja, config), "SIGA": _limpiar(verde, config)}


def candidatos_en_mascara(mascara, tipo: str, config: Config) -> list[dict]:
    """Contornos de la máscara que podrían ser una señal."""
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    encontrados = []

    for contorno in contornos:
        area = cv2.contourArea(contorno)

        if area < config.area_minima_senal:
            continue

        perimetro = cv2.arcLength(contorno, True)
        aproximacion = cv2.approxPolyDP(contorno, config.precision_poligono * perimetro, True)
        x, y, ancho, alto = cv2.boundingRect(aproximacion)

        # Una señal es un bloque compacto de color: si el contorno es una
        # tira larga y delgada, es un reflejo o el borde de algo, no una señal.
        if alto == 0 or not 0.4 <= ancho / alto <= 2.5:
            continue

        encontrados.append({
            "tipo": tipo,
            "area": float(area),
            "centro": (x + ancho // 2, y + alto // 2),
            "vertices": len(aproximacion),
            "contorno": aproximacion,
            "octagono": es_octagono(len(aproximacion), ancho, alto, area, perimetro, config),
        })

    return encontrados


def detectar(roi, config: Config) -> ResultadoSenal:
    """Busca un octágono rojo o verde en la ROI recibida.

    Devuelve la señal de mayor área, que es la más cercana. Si no hay
    ninguna que pase los filtros, devuelve una señal vacía.
    """
    mascaras = mascaras_de_color(roi, config)
    candidatos: list[dict] = []

    for tipo, mascara in mascaras.items():
        candidatos += candidatos_en_mascara(mascara, tipo, config)

    if config.exigir_octagono:
        candidatos = [c for c in candidatos if c["octagono"]]

    mascara_debug = cv2.bitwise_or(mascaras["PARE"], mascaras["SIGA"])

    if not candidatos:
        return ResultadoSenal(mascara=mascara_debug)

    mejor = max(candidatos, key=lambda c: c["area"])

    return ResultadoSenal(
        tipo=mejor["tipo"],
        area=mejor["area"],
        centro=mejor["centro"],
        vertices=mejor["vertices"],
        contorno=mejor["contorno"],
        mascara=mascara_debug,
        es_octagono=mejor["octagono"],
    )

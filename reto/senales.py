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
    """Aplica vértices, relación de aspecto y circularidad (clase 3)."""
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
    if config.iteraciones_apertura:
        mascara = cv2.morphologyEx(
            mascara, cv2.MORPH_OPEN, kernel, iterations=config.iteraciones_apertura
        )
    if config.iteraciones_cierre:
        mascara = cv2.morphologyEx(
            mascara, cv2.MORPH_CLOSE, kernel, iterations=config.iteraciones_cierre
        )
    return mascara


def _mascara_roja(hsv, config: Config):
    """Rojo en los dos extremos del círculo de H, unidos con OR (clase 2)."""
    roja = cv2.inRange(hsv, np.array(config.hsv_rojo_bajo[0]), np.array(config.hsv_rojo_bajo[1]))
    return roja | cv2.inRange(hsv, np.array(config.hsv_rojo_alto[0]), np.array(config.hsv_rojo_alto[1]))


def _mascara_verde(hsv, config: Config):
    """Verde de la señal SIGA (clase 2)."""
    return cv2.inRange(hsv, np.array(config.hsv_verde[0]), np.array(config.hsv_verde[1]))


def mascaras_de_color(roi, config: Config) -> dict:
    """Una máscara por señal: roja (dos rangos de H) y verde."""
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    return {"PARE": _limpiar(_mascara_roja(hsv, config), config),
            "SIGA": _limpiar(_mascara_verde(hsv, config), config)}


def candidatos_en_mascara(mascara, tipo: str, config: Config) -> list[dict]:
    """Contornos, área, polígono y relación de aspecto (clase 3)."""
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
        minima, maxima = config.relacion_aspecto_senal
        if alto == 0 or not minima <= ancho / alto <= maxima:
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


def mascara_senales(roi, config: Config):
    """Máscara con los colores de las señales: rojo, verde y amarillo (clases 1 y 2).

    Sirve para *proponer* dónde hay una señal; la clase concreta la decide la
    CNN (`reto/clasificador.py`). El azul del chasis del robot queda fuera, que
    era lo que enganchaba una máscara de "cualquier color fuerte".

    Se dilata una vez y se cierra, sin abrir: el anillo rojo del VELOCIDAD_60 es
    delgado y el desenfoque de `preparar` lo parte en trazos sueltos cuando la
    señal está lejos. La dilatación lo reconecta; una apertura, en cambio, se lo
    come. El ruido fino igual se descarta por área en `proponer_candidatos`.
    """
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    amarilla = cv2.inRange(hsv, np.array(config.hsv_amarillo[0]), np.array(config.hsv_amarillo[1]))
    unida = _mascara_roja(hsv, config) | _mascara_verde(hsv, config) | amarilla
    kernel = np.ones((config.kernel_morfologico, config.kernel_morfologico), np.uint8)
    unida = cv2.dilate(unida, kernel, iterations=1)
    return cv2.morphologyEx(unida, cv2.MORPH_CLOSE, kernel, iterations=config.iteraciones_cierre)


def proponer_candidatos(roi, config: Config) -> tuple[list[dict], np.ndarray]:
    """Regiones donde podría haber una señal, para que la CNN las clasifique.

    Devuelve las cajas candidatas (las de mayor área primero, que son las más
    cercanas) y la máscara usada, que el mosaico dibuja para calibrar. Filtra
    por área y relación de aspecto, igual que `candidatos_en_mascara`.
    """
    mascara = mascara_senales(roi, config)
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidatos = []

    for contorno in contornos:
        area = cv2.contourArea(contorno)

        if area < config.area_minima_candidato_senal:
            continue

        x, y, ancho, alto = cv2.boundingRect(contorno)

        if alto == 0:
            continue

        minima, maxima = config.relacion_aspecto_senal

        if not minima <= ancho / alto <= maxima:
            continue

        candidatos.append({
            "caja": (x, y, ancho, alto),
            "area": float(area),
            "centro": (x + ancho // 2, y + alto // 2),
            "contorno": contorno,
        })

    candidatos.sort(key=lambda candidato: candidato["area"], reverse=True)
    return candidatos[:config.max_candidatos_senal], mascara


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

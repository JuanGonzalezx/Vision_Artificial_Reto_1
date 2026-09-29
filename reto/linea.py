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

Horizonte (`mirar_adelante`): los mismos pasos, pero en tramos apilados de
cerca a lejos, para saber hacia dónde va la línea y no solo dónde está.
"""

from __future__ import annotations

from dataclasses import dataclass

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


def contorno_principal(mascara, config: Config, centro_previo: int | None = None,
                       area_minima: int | None = None, ancho_maximo: float | None = None):
    """Contorno que sigue la línea, o None si no hay uno válido.

    Válido = área >= `area_minima_linea` y no más ancho que `ancho_maximo_linea`
    (una cinta transversal no sirve de guía); los tramos del horizonte pasan
    sus propios límites. Sin `centro_previo` se toma el de mayor área; con él,
    el más cercano a donde estaba la línea, para no saltar de un trozo a otro
    cuando algo la parte en dos.

    Técnicas: findContours, contourArea, boundingRect y momentos (clase 3).
    """
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ancho_mascara = mascara.shape[1]
    area_minima = config.area_minima_linea if area_minima is None else area_minima
    ancho_maximo = config.ancho_maximo_linea if ancho_maximo is None else ancho_maximo

    validos = [
        c for c in contornos
        if cv2.contourArea(c) >= area_minima
        and cv2.boundingRect(c)[2] / ancho_mascara <= ancho_maximo
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


# --- Horizonte: el camino que viene, no solo dónde está la línea ahora ------


@dataclass(frozen=True)
class Horizonte:
    """Lo que devuelve `mirar_adelante`: el camino visible delante del robot.

    puntos: centro de la línea en cada tramo, de cerca (abajo) a lejos
    (arriba), en píxeles del frame. Solo entran tramos conectados entre sí.
    desviacion_objetivo: desviación del punto al que conviene apuntar (-1..+1).
    curvatura: objetivo menos cercano; positiva = la pista se va a la derecha.
    sale_por: -1 si la línea se sale por el borde izquierdo antes de llegar
    arriba, +1 por el derecho, 0 si no (curva cerrada que se viene).
    """

    puntos: tuple[tuple[int, int], ...] = ()
    desviacion_objetivo: float = 0.0
    curvatura: float = 0.0
    sale_por: int = 0

    @property
    def detectado(self) -> bool:
        return len(self.puntos) >= 2


def centros_por_tramo(mascara, config: Config, centro_inicial: int | None) -> list[tuple[int, int]]:
    """Recorre la máscara en tramos horizontales de abajo hacia arriba y encadena
    el centroide de la línea en cada uno.

    Cada tramo busca el trozo más cercano al centro del tramo anterior, así la
    cadena sigue la misma línea y no salta a una sombra o a un papel. En un
    tramo bajo la línea es angosta, así que un contorno más ancho que
    `ancho_maximo_tramo` es la barra negra de una señal y se ignora. Si en un
    tramo no hay línea, o el salto es más grande que `salto_maximo_tramo`, la
    cadena se corta: de ahí en adelante ya no es la línea que venimos siguiendo.

    Técnicas: ROI por filas (clase 1), contornos y centroide por momentos
    (clase 3), resta y valor absoluto (clase 2).
    """
    alto, ancho = mascara.shape[:2]
    alto_tramo = alto // config.tramos_horizonte
    salto_maximo = config.salto_maximo_tramo * ancho
    puntos: list[tuple[int, int]] = []
    previo = centro_inicial

    for i in range(config.tramos_horizonte):
        abajo = alto - i * alto_tramo
        arriba = abajo - alto_tramo
        tramo = mascara[arriba:abajo, :]
        contorno = contorno_principal(tramo, config, previo, config.area_minima_tramo,
                                      config.ancho_maximo_tramo)
        centro = centro_horizontal(contorno) if contorno is not None else None

        if centro is None and not puntos:
            continue  # la barra de una señal puede tapar los primeros tramos
        se_corto = centro is None or (previo is not None and abs(centro - previo) > salto_maximo)
        if se_corto:
            break

        puntos.append((centro, (arriba + abajo) // 2))
        previo = centro

    return puntos


def lado_de_salida(puntos: list[tuple[int, int]], ancho: int, alto_tramo: int,
                   config: Config) -> int:
    """-1 / +1 si la cadena se corta pegada a un borde lateral, 0 si no.

    Es la señal más clara de curva cerrada: la línea se va del cuadro por un
    lado antes de llegar a la parte alta de la imagen (el tramo de arriba).
    Los puntos van en coordenadas de la máscara del horizonte.
    """
    llego_arriba = bool(puntos) and puntos[-1][1] < alto_tramo
    if not puntos or llego_arriba:
        return 0

    x_final = puntos[-1][0]
    margen = config.margen_borde_horizonte * ancho

    if x_final <= margen:
        return -1
    if x_final >= ancho - margen:
        return 1
    return 0


def mirar_adelante(frame, config: Config, centro_cercano: int | None = None) -> Horizonte:
    """Anticipa el camino: dónde va a estar la línea cuando el robot avance.

    1. Segmenta una sola vez la zona `roi_horizonte` (misma máscara que la línea).
    2. La recorre en `tramos_horizonte` tramos, de cerca a lejos, encadenando
       los centroides (`centros_por_tramo`).
    3. El punto objetivo es el de `tramo_objetivo` (o el último que se vio si
       la cadena es más corta): es a dónde apunta el robot, como un conductor
       que mira la curva y no el capó.
    4. Si la cadena se sale por un borde, el objetivo es ese borde (±1): la
       curva es más cerrada de lo que la cámara alcanza a mostrar.

    `centro_cercano` ancla el primer tramo a la línea que ya se está siguiendo.

    Técnicas: ROI (clase 1), HSV + inRange (clases 1 y 2), apertura y cierre
    (clase 3), contornos y momentos (clase 3), operaciones aritméticas (clase 2).
    """
    alto, ancho = frame.shape[:2]
    y1, y2 = int(alto * config.roi_horizonte[0]), int(alto * config.roi_horizonte[1])
    mascara = segmentar_linea(frame[y1:y2, :], config)

    locales = centros_por_tramo(mascara, config, centro_cercano)
    puntos = [(x, y + y1) for x, y in locales]
    if len(puntos) < 2:
        return Horizonte(puntos=tuple(puntos))

    sale_por = lado_de_salida(locales, ancho, mascara.shape[0] // config.tramos_horizonte, config)
    objetivo_x = puntos[min(config.tramo_objetivo, len(puntos) - 1)][0]
    desviacion_objetivo = float(sale_por) if sale_por else desviacion_desde_centro(objetivo_x, ancho)
    curvatura = desviacion_objetivo - desviacion_desde_centro(puntos[0][0], ancho)

    return Horizonte(tuple(puntos), desviacion_objetivo, curvatura, sale_por)

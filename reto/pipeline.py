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


GIROS = {
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


def rotar(frame, grados: int):
    """Gira el frame antes de procesarlo (clase 1).

    El celular en el soporte puede quedar de lado; todo lo demas (ROI,
    izquierda y derecha) asume que la pista se ve de frente.
    """
    if grados == 0:
        return frame

    return cv2.rotate(frame, GIROS[grados])


def preparar(frame, config: Config):
    """Redimensiona a un ancho fijo y suaviza (clases 1 y 3).

    Procesar en pequeño es lo que mantiene los FPS, y los FPS son los que
    deciden si la corrección llega a tiempo.
    """
    if frame is None or getattr(frame, "ndim", None) != 3 or frame.shape[2] != 3:
        raise ValueError("El pipeline necesita un frame BGR de tres canales")
    frame = rotar(frame, config.rotacion)
    alto, ancho = frame.shape[:2]
    if alto == 0 or ancho == 0:
        raise ValueError("El pipeline recibió un frame vacío")

    if ancho != config.ancho_proceso:
        nuevo_alto = max(1, int(alto * config.ancho_proceso / ancho))
        frame = cv2.resize(frame, (config.ancho_proceso, nuevo_alto))

    return cv2.GaussianBlur(frame, (config.kernel_gauss, config.kernel_gauss), 0)


def recortar(frame, franja: tuple[float, float]):
    """Devuelve la franja horizontal indicada (ROI, clase 1)."""
    y1, y2 = franja_a_pixeles(frame.shape[0], franja)
    if not 0 <= y1 < y2 <= frame.shape[0]:
        raise ValueError(f"La ROI {franja} no contiene filas válidas con este tamaño de frame")
    return frame[y1:y2, :], y1


def procesar_frame(frame, estado: Estado, config: Config,
                   ahora: float | None = None) -> tuple[Decision, dict]:
    """Ejecuta el algoritmo completo sobre un frame.

    Devuelve la decisión y un diccionario con los resultados intermedios,
    que overlay usa para dibujar y nosotros para calibrar.

    `ahora` permite pasar un reloj distinto al del sistema: el tiempo del
    video al evaluar clips, o el del simulador. Sin él usa el reloj real.
    """
    preparado = preparar(frame, config)

    roi_cercana, desplazamiento = recortar(preparado, config.roi_linea_cercana)
    linea: ResultadoLinea = modulo_linea.detectar(roi_cercana, config, estado.ultimo_centro_linea)
    if linea.detectada:  # si se pierde un instante, se conserva la última posición conocida
        estado.ultimo_centro_linea = linea.centro_x

    roi_lejana, _ = recortar(preparado, config.roi_linea_lejana)
    linea_lejana: ResultadoLinea = modulo_linea.detectar(roi_lejana, config)

    roi_senal, desplazamiento_senal = recortar(preparado, config.roi_senal)
    senal: ResultadoSenal = modulo_senales.detectar(roi_senal, config)

    linea = combinar_franjas(linea, linea_lejana, config, desplazamiento)

    # La señal va sobre una barra negra que cruza la pista: cuando llega a la
    # franja de la línea, la barra entra en la máscara y mueve el centroide.
    # Mientras la tape, se mantiene el rumbo que se traía (ver config).
    congelada = False
    tapa_la_linea = config.congelar_con_senal and senal_sobre_franja(
        senal, desplazamiento_senal, preparado.shape[0], config
    )

    if tapa_la_linea and estado.ultima_desviacion_limpia is not None:
        linea = ResultadoLinea(True, linea.centro_x, estado.ultima_desviacion_limpia,
                               linea.area, linea.mascara)
        congelada = True
    elif linea.detectada:
        estado.ultima_desviacion_limpia = linea.desviacion

    linea = suavizar(linea, estado, config)
    decision = decidir(estado, linea, senal, config, ahora)

    # Diferencia entre lo que ve la franja lejana y la cercana: positiva, la
    # pista se va a la derecha mas adelante. No entra en la decision todavia
    # (ver peso_linea_lejana), pero se muestra en el HUD.
    curvatura = (linea_lejana.desviacion - linea.desviacion
                 if linea.detectada and linea_lejana.detectada else 0.0)

    depuracion = {
        "frame": preparado,
        "linea": linea,
        "linea_lejana": linea_lejana,
        "curvatura": curvatura,
        "linea_congelada": congelada,
        "senal": senal,
        "mascaras": {"linea": linea.mascara, "senal": senal.mascara},
    }

    return decision, depuracion


def senal_sobre_franja(senal: ResultadoSenal, desplazamiento_senal: int, alto: int,
                       config: Config) -> bool:
    """Indica si la señal (y la barra en la que va montada) tapa la franja de la línea.

    Se compara el alto de la caja de la señal (boundingRect, clase 3) con las
    filas de la franja cercana, con un margen porque la barra sobresale un poco.
    """
    if senal.tipo is None or senal.contorno is None:
        return False

    _, y, _, alto_senal = cv2.boundingRect(senal.contorno)
    arriba = y + desplazamiento_senal
    abajo = arriba + alto_senal
    margen = int(alto * config.margen_senal_franja)
    y1, y2 = franja_a_pixeles(alto, config.roi_linea_cercana)

    return abajo + margen >= y1 and arriba - margen <= y2


def suavizar(linea: ResultadoLinea, estado: Estado, config: Config) -> ResultadoLinea:
    """Promedia las últimas desviaciones con operaciones aritméticas (clase 2)."""
    if config.suavizado_desviacion <= 1 or not linea.detectada:
        if not linea.detectada:
            estado.ultimas_desviaciones.clear()
        return linea
    estado.ultimas_desviaciones.append(linea.desviacion)
    del estado.ultimas_desviaciones[:-config.suavizado_desviacion]
    promedio = sum(estado.ultimas_desviaciones) / len(estado.ultimas_desviaciones)
    return ResultadoLinea(True, linea.centro_x, promedio, linea.area, linea.mascara)


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

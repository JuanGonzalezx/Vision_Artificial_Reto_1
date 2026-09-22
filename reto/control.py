"""Máquina de estados: de lo que se ve a lo que hace el robot.

Dueño: Juan David.

No usa OpenCV: solo decide. Eso lo hace fácil de probar sin cámara y fácil de
explicar en la sustentación.

Estados:
  SIGUIENDO  gira proporcional a la desviación de la línea
  DETENIDO   obedece un PARE durante config.segundos_pare
  BUSCANDO   perdió la línea: gira hacia el último lado donde la vio
"""

from __future__ import annotations

import time

from .config import Config
from .tipos import Accion, Decision, Estado, EstadoRobot, ResultadoLinea, ResultadoSenal


def confirmar_senal(estado: Estado, senal: ResultadoSenal, config: Config) -> str | None:
    """Exige que la misma señal aparezca en varios frames seguidos.

    Evita frenar por un reflejo rojo o por un frame con ruido.
    """
    if senal.tipo is None or senal.area < config.area_minima_senal:
        estado.frames_con_senal = 0
        estado.senal_candidata = None
        return None

    if senal.tipo == estado.senal_candidata:
        estado.frames_con_senal += 1
    else:
        estado.senal_candidata = senal.tipo
        estado.frames_con_senal = 1

    if estado.frames_con_senal >= config.frames_confirmacion_senal:
        return senal.tipo

    return None


def decidir(estado: Estado, linea: ResultadoLinea, senal: ResultadoSenal,
            config: Config, ahora: float | None = None) -> Decision:
    """Decide la acción de este frame y actualiza la memoria del robot."""
    ahora = time.monotonic() if ahora is None else ahora
    senal_confirmada = confirmar_senal(estado, senal, config)

    # 1. Si está detenido por un PARE, ahí se queda hasta cumplir el tiempo.
    if estado.estado is EstadoRobot.DETENIDO:
        reanuda_por_siga = config.siga_reanuda and senal_confirmada == "SIGA"

        if ahora < estado.detenido_hasta and not reanuda_por_siga:
            restante = estado.detenido_hasta - ahora
            return Decision(Accion.PARAR, 0.0, f"PARE: faltan {restante:.1f}s")

        estado.estado = EstadoRobot.SIGUIENDO

    # 2. Un PARE confirmado detiene el robot (con espera para no repetir la misma señal).
    desde_la_ultima = ahora - estado.ultima_senal_obedecida

    if senal_confirmada == "PARE" and desde_la_ultima >= config.espera_entre_senales:
        estado.estado = EstadoRobot.DETENIDO
        estado.detenido_hasta = ahora + config.segundos_pare
        estado.ultima_senal_obedecida = ahora
        return Decision(Accion.PARAR, 0.0, f"PARE confirmado (area {senal.area:.0f})")

    # 3. Sin línea: primero se mantiene el rumbo, y si sigue perdida, se busca.
    if not linea.detectada:
        estado.frames_sin_linea += 1

        if estado.frames_sin_linea >= config.frames_para_buscar:
            estado.estado = EstadoRobot.BUSCANDO
            giro = 1.0 if estado.ultimo_giro >= 0 else -1.0
            lado = "derecha" if giro > 0 else "izquierda"
            return Decision(Accion.BUSCAR, giro, f"linea perdida: buscando hacia la {lado}")

        return Decision(Accion.RECTO, estado.ultimo_giro,
                        f"linea perdida hace {estado.frames_sin_linea} frames: mantengo rumbo")

    # 4. Con línea: giro proporcional a la desviación.
    estado.frames_sin_linea = 0
    estado.estado = EstadoRobot.SIGUIENDO
    estado.ultimo_giro = linea.desviacion

    if abs(linea.desviacion) < config.zona_muerta:
        return Decision(Accion.RECTO, 0.0, f"centrado ({linea.desviacion:+.2f})")

    giro = max(-1.0, min(1.0, linea.desviacion * config.ganancia_giro))
    accion = Accion.DERECHA if linea.desviacion > 0 else Accion.IZQUIERDA

    return Decision(accion, giro, f"desviacion {linea.desviacion:+.2f}")

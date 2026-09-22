"""Prueba la máquina de estados sin cámara ni robot.

Simula lo que verían los detectores y revisa que el control reaccione como
esperamos. Es la forma de tocar `control.py` sin miedo a romper algo.

    uv run python tools/probar_control.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reto.config import Config
from reto.control import decidir
from reto.tipos import Accion, Estado, EstadoRobot, ResultadoLinea, ResultadoSenal

SIN_SENAL = ResultadoSenal()


def linea(desviacion: float) -> ResultadoLinea:
    return ResultadoLinea(detectada=True, centro_x=100, desviacion=desviacion, area=5000)


def senal(tipo: str, area: float = 2000) -> ResultadoSenal:
    return ResultadoSenal(tipo=tipo, area=area, centro=(100, 50), vertices=8)


def main() -> None:
    config = Config()
    estado = Estado()
    reloj = 100.0

    # Línea centrada -> sigue recto.
    d = decidir(estado, linea(0.05), SIN_SENAL, config, reloj)
    assert d.accion is Accion.RECTO, d

    # Línea a la derecha -> gira a la derecha, proporcional.
    d = decidir(estado, linea(0.5), SIN_SENAL, config, reloj)
    assert d.accion is Accion.DERECHA and 0 < d.giro <= 1, d

    # Línea a la izquierda -> gira a la izquierda.
    d = decidir(estado, linea(-0.4), SIN_SENAL, config, reloj)
    assert d.accion is Accion.IZQUIERDA and -1 <= d.giro < 0, d

    # Se pierde la línea: primero mantiene el rumbo...
    for _ in range(config.frames_para_buscar - 1):
        d = decidir(estado, ResultadoLinea(), SIN_SENAL, config, reloj)
        assert d.accion is Accion.RECTO, d

    # ...y luego entra a buscar, hacia el último lado conocido (izquierda).
    d = decidir(estado, ResultadoLinea(), SIN_SENAL, config, reloj)
    assert d.accion is Accion.BUSCAR and d.giro < 0, d
    assert estado.estado is EstadoRobot.BUSCANDO

    # Un solo frame con PARE no detiene el robot: hace falta confirmarlo.
    estado = Estado()
    d = decidir(estado, linea(0.0), senal("PARE"), config, reloj)
    assert d.accion is Accion.RECTO, d

    # Con los frames de confirmación, se detiene.
    for _ in range(config.frames_confirmacion_senal - 1):
        d = decidir(estado, linea(0.0), senal("PARE"), config, reloj)
    assert d.accion is Accion.PARAR and estado.estado is EstadoRobot.DETENIDO, d

    # Sigue detenido mientras no pase el tiempo.
    d = decidir(estado, linea(0.0), SIN_SENAL, config, reloj + 1.0)
    assert d.accion is Accion.PARAR, d

    # Cumplido el tiempo, arranca otra vez.
    reloj += config.segundos_pare + 0.1
    d = decidir(estado, linea(0.0), SIN_SENAL, config, reloj)
    assert d.accion is Accion.RECTO and estado.estado is EstadoRobot.SIGUIENDO, d

    # La misma señal, vista enseguida, no vuelve a detener el robot (espera).
    for _ in range(config.frames_confirmacion_senal):
        d = decidir(estado, linea(0.0), senal("PARE"), config, reloj)
    assert d.accion is not Accion.PARAR, d

    # Un PARE nuevo, pasada la espera, sí detiene.
    reloj += config.espera_entre_senales + 1
    for _ in range(config.frames_confirmacion_senal):
        d = decidir(estado, linea(0.0), senal("PARE"), config, reloj)
    assert d.accion is Accion.PARAR, d

    # Un SIGA confirmado reanuda antes de tiempo.
    for _ in range(config.frames_confirmacion_senal):
        d = decidir(estado, linea(0.0), senal("SIGA"), config, reloj + 0.5)
    assert d.accion is not Accion.PARAR, d

    # Una señal lejana (área pequeña) se ignora.
    estado = Estado()
    for _ in range(config.frames_confirmacion_senal + 2):
        d = decidir(estado, linea(0.0), senal("PARE", area=10), config, reloj)
    assert d.accion is Accion.RECTO, d

    print("Todas las pruebas del control pasaron.")


if __name__ == "__main__":
    main()

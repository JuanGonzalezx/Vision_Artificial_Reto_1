"""Enviar las decisiones al mBot: caracteres, a ritmo de pulsos.

Traduce una `Decision` a los comandos del firmware del profesor. **Nosotros no
tocamos el Arduino**: solo mandamos caracteres.

| Carácter | Qué hace | Cuánto dura |
|---|---|---|
| `w` | adelante | 100 ms y **se detiene solo** |
| `s` | atrás | 100 ms y se detiene solo |
| `a` | giro a la izquierda | 30 ms y se detiene solo |
| `d` | giro a la derecha | 30 ms y se detiene solo |
| `x` | detener | inmediato |

**Lo más importante:** los comandos son *pulsos*, no estados. El robot avanza
100 ms y para; para que siga hay que mandarle `w` una y otra vez. Además el
firmware se bloquea 100 ms dentro de cada `w`, así que más de ~10 comandos por
segundo solo llenan el buffer. De ahí las dos reglas de `ActuadorRobot`:

1. **Cadencia fija** (`ritmo_hz`, 10 por defecto): la visión corre a los fps que
   dé la cámara y el robot recibe la última decisión a 10 Hz.
2. **El giro se reparte en pulsos:** se acumula la magnitud del giro y se manda
   un pulso de giro cuando el acumulado pasa de 1; el resto del tiempo, `w`.

`ActuadorRobot` solo llama los verbos del robot: `adelante`, `izquierda`,
`derecha`, `parar`. El robot puede ser `Robot` (`reto/Robot.py`, Bluetooth),
`RobotMac` (`reto/Robot_mac.py`, serie en macOS) o `RobotSimulado` (sin
hardware).

    uv run main.py --fuente <url> --robot-mac 00:1B:10:21:2C:1B
    uv run main.py --fuente <url> --robot-puerto /dev/tty.Makeblock-ELETSPP
    uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --robot-simulado
"""

from __future__ import annotations

import socket
import time

from .Robot import Robot
from .Robot_mac import RobotMac
from .tipos import Accion, Decision


class RobotSimulado:
    """El robot de mentira: imprime el comando en vez de enviarlo."""

    def conectar(self) -> None:
        print("[robot simulado] listo")

    def adelante(self) -> None:
        print("[robot simulado] w")

    def atras(self) -> None:
        print("[robot simulado] s")

    def izquierda(self) -> None:
        print("[robot simulado] a")

    def derecha(self) -> None:
        print("[robot simulado] d")

    def parar(self) -> None:
        print("[robot simulado] x")

    def cerrar(self) -> None:
        print("[robot simulado] cerrado")


def crear_robot(mac: str | None = None, puerto: str | None = None,
                simulado: bool = False):
    """Devuelve el robot a usar: `Robot`/`RobotMac` según el transporte, o el simulado.

    `puerto` es el camino de macOS (serie); `mac` el de Linux y Windows
    (Bluetooth), que necesita `AF_BLUETOOTH` y no existe en Darwin.
    """
    if simulado:
        return RobotSimulado()

    if puerto:
        return RobotMac(puerto)

    if mac:
        if not hasattr(socket, "AF_BLUETOOTH"):
            raise RuntimeError(
                "Este sistema no expone AF_BLUETOOTH (le pasa a macOS). "
                "Empareja el robot y usa el puerto serie: --robot-puerto /dev/tty.<nombre>"
            )
        return Robot(mac)

    raise ValueError("Hace falta --robot-mac o --robot-puerto")


class ActuadorRobot:
    """Convierte decisiones en pulsos para el mBot, a un ritmo controlado.

    Args:
        robot: `Robot`, `RobotMac` o `RobotSimulado`.
        ritmo_hz: cuántos comandos por segundo como máximo. El firmware se
            bloquea 100 ms en cada `w`, así que subir de 10 solo acumula retraso.
        avanzar_al_girar: si es True, después de un pulso de giro también se
            manda `w`. Hace el recorrido más rápido pero las curvas más abiertas.
    """

    def __init__(self, robot, ritmo_hz: float = 10.0,
                 avanzar_al_girar: bool = False) -> None:
        self.robot = robot
        self.intervalo = 1.0 / ritmo_hz if ritmo_hz > 0 else 0.0
        self.avanzar_al_girar = avanzar_al_girar
        self.acumulado_de_giro = 0.0
        self._ultimo_envio = 0.0
        self._detenido = False
        robot.conectar()

    def acciones_para(self, decision: Decision) -> list:
        """Verbos del robot a llamar en este tick. Sin efectos: fácil de probar."""
        if decision.accion is Accion.PARAR:
            self.acumulado_de_giro = 0.0
            return [self.robot.parar]

        if decision.accion is Accion.RECTO:
            self.acumulado_de_giro = 0.0
            return [self.robot.adelante]

        # Giro proporcional repartido en pulsos: se acumula la magnitud del giro
        # y se gasta un pulso cada vez que el acumulado pasa de 1.
        self.acumulado_de_giro += abs(decision.giro)

        if self.acumulado_de_giro < 1.0:
            # Todavía no toca girar: se sigue avanzando, salvo que estemos
            # buscando la línea, donde avanzar a ciegas es peor.
            return [] if decision.accion is Accion.BUSCAR else [self.robot.adelante]

        self.acumulado_de_giro -= 1.0
        girar = self.robot.derecha if decision.giro > 0 else self.robot.izquierda

        if decision.accion is Accion.BUSCAR:
            return [girar]

        return [girar, self.robot.adelante] if self.avanzar_al_girar else [girar]

    def aplicar(self, decision: Decision, contexto: dict | None = None) -> None:
        ahora = time.monotonic()

        # Un PARAR se manda siempre, sin esperar el ritmo: frenar es urgente.
        urgente = decision.accion is Accion.PARAR and not self._detenido

        if not urgente and ahora - self._ultimo_envio < self.intervalo:
            return

        self._ultimo_envio = ahora
        self._detenido = decision.accion is Accion.PARAR

        for accion in self.acciones_para(decision):
            accion()

    def cerrar(self) -> None:
        """Siempre deja el robot quieto antes de soltar la conexión."""
        try:
            self.robot.parar()
        except Exception:  # noqa: BLE001 - al cerrar, un fallo aquí no importa
            pass

        self.robot.cerrar()

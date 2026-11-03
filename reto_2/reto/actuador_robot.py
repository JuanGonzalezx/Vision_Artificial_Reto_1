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
import threading
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
        avance_en_curva: fracción de los `w` que se mandan cuando la decisión
            viene marcada `en_curva` (config.avance_en_curva). 1.0 = no frena.
    """

    def __init__(self, robot, ritmo_hz: float = 10.0,
                 avanzar_al_girar: bool = False, avance_en_curva: float = 1.0) -> None:
        self.robot = robot
        self.intervalo = 1.0 / ritmo_hz if ritmo_hz > 0 else 0.0
        self.avanzar_al_girar = avanzar_al_girar
        self.avance_en_curva = avance_en_curva
        self.acumulado_de_giro = 0.0
        self.acumulado_de_avance = 0.0
        self._ultimo_envio = 0.0
        self._detenido = False
        robot.conectar()

    def _avanzar(self, decision: Decision) -> list:
        """Un pulso `w`, o ninguno si en curva toca frenar.

        Mismo reparto que el giro: en curva se acumula `avance_en_curva` y solo
        se avanza cuando el acumulado pasa de 1. En los ticks sin `w` el robot
        se queda quieto (los pulsos paran solos) y el giro alcanza a corregir.
        """
        if not decision.en_curva:
            self.acumulado_de_avance = 0.0
            return [self.robot.adelante]

        self.acumulado_de_avance += self.avance_en_curva
        if self.acumulado_de_avance < 1.0:
            return []

        self.acumulado_de_avance -= 1.0
        return [self.robot.adelante]

    def acciones_para(self, decision: Decision) -> list:
        """Verbos del robot a llamar en este tick. Sin efectos: fácil de probar."""
        if decision.accion is Accion.PARAR:
            self.acumulado_de_giro = 0.0
            self.acumulado_de_avance = 0.0
            return [self.robot.parar]

        if decision.accion is Accion.RECTO:
            self.acumulado_de_giro = 0.0
            return self._avanzar(decision)

        # Giro proporcional repartido en pulsos: se acumula la magnitud del giro
        # y se gasta un pulso cada vez que el acumulado pasa de 1.
        self.acumulado_de_giro += abs(decision.giro)

        if self.acumulado_de_giro < 1.0:
            # Todavía no toca girar: se sigue avanzando, salvo que estemos
            # buscando la línea, donde avanzar a ciegas es peor.
            return [] if decision.accion is Accion.BUSCAR else self._avanzar(decision)

        self.acumulado_de_giro -= 1.0
        girar = self.robot.derecha if decision.giro > 0 else self.robot.izquierda

        if decision.accion is Accion.BUSCAR:
            return [girar]

        return [girar, *self._avanzar(decision)] if self.avanzar_al_girar else [girar]

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


class ActuadorEnHilo:
    """Envuelve un actuador para que sus envíos no frenen la visión.

    `Robot` duerme 100 ms tras cada carácter; si eso ocurre en el hilo de la
    visión, los fps caen a ~10 y las decisiones salen de imágenes viejas. Aquí
    `aplicar` solo deja la decisión en un casillero de tamaño 1 (la nueva pisa
    a la anterior) y un hilo aparte la manda al actuador real a su ritmo.
    """

    ESPERA_CIERRE_S = 3.0

    def __init__(self, actuador) -> None:
        self.actuador = actuador
        self._condicion = threading.Condition()
        self._pendiente = None
        self._cerrado = False
        self._hilo = threading.Thread(target=self._enviar, daemon=True)
        self._hilo.start()

    def aplicar(self, decision: Decision, contexto: dict | None = None) -> None:
        with self._condicion:
            self._pendiente = (decision, contexto)
            self._condicion.notify()

    def _enviar(self) -> None:
        while True:
            with self._condicion:
                self._condicion.wait_for(lambda: self._pendiente is not None or self._cerrado)
                if self._pendiente is None:
                    return
                decision, contexto = self._pendiente
                self._pendiente = None

            try:
                self.actuador.aplicar(decision, contexto)
            except Exception as error:  # noqa: BLE001 - un fallo de envío no debe matar el hilo
                print(f"[robot] error al enviar: {error}")

    def cerrar(self) -> None:
        """Termina de enviar lo pendiente (el PARAR final) y cierra el actuador."""
        with self._condicion:
            self._cerrado = True
            self._condicion.notify()

        self._hilo.join(timeout=self.ESPERA_CIERRE_S)
        self.actuador.cerrar()

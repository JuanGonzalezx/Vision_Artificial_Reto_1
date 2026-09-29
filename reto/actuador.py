"""Salida del cerebro: entrega cada `Decision` a quien mueve el robot.

Es el único punto que cambia entre el simulador y el robot real. `main.py`
solo conoce la interfaz `Actuador`; para el robot físico se agrega otra clase
(por ejemplo `ActuadorSerial`) que traduzca `comando_desde_decision` a su
protocolo, y ningún otro módulo cambia (docs/arquitectura.md, RF-23).
"""

from __future__ import annotations

from typing import Protocol

from .tipos import Decision


class Actuador(Protocol):
    """Lo que `main.py` necesita de cualquier destino de las decisiones."""

    def enviar(self, decision: Decision) -> None:
        """Entrega la decisión de este frame."""

    def cerrar(self) -> None:
        """Libera lo que haya abierto (puerto, servidor)."""


class ActuadorNulo:
    """No mueve nada: la decisión solo se ve en el HUD (flujo normal)."""

    def enviar(self, decision: Decision) -> None:
        pass

    def cerrar(self) -> None:
        pass


def comando_desde_decision(decision: Decision) -> dict:
    """Formato común de la orden: acción y giro (-1 izquierda .. +1 derecha).

    Lo usan el simulador y, más adelante, el robot real.
    """
    return {"accion": decision.accion.value, "giro": round(decision.giro, 3)}

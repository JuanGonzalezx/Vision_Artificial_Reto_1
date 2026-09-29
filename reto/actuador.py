"""A dónde va la decisión: consola, registro, simulador o robot real.

El control decide y ya; quién ejecuta esa decisión se cambia aquí sin tocar
el resto. Es lo que permite probar el mismo cerebro contra el simulador y
después contra el carro, sin cambiar una línea de `control.py`.

Un actuador solo tiene que cumplir esto:

    class MiActuador:
        def aplicar(self, decision: Decision, contexto: dict | None = None) -> None: ...
        def cerrar(self) -> None: ...
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

from .tipos import Decision


class ActuadorConsola:
    """Imprime la decisión. Útil para ver qué está pensando el robot."""

    def __init__(self, solo_cambios: bool = True) -> None:
        self.solo_cambios = solo_cambios
        self._ultima: str | None = None

    def aplicar(self, decision: Decision, contexto: dict | None = None) -> None:
        clave = f"{decision.accion.value}|{decision.razon}"

        if self.solo_cambios and clave == self._ultima:
            return

        self._ultima = clave
        print(f"[{decision.accion.value:<10}] giro {decision.giro:+.2f}  {decision.razon}")

    def cerrar(self) -> None:
        pass


class ActuadorRegistro:
    """Guarda cada decisión en un CSV.

    De aquí salen las gráficas del póster y el análisis de resultados: cuántas
    correcciones hubo, cuánto tiempo estuvo sin ver la línea, en qué momento
    reconoció cada señal.
    """

    COLUMNAS = ("tiempo", "accion", "giro", "razon", "desviacion", "linea_detectada", "senal")

    def __init__(self, ruta: str | Path) -> None:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)

        self._archivo = ruta.open("w", newline="", encoding="utf8")
        self._csv = csv.writer(self._archivo)
        self._csv.writerow(self.COLUMNAS)
        self._inicio = time.monotonic()

    def aplicar(self, decision: Decision, contexto: dict | None = None) -> None:
        contexto = contexto or {}
        linea = contexto.get("linea")
        senal = contexto.get("senal")
        tiempo = contexto.get("tiempo")
        if tiempo is None:
            tiempo = time.monotonic() - self._inicio

        self._csv.writerow((
            f"{tiempo:.3f}",
            decision.accion.value,
            f"{decision.giro:.3f}",
            decision.razon,
            f"{getattr(linea, 'desviacion', 0.0):.3f}",
            int(bool(getattr(linea, "detectada", False))),
            getattr(senal, "tipo", None) or "",
        ))

    def cerrar(self) -> None:
        self._archivo.close()


class ActuadorMultiple:
    """Manda la misma decisión a varios actuadores (consola + registro + simulador)."""

    def __init__(self, *actuadores) -> None:
        self.actuadores = [a for a in actuadores if a is not None]

    def aplicar(self, decision: Decision, contexto: dict | None = None) -> None:
        for actuador in self.actuadores:
            actuador.aplicar(decision, contexto)

    def cerrar(self) -> None:
        for actuador in self.actuadores:
            actuador.cerrar()


# --- Pendientes -------------------------------------------------------------
#
# ActuadorSimulador (Daniel): recibe la Decision y mueve el carrito del
# simulador. Si el simulador además dibuja la vista de la cámara, esa imagen
# se puede meter de vuelta al pipeline y el lazo queda cerrado.
#
# ActuadorRobot: traduce la Decision a lo que entienda el hardware (serial,
# HTTP...). Es lo único que habría que escribir el día que haya carro.

"""Manejar el robot a mano, sin visión. Lo primero que hay que correr en el laboratorio.

Sirve para separar dos problemas que se confunden: "el robot no se conecta" y
"la visión decide mal". Si aquí el robot responde, la conexión está bien y lo
que falle después es del algoritmo.

    # ver los comandos sin robot
    uv run python tools/probar_robot.py --simulado

    # Linux o Windows
    uv run python tools/probar_robot.py --mac 00:1B:10:21:2C:1B

    # macOS (emparejar primero y buscar el puerto con: ls /dev/tty.*)
    uv run python tools/probar_robot.py --puerto /dev/tty.Makeblock-ELETSPP

Teclas: w adelante, s atras, a izquierda, d derecha, x parar, q salir.
También: `t` mide cuánto tarda el robot en arrancar (latencia) y `r` manda
diez `w` seguidos para ver cómo se comporta con la cadencia real.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reto.actuador_robot import crear_robot  # noqa: E402


def medir_latencia(robot) -> None:
    """Manda un `w` y pide cronometrar cuándo se movió el robot.

    No hay sensor que nos diga cuándo arrancó, así que lo medimos a ojo: es
    suficiente para saber si el Bluetooth mete 50 ms o medio segundo.
    """
    input("Listo para medir. Enter y cronometra cuando arranque... ")
    inicio = time.monotonic()
    robot.adelante()
    input("Enter apenas veas que se movió... ")
    print(f"Latencia aproximada: {1000 * (time.monotonic() - inicio):.0f} ms")


def rafaga(robot, cuantos: int = 10, ritmo_hz: float = 10.0) -> None:
    """Manda varios `w` seguidos al ritmo real, para ver si avanza parejo."""
    print(f"Mandando {cuantos} 'w' a {ritmo_hz} Hz...")
    for _ in range(cuantos):
        robot.adelante()
        time.sleep(1 / ritmo_hz)
    robot.parar()
    print("Listo. ¿Avanzó parejo o a tirones?")


def main() -> None:
    parser = argparse.ArgumentParser(description="Teleoperación del mBot, sin visión.")
    parser.add_argument("--mac", help="MAC Bluetooth del robot (Linux y Windows).")
    parser.add_argument("--puerto", help="Puerto serie del robot (macOS: /dev/tty.*).")
    parser.add_argument("--simulado", action="store_true", help="Solo imprime los comandos.")
    argumentos = parser.parse_args()

    robot = crear_robot(mac=argumentos.mac, puerto=argumentos.puerto,
                        simulado=argumentos.simulado)
    robot.conectar()

    # Cada tecla llama directo al verbo del robot.
    acciones = {
        "w": robot.adelante,
        "s": robot.atras,
        "a": robot.izquierda,
        "d": robot.derecha,
        "x": robot.parar,
    }

    print(__doc__.split("Teclas:")[1].strip())
    print("Recuerda: cada comando es un pulso corto, el robot se detiene solo.\n")

    try:
        while True:
            entrada = input("> ").strip().lower()

            if not entrada:
                continue
            if entrada == "q":
                break
            if entrada == "t":
                medir_latencia(robot)
                continue
            if entrada == "r":
                rafaga(robot)
                continue

            for letra in entrada:
                if letra not in acciones:
                    print(f"'{letra}' no es un comando; usa w a s d x t r q")
                    continue

                acciones[letra]()
                print(f"  {letra} -> {acciones[letra].__name__}")
                time.sleep(0.1)
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        try:
            robot.parar()
        finally:
            robot.cerrar()


if __name__ == "__main__":
    main()

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

from reto.actuador_robot import ADELANTE, ATRAS, DERECHA, IZQUIERDA, PARAR, crear_canal  # noqa: E402

TECLAS = {
    "w": (ADELANTE, "adelante"),
    "s": (ATRAS, "atras"),
    "a": (IZQUIERDA, "izquierda"),
    "d": (DERECHA, "derecha"),
    "x": (PARAR, "parar"),
}


def medir_latencia(canal) -> None:
    """Manda un `w` y pide cronometrar cuándo se movió el robot.

    No hay sensor que nos diga cuándo arrancó, así que lo medimos a ojo: es
    suficiente para saber si el Bluetooth mete 50 ms o medio segundo.
    """
    input("Listo para medir. Enter y cronometra cuando arranque... ")
    inicio = time.monotonic()
    canal.enviar(ADELANTE)
    input("Enter apenas veas que se movió... ")
    print(f"Latencia aproximada: {1000 * (time.monotonic() - inicio):.0f} ms")


def rafaga(canal, cuantos: int = 10, ritmo_hz: float = 10.0) -> None:
    """Manda varios `w` seguidos al ritmo real, para ver si avanza parejo."""
    print(f"Mandando {cuantos} 'w' a {ritmo_hz} Hz...")
    for _ in range(cuantos):
        canal.enviar(ADELANTE)
        time.sleep(1 / ritmo_hz)
    canal.enviar(PARAR)
    print("Listo. ¿Avanzó parejo o a tirones?")


def main() -> None:
    parser = argparse.ArgumentParser(description="Teleoperación del mBot, sin visión.")
    parser.add_argument("--mac", help="MAC Bluetooth del robot (Linux y Windows).")
    parser.add_argument("--puerto", help="Puerto serie del robot (macOS: /dev/tty.*).")
    parser.add_argument("--simulado", action="store_true", help="Solo imprime los comandos.")
    argumentos = parser.parse_args()

    canal = crear_canal(mac=argumentos.mac, puerto_serie=argumentos.puerto,
                        simulado=argumentos.simulado)
    canal.abrir()

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
                medir_latencia(canal)
                continue
            if entrada == "r":
                rafaga(canal)
                continue

            for letra in entrada:
                if letra not in TECLAS:
                    print(f"'{letra}' no es un comando; usa w a s d x t r q")
                    continue

                comando, descripcion = TECLAS[letra]
                canal.enviar(comando)
                print(f"  {comando} -> {descripcion}")
                time.sleep(0.1)
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        try:
            canal.enviar(PARAR)
        finally:
            canal.cerrar()


if __name__ == "__main__":
    main()

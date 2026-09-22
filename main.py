"""Punto de entrada del proyecto.

Por ahora solo abre la cámara en tiempo real y muestra el video en vivo.
Más adelante este mismo loop será el lugar donde se agregue la detección de
la línea guía y de las señales de tránsito.

Ejemplos de uso:

    # Webcam del computador (para desarrollar)
    uv run main.py

    # Cámara del teléfono por la red WiFi (Android o iPhone)
    uv run main.py --fuente http://192.168.1.50:8080/video

    # También se puede fijar la fuente con una variable de entorno
    export CAMARA_URL=http://192.168.1.50:8080/video
    uv run main.py
"""

from __future__ import annotations

import argparse
import os

from camara import mostrar_video_en_vivo


def parsear_argumentos() -> argparse.Namespace:
    """Lee la fuente de video desde --fuente o desde la variable CAMARA_URL."""
    parser = argparse.ArgumentParser(
        description="Muestra en vivo el video de la camara del telefono."
    )
    parser.add_argument(
        "--fuente",
        "-f",
        default=os.environ.get("CAMARA_URL", "0"),
        help=(
            "URL de la camara del telefono (http://IP:PUERTO/video o rtsp://...) "
            "o un indice local como 0 para la webcam. Por defecto usa CAMARA_URL o 0."
        ),
    )
    return parser.parse_args()


def main() -> None:
    argumentos = parsear_argumentos()
    print(f"Abriendo fuente de video: {argumentos.fuente}")
    print("Presiona 'q' en la ventana para salir.")
    mostrar_video_en_vivo(argumentos.fuente)


if __name__ == "__main__":
    main()

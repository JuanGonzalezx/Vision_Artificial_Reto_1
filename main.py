"""Punto de entrada: abre la cámara, corre el pipeline y muestra el resultado.

Ejemplos de uso:

    # Webcam del computador (para desarrollar)
    uv run main.py

    # Cámara del teléfono por WiFi (Android o iPhone)
    uv run main.py --fuente http://192.168.1.50:8080/video

    # Un video de ensayo del profesor
    uv run main.py --fuente datos/videos/pista1.mp4

    # Con una calibración distinta y viendo las máscaras
    uv run main.py --config config_pista.json --mascaras

También se puede fijar la fuente con la variable de entorno CAMARA_URL.
"""

from __future__ import annotations

import argparse
import os
import time

import cv2

from reto.camara import abrir_camara
from reto.config import Config
from reto.overlay import dibujar, mosaico
from reto.pipeline import procesar_frame
from reto.tipos import Estado

VENTANA = "Reto 1 - cerebro del robot"


def parsear_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cerebro del robot seguidor de linea.")
    parser.add_argument(
        "--fuente", "-f",
        default=os.environ.get("CAMARA_URL", "0"),
        help="URL de la camara del telefono, ruta de un video o indice local (0 = webcam).",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="JSON con la calibracion (ver reto/config.py).",
    )
    parser.add_argument(
        "--mascaras", "-m",
        action="store_true",
        help="Muestra tambien el mosaico con las mascaras, para calibrar.",
    )
    return parser.parse_args()


def main() -> None:
    argumentos = parsear_argumentos()
    config = Config.desde_json(argumentos.config) if argumentos.config else Config()
    estado = Estado()

    print(f"Abriendo fuente de video: {argumentos.fuente}")
    print("Presiona 'q' para salir.")

    captura = abrir_camara(argumentos.fuente)
    frames = 0
    inicio = time.time()
    fps = 0.0

    try:
        while True:
            ok, frame = captura.read()

            if not ok:
                print("No llego un frame. Se termino el video o se cayo la conexion.")
                break

            decision, depuracion = procesar_frame(frame, estado, config)

            frames += 1
            transcurrido = time.time() - inicio

            if transcurrido >= 1.0:
                fps = frames / transcurrido
                frames, inicio = 0, time.time()

            vista = dibujar(
                depuracion["frame"], depuracion["linea"], depuracion["senal"],
                decision, estado, config, fps,
            )

            cv2.imshow(VENTANA, vista)

            if argumentos.mascaras:
                cv2.imshow("Mascaras", mosaico(depuracion["frame"], depuracion["mascaras"]))

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        captura.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

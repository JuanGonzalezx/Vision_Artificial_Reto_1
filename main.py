"""Punto de entrada: abre la cámara, corre el pipeline y muestra el resultado.

El loop principal vive aquí: pide frames, se los pasa al pipeline, dibuja el
HUD y sale con 'q'. La lógica de visión está toda en `reto/`.

Ejemplos de uso:

    # Webcam del computador (para desarrollar)
    uv run main.py

    # Camara del iPhone/Android que transmite por red (sin contrasena)
    uv run main.py --fuente http://192.168.1.50:8081/

    # Camara del telefono que pide usuario y contrasena
    uv run main.py --fuente http://100.83.23.67:8081/ --usuario admin --contrasena admin

    # Viendo las mascaras, para calibrar
    uv run main.py --fuente datos/videos/pista1.mp4 --mascaras

    # Con una calibracion aparte, sin tocar el codigo
    uv run main.py --config config_pista.json

    # Tambien se puede configurar todo con variables de entorno
    export CAMARA_URL=http://100.83.23.67:8081/
    export CAMARA_USUARIO=admin
    export CAMARA_CONTRASENA=admin
    uv run main.py
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
VENTANA_MASCARAS = "Mascaras"

# Cuantos frames seguidos pueden fallar antes de dar la camara por perdida.
REINTENTOS = 5


def parsear_argumentos() -> argparse.Namespace:
    """Lee la fuente, las credenciales y la configuracion del CLI o del entorno."""
    parser = argparse.ArgumentParser(
        description="Corre el cerebro del robot sobre el video de la camara."
    )
    parser.add_argument(
        "--fuente",
        "-f",
        default=os.environ.get("CAMARA_URL", "0"),
        help=(
            "URL de la camara del telefono (http://IP:PUERTO/ o rtsp://...), "
            "un archivo de video o un indice local como 0. Por defecto CAMARA_URL o 0."
        ),
    )
    parser.add_argument(
        "--usuario",
        "-u",
        default=os.environ.get("CAMARA_USUARIO"),
        help="Usuario del stream si la app lo pide. Por defecto usa CAMARA_USUARIO.",
    )
    parser.add_argument(
        "--contrasena",
        "-p",
        default=os.environ.get("CAMARA_CONTRASENA"),
        help="Contrasena del stream si la app la pide. Por defecto usa CAMARA_CONTRASENA.",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="JSON con la calibracion; lo que no venga ahi queda por defecto.",
    )
    parser.add_argument(
        "--mascaras",
        "-m",
        action="store_true",
        help="Muestra una ventana aparte con el frame preparado y las mascaras.",
    )
    return parser.parse_args()


def main() -> None:
    argumentos = parsear_argumentos()
    config = Config.desde_json(argumentos.config) if argumentos.config else Config()
    estado = Estado()

    print(f"Abriendo fuente de video: {argumentos.fuente}")
    if argumentos.config:
        print(f"Calibracion cargada de: {argumentos.config}")
    print("Presiona 'q' en la ventana para salir.")

    captura = abrir_camara(argumentos.fuente, argumentos.usuario, argumentos.contrasena)
    intentos_fallidos = 0
    inicio = time.time()
    frames = 0

    try:
        while True:
            ok, frame = captura.read()

            # Si no llega un frame, la transmision pudo caerse: reintentamos.
            if not ok:
                intentos_fallidos += 1
                if intentos_fallidos > REINTENTOS:
                    print("Se perdio la senal de la camara. Cerrando...")
                    break
                print(f"Frame perdido, reintentando ({intentos_fallidos}/{REINTENTOS})...")
                captura.release()
                time.sleep(0.5)
                captura = abrir_camara(argumentos.fuente, argumentos.usuario, argumentos.contrasena)
                continue

            intentos_fallidos = 0

            # FPS reales: son los que dicen si el control alcanza a llegar a tiempo.
            frames += 1
            fps = frames / (time.time() - inicio)

            # Un frame entra al pipeline y sale una decision, con sus datos intermedios.
            decision, depuracion = procesar_frame(frame, estado, config)

            vista = dibujar(
                frame,
                depuracion["linea"],
                depuracion["senal"],
                decision,
                estado,
                config,
                fps,
            )
            cv2.imshow(VENTANA, vista)

            # Para calibrar: el frame preparado junto a las mascaras de cada etapa.
            if argumentos.mascaras:
                cv2.imshow(
                    VENTANA_MASCARAS,
                    mosaico(depuracion["frame"], depuracion["mascaras"]),
                )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        # Liberamos la camara y cerramos las ventanas al terminar.
        captura.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

"""Punto de entrada: abre la cámara, corre el pipeline y muestra el resultado.

El loop principal vive aquí: pide frames, se los pasa al pipeline, dibuja el
HUD y sale con 'q'. La lógica de visión está toda en `reto/`.

Ejemplos de uso:

    # Video de desarrollo (vid/video1.mp4), se repite al terminar
    uv run main.py

    # Webcam del computador
    uv run main.py --fuente 0

    # Camara del iPhone/Android que transmite por red (sin contrasena)
    uv run main.py --fuente http://192.168.1.50:8081/

    # Camara del telefono que pide usuario y contrasena
    uv run main.py --fuente http://100.83.23.67:8081/ --usuario admin --contrasena admin

    # Viendo las mascaras, para calibrar
    uv run main.py --fuente datos/videos/pista1.mp4 --mascaras

    # Con una calibracion aparte, sin tocar el codigo
    uv run main.py --config config_pista.json

    # Flujo alterno: el simulador (simulacion/index.html) hace de camara y de robot
    uv run main.py --index

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

from reto.actuador import ActuadorNulo
from reto.camara import abrir_camara
from reto.config import Config
from reto.overlay import dibujar, mosaico
from reto.pipeline import procesar_frame
from reto.simulador import PuenteSimulador
from reto.tipos import Estado

VENTANA = "Reto 1 - cerebro del robot"
VENTANA_MASCARAS = "Mascaras"

# Fuente por defecto para desarrollar sin celular; las pruebas reales usan --fuente <url>.
FUENTE_DESARROLLO = "vid/video1.mp4"

# Calibracion del flujo --index (camara del simulador).
CONFIG_SIMULADOR = "configs/simulador.json"

# Cuantos frames seguidos pueden fallar antes de dar la camara por perdida.
REINTENTOS = 5


def es_archivo_de_video(fuente: str) -> bool:
    """Un archivo se repite al terminar; una camara en vivo se reconecta."""
    return os.path.isfile(fuente)


def parsear_argumentos() -> argparse.Namespace:
    """Lee la fuente, las credenciales y la configuracion del CLI o del entorno."""
    parser = argparse.ArgumentParser(
        description="Corre el cerebro del robot sobre el video de la camara."
    )
    parser.add_argument(
        "--fuente",
        "-f",
        default=os.environ.get("CAMARA_URL", FUENTE_DESARROLLO),
        help=(
            "URL de la camara del telefono (http://IP:PUERTO/ o rtsp://...), "
            f"un archivo de video o un indice local como 0. Por defecto CAMARA_URL o {FUENTE_DESARROLLO}."
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
    parser.add_argument(
        "--index",
        action="store_true",
        help=(
            "Flujo alterno: abre el simulador (simulacion/index.html) en el navegador, "
            "lee su pantalla como camara y le envia las decisiones como si fuera el robot."
        ),
    )
    return parser.parse_args()


def main() -> None:
    argumentos = parsear_argumentos()
    # El simulador tiene otra geometria de camara: usa su propia calibracion si no se pasa --config.
    ruta_config = argumentos.config or (CONFIG_SIMULADOR if argumentos.index else None)
    config = Config.desde_json(ruta_config) if ruta_config else Config()
    estado = Estado()

    if ruta_config:
        print(f"Calibracion cargada de: {ruta_config}")
    print("Presiona 'q' en la ventana para salir.")

    # La camara y el actuador son lo unico que cambia entre flujos:
    #   normal: camara/video + ActuadorNulo (la decision solo se ve en el HUD)
    #   --index: el simulador es a la vez camara y actuador
    #   robot real: camara del celular + el actuador del robot (T5.4)
    if argumentos.index:
        captura = actuador = PuenteSimulador()
        print(f"Simulador en {captura.url} (si no se abre solo, pegalo en el navegador)")
    else:
        print(f"Abriendo fuente de video: {argumentos.fuente}")
        captura = abrir_camara(argumentos.fuente, argumentos.usuario, argumentos.contrasena)
        actuador = ActuadorNulo()

    es_video = not argumentos.index and es_archivo_de_video(argumentos.fuente)
    # Un video se reproduce a su velocidad real, para que los tiempos del control
    # (segundos de PARE, esperas) se comporten como en la pista.
    espera_ms = int(1000 / (captura.get(cv2.CAP_PROP_FPS) or 30)) if es_video else 1
    intentos_fallidos = 0
    inicio = time.time()
    frames = 0

    try:
        while True:
            ok, frame = captura.read()

            # Fin del video de desarrollo: vuelve al inicio con el robot en estado limpio.
            if not ok and es_video:
                captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
                estado = Estado()
                continue

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
            actuador.enviar(decision)

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

            if cv2.waitKey(espera_ms) & 0xFF == ord("q"):
                break
    finally:
        # Liberamos la camara y cerramos las ventanas al terminar.
        actuador.cerrar()
        if not argumentos.index:
            captura.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

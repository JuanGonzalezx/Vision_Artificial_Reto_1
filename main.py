"""Entrada del cerebro: cámara/archivo -> pipeline -> actuador y visualización.

    uv run main.py --fuente http://192.168.1.50:8081/ --usuario admin
    uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --mascaras
    uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --sin-ventana --grabar
    uv run main.py --fuente <url> --robot-mac 00:1B:10:21:2C:1B
    uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --robot-simulado

También acepta CAMARA_URL, CAMARA_USUARIO y CAMARA_CONTRASENA.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

from reto.actuador import ActuadorConsola, ActuadorMultiple, ActuadorRegistro
from reto.actuador_robot import ActuadorRobot, crear_canal
from reto.camara import abrir_camara, describir_fuente, es_fuente_archivo
from reto.config import Config
from reto.overlay import dibujar, mosaico
from reto.pipeline import procesar_frame
from reto.tipos import Accion, Decision, Estado

VENTANA = "Reto 1 - cerebro del robot"
VENTANA_MASCARAS = "Mascaras"
GRABACIONES = Path(__file__).resolve().parent / "datos" / "grabaciones"


def parsear_argumentos() -> argparse.Namespace:
    """Lee la fuente y las credenciales del CLI o de variables de entorno."""
    parser = argparse.ArgumentParser(description="Cerebro del robot seguidor de linea.")
    parser.add_argument("--fuente", "-f", default=os.environ.get("CAMARA_URL", "0"),
                        help="URL de camara, archivo de video o indice local (CAMARA_URL o 0).")
    parser.add_argument("--usuario", "-u", default=os.environ.get("CAMARA_USUARIO"),
                        help="Usuario del stream; por defecto CAMARA_USUARIO.")
    parser.add_argument("--contrasena", "-p", default=os.environ.get("CAMARA_CONTRASENA"),
                        help="Clave del stream; por defecto CAMARA_CONTRASENA.")
    parser.add_argument("--config", "-c", help="JSON de calibracion; los campos omitidos usan defaults.")
    parser.add_argument("--mascaras", "-m", action="store_true", help="Muestra las mascaras.")
    parser.add_argument("--grabar", "-g", action="store_true",
                        help="Guarda video y CSV en datos/grabaciones/.")
    parser.add_argument("--consola", action="store_true", help="Imprime las decisiones.")
    parser.add_argument("--sin-ventana", action="store_true", help="Procesa sin abrir ventanas.")

    robot = parser.add_argument_group("robot (mBot del profesor)")
    robot.add_argument("--robot-mac", default=os.environ.get("ROBOT_MAC"),
                       help="MAC Bluetooth del mBot; por defecto ROBOT_MAC. Linux y Windows.")
    robot.add_argument("--robot-puerto", default=os.environ.get("ROBOT_PUERTO"),
                       help="Puerto serie del mBot (macOS: /dev/tty.<nombre>); por defecto ROBOT_PUERTO.")
    robot.add_argument("--robot-simulado", action="store_true",
                       help="Imprime los comandos en vez de enviarlos, para probar sin robot.")
    robot.add_argument("--robot-ritmo", type=float, default=10.0,
                       help="Comandos por segundo (el firmware se bloquea 100 ms por cada 'w').")
    robot.add_argument("--robot-avanzar-al-girar", action="store_true",
                       help="Manda 'w' despues de cada pulso de giro: mas rapido, curvas mas abiertas.")

    argumentos = parser.parse_args()
    if argumentos.sin_ventana and argumentos.mascaras:
        parser.error("--mascaras requiere ventana; retira --sin-ventana.")
    return argumentos


def crear_actuador(argumentos: argparse.Namespace, marca: str) -> ActuadorMultiple:
    """El mismo contrato sirve para consola, CSV y el robot real."""
    consola = ActuadorConsola() if argumentos.consola else None
    registro = ActuadorRegistro(GRABACIONES / f"{marca}_decisiones.csv") if argumentos.grabar else None
    robot = None

    if argumentos.robot_simulado or argumentos.robot_mac or argumentos.robot_puerto:
        canal = crear_canal(
            mac=argumentos.robot_mac,
            puerto_serie=argumentos.robot_puerto,
            simulado=argumentos.robot_simulado,
        )
        robot = ActuadorRobot(
            canal,
            ritmo_hz=argumentos.robot_ritmo,
            avanzar_al_girar=argumentos.robot_avanzar_al_girar,
        )

    return ActuadorMultiple(consola, registro, robot)


def fps_de_fuente(captura, config: Config) -> float:
    """Usa la cadencia declarada, con respaldo si el backend no la informa."""
    fps = captura.get(cv2.CAP_PROP_FPS)
    return fps if math.isfinite(fps) and fps > 0 else config.fps_respaldo


def reconectar(argumentos, config: Config):
    """Intenta abrir y recibir un frame; abrir sin recibir no es recuperarse."""
    for intento in range(1, config.reintentos_camara + 1):
        print(f"Reconectando camara ({intento}/{config.reintentos_camara})...")
        time.sleep(config.pausa_reconexion_s)
        captura = None
        recuperada = False
        try:
            captura = abrir_camara(argumentos.fuente, argumentos.usuario,
                                   argumentos.contrasena, config)
            ok, frame = captura.read()
            if ok and frame is not None:
                recuperada = True
                return captura, frame
        except (RuntimeError, cv2.error):
            pass
        finally:
            if captura is not None and not recuperada:
                captura.release()
    raise RuntimeError("Se perdio la camara y se agotaron los intentos de reconexion.")


def crear_grabador(vista, marca: str, fps: float):
    """Abre el video de salida y comprueba que el codec esté disponible."""
    GRABACIONES.mkdir(parents=True, exist_ok=True)
    ruta = GRABACIONES / f"{marca}_procesado.mp4"
    alto, ancho = vista.shape[:2]
    grabador = cv2.VideoWriter(str(ruta), cv2.VideoWriter_fourcc(*"mp4v"), fps, (ancho, alto))
    if not grabador.isOpened():
        grabador.release()
        raise RuntimeError(f"No se pudo crear la grabacion: {ruta}")
    return grabador


def ejecutar(argumentos, config: Config) -> int:
    """Procesa una sesión y libera sus recursos incluso cuando hay errores."""
    config.validar()
    estado = Estado()
    marca = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    es_archivo = es_fuente_archivo(argumentos.fuente)
    captura = grabador = actuador = None
    frames = 0
    tiempo_frame = 0.0
    inicio = time.monotonic()
    print(f"Abriendo fuente de video: {describir_fuente(argumentos.fuente)}")
    if not argumentos.sin_ventana:
        print("Presiona 'q' o Esc para salir.")

    try:
        captura = abrir_camara(argumentos.fuente, argumentos.usuario, argumentos.contrasena, config)
        fps_fuente = fps_de_fuente(captura, config)
        actuador = crear_actuador(argumentos, marca)
        inicio = time.monotonic()
        while True:
            ok, frame = captura.read()
            if not ok or frame is None:
                if es_archivo:
                    if frames == 0:
                        raise RuntimeError("El archivo no contiene frames que se puedan leer.")
                    print(f"Fin del video: {frames} frames procesados.")
                    break
                actuador.aplicar(Decision(Accion.PARAR, razon="camara sin imagen"),
                                 {"tiempo": time.monotonic() - inicio})
                captura.release()
                captura, frame = reconectar(argumentos, config)
                # Una interrupción rompe la evidencia de frames consecutivos.
                estado.frames_con_senal = 0
                estado.senal_candidata = None
                estado.ultimas_desviaciones.clear()

            # En archivos usamos el tiempo del video, aunque se procese más rápido.
            tiempo_frame = frames / fps_fuente if es_archivo else time.monotonic() - inicio
            decision, depuracion = procesar_frame(frame, estado, config, ahora=tiempo_frame)
            depuracion["tiempo"] = tiempo_frame
            actuador.aplicar(decision, depuracion)
            frames += 1
            transcurrido = time.monotonic() - inicio
            fps_proceso = frames / transcurrido if transcurrido > 0 else 0.0

            if argumentos.grabar or not argumentos.sin_ventana:
                vista = dibujar(depuracion["frame"], depuracion["linea"], depuracion["senal"],
                                decision, estado, config, fps_proceso, depuracion["curvatura"])
                if argumentos.grabar:
                    if grabador is None:
                        grabador = crear_grabador(vista, marca, fps_fuente)
                    grabador.write(vista)
                if not argumentos.sin_ventana:
                    cv2.imshow(VENTANA, vista)
                    if argumentos.mascaras:
                        cv2.imshow(VENTANA_MASCARAS, mosaico(depuracion["frame"], depuracion["mascaras"]))
                    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                        break
    finally:
        # Una salida normal, Ctrl+C o error debe dejar una orden de parada.
        try:
            if actuador is not None:
                tiempo_cierre = frames / fps_fuente if es_archivo else time.monotonic() - inicio
                actuador.aplicar(Decision(Accion.PARAR, razon="fin de sesion"),
                                 {"tiempo": tiempo_cierre})
        finally:
            try:
                if actuador is not None:
                    actuador.cerrar()
            finally:
                if captura is not None:
                    captura.release()
                if grabador is not None:
                    grabador.release()
                if not argumentos.sin_ventana:
                    cv2.destroyAllWindows()
    if argumentos.grabar:
        print(f"Resultados guardados en {GRABACIONES}/{marca}_*")
    return frames


def main() -> int:
    argumentos = parsear_argumentos()
    try:
        config = Config.desde_json(argumentos.config) if argumentos.config else Config()
        ejecutar(argumentos, config)
    except KeyboardInterrupt:
        print("Sesion interrumpida.")
        return 130
    except (OSError, ValueError, RuntimeError, cv2.error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

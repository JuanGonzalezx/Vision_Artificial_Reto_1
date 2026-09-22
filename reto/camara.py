"""Captura de video en tiempo real desde la cámara del teléfono.

Etapa 1 del proyecto: obtener los frames crudos de la cámara para poder
trabajar sobre ellos más adelante (detección de línea y de señales).

La fuente de video puede ser:
- Una URL de red (MJPEG o RTSP): el teléfono transmite por la red interna y la
  computadora la lee. Funciona igual con iPhone y con Android.
- Un índice local (0, 1, ...): la webcam del computador, útil para desarrollar.

Todas las operaciones de imagen usan OpenCV (cv2), tal como se vio en el
notebook 1 (Fundamentación): leer imágenes, manipularlas y mostrarlas.
"""

from __future__ import annotations

import time

import cv2

# Nombre por defecto de la ventana donde se muestra el video en vivo.
VENTANA_POR_DEFECTO = "Camara en vivo"


def abrir_camara(fuente: str | int) -> cv2.VideoCapture:
    """Abre la fuente de video y la deja lista para leer frames.

    Se configura un buffer de 1 frame para reducir la latencia: en video en
    tiempo real nos interesa el frame más reciente, no los que se acumulan.
    """
    # Un índice local se convierte a entero; una URL se usa tal cual.
    objetivo = int(fuente) if isinstance(fuente, str) and fuente.isdigit() else fuente

    captura = cv2.VideoCapture(objetivo)
    captura.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not captura.isOpened():
        raise RuntimeError(
            f"No se pudo abrir la fuente de video: {objetivo!r}\n"
            "Si es la camara del telefono verifica que:\n"
            "  - El telefono y la computadora esten en la misma red WiFi.\n"
            "  - La app de camara IP este transmitiendo y usa la URL correcta\n"
            "    (por ejemplo http://192.168.1.50:8080/video)."
        )

    return captura


def mostrar_video_en_vivo(
    fuente: str | int,
    nombre_ventana: str = VENTANA_POR_DEFECTO,
    reintentos: int = 5,
) -> None:
    """Abre la cámara y muestra el video en vivo hasta que se presione 'q'.

    Si la transmisión por red se corta (algo común en WiFi), se intenta
    reconectar unas pocas veces antes de rendirse.
    """
    captura = abrir_camara(fuente)
    intentos_fallidos = 0
    inicio = time.time()
    frames = 0

    try:
        while True:
            ok, frame = captura.read()

            # Si no llega un frame, la transmisión pudo caerse: reintentamos.
            if not ok:
                intentos_fallidos += 1
                if intentos_fallidos > reintentos:
                    print("Se perdio la senal de la camara. Cerrando...")
                    break
                print(f"Frame perdido, reintentando ({intentos_fallidos}/{reintentos})...")
                captura.release()
                time.sleep(0.5)
                captura = abrir_camara(fuente)
                continue

            intentos_fallidos = 0

            # Calculamos los FPS reales para vigilar el rendimiento en vivo.
            frames += 1
            fps = frames / (time.time() - inicio)
            cv2.putText(
                frame,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
            )

            # Mostramos el frame y salimos si se presiona 'q'.
            cv2.imshow(nombre_ventana, frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        # Liberamos la cámara y cerramos las ventanas al terminar.
        captura.release()
        cv2.destroyAllWindows()

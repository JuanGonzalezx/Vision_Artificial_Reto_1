"""Captura de video en tiempo real desde la cámara del teléfono.

Etapa 1 del proyecto: obtener los frames crudos de la cámara para poder
trabajar sobre ellos más adelante (detección de línea y de señales).

La fuente de video puede ser:
- Una URL de red (MJPEG o RTSP): el teléfono transmite y la computadora la lee.
  Funciona igual con iPhone y con Android, y sirve tanto por WiFi como por
  Tailscale (IP 100.x). Muchas apps piden usuario y contraseña.
- Un índice local (0, 1, ...): la webcam del computador, útil para desarrollar.

Todas las operaciones de imagen usan OpenCV (cv2), tal como se vio en el
notebook 1 (Fundamentación): leer imágenes, manipularlas y mostrarlas.
"""

from __future__ import annotations

from urllib.parse import quote, urlsplit, urlunsplit

import cv2

# Tiempo máximo (ms) para abrir y para leer de un stream de red, para no
# quedarnos colgados si el teléfono deja de responder.
TIEMPO_LIMITE_MS = 8000


def agregar_credenciales(url: str, usuario: str | None, contrasena: str | None) -> str:
    """Inserta usuario y contraseña dentro de la URL del stream.

    OpenCV no acepta usuario y contraseña por separado, así que los metemos en
    la URL con el formato http://usuario:contrasena@host:puerto/ruta.
    """
    if not usuario:
        return url

    partes = urlsplit(url)
    # quote() escapa caracteres especiales (@, :, espacios) en las credenciales.
    credenciales = f"{quote(usuario)}:{quote(contrasena or '')}@"
    autoridad = f"{credenciales}{partes.hostname}"
    if partes.port:
        autoridad += f":{partes.port}"

    return urlunsplit(partes._replace(netloc=autoridad))


def abrir_camara(
    fuente: str | int,
    usuario: str | None = None,
    contrasena: str | None = None,
) -> cv2.VideoCapture:
    """Abre la fuente de video y la deja lista para leer frames.

    Se configura un buffer de 1 frame para reducir la latencia: en video en
    tiempo real nos interesa el frame más reciente, no los que se acumulan.
    """
    # Un índice local se convierte a entero; una URL recibe las credenciales.
    if isinstance(fuente, str) and not fuente.isdigit():
        objetivo = agregar_credenciales(fuente, usuario, contrasena)
    else:
        objetivo = int(fuente)

    captura = cv2.VideoCapture(objetivo)
    captura.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if isinstance(objetivo, str):
        # Solo aplican a streams de red, evitan bloqueos indefinidos.
        captura.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, TIEMPO_LIMITE_MS)
        captura.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, TIEMPO_LIMITE_MS)

    if not captura.isOpened():
        raise RuntimeError(
            f"No se pudo abrir la fuente de video: {objetivo!r}\n"
            "Si es la camara del telefono verifica que:\n"
            "  - El telefono este encendido y transmitiendo.\n"
            "  - La computadora alcance su IP (misma red WiFi o Tailscale).\n"
            "  - La URL sea la correcta (por ejemplo http://IP:8081/).\n"
            "  - El usuario y la contrasena sean los que pide la app."
        )

    return captura



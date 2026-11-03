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

import threading
from urllib.parse import quote, urlsplit, urlunsplit

import cv2

from .config import Config


def es_fuente_red(fuente: str | int) -> bool:
    """Distingue un stream de red de un índice local o un archivo."""
    return isinstance(fuente, str) and urlsplit(fuente).scheme.lower() in {
        "http", "https", "rtsp", "rtsps", "rtmp", "udp", "tcp",
    }


def es_fuente_archivo(fuente: str | int) -> bool:
    """Los archivos terminan al llegar a EOF; las cámaras pueden reconectarse."""
    return isinstance(fuente, str) and not fuente.isdigit() and not es_fuente_red(fuente)


def describir_fuente(fuente: str | int) -> str:
    """Describe la fuente sin imprimir credenciales ni parámetros de la URL."""
    if not es_fuente_red(fuente):
        return str(fuente)
    partes = urlsplit(fuente)
    return urlunsplit(partes._replace(netloc=partes.netloc.rsplit("@", 1)[-1],
                                     query="", fragment=""))


def agregar_credenciales(url: str, usuario: str | None, contrasena: str | None) -> str:
    """Inserta usuario y contraseña dentro de la URL del stream.

    OpenCV no acepta usuario y contraseña por separado, así que los metemos en
    la URL con el formato http://usuario:contrasena@host:puerto/ruta.
    """
    if not usuario or not es_fuente_red(url):
        return url

    partes = urlsplit(url)
    # quote() escapa caracteres especiales (@, :, espacios) en las credenciales.
    credenciales = f"{quote(usuario, safe='')}:{quote(contrasena or '', safe='')}@"
    autoridad = credenciales + partes.netloc.rsplit("@", 1)[-1]

    return urlunsplit(partes._replace(netloc=autoridad))


def abrir_camara(
    fuente: str | int,
    usuario: str | None = None,
    contrasena: str | None = None,
    config: Config | None = None,
) -> cv2.VideoCapture:
    """Abre la fuente de video y la deja lista para leer frames.

    Se configura un buffer de 1 frame para reducir la latencia: en video en
    tiempo real nos interesa el frame más reciente, no los que se acumulan.
    """
    config = config or Config()
    # Un índice local se convierte a entero; solo una URL recibe credenciales.
    if isinstance(fuente, str) and not fuente.isdigit():
        objetivo = agregar_credenciales(fuente, usuario, contrasena)
    else:
        objetivo = int(fuente)

    if es_fuente_red(fuente):
        # FFmpeg aplica los límites al abrir, no con set() después de abrir.
        captura = cv2.VideoCapture(objetivo, cv2.CAP_FFMPEG, [
            cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, config.tiempo_limite_camara_ms,
            cv2.CAP_PROP_READ_TIMEOUT_MSEC, config.tiempo_limite_camara_ms,
        ])
    else:
        captura = cv2.VideoCapture(objetivo)
    captura.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not captura.isOpened():
        captura.release()
        raise RuntimeError(
            f"No se pudo abrir la fuente de video: {describir_fuente(fuente)!r}\n"
            "Si es la camara del telefono verifica que:\n"
            "  - El telefono este encendido y transmitiendo.\n"
            "  - La computadora alcance su IP (misma red WiFi o Tailscale).\n"
            "  - La URL sea la correcta (por ejemplo http://IP:8081/).\n"
            "  - El usuario y la contrasena sean los que pide la app."
        )

    return captura


class LectorReciente:
    """Lee la cámara en un hilo y entrega siempre el frame más nuevo.

    El buffer de FFmpeg en streams de red suele ignorar `CAP_PROP_BUFFERSIZE`,
    y si el procesamiento va más lento que la cámara se leen frames cada vez
    más viejos. Aquí un hilo lee sin parar y solo guarda el último; `read()`
    espera un frame que no se haya entregado y descarta los intermedios.
    """

    def __init__(self, captura: cv2.VideoCapture, espera_s: float = 5.0) -> None:
        self._captura = captura
        self._espera_s = espera_s
        self._condicion = threading.Condition()
        self._frame = None
        self._hay_frame_nuevo = False
        self._terminado = False
        self._detener = threading.Event()
        self._hilo = threading.Thread(target=self._leer, daemon=True)
        self._hilo.start()

    def _leer(self) -> None:
        while not self._detener.is_set():
            ok, frame = self._captura.read()
            with self._condicion:
                if ok and frame is not None:
                    self._frame = frame
                    self._hay_frame_nuevo = True
                else:
                    # Sin imagen: el consumidor decide si reconecta.
                    self._terminado = True
                self._condicion.notify_all()
            if self._terminado:
                return

    def read(self):
        """Mismo contrato que `VideoCapture.read()`: (ok, frame)."""
        with self._condicion:
            self._condicion.wait_for(
                lambda: self._hay_frame_nuevo or self._terminado, self._espera_s)
            if not self._hay_frame_nuevo:
                return False, None
            self._hay_frame_nuevo = False
            return True, self._frame

    def get(self, propiedad: int) -> float:
        return self._captura.get(propiedad)

    def isOpened(self) -> bool:
        return self._captura.isOpened()

    def release(self) -> None:
        # Se espera al hilo antes de liberar: soltar la captura en plena lectura no es seguro.
        self._detener.set()
        self._hilo.join(timeout=self._espera_s)
        self._captura.release()


def con_frame_reciente(captura, fuente: str | int, config: Config | None = None):
    """Envuelve las fuentes de red en `LectorReciente`; archivos y webcam pasan igual."""
    if not es_fuente_red(fuente):
        return captura
    config = config or Config()
    return LectorReciente(captura, espera_s=config.tiempo_limite_camara_ms / 1000 + 1.0)


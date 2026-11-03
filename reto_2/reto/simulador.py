"""Puente con el simulador de la pista (simulacion/index.html).

Flujo alterno `uv run main.py --index`: hace de "cámara" y de "robot" a la vez.

  navegador (canvas del simulador) --POST /frame (JPEG)--> este servidor --> pipeline
  navegador  <--respuesta JSON con la última orden------- este servidor <-- Decision

Solo usa la librería estándar: el servidor HTTP sirve la carpeta simulacion/ y
recibe los frames. Por dentro se comporta como una captura de OpenCV
(`read`, `release`) y como un actuador (`aplicar`, `cerrar`), así que
`main.py` lo trata igual que a la cámara del celular y al robot.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np

from .actuador import comando_desde_decision
from .tipos import Decision

CARPETA_SIMULADOR = Path(__file__).resolve().parent.parent / "simulacion"
PUERTO = 8765
ESPERA_FRAME_S = 0.2                  # cuánto espera read() un frame nuevo antes de repetir el último
TAMANO_INICIAL = (850, 480, 3)        # alto, ancho, canales del canvas del simulador
COMANDO_INICIAL = {"accion": "PARAR", "giro": 0.0}


class PuenteSimulador:
    """Captura + actuador conectados al simulador por HTTP."""

    def __init__(self, puerto: int = PUERTO, abrir_navegador: bool = True):
        self.puerto = puerto
        self.telemetria: dict = {}        # descarrilamientos, incumplimientos, vueltas...
        self._frame = np.zeros(TAMANO_INICIAL, np.uint8)
        self._numero = 0                  # cuántos frames han llegado
        self._leido = 0                   # cuántos ha entregado read()
        self._comando = dict(COMANDO_INICIAL)
        self._llego_frame = threading.Condition()
        self._servidor = ThreadingHTTPServer(("127.0.0.1", puerto), self._crear_manejador())
        threading.Thread(target=self._servidor.serve_forever, daemon=True).start()
        self.url = f"http://localhost:{puerto}/index.html?puente=1"

        if abrir_navegador:
            webbrowser.open(self.url)

    # --- como captura de OpenCV -------------------------------------------
    def read(self):
        """Último frame del simulador. Si no llegó uno nuevo, repite el anterior."""
        with self._llego_frame:
            if self._numero == self._leido:
                self._llego_frame.wait(ESPERA_FRAME_S)
            self._leido = self._numero
            return True, self._frame.copy()

    def release(self) -> None:
        self._servidor.shutdown()
        self._servidor.server_close()

    def get(self, propiedad) -> float:
        return 0.0

    # --- como actuador ---------------------------------------------------
    def aplicar(self, decision: Decision, contexto: dict | None = None) -> None:
        self._comando = comando_desde_decision(decision)

    def cerrar(self) -> None:
        self.release()

    # --- servidor HTTP -----------------------------------------------------
    def _recibir(self, cuerpo: bytes, telemetria: str | None) -> dict:
        """Guarda el frame recibido y devuelve la última orden."""
        imagen = cv2.imdecode(np.frombuffer(cuerpo, np.uint8), cv2.IMREAD_COLOR)

        if imagen is not None:
            with self._llego_frame:
                self._frame = imagen
                self._numero += 1
                self._llego_frame.notify_all()

        if telemetria:
            try:
                self.telemetria = json.loads(telemetria)
            except ValueError:
                pass

        return self._comando

    def _crear_manejador(self):
        puente = self

        class Manejador(SimpleHTTPRequestHandler):
            def do_POST(self):
                if self.path != "/frame":
                    self.send_error(404)
                    return

                cuerpo = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                respuesta = json.dumps(puente._recibir(cuerpo, self.headers.get("X-Telemetria"))).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(respuesta)))
                self.end_headers()
                self.wfile.write(respuesta)

            def log_message(self, *args):
                pass  # sin ruido en la consola

        return partial(Manejador, directory=str(CARPETA_SIMULADOR))

"""La versión de `Robot` (`reto/Robot.py`) que sí funciona en macOS.

En macOS el módulo `socket` de Python **no trae `AF_BLUETOOTH`**, así que el
socket RFCOMM de `Robot` falla al conectar. Al emparejar el mBot, macOS crea
un dispositivo `/dev/tty.<nombre>`; por ahí se mandan **los mismos caracteres**
con el mismo firmware. Esta clase tiene la misma interfaz que `Robot`
(`conectar`, `adelante`, `atras`, `izquierda`, `derecha`, `parar`, `cerrar`)
y los mismos tiempos, solo cambia el transporte.

    python3 -c "import socket; print(hasattr(socket, 'AF_BLUETOOTH'))"   # False
    ls /dev/tty.* | grep -i makeblock
    uv run main.py --fuente <url> --robot-puerto /dev/tty.Makeblock-ELETSPP

Necesita pyserial, que ya está en el proyecto.
"""

import time


class RobotMac:
    def __init__(self, puerto: str, baudios: int = 115200):
        self.puerto = puerto
        self.baudios = baudios
        self.serie = None

    def conectar(self):
        try:
            import serial
        except ImportError as error:  # pragma: no cover - depende del entorno
            raise RuntimeError("Falta pyserial: corre 'uv add pyserial'") from error

        print(f"Abriendo {self.puerto} a {self.baudios} baudios...")
        self.serie = serial.Serial(self.puerto, self.baudios, timeout=1)
        time.sleep(2)  # el módulo Bluetooth tarda un momento en quedar listo
        print("Conexión establecida")

    def _enviar(self, comando: str):
        if self.serie is None:
            raise RuntimeError("El robot no está conectado")

        self.serie.write(comando.encode("utf-8"))
        print(f"Comando enviado: {comando}")
        time.sleep(0.1)

    def adelante(self):
        self._enviar("w")

    def atras(self):
        self._enviar("s")

    def izquierda(self):
        self._enviar("a")

    def derecha(self):
        self._enviar("d")

    def parar(self):
        self._enviar("x")

    def cerrar(self):
        if self.serie is not None:
            self.serie.close()
            self.serie = None
            print("Conexión cerrada")

"""Enviar las decisiones al mBot real, por Bluetooth.

Traduce una `Decision` a los comandos del firmware del profesor
(`actuadores_arduino/arduinoFinal.ino` de su repositorio). **Nosotros no
tocamos el Arduino**: solo mandamos caracteres.

Lo que hace el firmware con cada carácter:

| Carácter | Qué hace | Cuánto dura |
|---|---|---|
| `w` | adelante | 100 ms y **se detiene solo** |
| `s` | atrás | 100 ms y se detiene solo |
| `a` | giro a la izquierda | 30 ms y se detiene solo |
| `d` | giro a la derecha | 30 ms y se detiene solo |
| `x` | detener | inmediato |

**Esto es lo más importante de todo el archivo:** los comandos son *pulsos*,
no estados. El robot no "queda andando": avanza 100 ms y para. Para que se
mueva de verdad hay que mandarle `w` una y otra vez.

De ahí salen las dos decisiones de diseño de este módulo:

1. **Cadencia fija (`ritmo_hz`, 10 por defecto).** El Arduino se bloquea
   100 ms en cada `w`, así que más de ~10 comandos por segundo solo llenan
   el buffer del puerto serie y el robot termina ejecutando órdenes viejas.
   La visión puede correr a 30 fps; los comandos salen a 10 Hz con la última
   decisión disponible.
2. **El giro se reparte en pulsos.** Un giro de 30 ms es un empujoncito. En
   vez de mandar "gire mucho", se acumula la magnitud del giro y se manda un
   pulso de giro cuando el acumulado pasa de 1; el resto del tiempo se manda
   `w`. Con giro 0.3 salen 3 pulsos de giro de cada 10, con 1.0 salen todos.
   Es control proporcional con los pulsos que el firmware permite.

Uso desde main.py:

    uv run main.py --fuente <url> --robot --robot-mac 00:1B:10:21:2C:1B
    uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --robot-simulado
"""

from __future__ import annotations

import time

from .tipos import Accion, Decision

ADELANTE = "w"
ATRAS = "s"
IZQUIERDA = "a"
DERECHA = "d"
PARAR = "x"


class CanalSimulado:
    """Imprime los comandos en vez de enviarlos. Para probar sin robot."""

    def __init__(self, silencioso: bool = False) -> None:
        self.silencioso = silencioso
        self.enviados: list[str] = []

    def abrir(self) -> None:
        if not self.silencioso:
            print("[robot simulado] listo")

    def enviar(self, comando: str) -> None:
        self.enviados.append(comando)

        if not self.silencioso:
            print(f"[robot simulado] {comando}")

    def cerrar(self) -> None:
        if not self.silencioso:
            print(f"[robot simulado] cerrado ({len(self.enviados)} comandos)")


class CanalBluetooth:
    """Socket Bluetooth RFCOMM, igual que el ejemplo del profesor.

    Funciona en Linux y en Windows. **En macOS no**: el módulo socket de
    Python no trae `AF_BLUETOOTH` en Darwin. Compruébalo con:

        python3 -c "import socket; print(hasattr(socket, 'AF_BLUETOOTH'))"

    Si sale False, empareja el mBot por Bluetooth y usa `CanalSerial`, que
    habla por el puerto /dev/tty.* que crea macOS al emparejarlo.
    """

    def __init__(self, mac: str, puerto: int = 1) -> None:
        self.mac = mac
        self.puerto = puerto
        self.socket = None

    def abrir(self) -> None:
        import socket

        if not hasattr(socket, "AF_BLUETOOTH"):
            raise RuntimeError(
                "Este sistema no expone AF_BLUETOOTH (le pasa a macOS). "
                "Empareja el robot y usa el canal serial: --robot-puerto /dev/tty.<nombre>"
            )

        self.socket = socket.socket(
            socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM
        )
        print(f"Conectando al robot {self.mac}...")
        self.socket.connect((self.mac, self.puerto))
        print("Robot conectado")

    def enviar(self, comando: str) -> None:
        if self.socket is None:
            raise RuntimeError("El robot no está conectado")

        self.socket.sendall(comando.encode("utf-8"))

    def cerrar(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None
            print("Robot desconectado")


class CanalSerial:
    """Puerto serie Bluetooth (SPP). Es la vía en macOS.

    Al emparejar el mBot, macOS crea un dispositivo /dev/tty.<nombre>. Por ahí
    se mandan exactamente los mismos caracteres.

        ls /dev/tty.* | grep -i makeblock

    Necesita pyserial (`uv add pyserial`).
    """

    def __init__(self, puerto: str, baudios: int = 115200) -> None:
        self.puerto = puerto
        self.baudios = baudios
        self.serie = None

    def abrir(self) -> None:
        try:
            import serial
        except ImportError as error:  # pragma: no cover - depende del entorno
            raise RuntimeError("Falta pyserial: corre 'uv add pyserial'") from error

        print(f"Abriendo {self.puerto} a {self.baudios} baudios...")
        self.serie = serial.Serial(self.puerto, self.baudios, timeout=1)
        time.sleep(2)  # el módulo Bluetooth tarda un momento en quedar listo
        print("Robot conectado")

    def enviar(self, comando: str) -> None:
        if self.serie is None:
            raise RuntimeError("El robot no está conectado")

        self.serie.write(comando.encode("utf-8"))

    def cerrar(self) -> None:
        if self.serie is not None:
            self.serie.close()
            self.serie = None
            print("Robot desconectado")


class ActuadorRobot:
    """Convierte decisiones en pulsos para el mBot, a un ritmo controlado.

    Args:
        canal: por dónde salen los comandos (bluetooth, serial o simulado).
        ritmo_hz: cuántos comandos por segundo como máximo. El firmware se
            bloquea 100 ms en cada `w`, así que subir de 10 solo acumula
            retraso.
        avanzar_al_girar: si es True, después de un pulso de giro también se
            manda `w`. Hace el recorrido más rápido pero las curvas más
            abiertas.
    """

    def __init__(self, canal, ritmo_hz: float = 10.0, avanzar_al_girar: bool = False) -> None:
        self.canal = canal
        self.intervalo = 1.0 / ritmo_hz if ritmo_hz > 0 else 0.0
        self.avanzar_al_girar = avanzar_al_girar
        self.acumulado_de_giro = 0.0
        self._ultimo_envio = 0.0
        self._detenido = False
        self.canal.abrir()

    def comandos_para(self, decision: Decision) -> list[str]:
        """Decide qué caracteres mandar en este tick. Sin efectos: fácil de probar."""
        if decision.accion is Accion.PARAR:
            self.acumulado_de_giro = 0.0
            return [PARAR]

        if decision.accion is Accion.RECTO:
            self.acumulado_de_giro = 0.0
            return [ADELANTE]

        # Giro proporcional repartido en pulsos: se acumula la magnitud y se
        # gasta un pulso cada vez que el acumulado pasa de 1.
        self.acumulado_de_giro += abs(decision.giro)

        if self.acumulado_de_giro < 1.0:
            # Todavía no toca girar: se sigue avanzando, salvo que estemos
            # buscando la línea, donde avanzar a ciegas es peor.
            return [] if decision.accion is Accion.BUSCAR else [ADELANTE]

        self.acumulado_de_giro -= 1.0
        giro = DERECHA if decision.giro > 0 else IZQUIERDA

        if decision.accion is Accion.BUSCAR:
            return [giro]

        return [giro, ADELANTE] if self.avanzar_al_girar else [giro]

    def aplicar(self, decision: Decision, contexto: dict | None = None) -> None:
        ahora = time.monotonic()

        # Un PARAR se manda siempre, sin esperar el ritmo: frenar es urgente.
        urgente = decision.accion is Accion.PARAR and not self._detenido

        if not urgente and ahora - self._ultimo_envio < self.intervalo:
            return

        self._ultimo_envio = ahora
        self._detenido = decision.accion is Accion.PARAR

        for comando in self.comandos_para(decision):
            self.canal.enviar(comando)

    def cerrar(self) -> None:
        """Siempre deja el robot quieto antes de soltar la conexión."""
        try:
            self.canal.enviar(PARAR)
        except Exception:  # noqa: BLE001 - al cerrar, un fallo aquí no importa
            pass

        self.canal.cerrar()


def crear_canal(mac: str | None = None, puerto_serie: str | None = None,
                simulado: bool = False):
    """Elige el canal según lo que se haya pedido por línea de comandos."""
    if simulado:
        return CanalSimulado()

    if puerto_serie:
        return CanalSerial(puerto_serie)

    if mac:
        return CanalBluetooth(mac)

    raise ValueError("Para hablarle al robot hace falta --robot-mac o --robot-puerto")

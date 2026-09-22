"""Contratos entre los módulos del pipeline.

Mientras estos tipos no cambien, cada quien puede trabajar en su módulo
aunque el de los demás todavía no esté listo. Cambiarlos se acuerda entre
los tres.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Accion(str, Enum):
    """Lo que el cerebro le pide al robot en este frame."""

    RECTO = "RECTO"
    IZQUIERDA = "IZQUIERDA"
    DERECHA = "DERECHA"
    PARAR = "PARAR"
    BUSCAR = "BUSCAR"


class EstadoRobot(str, Enum):
    """En qué situación está el robot."""

    SIGUIENDO = "SIGUIENDO"
    DETENIDO = "DETENIDO"
    BUSCANDO = "BUSCANDO"


@dataclass(frozen=True)
class ResultadoLinea:
    """Lo que devuelve `linea.detectar`.

    desviacion: -1.0 (línea pegada a la izquierda) a +1.0 (a la derecha),
    0.0 = centrada. Va normalizada para que el control no dependa de la
    resolución de la cámara.
    """

    detectada: bool = False
    centro_x: int | None = None
    desviacion: float = 0.0
    area: float = 0.0
    mascara: Any | None = None


@dataclass(frozen=True)
class ResultadoSenal:
    """Lo que devuelve `senales.detectar`.

    tipo: "PARE", "SIGA" o None. `area` sirve como medida de distancia:
    entre más grande el octágono, más cerca está la señal.
    """

    tipo: str | None = None
    area: float = 0.0
    centro: tuple[int, int] | None = None
    vertices: int = 0
    contorno: Any | None = None
    mascara: Any | None = None


@dataclass(frozen=True)
class Decision:
    """Lo que devuelve `control.decidir`.

    giro: -1.0 (girar todo a la izquierda) a +1.0 (todo a la derecha).
    razon: texto para el HUD y para poder explicar en la sustentación por
    qué el robot hizo lo que hizo.
    """

    accion: Accion
    giro: float = 0.0
    razon: str = ""


@dataclass
class Estado:
    """Memoria entre frames. Es mutable a propósito: el control la actualiza."""

    estado: EstadoRobot = EstadoRobot.SIGUIENDO
    ultimo_giro: float = 0.0
    frames_sin_linea: int = 0
    frames_con_senal: int = 0
    senal_candidata: str | None = None
    detenido_hasta: float = 0.0
    ultima_senal_obedecida: float = -999.0

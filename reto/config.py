"""Todos los parámetros del algoritmo en un solo lugar.

Ningún número mágico dentro de la lógica: si hay que calibrar el día de la
carrera, se toca este archivo o un JSON aparte, no el código.

    uv run main.py --config config_pista.json
"""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path

# Rango de color en HSV de OpenCV: H 0-179, S 0-255, V 0-255.
Rango = tuple[tuple[int, int, int], tuple[int, int, int]]


@dataclass
class Config:
    # --- Preprocesamiento -------------------------------------------------
    ancho_proceso: int = 480           # se redimensiona a este ancho: menos cómputo, más FPS
    kernel_gauss: int = 5              # impar; suaviza antes de segmentar (clase 3)

    # --- Línea guía -------------------------------------------------------
    # Franjas del frame, en fracción del alto (0.0 arriba, 1.0 abajo).
    roi_linea_cercana: tuple[float, float] = (0.70, 1.00)
    roi_linea_lejana: tuple[float, float] = (0.50, 0.70)
    # Por defecto: línea oscura sobre pista clara (V bajo). Calibrar con K-Means.
    hsv_linea: Rango = ((0, 0, 0), (179, 255, 80))
    area_minima_linea: int = 300
    kernel_morfologico: int = 3
    iteraciones_apertura: int = 1
    iteraciones_cierre: int = 2

    # --- Señales ----------------------------------------------------------
    roi_senal: tuple[float, float] = (0.00, 0.70)
    # El rojo está en los dos extremos del círculo de H: necesita dos rangos.
    hsv_rojo_bajo: Rango = ((0, 120, 80), (10, 255, 255))
    hsv_rojo_alto: Rango = ((170, 120, 80), (179, 255, 255))
    hsv_verde: Rango = ((40, 80, 60), (85, 255, 255))
    area_minima_senal: int = 800       # también funciona como "está lo bastante cerca"
    precision_poligono: float = 0.03   # epsilon de approxPolyDP, como fracción del perímetro
    vertices_octagono: tuple[int, int] = (7, 9)
    relacion_aspecto_octagono: tuple[float, float] = (0.75, 1.30)
    circularidad_minima: float = 0.70
    frames_confirmacion_senal: int = 3  # tiene que verse en N frames seguidos

    # --- Control ----------------------------------------------------------
    zona_muerta: float = 0.12          # |desviación| menor que esto = seguir recto
    ganancia_giro: float = 1.2
    peso_linea_lejana: float = 0.3     # cuánto pesa la franja lejana (anticipar curvas)
    frames_para_buscar: int = 5        # frames sin línea antes de entrar a BUSCANDO
    segundos_pare: float = 3.0         # confirmar con el profesor
    espera_entre_senales: float = 5.0  # para no obedecer dos veces la misma señal
    siga_reanuda: bool = True          # un SIGA puede cortar la espera del PARE

    @classmethod
    def desde_json(cls, ruta: str | Path) -> "Config":
        """Carga una configuración de calibración; lo que no esté, queda por defecto."""
        datos = json.loads(Path(ruta).read_text(encoding="utf8"))
        conocidos = {f.name for f in fields(cls)}
        desconocidos = set(datos) - conocidos

        if desconocidos:
            raise ValueError(f"Parámetros que no existen en Config: {sorted(desconocidos)}")

        # Las tuplas vuelven de JSON como listas; se convierten.
        limpios = {k: (tuple(map(tuple, v)) if k.startswith("hsv") else v) for k, v in datos.items()}
        limpios = {
            k: (tuple(v) if isinstance(v, list) else v) for k, v in limpios.items()
        }
        return cls(**limpios)

    def guardar(self, ruta: str | Path) -> None:
        """Guarda la configuración actual, para dejar registro de una calibración."""
        datos = {f.name: getattr(self, f.name) for f in fields(self)}
        Path(ruta).write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf8")

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
    #
    # OJO con el encuadre de los videos del profesor: el celular va detrás del
    # carro, así que el carro ocupa el 40% inferior de la imagen y la pista se
    # ve ARRIBA. Por eso la franja "cercana" (la que hay que corregir ya) no es
    # el borde inferior, sino justo encima del carro. Medido en datos/frames/:
    # los píxeles oscuros de la línea están entre y=0.0 y y=0.6; más abajo es
    # el carro. Si cambia el montaje del celular, esto se recalibra.
    roi_linea_cercana: tuple[float, float] = (0.40, 0.58)
    roi_linea_lejana: tuple[float, float] = (0.18, 0.40)
    # Línea negra sobre piso claro: lo que la separa es el brillo (V), no el
    # tono. Medido en los frames: línea V≈45-90 con S baja, piso V≈200.
    hsv_linea: Rango = ((0, 0, 0), (179, 90, 110))
    area_minima_linea: int = 300
    kernel_morfologico: int = 3
    iteraciones_apertura: int = 1
    iteraciones_cierre: int = 2

    # --- Señales ----------------------------------------------------------
    # Solo la zona de la pista: deja fuera el carro, que trae naranja (pilas) y
    # cian (chasis) y se colaría como señal.
    roi_senal: tuple[float, float] = (0.00, 0.55)
    # El rojo está en los dos extremos del círculo de H: necesita dos rangos.
    # En los videos del profesor la señal roja cayó en el extremo alto
    # (H≈173-175, S≈193, V≈168). Las pilas del carro son H≈6-15: por eso el
    # rango bajo va angosto y la ROI deja el carro por fuera.
    hsv_rojo_bajo: Rango = ((0, 120, 80), (8, 255, 255))
    hsv_rojo_alto: Rango = ((165, 120, 80), (179, 255, 255))
    # Señal verde medida: H≈70, S≈130-200, V≈90-142. El límite inferior en 62
    # evita el verde amarillento del carro (H≈41-61).
    hsv_verde: Rango = ((62, 90, 60), (85, 255, 255))
    # Las señales de los videos dan 34.000-39.000 px cuando están cerca; con
    # 3.000 se alcanzan a ver desde más lejos, y luego se decide con el área
    # a partir de cuándo obedecer.
    area_minima_senal: int = 3000      # también funciona como "está lo bastante cerca"
    precision_poligono: float = 0.03   # epsilon de approxPolyDP, como fracción del perímetro
    vertices_octagono: tuple[int, int] = (7, 9)
    relacion_aspecto_octagono: tuple[float, float] = (0.75, 1.30)
    circularidad_minima: float = 0.70
    frames_confirmacion_senal: int = 3  # tiene que verse en N frames seguidos
    # Medido en los videos del profesor: sus señales dan 4-5 vértices y
    # circularidad 0.58-0.72 porque están inclinadas y a veces tapadas. Con
    # esto en True no se detectaría ninguna. La forma suma confianza
    # (ResultadoSenal.es_octagono), pero no descarta.
    exigir_octagono: bool = False

    # --- Control ----------------------------------------------------------
    zona_muerta: float = 0.12          # |desviación| menor que esto = seguir recto
    ganancia_giro: float = 1.2
    # Mezclar la franja lejana con la cercana lo probamos y EMPEORA con los
    # videos que tenemos: con 0.3 los saltos pasan de 12 a 16 y con 0.7 se
    # pierden 2 de las 5 recuperaciones. Las dos franjas ven cosas muy
    # distintas (diferencia media de 0.32) porque la linea es curva. Queda en
    # 0: la franja lejana se sigue calculando y sirve para la curvatura, pero
    # no entra en la desviacion hasta poder probarla en lazo cerrado.
    peso_linea_lejana: float = 0.0
    # Promedio de los ultimos N frames de desviacion. Medido: con 3 los
    # saltos bajan de 12 a 4 y el zigzag a la mitad. Con 5 quedan en 0 pero
    # son 167 ms de retraso a 30 fps, y el retraso no se puede medir con
    # video: se sube en la pista si el carro zigzaguea.
    suavizado_desviacion: int = 3
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

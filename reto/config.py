"""Todos los parámetros del algoritmo en un solo lugar.

Ningún número mágico dentro de la lógica: si hay que calibrar el día de la
carrera, se toca este archivo o un JSON aparte, no el código.

    uv run main.py --config config_pista.json
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, fields
from pathlib import Path

# Rango de color en HSV de OpenCV: H 0-179, S 0-255, V 0-255.
Rango = tuple[tuple[int, int, int], tuple[int, int, int]]


@dataclass
class Config:
    # --- Captura ----------------------------------------------------------
    tiempo_limite_camara_ms: int = 8000
    reintentos_camara: int = 5
    pausa_reconexion_s: float = 0.5
    fps_respaldo: float = 30.0
    # Giro que se aplica al frame antes de procesarlo, en grados: 0, 90, 180 o
    # 270. IP Camera Lite entrega la imagen segun como quede el celular en el
    # soporte, y el pipeline asume que la pista se ve "de frente".
    rotacion: int = 0

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
    ancho_maximo_linea: float = 0.50   # contorno más ancho (fracción de la ROI) = cinta transversal, se ignora
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
    relacion_aspecto_senal: tuple[float, float] = (0.4, 2.5)
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
    umbral_curvatura: float = 0.15     # diferencia entre franjas para mostrar la curva en el HUD
    # Promedio de los ultimos N frames de desviacion. Medido: con 3 los
    # saltos bajan de 12 a 4 y el zigzag a la mitad. Con 5 quedan en 0 pero
    # son 167 ms de retraso a 30 fps, y el retraso no se puede medir con
    # video: se sube en la pista si el carro zigzaguea.
    suavizado_desviacion: int = 3
    frames_para_buscar: int = 5        # frames sin línea antes de entrar a BUSCANDO
    segundos_pare: float = 3.0         # confirmar con el profesor
    espera_entre_senales: float = 5.0  # para no obedecer dos veces la misma señal
    siga_reanuda: bool = True          # un SIGA puede cortar la espera del PARE

    def __post_init__(self) -> None:
        self.validar()
        # JSON representa las tuplas como listas; el resto del código recibe
        # siempre la misma estructura, sin importar cómo se creó Config.
        for campo in fields(self):
            valor = getattr(self, campo.name)
            if campo.name.startswith("hsv_"):
                setattr(self, campo.name, tuple(tuple(limite) for limite in valor))
            elif isinstance(valor, list):
                setattr(self, campo.name, tuple(valor))

    def validar(self) -> None:
        """Rechaza una calibración inválida antes de abrir cámara o procesar."""
        enteros_positivos = (
            "ancho_proceso", "kernel_gauss", "kernel_morfologico",
            "frames_confirmacion_senal", "frames_para_buscar", "tiempo_limite_camara_ms",
        )
        enteros_no_negativos = (
            "area_minima_linea", "area_minima_senal", "iteraciones_apertura",
            "iteraciones_cierre", "suavizado_desviacion", "reintentos_camara",
        )
        for nombre in enteros_positivos + enteros_no_negativos:
            minimo = 1 if nombre in enteros_positivos else 0
            _validar_numero(nombre, getattr(self, nombre), minimo, entero=True)
        if self.kernel_gauss % 2 == 0:
            raise ValueError("kernel_gauss debe ser impar")
        if self.rotacion not in (0, 90, 180, 270):
            raise ValueError("rotacion debe ser 0, 90, 180 o 270")

        for nombre in ("segundos_pare", "espera_entre_senales", "ganancia_giro", "pausa_reconexion_s"):
            _validar_numero(nombre, getattr(self, nombre), 0)
        for nombre in ("zona_muerta", "peso_linea_lejana", "circularidad_minima"):
            _validar_numero(nombre, getattr(self, nombre), 0, 1)
        _validar_numero("umbral_curvatura", self.umbral_curvatura, 0, 2)
        _validar_numero("fps_respaldo", self.fps_respaldo, 0)
        if self.fps_respaldo == 0:
            raise ValueError("fps_respaldo debe ser mayor que cero")
        _validar_numero("precision_poligono", self.precision_poligono, 0, 1)
        if self.precision_poligono == 0:
            raise ValueError("precision_poligono debe ser mayor que cero")

        for nombre in ("siga_reanuda", "exigir_octagono"):
            if not isinstance(getattr(self, nombre), bool):
                raise ValueError(f"{nombre} debe ser true o false")

        for nombre in ("roi_linea_cercana", "roi_linea_lejana", "roi_senal"):
            inicio, fin = _validar_par(nombre, getattr(self, nombre))
            _validar_numero(nombre, inicio, 0, 1)
            _validar_numero(nombre, fin, 0, 1)
            if inicio >= fin:
                raise ValueError(f"{nombre} debe cumplir 0 <= inicio < fin <= 1")

        for nombre, minimo, entero in (("vertices_octagono", 3, True),
                                        ("relacion_aspecto_octagono", 0, False),
                                        ("relacion_aspecto_senal", 0, False)):
            inferior, superior = _validar_par(nombre, getattr(self, nombre))
            _validar_numero(nombre, inferior, minimo, entero=entero)
            _validar_numero(nombre, superior, minimo, entero=entero)
            if inferior > superior or inferior == 0:
                raise ValueError(f"{nombre} debe tener límites positivos y ordenados")

        for nombre in ("hsv_linea", "hsv_rojo_bajo", "hsv_rojo_alto", "hsv_verde"):
            inferior, superior = _validar_par(nombre, getattr(self, nombre))
            for limite in (inferior, superior):
                if not isinstance(limite, (tuple, list)) or len(limite) != 3:
                    raise ValueError(f"{nombre} necesita dos ternas HSV")
            for canal, maximo in enumerate((179, 255, 255)):
                _validar_numero(nombre, inferior[canal], 0, maximo, entero=True)
                _validar_numero(nombre, superior[canal], 0, maximo, entero=True)
                if inferior[canal] > superior[canal]:
                    raise ValueError(f"{nombre} necesita límites HSV ordenados")

    @classmethod
    def desde_json(cls, ruta: str | Path) -> "Config":
        """Carga una configuración de calibración; lo que no esté, queda por defecto."""
        datos = json.loads(Path(ruta).read_text(encoding="utf8"))
        if not isinstance(datos, dict):
            raise ValueError("La configuración JSON debe ser un objeto de parámetros")
        conocidos = {f.name for f in fields(cls)}
        desconocidos = set(datos) - conocidos

        if desconocidos:
            raise ValueError(f"Parámetros que no existen en Config: {sorted(desconocidos)}")

        return cls(**datos)

    def guardar(self, ruta: str | Path) -> None:
        """Guarda la configuración actual, para dejar registro de una calibración."""
        self.validar()
        datos = {f.name: getattr(self, f.name) for f in fields(self)}
        Path(ruta).write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf8")


def _validar_numero(nombre: str, valor, minimo: float, maximo: float | None = None,
                    *, entero: bool = False) -> None:
    tipo_correcto = type(valor) is int if entero else type(valor) in (int, float)
    if not tipo_correcto or not math.isfinite(valor):
        tipo = "entero" if entero else "número finito"
        raise ValueError(f"{nombre} debe ser un {tipo}")
    if valor < minimo or (maximo is not None and valor > maximo):
        limite = f"entre {minimo} y {maximo}" if maximo is not None else f">= {minimo}"
        raise ValueError(f"{nombre} debe ser {limite}")


def _validar_par(nombre: str, valor) -> tuple:
    if not isinstance(valor, (tuple, list)) or len(valor) != 2:
        raise ValueError(f"{nombre} debe tener exactamente dos límites")
    return tuple(valor)

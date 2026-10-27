"""Clasificación de las señales del Reto 2 con una CNN (transfer learning).

La localización es híbrida: `senales.proponer_candidatos` propone regiones por
color y aquí se clasifica cada recorte con el modelo de Keras entrenado en
clase (material en `5_cnns/`, dataset en `datos/senales/`). Así la CNN decide
*qué* señal es y el color solo decide *dónde* mirar.

El modelo usa las arquitecturas de `keras.applications` (VGG16/19, MobileNet,
ResNet50, DenseNet121) con una cabeza propia, congeladas sobre ImageNet. Por eso
en inferencia hay que replicar el mismo `preprocess_input` y el mismo tamaño de
entrada con que se entrenó, y el orden de clases es el `sorted()` de las
carpetas del dataset (igual que en `5_cnns/cnn_trainer.py`).

El import de `keras` va dentro de las funciones: es pesado y no debe cargarse
cuando se usa el detector por color.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .config import Config
from .senales import proponer_candidatos
from .tipos import ResultadoSenal

_modelos: dict[str, object] = {}  # caché por ruta: el modelo se carga una sola vez


def _preproceso(nombre: str):
    """Función de preprocesamiento de la arquitectura, igual que en clase."""
    from keras import applications

    return {
        "MobileNet": applications.mobilenet.preprocess_input,
        "ResNet50": applications.resnet50.preprocess_input,
        "VGG16": applications.vgg16.preprocess_input,
        "VGG19": applications.vgg19.preprocess_input,
        "DenseNet121": applications.densenet.preprocess_input,
    }[nombre]


def modelo_disponible(config: Config) -> bool:
    """Indica si el archivo del modelo existe, sin cargarlo."""
    return Path(config.ruta_modelo_senales).is_file()


def cargar_modelo(config: Config):
    """Carga el modelo `.keras` una sola vez. Falla claro si no existe."""
    ruta = config.ruta_modelo_senales

    if ruta in _modelos:
        return _modelos[ruta]

    if not Path(ruta).is_file():
        raise FileNotFoundError(
            f"No existe el modelo de señales en '{ruta}'. Entrénalo con el pipeline "
            f"de 5_cnns sobre datos/senales/ y copia el .keras elegido ahí "
            f"(ver docs/decisiones/0010-clasificador-cnn.md)."
        )

    from keras import models

    modelo = models.load_model(ruta)
    _modelos[ruta] = modelo
    return modelo


def clasificar(recorte, config: Config) -> tuple[str, float]:
    """Clase y confianza del recorte BGR recibido (una de `config.clases_senales`)."""
    ancho, alto = config.tamano_entrada_senales
    imagen = cv2.resize(recorte, (ancho, alto)).astype(np.float32)
    imagen = _preproceso(config.clase_modelo_senales)(imagen)
    probabilidades = cargar_modelo(config).predict(imagen[None, ...], verbose=0)[0]
    indice = int(np.argmax(probabilidades))
    return config.clases_senales[indice], float(probabilidades[indice])


def _recorte(roi, caja: tuple[int, int, int, int], margen: float):
    """Recorta la caja con un margen, sin salirse de la ROI."""
    x, y, ancho, alto = caja
    mx = int(ancho * margen)
    my = int(alto * margen)
    x1 = max(0, x - mx)
    y1 = max(0, y - my)
    x2 = min(roi.shape[1], x + ancho + mx)
    y2 = min(roi.shape[0], y + alto + my)
    return roi[y1:y2, x1:x2]


def detectar(roi, config: Config) -> ResultadoSenal:
    """Clasifica los candidatos de la ROI y devuelve el de mayor confianza.

    Devuelve una señal vacía si no hay candidatos o si ninguno supera
    `config.confianza_minima_senal`.
    """
    candidatos, mascara = proponer_candidatos(roi, config)
    mejor = None

    for candidato in candidatos:
        recorte = _recorte(roi, candidato["caja"], config.margen_candidato_senal)

        if recorte.size == 0:
            continue

        tipo, confianza = clasificar(recorte, config)

        if confianza < config.confianza_minima_senal:
            continue

        if mejor is None or confianza > mejor[2]:
            mejor = (candidato, tipo, confianza)

    if mejor is None:
        return ResultadoSenal(mascara=mascara)

    candidato, tipo, confianza = mejor

    return ResultadoSenal(
        tipo=tipo,
        area=candidato["area"],
        centro=candidato["centro"],
        contorno=candidato["contorno"],
        mascara=mascara,
        confianza=confianza,
    )

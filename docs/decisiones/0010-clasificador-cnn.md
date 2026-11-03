# 0010 — Reconocer las señales del Reto 2 con una CNN

- **Fecha:** 2026-10-27
- **Estado:** propuesta
- **Deciden:** Santiago / Daniel / Juan David

## Contexto
El Reto 2 pide reconocer cuatro señales (PARE, SIGA, ZONA ESCOLAR y VELOCIDAD
60) con las CNN vistas en clase, y esta condición reemplaza la restricción del
Reto 1 que prohibía el aprendizaje profundo. El material de clase (`cnn/`)
trae un pipeline de transfer learning con `keras.applications` (VGG16/19,
MobileNet, ResNet50, DenseNet121) que espera una carpeta de imágenes por clase,
pero **solo clasifica**: no dice dónde está la señal en el frame. El proyecto
principal ya sabe *localizar* la señal en la ROI (`senales.py`, por color y
contorno) y decidir con ella (`control.py`).

## Decisión
- **Localización híbrida:** el color propone regiones candidatas (una sola
  máscara de saturación en `senales.proponer_candidatos`) y la CNN clasifica el
  recorte de cada caja. La CNN decide *qué* señal es; el color solo decide
  *dónde* mirar. Así se reutiliza lo que ya funcionaba y hay una sola pasada de
  CNN por candidato.
- **Módulo nuevo `reto/clasificador.py`** con funciones planas: carga perezosa
  del modelo (el import de `keras` va dentro de las funciones), réplica del
  `preprocess_input` y del tamaño de entrada del entrenamiento, y
  `detectar(roi, config) -> ResultadoSenal`.
- **El detector es configurable** con `detector_senales`: `"cnn"` (por defecto)
  o `"color"` (el del Reto 1). Mientras no exista el `.keras`, el pipeline avisa
  una vez y cae al detector por color, para no romper la evaluación sobre los
  clips viejos.
- **El modelo corre en el proyecto principal**: se agrega `tensorflow`
  (2.22.0rc0, el que funciona en Python 3.14) y se carga el `.keras` en proceso.
  El archivo vive en `modelos/senales.keras` y no se sube al repo.
- `ResultadoSenal` gana `confianza` (por defecto `0.0`), compatible con el
  código existente. El control no cambia en esta tanda: las clases nuevas llegan
  sin romper nada hasta implementar sus comportamientos.

Técnicas: la localización usa las del Reto 1 (ROI y HSV, clase 1; `inRange`,
clase 2; morfología, contornos y `boundingRect`, clase 3). La clasificación usa
las CNN de clase (Reto 2).

## Alternativas consideradas
- **Clasificar toda la `roi_senal`** en vez de recortes: más simple, pero la
  señal debe dominar el recorte y el fondo (barra, pista) confunde; el dataset
  son recortes, no escenas.
- **Escanear la ROI por ventanas**: más robusto ante posiciones arbitrarias,
  pero multiplica el cómputo por frame y choca con el objetivo de tiempo real.
- **Inferencia en el venv de `cnn`** (servicio/proceso aparte): evita la
  dependencia pesada, pero agrega latencia y complejidad de comunicación.
- **Detector de objetos (YOLO/SSD)**: fuera de las arquitecturas de clase y de
  las técnicas permitidas.

## Resultados

**Pendiente de reentrenar.** Una primera ronda (2026-10-27) se hizo con 178
recortes sacados de otro conjunto de imágenes; ese conjunto y sus resultados se
retiraron del repo (siguen en el historial de Git, commit `6642a4f^`).

Dataset vigente: las fotos tomadas en la pista, en `reto_2/cnn/dataset/`
(0 PARE, 1 SIGA, 2 ZONA_ESCOLAR, 3 VELOCIDAD_60). Entrenamiento con
`cnn/cnn_trainer.py`, directo (`cnn/main.py`) o con `tools/entrenar_senales.py`.
Las particiones train/val/test son estratificadas con `seed=42`, iguales para
todas las arquitecturas, y cada experimento deja `particiones.csv` con el
reparto. Los dos mejores modelos se eligen por `val_loss` y el elegido se copia
a `modelos/senales.keras`.

## Consecuencias
- Falta lo demás del Reto 2: entrenar y comparar arquitecturas, elegir los dos
  mejores, entrenar una clase "fondo" para descartar candidatos falsos, y los
  comportamientos de velocidad (ZONA ESCOLAR reduce, VELOCIDAD 60 sube).
- `tensorflow` añade ~700 MB y arranque lento; el import es perezoso para que el
  modo `"color"` no lo cargue.
- La localización por color puede proponer falsos candidatos (objetos de color
  en la escena); se filtran con `confianza_minima_senal` y
  `frames_confirmacion_senal`.
- Se toca `tipos.py` (contrato compartido), `senales.py` y `pipeline.py`
  (frente de Daniel): hay que avisarle al equipo.

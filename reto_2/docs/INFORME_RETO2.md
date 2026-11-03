# Informe: rama `reto2` vs `main`

- Base común: `2e93b71` (main). `main` ya al día tras `git pull`.
- 2 commits nuevos, autor SantiagoBedoyaU, 2026-10-27: `bb543af cnn`, `76c41c5 training models`.
- 1024 archivos cambiados (+3189 / −38); la mayoría son imágenes del dataset.

## Qué hay de nuevo

| Área | Cambio |
|---|---|
| `reto/clasificador.py` | Nuevo. Carga perezosa del modelo Keras, `preprocess_input`, `detectar(roi, config) -> ResultadoSenal`. |
| `reto/pipeline.py` | `detectar_senal()`: usa CNN; si no existe `modelos/senales.keras`, avisa una vez y cae al detector por color. |
| `reto/senales.py` | `proponer_candidatos`: máscara rojo/verde/amarillo propone regiones; la CNN clasifica el recorte. |
| `reto/config.py` | Opciones `detector_senales` (`cnn`/`color`), `ruta_modelo_senales`, `clase_modelo_senales` (MobileNet), `clases_senales`, `confianza_minima_senal` (0.6), `max_candidatos_senal`, `hsv_amarillo`; `hsv_verde` ampliado a H≤95. |
| `reto/tipos.py` | `ResultadoSenal.confianza` (default 0.0). |
| `reto/overlay.py` | Ajustes para nuevas clases. |
| `cnn/` | Material de clase (trainer, dataset, README). |
| `tools/` | `preparar_senales.py`, `entrenar_senales.py`. |
| `datos/senales/` | 178 recortes: PARE 43, SIGA 45, VELOCIDAD_60 45, ZONA_ESCOLAR 45. |
| `modelos/entrenamiento/senales_reto2/` | Matrices de confusión, curvas de pérdida, reportes y `resultados.csv` de 5 arquitecturas. |
| `tests/` | `test_clasificador.py` nuevo; `test_integracion.py` ajustado. |
| `docs/` | `reto/reto-2.md`, ADR `0010-clasificador-cnn.md`, `arquitectura.md`. |
| Dependencias | `tensorflow` en `pyproject.toml` y `uv.lock` (~700 MB). |

## Resultados de entrenamiento (test, 18 imágenes)

| Modelo | val_loss | Accuracy | F1 macro |
|---|---|---|---|
| ResNet50 | 0.0055 | 1.00 | 1.00 |
| MobileNet (integrado) | 0.0079 | 1.00 | 1.00 |
| VGG16 | 0.0349 | 1.00 | 1.00 |
| VGG19 | 0.0400 | 1.00 | 1.00 |
| DenseNet121 | 0.0786 | 1.00 | 1.00 |

- Dos mejores por `val_loss`: ResNet50 y MobileNet. Elegido MobileNet por ser el más liviano.
- El `.keras` no se sube al repo; se copia a `modelos/senales.keras`.

## Hallazgos técnicos

- Entrenamiento usa RGB; OpenCV usa BGR. Sin convertir, PARE se clasificaba como SIGA.
- Verde de SIGA (H≈86-87) caía fuera del rango anterior (62-85).
- Anillo rojo de VELOCIDAD_60 desaparecía con apertura morfológica; ahora se dilata y cierra.
- Máscara de cualquier color saturado enganchaba el chasis azul; se limita a rojo/verde/amarillo.

## Pendiente / riesgos

- Accuracy 1.00 no es medida fuerte: test pequeño y fotos casi idénticas entre particiones (el reto lo prohíbe). Falta separar por tandas.
- `control.py` sin cambios: faltan los comportamientos ZONA ESCOLAR (reducir velocidad) y VELOCIDAD 60 (aumentar).
- Falta clase "fondo" para descartar candidatos falsos.
- Toca `tipos.py`, `senales.py` y `pipeline.py` (contratos compartidos): avisar al equipo.
- Falta interpretación de confusiones y tiempo de respuesta exigidas como entregable.

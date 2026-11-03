# Estructura de carpetas y relación con los retos

Corte: commit `2e93b71` (FINAL) = **fin del Reto 1**. Todo lo marcado **R2** se agregó después.
Leyenda: **R1** = Reto 1 · **R2** = Reto 2 · **Ambos** · **Apoyo** = no es entregable · **Basura** = no versionado / sobra.

## Raíz

| Ruta | Qué es | Reto |
|---|---|---|
| `main.py` | Entrada: corre el cerebro (cámara → decisión) | R1 (sin cambios en R2) |
| `reto/` | Paquete del cerebro (ver abajo) | Ambos |
| `configs/` | JSON de calibración (`video1`, `video1-kmeans`, `simulador`) | R1 |
| `config_celular.json` | Config de cámara del celular | R1 |
| `datos/` | Clips, frames, señales (ver abajo) | Ambos |
| `docs/` | Documentación, decisiones, rúbrica, diagramas | Ambos |
| `notebooks/` | 4 notebooks de fundamentación (color, ops, K-Means) | R1 |
| `tools/` | Scripts de calibración, evaluación, entrenamiento | Ambos |
| `tests/` | Pruebas automáticas | Ambos |
| `simulacion/index.html` | Simulador visual web | R1 |
| `modelos/` | Resultados de entrenamiento CNN (5 arquitecturas) | **R2** |
| `5_cnns/` | Código de clase de CNN + dataset MNIST-like (10 clases × ~80) | **R2** (material base) |
| `Reto-2.docx` | Enunciado del Reto 2 | **R2** |
| `INFORME_RETO2.md` | Informe Reto 2 (sin commitear) | **R2** |
| `README.md`, `AGENTS.md`, `CLAUDE.md`, `MEJORAS.md` | Guías del repo | Ambos |
| `pyproject.toml`, `uv.lock`, `.python-version` | Entorno | Ambos |
| `Captura de pantalla 2026-09-29 101903.png` | Captura suelta | Basura |
| `figuras/` | Vacía | Basura |
| `salida/poster/` | Póster (sin versionar) | Apoyo |
| `temp/`, `scripts/`, `vid/`, `test_/` | Pruebas sueltas, videos crudos, pruebas del robot (ignorados por git) | Basura / Apoyo |

## `reto/` — el cerebro

| Archivo | Función | Reto |
|---|---|---|
| `tipos.py`, `config.py` | Contratos y umbrales | Ambos (R2 los modificó) |
| `camara.py` | Captura de frames | R1 |
| `linea.py` | Detección de línea guía | R1 |
| `control.py` | Máquina de estados (sin OpenCV) | R1 |
| `senales.py` | Señales PARE/SIGA por color y forma | R1 (queda como respaldo en R2) |
| `clasificador.py` | CNN para 4 señales | **R2** |
| `pipeline.py`, `overlay.py` | Integración y dibujo | Ambos (R2 los modificó) |
| `actuador.py`, `actuador_robot.py`, `simulador.py` | Salida: consola/CSV/simulador/robot | R1 |
| `Robot.py`, `Robot_mac.py` | Driver del robot físico | R1 |

## `datos/`

| Carpeta | Contenido | Reto |
|---|---|---|
| `clips/` | Videos livianos de prueba (`rutaIdeal`, `desacarrilamiento`) | R1 |
| `frames/` | Frames extraídos de esos clips | R1 |
| `senales/` | Dataset de recortes: PARE, SIGA, VELOCIDAD_60, ZONA_ESCOLAR (~45 c/u) | **R2** |
| `grabaciones/`, `pruebas/` | Salidas de corridas (ignorado) | Apoyo |

## `tools/`

| Script | Reto |
|---|---|
| `calibrar*.py`, `barrido.py`, `evaluar*.py`, `probar_*.py`, `preparar_videos.py`, `notebooks.py`, `sync_apuntes.py` | R1 |
| `preparar_senales.py` (arma dataset) , `entrenar_senales.py` (entrena 5 CNN) | **R2** |

## `tests/`

| Archivo | Reto |
|---|---|
| `test_core.py`, `test_congelar.py`, `test_herramientas.py` | R1 |
| `test_integracion.py` | R1 (ampliado en R2) |
| `test_clasificador.py` | **R2** |

## `docs/`

| Ruta | Reto |
|---|---|
| `reto/` : `Reto-1.docx`, `Rubrica-Reto-1.xlsx`, `especificacion.md`, `rubrica.md`, `tecnicas-permitidas.md` | R1 |
| `reto/reto-2.md` | **R2** |
| `decisiones/0001`–`0009` + `plantilla.md` (ADRs) | R1 |
| `decisiones/0010-clasificador-cnn.md` | **R2** |
| `arquitectura.md` | Ambos (R2 la editó) |
| `algoritmo.md`, `bitacora.md`, `estado-vs-rubrica.md`, `flujo-de-pruebas.md`, `guion-sustentacion.md`, `plan-reto.md`, `preguntas-del-profe.md`, `resumen-proyecto.md`, `robot.md` | R1 |
| `clases/` (apuntes clase1–4 + img) | Apoyo del curso |
| `diagramas/`, `media/` (dot, png, svg, demo mp4) | R1 |

## `modelos/`

`modelos/entrenamiento/senales_reto2/{DenseNet121,MobileNet,ResNet50,VGG16,VGG19}/` — 3 archivos por arquitectura. **R2.**

## Problemas detectados

1. Raíz sucia: `Captura de pantalla…png`, `figuras/` vacía, `Reto-2.docx` suelto (los de R1 viven en `docs/reto/`).
2. `5_cnns/` es un proyecto aparte (propio `pyproject.toml`, `uv.lock`, `main.py`) con 800 imágenes de dataset dentro del repo; `AGENTS.md` lo referencia como `@5_cnns/`.
3. `5_cnns/src/5_cnns` tiene un solo archivo anidado, probablemente residuo.
4. `docs/` mezcla en plano documentos de R1 y R2 sin separar por reto; `reto/` (código) y `docs/reto/` (enunciados) tienen nombres confusos.
5. `reto/` mezcla señales R1 (color) y R2 (CNN) y drivers del robot.
6. `tools/` mezcla calibración R1 con entrenamiento R2.
7. Ignorados pero presentes: `temp/`, `scripts/`, `vid/`, `test_/` (este último trae `Robot.py` de pruebas).

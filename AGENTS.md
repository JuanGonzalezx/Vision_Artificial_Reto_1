# Guía para agentes (y para nosotros)

Este archivo manda sobre cómo se trabaja en este repo. `CLAUDE.md` apunta aquí.

## Qué es esto

El "cerebro" de un robot seguidor de línea para el reto 1 de Visión Artificial (UCaldas 2026-2). Lee la cámara en tiempo real, sigue la línea guía y obedece un octágono rojo (PARE) y uno verde (SIGA). Contexto completo en @README.md y @docs/arquitectura.md.

## Reglas duras del reto

**Solo se usan técnicas vistas en el curso.** La lista oficial, con dónde vimos cada una, está en @docs/reto/tecnicas-permitidas.md. Resumen:

- **Permitido:** operaciones aritméticas y lógicas, máscaras, espacios de color (RGB, HSV, CIELab), ROI, redimensionar y rotar, umbralización, segmentación por color, K-Means básico, morfología, suavizado, Canny, contornos y sus propiedades (área, perímetro, centroide, aproximación poligonal, relación de aspecto), identificación de formas simples.
- **Prohibido:** redes neuronales, deep learning, modelos preentrenados, YOLO / SSD / Faster R-CNN, cascadas Haar, servicios externos de IA, y cualquier librería que detecte la línea o las señales por nosotros.
- Si algo parece necesitar una técnica que no está en la lista, **no la uses**: busca una alternativa con lo disponible, o déjalo anotado en la zona gris de ese documento para preguntarle al profesor.
- Cada función que use una técnica dice en su docstring de qué clase sale. Eso es lo que se sustenta después.

## Arquitectura

Un frame entra, una `Decision` sale. Ver @docs/arquitectura.md. Lo esencial:

- Los contratos entre módulos están en @reto/tipos.py. **No se cambian sin avisarle a los otros dos**, porque cada quien programa contra ellos.
- Todos los umbrales van en @reto/config.py. **Ningún número mágico en la lógica.**
- Un archivo por etapa: `camara`, `linea`, `senales`, `control`, `pipeline`, `overlay`.
- `control.py` no usa OpenCV: es lógica pura y se prueba con `tools/probar_control.py`.
- La decisión sale por un **actuador** (@reto/actuador.py): consola, CSV, simulador o robot. El simulador de Daniel se conecta ahí, sin tocar el control (ver @docs/flujo-de-pruebas.md y @docs/decisiones/0003-simulador-y-actuador.md).

## Quién es dueño de qué

| Archivo | Dueño |
|---|---|
| `reto/camara.py`, `main.py` | Santiago |
| `reto/pipeline.py`, `reto/senales.py` | Daniel |
| `reto/linea.py`, `reto/control.py`, `docs/` | Juan David |
| `reto/tipos.py`, `reto/config.py` | los tres, de común acuerdo |

Antes de editar el archivo de otro, avisar. Si hace falta algo de su módulo, se acuerda en `tipos.py`.

## Estilo de código

- Español en nombres, comentarios y docstrings.
- Nombres descriptivos; condiciones complejas se extraen a variables con nombre.
- Comentarios que expliquen **la etapa del algoritmo**, no lo que ya dice el código.
- Lo más simple que funcione. Este código hay que poder explicarlo de memoria en la sustentación.
- Funciones cortas, una responsabilidad por función, y que se puedan probar sin cámara cuando se pueda.

## Comandos

```bash
uv sync                                  # instalar todo
uv run main.py --fuente <url|video|0>    # correr el cerebro
uv run main.py --mascaras                # ver las máscaras para calibrar
uv run python tools/probar_control.py    # pruebas de la máquina de estados
uv run main.py --fuente datos/clips/x.mp4 --grabar   # deja video + CSV en datos/grabaciones/
uv run python tools/preparar_videos.py   # clips livianos y frames desde datos/originales/
uv run python tools/calibrar.py <clip>   # trackbars para rangos HSV y ROI
uv run python tools/evaluar.py           # numeros comparables sobre todos los clips
uv run python tools/sync_apuntes.py      # traer los apuntes de clase al repo
uv run python tools/notebooks.py limpiar <in.ipynb> <out.ipynb>
```

## Qué no hacer

- No agregar dependencias sin discutirlo: cada librería nueva hay que justificarla frente a las restricciones del reto.
- No subir videos pesados: los originales van a `datos/originales/` (ignorado) y al repo solo entran los clips livianos y los frames que genera `tools/preparar_videos.py`.
- No meter los notebooks pesados del profesor al repo: van limpios (`tools/notebooks.py`).
- No dejar umbrales dentro de la lógica: van a `config.py`.
- No cambiar los contratos de `tipos.py` sin avisar.

## Antes de dar algo por bueno

Correr `uv run python tools/evaluar.py` y comparar con la corrida anterior. "Me pareció que iba mejor" no cuenta. Y revisar que la respuesta a la técnica usada esté en @docs/preguntas-del-profe.md.

## Después de cada avance

- Si el cambio fue una decisión de diseño, se escribe un archivo corto en `docs/decisiones/` (hay plantilla).
- Si fue un ensayo con la pista, se llena la entrada del día en `docs/bitacora.md`. De ahí salen el póster y el análisis de resultados, que son dos criterios completos de la rúbrica.

# Reto 1 — Cerebro de un robot seguidor de línea

Visión Artificial en Tiempo Real · Universidad de Caldas · 2026-2

Algoritmo que lee en tiempo real la cámara del celular (por WiFi), sigue la línea guía de la pista y obedece dos señales: **octágono rojo = PARE** y **octágono verde = SIGA**. Solo con técnicas vistas en clase: nada de deep learning, modelos preentrenados ni detectores tipo YOLO.

- Especificación del profesor: [docs/reto/especificacion.md](docs/reto/especificacion.md)
- Rúbrica: [docs/reto/rubrica.md](docs/reto/rubrica.md)
- Qué se puede usar y dónde lo vimos: [docs/reto/tecnicas-permitidas.md](docs/reto/tecnicas-permitidas.md)
- Cómo está armado el código: [docs/arquitectura.md](docs/arquitectura.md)
- Cómo probamos: [docs/flujo-de-pruebas.md](docs/flujo-de-pruebas.md)
- Qué nos va a preguntar el profesor: [docs/preguntas-del-profe.md](docs/preguntas-del-profe.md)
- Guion de la sustentación: [docs/guion-sustentacion.md](docs/guion-sustentacion.md)

## Equipo

| Integrante | Frente |
|---|---|
| Santiago Bedoya Arcila | Conexión y captura de la cámara (`reto/camara.py`, `main.py`) |
| Daniel Felipe Franco Rincón | Pipeline y detección de señales (`reto/pipeline.py`, `reto/senales.py`) |
| Juan David Ocampo González | Orquestación, documentación, línea y control (`reto/linea.py`, `reto/control.py`, `docs/`) |

## Estado

- ✅ Captura de video (webcam, celular por IP o archivo de video), con reintentos
- ✅ Estructura del pipeline, contratos entre módulos y configuración central
- ✅ Máquina de estados del control, con pruebas (`uv run python tools/probar_control.py`)
- ✅ HUD y mosaico de máscaras para calibrar
- ⬜ `reto/linea.py` — segmentación de la línea y desviación
- ⬜ `reto/senales.py` — detección de los octágonos
- ✅ Actuadores (consola y CSV) y modo `--grabar`
- ⬜ Calibración con los videos de ensayo del profesor
- ⬜ Simulador conectado como actuador (Daniel)

## Instalación

Requiere [uv](https://docs.astral.sh/uv/). Python y las librerías las instala él mismo:

```bash
git clone git@github.com:JuanGonzalezx/Vision_Artificial_Reto_1.git
cd Vision_Artificial_Reto_1
uv sync
```

## Uso

```bash
# Webcam del computador (para desarrollar)
uv run main.py

# Cámara del celular por WiFi (la IP la da la app de cámara IP)
uv run main.py --fuente http://192.168.1.50:8080/video

# Un video de ensayo del profesor
uv run main.py --fuente datos/videos/pista1.mp4

# Viendo las máscaras, para calibrar
uv run main.py --config config_pista.json --mascaras

# Guardando el video procesado y el CSV de decisiones (material del póster)
uv run main.py --fuente datos/clips/pista1.mp4 --grabar
```

Se sale con `q`. En macOS, la primera vez el sistema pide permiso de cámara para la terminal: se acepta y se vuelve a correr.

Otros comandos:

```bash
uv run python tools/probar_control.py    # prueba la lógica de control sin cámara
uv run python tools/calibrar.py datos/clips/rutaIdeal/video1.mp4   # trackbars de color y ROI
uv run python tools/evaluar.py           # corre el pipeline sobre todos los clips y da números
uv run python tools/calibrar_kmeans.py datos/frames -o config_pista.json   # calibración automática
uv run python tools/barrido.py vmax 100 110 120                            # elegir un umbral con datos
uv run python tools/preparar_videos.py   # clips livianos + frames de calibración desde datos/originales/
uv run python tools/sync_apuntes.py      # actualiza docs/clases desde la carpeta de la materia
```

## Estructura

```
Vision_Artificial_Reto_1/
├── main.py                 # línea de comandos y loop principal
├── reto/                   # el cerebro, un archivo por etapa
│   ├── tipos.py            # contratos entre módulos (empezar por aquí)
│   ├── config.py           # todos los parámetros y umbrales
│   ├── camara.py           # captura y reconexión
│   ├── linea.py            # línea guía -> desviación
│   ├── senales.py          # octágonos PARE y SIGA
│   ├── control.py          # máquina de estados -> acción
│   ├── actuador.py         # a dónde va la decisión: consola, CSV, simulador, robot
│   ├── pipeline.py         # orquesta las etapas
│   └── overlay.py          # HUD y mosaico de depuración
├── docs/
│   ├── arquitectura.md     # diseño, estrategia y división del trabajo
│   ├── flujo-de-pruebas.md # de los videos del profesor a la pista
│   ├── bitacora.md         # qué pasó en cada ensayo (material del póster)
│   ├── clases/             # apuntes de las clases 1 a 4
│   ├── decisiones/         # decisiones tomadas, una por archivo
│   └── reto/               # especificación, rúbrica y técnicas permitidas
├── notebooks/              # notebooks del profesor, sin imágenes, + su código en .py
├── tools/                  # utilidades del repo
└── datos/
    ├── originales/         # videos tal cual del profesor (no se suben)
    ├── clips/              # versiones livianas, sí se suben
    ├── frames/             # frames de calibración, sí se suben
    └── grabaciones/        # salidas de --grabar (no se suben)
```

Los notebooks originales del profesor, con sus imágenes, están fuera del repo, en `contenidoClase/notebooks/` de la carpeta de la materia.

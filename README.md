# Reto 1 — Cerebro de un robot seguidor de línea

Visión Artificial en Tiempo Real · Universidad de Caldas · 2026-2

Algoritmo que lee en tiempo real la cámara del celular (por WiFi), sigue la línea guía de la pista y obedece dos señales: **octágono rojo = PARE** y **octágono verde = SIGA**. Solo con técnicas vistas en clase: nada de deep learning, modelos preentrenados ni detectores tipo YOLO.

- Especificación del profesor: [docs/reto/especificacion.md](docs/reto/especificacion.md)
- Rúbrica: [docs/reto/rubrica.md](docs/reto/rubrica.md)
- Qué se puede usar y dónde lo vimos: [docs/reto/tecnicas-permitidas.md](docs/reto/tecnicas-permitidas.md)
- Cómo está armado el código: [docs/arquitectura.md](docs/arquitectura.md)

## Equipo

| Integrante | Frente |
|---|---|
| Santiago Bedoya Arcila | Conexión y captura de la cámara (`reto/camara.py`, `main.py`) |
| Daniel Felipe Franco Rincón | Pipeline y detección de la línea (`reto/pipeline.py`, `reto/linea.py`) |
| Juan David Ocampo González | Orquestación, documentación, señales y control (`reto/senales.py`, `reto/control.py`, `docs/`) |

## Estado

- ✅ Captura de video (webcam, celular por IP o archivo de video), con reintentos
- ✅ Estructura del pipeline, contratos entre módulos y configuración central
- ✅ Máquina de estados del control, con pruebas (`uv run python tools/probar_control.py`)
- ✅ HUD y mosaico de máscaras para calibrar
- ⬜ `reto/linea.py` — segmentación de la línea y desviación
- ⬜ `reto/senales.py` — detección de los octágonos
- ⬜ Calibración con los videos de ensayo del profesor

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
```

Se sale con `q`. En macOS, la primera vez el sistema pide permiso de cámara para la terminal: se acepta y se vuelve a correr.

Otros comandos:

```bash
uv run python tools/probar_control.py    # prueba la lógica de control sin cámara
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
│   ├── pipeline.py         # orquesta las etapas
│   └── overlay.py          # HUD y mosaico de depuración
├── docs/
│   ├── arquitectura.md     # diseño, estrategia y división del trabajo
│   ├── bitacora.md         # qué pasó en cada ensayo (material del póster)
│   ├── clases/             # apuntes de las clases 1 a 4
│   ├── decisiones/         # decisiones tomadas, una por archivo
│   └── reto/               # especificación, rúbrica y técnicas permitidas
├── notebooks/              # notebooks del profesor, sin imágenes, + su código en .py
├── tools/                  # utilidades del repo
└── datos/                  # videos y grabaciones (no se suben al repo)
```

Los notebooks originales del profesor, con sus imágenes, están fuera del repo, en `contenidoClase/notebooks/` de la carpeta de la materia.

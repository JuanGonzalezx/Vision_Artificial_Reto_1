# Propuesta de organización: un reto por carpeta

## Idea

- `reto_1/` = **congelado**. Copia exacta del repo en `2e93b71` (fin del Reto 1). No se toca más.
- `reto_2/` = **copia de `reto_1/`** sobre la que se trabaja. Aquí viven los cambios y el material de R2.
- `compartido/` = lo que no es de un reto (apuntes de clase, material del curso).
- La raíz queda limpia: solo README, guías de agentes y carpetas de retos.

Ventaja: cada reto corre solo (`cd reto_2 && uv sync && uv run main.py`), sin que cambios de R2 rompan R1 y sin mezclar contexto.

## Árbol propuesto

```
Vision_Artificial/
├── README.md                  # índice: qué hay en cada reto y cómo correrlo
├── AGENTS.md                  # solo reglas globales (equipo, estilo, git)
├── CLAUDE.md                  # apunta a AGENTS.md
├── .gitignore
│
├── compartido/
│   └── clases/                # apuntes clase1-4 + img (antes docs/clases)
│
├── reto_1/                    # CONGELADO (= commit 2e93b71)
│   ├── AGENTS.md              # reglas R1 (sin CNN, solo técnicas del curso)
│   ├── README.md
│   ├── pyproject.toml, uv.lock, .python-version
│   ├── main.py
│   ├── reto/                  # camara, linea, senales, control, pipeline, overlay, actuador*, simulador, Robot*
│   ├── configs/, config_celular.json
│   ├── datos/                 # clips, frames
│   ├── notebooks/
│   ├── tools/
│   ├── tests/
│   ├── simulacion/
│   ├── docs/                  # enunciado, rúbrica, ADR 0001-0009, arquitectura, bitácora, guion...
│   └── MEJORAS.md
│
└── reto_2/                    # TRABAJO ACTIVO (empieza como copia de reto_1)
    ├── AGENTS.md              # reglas R2 (CNN permitida para señales)
    ├── README.md
    ├── pyproject.toml, uv.lock, .python-version
    ├── main.py
    ├── reto/                  # + clasificador.py; pipeline/tipos/config/overlay/senales modificados
    ├── configs/, config_celular.json
    ├── datos/
    │   ├── clips/, frames/    # heredados de R1
    │   └── senales/           # dataset PARE/SIGA/VELOCIDAD_60/ZONA_ESCOLAR
    ├── cnn/                   # antes 5_cnns/ (cnn_trainer.py, dataset de clase)
    ├── modelos/               # DenseNet121, MobileNet, ResNet50, VGG16, VGG19
    ├── notebooks/
    ├── tools/                 # + entrenar_senales.py, preparar_senales.py
    ├── tests/                 # + test_clasificador.py
    ├── simulacion/
    ├── docs/                  # enunciado R2 (Reto-2.docx, reto-2.md), ADR 0001-0010, arquitectura actualizada
    └── INFORME_RETO2.md
```

## Qué va dónde (mapeo)

| Hoy | Destino |
|---|---|
| Todo lo versionado en `2e93b71` | `reto_1/` (tal cual) |
| `docs/clases/` | `compartido/clases/` (se quita de ambos retos; R1 y R2 lo referencian) |
| Copia de `reto_1/` | `reto_2/` base |
| `5_cnns/` | `reto_2/cnn/` (renombrar: nombre que empieza con número es incómodo para imports) |
| `modelos/` | `reto_2/modelos/` |
| `datos/senales/` | `reto_2/datos/senales/` |
| `Reto-2.docx`, `INFORME_RETO2.md` | `reto_2/docs/` |
| `reto/clasificador.py`, `tools/entrenar_senales.py`, `tools/preparar_senales.py`, `tests/test_clasificador.py`, ADR 0010, `reto-2.md` | `reto_2/...` misma ruta relativa |
| Archivos modificados por R2 (`tipos`, `config`, `pipeline`, `overlay`, `senales`, `arquitectura.md`, `test_integracion`) | versión R2 en `reto_2/`; versión original queda en `reto_1/` |

## Limpieza (no se migra)

- `Captura de pantalla 2026-09-29 101903.png` → borrar o mover a `reto_1/docs/media/`.
- `figuras/` vacía → borrar.
- `temp/`, `scripts/`, `test_/`, `vid/`, `salida/` (ignorados): decidir caso a caso. `test_/Robot.py` y `vid/*.mp4` solo si se usan; si sí, van a `reto_2/` (`vid/` → `datos/originales/`, que es lo que espera `tools/preparar_videos.py`).
- `5_cnns/src/5_cnns/` (anidado, un archivo) → revisar y borrar si es residuo.
- `5_cnns/pyproject.toml`, `uv.lock`, `requirements.txt`, `main.py` propios → fusionar dependencias en el `pyproject.toml` de `reto_2/` y borrar el resto; así hay un solo entorno.

## Pasos de ejecución (cuando lo apruebes)

1. Rama nueva `reorganizar` desde `reto2` (nada se pierde; git conserva historia).
2. `git mv` de todo lo trackeado actual a `reto_2/`.
3. Restaurar el estado `2e93b71` en `reto_1/` (`git archive 2e93b71 | tar -x -C reto_1`) y commitear.
4. Quitar de `reto_1/` y `reto_2/` lo que ya vive en `compartido/` y ajustar rutas (`tools/sync_apuntes.py`).
5. Ajustar en `reto_2/`: rutas `@5_cnns/` → `@cnn/` en `AGENTS.md`/docs, imports, `.gitignore`.
6. Dividir `AGENTS.md`: reglas globales en raíz, reglas del reto en cada carpeta.
7. Correr `uv sync` + `uv run pytest` en cada reto para validar.

## Decisiones (cerradas)

1. **Entorno aislado por reto**: cada uno con su `pyproject.toml`, `uv.lock` y `.venv`. R1 sin tensorflow/keras.
2. **Dataset de `cnn/` (antes `5_cnns/dataset`) se versiona**, no va a `.gitignore`.
3. **`Robot.py`/`Robot_mac.py` duplicados** en ambos retos (autonomía).

## Estado

Pendiente: tu revisión de la estructura. No se ha movido nada.

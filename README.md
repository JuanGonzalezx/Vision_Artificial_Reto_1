# Visión Artificial — Robot seguidor de línea (UCaldas 2026-2)

Un reto por carpeta, cada uno con su propio entorno (`uv`).

| Carpeta | Qué es | Estado |
|---|---|---|
| `reto_1/` | Reto 1: línea + señales PARE/SIGA por color y forma. Snapshot del commit `2e93b71`. | **Congelado** |
| `reto_2/` | Reto 2: parte de `reto_1/` y reconoce 4 señales con CNN. | **Activo** |
| `docs/` | Documentación de ambos retos: algoritmo, arquitectura, decisiones, bitácora, enunciados (`docs/reto/`). `arquitectura-reto1.md` es la versión de Reto 1. | Compartido |
| `compartido/` | Apuntes (`clases/`) y notebooks de clase. | Referencia |

Correr un reto:

```bash
cd reto_2          # o reto_1
uv sync
uv run main.py --fuente <url|video|0>
uv run pytest tests
```

Reglas del equipo y estilo: `AGENTS.md`. **Estado actual y pendientes del Reto 2: `ESTADO.md`.**

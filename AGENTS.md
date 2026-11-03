# Guía para agentes (raíz)

Repo de Visión Artificial (UCaldas 2026-2): robot seguidor de línea. Un reto por carpeta.

- **`reto_1/` está congelado** (estado del commit `2e93b71`): no se edita, solo se ejecuta.
- **El trabajo activo es `reto_2/`**: mismo pipeline de Reto 1 + reconocimiento de 4 señales con CNN (PARE, SIGA, ZONA_ESCOLAR, VELOCIDAD_60). Enunciado: `docs/reto/Reto-2.md`.
- Cada reto es autónomo (propio `pyproject.toml`, `uv.lock`, `.venv`). Ejecutar siempre desde su carpeta con `uv run`.
- Dataset del reto: `reto_2/cnn/dataset/` (0 PARE, 1 SIGA, 2 ZONA_ESCOLAR, 3 VELOCIDAD_60). No hay otro dataset de entrenamiento.
- Documentación compartida: `docs/`. Apuntes y notebooks de clase: `compartido/`.
- Tests de `reto_2`: `uv run python -m unittest discover -s tests`.
- Git: nunca atribuir a Claude/Anthropic en commits ni PRs.

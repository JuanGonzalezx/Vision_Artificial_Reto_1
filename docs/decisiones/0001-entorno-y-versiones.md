# 0001 — Entorno y versiones

- **Fecha:** 2026-09-22
- **Estado:** aceptada
- **Deciden:** Juan David (propone), pendiente de confirmar con Santiago y Daniel

## Contexto
El repo arrancó con Python 3.14 y OpenCV 5.0.0.93 (lo que montó Santiago). La carpeta personal de clases de Juan David está en Python 3.12 con OpenCV 4.14. Los tres tenemos que correr el mismo código y el `uv.lock` tiene que servirle a todos.

## Decisión
Se mantiene **Python 3.14 + OpenCV 5.0.0.93**, que es lo que ya está en el repo y en el `uv.lock`. Se agregan `numpy` y `scikit-learn` (K-Means de la clase 4) y `matplotlib` (los notebooks del profesor lo usan) como dependencias explícitas.

## Alternativas consideradas
Bajar el repo a Python 3.12 + OpenCV 4.x, que es lo que usa la mayoría del material de referencia. Se descartó por ahora para no hacer que dos personas reinstalen su entorno a mitad del reto.

## Consecuencias
- Nadie reinstala nada y `uv sync` deja a los tres iguales.
- OpenCV 5 es muy nuevo: casi todo lo que se encuentra en internet asume 4.x. Si aparece un comportamiento raro en una función, lo primero que hay que descartar es la versión.
- Si algo no funciona en OpenCV 5, el plan B es fijar `opencv-python>=4.10,<5` en `pyproject.toml` y volver a correr `uv sync`. Los scripts de clase ya se probaron en las dos versiones.

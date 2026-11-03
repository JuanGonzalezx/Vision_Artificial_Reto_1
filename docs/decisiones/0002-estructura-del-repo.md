# 0002 — Estructura del repositorio

- **Fecha:** 2026-09-22
- **Estado:** aceptada
- **Deciden:** Juan David (propone), pendiente de confirmar con Santiago y Daniel

## Contexto
El repo arrancó con todo en la raíz (`main.py`, `camara.py`, `resources/` con los notebooks del profesor y el .docx del reto). Los notebooks pesaban 12.7 MB porque llevan las imágenes incrustadas en base64, y no había dónde poner la documentación ni forma de que los tres trabajáramos en paralelo sin chocar.

## Decisión
- El código de la solución vive en el paquete `reto/`, un archivo por etapa, con los contratos en `reto/tipos.py`.
- La documentación vive en `docs/`: el reto y la rúbrica en markdown, los apuntes de cada clase, las decisiones y la bitácora.
- Los notebooks del profesor entran al repo **sin imágenes ni salidas** (56 KB en total) más su código en `.py`. Los originales pesados quedan fuera del repo, en `contenidoClase/notebooks/` de la carpeta de la materia.
- `datos/` (videos de ensayo, grabaciones) está en `.gitignore`.

## Alternativas consideradas
Dejar todo plano en la raíz. Funciona para dos archivos, pero con tres personas trabajando a la vez se vuelve un choque de merges permanente.

## Consecuencias
- El árbol de trabajo baja de 24 MB a menos de 1 MB. El historial de git sigue pesando ~11 MB por el primer commit; reescribirlo no vale la pena.
- Cada quien trabaja en su archivo y los contratos se acuerdan entre los tres.
- Hay que mantener los apuntes sincronizados (`tools/sync_apuntes.py`).

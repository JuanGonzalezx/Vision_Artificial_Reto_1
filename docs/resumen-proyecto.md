# Resumen del proyecto — estado actual

Generado para orientar a alguien nuevo en el repo. Fuente de verdad sigue siendo `AGENTS.md` y `docs/arquitectura.md`.

## Qué es

Cerebro de robot seguidor de línea (Reto 1, Visión Artificial, UCaldas 2026-2). Lee cámara (celular por WiFi, webcam o video), sigue línea guía, obedece octágono rojo (PARE) y verde (SIGA). Solo técnicas vistas en clase — sin deep learning ni modelos preentrenados.

Equipo: Santiago (cámara), Daniel (pipeline/línea), Juan David (señales/control/docs).

## Qué se lleva (implementado y funcionando)

- **`reto/camara.py` + `main.py`** — captura completa: webcam, URL de celular, archivo de video, reconexión con reintentos, CLI con `--fuente/--usuario/--contrasena/--config/--mascaras`.
- **`reto/config.py`** — todos los umbrales centralizados, carga/guardado en JSON para calibrar sin tocar código.
- **`reto/tipos.py`** — contratos entre módulos (`ResultadoLinea`, `ResultadoSenal`, `Decision`, `Estado`).
- **`reto/control.py`** — máquina de estados completa (`SIGUIENDO`/`DETENIDO`/`BUSCANDO`), con confirmación de señal por persistencia y espera entre señales. Tiene pruebas: `tools/probar_control.py`.
- **`reto/pipeline.py`** — orquesta todo: preprocesa, recorta dos franjas de línea (cercana + lejana, idea propia del equipo para anticipar curvas), llama detección de línea/señal, combina franjas, decide.
- **`reto/overlay.py`** — HUD y mosaico de máscaras para calibrar visualmente.
- **`simulacion/index.html`** — simulador para probar sin hardware.
- Documentación: arquitectura, especificación del reto, rúbrica, técnicas permitidas, apuntes de clase 1-4.

## Qué falta (bloqueante)

- **`reto/linea.py` → `detectar()`** — solo el esqueleto y el plan en docstring; devuelve siempre "no detectada". Sin esto el robot no ve la línea. Dueño: Daniel.
- **`reto/senales.py` → `detectar()`** — mismo caso, solo plan en docstring; devuelve siempre "sin señal". Sin esto no hay PARE/SIGA. Dueño: Juan David.
- **Calibración real** — no hay videos del profesor en `datos/videos/` todavía (carpeta vacía, en `.gitignore`). Sin video de pista no se pueden ajustar los rangos HSV de `config.py`.
- `docs/bitacora.md` solo tiene la entrada de organización del repo — cero ensayos con pista real todavía.
- `docs/arquitectura.md` sección 9 ("Lo que falta") está desactualizada: ya marca `control.decidir` como pendiente pero está implementado.

## Cómo ponerlo a andar

```bash
uv sync                                     # instala Python + dependencias
uv run python tools/probar_control.py       # confirma que la máquina de estados corre (sin cámara)
uv run main.py                              # video de desarrollo vid/video1.mp4 (por defecto)
uv run main.py --fuente 0                   # webcam local
uv run main.py --fuente <url_celular>       # cámara del celular por WiFi
uv run main.py --mascaras                   # ventana extra con las máscaras, para calibrar
```

Hoy correr `main.py` abre cámara y dibuja el HUD, pero la línea y las señales no se detectan de verdad (los dos `detectar()` son stubs) — el robot corre "ciego".

## Siguiente paso, en orden

1. **Implementar `linea.py`** (Daniel) — HSV → `inRange` → apertura/cierre → contorno mayor → centroide → desviación. El plan ya está en el docstring del archivo, paso a paso.
2. **Implementar `senales.py`** (Juan David) — HSV rojo (dos rangos) + verde → morfología → contornos → `approxPolyDP` → filtro vértices/relación de aspecto/circularidad. Plan también en el docstring.
3. **Conseguir videos de pista del profesor** y ponerlos en `datos/videos/`, o grabar propios — sin esto, los pasos 1 y 2 no se pueden calibrar con nada real.
4. **Calibrar HSV con K-Means** (clase 4) sobre un frame real de la pista, como propone `docs/arquitectura.md` sección 6 — es la estrategia diferenciadora que el equipo quiere sustentar.
5. **Primer ensayo con pista** y llenar `docs/bitacora.md` el mismo día — de ahí sale el póster y el análisis de resultados de la rúbrica.
6. Decidir y documentar en `docs/decisiones/` cuáles de las 4 estrategias diferenciadoras (sección 6 de arquitectura) entran finalmente.
7. Confirmar con el profesor los segundos exactos de PARE (`config.segundos_pare` hoy es un valor provisional de 3.0s).

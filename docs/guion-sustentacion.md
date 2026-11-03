# Guion de la sustentación (2026-09-29)

Cinco minutos para mostrar qué está implementado, cómo se prueba y qué falta validar con el robot. Los números de los clips describen decisiones sobre videos; no equivalen a una prueba física.

## Preparación

Desde la raíz del repo:

```bash
uv sync --locked
uv run python tools/probar_control.py
uv run python -m unittest discover -s tests -v
uv run python tools/evaluar.py
uv run main.py --fuente datos/clips/rutaIdeal/video4.mp4 --mascaras --consola
```

Tener abiertos [arquitectura y diagramas](arquitectura.md), `docs/media/etapas.png` y la [bitácora](bitacora.md). `docs/media/demo_sustentacion.mp4` es material ilustrativo de la versión anterior; para mostrar el comportamiento actual se ejecuta el comando de arriba o se genera una grabación nueva con `--grabar`.

## Qué mostrar

**1. Problema y restricciones — Santiago, 30 s.** Seguimos una línea y respondemos a PARE/SIGA con técnicas vistas en clase. La electrónica y Arduino no se modifican. Por ahora la decisión se ve en HUD, consola y CSV.

**2. Algoritmo — Daniel, 1 min.** Mostrar el diagrama de procesamiento: resize y Gauss; ROI; HSV; máscaras; morfología; contorno y centroide para la línea; color, área y geometría para señales; persistencia y máquina de estados. K-Means solo propone rangos durante la calibración.

**3. Demostración reproducible — Juan David, 1 min.** Ejecutar un clip con PARE, otro con SIGA y uno de descarrilamiento. Señalar la razón de cada decisión y las máscaras. El archivo termina sin repetirse. Si se usa cámara, aclarar si ya se midieron sus FPS y latencia con el montaje definitivo.

**4. Resultados — Juan David, 1 min.** Mostrar la evaluación actual junto a la referencia anterior a la integración:

| Medida en clips | Referencia previa |
|---|---|
| Frames con detección de línea | 91.1% de 2341; 100% en ruta ideal |
| Saltos sospechosos de desviación | 4 |
| Búsqueda hacia lado esperado | 5 de 5 clips de descarrilamiento |
| Detecciones PARE/SIGA en clips sin señales | 0 en los cinco clips negativos |

La dirección de búsqueda está comprobada sobre un video que no responde a las órdenes. La recuperación física, el tiempo de recorrido y las intervenciones se medirán con el robot. Sin etiquetado manual, el porcentaje de detección no es una medida de precisión.

**5. Límites y siguiente prueba — Santiago, 1 min.** ROI y colores calibrados con los clips del profesor; el montaje propio puede cambiarlos. La demo JavaScript todavía no se conecta con Python. Falta integrar la API del robot y validar trayectoria, señales y pérdida de comunicación en la práctica.

**6. Aclaraciones para el profesor — los tres, 30 s.** Confirmar duración del PARE, si SIGA puede interrumpirlo y si las señales de la práctica son octágonos de frente. El valor actual de 3 segundos es provisional.

## Preguntas probables

1. **¿Por qué esos umbrales?** Se compararon configuraciones y máscaras. V=129 elevaba la cantidad de detecciones, pero también los saltos y empeoraba la dirección de búsqueda. K-Means propone; la evaluación y la inspección deciden.
2. **¿Por qué aceptan una cartulina que no es octágono?** Los clips de ensayo dan 4–5 vértices; el modo permisivo permite probar esas secuencias. `exigir_octagono=True` activa los filtros geométricos, que todavía pueden confundir figuras similares. Debe validarse con las señales reales.
3. **¿Las dos franjas anticipan las curvas?** Se calcula la lejana para mostrar un indicador de curvatura, pero su peso en la decisión es cero porque mezclarla empeoró estas pruebas.
4. **¿Ya mueve el robot?** No. Están listos percepción, control y salida de decisiones; falta el adaptador autorizado y la prueba física.

Cada integrante debe poder explicar las partes de los otros. Más respuestas en [preguntas-del-profe.md](preguntas-del-profe.md).

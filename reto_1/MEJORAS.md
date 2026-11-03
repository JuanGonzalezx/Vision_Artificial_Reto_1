# Mejoras de la rama `feat/linea-y-medicion` frente a `main`

Autor de los cambios: Daniel Felipe Franco Rincón. Fecha: 2026-09-29.

Este documento resume todo lo que esta rama le agrega a `main`: qué cambió, por qué, cómo se usa y qué se midió. El detalle de cada decisión está en `docs/decisiones/` y el estado por requisito en `docs/plan-reto.md` (v1.5).

## Resumen

| Área | Antes (`main`) | Ahora |
|---|---|---|
| Seguimiento de la línea | Solo la franja cercana. La franja lejana se calculaba suelta y no entraba en la decisión | **Horizonte**: la línea se sigue de cerca a lejos en 8 tramos encadenados y el robot apunta a un punto más adelante |
| Selección del contorno | Siempre el más grande de la franja | El más cercano a donde estaba la línea en el frame anterior (`Estado.ultimo_centro_linea`), para no saltar entre trozos |
| Calibración de colores | A ojo, con trackbars | K-Means (clase 4) sobre un frame real: `tools/calibrar_clusters.py` |
| Medición | `tools/evaluar.py` sobre todos los clips | Además, `tools/evaluar_video.py`: métricas por video, salto máximo, tiempos y CSV por frame |
| Desarrollo sin celular | Había que pasar `--fuente` | `--bucle`: el video se repite a su velocidad real y el estado se reinicia en cada vuelta |
| Simulador | Solo se manejaba con el teclado | `--index`: el simulador hace de cámara y de robot, en lazo cerrado con el cerebro en Python |
| HUD | Estado, acción, ROI y curva | También la cadena del horizonte y el punto objetivo |
| Pruebas | 43 | 52 (`tests/test_horizonte.py`) más `tools/probar_linea.py` |

## 1. Horizonte: anticipar la curva (lo principal)

**Problema.** El control solo miraba la franja cercana, así que corregía cuando la curva ya estaba encima del carro. Mezclar la franja lejana (`peso_linea_lejana`) se había probado y empeoraba: esa franja se calcula suelta y a veces toma otro trozo oscuro (una sombra, un papel).

**Solución** (`reto/linea.py` → `mirar_adelante`, `reto/pipeline.py` → `anticipar`):

1. La zona delante del carro (`roi_horizonte`, 0.05–0.58 del alto) se segmenta una sola vez, igual que la línea: HSV + `inRange` + apertura y cierre.
2. Se corta en `tramos_horizonte` (8) franjas horizontales. De abajo hacia arriba se saca el centroide de la línea en cada una con momentos.
3. **Cada tramo se queda con el trozo más cercano al tramo anterior**, así la cadena sigue la misma línea. Si un tramo no tiene línea o el centro salta más de `salto_maximo_tramo`, la cadena se corta.
4. Un contorno más ancho que `ancho_maximo_tramo` es la barra negra sobre la que va la señal y se ignora. Los tramos de abajo pueden faltar, porque la barra o el sensor los tapan.
5. El robot apunta al tramo `tramo_objetivo` (6). Si la cadena termina pegada a un borde sin llegar arriba, la curva se sale del cuadro y el objetivo pasa a ser ese borde (±1).
6. La desviación final es `(1 − peso_horizonte) · cercana + peso_horizonte · objetivo`, un promedio ponderado.

**Técnicas** (todas del curso): ROI (clase 1), HSV (clase 1), `inRange` (clase 2), apertura y cierre (clase 3), contornos, `boundingRect` y momentos (clase 3), operaciones aritméticas (clase 2). No se usa `fitLine`, Hough, `minAreaRect` ni ajuste de curvas.

**Resultados** con `tools/evaluar.py` sobre los 9 clips:

| Métrica | `main` | Con horizonte (peso 0.5, tramo 6) |
|---|---|---|
| Línea detectada | 91.1 % | 91.1 % |
| Saltos sospechosos | 0 | 0 |
| Zigzag | 0/s | 0/s |
| Recuperación hacia el lado correcto | 5/5 clips | 5/5 clips |
| Frames con el giro ya hacia el lado correcto antes de perder la línea (5 clips de descarrilamiento) | 269 | **333 (+24 %)** |
| Salto máximo de desviación por frame (peor caso, video4) | 0.08 | 0.20 (meta ≤ 0.3) |
| Tiempo por frame | ~2.5 ms | ~4 ms (meta ≤ 25 ms) |

**A vigilar.** El robot gira más en general (desviación media 0.18 → 0.32), que es lo esperado al apuntar adelante. En lazo cerrado podría sobrecorregir, y eso hay que confirmarlo en el simulador o en la pista. Con `peso_horizonte = 0` todo queda como antes. Una curva casi horizontal se ve tan ancha como la barra de la señal y se descarta: ahí manda la franja cercana.

Decisión completa: `docs/decisiones/0007-horizonte.md`.

## 2. Detección de la línea más estable

- `contorno_principal` elige el trozo **más cercano a la posición anterior** (`Estado.ultimo_centro_linea`) en vez del más grande. Cuando la cinta transversal parte la línea en dos, el centro no salta de un lado al otro.
- Parámetro `ancho_maximo_linea` para descartar contornos muy anchos. Queda en 1.0 (desactivado) porque con 0.50 se perdían curvas de los clips del profesor (91.1 % → 87.6 %).
- ROI y `hsv_linea` ajustados a la geometría real del video, fuera del chasis del robot.
- `tools/probar_linea.py`: líneas sintéticas (izquierda, centro, derecha, espejada, vacía, con cinta en T) y una imagen real.

## 3. Calibración con K-Means (clase 4)

`tools/calibrar_clusters.py --fuente <video|imagen> [--frame N] --k 5`: recorta la zona sin el chasis, pasa a HSV y corre `KMeans` sobre los píxeles. Se eligen los clusters de línea, rojo y verde, y el rango se calcula como centroide ± k·desviación, con el rojo dando la vuelta en H = 0/179. Se guarda en `configs/`. Resultado: `configs/video1-kmeans.json`, con la línea detectada en el 99.0 % del video1. Decisión: `docs/decisiones/0006-calibracion-kmeans.md`.

## 4. Medición objetiva

`tools/evaluar_video.py [video] [--config json] [--csv salida.csv]` corre el pipeline sin ventanas y reporta el % de frames con línea, el salto máximo de desviación, los frames seguidos en BUSCAR, los rangos de cada señal (candidata y confirmada), los cambios de estado y los ms por frame. El reloj del control se simula con el número de frame, así que el resultado es el mismo en cualquier computador.

## 5. Desarrollo y simulador

- `uv run main.py --fuente <video> --bucle`: repite el video a su velocidad real, así los segundos del PARE se comportan como en la pista, y reinicia el estado del robot en cada vuelta.
- `uv run main.py --index`: `reto/simulador.py` levanta un servidor local (solo librería estándar). El simulador (`simulacion/index.html?puente=1`) le manda su canvas como JPEG y recibe la orden `{accion, giro}`. El simulador entra como un actuador más (`reto/actuador.py`), sin tocar el control. Calibración propia: `configs/simulador.json`.

## 6. Documentación

- `docs/plan-reto.md` (v1.5): requisitos con criterios de aceptación, Definition of Done, plan por fases, protocolo de pruebas y estado.
- `docs/decisiones/0006-calibracion-kmeans.md` y `docs/decisiones/0007-horizonte.md`.
- `docs/preguntas-del-profe.md`: respuesta a "¿cómo anticipan las curvas?" y diferenciación actualizada.
- `docs/resumen-proyecto.md`.

## Cómo probarlo

```powershell
uv sync
uv run python -m unittest discover -s tests -v           # 52 pruebas
uv run python tools/probar_linea.py
uv run python tools/probar_control.py
uv run python tools/evaluar.py                           # métricas sobre todos los clips
uv run main.py --fuente datos/clips/rutaIdeal/video4.mp4 --bucle   # ver el horizonte en el HUD
uv run main.py --index                                   # lazo cerrado con el simulador
```

Para comparar con y sin horizonte, se crea un JSON con `{"peso_horizonte": 0.0}` y se pasa con `--config`.

## Cambios en archivos compartidos (avisar al equipo)

- `reto/tipos.py`: `Estado.ultimo_centro_linea`.
- `reto/config.py`: `ancho_maximo_linea` y el bloque del horizonte (`roi_horizonte`, `tramos_horizonte`, `area_minima_tramo`, `salto_maximo_tramo`, `ancho_maximo_tramo`, `margen_borde_horizonte`, `tramo_objetivo`, `peso_horizonte`), todos validados.
- `main.py` (Santiago): `--bucle`, `--index` y el horizonte que se le pasa a `dibujar`.
- `reto/overlay.py`: `dibujar(..., horizonte=None)`. Es compatible con las llamadas anteriores.
- `reto/pipeline.py`: `depuracion["horizonte"]`. `procesar_frame(..., ahora)` sigue igual.

## Pendiente

- Probar el horizonte en lazo cerrado (simulador y pista, T6.2) y ajustar `peso_horizonte`.
- Validar la línea con video del celular montado en el robot (T0.2).
- Pasar `auditor-tecnicas` sobre el diff antes del tag `v1.0`.

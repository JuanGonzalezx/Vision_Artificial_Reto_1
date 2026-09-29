# Bitácora de ensayos

Se llena **el mismo día del ensayo**. De aquí salen el póster y el análisis de resultados, que son dos criterios completos de la rúbrica.

## Plantilla

### AAAA-MM-DD — <qué se probó>

- **Montaje:** cámara (celular/webcam), resolución, altura y ángulo, FPS medidos.
- **Luz:** salón, hora, natural o artificial.
- **Parámetros:** qué config se usó (rangos HSV, ROI, zona muerta…).
- **Qué funcionó:**
- **Qué falló:** con el frame o el video guardado, si se puede.
- **Cambios que se hicieron:**
- **Siguiente paso:**

---

### 2026-09-22 — Organización del repo

- **Montaje:** todavía sin pista; solo estructura y documentación.
- **Qué se hizo:** se reorganizó el repo (ver `docs/decisiones/0002`), se pasaron el reto y la rúbrica a markdown, se metieron los apuntes de las clases 1 a 4 y se definieron los contratos entre módulos.
- **Siguiente paso:** bajar los videos del profesor a `datos/videos/` y calibrar con ellos los rangos de color de la línea.

### 2026-09-22 (tarde) — Primer vistazo a los videos del profesor

- **Material:** 9 videos, 28.5 MB en total. Comprimidos a 4.3 MB (`tools/preparar_videos.py`), más 27 frames de calibración. Están en `datos/clips/` y `datos/frames/`, separados en `rutaIdeal/` y `desacarrilamiento/`.
- **Formato:** verticales, 478×850, 30 fps (dos a 120 fps), entre 6 y 27 segundos.
- **Hallazgo grande — el encuadre:** el celular va detrás del carro, así que **el carro ocupa el 40% inferior de la imagen y la pista se ve arriba**. La ROI de la línea no es el borde inferior del frame: va entre y≈0.40 y y≈0.58. Medido sobre los frames: los píxeles oscuros de la línea están entre y=0.0 y y=0.6; de ahí para abajo es el carro.
- **Valores medidos** (percentiles 5/50/95 sobre los frames, HSV de OpenCV):

  | Qué | H | S | V | Área cuando está cerca |
  |---|---|---|---|---|
  | Línea (cinta negra sobre piso claro) | — | 10-90 | 29-90 (piso ≈200) | 9.000-20.000 px |
  | Señal roja | 173-175 | ≈193 | ≈168 | 39.000 px |
  | Señal verde | 69-74 | 129-200 | 90-142 | 34.000 px |
  | Pilas del carro (falso positivo de rojo) | 6-15 | alta | — | 6.000 px, siempre abajo |
  | Chasis del carro (falso positivo de verde/cian) | 41-61 y 92-102 | alta | — | ~25.000 px, siempre abajo |

- **Decisiones que salieron de esto:** la línea se separa por brillo (V), no por tono; el rango rojo alto es el que importa; el verde arranca en H=62 para no comerse el carro; y la ROI de señales deja fuera el 45% inferior. Todo quedó en `reto/config.py`.
- **Siguiente paso:** implementar `linea.detectar` y `senales.detectar` y verificar contra estos mismos clips con `--mascaras`.

### Plan hasta la próxima clase (2026-09-29)

Sin póster todavía: el objetivo es tener el algoritmo funcionando y **medido**.

| Día | Quién | Qué |
|---|---|---|
| 1-2 | Juan David | `linea.detectar` y calibración con los clips. Meta: línea detectada en más del 90% de los frames de `rutaIdeal` (`tools/evaluar.py`) |
| 2-3 | Daniel | `senales.detectar`. Meta: PARE en video4 y SIGA en video1, sin falsos positivos en los otros 7 clips |
| 3 | Santiago | Montaje definitivo del celular, FPS medidos, 2-3 clips grabados con ese montaje |
| 4-5 | Juan David | Grabar videos propios como los del profesor, recalibrar y volver a evaluar |
| 5-6 | los tres | Pista con cinta en el piso, prueba en vivo con el celular; simulador conectado como actuador |
| 7 | los tres | Repaso de `docs/preguntas-del-profe.md`: cada uno explica el pipeline completo |

Cada vez que se cambie algo del algoritmo, se corre `tools/evaluar.py` y se compara con la corrida anterior. Si empeora, se devuelve.

### 2026-09-26 — Línea y señales funcionando sobre los clips del profesor

**Línea (`reto/linea.py`).** Implementada: HSV → `inRange` por brillo → apertura y cierre → contorno más grande → centroide por momentos → desviación normalizada.

| Clips | Línea detectada |
|---|---|
| rutaIdeal (4 clips) | 100% |
| desacarrilamiento (5 clips) | 60-95% |
| **Total** | **91.1% de 2341 frames** |

Ese 60-70% en los de descarrilamiento es correcto: en esos videos la línea se sale del cuadro. Lo que importa es qué hace cuando eso pasa:

**Prueba automática de recuperación.** El nombre de cada clip dice hacia dónde se fue la línea (`noReconoceIzquierda`, `noReconoceDerecha`), así que `tools/evaluar.py` verifica solo que el robot busque hacia ese lado. **5 de 5 clips pasan.**

**Señales (`reto/senales.py`).** Versión base para que Daniel la revise: máscaras de color (dos rangos para el rojo) → morfología → contornos → área → `approxPolyDP` → forma.

- Detecta la señal verde y la roja en los 4 clips de `rutaIdeal`, con áreas de 38.000 a 43.000 px.
- **0 detecciones en los 5 clips de descarrilamiento**, o sea 0 falsos positivos.
- **Hallazgo:** las señales de los videos del profesor **no son octágonos**, son cuadrados de cartulina. Medido: 4-5 vértices con `approxPolyDP` y circularidad 0.58-0.72 (un octágono de frente da ~0.95). Si exigiéramos la forma, no detectaríamos ninguna. Decisión: el color y el área deciden, la forma suma confianza (`ResultadoSenal.es_octagono`) y se puede volver estricta con `config.exigir_octagono = True`.

**Calibración automática con K-Means (`tools/calibrar_kmeans.py`).** Coincide con lo medido a mano:

| | Medido a mano | Propuesto por K-Means |
|---|---|---|
| Rojo | H 173-175 | H 167-179 |
| Verde | H 69-74 | H 62-78 |
| Línea | V ≤ 110 | V ≤ 129 |

**La trampa del día.** Usar el rango de K-Means sube la detección de 91.1% a 93.3%... y es peor. Revisando los frames, lo que detecta de más es una sombra del borde y la rueda del carro, no la línea. Para cazar esto agregué la métrica **saltos**: veces que la desviación brinca más de 0.35 entre dos frames seguidos, algo que el carro moviéndose no puede producir.

| Config | línea detectada | saltos | recuperaciones |
|---|---|---|---|
| V ≤ 110 (la nuestra) | 91.1% | 16 | 5/5 |
| V ≤ 129 (K-Means) | 93.3% | 24 | 4/5 |

Barrido completo (`tools/barrido.py vmax 90 100 110 120 129`): 110 es el que menos saltos produce sin perder recuperaciones. **Se queda en 110**, y ahora hay una tabla para justificarlo.

**Conclusión para la sustentación:** K-Means propone, la evaluación decide.

### 2026-09-28 — Suavizado, curvatura y material para la sustentación

**Franja lejana: la apagamos.** La probamos con el barrido y empeora con los datos que tenemos.

| peso_linea_lejana | saltos | desviación media | recuperaciones |
|---|---|---|---|
| 0.0 | 12 | 0.239 | 5/5 |
| 0.3 | 16 | 0.257 | 5/5 |
| 0.7 | 20 | 0.309 | 3/5 |

La razón: las dos franjas ven cosas muy distintas (diferencia media de 0.32 entre sus desviaciones) porque la línea es curva, así que promediarlas mete ruido en vez de anticipar. Queda en 0. La franja lejana se sigue calculando y ahora alimenta un valor de **curvatura** que sale en el HUD ("curva a la derecha"); volveremos a probar mezclarla cuando podamos medir en lazo cerrado con el simulador, que es donde se vería el beneficio.

**Suavizado temporal de la desviación.** Promedio de los últimos N frames:

| N | saltos | zigzag/s |
|---|---|---|
| 1 | 12 | 0.04 |
| 3 | 4 | 0.02 |
| 5 | 0 | 0.01 |
| 8 | 0 | 0.00 |

Se queda en **3**. Con 5 los saltos desaparecen, pero son 167 ms de retraso a 30 fps y el retraso no se puede medir sobre video grabado: en la pista el carro llegaría tarde a las curvas. Si zigzaguea, se sube.

**Estado de las métricas con la configuración actual:** 91.1% de detección, 4 saltos (eran 16), 5/5 recuperaciones, 0 falsos positivos de señales.

**Contaminación entre máscaras:** medimos si la señal se cuela en la máscara de la línea cuando se superpone a la franja. En los 1572 frames de ruta ideal, 0 frames con solapamiento significativo. Riesgo abierto: la **sombra** que proyecta la señal sí es oscura y podría entrar; no apareció en estos clips.

**Material para la sustentación:** `docs/media/etapas.png` (las 5 etapas sobre un frame con PARE) y `docs/media/demo_sustentacion.mp4` (tres segmentos: SIGA, PARE y pérdida de línea con BUSCANDO). Guion en `docs/guion-sustentacion.md`.

### 2026-09-29 (noche) — Integración con las pruebas en vivo de Santiago

Santiago ya tiene el pipeline corriendo **en vivo con el celular** (IP Camera Lite sobre WiFi) contra una pista dibujada en papel: el HUD marca SIGUIENDO → DERECHA con desviación +0.13, y la máscara sigue la línea. Es la primera vez que esto corre fuera de los videos del profesor.

**Lo que eso dejó ver:** su montaje no tiene el robot en el cuadro, así que la parte cercana de la pista es el borde inferior, no la franja del 40-58% que veníamos usando con los videos del profesor. **Tres montajes, tres calibraciones.** Para no seguir editando el código en cada prueba:

- `rotacion` en la configuración y `--rotar 0|90|180|270`, porque el celular en el soporte puede quedar de lado.
- `--roi-linea` y `--roi-senal` por línea de comandos, que mandan sobre el JSON.
- `config_celular.json`, un perfil con la ROI abajo para el montaje sin robot en cuadro.
- `--grande`, que escribe la acción con letra grande para mostrarla desde lejos.

**`tools/probar_robot.py`:** teleoperación por teclado, sin visión. Es lo primero que se corre en el laboratorio para separar "no conecta" de "la visión decide mal". Trae medición de latencia (`t`) y ráfaga a 10 Hz (`r`).

Verificado después de todo esto: 39 pruebas OK, y la evaluación sigue en 91.1%, 4 saltos y 5/5 recuperaciones.

Estado contra la rúbrica: `docs/estado-vs-rubrica.md`.

# Especificación y plan del Reto 1

> **Documento central del proyecto.** Aquí se define qué hay que construir (requisitos), cómo se sabe que está bien (criterios de aceptación y Definition of Done) y quién hace qué (plan de tareas). Si algo del código o de otro documento contradice esto, se corrige uno de los dos y se registra en el [registro de cambios](#15-registro-de-cambios).
>
> Versión 1.3 · 2026-09-28 · Reglas del repo en [`AGENTS.md`](../AGENTS.md) · Técnicas auditadas con `auditor-tecnicas` contra [`tecnicas-permitidas.md`](reto/tecnicas-permitidas.md).

## Contenido

1. [Propósito y alcance](#1-propósito-y-alcance)
2. [Entornos de ejecución](#2-entornos-de-ejecución)
3. [Datos de referencia: `vid/video1.mp4`](#3-datos-de-referencia-vidvideo1mp4)
4. [Convenciones](#4-convenciones)
5. [Requisitos funcionales](#5-requisitos-funcionales)
6. [Requisitos no funcionales](#6-requisitos-no-funcionales)
7. [Restricciones de técnicas](#7-restricciones-de-técnicas)
8. [Definition of Done](#8-definition-of-done)
9. [Plan de trabajo](#9-plan-de-trabajo)
10. [Protocolo de pruebas](#10-protocolo-de-pruebas)
11. [Trazabilidad con la rúbrica](#11-trazabilidad-con-la-rúbrica)
12. [Preguntas abiertas](#12-preguntas-abiertas)
13. [Riesgos](#13-riesgos)
14. [Estado actual](#14-estado-actual)
15. [Registro de cambios](#15-registro-de-cambios)

---

## 1. Propósito y alcance

**Qué construimos:** el "cerebro" de un robot seguidor de línea. Por cada frame de la cámara del celular montado en el robot, el sistema entrega una `Decision` (acción + giro + razón) que:

- mantiene al robot sobre la línea guía,
- lo detiene ante una señal roja (PARE) el tiempo que indique el docente,
- lo deja continuar ante una señal verde (SIGA),
- recupera la línea si la pierde.

**Qué se evalúa** (ver [rúbrica](reto/rubrica.md)): recorrido (corrección de trayectoria, intervenciones, PARE, SIGA, tiempo), cumplimiento de técnicas, diferenciación de la estrategia, póster, análisis de resultados, comunicación verbal y participación de los tres.

**Fuera de alcance** mientras el profesor no diga lo contrario (ver [P-02](#12-preguntas-abiertas)): control de motores y hardware del robot, y cualquier técnica fuera de la [lista permitida](reto/tecnicas-permitidas.md).

## 2. Entornos de ejecución

| Entorno | Para qué | Comando | Fuente |
|---|---|---|---|
| **Desarrollo (por defecto)** | Programar y calibrar sin celular; resultados repetibles | `uv run main.py` | `vid/video1.mp4`, se repite al terminar y se reproduce a su velocidad real |
| **Prueba real** | Ensayos en pista y competencia | `uv run main.py --fuente http://IP:PUERTO/ [--usuario u --contrasena p]` | Cámara del celular por WiFi (IP Camera Lite) |
| Otro video | Videos del profesor o grabaciones propias | `uv run main.py --fuente datos/videos/<x>.mp4` | Archivo |
| Webcam | Pruebas rápidas de color con objetos en mano | `uv run main.py --fuente 0` | Webcam del PC |
| Sin ventanas | Métricas objetivas (DoD) | `uv run python tools/evaluar_video.py [video] [--config json] [--csv f.csv]` *(T1.1, hecho)* | Archivo |

Reglas:

- La variable de entorno `CAMARA_URL` reemplaza la fuente por defecto. Así cada integrante puede dejar fija la IP de su celular sin tocar el código.
- `--config <json>` carga una calibración sin tocar el código. Perfiles versionados en `configs/`: `video1.json` (señales cuadradas) y `video1-kmeans.json` (calibrado con `tools/calibrar_clusters.py`).
- `vid/video1.mp4` **no se sube al repo** (`*.mp4` está en `.gitignore`). Cada integrante lo pone en `vid/` de su copia local.
- Un requisito se considera **cumplido** solo cuando pasa en desarrollo (video1) **y** en prueba real (celular). Pasar solo con el video no basta.

## 3. Datos de referencia: `vid/video1.mp4`

Medido el 2026-09-28. Estos datos condicionan los requisitos; si cambia el montaje de la cámara, hay que volver a medirlos.

| Propiedad | Valor |
|---|---|
| Resolución | 478 × 850 (vertical) · 25 FPS · 690 frames (27.5 s) |
| **Chasis del robot** | Ocupa desde **~54 % del alto hacia abajo**: sensor ultrasónico, cables y baterías verdes, naranjas y amarillas. **No es pista.** |
| Línea guía | Cinta oscura con textura, ancha. HSV ≈ H libre, **S 18–23, V 68–83** |
| Fondo | Papel blanco. HSV ≈ S 7–16, **V ~195** |
| Señal verde | Papel **cuadrado** rotado. HSV ≈ **H 68–70**, S 150–177, V ~140. Frames **~24–131** |
| Señal roja | Papel **cuadrado** rotado, rojo tirando a magenta. HSV ≈ **H 174**, S ~198, V ~190. Frames **~582–689** |
| Cinta transversal | Cinta negra que cruza la línea bajo cada señal. HSV ≈ V ~30 (más oscura que la línea) |
| Distractor rojo | Papel rojo **fuera de la pista**, cortado por el borde superior derecho. Frames **~172–195** |
| Distractor amarillo | Papel amarillo fuera de la pista. Frames **~240–320** |
| Baterías del robot | Una batería HSV ≈ H 41, S 219 queda **dentro** del rango verde actual (40–85) |
| Curva | La línea sale por el borde izquierdo alrededor de los frames 250–300 |

**Consecuencias directas:**

1. Las ROI por defecto (`roi_linea_cercana = 0.70–1.00`, `roi_senal = 0.00–0.70`) miran el chasis del robot. Hay que moverlas por encima del 0.54 (T1.2).
2. `hsv_linea` con V ≤ 80 corta la línea (V llega a 83). Hay que subirlo a ~110.
3. En el video las señales son **cuadradas** y la especificación pide **octágonos**. El filtro de forma tiene que ser configurable (ver [P-01](#12-preguntas-abiertas)).
4. La cinta transversal suma área oscura en forma de "T" junto a la línea y puede desplazar el centroide (RF-05).

## 4. Convenciones

- **Desviación:** de −1.0 (línea en el borde izquierdo de la ROI) a +1.0 (borde derecho); 0.0 = centrada. **Giro:** mismo signo y rango.
- **ROI:** franjas horizontales en fracción del alto (0.0 arriba, 1.0 abajo), medidas sobre el frame ya redimensionado.
- **Rangos HSV:** en la escala de OpenCV: H 0–179, S 0–255, V 0–255.
- **Frame "confirmado":** la señal aparece en `frames_confirmacion_senal` frames seguidos.
- **Prioridad (MoSCoW):** **M** = obligatorio para competir · **S** = importante para la nota · **C** = si da el tiempo.

## 5. Requisitos funcionales

Cada requisito tiene un criterio de aceptación **verificable**. "Video1" = `vid/video1.mp4` evaluado con `tools/evaluar_video.py`.

### 5.1 Captura

| ID | Prio | Requisito | Criterio de aceptación | Estado |
|---|---|---|---|---|
| RF-01 | M | Leer frames de una URL de celular (con o sin credenciales), de un archivo de video o de un índice de webcam | Con cada tipo de fuente, `main.py` muestra el video y la decisión | ✅ |
| RF-02 | M | Si se pierde la señal de la cámara, reconectar sin cerrar el programa | Apagar el WiFi del celular 3 s y volverlo a encender: el programa sigue solo | ✅ (probar en T6.1) |
| RF-03 | M | Sin argumentos, usar `vid/video1.mp4` en bucle y a su velocidad real | `uv run main.py` reproduce el video sin parar hasta pulsar `q`; al volver al inicio, el estado del robot se reinicia | ✅ 2026-09-28 |

### 5.2 Línea guía

| ID | Prio | Requisito | Criterio de aceptación |
|---|---|---|---|
| RF-04 | M | Segmentar la línea dentro de la ROI cercana y de la lejana, excluyendo el chasis del robot | En `--mascaras`, la máscara de línea no tiene píxeles del chasis en ningún frame del video1 (✅ 2026-09-28 en video1; falta celular) |
| RF-05 | M | Calcular el centro de la línea (centroide del contorno principal) y su desviación normalizada | Video1: línea detectada en **≥ 95 %** de los frames. La cinta transversal parte la línea cuando la señal la tapa (frames ~106–125); fuera de esa ventana la desviación no salta más de 0.3 entre frames seguidos, y dentro no más de 0.6 (✅ 2026-09-28: 99.1 %, salto máx. 0.54 en el frame 122; falta celular) |
| RF-06 | M | El signo de la desviación corresponde al lado de la línea | En `tools/probar_linea.py`: línea sintética a la izquierda da desviación < −0.3, a la derecha > +0.3, al centro \|d\| < 0.1. Espejar la imagen invierte el signo (✅ 2026-09-28: `probar_linea.py` pasa) |
| RF-07 | M | Reportar "no detectada" si no hay línea o si su área es menor a `area_minima_linea` | ROI en blanco o solo ruido: `detectada = False` y ninguna excepción (✅ 2026-09-28: `probar_linea.py` pasa) |
| RF-08 | S | Anticipar curvas con el horizonte: centros de la línea encadenados de cerca a lejos (`linea.mirar_adelante`, `peso_horizonte`). Reemplaza la mezcla suelta con la franja lejana (`peso_linea_lejana`, medida como peor) | En los 5 clips de descarrilamiento el giro apunta al lado correcto más frames antes de perder la línea que sin horizonte, sin subir saltos ni zigzag en `evaluar.py` (✅ 2026-09-29: 269 → 333 frames, 0 saltos, 0 zigzag; falta lazo cerrado, ver decisión 0007) |

### 5.3 Señales

| ID | Prio | Requisito | Criterio de aceptación |
|---|---|---|---|
| RF-09 | M | Detectar la señal roja (dos rangos de H) y la verde por color | Video1: hay candidato rojo en ≥ 80 % de los frames 600–689 y verde en ≥ 80 % de los frames 40–110 |
| RF-10 | M | Validar la forma: número de vértices (`approxPolyDP`), relación de aspecto y circularidad, con rangos en `config` | `tools/probar_senales.py`: el octágono rojo y el verde sintéticos se aceptan; el círculo, el triángulo y el rectángulo 3:1 se rechazan. Con el perfil `configs/video1.json` se aceptan los cuadrados del video |
| RF-11 | M | Descartar candidatos que tocan el borde de la ROI (señal cortada o fuera de la pista) | Video1: **ningún** PARE en los frames ~172–195 (distractor rojo) ni por el papel amarillo |
| RF-12 | M | Ignorar el chasis del robot (baterías verdes y naranjas) | Video1: ningún candidato con centro dentro del 54 % inferior del frame |
| RF-13 | M | Con varias señales, devolver la de mayor área (la más cercana) | Prueba sintética con dos octágonos: se devuelve el mayor |
| RF-14 | S | Solo obedecer señales lo bastante cerca (`area_minima_senal`) y confirmadas en N frames | Ya implementado en `control.confirmar_senal`. Video1: exactamente **1 PARE** confirmado en 582–689 y **1 SIGA** en 24–131 por pasada |

### 5.4 Control

| ID | Prio | Requisito | Criterio de aceptación | Estado |
|---|---|---|---|---|
| RF-15 | M | Giro proporcional a la desviación, con zona muerta | `tools/probar_control.py` pasa | ✅ |
| RF-16 | M | PARE confirmado: acción `PARAR` durante `segundos_pare`; no obedecer la misma señal dos veces (`espera_entre_senales`) | `probar_control.py` pasa. Video1: HUD en `DETENIDO` durante `segundos_pare` ± 0.2 s | ✅ lógica / ⬜ video |
| RF-17 | M | SIGA: continuar; si `siga_reanuda`, corta la espera del PARE | `probar_control.py` pasa | ✅ |
| RF-18 | M | Línea perdida: mantener el rumbo `frames_para_buscar` frames y luego girar hacia el último lado visto (`BUSCANDO`) | `probar_control.py` pasa. En la pista: tras sacar el robot de la línea, la recupera en ≤ 3 s (T6.3) | ✅ lógica / ⬜ pista |

### 5.5 Calibración, visualización y registro

| ID | Prio | Requisito | Criterio de aceptación |
|---|---|---|---|
| RF-19 | S | Calibrar los rangos HSV con K-Means (clase 4) a partir de un frame real y guardarlos como JSON | `tools/calibrar_clusters.py --fuente vid/video1.mp4` genera un JSON que, cargado con `--config`, cumple RF-05 y RF-09. Recalibrar toma < 60 s (🟡 2026-09-28: `calibrar_clusters.py` listo, línea 99.0 % en video1; rojo y verde por validar con F3) |
| RF-20 | M | HUD con estado, acción, razón, FPS y ROI dibujadas; mosaico de máscaras con `--mascaras` | ✅ Existe. Tiene que seguir funcionando con las ROI nuevas |
| RF-21 | S | Registro por frame en CSV: `t, frame, fps, estado, accion, giro, desviacion, linea_detectada, senal, area_senal` | `main.py --registro corrida.csv` y `evaluar_video.py` lo escriben; se abre en pandas o Excel sin errores (🟡 `evaluar_video.py --csv` ya lo escribe; falta `main.py --registro` (T5.1)) |
| RF-22 | C | Grabar la vista con el HUD a un `.mp4` (`--grabar`) | Requiere respuesta de P-06. El archivo se reproduce y dura lo mismo que la corrida |
| RF-23 | C | Enviar la `Decision` al robot físico (`reto/actuador.py`) | Depende de P-02. Ningún otro módulo cambia (arquitectura §3) |

## 6. Requisitos no funcionales

| ID | Requisito | Medida / cómo se verifica |
|---|---|---|
| RNF-01 | **Tiempo real** | Pipeline completo ≤ **25 ms/frame** en el portátil del equipo (medido por `evaluar_video.py`). Con la cámara real, **≥ 15 FPS** en el HUD |
| RNF-02 | **Solo técnicas permitidas** | 0 técnicas prohibidas y 0 de zona gris sin respuesta del profesor. Se verifica con el agente `auditor-tecnicas` sobre el diff |
| RNF-03 | **Trazabilidad de técnicas** | Cada función que usa una técnica de visión dice en su docstring cuál es y de qué clase sale |
| RNF-04 | **Sin números mágicos** | Todo umbral, rango, ROI o tiempo vive en `reto/config.py`. Revisión: grep de literales numéricos en `linea.py` y `senales.py` (se admiten 0, 1, 2 y 255 en operaciones obvias) |
| RNF-05 | **Explicabilidad** | Cualquier integrante explica cualquier módulo en ≤ 2 min sin leer el código (se valida en T8.3) |
| RNF-06 | **Pruebas sin cámara** | Línea, señales y control tienen script de prueba en `tools/` que corre sin cámara ni ventanas |
| RNF-07 | **Robustez** | Ninguna excepción no controlada en 3 pasadas completas del video1 ni en 5 minutos de cámara real |
| RNF-08 | **Reproducibilidad** | `uv sync && uv run main.py` funciona en los 3 portátiles. Cada calibración usada en un ensayo queda en `configs/` con fecha |
| RNF-09 | **Contratos estables** | `reto/tipos.py` solo cambia de común acuerdo entre los tres, avisado en el PR |
| RNF-10 | **Estilo** | Español en nombres y comentarios, funciones cortas con una sola responsabilidad (ver `AGENTS.md`) |

## 7. Restricciones de técnicas

Resultado del agente `auditor-tecnicas` (2026-09-28). El código actual **no tiene** técnicas prohibidas ni de zona gris.

| Etapa | ✅ Usar | ⛔ No usar (zona gris o no vista) |
|---|---|---|
| Preprocesamiento | `cv2.resize` (clase 1), `cv2.GaussianBlur` (clase 3) | — |
| Línea | `cvtColor` HSV/Lab (clase 1), `inRange` / `threshold` (clase 2), `morphologyEx` OPEN/CLOSE, `erode`, `dilate` (clase 3), `findContours`, `contourArea`, `moments` (clase 3) | `fitLine` (no vista), `HoughLines(P)` y `minAreaRect` (zona gris, P-04) |
| Señales | `inRange` ×2 + `bitwise_or` (clase 2), morfología (clase 3), `findContours`, `contourArea`, `arcLength`, `approxPolyDP`, `boundingRect` (clase 3), circularidad calculada a mano | `matchShapes`, `matchTemplate`, `HoughCircles` (zona gris), cualquier clasificador |
| Calibración | `sklearn.cluster.KMeans` (clase 4) | `cv2.kmeans` (zona gris, P-05), DBSCAN, GMM y cualquier otro clustering |
| Registro | `csv` de la librería estándar | `cv2.VideoWriter` hasta tener respuesta de P-06 |

Regla: si algo no está en la columna ✅, **no se usa**. Se anota como pregunta en la sección 12.

## 8. Definition of Done

### 8.1 DoD general (toda tarea de código)

Una tarea está **terminada** solo si se cumple **todo** esto:

- [ ] Se cumplen los criterios de aceptación de los RF/RNF que cubre la tarea (sección 5 y 6).
- [ ] `uv run main.py` corre el video1 completo al menos una vez sin excepciones.
- [ ] Todos los scripts de `tools/probar_*.py` pasan, no solo el de la tarea.
- [ ] Sin números mágicos: los parámetros nuevos están en `config.py` con un comentario de una línea (RNF-04).
- [ ] Docstring con la técnica y la clase de origen (RNF-03).
- [ ] `auditor-tecnicas` no reporta nada prohibido ni zona gris sin respuesta (RNF-02).
- [ ] Si cambió `tipos.py` o `config.py`, los otros dos están enterados (queda escrito en el PR).
- [ ] Rama propia → PR a `main` → **revisión de otro integrante**, que corre el video1 en su máquina antes de aprobar.
- [ ] La casilla de la tarea está marcada en la sección 9 de este documento, con fecha.
- [ ] El dueño se lo explicó al menos a otro integrante (RNF-05).

### 8.2 DoD adicional por tipo de tarea

| Tipo | Además del DoD general |
|---|---|
| **Detección** (línea, señales) | Probada en video1 **y** en al menos un video grabado con el celular real (T0.2). Captura de `--mascaras` guardada en `docs/img/` para el póster |
| **Calibración** | JSON guardado en `configs/<nombre>-<fecha>.json`, con el frame usado, y el procedimiento anotado en la bitácora |
| **Ensayo en pista** | Entrada de `docs/bitacora.md` llenada **el mismo día**, con el CSV de la corrida en `datos/corridas/` y métricas: descarrilamientos, intervenciones, PARE y SIGA correctos, tiempo |
| **Decisión de diseño** | Archivo en `docs/decisiones/NNNN-*.md` con la plantilla |
| **Documento o póster** | Revisado por los tres; cada técnica citada coincide con los docstrings |

### 8.3 DoD del proyecto (listo para competir)

- [ ] Todos los RF de prioridad **M** cumplidos en video1 **y** con la cámara real.
- [ ] 3 corridas completas seguidas en la pista con **0 intervenciones**, todos los PARE y SIGA correctos (T6.5).
- [ ] `configs/pista-final.json` congelado y tag `v1.0` en `main`.
- [ ] Póster, análisis de resultados y sustentación ensayados (fase 8).
- [ ] Preguntas abiertas P-01 a P-03 resueltas.

## 9. Plan de trabajo

Formato: **ID · tarea · dueño · depende de · cubre**. Cada tarea hereda el DoD general (8.1) además de su propio criterio.

```
F0 Desbloqueo ─► F1 Medición ─┬─► F2 Línea ───┬─► F4 K-Means ─► F6 Ensayos ─► F8 Entregables
                              └─► F3 Señales ─┘        ▲
                                  F5 Integración ──────┘      F7 Estrategia (continuo)
```

Las fases F2 y F3 van **en paralelo** (archivos distintos, contrato común en `tipos.py`).

### F0 — Desbloqueo (esta semana)

- [x] **T0.1** · Fuente por defecto = `vid/video1.mp4`, en bucle y a su velocidad real · Daniel · — · RF-03. *Hecho 2026-09-28 en `main.py`; **Santiago** tiene que revisarlo porque es su archivo.*
- [ ] **T0.2** · Grabar 3 videos con el celular **montado en el robot real** (recta, curva cerrada, PARE + SIGA), con la resolución y la app de la competencia, en `datos/videos/` · Santiago · — · RF-04..14. *DoD: los 3 videos corren con `--fuente` y el chasis aparece en la misma posición que en video1 (si no, se registra la nueva frontera).*
- [ ] **T0.3** · Bajar los videos del profesor ([Drive](https://drive.google.com/drive/folders/1m6mazLjCKPlwaVpH-arGSYZMF_P2KC77?usp=sharing)) a `datos/videos/` · Santiago · — · —. *DoD: se reproducen con `--fuente`.*
- [ ] **T0.4** · Desactivar el texto sobreimpreso de IP Camera Lite (fecha, batería, "Powered by") · Santiago · — · RF-12. *DoD: captura del HUD sin marcas de agua en la bitácora.*
- [ ] **T0.5** · Llevarle al profesor las preguntas P-01 a P-06 y anotar las respuestas en la sección 12 y en `tecnicas-permitidas.md` · Juan David · — · RNF-02.
- [x] **T0.6** · Limpieza: mover `linea2.jpeg` a `datos/pruebas/` (sacarlo del índice de git) y agregar `temp/` y `vid/` al `.gitignore` · Daniel · — · —.

### F1 — Base de medición

- [x] **T1.1** · `tools/evaluar_video.py [video] [--config json] [--csv salida.csv]`: corre el pipeline sin ventanas y reporta el % de frames con línea, los rangos de frames con cada señal confirmada, los cambios de estado, los ms por frame y el máximo salto de desviación · Daniel · T0.1 · RNF-01, RF-21 y todos los criterios "Video1". *DoD: con los stubs actuales reporta 0 % de línea y 0 señales; la salida es texto legible más el CSV opcional. Hecho 2026-09-28; `procesar_frame` recibe `ahora` para simular el reloj.*
- [x] **T1.2** · Ajustar los valores por defecto de `config.py` a la geometría real: `roi_linea_cercana ≈ (0.38, 0.53)`, `roi_linea_lejana ≈ (0.18, 0.38)`, `roi_senal ≈ (0.00, 0.54)`, `hsv_linea` con V ≤ 110. Crear `configs/video1.json` con los rangos de forma para cuadrados (P-01) · Los tres · T0.2 · RF-04, RF-12. *DoD: en `--mascaras` ninguna ROI toca el chasis en todo el video1; commit acordado por los tres. Hecho 2026-09-28: ROI y `hsv_linea` en `config.py` y `configs/video1.json` (cuadrados); falta que Santiago y Juan David lo revisen y calibrar `precision_poligono` en T3.5.*

### F2 — Línea guía (Daniel)

- [x] **T2.1** · `segmentar_linea(roi, config) -> mascara`: HSV, `inRange(hsv_linea)`, apertura y cierre · T1.2 · RF-04.
- [x] **T2.2** · `contorno_principal(mascara, config)`: el contorno de mayor área si supera `area_minima_linea`; si no, `None` · T2.1 · RF-07.
- [x] **T2.3** · `detectar()`: centroide por `moments` (con protección para `m00 == 0`), `desviacion_desde_centro` y `ResultadoLinea` completo, con máscara · T2.2 · RF-05, RF-06.
- [x] **T2.4** · Robustez frente a la cinta transversal: si el contorno es mucho más ancho que la línea normal, calcular el centroide solo con la mitad inferior de la ROI (o subir la apertura). Parámetro en config · T2.3 · RF-05. *Hecho 2026-09-28 de otra forma: `ancho_maximo_linea` descarta contornos anchos y `Estado.ultimo_centro_linea` elige el trozo más cercano a la posición previa. Salto máx. en video1: 0.54 (frame 122), dentro de la ventana de la cinta.*
- [x] **T2.5** · `tools/probar_linea.py`: líneas sintéticas (izquierda, centro, derecha, espejada, vacía, con cinta en T) más `datos/pruebas/linea2.jpeg` · T2.3 · RF-06, RF-07, RNF-06.
- [ ] **T2.6** · Si el blanco o los reflejos se cuelan en la máscara, alternativa con el canal L de Lab + `threshold` (clases 1 y 2), elegible con `config.espacio_linea` · T2.3 · RF-04. *Opcional: solo si T2.3 no alcanza el 95 %.*

**DoD de F2:** `evaluar_video.py` sobre video1 reporta línea detectada en ≥ 95 % de los frames y saltos ≤ 0.3; `probar_linea.py` pasa; se cumple el DoD general.

### F3 — Señales (Juan David)

- [ ] **T3.1** · `mascaras_color(roi, config) -> {"PARE": m, "SIGA": m}`: rojo = `inRange(rojo_bajo) | inRange(rojo_alto)`, verde = `inRange(verde)`, más apertura y cierre · T1.2 · RF-09.
- [ ] **T3.2** · `candidatos(mascara, tipo, config)`: contornos con área ≥ `area_minima_senal` que **no tocan el borde de la ROI** (con `boundingRect` y un margen en config), aproximados con `approxPolyDP(precision_poligono · arcLength)` y filtrados con `es_octagono` · T3.1 · RF-10, RF-11, RF-12.
- [ ] **T3.3** · `detectar()`: el candidato de mayor área entre los dos colores → `ResultadoSenal` completo, con la máscara combinada para el mosaico · T3.2 · RF-13.
- [ ] **T3.4** · `tools/probar_senales.py` con figuras sintéticas (`cv2.fillPoly` y `cv2.circle`): octágono rojo, octágono verde, círculo rojo, triángulo rojo, rectángulo verde 3:1, octágono cortado por el borde y dos octágonos de distinto tamaño · T3.3 · RF-10, RF-11, RF-13, RNF-06.
- [ ] **T3.5** · Calibrar la forma en video1 y en los videos de T0.2: vértices reales que da `approxPolyDP` con desenfoque de movimiento, relación de aspecto en perspectiva y circularidad. Dejar los valores en `configs/video1.json` y en la configuración por defecto (octágonos) · T3.3, T0.2 · RF-10, RF-14.

**DoD de F3:** `evaluar_video.py` sobre video1 con `configs/video1.json` reporta 1 SIGA confirmado en ~24–131, 1 PARE en ~582–689 y **0** señales en el resto (distractores de 172–195 y 240–320 incluidos); `probar_senales.py` pasa; se cumple el DoD general.

### F4 — Calibración con K-Means (Daniel, apoyo de Santiago) · diferenciador

- [x] **T4.1** · `tools/calibrar_clusters.py --fuente <video|imagen> [--frame N] --k 5`: toma el frame, recorta la ROI sin el chasis, lo pasa a HSV y corre `KMeans` sobre los píxeles. Muestra los centroides como parches numerados · F2, F3 · RF-19. *Hecho 2026-09-28.*
- [x] **T4.2** · El usuario elige qué cluster es línea, rojo y verde. El script calcula cada rango (centroide ± k·desviación estándar por canal, con H del rojo que da la vuelta en 0/179) y lo guarda con `Config.guardar()` en `configs/` · T4.1 · RF-19. *Hecho 2026-09-28; la línea admite varios clusters (`--linea 3,5`).*
- [ ] **T4.3** · Validar: la calibración generada desde video1 cumple los DoD de F2 y F3 · T4.2.
- [x] **T4.4** · `docs/decisiones/0006-calibracion-kmeans.md` · T4.3 · Diferenciación.

**DoD de F4:** recalibrar desde cero en < 60 s cronometrado, y la calibración resultante pasa `evaluar_video.py`.

### F5 — Integración y telemetría (Santiago, apoyo de Juan David)

- [ ] **T5.1** · `main.py --registro corrida.csv` (RF-21), con las mismas columnas que `evaluar_video.py` · T1.1.
- [ ] **T5.2** · `main.py --grabar salida.mp4` (RF-22) · P-06.
- [x] **T5.6** · Flujo alterno `uv run main.py --index`: el simulador (`simulacion/index.html?puente=1`) manda su canvas como JPEG a un servidor local (`reto/simulador.py`, solo librería estándar) y recibe la orden `{accion, giro}` de la respuesta. `reto/actuador.py` define la interfaz `Actuador`; para el robot real solo se agrega otra clase y se cambia en `main.py` · Daniel · T5.4 · RF-23. *Hecho 2026-09-28 (2 de 3 piezas: puente y calibración `configs/simulador.json`); falta afinar el seguimiento: hoy la línea se detecta y el robot gira, pero todavía se descarrila. Ojo: con varias pestañas del simulador abiertas se mezclan los frames.*
- [ ] **T5.3** · Simulador: cambiar `drawPentagon` por un octágono (`simulacion/index.html:580`) y grabar un video del simulador para `datos/videos/` · — · Prueba extra de RF-10. *Opcional.*
- [ ] **T5.4** · `reto/actuador.py`: traducir `Decision` al protocolo del robot (RF-23) · P-02. *Solo si hay hardware.*
- [ ] **T5.5** · Medir FPS con la cámara real y todo encendido. Si baja de 15, reducir `ancho_proceso` (480 → 360 → 320) y volver a validar F2 y F3 · F2, F3 · RNF-01.

### F6 — Ensayos con la cámara real (los tres)

Cada ensayo cumple el DoD de "Ensayo en pista" (8.2).

- [ ] **T6.1** · Ensayo de conexión: 5 min de stream, cortar el WiFi 3 s, medir FPS · RF-02, RNF-07.
- [ ] **T6.2** · Ensayo de línea: recta y curvas. Ajustar `ganancia_giro`, `zona_muerta` y `peso_linea_lejana`. Meta: 0 descarrilamientos en 3 vueltas · RF-05, RF-08, RF-15.
- [ ] **T6.3** · Ensayo de recuperación: sacar el robot de la línea a propósito 5 veces. Meta: la recupera en ≤ 3 s, 5 de 5 veces · RF-18.
- [ ] **T6.4** · Ensayo de señales: 10 pasadas por PARE y 10 por SIGA, con objetos rojos y verdes de distractor cerca. Meta: 10/10 correctas y 0 falsos positivos · RF-09..14, RF-16, RF-17.
- [ ] **T6.5** · Ensayo general cronometrado con las reglas de la competencia. Meta: DoD del proyecto (8.3) · Todo.
- [ ] **T6.6** · Ensayo con otra luz: recalibrar con `calibrar_clusters.py` y repetir T6.4 · RF-19.

### F7 — Estrategia y documentación (Juan David, aportes de todos)

- [ ] **T7.1** · `docs/decisiones/0004-estrategia.md`: cuáles de las 4 estrategias de `arquitectura.md` §6 entran y por qué (recomendado: las 4).
- [ ] **T7.2** · Tabla "nosotros vs. enfoque típico" (un solo umbral, sin forma ni persistencia) para el criterio de diferenciación.
- [ ] **T7.3** · Actualizar `arquitectura.md` §9 y el "Estado" del `README.md` después de cada fase.
- [ ] **T7.4** · Pasar `auditor-tecnicas` sobre todo `reto/` y `tools/` antes del tag `v1.0`.

### F8 — Entregables (los tres)

- [ ] **T8.1** · Análisis de resultados a partir de los CSV y la bitácora: **aciertos, errores, dificultades, limitaciones y mejoras** (la rúbrica pide los 5). Gráficas: desviación en el tiempo, FPS y detecciones.
- [ ] **T8.2** · Póster: problema → pipeline → cada etapa con su técnica y clase → máscaras reales → estrategia propia → resultados → limitaciones.
- [ ] **T8.3** · Sustentación cruzada: Daniel explica señales, Juan David explica la línea y Santiago explica el control y la calibración. Cada uno ≤ 2 min por módulo (RNF-05).
- [ ] **T8.4** · Kit del día de la competencia: `configs/pista-final.json` más uno de respaldo, hotspot propio, celular cargado, app sin marcas de agua, `calibrar_clusters.py` probado.

## 10. Protocolo de pruebas

| Nivel | Qué | Herramienta | Cuándo |
|---|---|---|---|
| 1. Unitario | Control, línea y señales con datos sintéticos | `tools/probar_control.py`, `probar_linea.py`, `probar_senales.py` | En cada commit |
| 2. Video de referencia | Métricas objetivas en video1 | `tools/evaluar_video.py vid/video1.mp4 --config configs/video1.json` | Antes de cada PR |
| 3. Videos reales | Mismo análisis en los videos de T0.2 y los del profesor | `evaluar_video.py datos/videos/*.mp4` | Antes de cada ensayo |
| 4. Cámara real | Robot en pista | `main.py --fuente <url> --registro ...` | Ensayos de F6 |

**Casos de prueba sobre video1** (resultado esperado):

| Caso | Frames | Esperado |
|---|---|---|
| CP-01 Seguimiento | 0–689 | Línea detectada ≥ 95 %, nunca `BUSCANDO` más de 10 frames seguidos |
| CP-02 SIGA | ~24–131 | 1 SIGA confirmado; nunca `DETENIDO` |
| CP-03 Distractor rojo | ~172–195 | 0 PARE |
| CP-04 Distractor amarillo y curva | ~240–320 | 0 señales; la desviación sigue la curva a la izquierda (negativa) |
| CP-05 PARE | ~582–689 | Exactamente 1 PARE; `DETENIDO` durante `segundos_pare` |
| CP-06 Chasis | todos | 0 candidatos con centro en el 54 % inferior |
| CP-07 Bucle | fin del video | Vuelve al inicio con el estado reiniciado y sin excepciones |

## 11. Trazabilidad con la rúbrica

| Criterio de la rúbrica | Requisitos | Tareas | Evidencia |
|---|---|---|---|
| Corrección de trayectoria | RF-04..08, RF-15 | F2, T6.2 | Bitácora, CSV, gráfica de desviación |
| Intervenciones humanas | RF-18, RNF-07 | T6.3, T6.5 | Bitácora |
| Reconocimiento de PARE | RF-09..14, RF-16 | F3, T6.4 | CP-05, bitácora |
| Reconocimiento de SIGA | RF-09..14, RF-17 | F3, T6.4 | CP-02, bitácora |
| Uso de técnicas | RNF-03 | Todas las de código | Docstrings, póster |
| Cumplimiento de restricciones | RNF-02, sección 7 | T0.5, T7.4 | Reporte del auditor |
| Tiempo de recorrido | RNF-01, RF-08 | T5.5, T6.2 | Cronómetro en T6.5 |
| Diferenciación | RF-08, RF-11, RF-14, RF-19 | F4, T7.1, T7.2 | Decisiones 0003 y 0004 |
| Comunicación verbal | RNF-05 | T8.3 | Ensayo de sustentación |
| Póster | — | T8.2 | Póster |
| Análisis de resultados | RF-21 | T8.1 | Documento de análisis |
| Participación del equipo | RNF-05 | T8.3 | Sustentación cruzada |

## 12. Preguntas abiertas

Las lleva Juan David (T0.5). Al responderse, se anota la respuesta aquí y se cierra la pregunta.

| ID | Pregunta | Impacto si no se resuelve | Respuesta |
|---|---|---|---|
| **P-01** | En la competencia, ¿las señales son **octágonos** (como dice la especificación) o **cuadrados** (como en video1)? | Crítico: define `vertices_octagono` | — |
| **P-02** | ¿Hay robot físico que reciba la decisión? ¿Por qué medio (serial, HTTP, Bluetooth), o se califica con el video y el HUD? | Crítico: define si existe T5.4 | — |
| **P-03** | ¿Cuántos segundos dura el PARE? ¿Cuándo es la competencia y cuántos intentos hay? | `segundos_pare`; fechas del plan | — |
| P-04 | ¿Se permite `cv2.minAreaRect` para la orientación de la línea? | Solo mejora opcional | — |
| P-05 | ¿`cv2.kmeans` cuenta como la técnica de la clase 4? | Ninguno: se usa sklearn | — |
| P-06 | ¿Se permite `cv2.VideoWriter` para grabar las corridas? | Define RF-22 | — |

## 13. Riesgos

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Señales cuadradas en los ensayos y octagonales en la competencia (o al revés) | Alta | Alto | Filtro de forma configurable, perfiles en `configs/`, P-01 |
| Chasis o baterías (verdes y naranjas) confundidos con señales | Alta | Alto | ROI por encima del 0.54 (T1.2), RF-12, CP-06 |
| La cinta transversal desplaza el centroide de la línea | Media | Medio | T2.4, criterio de saltos ≤ 0.3 |
| Cambio de luz en el salón | Media | Alto | K-Means (F4), T6.6 |
| Desenfoque de movimiento redondea las esquinas (vértices inestables) | Media | Medio | Rango de vértices amplio + circularidad + persistencia (T3.5) |
| Latencia del WiFi o bajos FPS | Media | Alto | Buffer de 1 frame (ya está), T5.5, hotspot propio |
| Otros objetos de color en la escena | Media | Medio | RF-11 (borde), área mínima, persistencia, CP-03 |
| Un integrante no puede explicar el pipeline | Baja | Alto | T8.3 |
| Fecha de la competencia desconocida | — | Alto | P-03; sin ella no hay plazos por fase |

## 14. Estado actual

Al 2026-09-28.

| Componente | Estado |
|---|---|
| `camara.py`, `main.py` (RF-01..03) | ✅ Fuente por defecto `vid/video1.mp4` en bucle |
| `config.py`, `tipos.py` | ✅ ROI ajustadas al video1 (T1.2) · `tipos.Estado` ganó `ultimo_centro_linea` y `config` ganó `ancho_maximo_linea`: avisar a los otros dos |
| `control.py` (RF-15..18) | ✅ `probar_control.py` pasa |
| `pipeline.py` (RF-08), `overlay.py` (RF-20) | ✅ Listos · pipeline a 2.5 ms/frame con los stubs |
| `linea.py` | ✅ Implementado (F2): 99.1 % de frames con línea, 2.3 ms/frame · ⬜ falta probar con video real del celular (T0.2) |
| `senales.py` | ⬜ Stub; `circularidad` y `es_octagono` sí existen (F3) |
| `evaluar_video.py`, `probar_linea.py` | ✅ |
| `calibrar_clusters.py` | ✅ `configs/video1-kmeans.json`: línea 99.0 %, salto máx. 0.56 · ⬜ rojo y verde por validar con F3 (T4.3) |
| `probar_senales.py` | ⬜ Por crear |
| Ensayos en pista | ⬜ 0 |
| Póster y análisis | ⬜ 0 |
| Auditoría de técnicas | ✅ Sin hallazgos |

**Avance de Daniel (rama `feat/linea-y-medicion`, sin PR todavía):** T0.1, T0.6, T1.1, T1.2, T2.1–T2.5, T4.1, T4.2 y T4.4 hechas. Con `configs/video1-kmeans.json`: línea 99.0 %, salto máx. 0.56 (frame 110, dentro de la cinta), máx. 3 frames seguidos en BUSCAR, 2–3 ms/frame. `probar_linea.py` y `probar_control.py` pasan.

**Pendiente de mi lado:** T2.6 (opcional, no hace falta), T4.3 (validar rojo y verde cuando F3 exista), T5.1 (`--registro`, es de Santiago) y validar F2 con video del celular.

**Cambios en archivos compartidos, por avisar a Santiago y Juan David:** `tipos.Estado.ultimo_centro_linea`, `config.ancho_maximo_linea`, ROI nuevas en `config.py` y `procesar_frame(..., ahora)`.

**Bloqueos:** T0.2–T0.5 (Santiago y Juan David) y F3 (Juan David). Sin T0.2 no se puede validar la línea con el celular real.

**Próximo paso:** abrir PR con esta rama, T0.2–T0.5 y F3.

## 15. Registro de cambios

| Fecha | Versión | Cambio |
|---|---|---|
| 2026-09-29 | 1.5 | RF-08: horizonte (`linea.mirar_adelante`, `pipeline.anticipar`), parámetros nuevos en `config.py`, HUD y decisión 0007 |
| 2026-09-28 | 1.4 | T5.6: flujo `--index`, `reto/actuador.py`, `reto/simulador.py`, `configs/simulador.json` |
| 2026-09-28 | 1.3 | Estado por requisito (RF-04..08, 19, 21), avance de Daniel, cambios compartidos y bloqueos en la sección 14 |
| 2026-09-28 | 1.2 | F4: `tools/calibrar_clusters.py` (T4.1, T4.2) y decisión 0006 (T4.4). T4.3 queda pendiente hasta tener F3 |
| 2026-09-28 | 1.1 | RF-05: criterio de saltos relajado a 0.6 dentro de la ventana de la cinta transversal (medido en video1). T0.6, T1.1, T1.2 y F2 hechas |
| 2026-09-28 | 1.0 | Primera especificación: requisitos, DoD, plan por fases y medición de video1. Fuente de desarrollo por defecto = `vid/video1.mp4` |

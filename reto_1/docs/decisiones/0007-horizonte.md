# 0007 — Horizonte: apuntar a dónde va la línea, no solo a dónde está

- **Fecha:** 2026-09-29
- **Estado:** propuesta
- **Deciden:** Daniel (avisar a Santiago y Juan David: toca `config.py`, `overlay.py` y una línea de `main.py`)

## Contexto
El control solo miraba la franja cercana: corregía cuando la curva ya estaba encima del carro. La idea de mezclar la franja lejana (`peso_linea_lejana`) empeoró las métricas porque esa franja se calcula suelta y a veces se va a otro trozo oscuro (diferencia media de 0.32 con la cercana). Todo tiene que salir de técnicas del curso.

## Decisión
`linea.mirar_adelante` corta la zona delante del carro (`roi_horizonte`) en `tramos_horizonte` tramos y, de abajo hacia arriba, toma el centroide de la línea en cada uno. Cada tramo elige el contorno más cercano al centro del tramo anterior, así que la cadena sigue **la misma** línea:

1. Segmentación igual que la línea: HSV + `inRange` + apertura y cierre (clases 1, 2 y 3).
2. Por tramo: contornos, área mínima, ancho máximo (`boundingRect`) y centroide por momentos (clase 3).
3. La cadena se corta si un tramo no tiene línea o si el centro salta más de `salto_maximo_tramo`. Los tramos de abajo pueden faltar (la barra de una señal o el sensor los tapan).
4. Un contorno más ancho que `ancho_maximo_tramo` es la barra negra de una señal, no la línea.
5. Punto objetivo: el tramo `tramo_objetivo` (o el último que se vio). Si la cadena termina pegada a un borde sin llegar arriba, la curva se sale del cuadro y el objetivo es ese borde (±1).
6. `pipeline.anticipar`: `d = (1 - peso_horizonte) · d_cercana + peso_horizonte · d_objetivo` (aritmética, clase 2).

El HUD dibuja la cadena y el objetivo (rojo si la curva se sale por el borde).

## Alternativas consideradas
- `peso_linea_lejana`: franja lejana sin conexión con la cercana, ya medida como peor.
- `fitLine`, `HoughLinesP`, `minAreaRect` para la dirección: no vistas o zona gris (P-04).
- Ajustar una curva con mínimos cuadrados (`np.polyfit`): funciona, pero no es del curso; el promedio ponderado alcanza.

## Consecuencias
Medido con `tools/evaluar.py` sobre los 9 clips (peso 0.5, tramo 6):

| | Antes | Con horizonte |
|---|---|---|
| Línea detectada | 91.1 % | 91.1 % |
| Saltos sospechosos | 0 | 0 |
| Zigzag | 0/s | 0/s |
| Frames con el giro ya hacia el lado correcto antes de perder la línea (5 clips de descarrilamiento) | 269 | **333 (+24 %)** |
| Salto máx. por frame (video4, barra de la señal) | 0.08 | 0.20 (meta ≤ 0.3) |
| Tiempo por frame | ~2.5 ms | ~4 ms |

- Se gana anticipación: el carro empieza a girar antes de que la curva llegue a la franja cercana.
- Gira más en general (desviación media 0.18 → 0.32): es lo esperado al apuntar adelante, pero en lazo cerrado podría sobrecorregir. Hay que confirmarlo en el simulador y en la pista (T6.2). Con `peso_horizonte = 0` queda como antes.
- Limitación: una curva casi horizontal se ve tan ancha como la barra de la señal y se descarta; la cadena se corta ahí y el control vuelve a depender de la franja cercana.
- Pruebas: `tests/test_horizonte.py` (recta, curva, espejo, salida por el borde, barra, mancha lejana).

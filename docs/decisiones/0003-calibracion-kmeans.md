# 0003 — Calibración de rangos HSV con K-Means

- **Fecha:** 2026-09-28
- **Estado:** propuesta
- **Deciden:** Daniel (revisan Santiago y Juan David)

## Contexto
Los rangos HSV de la línea, el rojo y el verde cambian con la luz del salón. Ajustarlos a mano el día de la competencia es lento y propenso a errores. En video1 la línea no tiene un color único: va de V ~18 (cinta transversal) a V ~83 (cinta con textura), con S bajo.

## Decisión
`tools/calibrar.py` toma frames reales (sin la zona del chasis), agrupa los píxeles (H, S, V) con `sklearn.cluster.KMeans` (clase 4) y la persona indica qué clusters son línea, rojo y verde. Cada rango sale de media ± N desviaciones por canal (N = 3.5 en video1) y se guarda como JSON para `main.py --config`. La línea admite varios clusters (`--linea 3,5`) y el rojo se calcula con el tono desplazado medio círculo, porque da la vuelta en 0/179.

## Alternativas consideradas
- **Rangos a mano:** lo que hacíamos; no escala a otra luz.
- **`cv2.kmeans`:** es la misma técnica, pero está en zona gris (P-05); sklearn es lo visto en clase.
- **Un solo cluster por clase:** en video1 dio entre 36 % y 73 % de frames con línea; con dos clusters y 3.5σ da 99.0 %.

## Consecuencias
- Recalibrar tarda ~4 s de cómputo más el tiempo de elegir clusters (meta < 60 s).
- Con video1: línea detectada en 99.0 % de los frames, salto máx. 0.56 (frame 110, dentro de la ventana de la cinta), máx. 3 frames seguidos en BUSCAR.
- Rojo y verde quedan por validar cuando F3 (`senales.py`) esté implementada (T4.3).
- Hay que vigilar que un rango demasiado ancho (σ alto) deje pasar el fondo; se comprueba siempre con `evaluar_video.py`.

# 0009 — Frenar en curva y anticiparla con la franja lejana

- **Fecha:** 2026-09-29
- **Estado:** propuesta
- **Deciden:** Santiago / Daniel / Juan David

## Contexto
En las curvas el robot se descarrila. La causa está en los pulsos del firmware:
`w` avanza 100 ms y `a`/`d` giran 30 ms, y cada comando ocupa un tick de 100 ms.
Con un giro mediano (`giro=0.5`) el actuador manda `w, d, w, d…`: por cada 30 ms
de giro hay 100 ms de avance, así que el robot se abre de la curva. Además la
velocidad era la misma en recta y en curva, y la franja lejana (`curvatura`)
solo se usaba en el HUD.

## Decisión
- `Decision` tiene un campo nuevo, `en_curva` (por defecto `False`, así que el
  código que ya existía sigue funcionando).
- `control.decidir` recibe `curvatura` y marca `en_curva` cuando
  `|giro| >= giro_para_frenar` (la curva ya llegó) o
  `|curvatura| >= curvatura_para_frenar` (la curva viene en camino). La
  curvatura **no cambia el rumbo**: solo la velocidad.
- En curva, `ActuadorRobot` manda solo una fracción de los `w`
  (`avance_en_curva`), repartida con un acumulador igual al del giro. En los
  ticks sin `w` el robot se queda quieto y el giro alcanza a corregir.
- `tools/evaluar.py` muestra la columna `curva_%` para calibrar los umbrales.

Técnicas: solo operaciones aritméticas sobre valores que ya se calculaban
(clase 2) y ROI (clase 1).

## Alternativas consideradas
- **Mezclar la franja lejana en la desviación** (`peso_linea_lejana`): ya se
  midió y empeora los clips (ver config). Por eso aquí la franja lejana solo
  decide la velocidad.
- **Bajar `--robot-ritmo`**: frena el recorrido completo, también en las rectas.
- **Girar en el sitio** (estado CURVA con umbral de entrada y de salida): queda
  de respaldo si todavía hay curvas cerradas que se salen.

## Consecuencias
- Con los clips del profesor frena en el 14–47 % de los frames; la vuelta
  será más lenta.
- Los números de los clips no dicen si ya no se descarrila: eso hay que
  probarlo en la pista. Si todavía se sale, bajar `avance_en_curva` (0.3) o
  `giro_para_frenar`; si va demasiado lento en las rectas, subir
  `curvatura_para_frenar`.
- Cuando una señal está cerca, la barra negra puede alterar la franja lejana
  y disparar un frenado de más. Si falla por ese lado, frena, no se acelera.

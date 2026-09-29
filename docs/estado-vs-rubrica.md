# Dónde vamos contra la rúbrica (2026-09-29)

Estado honesto criterio por criterio. Lo que dice "sin probar" es lo que se decide mañana en el laboratorio.

| Criterio | Cómo vamos | Qué falta |
|---|---|---|
| Corrección de trayectoria | Algoritmo listo y medido: 91.1% de línea detectada en 2341 frames, 0 saltos, zigzag 0 en ruta ideal | **Sin probar en el robot.** Es lo de mañana |
| Intervenciones humanas | Existe el estado `BUSCANDO`: al perder la línea gira hacia el último lado visto, 5/5 aciertos en los clips del profesor | Medirlo en la pista real |
| Reconocimiento de PARE | Detecta la señal roja en los 4 clips de ruta ideal, 0 falsos positivos en los otros 5 | Ajustar a qué área (o sea, a qué distancia) frena |
| Reconocimiento de SIGA | Igual con la verde, y ya no da volantazo al pasarla: mientras la señal tapa la franja se mantiene el rumbo (ver `docs/algoritmo.md`, etapa 12) | Lo mismo |
| Uso de técnicas | Cada módulo cita en su docstring de qué clase sale la técnica; la tabla completa está en `docs/reto/tecnicas-permitidas.md` | Que los tres puedan explicarla sin leer |
| Cumplimiento de restricciones | Solo color, máscaras, morfología, contornos y K-Means. Ni deep learning, ni preentrenados, ni Haar. Arduino intacto | Poder responder por qué scikit-learn sí (es el K-Means de la clase 4) |
| Tiempo de recorrido | El actuador manda pulsos a 10 Hz y reparte el giro | **Sin probar.** Depende del ritmo y de la ganancia |
| Diferenciación de la estrategia | Lo más fuerte que tenemos: calibración automática con K-Means, decisiones tomadas con evaluación cuantitativa, validación de señales en tres pasos (color, forma, persistencia) y control anticipativo con dos franjas | Contarlo bien en 30 segundos |
| Comunicación verbal | `docs/guion-sustentacion.md` y `docs/preguntas-del-profe.md` | Que Santiago y Daniel los lean |
| Póster | No empezado (no es para mañana) | Sale de la bitácora y de `docs/media/` |
| Análisis de resultados | Bitácora con mediciones reales, tablas de barrido y el caso del "falso mejor" (una configuración que sube el porcentaje y empeora) | Agregar lo que salga de la pista |
| Participación del equipo | Cada uno programó su parte | **Riesgo real:** que cada uno explique una parte que no programó |

## Lo que más puede costarnos nota

1. **Nada de esto se ha probado con el robot.** Todo está medido sobre video. Mañana es la primera vez que la decisión mueve algo.
2. **Tres montajes distintos de cámara, tres calibraciones.** Los videos del profesor tienen el carro ocupando el 40% inferior; el montaje de prueba de Santiago apunta directo al papel; el de mañana irá sobre el robot. La ROI cambia en cada uno. Por eso ahora hay perfiles (`config_celular.json`) y overrides por línea de comandos (`--roi-linea`, `--rotar`).
3. **La participación del equipo.** El profesor pregunta a cualquiera.

## Antes de salir de la casa

```bash
git pull --rebase && uv sync
uv run python tools/probar_control.py
uv run python -m unittest discover -s tests
uv run python tools/evaluar.py
uv run python tools/probar_robot.py --simulado     # teclea: wwad, luego r, luego q
```

Llevar: el celular con IP Camera Lite, el cable, la pista de papel que ya hizo Santiago, y el video `docs/media/demo_sustentacion.mp4` descargado por si no hay internet.

## Qué computador le habla al robot

**El de Daniel (Windows).** El `socket` de Python en Windows sí trae Bluetooth RFCOMM, así que funciona exactamente como el ejemplo del profesor, con la MAC:

```bash
uv run python tools/probar_robot.py --mac <MAC_DEL_ROBOT>
uv run main.py --fuente <url_celular> --robot-mac <MAC_DEL_ROBOT> --grande
```

Antes, emparejar el mBot en la configuración de Bluetooth de Windows.

**En el Mac de Juan David** el ejemplo del profesor no corre (macOS no trae `AF_BLUETOOTH`): hay que emparejar el robot y usar el puerto serie con `--robot-puerto /dev/tty.<nombre>`. Queda como plan B.

## Calibrar el montaje nuevo (5 minutos)

1. Con el celular **ya montado en el robot**: `uv run main.py --fuente <url> --mascaras --grande`. Mirar dónde queda la pista en la imagen y dónde empieza el robot.
2. Si la imagen sale de lado: `--rotar 90` (o 270).
3. Poner la franja de la línea **justo encima de lo que se ve del robot**: `--roi-linea 0.40 0.58` es para el encuadre de los videos del profesor; `--roi-linea 0.78 1.00` es para un celular que no ve el robot. Mover los dos números hasta que la franja amarilla del HUD caiga sobre la pista cercana.
4. Si la máscara de la línea sale con huecos o con sombras: foto de la pista → `uv run python tools/calibrar_kmeans.py <foto> -o config_pista.json` → correr con `--config config_pista.json` y volver a mirar las máscaras.
5. Anotar en la bitácora los valores que quedaron.

## Orden de las pruebas con el robot (el turno es corto)

1. **Conexión sin visión:** `tools/probar_robot.py` con la MAC o el puerto. Si el robot responde a `w a s d x`, la conexión está bien y lo que falle después es del algoritmo. Con `t` se mide la latencia y con `r` se ve si avanza parejo a 10 Hz.
2. **Robot levantado del piso**, corriendo el pipeline completo: mirar que las ruedas giren hacia donde dice el HUD. Nadie pone el robot en el piso antes de esto.
3. **Calibrar el montaje:** una foto de la pista con el celular ya montado → `tools/calibrar_kmeans.py` → `--roi-linea` ajustada → verificar con `--mascaras`.
4. **En la pista, tramo recto.** Si va a tirones: bajar `--robot-ritmo` a 8 o 5 antes de tocar cualquier otra cosa.
5. **Curvas.** Si se queda corto: `--robot-avanzar-al-girar` o subir `ganancia_giro`.
6. **Señales**, con los octágonos de verdad: revisar el área a la que frena.

Después de cada prueba, una línea en `docs/bitacora.md`. Eso es el análisis de resultados y el póster.

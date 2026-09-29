# Flujo de pruebas: de los clips a la pista

Cada nivel valida algo distinto. Una ejecución correcta sobre archivos es suficiente para demostrar el algoritmo, pero no certifica el comportamiento del robot en movimiento.

| Nivel | Material | Qué valida | Límite |
|---|---|---|---|
| 0. Pruebas del programa | Datos sintéticos y capturas simuladas | Contratos, estados, errores, cierre y compatibilidad | No mide percepción en el salón |
| 1. Frames | `datos/frames/` | Color, ROI, morfología y geometría | No valida tiempo ni movimiento |
| 2. Clips | `datos/clips/` | Percepción y decisiones sobre secuencias reales | El video no cambia por nuestras decisiones |
| 3. Simulación conectada | Pendiente | Control que modifica la siguiente observación | La página JavaScript actual no está conectada |
| 4. Pista real | Cámara y robot del profesor | Percepción, control, iluminación y latencia juntos | Requiere integración autorizada pendiente |

## Verificación reproducible del programa

Desde la raíz del repositorio:

```bash
uv sync --locked
uv run python tools/probar_control.py
uv run python -m unittest discover -s tests -v
uv run python tools/evaluar.py --salida datos/grabaciones/evaluacion_actual.csv
uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --sin-ventana --grabar
```

El último comando procesa el archivo una sola vez y debe terminar sin reconectar ni repetirlo. Deja un video y un CSV en `datos/grabaciones/`. Los errores al abrir la fuente o una configuración deben producir un mensaje comprensible y salida fallida; no una ejecución aparentemente exitosa sin frames.

Al modificar el algoritmo, evaluar **antes y después**, con los mismos clips y configuración:

```bash
uv run python tools/evaluar.py --salida datos/grabaciones/evaluacion_antes.csv
# Aplicar el cambio que se quiere medir
uv run python tools/evaluar.py --salida datos/grabaciones/evaluacion_despues.csv
```

Comparar frames, porcentaje de línea, saltos, señales y dirección de búsqueda por clip. Los FPS de proceso dependen del equipo y la carga: sirven como referencia de rendimiento, no como resultado determinista ni como FPS del celular. Si cambia el algoritmo, revisar máscaras de los casos afectados antes de aceptar una mejora numérica.

## Calibración con frames y clips

Los videos de ensayo ya están preparados. Para material nuevo:

1. Guardar originales en `datos/originales/` y ejecutar `uv run python tools/preparar_videos.py`.
2. Abrir `uv run python tools/calibrar.py datos/clips/rutaIdeal/video1.mp4` y ajustar ROI/HSV observando las máscaras.
3. Como propuesta inicial, ejecutar `uv run python tools/calibrar_kmeans.py datos/frames -o config_local.json`.
4. Evaluar con `uv run python tools/evaluar.py --config config_local.json` y comparar contra la configuración base.
5. Ver el resultado con `uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --config config_local.json --mascaras`.

K-Means no decide qué configuración es mejor. El umbral V=129 propuesto en un ensayo aumentó la cantidad de detecciones, pero también los saltos y la búsqueda equivocada: se mantuvo V=110. Ver [bitácora](bitacora.md).

## Qué significan las métricas

- **`linea_%`:** fracción de frames donde el detector devolvió un contorno válido. Sin anotaciones manuales no es exactitud ni precisión de segmentación.
- **Saltos:** cambios grandes de desviación entre detecciones consecutivas. Son una alerta para revisar el frame: también podrían aparecer con cámara movida, baja frecuencia o geometría difícil.
- **`pare` y `siga`:** cantidad de frames con cada detección, no número de señales distintas ni número de paradas.
- **Búsqueda correcta:** en clips cuyo nombre indica izquierda/derecha, se comprueba que predomine `BUSCAR` hacia ese lado. No prueba que el robot haya vuelto a la pista.
- **Cero detecciones en clips sin señales:** evidencia limitada a esos clips; no garantiza cero falsos positivos en cualquier ambiente.
- **`fps_proceso`:** velocidad de ejecución del pipeline sobre un archivo. No incluye la latencia del celular ni mide la reacción física del robot.

Los nueve clips contienen 2341 frames. La referencia previa a la estabilización está en `datos/grabaciones/evaluacion_antes_estabilizacion.csv`: 91.1% de detección de línea, 4 saltos y búsqueda del lado esperado en los cinco clips de descarrilamiento. Los CSV locales están ignorados por Git; para compartir resultados duraderos, registrar una tabla en la bitácora.

## Tiempo y registro de decisiones

El control recibe `ahora`. En archivos se usa el tiempo del video (`frame / FPS`); en cámaras se usa el reloj monotónico. El CSV registra el mismo tiempo de la secuencia. Esto permite reproducir un PARE sin depender de la velocidad de la computadora. El video procesado es de frecuencia constante; para investigar tiempos y eventos, el CSV es la referencia.

Al perder un stream o cerrar el programa se emite `PARAR` hacia los actuadores configurados. Actualmente estos son consola/CSV. Al integrar otro actuador se debe comprobar que traduzca esa orden, incluyendo el caso de pérdida de comunicación; esta prueba todavía no se ha realizado con el robot.

## Simulación y práctica pendiente

Se puede abrir `simulacion/index.html` en el navegador para ver la demo de Daniel. Tiene control propio en JavaScript y no consume las decisiones de `reto/control.py`; sus resultados no validan este algoritmo. La integración propuesta está en [0003](decisiones/0003-simulador-y-actuador.md): un actuador recibe `Decision`, mueve el simulador y este devuelve el siguiente frame y su reloj.

Para la clase en CI2DT2:

- Mostrar [diagramas](arquitectura.md), clip con máscaras, pruebas y tabla de resultados.
- Confirmar duración exacta de PARE, si SIGA puede acortarla y geometría real de las señales.
- Fijar el montaje de cámara y medir FPS/latencia y cambios de iluminación.
- Recalibrar ROI y colores con ese montaje; capturar clips propios y evaluarlos.
- Integrar más adelante la API Python indicada por el profesor, sin modificar Arduino ni configuraciones electrónicas.
- Registrar cada ensayo real en la bitácora: intervenciones, descarrilamientos, respuesta a señales y tiempo de recorrido.

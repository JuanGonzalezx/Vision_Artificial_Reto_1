# Reto 1 — Cerebro de un robot seguidor de línea

Visión Artificial en Tiempo Real · Universidad de Caldas · 2026-2

El programa recibe imágenes de una webcam, un celular por IP o un archivo, detecta la línea y las señales PARE/SIGA, y produce una decisión de movimiento. Usa las técnicas del curso: HSV, máscaras, morfología y contornos; K-Means propone calibraciones fuera del procesamiento en tiempo real.

**Estado al 28 de septiembre:** percepción, control, captura, HUD y grabación integrados. La salida disponible es consola/CSV. La conexión al robot y la validación física quedan pendientes; no se modifica Arduino ni la electrónica.

- [Arquitectura y diagramas del sistema, algoritmo y estados](docs/arquitectura.md)
- [Cómo probar y comparar resultados](docs/flujo-de-pruebas.md)
- [Especificación](docs/reto/especificacion.md), [rúbrica](docs/reto/rubrica.md) y [técnicas permitidas](docs/reto/tecnicas-permitidas.md)
- [Preguntas para la sustentación](docs/preguntas-del-profe.md) y [guion de la demostración](docs/guion-sustentacion.md)
- [Bitácora y mediciones](docs/bitacora.md)

## Instalación y verificación

El equipo usa **Python 3.14** y las versiones fijadas en `uv.lock` (incluido OpenCV 5). El archivo de bloqueo conserva el mismo entorno entre equipos.

```bash
git clone git@github.com:JuanGonzalezx/Vision_Artificial_Reto_1.git
cd Vision_Artificial_Reto_1
uv sync --locked
uv run python tools/probar_control.py
uv run python -m unittest discover -s tests -v
uv run python tools/evaluar.py
```

Los clips livianos están en `datos/clips/`. La evaluación anterior a la estabilización dio **91.1% de frames con detección de línea, 2341 frames, 4 saltos sospechosos y búsqueda hacia el lado esperado en 5/5 clips de descarrilamiento**. Son mediciones sobre video grabado: no prueban que el robot haya recuperado físicamente la trayectoria ni equivalen a precisión contra anotaciones manuales.

## Uso

```bash
# Demostración con un clip incluido, máscaras y decisiones en consola
uv run main.py --fuente datos/clips/rutaIdeal/video4.mp4 --mascaras --consola

# Procesar un clip completo sin ventanas; termina al llegar al final
uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --sin-ventana --grabar

# Webcam
uv run main.py --fuente 0 --mascaras

# Cámara IP: usar la URL exacta que indique la aplicación del teléfono
uv run main.py --fuente http://192.168.1.50:8081/ --mascaras

# Si la cámara pide autenticación, también existen -u y -p
uv run main.py --fuente http://192.168.1.50:8081/ --usuario usuario --contrasena clave

# Calibración guardada
uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --config config_local.json
```

También se admiten `CAMARA_URL`, `CAMARA_USUARIO` y `CAMARA_CONTRASENA`; los argumentos del comando tienen prioridad. `--grabar` deja un video procesado y un CSV de decisiones en `datos/grabaciones/`. El control y el CSV usan el tiempo del clip al leer archivos y el tiempo transcurrido al usar una cámara. La cámara intenta reconectar si se pierde la transmisión; un archivo termina sin volver a abrirse.

Se sale con `q` o `Ctrl+C`. En macOS, si se solicita permiso de cámara, hay que concederlo a la aplicación que ejecuta Python y volver a intentar. La demo con archivos funciona sin acceso a la cámara.

## Calibración y límites actuales

Las ROI y los colores están calibrados con los videos del profesor: **el carro ocupa la parte inferior**; la franja cercana de la línea está entre el 40% y el 58% del alto. Un montaje distinto requiere recalibrar.

```bash
uv run python tools/calibrar.py datos/clips/rutaIdeal/video1.mp4
uv run python tools/calibrar_kmeans.py datos/frames -o config_local.json
uv run python tools/evaluar.py --config config_local.json
uv run python tools/barrido.py vmax 100 110 120
```

K-Means propone rangos; la comparación con clips y máscaras decide si se conservan. La franja lejana se muestra como indicador de curvatura y tiene peso cero en el control por defecto. Las señales de los clips no pasan el filtro estricto de octágono, por eso `exigir_octagono` está desactivado. Duración de PARE, comportamiento de SIGA, iluminación, latencia y montaje deben confirmarse en la práctica.

El archivo [simulacion/index.html](simulacion/index.html) se puede abrir en un navegador. Es una simulación autónoma en JavaScript: todavía no recibe las decisiones de Python ni valida este pipeline en lazo cerrado.

## Equipo y estructura

| Integrante | Frente |
|---|---|
| Santiago Bedoya Arcila | Captura y entrada: `reto/camara.py`, `main.py` |
| Daniel Felipe Franco Rincón | Pipeline, señales y simulación |
| Juan David Ocampo González | Línea, control, orquestación y documentación |

```text
main.py                  CLI, lectura de frames, reloj y cierre de recursos
reto/tipos.py            Contratos compartidos; no cambiar sin avisar al equipo
reto/config.py           Parámetros y calibración JSON
reto/camara.py           Apertura de webcam, URL o archivo y autenticación
reto/pipeline.py         Orden del procesamiento por frame
reto/linea.py            Máscara, contorno, centroide y desviación
reto/senales.py          Color y propiedades de los contornos de señales
reto/control.py          Máquina de estados, sin OpenCV
reto/actuador.py         Consola/CSV e interfaz para futuros adaptadores
reto/overlay.py          HUD y máscaras
tests/                   Pruebas de integración y casos de error
tools/                   Evaluación, calibración y preparación de datos
simulacion/index.html    Demo independiente de Daniel
docs/                    Arquitectura, bitácora, decisiones, clases y reto
notebooks/               Material docente de referencia, limpio
datos/clips/             Videos livianos de ensayo incluidos
datos/frames/            Imágenes para calibración incluidas
datos/originales/        Videos originales, ignorados por Git
datos/grabaciones/       Salidas de ejecución y evaluación, ignoradas por Git
```

Los notebooks conservan ejemplos del profesor: algunos usan Colab o imágenes de internet y no son comandos del programa. Los apuntes de `docs/clases/` también mencionan demos externas de la carpeta de la materia. Para nuevos ensayos: guardar originales en `datos/originales/`, ejecutar `uv run python tools/preparar_videos.py`, evaluar y registrar los resultados en la bitácora.

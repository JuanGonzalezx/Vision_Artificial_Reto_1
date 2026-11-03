# Reto 1 — Cerebro de un robot seguidor de línea

Visión Artificial en Tiempo Real · Universidad de Caldas · 2026-2

> **Reto 1 finalizado y archivado.** Esta carpeta es el estado exacto del commit `2e93b71`, sin herramientas de desarrollo: se conserva solo lo necesario para **ejecutarlo**. El código (`main.py`, `reto/`, `simulacion/`, `configs/`, `uv.lock`) es idéntico al de ese commit. Las herramientas de calibración/evaluación, las pruebas y los notebooks se retiraron (siguen en el historial: `git show 2e93b71:tools/...`).

El programa recibe imágenes (archivo de video, webcam, celular por IP o el simulador), detecta la línea guía y las señales PARE/SIGA con técnicas del curso (HSV, máscaras, morfología, contornos) y produce una decisión de movimiento: `adelante`, `izquierda`, `derecha` o `parar`. Esa decisión sale por consola, CSV, el simulador o el robot mBot.

## Instalación

Requiere **Python 3.14** y [`uv`](https://docs.astral.sh/uv/). Desde la raíz del repo:

```bash
cd reto_1
uv sync --locked
```

Las versiones quedan fijadas en `uv.lock` (OpenCV 5, NumPy, scikit-learn, matplotlib, pyserial).

## Las 4 formas de correrlo

Todos los comandos se ejecutan dentro de `reto_1/`. Se sale con `q`, `Esc` o `Ctrl+C`.

### 1. Video (sin hardware)

Procesa un clip incluido en `datos/clips/`. Es la forma más simple de comprobar que todo funciona.

```bash
# Con ventana, máscaras y decisiones en consola
uv run main.py --fuente datos/clips/rutaIdeal/video4.mp4 --mascaras --consola

# Sin ventana, hasta el final del clip; deja video procesado + CSV en datos/grabaciones/
uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --sin-ventana --grabar

# En bucle y a velocidad real (para mirar con calma)
uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --bucle --mascaras
```

Clips: `rutaIdeal/video1..4.mp4` (recorrido normal) y `desacarrilamiento/noReconoce*.mp4` (pérdida de la línea).

### 2. Cámara en vivo (webcam o celular por IP)

```bash
# Webcam
uv run main.py --fuente 0 --mascaras

# Celular por IP: la URL exacta que muestre la app del teléfono
uv run main.py --fuente http://192.168.1.50:8081/ --mascaras

# Si pide autenticación
uv run main.py --fuente http://192.168.1.50:8081/ --usuario usuario --contrasena clave

# Celular en el soporte: girar la imagen y ajustar la franja donde se busca la línea
uv run main.py --fuente http://192.168.1.50:8081/ --rotar 90 --roi-linea 0.78 1.00 --grande
```

También se leen `CAMARA_URL`, `CAMARA_USUARIO` y `CAMARA_CONTRASENA`; los argumentos tienen prioridad. Para el montaje con celular sin el robot en cuadro hay un perfil listo: `--config config_celular.json`. Si se pierde la transmisión, intenta reconectar. En macOS hay que dar permiso de cámara a la aplicación que ejecuta Python.

### 3. Simulador (lazo cerrado en el navegador)

El simulador hace de cámara **y** de robot: el navegador manda su pantalla al pipeline y recibe la decisión.

```bash
uv run main.py --index
```

Abre `http://localhost:8765/index.html?puente=1` solo. Usa la calibración `configs/simulador.json`. Valida estados y ganancias, no la percepción real (los frames dibujados son más limpios que los reales). Sin el puente, `simulacion/index.html` también se puede abrir directo en el navegador como demo autónoma.

### 4. Robot mBot (real o simulado)

El robot recibe los comandos `w`, `a`, `d`, `x` como pulsos (detalle en [docs/robot.md](docs/robot.md)). Se combina con cualquier fuente de imagen de las formas 1 o 2.

```bash
# Sin robot: imprime los comandos en lugar de enviarlos (para probar)
uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --robot-simulado

# Robot real, Linux/Windows, por Bluetooth (MAC del mBot)
uv run main.py --fuente http://192.168.1.50:8081/ --robot-mac 00:1B:10:21:2C:1B

# Robot real por puerto serie (macOS: /dev/tty.<nombre>; Windows: COMn)
uv run main.py --fuente http://192.168.1.50:8081/ --robot-puerto /dev/tty.Makeblock-ELETSPP
```

Antes de usar el robot real: emparejarlo por Bluetooth con el equipo. También se leen `ROBOT_MAC` y `ROBOT_PUERTO`. Ajustes: `--robot-ritmo` (comandos por segundo, 10 por defecto, porque el firmware se bloquea 100 ms por cada `w`) y `--robot-avanzar-al-girar` (curvas más abiertas). No se modifica el Arduino. Probar siempre primero con `--robot-simulado`.

## Opciones útiles

| Opción | Para qué |
|---|---|
| `--mascaras` | Ver las máscaras de línea y señales |
| `--consola` | Imprimir cada decisión |
| `--grabar` | Guardar video procesado y CSV en `datos/grabaciones/` |
| `--sin-ventana` | Procesar sin abrir ventanas |
| `--config <json>` | Cargar una calibración; los campos omitidos usan los valores por defecto |
| `--rotar 0/90/180/270` | Girar el frame |
| `--roi-linea D H` / `--roi-senal D H` | Franja (fracción del alto) donde buscar línea / señal |
| `--grande` | Acción en letra grande para mostrar desde lejos |
| `--bucle` | Repetir el video (solo archivos) |

## Calibración

Los rangos HSV y las ROI vienen calibrados con los videos del profesor: el carro ocupa la parte inferior de la imagen. Un montaje distinto necesita recalibrar. Perfiles incluidos:

| Archivo | Uso |
|---|---|
| `configs/video1.json` | Videos del profesor |
| `configs/video1-kmeans.json` | Rangos propuestos con K-Means |
| `configs/simulador.json` | Cámara del simulador (`--index`) |
| `config_celular.json` | Celular en el soporte, sin el robot en cuadro |

La calibración interactiva (`tools/calibrar*.py`) y la evaluación sobre clips (`tools/evaluar*.py`) se retiraron de esta carpeta; están en el commit `2e93b71`.

## Estructura

```text
main.py                  CLI, lectura de frames, reloj y cierre de recursos
reto/
  tipos.py               Contratos compartidos entre módulos
  config.py              Parámetros y calibración JSON
  camara.py              Webcam, URL o archivo; reconexión; autenticación
  pipeline.py            Orden del procesamiento por frame
  linea.py               Máscara, contorno, centroide y desviación de la línea
  senales.py             PARE/SIGA por color y forma
  control.py             Máquina de estados (sin OpenCV)
  overlay.py             HUD y máscaras
  actuador.py            Salida a consola y CSV
  actuador_robot.py      Salida al robot (real o simulado), con ritmo limitado
  Robot.py               Driver Bluetooth (Linux/Windows)
  Robot_mac.py           Driver por puerto serie (macOS)
  simulador.py           Puente HTTP con el simulador (--index)
simulacion/index.html    Simulador de la pista
configs/, config_celular.json   Calibraciones
datos/clips/             Videos livianos de ensayo
datos/grabaciones/       Salidas de --grabar (se crea sola; ignorada por Git)
docs/                    Documentación del reto (abajo)
```

## Documentación

- [El algoritmo etapa por etapa, y por qué así](docs/algoritmo.md)
- [Arquitectura y diagramas](docs/arquitectura.md)
- [Cómo hablarle al robot](docs/robot.md)
- [Cómo probar y comparar resultados](docs/flujo-de-pruebas.md) (usa `tools/` y `tests/`, ya retirados)
- [Especificación](docs/reto/especificacion.md), [rúbrica](docs/reto/rubrica.md) y [técnicas permitidas](docs/reto/tecnicas-permitidas.md)
- [Preguntas para la sustentación](docs/preguntas-del-profe.md) y [guion de la demostración](docs/guion-sustentacion.md)
- [Bitácora y mediciones](docs/bitacora.md) y [dónde quedó contra la rúbrica](docs/estado-vs-rubrica.md)

## Equipo

| Integrante | Frente |
|---|---|
| Santiago Bedoya Arcila | Captura y entrada: `reto/camara.py`, `main.py` |
| Daniel Felipe Franco Rincón | Pipeline, línea, calibración K-Means y simulación |
| Juan David Ocampo González | Línea, control, orquestación y documentación |

# Estado del Reto 2 — dónde vamos y qué falta

Actualizado: 2026-11-03 · Rama: `reto2` (remoto) / `reorganizar` (local). Enunciado: `docs/reto/Reto-2.md`.

## Hecho

- **Repo reorganizado**: `reto_1/` congelado; `reto_2/` activo con entorno `uv` propio; `docs/` y `compartido/` en la raíz.
- **Dataset real** en `reto_2/cnn/dataset/0..3` (538 fotos de la pista: 0 PARE, 1 SIGA, 2 ZONA_ESCOLAR, 3 VELOCIDAD_60).
- **Entrenamiento de las 5 arquitecturas** (`uv run python tools/entrenar_senales.py`, partición 70/20/10, `seed=42`). Resultados versionados en `reto_2/modelos/entrenamiento/senales_reto2/`: `resultados.csv`, `particiones.csv`, y por modelo matriz de confusión, curva de pérdida y reporte.

  | Modelo | Épocas | Mejor época | val_loss | Test (54 img) |
  |---|---|---|---|---|
  | ResNet50 | 50 (tope) | 50 | 0.00116 | 100 % |
  | MobileNet | 50 (tope) | 50 | 0.00241 | 100 % |
  | DenseNet121 | 50 (tope) | 50 | 0.01355 | 100 % |
  | VGG16 | 36 (early stopping) | 31 | 0.01844 | 100 % |
  | VGG19 | 41 (early stopping) | 36 | 0.02263 | 100 % |

- **Top-2 por `val_loss`**: ResNet50 y MobileNet. Candidato a modelo integrado: **MobileNet** (~3 M de parámetros frente a ~24 M de ResNet50), pero esto aún **no está medido** (ver pendientes).
- **Simulación** (`reto_2/simulacion/index.html`): las 4 señales aparecen en la pista con fotos reales del dataset (`simulacion/senales/`, 5 por clase, sorteadas cada vuelta). Orden en la vuelta: SIGA, ZONA_ESCOLAR, VELOCIDAD_60, PARE.
- Pipeline con CNN enchufada: `reto/clasificador.py` (carga `modelos/senales.keras`, o cae al detector por color de Reto 1 si falta) y `reto/senales.py` (máscara de color propone, CNN clasifica).

## Falta (en este orden)

1. **Medir tiempos de inferencia y justificar el modelo integrado.** `reto_2/tools/evaluar_modelos.py` está escrito (elige top-2 por `val_loss`, calcula métricas por clase y macro en test, mide tiempo por imagen) pero **no se ha podido terminar de ejecutar**: la primera corrida pasó de 20 min sin terminar. Hay que diagnosticar dónde se atasca (carga de modelos, inferencia en CPU, o el cálculo en sí) y correrlo con `--repeticiones 20` y la salida a un archivo. Debe producir `comparativa_top2.md` y `tiempos_inferencia.csv` en la carpeta del experimento. Es el entregable 4 y la justificación pedida en el enunciado.
2. **Copiar el modelo elegido a `reto_2/modelos/senales.keras`.** Los `.keras` están ignorados por Git (`modelos/**/*.keras`): quien clone el repo **debe reentrenar** (`uv run python tools/entrenar_senales.py`, tarda bastante en CPU) o recibir los archivos aparte. Sin `senales.keras` el pipeline usa el detector por color.
3. **Comportamientos de velocidad** (paso 7 del profesor). Hoy `reto/control.py` no tiene velocidades y `reto/actuador_robot.py` envía comandos a ritmo fijo (`ritmo_hz` = 10). Falta: estados normal/reducida, PARE prioritario (ZONA_ESCOLAR y VELOCIDAD_60 no reanudan un robot detenido), SIGA reanuda, y cadencia de "adelante" cercana a 2 s en lento y 0,5 s en rápido (afinar en pista). Ampliar `tests/` con esos casos.
4. **Simulación**: los chips de la interfaz solo muestran PARE y SIGA, y el simulador no reacciona a ZONA_ESCOLAR ni a VELOCIDAD_60 hasta que el control en Python los maneje. Además, el cuadrado de la foto trae su propio fondo y cinta; no se verificó visualmente (la extensión de Chrome no conectó). Revisar con `uv run main.py --index`.
5. **Demo en pista** con el robot, incluida la aparición repentina, y registro en `docs/bitacora.md`.
6. **Entregables escritos**: interpretación breve de las confusiones y justificación del modelo integrado (clasificación y tiempo de respuesta).

## Advertencias sobre los resultados

- **100 % en los 5 modelos no distingue nada.** Casi seguro hay fotos casi idénticas (ráfagas) repartidas entre train y test, que inflan el test. Si se quiere un resultado creíble, agrupar las ráfagas antes de partir y reentrenar. El enunciado pide evitar casi-duplicados entre particiones.
- ResNet50, MobileNet y DenseNet121 llegaron al tope de 50 épocas **sin converger** (seguían mejorando). Considerar 100 épocas.
- Las 20 fotos de `simulacion/senales/` salen del dataset de entrenamiento: clasificarlas en la simulación no prueba generalización.
- El dataset son recortes cercanos de la señal; en vivo el pipeline clasifica recortes de la máscara de color. Si el desempeño en vivo cae, usar `tools/preparar_senales.py` para que entrenamiento e inferencia recorten igual.

## Cómo seguir

```bash
cd reto_2
uv sync --locked                                   # TensorFlow pesa ~700 MB
uv run python -m unittest discover -s tests        # 67 tests OK al cierre de esta sesión
uv run python tools/entrenar_senales.py            # reentrena (los .keras no están en Git)
uv run main.py --index                             # simulador + pipeline
```

Pendientes menores: `docs/arquitectura.md`, `docs/plan-reto.md` y `docs/flujo-de-pruebas.md` aún mencionan `datos/senales` y cosas viejas; afinar `AGENTS.md` al terminar el desarrollo; `temp/`, `scripts/`, `vid/`, `salida/` y `figuras/` en la raíz son locales y sin uso (ignorados por Git).

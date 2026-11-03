# Modelos de señales (Reto 2)

Aquí va el modelo CNN que usa el pipeline (`reto/clasificador.py`). El `.keras`
pesa y **no se sube al repo** (`.gitignore`); se regenera entrenando.

## Cómo generarlo

1. El dataset está en `cnn/dataset/`, una carpeta por clase:
   `0` = PARE, `1` = SIGA, `2` = ZONA_ESCOLAR, `3` = VELOCIDAD_60.
2. Entrenar con `cnn/cnn_trainer.py`, directo (`cnn/main.py`) o con
   `uv run python tools/entrenar_senales.py --modelos MobileNet`; los resultados
   (matriz de confusión, curva de pérdida y reporte) quedan en `modelos/entrenamiento/`.
3. Copiar el `.keras` elegido aquí como `modelos/senales.keras`.

## Cómo lo usa el pipeline

- `config.ruta_modelo_senales` = `modelos/senales.keras`.
- `config.clase_modelo_senales` y `config.tamano_entrada_senales` **deben coincidir**
  con lo usado al entrenar: el nombre elige el `preprocess_input`.
- `config.clases_senales` sigue el orden de las carpetas del dataset (`0..3`).

Mientras no exista el archivo, el pipeline avisa una vez y usa el detector por
color del Reto 1. Ver `docs/decisiones/0010-clasificador-cnn.md`.

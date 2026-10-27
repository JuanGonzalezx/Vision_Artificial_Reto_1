# Modelos de señales (Reto 2)

Aquí va el modelo CNN entrenado que usa el pipeline (`reto/clasificador.py`).
El archivo `.keras` pesa y **no se sube al repo** (está en `.gitignore`); se
regenera con el material de clase.

## Cómo generarlo

1. Poner los recortes en `datos/senales/<CLASE>/` (una carpeta por clase:
   `PARE`, `SIGA`, `VELOCIDAD_60`, `ZONA_ESCOLAR`).
2. Entrenar con el pipeline de `5_cnns/` apuntando `dataset_dir` a
   `../datos/senales` (no se modifica el código del profesor).
3. Copiar el `.keras` elegido aquí como `senales.keras`.

## Modelos ya entrenados

Resultados en `modelos/entrenamiento/senales_reto2/` (matriz de confusión, curva
de pérdida y reporte por arquitectura). Los dos mejores por `val_loss` son
ResNet50 y MobileNet; el pipeline integra **MobileNet** (el más liviano):

```bash
cp modelos/entrenamiento/senales_reto2/MobileNet/MobileNet.keras modelos/senales.keras
```

## Cómo lo usa el pipeline

- `config.ruta_modelo_senales` = `modelos/senales.keras` (por defecto).
- `config.clase_modelo_senales` y `config.tamano_entrada_senales` **deben
  coincidir** con lo usado al entrenar: el nombre elige el `preprocess_input`.
- `config.clases_senales` es el `sorted()` de las carpetas del dataset (el orden
  de salida de la CNN).

Mientras no exista el archivo, el pipeline avisa una vez y usa el detector por
color del Reto 1. Ver `docs/decisiones/0010-clasificador-cnn.md`.

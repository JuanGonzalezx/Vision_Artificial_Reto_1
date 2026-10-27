# Dataset de señales (Reto 2)

Recortes de las cuatro señales, **una carpeta por clase**. Es el formato que
espera el pipeline de entrenamiento (`5_cnns/cnn_trainer.py`): la clase de cada
imagen es el nombre de su carpeta y el orden de salida de la CNN es el
`sorted()` de estos nombres.

```
datos/senales/
├── PARE/
├── SIGA/
├── VELOCIDAD_60/
└── ZONA_ESCOLAR/
```

Conviene mezclar muchas condiciones (distancia, ángulo, iluminación y fondo) y
evitar fotogramas casi idénticos entre entrenamiento, validación y prueba: el
reto lo pide expresamente. Si se agrega una clase "fondo", hay que añadirla a
`config.clases_senales` en el mismo orden.

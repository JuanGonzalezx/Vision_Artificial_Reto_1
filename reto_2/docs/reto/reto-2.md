# Reto de visión artificial

## Segunda parte del robot seguidor de línea con redes neuronales convolucionales

En la primera parte del reto, los equipos desarrollaron un sistema de visión artificial que permitía a un robot seguir una línea y reconocer las señales de PARE y SIGA mediante el análisis de su forma y color.

Ahora, el sistema deberá responder a un nuevo requerimiento: reconocer cuatro señales de tránsito —PARE, SIGA, ZONA ESCOLAR y VELOCIDAD DE 60 km/h— utilizando las arquitecturas de redes neuronales convolucionales —CNN— predeterminadas y trabajadas en clase.

El robot deberá mantener el seguimiento de la línea, analizar las imágenes capturadas por su cámara y ajustar su movimiento según la señal identificada. Las señales podrán presentarse de manera repentina durante el recorrido y no necesariamente estarán ubicadas en posiciones fijas de la pista. Por lo tanto, las decisiones deberán basarse en la información visual recibida y no en una secuencia de acciones programada previamente.

## Objetivo general

Desarrollar e integrar un sistema de reconocimiento de señales de tránsito mediante redes neuronales convolucionales que permita a un robot seguidor de línea detenerse, reanudar la marcha y modificar su velocidad de acuerdo con las señales identificadas.

## Objetivos específicos

- Preparar un conjunto de imágenes para el reconocimiento de las cuatro señales.
- Entrenar y comparar las arquitecturas CNN establecidas y trabajadas en clase.
- Seleccionar los dos mejores modelos a partir de su desempeño en validación.
- Evaluar ambos modelos mediante matrices de confusión, curvas de pérdida y métricas de clasificación.
- Integrar el modelo seleccionado al sistema de control del robot.
- Demostrar el cumplimiento de los comportamientos requeridos sin perder el seguimiento de la línea.

## Comportamientos requeridos

| **Señal identificada** | **Comportamiento del robot** |
| --- | --- |
| **PARE** | Detenerse completamente y permanecer detenido hasta identificar la señal de SIGA. |
| **SIGA** | Iniciar la marcha si está detenido. Si ya está en movimiento, continuar el recorrido. |
| **ZONA ESCOLAR** | Reducir considerablemente la velocidad, de forma que el cambio sea claramente observable, y continuar siguiendo la línea. |
| **VELOCIDAD DE 60 km/h** | Aumentar la velocidad si circula a velocidad reducida. Si ya se desplaza a la velocidad normal establecida para la pista, conservarla. |

La orden de PARE tendrá prioridad: las señales de ZONA ESCOLAR y VELOCIDAD DE 60 km/h no deberán reanudar la marcha de un robot detenido por PARE.

## Consideraciones técnicas

El reconocimiento de las cuatro señales deberá realizarse mediante las CNN establecidas en clase. Esta condición reemplaza, para esta segunda parte, la restricción del reto inicial que impedía utilizar aprendizaje profundo.

El seguimiento de la línea podrá conservar la estrategia desarrollada previamente, integrándola con las decisiones generadas por el modelo de reconocimiento de señales.

Los equipos deberán definir velocidades de marcha normal y reducida que permitan distinguir claramente ambos comportamientos y mantener la estabilidad del robot sobre la pista.

Para comparar los modelos, se deberán utilizar las mismas particiones de entrenamiento, validación y prueba. Las imágenes de prueba no podrán utilizarse durante el entrenamiento ni para seleccionar los dos mejores modelos. Si se extraen imágenes de videos, se deberá evitar distribuir fotogramas casi idénticos entre las distintas particiones.

## Entregables

Cada equipo deberá presentar:

1. **Demostración funcional del robot.**\
   Recorrido sobre la pista en el que se evidencie el seguimiento de la línea y la respuesta correcta ante las cuatro señales, incluyendo su aparición repentina.
2. **Matrices de confusión de los dos mejores modelos CNN.**\
   Una matriz por modelo, calculada sobre el conjunto de prueba, con las cuatro clases claramente identificadas.
3. **Curvas de pérdida de los dos mejores modelos.**\
   Gráficas de la pérdida de entrenamiento y validación a lo largo de las épocas, con sus ejes y leyendas correspondientes.
4. **Métricas de los dos mejores modelos.**\
   Tabla comparativa con exactitud global —accuracy—, precisión, sensibilidad —recall— y F1-score. Se deberán incluir resultados por clase y el promedio macro de precisión, recall y F1-score.

Los resultados deberán acompañarse de una breve interpretación que explique las confusiones más frecuentes y justifique la elección del modelo integrado al robot, considerando tanto su capacidad de clasificación como su tiempo de respuesta durante el recorrido.

## Originalidad de la solución

Se premiarán las soluciones que se diferencien de las propuestas de los demás equipos por su originalidad en el procesamiento de imágenes, el reconocimiento de señales o el control del robot. Estas propuestas deberán cumplir con los requisitos técnicos y los comportamientos establecidos en el reto.

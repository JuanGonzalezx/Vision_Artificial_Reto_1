# Reto 1 — El cerebro de un robot autónomo seguidor de línea

> Transcripción del documento oficial del profesor (`Reto-1.docx`, en esta misma carpeta).
> Si hay diferencias, manda el .docx.

## Planteamiento

Somos un equipo de ingenieros encargado de programar el "cerebro" de un robot móvil. El robot tiene una cámara y debe desplazarse de manera autónoma sobre una pista con una línea guía.

El algoritmo debe analizar **en tiempo real** las imágenes de la cámara y decidir el movimiento del robot: seguir la línea sin descarrilarse y responder a dos señales de tránsito:

- **Octágono rojo → PARE:** el robot se detiene durante el tiempo que indique el docente.
- **Octágono verde → SIGA:** el robot continúa el recorrido.

No basta con que el robot avance: hay que **justificar** cómo el algoritmo identifica la línea, determina la dirección, reconoce las señales y controla el comportamiento en cada situación.

## Objetivo general

Diseñar e implementar un algoritmo de visión artificial que permita a un robot móvil seguir una línea sobre una pista, corregir su trayectoria y reconocer señales representadas con octágonos rojos y verdes, **sin usar aprendizaje profundo**.

## Objetivos específicos

1. Capturar y analizar las imágenes de la cámara del robot.
2. Identificar la línea guía con técnicas de procesamiento y segmentación.
3. Calcular la posición de la línea respecto al centro del robot.
4. Generar acciones de control para corregir la trayectoria y evitar el descarrilamiento.
5. Detectar e identificar los octágonos rojo y verde en distintos puntos de la pista.
6. Detener el robot ante PARE y reanudar ante SIGA.
7. Comparar la estrategia con la de los demás equipos y explicar ventajas, limitaciones y mejoras.

## Restricciones técnicas

La lista completa, con dónde vimos cada técnica, está en [tecnicas-permitidas.md](tecnicas-permitidas.md).

**Permitido:** operaciones lógicas y aritméticas, espacios de color (RGB, HSV, CIELab), recorte de ROI, redimensionamiento y rotación, umbralización, segmentación por color, K-Means básico, operaciones morfológicas, suavizado, Canny, contornos y sus propiedades (área, perímetro, centroide, aproximación poligonal, relación de aspecto), identificación de formas simples.

**No permitido:** redes neuronales, deep learning, modelos preentrenados, YOLO / SSD / Faster R-CNN, cascadas Haar, servicios externos de IA, y cualquier librería que detecte la línea o las señales automáticamente sin que nosotros implementemos la lógica.

El código debe ser comprensible, estar organizado y permitir explicar cada etapa.

## Entregables

- Un **póster o material visual** con la metodología, las etapas del procesamiento y los resultados.
- Una **demostración práctica** del robot durante la competencia.

## Competencia

Recorrido completo sobre la pista, con los intentos que defina el docente. Se tiene en cuenta:

- tiempo total empleado,
- cumplimiento de PARE,
- cumplimiento de SIGA,
- número de descarrilamientos,
- necesidad de intervención manual,
- capacidad de recuperar la trayectoria.

## Ayudas

Videos de ensayo del profesor (Google Drive):
<https://drive.google.com/drive/folders/1m6mazLjCKPlwaVpH-arGSYZMF_P2KC77?usp=sharing>

Descárgalos en `datos/videos/` (esa carpeta está en .gitignore, no se suben al repo).

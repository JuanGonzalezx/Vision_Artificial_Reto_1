# Técnicas permitidas y dónde las vimos

Regla del reto: **solo se usa lo visto en el curso**. Esta tabla es la fuente para justificar cada paso del algoritmo, tanto en el código como en la sustentación.

> ⚠️ Ojo con una confusión que ya tuvimos: la especificación del profesor permite **más** que los 4 notebooks. Los notebooks cubren las clases 1, 2 y 4; Canny, morfología y contornos se vieron en la **clase 3** (slides `FundamentosVisionArtificial.pdf`) y están explícitamente permitidos en el .docx. La versión anterior de `AGENTS.md` restringía todo a los notebooks y eso dejaba por fuera la detección de octágonos.

## Permitido

| Técnica | Función típica | Dónde se vio | Apuntes |
|---|---|---|---|
| Imagen como matriz, canales BGR | `img[y, x]`, `cv2.split` | Clase 1 / notebook 1 | [clase1](../clases/clase1.md) |
| Espacios de color RGB, HSV, CIELab | `cv2.cvtColor` | Clase 1 / notebook 2 | [clase1](../clases/clase1.md) |
| Operaciones aritméticas (resta, absdiff) | `cv2.absdiff`, `cv2.subtract` | Clase 2 / notebook 3 | [clase2](../clases/clase2.md) |
| Operaciones lógicas y máscaras | `cv2.bitwise_and`, `mask=` | Clase 2 / notebook 3 | [clase2](../clases/clase2.md) |
| Umbralización | `cv2.threshold` | Clase 2 / notebook 3 | [clase2](../clases/clase2.md) |
| Segmentación por color | `cv2.inRange` | Clase 2 | [clase2](../clases/clase2.md) |
| Recorte de ROI | `img[y1:y2, x1:x2]` | Clase 1 | [clase1](../clases/clase1.md) |
| Redimensionar y rotar | `cv2.resize`, `cv2.rotate`, `warpAffine` | Clase 1 | [clase1](../clases/clase1.md) |
| Suavizado / reducción de ruido | `cv2.GaussianBlur` | Clase 3 | [clase3](../clases/clase3.md) |
| Detección de bordes | `cv2.Canny` | Clase 3 | [clase3](../clases/clase3.md) |
| Morfología (erosión, dilatación, apertura, cierre) | `cv2.erode`, `cv2.dilate`, `cv2.morphologyEx` | Clase 3 | [clase3](../clases/clase3.md) |
| Contornos y sus propiedades | `cv2.findContours`, `contourArea`, `arcLength`, `moments` | Clase 3 | [clase3](../clases/clase3.md) |
| Aproximación poligonal e identificación de formas | `cv2.approxPolyDP`, `cv2.boundingRect` | Clase 3 | [clase3](../clases/clase3.md) |
| K-Means básico | `sklearn.cluster.KMeans` | Clase 4 / notebook 4 | [clase4](../clases/clase4.md) |

Las propiedades de contorno que menciona el .docx —área, perímetro, **centroide**, aproximación poligonal y relación de aspecto— están todas permitidas. El centroide sale de los momentos: `M = cv2.moments(c)`, `cx = M["m10"] / M["m00"]`.

## No permitido

- Redes neuronales y deep learning.
- Modelos preentrenados de cualquier tipo.
- Detectores tipo YOLO, SSD, Faster R-CNN o equivalentes.
- Cascadas Haar.
- Servicios externos de inteligencia artificial.
- Librerías que hagan la detección de la línea o de las señales automáticamente sin que nosotros implementemos la lógica.

## Zona gris: consultarlo antes de usarlo

Estas funciones existen en OpenCV y son tentadoras, pero **no las hemos visto en clase**. Si alguna resulta necesaria, se le pregunta primero al profesor y se deja escrito aquí con su respuesta.

- `cv2.HoughLines` / `cv2.HoughCircles` (están en el programa del curso, pero en un módulo posterior).
- `cv2.matchShapes`, `cv2.matchTemplate`.
- `cv2.kmeans` de OpenCV (equivalente al de sklearn que sí vimos; si se usa, hay que decir que es la misma técnica de la clase 4).
- Rastreadores de OpenCV (`cv2.Tracker*`).
- `cv2.minAreaRect` (es una propiedad de contorno, muy cercana a lo permitido, pero no apareció en clase).

## Cómo se justifica en el código

Cada módulo de `reto/` dice en su docstring qué técnicas usa y de qué clase salen. Ejemplo:

```python
"""Detección de la línea guía.

Técnicas: conversión a HSV (clase 1), segmentación por color con inRange
(clase 2), apertura morfológica para limpiar la máscara (clase 3) y
centroide por momentos (clase 3).
"""
```

Eso es lo que se copia luego al póster y lo que hay que poder explicar de memoria.

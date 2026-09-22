# Apuntes de clase

Copias de los apuntes de la materia, para tener en el repo todo lo que se puede usar en el reto. Se actualizan con `uv run python tools/sync_apuntes.py`.

| Clase | Tema | Qué de aquí sirve para el reto |
|---|---|---|
| [1](clase1.md) | Composición de una imagen: matriz, BGR, HSV, CIELab, ROI, resize, rotar | HSV para segmentar por color pase lo que pase con la luz; ROI para mirar solo la franja de la pista |
| [2](clase2.md) | Máscaras: operaciones lógicas, umbral, `inRange`, `absdiff` | La máscara de la línea y las de los colores de las señales |
| [3](clase3.md) | Filtros: Gauss, Canny, morfología, contornos, `approxPolyDP`, `boundingRect` | Limpiar máscaras y detectar los octágonos contando vértices |
| [4](clase4.md) | K-Means: segmentación de color no supervisada | Calibrar los rangos de color de la pista real (nuestra estrategia propia) |

El código de ejemplo de cada clase está en la carpeta de la materia; los notebooks del profesor, en [../../notebooks/](../../notebooks/).

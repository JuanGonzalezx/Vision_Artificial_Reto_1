# Clase 1 — Composición de una imagen

> Apuntes para ponerme al día. Salen de los slides 2–6 de `los slides del profesor (fuera del repo, en contenidoClase/)` y del programa del curso.
> Demo: `uv run python clase1/demo_composicion.py`

**En una línea:** una imagen digital es una **matriz de números**. En Python es un arreglo NumPy de forma `(alto, ancho, canales)` con valores `uint8` (0–255).

---

## 1. Estructura

- **Píxel:** la unidad mínima de la imagen. En gris es 1 número; en color, un vector de 3.
- **Resolución:** ancho × alto. Una imagen de 640×480 tiene 307 200 píxeles, que en color son 921 600 números.
- **Tipos de imagen:**
  - binaria: 1 canal, solo 0 o 255
  - gris: 1 canal, 0–255
  - color: 3 canales
- **Ejemplo del slide 2:** la bandera como cubo 3×3 tiene `shape = (3, 3, 3)`, y `img[0, 0]` vale `[0, 255, 255]` (amarillo).

> ⚠️ **Orden de las coordenadas.** NumPy indexa `img[fila, columna]`, o sea `img[y, x]`. Las funciones de OpenCV que reciben puntos usan `(x, y)`, como `cv2.rectangle(img, (20, 20), …)` en `filtros.py`. Y `cv2.resize` recibe `(ancho, alto)`, al revés de `shape`.

---

## 2. BGR (slide 3)

OpenCV guarda los canales en orden **B, G, R**, no RGB.

| Color | Valor en OpenCV (B, G, R) |
|---|---|
| Amarillo | (0, 255, 255) |
| Azul | (255, 0, 0) |
| Rojo | (0, 0, 255) |

- **Separar canales:** `cv2.split(img)` o `img[:, :, 0]`. Cada canal es una imagen de **1 canal** y con `imshow` se ve en **gris** (blanco = 255). El slide los pinta de colores solo para ilustrar.
- **matplotlib usa RGB**, así que si muestras una imagen de OpenCV sin convertirla, los rojos y los azules salen intercambiados. Se arregla con `cv2.cvtColor(img, cv2.COLOR_BGR2RGB)`.

---

## 3. HSV (slides 4–5)

HSV separa el **color** del **brillo**:

| Canal | Qué es | Rango en OpenCV |
|---|---|---|
| **H** (tono) | qué color es | 0–179 (grados ÷ 2, porque 360 no cabe en un byte) |
| **S** (saturación) | qué tan puro es | 0 = gris → 255 = color puro |
| **V** (valor) | qué tan brillante es | 0 = negro → 255 = máximo brillo |

- En la bandera, el amarillo tiene **H = 30**, el azul **H = 120** y el rojo **H = 0**.
- **¿Para qué sirve?** Para **segmentar por color**. Una sombra cambia sobre todo V y apenas H, así que un rango de color sigue funcionando con distinta iluminación.
- **Fórmula (slide 4):** con R, G y B normalizados a [0, 1]: `V = max`, `S = Δ / max`, y H depende de cuál canal es el máximo. No hace falta memorizarla, `cvtColor` la aplica.

> ⚠️ **El rojo está en los dos extremos de H** (≈0 y ≈179; se ve en el arcoíris del demo de la clase 2). Para detectar rojo se necesitan **dos rangos** y unirlos.
>
> ⚠️ **`COLOR_BGR2HSV` ≠ `COLOR_RGB2HSV`.** Si usas la conversión equivocada, el rojo sale con H = 120, como si fuera azul (el demo lo muestra).

---

## 4. CIELab (slide 6)

- **Canales:**
  - **L\***: luminosidad (0 = negro, 100 = blanco)
  - **a\***: verde (−) ↔ rojo (+)
  - **b\***: azul (−) ↔ amarillo (+)
- **Idea clave:** está diseñado para que la **distancia entre dos colores** coincida con qué tan distintos los ve el ojo. Por eso sirve para comparar colores y para agrupar con K-Means.
- **En OpenCV (8 bits):** L se escala a 0–255, y a y b se desplazan +128, así que **128 es el "cero"**. Por ejemplo, un gris da `(137, 128, 128)`.
- **Cadena de conversión:** RGB → (normalizar + gamma) → XYZ → Lab.

### ¿Cuándo usar cada espacio?

| Espacio | Úsalo para |
|---|---|
| BGR | cargar, mostrar y dibujar |
| Gris | bordes y umbrales, cuando el color no importa (y son 3× menos datos) |
| HSV | segmentar por color |
| Lab | medir qué tan distintos son dos colores |

---

## 5. Operaciones básicas (del programa del curso)

| Operación | Código | Ojo con |
|---|---|---|
| Suma / resta | `cv2.add(a, b)`, `cv2.subtract(a, b)` | Con `uint8`, NumPy **da la vuelta** (`250 + 10 = 4`) y OpenCV **satura** (`255`). Para imágenes, usa OpenCV. |
| Lógicas | `cv2.bitwise_and/or/xor/not` | Se ven en la clase 2. |
| Recorte (ROI) | `roi = img[y1:y2, x1:x2]` | Es una **vista**: si la modificas, cambia la original. Usa `.copy()` si no quieres eso. |
| Redimensionar | `cv2.resize(img, (ancho, alto))` | El orden es (ancho, alto). |
| Rotar 90° | `cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)` | — |
| Rotar cualquier ángulo | `M = cv2.getRotationMatrix2D((cx, cy), ang, 1.0)` y luego `cv2.warpAffine(img, M, (ancho, alto))` | El ángulo positivo gira en sentido antihorario. |

---

## Conexión con lo que ya sé

- **Estructuras de datos:** una imagen es un arreglo 3D contiguo en memoria. Hacer slicing no copia datos (son vistas NumPy); por eso el ROI se comporta así.
- **Tiempo real / HPC:** un video de 640×480 a color y 30 fps son **~27.6 MB/s** de datos crudos. Por eso en tiempo real casi siempre se pasa a gris o se baja la resolución antes de procesar.

---

## Autoevaluación

<details><summary>1. <code>img.shape</code> da <code>(720, 1280, 3)</code>. ¿Cuál es el ancho?</summary>1280. El orden es (alto, ancho, canales).</details>
<details><summary>2. ¿Cuál es el valor BGR del verde puro?</summary>(0, 255, 0)</details>
<details><summary>3. ¿Por qué H llega solo hasta 179?</summary>Porque 360 no cabe en <code>uint8</code>, así que OpenCV guarda los grados divididos entre 2.</details>
<details><summary>4. ¿Qué pasa con <code>roi = img[0:100, 0:100]; roi[:] = 0</code>?</summary>La esquina superior izquierda de <code>img</code> también queda negra, porque el ROI es una vista.</details>

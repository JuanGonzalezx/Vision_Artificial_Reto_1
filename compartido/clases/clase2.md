# Clase 2 — Máscaras

> Apuntes para ponerme al día. Salen de los slides 7–8 de `los slides del profesor (fuera del repo, en contenidoClase/)`.
> Demo: `uv run python clase2/demo_mascaras.py`

**En una línea:** una máscara es una imagen de **1 canal** con solo dos valores: **255 = conservar** y **0 = descartar**. Le dice a una operación *dónde* actuar.

---

## 1. Operaciones lógicas bit a bit (slide 7)

| Función | Resultado en cada píxel |
|---|---|
| `cv2.bitwise_and(a, b)` | bits que están en 1 en **ambas** |
| `cv2.bitwise_or(a, b)` | bits que están en 1 en **alguna** |
| `cv2.bitwise_xor(a, b)` | bits que están en 1 en **solo una** |
| `cv2.bitwise_not(a)` | invierte la imagen (negativo) |

**Por qué funciona el AND con una máscara:** 255 en binario es `11111111`. Entonces `v & 255 = v` (el píxel se conserva) y `v & 0 = 0` (el píxel se borra). Por eso el slide dice que el blanco "actúa como 1".

> ⚠️ **Es bit a bit, no lógico.** `200 & 150 = 128`. Por eso la máscara debe tener solo 0 y 255: un gris intermedio da resultados sin sentido.

**Forma recomendada:**

```python
resultado = cv2.bitwise_and(img, img, mask=mascara)   # mascara: 1 canal
```

Con `mask=`, cualquier valor distinto de 0 cuenta como "conservar", y no necesitas una máscara de 3 canales como la del slide.

---

## 2. Cómo se crea una máscara

| Forma | Código | Cuándo se usa |
|---|---|---|
| Dibujándola | `m = np.zeros((alto, ancho), np.uint8)` y luego `cv2.circle(m, (x, y), r, 255, -1)` | una zona fija (ROI con cualquier forma) |
| Con un umbral | `_, m = cv2.threshold(gris, 127, 255, cv2.THRESH_BINARY)` | separar lo claro de lo oscuro |
| Por color | `m = cv2.inRange(hsv, (h1, s1, v1), (h2, s2, v2))` | objetos de un color (usa HSV, de la clase 1) |
| Por bordes | `m = cv2.Canny(gris, bajo, alto)` | clase 3 |

- `cv2.threshold` devuelve **dos valores**: `(umbral_usado, imagen)`. Por eso se escribe `_, m = …`.
- **Rojo con dos rangos:**

  ```python
  m = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255)) | cv2.inRange(hsv, (170, 100, 100), (179, 255, 255))
  ```

  Aquí `|` sobre dos máscaras equivale a `bitwise_or`.

---

## 3. Encontrar diferencias (slide 8)

```
img1, img2 → absdiff → gris → threshold(30) → máscara de cambios
```

- **`cv2.absdiff`** calcula `|I1 − I2|` en cada píxel. Donde las imágenes son iguales da 0 (negro); donde cambian, da un valor alto.
- **Umbral de 30:** ignora diferencias pequeñas (ruido de la cámara, compresión) y convierte el resto en 255.
- **Mismo tamaño:** las dos imágenes deben medir lo mismo. Se ajusta con `cv2.resize(img2, (img1.shape[1], img1.shape[0]))` (ojo: ancho, alto).

| I1 | I2 | \|I1 − I2\| | Umbral > 30 |
|---|---|---|---|
| 120 | 120 | 0 | 0 (negro) |
| 200 | 50 | 150 | 255 (blanco) |
| 80 | 90 | 10 | 0 (negro) |

> ⚠️ **¿Por qué no simplemente `img1 - img2`?** Con `uint8`, `50 − 200` da **106** en NumPy (da la vuelta) y **0** con `cv2.subtract` (satura y se pierde el cambio). `absdiff` da **150**, que es lo correcto.
>
> ⚠️ **El gris "pesa" poco el azul** (`0.114·B`). Un cambio de 150 solo en el canal B queda en **17** en gris, y el umbral de 30 lo ignora. En cambio, el mismo cambio en R da 45. Si importan los cambios de color, umbraliza cada canal por separado o usa el máximo de los canales.

---

## 4. Para qué sirve y hacia dónde va

- **Detección de movimiento (módulo 3):** es la misma idea con **frames consecutivos** de la cámara, `absdiff(frame_anterior, frame_actual)`.
- **Segmentación por color (módulo 2):** `inRange`, y luego morfología para limpiar la máscara.
- **Clase 3:** la salida de Canny **es una máscara**, y la erosión y la dilatación son operaciones sobre máscaras.

---

## Autoevaluación

<details><summary>1. ¿Cuánto da <code>100 & 255</code>? ¿Y <code>100 & 0</code>?</summary>100 y 0.</details>
<details><summary>2. ¿Qué devuelve <code>cv2.bitwise_and(img, img, mask=m)</code> donde <code>m</code> vale 0?</summary>Negro (0) en esos píxeles.</details>
<details><summary>3. ¿Por qué se usa <code>absdiff</code> y no <code>cv2.subtract</code>?</summary>Porque <code>subtract</code> satura en 0 y pierde los cambios donde I2 &gt; I1.</details>
<details><summary>4. Una máscara tiene 0 y 1 en vez de 0 y 255. ¿Qué pasa?</summary>Con <code>mask=</code> funciona, porque cualquier valor distinto de 0 cuenta. Si la usas como segunda imagen en el AND, <code>v & 1</code> solo deja el último bit. Y con <code>imshow</code> se ve negra.</details>

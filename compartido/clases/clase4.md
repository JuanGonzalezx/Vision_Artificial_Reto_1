# Clase 4 — K-Means (segmentación de color no supervisada)

> Apuntes para ponerme al día. Código de ejemplo dado en clase (Colab, `cv2` + `sklearn.cluster.KMeans`).
> Versión local: `uv run python clase4/kmeans_segmentacion.py <imagen> [K]`
> Apuntes completos de lo anterior: [clase 1](clase1.md) · [clase 2](clase2.md) · [clase 3](clase3.md)

**En una línea:** K-Means es un algoritmo de **aprendizaje no supervisado** que agrupa datos parecidos (aquí, píxeles) en K clústeres según la distancia entre ellos, sin necesitar etiquetas.

---

## 0. Vocabulario

- **Centroide:** el punto "central" de un clúster en el espacio de n atributos (aquí, n = 3: R, G, B). Es el elemento que representa al grupo.
- **Clúster:** grupo de observaciones similares, medidas por distancia.

## 1. El algoritmo, paso a paso

1. Elegir el número de clústeres, **K**.
2. Elegir K centroides iniciales (al azar).
3. Medir la distancia de cada observación a los K centroides.
4. Asignar cada observación al centroide más cercano.
5. Por cada grupo, recalcular el centroide como el **promedio** de sus observaciones. Repetir 3–5 hasta que los centroides dejen de moverse (converge).

## 2. Por qué un píxel es una "observación"

**Conexión con clase 1:** una imagen es una matriz `(alto, ancho, canales)`. Para K-Means, esa estructura espacial estorba: lo que le importa es el **color** de cada píxel, no su posición. Por eso el primer paso siempre es aplanar:

```python
pixeles = imagen_rgb.reshape((-1, 3))   # (alto*ancho, 3): una fila por píxel
pixeles = pixeles.astype(np.float32)    # K-Means calcula distancias/promedios; uint8 se desborda (clase 1)
```

Cada píxel pasa a ser un punto en un espacio 3D (R, G, B), y K-Means agrupa por cercanía en ese espacio de color — sin importar en qué parte de la imagen estaba.

## 3. `sklearn.cluster.KMeans`

```python
modelo = KMeans(n_clusters=K, random_state=42, n_init=10)
etiquetas = modelo.fit_predict(pixeles)
```

| Parámetro | Qué hace |
|---|---|
| `n_clusters` | K, el número de grupos de color a buscar |
| `random_state` | fija la semilla aleatoria → resultado reproducible |
| `n_init` | corre el algoritmo completo n veces con distintos centroides iniciales y se queda con el mejor resultado; evita quedar atrapado en un mínimo local |

`fit_predict` devuelve `etiquetas`: un arreglo del mismo largo que `pixeles`, con la etiqueta de clúster (0, 1, 2…) de cada uno.

## 4. Reconstruir la imagen segmentada

```python
centroides = modelo.cluster_centers_        # K colores promedio, en float
colores = np.uint8(centroides)               # a enteros 0-255 para poder mostrarlos

pixeles_segmentados = colores[etiquetas]     # cada píxel -> color de su centroide (indexado "fancy")
imagen_segmentada = pixeles_segmentados.reshape(imagen_rgb.shape)  # deshace el reshape del paso 2
```

El efecto es "posterizar" la imagen: en vez de miles de colores, queda reducida a K colores planos, cada uno el promedio de un grupo.

> ⚠️ **`reshape` va y viene.** Se aplana para poder alimentar `KMeans` (tabla de observaciones × atributos) y se vuelve a armar al final con `.reshape(imagen_rgb.shape)`, porque en el camino se perdió la forma `(alto, ancho, 3)`.

## 5. Relación con `inRange` (clase 2)

| | `inRange` (clase 2) | K-Means (clase 4) |
|---|---|---|
| Rango de color | lo defines tú a mano (H, S, V) | lo descubre el algoritmo |
| Resultado | máscara binaria (0/255) para un color específico | K colores promedio + cada píxel asignado a uno |
| Costo | muy barato, corre en cada frame de video | más pesado; no pensado para correr en tiempo real por frame |
| Uso típico | segmentar en video/tiempo real | análisis exploratorio, calibración, compresión de color |

**Idea práctica:** K-Means se puede usar *offline* sobre una foto de una señal para descubrir su color dominante (el centroide) y así calibrar mejor los rangos que luego usa `inRange` en el pipeline en tiempo real — pero no reemplaza a `inRange` dentro del loop de video por su costo.

Eso es justo lo que hace `kmeans_segmentacion.py`: imprime cada centroide en RGB y en HSV con su peso en la imagen, para copiar el H al `inRange`. Es la idea que quedó como estrategia propia del [reto 1](../arquitectura.md).

---

## Autoevaluación

<details><summary>1. ¿Por qué hay que hacer <code>reshape((-1, 3))</code> antes de pasarle los píxeles a KMeans?</summary>Porque KMeans espera una tabla de observaciones × atributos (una fila por píxel, 3 columnas RGB), no una cuadrícula 2D con estructura espacial.</details>
<details><summary>2. ¿Para qué sirve <code>n_init=10</code>?</summary>Corre el algoritmo 10 veces con distintos centroides iniciales (al azar) y se queda con el mejor resultado, para no quedar atrapado en un mínimo local.</details>
<details><summary>3. ¿Qué representa cada valor en <code>cluster_centers_</code>?</summary>El color promedio (R, G, B) de todos los píxeles asignados a ese clúster — el centroide.</details>
<details><summary>4. ¿Por qué K-Means no es la primera opción para segmentar color en el carrito en tiempo real?</summary>Es más costoso que <code>inRange</code>; <code>inRange</code> es una comparación directa por rango y corre bien en cada frame, mientras K-Means no está pensado para eso.</details>

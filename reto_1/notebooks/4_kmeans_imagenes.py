"""Codigo extraido de 4_Kmeans_Imagenes.ipynb (notebook del profesor).

Generado con tools/notebooks.py; no editar a mano.
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt

from google.colab import files
from sklearn.cluster import KMeans


# 1. Cargar la imagen
archivos = files.upload()
nombre_imagen = next(iter(archivos))


# 2. Leer la imagen
imagen_bgr = cv2.imread(nombre_imagen)

if imagen_bgr is None:
    raise ValueError(
        "No fue posible leer la imagen seleccionada."
    )


# 3. Convertir BGR a RGB
imagen_rgb = cv2.cvtColor(
    imagen_bgr,
    cv2.COLOR_BGR2RGB
)


# 4. Mostrar la imagen original
plt.figure(figsize=(8, 6))
plt.imshow(imagen_rgb)
plt.title("Imagen original")
plt.axis("off")
plt.show()


# 5. Obtener sus dimensiones
alto, ancho, canales = imagen_rgb.shape

print("Alto:", alto)
print("Ancho:", ancho)
print("Canales:", canales)
print("Cantidad de píxeles:", alto * ancho)


# 6. Convertir la imagen en una tabla de píxeles
pixeles = imagen_rgb.reshape((-1, 3))
pixeles = pixeles.astype(np.float32)


# 7. Definir la cantidad de clústeres
K = 3


# 8. Crear y entrenar K-Means
modelo = KMeans(
    n_clusters=K,
    random_state=42,
    n_init=10
)

etiquetas = modelo.fit_predict(pixeles)


# 9. Obtener los centroides
centroides = modelo.cluster_centers_

print("Centroides encontrados:")
print(centroides)


# 10. Convertir los centroides a colores enteros
colores = np.uint8(centroides)


# 11. Reemplazar cada píxel por su centroide
pixeles_segmentados = colores[etiquetas]


# 12. Reconstruir la imagen
imagen_segmentada = pixeles_segmentados.reshape(
    imagen_rgb.shape
)


# 13. Comparar los resultados
fig, ejes = plt.subplots(
    1,
    2,
    figsize=(14, 6)
)

ejes[0].imshow(imagen_rgb)
ejes[0].set_title("Imagen original")
ejes[0].axis("off")

ejes[1].imshow(imagen_segmentada)
ejes[1].set_title(
    f"Imagen segmentada con K = {K}"
)
ejes[1].axis("off")

plt.tight_layout()
plt.show()


"""Codigo extraido de 1_Fundamentación.ipynb (notebook del profesor).

Generado con tools/notebooks.py; no editar a mano.
"""


# #Composición de la imagen digital
# Una imagen digital está formada por píxeles organizados en una matriz.
# En OpenCV, cada píxel tiene un color representado por 3 valores:
# 
# ```text
# [B, G, R]
# ```
# 
# (B = azul, G = verde, R = rojo)
# 
# Para crear imágenes, podemos modificar regiones de la matriz y asignarles colores.
# En este ejemplo construiremos la bandera de Colombia pintando tres franjas: amarilla, azul y roja.
# 
# _(imagen en el notebook original)_

import cv2
import numpy as np
import matplotlib.pyplot as plt

# Crear imagen blanca
imagen = np.ones((300, 500, 3), dtype=np.uint8)

# Franja amarilla
imagen[0:150, :] = [0, 255, 255]

# Franja azul
imagen[150:225, :] = [255, 0, 0]

# Franja roja
imagen[225:300, :] = [0, 0, 255]

# Convertir de BGR a RGB para mostrar en Colab
imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)

# Mostrar imagen
plt.imshow(imagen_rgb)
# plt.axis("off")
plt.title("Bandera de Colombia")
plt.show()


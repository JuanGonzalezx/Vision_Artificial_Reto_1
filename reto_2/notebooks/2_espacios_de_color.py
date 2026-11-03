"""Codigo extraido de 2_Espacios_de_Color.ipynb (notebook del profesor).

Generado con tools/notebooks.py; no editar a mano.
"""


# # Espacio RGB
# El espacio de color **RGB** en OpenCV es un modelo que representa los colores de una imagen mediante la combinación de tres canales de luz: rojo (**Red**), verde (**Green**) y azul (**Blue**).
# 
# La teoría consiste en que cada píxel de la imagen almacena la intensidad de esos tres colores, y al mezclarlos se obtiene un color final.
# Cada canal suele tener valores entre **0 y 255**:
# 
# * `0` → ausencia de color
# * `255` → máxima intensidad del color
# 
# Por ejemplo:
# 
# * `(255,255,255)` produce blanco porque los tres colores están al máximo.
# * `(0,0,0)` produce negro porque no hay luz.
# * `(255,0,0)` produce rojo puro.
# 
# En OpenCV esta teoría se aplica igual, pero la biblioteca guarda los canales en orden **BGR** (Blue, Green, Red) en lugar de RGB. Esto significa que internamente los píxeles se almacenan primero con azul, luego verde y finalmente rojo.
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
plt.axis("off")
plt.title("Bandera de Colombia")
plt.show()


# # Espacio HSV
# 
# El espacio de color **HSV** es un modelo que representa los colores de una forma más cercana a cómo los percibe el ser humano.
# En OpenCV, HSV significa:
# 
# * **H (Hue / Matiz)** → el tipo de color
# * **S (Saturation / Saturación)** → la intensidad o pureza del color
# * **V (Value / Valor)** → el brillo del color
# 
# ### Teoría de cada componente
# 
# #### 1. Hue (H)
# 
# Define qué color es:
# 
# * rojo
# * azul
# * verde
# * amarillo, etc.
# 
# En OpenCV el rango de H es:
# 
# ```python id="7bfy93"
# 0 - 179
# ```
# 
# Ejemplos:
# 
# * Rojo ≈ 0
# * Verde ≈ 60
# * Azul ≈ 120
# 
# ---
# 
# #### 2. Saturation (S)
# 
# Define qué tan fuerte o puro es el color.
# 
# * `0` → gris (sin color)
# * `255` → color intenso
# 
# Ejemplo:
# 
# * rojo apagado → baja saturación
# * rojo vivo → alta saturación
# 
# Rango:
# 
# ```python id="kv25x7"
# 0 - 255
# ```
# 
# ---
# 
# #### 3. Value (V)
# 
# Representa el brillo.
# 
# * `0` → negro
# * `255` → máximo brillo
# 
# Rango:
# 
# ```python id="4ymxq9"
# 0 - 255
# ```
# 
# ---
# 
# ### ¿Por qué HSV es importante en OpenCV?
# 
# HSV se usa mucho en visión artificial porque permite detectar colores más fácilmente que RGB/BGR.
# Por ejemplo, para detectar objetos amarillos, azules o rojos, es más sencillo trabajar con el canal H (matiz) que con combinaciones BGR.
# 
# Conversión en OpenCV:
# 
# ```python id="8n9v4w"
# hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# ```
# 
# Así, OpenCV transforma la imagen desde BGR al espacio HSV para facilitar el análisis de colores.
# 
# _(imagen en el notebook original)_

# Convertir de BGR a HSV
imagen_hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)

# Mostrar HSV puro
plt.figure(figsize=(8,5))
plt.imshow(imagen_hsv)
plt.axis("off")
plt.title("Bandera de Colombia en HSV puro")
plt.show()


# # Ejemplo 2

import cv2
import numpy as np
import matplotlib.pyplot as plt
import urllib.request

# =========================
# CARGAR IMAGEN DE PAISAJE
# =========================

url = "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200"

req = urllib.request.urlopen(url)
arr = np.asarray(bytearray(req.read()), dtype=np.uint8)

# OpenCV carga en BGR
imagen_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)

# =========================
# CONVERTIR A HSV
# =========================

imagen_hsv = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)

# Convertir BGR -> RGB para mostrar original
imagen_rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)

# =========================
# MOSTRAR
# =========================

plt.figure(figsize=(14,6))

# Imagen original
plt.subplot(1,2,1)
plt.imshow(imagen_rgb)
plt.title("Paisaje Original (RGB)")
plt.axis("off")

# Imagen HSV pura
plt.subplot(1,2,2)
plt.imshow(imagen_hsv)
plt.title("Paisaje en HSV Puro")
plt.axis("off")

plt.show()


# # Espacio de color CIELAB
# 
# El espacio de color **CIELAB** (o **L*a*b*** ) es un modelo de color diseñado para representar los colores de una forma más cercana a la percepción humana.
# Fue creado por la **CIE (Commission Internationale de l'Éclairage)**.
# 
# Se compone de tres canales:
# 
# * **L*** → luminosidad o brillo
# * **a*** → eje entre verde y rojo
# * **b*** → eje entre azul y amarillo
# 
# ---
# 
# ## Teoría de cada componente
# 
# ### 1. L* (Lightness)
# 
# Representa la cantidad de luz:
# 
# * `0` → negro
# * `100` → blanco
# 
# No contiene información de color, solo brillo.
# 
# ---
# 
# ### 2. a*
# 
# Representa colores entre:
# 
# * valores negativos → verde
# * valores positivos → rojo
# 
# Ejemplo:
# 
# * `a* = -50` → tono verdoso
# * `a* = +50` → tono rojizo
# 
# ---
# 
# ### 3. b*
# 
# Representa colores entre:
# 
# * valores negativos → azul
# * valores positivos → amarillo
# 
# Ejemplo:
# 
# * `b* = -50` → azulado
# * `b* = +50` → amarillento
# 
# ---
# 
# # ¿Por qué CIELAB es importante?
# 
# CIELAB intenta que la distancia entre colores sea perceptualmente uniforme.
# Es decir:
# 
# * dos colores “parecidos” para el ojo humano
# * tendrán valores cercanos en Lab.
# 
# Por eso se usa mucho en:
# 
# * visión artificial,
# * segmentación,
# * análisis de color,
# * impresión,
# * control de calidad industrial.
# 
# ---
# 
# # Conversión en OpenCV
# 
# OpenCV convierte desde BGR a Lab con:
# 
# ```python
# lab = cv2.cvtColor(imagen, cv2.COLOR_BGR2LAB)
# ```
# 
# ---
# 
# _(imagen en el notebook original)_

import cv2
import numpy as np
import matplotlib.pyplot as plt

# =========================
# CREAR BANDERA
# =========================

# Crear imagen blanca
imagen = np.ones((300, 500, 3), dtype=np.uint8)

# Franja amarilla (BGR)
imagen[0:150, :] = [0, 255, 255]

# Franja azul (BGR)
imagen[150:225, :] = [255, 0, 0]

# Franja roja (BGR)
imagen[225:300, :] = [0, 0, 255]

# =========================
# CONVERTIR A CIELAB
# =========================

imagen_lab = cv2.cvtColor(imagen, cv2.COLOR_BGR2LAB)

# =========================
# MOSTRAR LAB PURO
# =========================

plt.figure(figsize=(8,5))

# Mostrar directamente LAB
plt.imshow(imagen_lab)
plt.axis("off")
plt.title("Bandera de Colombia en CIELAB Puro")

plt.show()


# # Diferencia con RGB/HSV/CIELAB
# 
# | Espacio | Qué representa              |
# | ------- | --------------------------- |
# | RGB     | mezcla de luces             |
# | HSV     | color, intensidad y brillo  |
# | CIELAB  | percepción humana del color |
# 
# CIELAB separa mejor:
# 
# * iluminación
# * y color real,
# 
# por eso funciona muy bien para detectar objetos aunque cambie la luz.


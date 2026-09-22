# Memory

## Project Overview
See @README.md for project overview and @pyproject.toml for dependencies and project configuration.

## Reto (especificación)
La especificación completa del reto está en @Reto-1.docx. Resumen:
- Programar el "cerebro" de un robot móvil autónomo que sigue una línea guía sobre una pista.
- Debe procesar imágenes de la cámara en tiempo real y decidir el movimiento del robot.
- Debe reconocer dos señales de tránsito: octágono rojo (PARE, detenerse) y octágono verde (SIGA, continuar).

## Restricciones técnicas (OBLIGATORIO)
- Solo se pueden usar los temas trabajados en los notebooks de @resources. Cada técnica del algoritmo debe estar respaldada por uno de estos notebooks:
  - `resources/1_Fundamentación.ipynb`: creación y manipulación básica de imágenes, canales BGR/RGB, mostrar imágenes.
  - `resources/2_Espacios_de_Color.ipynb`: espacios de color RGB, HSV y CIELAB, conversiones entre ellos y segmentación por color.
  - `resources/3_OperacionesMatemáticas.ipynb`: operaciones aritméticas (resta) y lógicas (AND), uso de máscaras.
  - `resources/4_Kmeans_Imagenes.ipynb`: K-Means en su modalidad básica sobre imágenes.
- NO está permitido usar temas que no estén en los notebooks, en particular:
  - Redes neuronales artificiales ni deep learning.
  - Modelos previamente entrenados.
  - Detectores tipo YOLO, SSD, Faster R-CNN u otros equivalentes.
  - Cascadas Haar.
  - Servicios externos de inteligencia artificial.
  - Librerías o algoritmos que hagan la detección de la línea o las señales automáticamente sin implementar la lógica.
- Si una solución requiere una técnica que no aparece en los notebooks, no la uses: busca una alternativa con los temas disponibles.

## Code Style Guidelines
- Use descriptive variable names.
- Follow existing patterns in the codebase.
- Extract complex conditions into meaningful boolean variables.
- Sigue las mejores prácticas de programación y mantén las cosas lo más simples posible.
- Agrega comentarios útiles que expliquen la lógica de cada etapa del algoritmo (segmentación, detección de línea, detección de señales, control).
- El código debe ser comprensible y estar organizado por etapas, para poder explicar cómo funciona cada parte.

## Architecture Notes
Add important architectural decisions and patterns here.

## Common Workflows
Document frequently used workflows and commands here.

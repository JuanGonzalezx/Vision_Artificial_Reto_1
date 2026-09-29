# Guion de la sustentación (primera, 2026-09-29)

5 minutos, hablan los tres. La idea no es decir que está terminado, sino mostrar **qué funciona, con qué números y qué falta**. Frente a una pregunta que no sepamos: "no lo hemos medido todavía" y seguir.

## Qué mostrar, en orden

**1. El problema y la restricción (Santiago, 30 s)**
Cerebro de un robot seguidor de línea que además obedece PARE y SIGA, usando solo lo visto en clase: color, máscaras, morfología, contornos y K-Means. Nada de deep learning ni modelos preentrenados.

**2. El pipeline, con la imagen de etapas (Daniel, 1 min)**
Abrir `docs/media/etapas.png`: frame → canal V → máscara de la línea en su franja → máscara de las señales → decisión en el HUD. Una frase por etapa y de qué clase sale cada una.

**3. El video de demostración (Juan David, 1 min)**
`docs/media/demo_sustentacion.mp4`, tres segmentos: sigue la línea con la señal SIGA a la vista, se detiene con el PARE, y pierde la línea y entra a BUSCANDO. Todo corrido sobre los videos de ensayo del profesor.

**4. Los números (Juan David, 1 min)**

| Qué | Resultado |
|---|---|
| Línea detectada | 100% en los 4 clips de ruta ideal, 91.1% sobre los 2341 frames |
| Recuperación | 5 de 5 clips de descarrilamiento: busca hacia el lado correcto |
| Señales | Las dos detectadas en los 4 clips de ruta ideal |
| Falsos positivos | 0 en los 5 clips sin señales |
| Saltos de detección | 4 en total (eran 16 antes del suavizado) |

Y la frase importante: **esos números salen de un comando** (`tools/evaluar.py`), no de mirar el video y opinar.

**5. Lo que falta y cómo lo vamos a probar (Santiago, 1 min)**
Cámara del celular por IP, montaje definitivo, pista propia con cinta, y el simulador para probar el control en lazo cerrado. Fechas.

**6. Una limitación dicha por nosotros antes de que la pregunten (30 s)**
Todo está calibrado con los videos del profesor. Si cambia la luz, los rangos cambian; por eso tenemos la calibración automática con K-Means, que se rehace en dos minutos con una foto de la pista.

## Las tres cosas que más nos pueden preguntar

1. **"¿Por qué esos umbrales?"** → Porque los barrimos. `tools/barrido.py vmax 90 100 110 120 129`: con 110 hay 16 saltos y 5/5 recuperaciones; con 129 sube la detección pero se va a las sombras. La tabla está en la bitácora.
2. **"Eso no es un octágono."** → Cierto, y lo medimos: en sus videos las señales son cartulinas inclinadas, dan 4-5 vértices y circularidad 0.58-0.72. Por eso el color y el área deciden y la forma suma confianza, con un parámetro para volverlo estricto.
3. **"¿Cómo sé que no está siguiendo una sombra?"** → Por la métrica de saltos y porque revisamos las máscaras frame por frame. Y mostrar el HUD con la máscara encima.

El resto de preguntas previstas están en [preguntas-del-profe.md](preguntas-del-profe.md). Hay que leerlo los tres antes de entrar.

## Repartición al hablar

Cada uno explica **una parte que no programó**. Es la mejor forma de comprobar que los tres entendemos el pipeline completo, y es un criterio de la rúbrica ("todos los integrantes conocen y explican la solución").

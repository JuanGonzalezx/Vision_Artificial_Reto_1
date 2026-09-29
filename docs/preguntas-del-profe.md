# Preguntas que nos va a hacer el profesor (y qué respondemos)

La rúbrica califica "comunicación verbal" y "uso de técnicas" aparte del recorrido, y el profesor va a buscar el hueco. Cada respuesta aquí tiene que poder darse **sin abrir el código**, y los tres tenemos que poder darla.

Regla de oro: si algo no lo medimos, se dice "no lo medimos". Inventar un número es lo único que hunde de verdad.

## Sobre el color

**¿Por qué HSV y no RGB?**
Porque en RGB el brillo está mezclado en los tres canales: una sombra cambia R, G y B a la vez y el rango deja de servir. En HSV el tono queda en un solo canal y la sombra se va casi toda a V. Medido en nuestros frames: el piso está en V≈200 y la línea entre V=29 y V=90.

**¿Y por qué no CIELab, que también separa la luminosidad?**
Se puede, y para *comparar* colores es mejor porque las distancias son perceptuales. Usamos HSV porque `inRange` con H es más directo de calibrar y de explicar. Si la iluminación de la pista nos da problemas, el plan B es el canal L de Lab para la línea.

**¿Por qué la línea la segmentan por brillo y no por tono?**
Porque es negra: un color oscuro no tiene tono estable (con S baja, H es ruido). Lo que la separa del piso es V. Por eso el rango es `(0,0,0)-(179,90,110)`: cualquier tono, saturación baja, brillo bajo.

**¿Por qué el rojo necesita dos rangos?**
Porque H es un círculo y el rojo está partido entre 0 y 179. En nuestros videos la señal roja cayó en H=173-175. Si usáramos solo el rango bajo, no la veríamos.

**¿Qué pasa si cambia la luz el día de la carrera?**
Recalibramos ahí mismo: corremos K-Means sobre una foto de la pista (clase 4), los centroides nos dan los colores dominantes en HSV y de ahí salen los rangos. Toma un par de minutos. Es nuestra estrategia propia y por eso la elegimos.

## Sobre las máscaras y la morfología

**¿Por qué apertura y luego cierre, y no al revés?**
La apertura (erosión → dilatación) quita las motas sueltas; el cierre (dilatación → erosión) tapa los huecos y une la línea cuando queda partida. En ese orden primero se limpia y después se rellena; al revés, el cierre agranda el ruido antes de quitarlo.

**¿Por qué un kernel de 3×3?**
Porque uno más grande engorda y deforma la línea, y la posición del centroide es justo lo que no queremos mover. Con 3×3 y varias iteraciones se controla mejor cuánto se limpia.

**Si erosionas, ¿no borras la línea?**
Sobre una máscara "rellena" como la de la línea, no: es ancha. Sobre bordes de 1 píxel sí, y lo comprobamos en la clase 3: aplicar erosión primero sobre la salida de Canny deja la imagen en negro.

## Sobre las señales

**¿Cómo saben que es un octágono y no un círculo?**
Por tres filtros juntos: número de vértices con `approxPolyDP` (7 a 9), relación de aspecto de la caja (cercana a 1) y circularidad `4πA/P²`. Hace falta el tercero porque contar vértices no distingue: en nuestras pruebas un círculo también dio 8 vértices.

**¿Cómo eligieron el epsilon de `approxPolyDP`?**
Como fracción del perímetro (3%), no en píxeles, para que funcione igual con la señal cerca y lejos. Probado: con 1% aparecen vértices de más (un triángulo salió con 4) y entre 2% y 4% clasifica bien.

**Si pongo algo rojo en el fondo, ¿su robot frena?**
No debería, y por tres razones: la ROI de las señales deja fuera la parte de la imagen donde está el carro, hay un área mínima (la señal solo cuenta cuando está cerca) y hay que verla en varios frames seguidos. Lo aprendimos midiendo: las pilas del carro son naranja (H 6-15) y se colaban en el rango del rojo.

**¿Cómo saben a qué distancia está la señal?**
No medimos distancia, usamos el **área del contorno como proxy**: entre más grande, más cerca. Con la señal cerca da entre 34.000 y 39.000 píxeles. Es una aproximación y falla si la señal está muy inclinada.

**¿Por qué no exigen que la señal sea un octágono, si el reto habla de octágonos?**
Porque lo medimos en sus propios videos de ensayo: ahí las señales son cartulinas inclinadas, `approxPolyDP` devuelve 4 o 5 vértices y la circularidad queda entre 0.58 y 0.72, cuando un octágono de frente da 0.95. Exigir la forma nos dejaría sin detectar ninguna. Entonces el color y el área deciden, y la forma suma confianza: el resultado trae un campo que dice si además es octágono, y con un parámetro se puede volver estricto cuando la señal se vea de frente.

**¿Y así no confunden cualquier cosa roja con un PARE?**
En los 5 videos de descarrilamiento, donde no hay señales, tenemos 0 detecciones. Además del color pedimos área mínima, forma compacta (ni tira larga ni delgada) y que aparezca en varios frames seguidos.

**¿Qué pasa cuando la señal está encima de la línea?**
Lo detectamos graficando la desviación en el tiempo: la señal va sobre una barra negra que cruza la pista, y esa barra entra en la máscara de la línea (es negra igual que la línea) y mueve el centroide. Por eso, mientras la caja de la señal toque la franja de la línea, mantenemos el rumbo que traíamos. Medido: el p95 del cambio de desviación con señal a la vista bajó de 0.135 a 0.017. El costo: durante ese segundo o dos el robot no sigue una curva.

## Sobre el control

**¿Cómo deciden si va a la izquierda o a la derecha?**
Sacamos el centroide de la línea dentro de la ROI y lo comparamos con el centro de la imagen. La desviación se normaliza entre −1 y +1, así el número no depende de la resolución de la cámara.

**¿Por qué una zona muerta?**
Sin ella, el robot corrige por un error de dos píxeles y oscila. La zona muerta dice "esto ya está centrado". El costo es que no corrige desviaciones mínimas.

**¿Qué pasa si pierde la línea?**
Entra al estado `BUSCANDO` y gira hacia el último lado donde la vio. Antes de eso mantiene el rumbo unos frames, porque perderla un instante suele ser un reflejo o un frame movido.

**¿Por qué no un PID?**
Porque no lo hemos visto en el curso; lo nuestro es proporcional con zona muerta. Si nos piden mejorarlo, un término derivativo ayudaría contra el zigzag.

**¿Por qué no frena dos veces con la misma señal de PARE?**
Porque después de obedecer una queda un tiempo de espera, y porque la señal debe confirmarse en varios frames antes de contar.

## Sobre las restricciones

**¿Eso no es un modelo preentrenado?**
No hay modelos. Todo son umbrales de color, morfología y propiedades de contornos. La única librería fuera de OpenCV es scikit-learn, y solo para el K-Means de la clase 4, que está en la lista de técnicas permitidas.

**¿Por qué no usan Hough para la línea?**
Porque no lo hemos visto en clase todavía (está en el módulo siguiente del programa). Si nos lo autoriza, es una alternativa para tramos rectos.

**¿En qué se diferencia su solución de la de los otros equipos?**
En tres cosas: calibramos los rangos con K-Means sobre la pista real en vez de a ojo; miramos dos franjas, una cercana para corregir y una lejana para anticipar la curva; y validamos las señales por color, forma, área y persistencia, no solo por color.

## Sobre los números

**¿Cómo saben que están detectando la línea y no una sombra?**
Por dos vías. Mirar la máscara sobre los frames, que es lo que hicimos. Y una métrica: contamos los **saltos**, las veces que la desviación brinca más de 0.35 entre dos frames seguidos. El carro moviéndose no puede producir eso; si pasa, la máscara se fue a otra cosa.

**¿Por qué ese umbral de brillo y no otro?**
Porque los probamos. Con V ≤ 129, que es lo que propone nuestra propia calibración automática, la detección sube de 91.1% a 93.3% **y empeora**: los saltos pasan de 16 a 24 y se pierde una de las cinco recuperaciones. Con V ≤ 110 quedan 16 saltos y 5 de 5. La tabla está en la bitácora.

**Entonces, ¿para qué sirve el K-Means si al final usan otro valor?**
Para no partir de cero: propone los rangos en un par de minutos con una foto de la pista, y la evaluación sobre los clips decide cuál se queda. Propone la máquina, decide el dato.

**¿Cómo comprueban que el robot recupera la trayectoria?**
Los clips de descarrilamiento dicen en el nombre hacia dónde se fue la línea, así que la evaluación verifica sola que el robot busque hacia ese lado. Hoy pasan 5 de 5.

## Las incómodas

**¿Qué es lo que peor funciona de su solución?**
Que todo depende de la calibración de color, y la calibración depende de la luz. Por eso la podemos rehacer en dos minutos.

**Muéstrame en el código dónde está X.**
`reto/linea.py` la línea, `reto/senales.py` las señales, `reto/control.py` la decisión, `reto/config.py` todos los umbrales y `reto/pipeline.py` el orden. Ningún número mágico vive dentro de la lógica.

**¿Y si le tapo media línea? ¿Y si la pista tiene un cruce?**
Un cruce no lo resolvemos: tomaríamos el contorno más grande, que puede ser el ramal equivocado. Es una limitación conocida y está escrita en la bitácora.

**¿Cuántos FPS procesan?**
Lo medimos en cada corrida y sale en el HUD y en el CSV. (Ojo: hay que llegar a la clase con ese número medido de verdad, con el celular, no con la webcam.)

## Lo que hay que tener medido antes de la clase

- [ ] FPS reales con la cámara del celular, con el montaje definitivo.
- [ ] Porcentaje de frames con la línea detectada en los 9 clips (`tools/evaluar.py`).
- [ ] Área de la señal a la distancia a la que queremos que frene.
- [ ] Qué pasa en los 5 videos de descarrilamiento: ¿entra a `BUSCANDO` y se recupera?
- [ ] Un ejemplo de falso positivo y cómo lo quitamos (sirve para responder la pregunta incómoda).

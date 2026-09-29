# Flujo de pruebas: de los videos del profesor a la pista

Cuatro niveles, del más barato al más caro. Cada uno valida algo distinto, y ninguno reemplaza al siguiente.

| Nivel | Con qué | Qué valida | Qué **no** valida |
|---|---|---|---|
| 0. Frames sueltos | `datos/frames/*.jpg` | Rangos de color, ROI, tamaños de kernel | Nada que dependa del tiempo |
| 1. Clips del profesor | `datos/clips/*.mp4` | Segmentación de la línea y detección de señales, cuadro a cuadro | El control: el video no reacciona a lo que decidimos |
| 2. Simulador | el juego de Daniel | Máquina de estados, ganancias, recuperación de la línea | La percepción, si los frames son dibujados |
| 3. Pista real | celular + pista | Todo junto, con la luz y los FPS reales | — |

## Nivel 0 — Calibrar con frames

Calibrar es mirar **un frame**, no un video. `tools/preparar_videos.py` saca varios frames repartidos de cada video justo para esto.

1. K-Means sobre un frame de la pista → los centroides son los colores dominantes, con su H y su S (clase 4).
2. Esos valores entran a `reto/config.py` (o a un JSON de calibración).
3. Se verifica con la máscara: `uv run main.py --fuente datos/clips/pista1.mp4 --mascaras`.

## Nivel 1 — Percepción con los clips (lazo abierto)

```bash
uv run main.py --fuente datos/clips/pista1.mp4 --mascaras --grabar
```

Se mira la máscara, no el video bonito: ¿la línea queda entera y sin huecos?, ¿el octágono aparece completo?, ¿algo rojo del fondo se cuela? `--grabar` deja el video procesado y un CSV con las decisiones en `datos/grabaciones/`, que es material directo para el póster.

Esto **no** valida el control: el video hace lo mismo pase lo que pase.

## Nivel 2 — Simulador (lazo cerrado)

Aquí sí se cierra el lazo: la decisión mueve el carrito y cambia lo que se ve después. Es la única forma de ver si las ganancias y los estados se comportan, sin tener el carro.

**Cómo encaja sin romper nada:** el simulador es un **actuador** más (`reto/actuador.py`). Recibe la misma `Decision` que recibiría el robot, así que `control.py` no cambia ni una línea cuando pasemos al hardware.

```python
class ActuadorSimulador:
    def aplicar(self, decision, contexto=None):
        # traduce accion/giro al movimiento del carrito
    def cerrar(self): ...
```

Dos formas de conectarlo, en orden de simplicidad:

1. **Todo en un proceso** (recomendado para empezar): el simulador dibuja la vista de la cámara, esa imagen entra a `procesar_frame`, la `Decision` vuelve al simulador.

   ```python
   while True:
       frame = simulador.renderizar_vista_camara()
       decision, _ = procesar_frame(frame, estado, config)
       simulador.aplicar(decision)
   ```

   Con esto el lazo queda cerrado de punta a punta: visión → control → movimiento → nueva vista.

2. **Dos procesos** (el simulador como juego aparte, hablando por UDP o HTTP con el cerebro). Más realista respecto al robot, pero más cosas que pueden fallar. Solo si el simulador crece.

**Detalle del tiempo:** `control.decidir` recibe el parámetro `ahora`. En el simulador se le pasa el reloj del simulador, y así los 3 segundos del PARE se respetan aunque la simulación corra más rápido o más lento que el tiempo real.

**La trampa del simulador:** si dibuja la pista con colores planos, la percepción ahí siempre va a funcionar y eso no dice nada de la pista real. Dos formas de que no engañe:

- que el simulador le meta ruido, desenfoque e iluminación despareja a la vista, o
- probar el control con la desviación exacta que da el simulador (saltándose la visión) y dejar la percepción para los niveles 1 y 3.

## Nivel 3 — Pista real

Celular por WiFi, pista, luz del salón. Lo que siempre sorprende aquí son dos cosas: **los FPS** (si caen, el control llega tarde) y **la luz** (los rangos calibrados con los videos del profesor pueden no servir). Por eso la calibración tiene que poder rehacerse en dos minutos el día de la carrera.

## Qué revisar en el CSV de `--grabar`

Con `datos/grabaciones/*_decisiones.csv` salen las gráficas del análisis de resultados:

- cuántos frames estuvo sin ver la línea (y si llegó a `BUSCANDO`),
- cuántas veces cambió de IZQUIERDA a DERECHA por segundo (si zigzaguea, sobra ganancia o falta zona muerta),
- en qué momento reconoció cada señal y con qué área (o sea, a qué distancia),
- si hubo un PARE o un SIGA que se disparó donde no debía.

## Orden sugerido esta semana

1. Bajar los videos a `datos/originales/` y correr `uv run python tools/preparar_videos.py`.
2. Calibrar los colores con los frames (nivel 0) y verificar con los clips (nivel 1).
3. En paralelo: simulador como `ActuadorSimulador` (nivel 2), primero con la desviación del simulador y después con su vista pasando por el pipeline.
4. Integrar con la cámara del celular y repetir la calibración en el salón (nivel 3).

Un aviso: el simulador es la parte más divertida y la que menos nota da por sí sola. Vale la pena mantenerlo simple y con tiempo acotado; la nota sale de la pista.

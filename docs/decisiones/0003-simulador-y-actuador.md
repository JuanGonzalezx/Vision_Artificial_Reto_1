# 0003 — El simulador entra como actuador

- **Fecha:** 2026-09-22
- **Estado:** propuesta
- **Deciden:** Daniel (propone el simulador), Juan David (propone la interfaz)

## Contexto
Daniel está armando una simulación tipo juego para ver cómo se movería el carrito con las señales que le mandamos, antes de tener hardware. El riesgo es que el simulador termine con su propia copia de la lógica de control y después no se pueda reutilizar nada con el robot real.

## Decisión
El simulador no llama a la lógica de control: **la recibe**. Se conecta como un actuador más (`reto/actuador.py`), consumiendo la misma `Decision` que consumiría el robot. Si además dibuja la vista de la cámara, esa imagen entra por `procesar_frame` como cualquier frame y el lazo queda cerrado de punta a punta.

Para el tiempo (los segundos del PARE) se le pasa el reloj del simulador a `control.decidir(..., ahora=...)`.

## Alternativas consideradas
- Un simulador independiente con su propio control: rápido de hacer, pero lo que se valide ahí no sirve para el robot.
- Simulador en otro proceso hablando por red desde el principio: más parecido al robot real, pero con más piezas que fallan mientras todavía no tenemos ni la percepción lista.

## Consecuencias
- `control.py` no cambia cuando pasemos del simulador al carro: solo se escribe otro actuador.
- Lo que se valide en el simulador son los estados y las ganancias, no la percepción: los frames dibujados son demasiado limpios (ver `docs/flujo-de-pruebas.md`).
- Hay que acotar el tiempo que se le mete al simulador.

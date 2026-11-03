# 0005 — Cómo le hablamos al robot: pulsos a ritmo fijo

- **Fecha:** 2026-09-29
- **Estado:** propuesta (falta probarla con el robot real)
- **Deciden:** Juan David; se confirma en el laboratorio con los tres

## Contexto
El profesor publicó el código del robot. Leyendo su firmware (`arduinoFinal.ino`) aparece lo importante: los comandos son **pulsos, no estados**. Una `w` mueve el robot hacia adelante 100 ms y lo detiene sola; una `a` o una `d` giran 30 ms y paran. Además el firmware hace `delay()` dentro de cada comando, así que se queda bloqueado mientras lo ejecuta.

Eso rompe la idea intuitiva de "le mando adelante y sigue andando". Y si le mandáramos un comando por frame (30 por segundo), el buffer del puerto serie se llenaría y el robot iría ejecutando órdenes viejas.

## Decisión
`reto/actuador_robot.py` implementa el contrato de actuador que ya teníamos, con dos reglas:

1. **Ritmo fijo de 10 comandos por segundo.** La visión corre a los fps que dé la cámara; el actuador manda la última decisión al ritmo que el robot aguanta. Ajustable con `--robot-ritmo`.
2. **El giro se reparte en pulsos.** Se acumula la magnitud del giro y se manda un pulso cuando el acumulado pasa de 1; el resto del tiempo se manda `w`. Control proporcional con los pulsos disponibles.

Además: `PARAR` se manda de inmediato sin esperar el ritmo, al cerrar siempre se manda `x`, y mientras el robot busca la línea no avanza a ciegas.

Tres transportes con la misma interfaz: socket Bluetooth (Linux y Windows, como el ejemplo del profesor), puerto serie con pyserial (macOS, porque su Python no trae `AF_BLUETOOTH`) y un modo simulado que imprime los comandos.

## Alternativas consideradas
- **Un comando por frame:** es lo directo, y es justo lo que satura el enlace.
- **Mandar solo cuando cambia la decisión:** no sirve, porque los pulsos se acaban solos: si no repetimos `w`, el robot se queda quieto.
- **Modificar el firmware** para que los comandos sean estados: prohibido por el profesor.

## Consecuencias
- El control sigue igual: `control.py` no sabe que existe el robot.
- El comportamiento fino depende de una cadencia que todavía no probamos con hardware. Primer ajuste en el laboratorio: `--robot-ritmo`.
- Con velocidad fija en el firmware (150), lo único que podemos modular es la mezcla de pulsos.

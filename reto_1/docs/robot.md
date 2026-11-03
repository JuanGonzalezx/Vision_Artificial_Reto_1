# Hablarle al robot (mBot del profesor)

Todo lo de este documento sale de leer el repositorio del profesor:
<https://github.com/felipebuitragocarmona/practica-vision-artificial-robotica>

**Nosotros no tocamos el Arduino.** Solo mandamos caracteres por Bluetooth.

## Lo que hace el firmware con cada carácter

| Carácter | Qué hace | Cuánto dura |
|---|---|---|
| `w` | adelante | **100 ms y se detiene solo** |
| `s` | atrás | 100 ms y se detiene solo |
| `a` | giro a la izquierda | **30 ms** y se detiene solo |
| `d` | giro a la derecha | 30 ms y se detiene solo |
| `x` | detener | inmediato |

## El detalle que cambia el diseño

**Los comandos son pulsos, no estados.** El robot no queda andando: avanza 100 ms y para. Para que se mueva de verdad hay que mandarle `w` una y otra vez.

Además, el firmware hace `delay(100)` dentro de cada `w`, o sea que se queda bloqueado 100 ms. Si le mandamos 30 comandos por segundo (uno por frame), se llena el buffer del puerto serie y el robot termina ejecutando órdenes de hace varios segundos: iría a ciegas.

De ahí las dos reglas de `reto/actuador_robot.py`:

1. **Cadencia fija de 10 comandos por segundo** (`--robot-ritmo`). La visión sigue corriendo a los fps que dé la cámara; el actuador manda la última decisión disponible al ritmo que el robot aguanta.
2. **El giro se reparte en pulsos.** Un pulso de giro son 30 ms, un empujoncito. Se acumula la magnitud del giro y se manda un pulso cuando el acumulado pasa de 1; el resto del tiempo se manda `w`. Con giro 0.3 salen unos 3 pulsos de giro de cada 10 y 7 de avance; con giro 1.0 salen todos de giro. Es control proporcional con lo que el firmware permite.

Comprobado en seco (`--robot-simulado`):

| Decisión | Lo que sale |
|---|---|
| RECTO | `wwwwwwwwww` |
| DERECHA con giro 0.3 | `wwwdwwdwww` |
| IZQUIERDA con giro 1.0 | `aaaaaaaaaa` |
| BUSCAR | `dddddddddd` (no avanza a ciegas mientras busca) |
| PARAR | `x` de inmediato, sin esperar el ritmo |

Al cerrar el programa siempre se manda `x`, pase lo que pase.

El transporte (la clase que de verdad entrega los caracteres) vive en `reto/Robot.py` para Bluetooth (Linux y Windows) y en `reto/Robot_mac.py` para el puerto serie de macOS. `ActuadorRobot` les habla directo: traduce cada pulso a su verbo (`adelante`, `izquierda`, `parar`). Ninguna de las dos clases se modifica.

## Conectarse

### Linux o Windows

Como en el ejemplo del profesor, socket Bluetooth RFCOMM:

```bash
uv run main.py --fuente <url_camara> --robot-mac 00:1B:10:21:2C:1B
```

La MAC del robot hay que pedírsela al profesor: la del ejemplo es de otro mBot.

### macOS

⚠️ **El socket Bluetooth del ejemplo no funciona en macOS.** El módulo `socket` de Python no trae `AF_BLUETOOTH` en Darwin. Compruébalo:

```bash
python3 -c "import socket; print(hasattr(socket, 'AF_BLUETOOTH'))"
```

Si sale `False`, el camino es el puerto serie que macOS crea al emparejar el mBot:

```bash
uv add pyserial                      # una sola vez
ls /dev/tty.*                        # buscar el del robot (suele decir Makeblock)
uv run main.py --fuente <url_camara> --robot-puerto /dev/tty.Makeblock-ELETSPP
```

Son los mismos caracteres por otro transporte: el firmware no nota la diferencia. Ese camino lo implementa `reto/Robot_mac.py` (clase `RobotMac`), la versión de `Robot` para macOS: mismos verbos y mismos tiempos, solo cambia el medio.

### Sin robot

```bash
uv run main.py --fuente datos/clips/rutaIdeal/video1.mp4 --robot-simulado
```

Imprime los comandos en vez de enviarlos. Sirve para ver la mezcla de pulsos antes de tener el robot al frente.

## Checklist para el laboratorio

1. Antes de salir: correr el modo simulado sobre un clip y ver que salen `w`, giros y `x` donde corresponde.
2. Pedir la MAC del robot y, en Mac, emparejarlo y anotar el `/dev/tty.*`.
3. Primera prueba con el robot **levantado del piso**, mirando que las ruedas giren hacia donde dice el HUD.
4. Segunda prueba en la pista, con alguien listo para levantarlo.
5. Si el robot va a tirones o reacciona tarde: bajar `--robot-ritmo` a 8 o 5 antes de tocar cualquier otra cosa.
6. Si se queda corto en las curvas: `--robot-avanzar-al-girar` o subir `ganancia_giro` en la configuración.

## Lo que todavía no sabemos

- La MAC del robot que nos toque.
- Si con velocidad fija (150 en el firmware) el carro alcanza a corregir en las curvas cerradas de la pista.
- Cuánta latencia agrega el Bluetooth. Hay que medirla en el laboratorio: mandar `w` y cronometrar cuánto tarda en arrancar.
- La clase `Robot` imprime cada comando y espera 100 ms: en la pista puede volver la consola ruidosa y acoplar el paso al firmware. Vigilarlo con `--robot-mac`.

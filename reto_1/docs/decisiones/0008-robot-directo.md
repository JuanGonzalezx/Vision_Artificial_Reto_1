# 0008 — El robot se maneja con sus verbos, sin capas de por medio

- **Fecha:** 2026-09-29
- **Estado:** aceptada
- **Deciden:** Santiago

## Contexto
Hay dos clases para hablarle al mBot y comparten interfaz, con un verbo por
acción (`adelante`, `izquierda`, `parar`, ...): `Robot` (`reto/Robot.py`,
Bluetooth, Linux y Windows) y `RobotMac` (`reto/Robot_mac.py`, puerto serie,
macOS). Alrededor de ellas había crecido un protocolo de "canal"
(`abrir`/`enviar`/`cerrar`) con su adaptador y su fábrica: demasiadas capas para
una sola orden, y el adaptador traducía carácter a verbo cuando `Robot` y
`RobotMac` **ya hablan en verbos**.

## Decisión
- `ActuadorRobot` (`reto/actuador_robot.py`) recibe el robot y **le llama sus
  verbos directo** (`self.robot.adelante()`, `self.robot.parar()`, ...): reparte
  el giro en pulsos y no hay mapa de caracteres ni `getattr` de por medio.
- `RobotSimulado` imprime los comandos en vez de enviarlos (modo
  `--robot-simulado`), así el actuador siempre tiene un robot y no llena el
  código de casos "sin hardware".
- `crear_robot` elige: `--robot-puerto` → `RobotMac`, `--robot-mac` → `Robot`
  (avisa si el sistema no expone `AF_BLUETOOTH`), `--robot-simulado` →
  `RobotSimulado`.
- Se eliminan `CanalRobot` y `crear_canal`.

## Alternativas consideradas
- **Mantener el protocolo de canal:** obligaba a un adaptador que traducía
  carácter a verbo, cuando las clases del robot ya exponen los verbos.

## Consecuencias
- De la imagen a la rueda hay un solo salto: `Decision` → `ActuadorRobot` →
  `Robot`/`RobotMac`.
- `Robot` y `RobotMac` imprimen cada comando y duermen 100 ms: la consola se
  llena y el paso queda acoplado al firmware. Vigilar si estorba en la pista.
- Sigue pendiente la MAC del robot y medir la latencia real.

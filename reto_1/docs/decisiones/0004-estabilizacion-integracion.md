# 0004 — Estabilización antes de integrar con el robot

- **Fecha:** 2026-09-29
- **Estado:** aceptada
- **Deciden:** Juan David, con los cambios de Santiago ya integrados

## Contexto
Santiago avanzó la parte de cámara (streams con credenciales, reconexión, IP del celular) y subió una simulación de pista en HTML. Al traer sus commits hubo conflicto en `main.py`, porque los dos habíamos tocado el loop principal. Además el proyecto tenía dos formas de hacer lo mismo en varios sitios: dos maneras de abrir la fuente, kernels que se corregían en el pipeline en vez de validarse, e iteraciones morfológicas fijas en las señales aunque existieran en la configuración.

Con el robot real a la vista, un programa que se cae a mitad de una prueba cuesta el turno con el robot, y solo hay dos robots para siete grupos.

## Decisión
1. **Un solo `main.py`** que unifica lo de los dos: fuente por URL, archivo o índice; credenciales por CLI o variables de entorno; reconexión; `--mascaras`, `--grabar`, `--consola`, `--sin-ventana`; y cierre seguro que siempre libera cámara y actuadores.
2. **`Config` se valida a sí misma** al construirse: ROI dentro de rango y ordenadas, HSV válidos, kernels impares y positivos, tiempos y umbrales con sentido. Una calibración mala falla al arrancar con un mensaje claro, no a los diez minutos en la pista.
3. **El pipeline rechaza entradas inválidas** (frames vacíos o de un canal, ROI sin filas) en vez de reventar adentro con un error de OpenCV.
4. **Las credenciales no se imprimen** nunca: la fuente se muestra sin usuario ni contraseña.
5. **Pruebas automáticas** en `tests/`: `test_core.py` (14), `test_integracion.py` (12) y `test_herramientas.py` (13), más `tools/probar_control.py`.
6. **No se toca nada de Arduino**, como pidió el profesor.

## Consecuencias
- La evaluación da exactamente lo mismo que antes de estabilizar: 91.1% de línea detectada sobre 2341 frames, 4 saltos y 5/5 recuperaciones. Era el objetivo: ordenar sin cambiar el comportamiento.
- Hay 39 pruebas que corren en segundos y avisan si algo se rompe.
- Queda una deuda: el `linea2.jpeg` de 4 MB que entró al repo en un commit. No estorba en el árbol de trabajo, pero ya pesa en el historial.

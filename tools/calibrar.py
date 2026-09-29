"""Calibrador con trackbars: encontrar los rangos HSV y las ROI sobre los clips.

Es la forma rápida de ajustar `reto/config.py` sin editar números a ciegas:
se mueven las barras y se ve la máscara al instante (los trackbars son los
de la clase 3).

    uv run python tools/calibrar.py datos/clips/rutaIdeal/video1.mp4
    uv run python tools/calibrar.py datos/frames/rutaIdeal      # carpeta de frames
    uv run python tools/calibrar.py datos/clips/rutaIdeal/video1.mp4 -c config_pista.json

Teclas:
    1 / 2 / 3 / 4   linea / rojo alto / verde / rojo bajo
    espacio     pausar o seguir el video
    n / p       siguiente o anterior imagen (en carpeta) o salto de 10 frames
    g           guardar la calibracion en el JSON (-c, por defecto config_pista.json)
    q o Esc     salir
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reto.config import Config  # noqa: E402
from reto.pipeline import preparar  # noqa: E402

VENTANA = "Calibrador"
MODOS = {ord("1"): "linea", ord("2"): "rojo_alto", ord("3"): "verde", ord("4"): "rojo_bajo"}
EXTENSIONES_IMG = {".jpg", ".jpeg", ".png"}


def nada(_valor) -> None:
    pass


def crear_trackbars(config: Config) -> None:
    cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)

    (h1, s1, v1), (h2, s2, v2) = config.hsv_linea
    for nombre, valor, maximo in [
        ("H min", h1, 179), ("H max", h2, 179),
        ("S min", s1, 255), ("S max", s2, 255),
        ("V min", v1, 255), ("V max", v2, 255),
        ("ROI arriba %", int(config.roi_linea_lejana[0] * 100), 100),
        ("ROI abajo %", int(config.roi_linea_cercana[1] * 100), 100),
        ("Apertura", config.iteraciones_apertura, 5),
        ("Cierre", config.iteraciones_cierre, 5),
    ]:
        cv2.createTrackbar(nombre, VENTANA, valor, maximo, nada)


def leer_trackbars() -> dict:
    """Mantiene los límites de HSV y ROI válidos al mover las barras (clase 3)."""
    lee = lambda nombre: cv2.getTrackbarPos(nombre, VENTANA)  # noqa: E731
    bajo = (lee("H min"), lee("S min"), lee("V min"))
    alto = tuple(max(inferior, lee(nombre)) for inferior, nombre in
                 zip(bajo, ("H max", "S max", "V max")))
    arriba = min(lee("ROI arriba %"), 99)
    abajo = max(lee("ROI abajo %"), arriba + 1)
    poner_trackbars(bajo, alto)
    cv2.setTrackbarPos("ROI arriba %", VENTANA, arriba)
    cv2.setTrackbarPos("ROI abajo %", VENTANA, abajo)
    return {
        "bajo": bajo,
        "alto": alto,
        "roi": (arriba / 100, abajo / 100),
        "apertura": lee("Apertura"),
        "cierre": lee("Cierre"),
    }


def poner_trackbars(bajo, alto) -> None:
    for nombre, valor in zip(("H min", "S min", "V min"), bajo):
        cv2.setTrackbarPos(nombre, VENTANA, int(valor))
    for nombre, valor in zip(("H max", "S max", "V max"), alto):
        cv2.setTrackbarPos(nombre, VENTANA, int(valor))


def cargar_modo(config: Config, modo: str) -> None:
    """Carga también la ROI del modo: las señales miran una zona diferente."""
    poner_trackbars(*getattr(config, f"hsv_{modo}"))
    roi = ((min(config.roi_linea_lejana[0], config.roi_linea_cercana[0]),
            max(config.roi_linea_lejana[1], config.roi_linea_cercana[1]))
           if modo == "linea" else config.roi_senal)
    cv2.setTrackbarPos("ROI arriba %", VENTANA, round(roi[0] * 100))
    cv2.setTrackbarPos("ROI abajo %", VENTANA, round(roi[1] * 100))
    cv2.setTrackbarPos("Apertura", VENTANA, config.iteraciones_apertura)
    cv2.setTrackbarPos("Cierre", VENTANA, config.iteraciones_cierre)


def limpiar(mascara, apertura: int, cierre: int, tamano: int):
    """Apertura para quitar ruido, cierre para tapar huecos (clase 3)."""
    kernel = np.ones((tamano, tamano), np.uint8)

    if apertura:
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel, iterations=apertura)
    if cierre:
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel, iterations=cierre)

    return mascara


def vista(frame, mascara, roi, modo: str, info: str):
    """Arma: frame con la ROI dibujada | mascara | lo que queda dentro."""
    alto, ancho = frame.shape[:2]
    y1, y2 = int(alto * roi[0]), int(alto * roi[1])

    izquierda = frame.copy()
    cv2.rectangle(izquierda, (0, y1), (ancho - 1, y2 - 1), (0, 255, 255), 2)

    centro = cv2.cvtColor(mascara, cv2.COLOR_GRAY2BGR)
    derecha = cv2.bitwise_and(frame, frame, mask=mascara)

    for imagen, texto in ((izquierda, f"modo: {modo}"), (centro, info), (derecha, "resultado")):
        cv2.rectangle(imagen, (0, 0), (ancho, 26), (0, 0, 0), -1)
        cv2.putText(imagen, texto, (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 0), 1, cv2.LINE_AA)

    return np.hstack((izquierda, centro, derecha))


def configuracion_ajustada(config: Config, modo: str, valores: dict) -> Config:
    """Ajusta la ROI (clase 1) conservando la distribución de las dos franjas."""
    cambios = {f"hsv_{modo}": (valores["bajo"], valores["alto"]),
               "iteraciones_apertura": valores["apertura"],
               "iteraciones_cierre": valores["cierre"]}
    if modo == "linea":
        arriba = min(config.roi_linea_lejana[0], config.roi_linea_cercana[0])
        abajo = max(config.roi_linea_lejana[1], config.roi_linea_cercana[1])
        nuevo_arriba, nuevo_abajo = valores["roi"]
        if (nuevo_arriba, nuevo_abajo) != (arriba, abajo):
            escala = (nuevo_abajo - nuevo_arriba) / (abajo - arriba)
            for nombre in ("roi_linea_lejana", "roi_linea_cercana"):
                cambios[nombre] = tuple(nuevo_arriba + (y - arriba) * escala
                                        for y in getattr(config, nombre))
    else:
        cambios["roi_senal"] = valores["roi"]
    return replace(config, **cambios)


def guardar(config: Config, modo: str, valores: dict, ruta: Path) -> Config:
    """Valida antes de guardar; un ajuste fallido no altera la configuración."""
    candidata = configuracion_ajustada(config, modo, valores)
    candidata.guardar(ruta)
    print(f"Guardado {modo} en {ruta}")
    return candidata


def cargar_imagenes(ruta: Path):
    """Devuelve imágenes legibles o None si es video; informa entradas rotas."""
    if not ruta.is_dir():
        return None
    archivos = sorted(f for f in ruta.rglob("*")
                      if f.is_file() and f.suffix.lower() in EXTENSIONES_IMG)
    if not archivos:
        raise ValueError(f"No hay imágenes en {ruta}")
    imagenes = []
    for archivo in archivos:
        frame = cv2.imread(str(archivo))
        if frame is None:
            raise ValueError(f"No se pudo leer la imagen: {archivo}")
        imagenes.append(frame)
    return imagenes


def leer_video(captura):
    """Repite clips al terminar y falla si ni el primer frame se puede leer."""
    ok, frame = captura.read()
    if not ok or frame is None:
        captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ok, frame = captura.read()
    if not ok or frame is None:
        raise ValueError("El video no contiene frames legibles.")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrador de color y ROI.")
    parser.add_argument("fuente", help="clip .mp4 o carpeta con frames")
    parser.add_argument("-c", "--config", default="config_pista.json",
                        help="JSON donde guardar (tecla g)")
    argumentos = parser.parse_args()

    captura = None
    try:
        ruta = Path(argumentos.fuente)
        config = Config.desde_json(argumentos.config) if Path(argumentos.config).exists() else Config()
        imagenes = cargar_imagenes(ruta)
        if imagenes is None:
            captura = cv2.VideoCapture(str(ruta))
            if not captura.isOpened():
                raise ValueError(f"No se pudo abrir el video: {ruta}")
            frame = leer_video(captura)
        else:
            frame = imagenes[0]
        crear_trackbars(config)
        modo = "linea"
        cargar_modo(config, modo)
        indice = 0
        pausa = False

        while True:
            valores = leer_trackbars()
            # Misma resolución y suavizado que recibe la segmentación del robot.
            preparado = preparar(frame, config)
            hsv = cv2.cvtColor(preparado, cv2.COLOR_BGR2HSV)
            mascara = cv2.inRange(hsv, valores["bajo"], valores["alto"])
            mascara = limpiar(mascara, valores["apertura"], valores["cierre"], config.kernel_morfologico)

            alto = preparado.shape[0]
            y1, y2 = int(alto * valores["roi"][0]), int(alto * valores["roi"][1])
            mascara[:y1] = 0
            mascara[y2:] = 0
            porcentaje = 100 * np.count_nonzero(mascara) / mascara.size
            info = f"{valores['bajo']} - {valores['alto']}  ({porcentaje:.1f}% del frame)"
            cv2.imshow(VENTANA, vista(preparado, mascara, valores["roi"], modo, info))
            tecla = cv2.waitKey(30) & 0xFF

            if tecla in (ord("q"), 27):
                break
            if tecla in MODOS:
                modo = MODOS[tecla]
                cargar_modo(config, modo)
            elif tecla == ord(" "):
                pausa = not pausa
            elif tecla == ord("g"):
                try:
                    config = guardar(config, modo, valores, Path(argumentos.config))
                except (OSError, ValueError) as error:
                    print(f"No se guardó la calibración: {error}", file=sys.stderr)
            elif tecla in (ord("n"), ord("p")):
                paso = 1 if tecla == ord("n") else -1
                if imagenes is not None:
                    indice = (indice + paso) % len(imagenes)
                    frame = imagenes[indice]
                else:
                    actual = captura.get(cv2.CAP_PROP_POS_FRAMES)
                    captura.set(cv2.CAP_PROP_POS_FRAMES, max(0, actual + paso * 10))
                    frame = leer_video(captura)
                    continue
            if captura is not None and not pausa:
                frame = leer_video(captura)
    except (OSError, ValueError, cv2.error) as error:
        parser.exit(1, f"No se pudo calibrar: {error}\n")
    finally:
        if captura is not None:
            captura.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

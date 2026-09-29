"""Calibrador con trackbars: encontrar los rangos HSV y las ROI sobre los clips.

Es la forma rápida de ajustar `reto/config.py` sin editar números a ciegas:
se mueven las barras y se ve la máscara al instante (los trackbars son los
de la clase 3).

    uv run python tools/calibrar.py datos/clips/rutaIdeal/video1.mp4
    uv run python tools/calibrar.py datos/frames/rutaIdeal      # carpeta de frames
    uv run python tools/calibrar.py datos/clips/rutaIdeal/video1.mp4 -c config_pista.json

Teclas:
    1 / 2 / 3   calibrar la linea / el rojo / el verde
    espacio     pausar o seguir el video
    n / p       siguiente o anterior imagen (en carpeta) o salto de 10 frames
    g           guardar la calibracion en el JSON (-c, por defecto config_pista.json)
    q o Esc     salir
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reto.config import Config  # noqa: E402

VENTANA = "Calibrador"
MODOS = {ord("1"): "linea", ord("2"): "rojo", ord("3"): "verde"}
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
    lee = lambda nombre: cv2.getTrackbarPos(nombre, VENTANA)  # noqa: E731
    return {
        "bajo": (lee("H min"), lee("S min"), lee("V min")),
        "alto": (lee("H max"), lee("S max"), lee("V max")),
        "roi": (lee("ROI arriba %") / 100, max(lee("ROI abajo %"), lee("ROI arriba %") + 1) / 100),
        "apertura": lee("Apertura"),
        "cierre": lee("Cierre"),
    }


def poner_trackbars(bajo, alto) -> None:
    for nombre, valor in zip(("H min", "S min", "V min"), bajo):
        cv2.setTrackbarPos(nombre, VENTANA, int(valor))
    for nombre, valor in zip(("H max", "S max", "V max"), alto):
        cv2.setTrackbarPos(nombre, VENTANA, int(valor))


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


def guardar(config: Config, modo: str, valores: dict, ruta: Path) -> None:
    """Escribe en el JSON el rango del modo actual y las ROI."""
    bajo, alto = valores["bajo"], valores["alto"]

    if modo == "linea":
        config.hsv_linea = (bajo, alto)
        config.roi_linea_lejana = (valores["roi"][0], sum(valores["roi"]) / 2)
        config.roi_linea_cercana = (sum(valores["roi"]) / 2, valores["roi"][1])
    elif modo == "rojo":
        # Se guarda en el rango que corresponda segun donde quedo H.
        if bajo[0] > 90:
            config.hsv_rojo_alto = (bajo, alto)
        else:
            config.hsv_rojo_bajo = (bajo, alto)
        config.roi_senal = valores["roi"]
    else:
        config.hsv_verde = (bajo, alto)
        config.roi_senal = valores["roi"]

    config.iteraciones_apertura = valores["apertura"]
    config.iteraciones_cierre = valores["cierre"]
    config.guardar(ruta)
    print(f"Guardado {modo} en {ruta}")


def cargar_imagenes(ruta: Path):
    """Devuelve una lista de frames (carpeta de imagenes) o None si es video."""
    if ruta.is_dir():
        archivos = sorted(f for f in ruta.rglob("*") if f.suffix.lower() in EXTENSIONES_IMG)
        return [cv2.imread(str(f)) for f in archivos]
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrador de color y ROI.")
    parser.add_argument("fuente", help="clip .mp4 o carpeta con frames")
    parser.add_argument("-c", "--config", default="config_pista.json",
                        help="JSON donde guardar (tecla g)")
    argumentos = parser.parse_args()

    ruta = Path(argumentos.fuente)
    config = Config.desde_json(argumentos.config) if Path(argumentos.config).exists() else Config()

    crear_trackbars(config)
    modo = "linea"
    imagenes = cargar_imagenes(ruta)
    captura = None if imagenes is not None else cv2.VideoCapture(str(ruta))
    indice = 0
    pausa = False
    frame = imagenes[0] if imagenes else None

    while True:
        if imagenes is None and not pausa:
            ok, nuevo = captura.read()

            if not ok:  # el video se repite en bucle
                captura.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = nuevo

        valores = leer_trackbars()
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mascara = cv2.inRange(hsv, valores["bajo"], valores["alto"])
        mascara = limpiar(mascara, valores["apertura"], valores["cierre"], config.kernel_morfologico)

        # Solo cuenta lo que cae dentro de la ROI.
        alto = frame.shape[0]
        y1, y2 = int(alto * valores["roi"][0]), int(alto * valores["roi"][1])
        fuera = np.ones_like(mascara)
        fuera[y1:y2, :] = 0
        mascara[fuera == 1] = 0

        porcentaje = 100 * np.count_nonzero(mascara) / mascara.size
        info = f"{valores['bajo']} - {valores['alto']}  ({porcentaje:.1f}% del frame)"

        cv2.imshow(VENTANA, vista(frame, mascara, valores["roi"], modo, info))
        tecla = cv2.waitKey(30) & 0xFF

        if tecla in (ord("q"), 27):
            break
        elif tecla in MODOS:
            modo = MODOS[tecla]
            rangos = {
                "linea": config.hsv_linea,
                "rojo": config.hsv_rojo_alto,
                "verde": config.hsv_verde,
            }[modo]
            poner_trackbars(*rangos)
        elif tecla == ord(" "):
            pausa = not pausa
        elif tecla == ord("g"):
            guardar(config, modo, valores, Path(argumentos.config))
        elif tecla in (ord("n"), ord("p")):
            paso = 1 if tecla == ord("n") else -1

            if imagenes is not None:
                indice = (indice + paso) % len(imagenes)
                frame = imagenes[indice]
            else:
                actual = captura.get(cv2.CAP_PROP_POS_FRAMES)
                captura.set(cv2.CAP_PROP_POS_FRAMES, max(0, actual + paso * 10))

    if captura is not None:
        captura.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

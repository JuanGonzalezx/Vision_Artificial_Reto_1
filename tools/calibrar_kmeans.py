"""Calibración automática de los rangos de color con K-Means (clase 4).

Esta es la estrategia propia del equipo: en vez de teclear rangos HSV a ojo,
se le pasan unos frames de la pista real y K-Means encuentra los colores
dominantes. De cada grupo salen los percentiles de H, S y V, y de ahí los
rangos para `inRange`.

Sirve el día de la carrera: si la luz del salón no es la de los ensayos, se
toma una foto de la pista, se corre esto y en dos minutos hay rangos nuevos.

    uv run python tools/calibrar_kmeans.py datos/frames/rutaIdeal
    uv run python tools/calibrar_kmeans.py datos/clips/rutaIdeal/video1.mp4 -k 5
    uv run python tools/calibrar_kmeans.py datos/frames -o config_pista.json

Lo que imprime hay que mirarlo antes de usarlo: K-Means agrupa por color, no
sabe qué es una señal. Por eso propone y nosotros confirmamos.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reto.config import Config  # noqa: E402

EXTENSIONES_IMG = {".jpg", ".jpeg", ".png"}
EXTENSIONES_VIDEO = {".mp4", ".mov", ".avi", ".mkv"}


def cargar_frames(ruta: Path, cuantos: int) -> list:
    """Lee muestras reales de imágenes o videos y rechaza entradas ilegibles."""
    if cuantos <= 0:
        raise ValueError("La cantidad de frames debe ser mayor que cero.")
    if ruta.is_dir():
        archivos = sorted(f for f in ruta.rglob("*")
                          if f.is_file() and f.suffix.lower() in EXTENSIONES_IMG)[:cuantos]
    elif ruta.suffix.lower() in EXTENSIONES_VIDEO:
        captura = cv2.VideoCapture(str(ruta))
        try:
            if not captura.isOpened():
                raise ValueError(f"No se pudo abrir el video: {ruta}")
            cantidad = captura.get(cv2.CAP_PROP_FRAME_COUNT)
            total = int(cantidad) if math.isfinite(cantidad) and cantidad > 0 else 0
            frames = []
            for indice in range(min(cuantos, total) if total else cuantos):
                if total:
                    captura.set(cv2.CAP_PROP_POS_FRAMES,
                                int(total * (indice + 0.5) / min(cuantos, total)))
                ok, frame = captura.read()
                if not ok or frame is None:
                    raise ValueError(f"No se pudo leer una muestra del video: {ruta}")
                frames.append(frame)
            if not frames:
                raise ValueError(f"El video no contiene frames legibles: {ruta}")
            return frames
        finally:
            captura.release()
    else:
        archivos = [ruta]
    if not archivos:
        raise ValueError(f"No hay imágenes en {ruta}")
    frames = []
    for archivo in archivos:
        frame = cv2.imread(str(archivo))
        if frame is None:
            raise ValueError(f"No se pudo leer la imagen: {archivo}")
        frames.append(frame)
    return frames


def juntar_pixeles(frames: list, franja: tuple[float, float], salto: int) -> np.ndarray:
    """Apila los píxeles HSV de la franja de interés de todos los frames.

    ROI y conversión HSV (clase 1). Se recorta la franja donde está la pista (arriba del carro) y se toma
    uno de cada `salto` píxeles: con 20.000 píxeles alcanza y K-Means corre
    en un segundo.
    """
    if salto <= 0:
        raise ValueError("El salto de píxeles debe ser mayor que cero.")
    if len(franja) != 2 or not 0 <= franja[0] < franja[1] <= 1:
        raise ValueError("La franja debe cumplir 0 <= arriba < abajo <= 1.")
    trozos = []

    for frame in frames:
        if frame is None:
            raise ValueError("Se recibió un frame ilegible.")

        alto = frame.shape[0]
        recorte = frame[int(alto * franja[0]):int(alto * franja[1])]
        if recorte.size == 0:
            raise ValueError("La franja es demasiado pequeña para la altura del frame.")
        hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
        trozos.append(hsv.reshape(-1, 3)[::salto])

    if not trozos:
        raise ValueError("No pude leer ningún frame de esa ruta.")

    return np.vstack(trozos)


def agrupar(pixeles: np.ndarray, k: int) -> list[dict]:
    """K-Means sobre los píxeles y percentiles reales de cada grupo.

    K-Means (clase 4). El centroide dice el color promedio; los percentiles 5 y 95 de cada
    canal son los que sirven como rango para inRange, porque el promedio
    solo no dice qué tan disperso está el grupo.
    """
    if k <= 0 or k > len(pixeles):
        raise ValueError("K debe ser positivo y no superar la cantidad de píxeles muestreados.")
    modelo = KMeans(n_clusters=k, random_state=42, n_init=10)
    etiquetas = modelo.fit_predict(pixeles.astype(np.float32))
    grupos = []

    for indice, centro in enumerate(modelo.cluster_centers_):
        del centro
        miembros = pixeles[etiquetas == indice]

        if len(miembros) == 0:
            continue

        bajo = np.percentile(miembros, 5, axis=0).astype(int)
        alto = np.percentile(miembros, 95, axis=0).astype(int)

        grupos.append({
            "h": int(np.median(miembros[:, 0])),
            "s": int(np.median(miembros[:, 1])),
            "v": int(np.median(miembros[:, 2])),
            "bajo": tuple(int(x) for x in bajo),
            "alto": tuple(int(x) for x in alto),
            "porcentaje": 100 * len(miembros) / len(pixeles),
        })

    return sorted(grupos, key=lambda g: -g["porcentaje"])


def clasificar(grupos: list[dict]) -> dict:
    """Le pone nombre a cada grupo: piso, línea, rojo o verde.

    Son reglas simples y explicables: el piso es el grupo claro más grande,
    la línea es el más oscuro, y las señales son grupos saturados con el
    tono del rojo o del verde.
    """
    nombres: dict[str, dict] = {}
    candidatos_piso = [g for g in grupos if g["v"] > 120 and g["s"] < 80]

    if candidatos_piso:
        nombres["piso"] = max(candidatos_piso, key=lambda g: g["porcentaje"])

    nombres["linea"] = min(grupos, key=lambda g: g["v"])

    for grupo in grupos:
        if grupo["s"] < 90 or grupo["v"] < 50:
            continue

        es_rojo = grupo["h"] <= 10 or grupo["h"] >= 160
        es_verde = 45 <= grupo["h"] <= 90

        if es_rojo and "rojo" not in nombres:
            nombres["rojo"] = grupo
        elif es_verde and "verde" not in nombres:
            nombres["verde"] = grupo

    return nombres


def con_margen(grupo: dict, margen_h: int = 8, minimo_s: int = 80, minimo_v: int = 60):
    """Convierte el grupo en un rango de inRange, con algo de margen en H.

    Para las señales se dejan S y V amplios a propósito: lo que identifica
    la señal es el tono, y S y V son los que más se mueven con la luz.
    """
    h_bajo = max(0, grupo["h"] - margen_h)
    h_alto = min(179, grupo["h"] + margen_h)
    return (h_bajo, minimo_s, minimo_v), (h_alto, 255, 255)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibra los rangos de color con K-Means.")
    parser.add_argument("fuente", help="carpeta de frames, un video o una imagen")
    parser.add_argument("-k", type=int, default=5, help="numero de grupos de color")
    parser.add_argument("--frames", type=int, default=8, help="cuantos frames usar")
    parser.add_argument("--salto", type=int, default=4, help="toma 1 de cada N pixeles")
    parser.add_argument("-c", "--config", default=None,
                        help="JSON base: conserva ROI y los demás parámetros calibrados")
    parser.add_argument("-o", "--salida", default=None,
                        help="escribe un JSON de calibracion con lo propuesto")
    parser.add_argument("--franja", type=float, nargs=2, default=None,
                        help="franja del frame a mirar, en fracciones (por defecto la de la pista)")
    argumentos = parser.parse_args()

    try:
        config = Config.desde_json(argumentos.config) if argumentos.config else Config()
        franja = tuple(argumentos.franja) if argumentos.franja else config.roi_senal
        frames = cargar_frames(Path(argumentos.fuente), argumentos.frames)
        pixeles = juntar_pixeles(frames, franja, argumentos.salto)
        grupos = agrupar(pixeles, argumentos.k)
        nombres = clasificar(grupos)
    except (OSError, ValueError, cv2.error) as error:
        parser.exit(1, f"No se pudo calibrar: {error}\n")

    print(f"{len(frames)} frames, {len(pixeles)} pixeles, franja {franja[0]:.2f}-{franja[1]:.2f}\n")
    print(f"{'grupo':>7}  {'H':>4} {'S':>4} {'V':>4}  {'% pixeles':>9}  rango medido (H,S,V)")

    etiquetas = {id(g): nombre for nombre, g in nombres.items()}

    for grupo in grupos:
        nombre = etiquetas.get(id(grupo), "-")
        print(f"{nombre:>7}  {grupo['h']:>4} {grupo['s']:>4} {grupo['v']:>4}  "
              f"{grupo['porcentaje']:>8.1f}%  {grupo['bajo']} - {grupo['alto']}")

    print("\nPropuesta:")

    if "linea" in nombres:
        linea = nombres["linea"]
        tope_v = min(255, int(linea["alto"][2]) + 20)
        tope_s = min(255, int(linea["alto"][1]) + 30)
        config.hsv_linea = ((0, 0, 0), (179, tope_s, tope_v))
        print(f"  hsv_linea = {config.hsv_linea}   (la linea es lo mas oscuro: V hasta {tope_v})")

    if "rojo" in nombres:
        bajo, alto = con_margen(nombres["rojo"])

        if nombres["rojo"]["h"] >= 160:
            config.hsv_rojo_alto = (bajo, alto)
            print(f"  hsv_rojo_alto = {config.hsv_rojo_alto}   (el rojo cayo en el extremo alto de H)")
        else:
            config.hsv_rojo_bajo = (bajo, alto)
            print(f"  hsv_rojo_bajo = {config.hsv_rojo_bajo}")
    else:
        print("  rojo: no aparecio ningun grupo rojo (no habia senal en estos frames)")

    if "verde" in nombres:
        config.hsv_verde = con_margen(nombres["verde"])
        print(f"  hsv_verde = {config.hsv_verde}")
    else:
        print("  verde: no aparecio ningun grupo verde en estos frames")

    if "piso" in nombres and "linea" in nombres:
        separacion = nombres["piso"]["v"] - nombres["linea"]["v"]
        print(f"\n  Separacion piso/linea en V: {separacion} niveles. "
              f"{'Buena.' if separacion > 60 else 'Justa: cuidado con las sombras.'}")

    if argumentos.salida:
        try:
            config.guardar(argumentos.salida)
        except (OSError, ValueError) as error:
            parser.exit(1, f"No se pudo guardar la calibración: {error}\n")
        print(f"\nEscrito {argumentos.salida}. Verificalo con:"
              f"\n  uv run python tools/evaluar.py --config {argumentos.salida}")
    else:
        print("\n(Con -o config_pista.json queda escrito en un JSON.)")


if __name__ == "__main__":
    main()

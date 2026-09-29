"""Calibra los rangos HSV con K-Means a partir de frames reales.

    uv run python tools/calibrar.py --fuente vid/video1.mp4 --frame 60 --frame 620
    uv run python tools/calibrar.py --fuente vid/video1.mp4 --frame 60 --frame 620 \\
        --linea 2 --rojo 4 --verde 1 --salida configs/video1-kmeans.json

Pasos (K-Means básico, clase 4; HSV, clase 1):
  1. Toma los frames indicados, los prepara igual que el pipeline y se queda con
     la zona sin el chasis del robot (de arriba hasta `roi_senal`).
  2. Agrupa los píxeles (H, S, V) en K clusters con sklearn.cluster.KMeans.
  3. Muestra los clusters numerados; la persona dice cuál es la línea, el rojo y el verde.
  4. Para cada uno, rango = media ± N desviaciones estándar por canal, y lo guarda
     en un JSON que `main.py --config` entiende.

Si no se pasan --linea / --rojo / --verde, los pregunta por consola.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reto.config import Config  # noqa: E402
from reto.overlay import franja_a_pixeles  # noqa: E402
from reto.pipeline import preparar  # noqa: E402

VIDEO_POR_DEFECTO = "vid/video1.mp4"
K_POR_DEFECTO = 6
SIGMAS_POR_DEFECTO = 2.5      # ancho del rango: media ± N desviaciones
MUESTRA_POR_FRAME = 30000     # píxeles por frame que entran a K-Means (velocidad)
SEMILLA = 0                   # resultados repetibles
MEDIO_CIRCULO_H = 90          # para desplazar el tono y tratar el rojo sin cortes
MAX_H = 179


def leer_frame(fuente: str, numero: int):
    """Frame `numero` del video (o la imagen, si la fuente es una imagen)."""
    imagen = cv2.imread(fuente)

    if imagen is not None:
        return imagen

    captura = cv2.VideoCapture(fuente)
    captura.set(cv2.CAP_PROP_POS_FRAMES, numero)
    ok, frame = captura.read()
    captura.release()

    if not ok:
        raise SystemExit(f"No se pudo leer el frame {numero} de {fuente}")

    return frame


def pixeles_hsv(frames: list, config: Config) -> np.ndarray:
    """Píxeles (H, S, V) de la zona sin chasis de cada frame, ya preparados."""
    generador = np.random.default_rng(SEMILLA)
    muestras = []

    for frame in frames:
        preparado = preparar(frame, config)
        y1, y2 = franja_a_pixeles(preparado.shape[0], (0.0, config.roi_senal[1]))
        hsv = cv2.cvtColor(preparado[y1:y2], cv2.COLOR_BGR2HSV).reshape(-1, 3)
        elegidos = generador.choice(len(hsv), min(MUESTRA_POR_FRAME, len(hsv)), replace=False)
        muestras.append(hsv[elegidos])

    return np.vstack(muestras)


def agrupar(pixeles: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """K-Means sobre los píxeles: etiqueta de cada uno y centro de cada cluster."""
    modelo = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(pixeles.astype(np.float32))
    return modelo.labels_, modelo.cluster_centers_


def rango_de_cluster(miembros: np.ndarray, sigmas: float) -> tuple[list[int], list[int]]:
    """Rango (bajo, alto) = media ± sigmas · desviación, canal por canal."""
    media, desviacion = miembros.mean(axis=0), miembros.std(axis=0)
    bajo = np.clip(media - sigmas * desviacion, 0, [MAX_H, 255, 255])
    alto = np.clip(media + sigmas * desviacion, 0, [MAX_H, 255, 255])
    return [int(v) for v in bajo], [int(v) for v in alto]


def rangos_de_rojo(miembros: np.ndarray, sigmas: float) -> tuple[tuple, tuple]:
    """Rojo: el tono da la vuelta en 0/179, así que puede salir en dos rangos.

    Se desplaza H medio círculo para que el rojo quede continuo, se calcula el
    rango ahí y se vuelve. Si cruza el borde, se parte en (bajo, ..179) y (0.., alto).
    Devuelve (rojo_bajo, rojo_alto) como los espera Config.
    """
    vuelta = MAX_H + 1
    desplazados = miembros.copy()
    desplazados[:, 0] = (desplazados[:, 0].astype(int) + MEDIO_CIRCULO_H) % vuelta
    bajo, alto = rango_de_cluster(desplazados, sigmas)
    h1, h2 = bajo[0] + MEDIO_CIRCULO_H, alto[0] + MEDIO_CIRCULO_H

    def rango(a: int, b: int) -> tuple:
        return ((a, bajo[1], bajo[2]), (b, alto[1], alto[2]))

    if h1 >= vuelta:  # todo el rango quedó del otro lado del borde
        h1, h2 = h1 - vuelta, h2 - vuelta

    if h2 >= vuelta:  # cruza por 0
        return rango(0, h2 - vuelta), rango(h1, MAX_H)

    return rango(h1, h2), rango(h1, h2)


def guardar_parches(centros: np.ndarray, cantidades: np.ndarray, ruta: str) -> None:
    """Imagen con un parche de color por cluster, numerado, para elegir."""
    ancho_parche, alto_parche = 110, 90
    lienzo = np.zeros((alto_parche, ancho_parche * len(centros), 3), np.uint8)

    for i, centro in enumerate(centros):
        parche = np.full((alto_parche, ancho_parche, 3), centro.astype(np.uint8))
        bgr = cv2.cvtColor(parche, cv2.COLOR_HSV2BGR)
        cv2.putText(bgr, f"#{i}", (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.putText(bgr, f"{cantidades[i]}px", (8, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(bgr, "HSV " + "/".join(str(int(v)) for v in centro), (8, 78),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)
        lienzo[:, i * ancho_parche:(i + 1) * ancho_parche] = bgr

    cv2.imwrite(ruta, lienzo)


def elegir(nombre: str, indices: str | int | None, k: int) -> list[int]:
    """Índices de cluster, tomados del argumento o preguntados por consola."""
    while True:
        texto = str(indices) if indices is not None else input(f"¿Qué cluster(s) es {nombre}? (0-{k - 1}, coma para varios): ")
        try:
            lista = [int(t) for t in texto.split(",")]
        except ValueError:
            lista = []
        if lista and all(0 <= i < k for i in lista):
            return lista
        indices = None


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Calibración HSV con K-Means.")
    parser.add_argument("--fuente", "-f", default=VIDEO_POR_DEFECTO, help="Video o imagen.")
    parser.add_argument("--frame", type=int, action="append", help="Frame a usar; repetible.")
    parser.add_argument("--k", type=int, default=K_POR_DEFECTO)
    parser.add_argument("--sigmas", type=float, default=SIGMAS_POR_DEFECTO)
    parser.add_argument("--linea", help="Índice(s) del cluster de la línea, separados por coma (la línea puede ocupar varios).")
    parser.add_argument("--rojo", type=int, help="Índice del cluster rojo.")
    parser.add_argument("--verde", type=int, help="Índice del cluster verde.")
    parser.add_argument("--salida", default="configs/calibracion.json")
    parser.add_argument("--parches", default="temp/parches.png", help="Imagen con los clusters.")
    argumentos = parser.parse_args()

    config = Config()
    numeros = argumentos.frame or [0]
    frames = [leer_frame(argumentos.fuente, n) for n in numeros]
    pixeles = pixeles_hsv(frames, config)
    etiquetas, centros = agrupar(pixeles, argumentos.k)
    cantidades = np.bincount(etiquetas, minlength=argumentos.k)

    Path(argumentos.parches).parent.mkdir(parents=True, exist_ok=True)
    guardar_parches(centros, cantidades, argumentos.parches)
    print(f"Clusters (HSV medio) — imagen en {argumentos.parches}")
    for i, centro in enumerate(centros):
        print(f"  #{i}: HSV {centro.round().astype(int).tolist()}  {cantidades[i]} px")

    if argumentos.linea is None or argumentos.rojo is None or argumentos.verde is None:
        cv2.imshow("Clusters", cv2.imread(argumentos.parches))
        cv2.waitKey(1)

    linea = elegir("la línea", argumentos.linea, argumentos.k)
    rojo = elegir("el rojo", argumentos.rojo, argumentos.k)
    verde = elegir("el verde", argumentos.verde, argumentos.k)

    def miembros(indices: list[int]) -> np.ndarray:
        return pixeles[np.isin(etiquetas, indices)]

    l_bajo, l_alto = rango_de_cluster(miembros(linea), argumentos.sigmas)
    v_bajo, v_alto = rango_de_cluster(miembros(verde), argumentos.sigmas)
    rojo_bajo, rojo_alto = rangos_de_rojo(miembros(rojo), argumentos.sigmas)

    nueva = replace(
        config,
        hsv_linea=(tuple(l_bajo), tuple(l_alto)),
        hsv_verde=(tuple(v_bajo), tuple(v_alto)),
        hsv_rojo_bajo=rojo_bajo,
        hsv_rojo_alto=rojo_alto,
    )
    Path(argumentos.salida).parent.mkdir(parents=True, exist_ok=True)
    nueva.guardar(argumentos.salida)
    print(f"\nlínea {nueva.hsv_linea}\nverde {nueva.hsv_verde}\n"
          f"rojo  {nueva.hsv_rojo_bajo} + {nueva.hsv_rojo_alto}\nGuardado en {argumentos.salida}")


if __name__ == "__main__":
    main()

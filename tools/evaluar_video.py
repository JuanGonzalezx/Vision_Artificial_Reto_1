"""Evalúa el pipeline sobre un video sin abrir ventanas y reporta métricas.

    uv run python tools/evaluar_video.py [video] [--config json] [--csv salida.csv]

Sin argumentos usa vid/video1.mp4. El reloj del control se simula con el
número de frame (frame / fps), así el resultado no depende de qué tan rápido
corra el computador. Sirve para comprobar los criterios de aceptación del
plan (docs/plan-reto.md, sección 5) y RNF-01 (ms por frame).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reto.config import Config  # noqa: E402
from reto.control import confirmar_senal  # noqa: E402
from reto.pipeline import procesar_frame  # noqa: E402
from reto.tipos import Estado  # noqa: E402

VIDEO_POR_DEFECTO = "vid/video1.mp4"
COLUMNAS_CSV = ["t", "frame", "fps", "estado", "accion", "giro", "desviacion",
                "linea_detectada", "senal", "area_senal"]
FPS_SIN_DATO = 30.0
MAX_BUSCANDO_SEGUIDO = 10  # CP-01: no más de estos frames seguidos en BUSCANDO


def rangos_de_frames(frames: list[int]) -> list[tuple[int, int]]:
    """Agrupa frames consecutivos: [3,4,5,9] -> [(3,5),(9,9)]."""
    rangos: list[tuple[int, int]] = []

    for f in frames:
        if rangos and f == rangos[-1][1] + 1:
            rangos[-1] = (rangos[-1][0], f)
        else:
            rangos.append((f, f))

    return rangos


def formatear_rangos(rangos: list[tuple[int, int]]) -> str:
    if not rangos:
        return "ninguno"
    return ", ".join(f"{a}-{b}" for a, b in rangos)


def porcentaje_en_rango(frames: set[int], desde: int, hasta: int) -> float:
    total = hasta - desde + 1
    return 100 * sum(1 for f in range(desde, hasta + 1) if f in frames) / total


def evaluar(video: str, config: Config, ruta_csv: str | None) -> dict:
    captura = cv2.VideoCapture(video)

    if not captura.isOpened():
        raise SystemExit(f"No se pudo abrir el video: {video}")

    fps_video = captura.get(cv2.CAP_PROP_FPS) or FPS_SIN_DATO
    estado = Estado()
    estado_sombra = Estado()  # solo para saber cuándo se confirma cada señal

    con_linea: set[int] = set()
    crudas = {"PARE": [], "SIGA": []}
    confirmadas = {"PARE": [], "SIGA": []}
    cambios_estado: list[tuple[int, str]] = []
    desviaciones: list[float] = []
    tiempos_ms: list[float] = []
    saltos: list[tuple[float, int]] = []
    buscando_seguido = 0
    max_buscando = 0
    estado_previo = None

    archivo = open(ruta_csv, "w", newline="", encoding="utf8") if ruta_csv else None
    escritor = csv.writer(archivo) if archivo else None
    if escritor:
        escritor.writerow(COLUMNAS_CSV)

    numero = 0
    try:
        while True:
            ok, frame = captura.read()
            if not ok:
                break

            t = numero / fps_video
            inicio = time.perf_counter()
            decision, dep = procesar_frame(frame, estado, config, ahora=t)
            ms = (time.perf_counter() - inicio) * 1000
            tiempos_ms.append(ms)

            linea, senal = dep["linea"], dep["senal"]

            if linea.detectada:
                con_linea.add(numero)
                if desviaciones:
                    saltos.append((abs(linea.desviacion - desviaciones[-1]), numero))
                desviaciones.append(linea.desviacion)

            if senal.tipo in crudas:
                crudas[senal.tipo].append(numero)

            confirmada = confirmar_senal(estado_sombra, senal, config)
            if confirmada in confirmadas:
                confirmadas[confirmada].append(numero)

            if estado.estado != estado_previo:
                cambios_estado.append((numero, estado.estado.value))
                estado_previo = estado.estado

            buscando_seguido = buscando_seguido + 1 if decision.accion.value == "BUSCAR" else 0
            max_buscando = max(max_buscando, buscando_seguido)

            if escritor:
                escritor.writerow([
                    f"{t:.3f}", numero, f"{1000 / ms:.1f}" if ms else "", estado.estado.value,
                    decision.accion.value, f"{decision.giro:.3f}", f"{linea.desviacion:.3f}",
                    int(linea.detectada), senal.tipo or "", f"{senal.area:.0f}",
                ])

            numero += 1
    finally:
        captura.release()
        if archivo:
            archivo.close()

    return {
        "total": numero, "fps_video": fps_video, "con_linea": con_linea, "crudas": crudas,
        "confirmadas": confirmadas, "cambios_estado": cambios_estado, "tiempos_ms": tiempos_ms,
        "saltos": saltos, "max_buscando": max_buscando,
    }


def imprimir_reporte(video: str, r: dict) -> None:
    total = r["total"]
    if total == 0:
        print("El video no tiene frames.")
        return

    ms = sorted(r["tiempos_ms"])
    salto_max, frame_salto = max(r["saltos"], default=(0.0, 0))

    print(f"Video: {video}  ({total} frames, {r['fps_video']:.1f} FPS)")
    print(f"Línea detectada:   {100 * len(r['con_linea']) / total:5.1f} %   (meta RF-05: >= 95 %)")
    print(f"Salto máx. desviación entre frames: {salto_max:.2f} en el frame {frame_salto}   (meta: <= 0.3; <= 0.6 en la cinta transversal, frames ~106-125)")
    print(f"Máx. frames seguidos en BUSCAR: {r['max_buscando']}   (meta CP-01: <= {MAX_BUSCANDO_SEGUIDO})")

    for tipo in ("PARE", "SIGA"):
        print(f"{tipo}: candidata en {formatear_rangos(rangos_de_frames(r['crudas'][tipo]))}")
        print(f"{tipo}: confirmada en {formatear_rangos(rangos_de_frames(r['confirmadas'][tipo]))}")

    cambios = ", ".join(f"{f}:{e}" for f, e in r["cambios_estado"])
    print(f"Cambios de estado: {cambios}")
    print(f"Tiempo por frame: media {sum(ms) / len(ms):.1f} ms · p95 {ms[int(0.95 * (len(ms) - 1))]:.1f} ms "
          f"· máx {ms[-1]:.1f} ms   (meta RNF-01: <= 25 ms)")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # tildes en la consola de Windows
    parser = argparse.ArgumentParser(description="Métricas del pipeline sobre un video.")
    parser.add_argument("video", nargs="?", default=VIDEO_POR_DEFECTO)
    parser.add_argument("--config", "-c", default=None, help="JSON de calibración.")
    parser.add_argument("--csv", default=None, help="Escribe el registro por frame en este CSV.")
    argumentos = parser.parse_args()

    config = Config.desde_json(argumentos.config) if argumentos.config else Config()
    imprimir_reporte(argumentos.video, evaluar(argumentos.video, config, argumentos.csv))


if __name__ == "__main__":
    main()

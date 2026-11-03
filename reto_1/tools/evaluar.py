"""Corre el pipeline sobre todos los clips y saca números comparables.

Sirve para tres cosas: saber si un cambio mejoró o empeoró (en vez de "me
pareció que iba mejor"), tener evidencia para la sustentación, y verificar
automáticamente que el robot busca la línea hacia el lado correcto en los
videos de descarrilamiento del profesor (el nombre del archivo dice hacia
dónde se fue la línea).

    uv run python tools/evaluar.py
    uv run python tools/evaluar.py --config config_pista.json
    uv run python tools/evaluar.py --carpeta datos/clips/rutaIdeal

Usa el tiempo del video como reloj, así que el resultado es el mismo en
cualquier computador, sin depender de los FPS de cada máquina.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reto.config import Config  # noqa: E402
from reto.pipeline import procesar_frame  # noqa: E402
from reto.tipos import Accion, Estado  # noqa: E402

COLUMNAS = ["clip", "frames", "duracion_s", "linea_%", "desviacion_media", "saltos_por_s",
            "zigzag_por_s", "curva_%", "pare", "siga", "area_max_senal", "busca_izq",
            "busca_der", "fps_proceso"]

# Un salto de desviación más grande que esto entre dos frames seguidos no lo
# puede producir el carro moviéndose: es que la detección se fue a otra cosa
# (una sombra, una rueda). Sirve para cazar "mejoras" que en realidad empeoran.
SALTO_SOSPECHOSO = 0.35


def evaluar_clip(ruta: Path, config: Config) -> dict:
    captura = cv2.VideoCapture(str(ruta))
    if not captura.isOpened():
        captura.release()
        raise ValueError(f"No se pudo abrir el clip: {ruta}")
    fps_video = captura.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(fps_video) or fps_video <= 0:
        captura.release()
        raise ValueError(f"El clip no tiene FPS válidos para evaluarlo: {ruta}")
    estado = Estado()

    frames = con_linea = cambios_de_giro = saltos = 0
    pare = siga = busca_izq = busca_der = en_curva = 0
    suma_desviacion = 0.0
    desviacion_anterior = None
    area_max = 0.0
    accion_anterior = None
    inicio = time.monotonic()

    try:
        while True:
            ok, frame = captura.read()

            if not ok:
                break

            # Reloj del video: hace la evaluación determinista.
            decision, depuracion = procesar_frame(frame, estado, config, ahora=frames / fps_video)
            linea = depuracion["linea"]
            senal = depuracion["senal"]

            frames += 1

            if linea.detectada:
                con_linea += 1
                suma_desviacion += abs(linea.desviacion)

                if desviacion_anterior is not None and \
                        abs(linea.desviacion - desviacion_anterior) > SALTO_SOSPECHOSO:
                    saltos += 1

                desviacion_anterior = linea.desviacion
            else:
                desviacion_anterior = None

            if senal.tipo == "PARE":
                pare += 1
            elif senal.tipo == "SIGA":
                siga += 1

            area_max = max(area_max, senal.area)

            # Frames en que el actuador frenaría: sirve para calibrar los umbrales
            # de curva (si da casi 100 %, el robot va lento en todo el recorrido).
            if decision.en_curva:
                en_curva += 1

            if decision.accion is Accion.BUSCAR:
                if decision.giro < 0:
                    busca_izq += 1
                else:
                    busca_der += 1

            giros = (Accion.IZQUIERDA, Accion.DERECHA)

            if accion_anterior in giros and decision.accion in giros and \
                    decision.accion is not accion_anterior:
                cambios_de_giro += 1

            accion_anterior = decision.accion

    finally:
        captura.release()

    if not frames:
        raise ValueError(f"El clip no contiene frames legibles: {ruta}")
    duracion = frames / fps_video if frames else 0.0

    return {
        # Contadores sin redondear: los resúmenes nunca se reconstruyen del CSV.
        "_con_linea": con_linea,
        "_saltos": saltos,
        "_cambios_de_giro": cambios_de_giro,
        "_suma_desviacion": suma_desviacion,
        "_duracion": duracion,
        "clip": str(ruta),
        "frames": frames,
        "duracion_s": round(duracion, 1),
        "linea_%": round(100 * con_linea / frames, 1) if frames else 0.0,
        "desviacion_media": round(suma_desviacion / con_linea, 3) if con_linea else 0.0,
        "saltos_por_s": round(saltos / duracion, 2) if duracion else 0.0,
        "zigzag_por_s": round(cambios_de_giro / duracion, 2) if duracion else 0.0,
        "curva_%": round(100 * en_curva / frames, 1) if frames else 0.0,
        "pare": pare,
        "siga": siga,
        "area_max_senal": round(area_max),
        "busca_izq": busca_izq,
        "busca_der": busca_der,
        "fps_proceso": round(frames / (time.monotonic() - inicio), 1) if frames else 0.0,
    }


def resumir(filas: list[dict]) -> dict:
    """Agrega contadores exactos; la desviación solo promedia frames con línea."""
    total = sum(f["frames"] for f in filas)
    con_linea = sum(f["_con_linea"] for f in filas)
    duracion = sum(f["_duracion"] for f in filas)
    if total <= 0 or duracion <= 0:
        raise ValueError("No hay frames evaluados para calcular un resumen.")
    return {
        "frames": total,
        "linea_%": 100 * con_linea / total,
        "saltos": sum(f["_saltos"] for f in filas),
        "zigzag_por_s": sum(f["_cambios_de_giro"] for f in filas) / duracion,
        "desviacion_media": (sum(f["_suma_desviacion"] for f in filas) / con_linea
                             if con_linea else 0.0),
    }


def buscar_clips(carpeta: str | Path) -> list[Path]:
    """Busca MP4 recursivamente, también si la extensión está en mayúsculas."""
    return sorted(p for p in Path(carpeta).rglob("*")
                  if p.is_file() and p.suffix.lower() == ".mp4")


def revisar_lado_de_busqueda(filas: list[dict]) -> list[str]:
    """Los clips de descarrilamiento dicen en el nombre hacia dónde se fue la línea.

    Es una prueba automática sobre datos reales: si el robot busca hacia el
    otro lado, el nombre del archivo nos delata el error.
    """
    resultados = []

    for fila in filas:
        nombre = Path(fila["clip"]).name.lower()

        if "izquierda" in nombre:
            esperado, contrario = fila["busca_izq"], fila["busca_der"]
            lado = "izquierda"
        elif "derecha" in nombre:
            esperado, contrario = fila["busca_der"], fila["busca_izq"]
            lado = "derecha"
        else:
            continue

        if esperado == 0 and contrario == 0:
            resultados.append(f"  ?  {Path(fila['clip']).name}: nunca entro a BUSCAR")
        elif esperado > contrario:
            resultados.append(f"  OK {Path(fila['clip']).name}: busca hacia la {lado} "
                              f"({esperado} frames contra {contrario})")
        else:
            resultados.append(f"  FALLA {Path(fila['clip']).name}: deberia buscar hacia la "
                              f"{lado} y busca al otro lado ({esperado} contra {contrario})")

    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua el pipeline sobre los clips.")
    parser.add_argument("--carpeta", default="datos/clips", help="carpeta con los clips")
    parser.add_argument("--config", default=None, help="JSON de calibracion")
    parser.add_argument("--salida", default="datos/grabaciones/evaluacion.csv")
    argumentos = parser.parse_args()

    try:
        config = Config.desde_json(argumentos.config) if argumentos.config else Config()
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error de configuración: {error}\n")
    clips = buscar_clips(argumentos.carpeta)

    if not clips:
        sys.exit(f"No hay clips en {argumentos.carpeta}/. Corre antes tools/preparar_videos.py")

    try:
        filas = [evaluar_clip(clip, config) for clip in clips]
    except (ValueError, cv2.error) as error:
        parser.exit(1, f"Evaluación incompleta: {error}\n")
    anchos = {c: max(len(c), *(len(str(f[c])) for f in filas)) for c in COLUMNAS}

    print("  ".join(c.ljust(anchos[c]) for c in COLUMNAS))
    for fila in filas:
        print("  ".join(str(fila[c]).ljust(anchos[c]) for c in COLUMNAS))

    resumen = resumir(filas)
    print(f"\nLinea detectada en {resumen['linea_%']:.1f}% de {resumen['frames']} frames "
          f"({len(filas)} clips), con {resumen['saltos']} saltos sospechosos de deteccion")
    print("Ojo: un % mas alto con mas saltos suele ser peor, no mejor: la mascara "
          "se esta yendo a una sombra.")

    revision = revisar_lado_de_busqueda(filas)

    if revision:
        print("\nRecuperacion de la linea (el nombre del clip dice el lado correcto):")
        print("\n".join(revision))

    salida = Path(argumentos.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)

    with salida.open("w", newline="", encoding="utf8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"\nGuardado en {salida}")


if __name__ == "__main__":
    main()

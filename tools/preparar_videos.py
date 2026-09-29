"""Deja los videos de ensayo listos para el repo: clips livianos + frames.

Los videos del profesor pesan ~4 MB cada uno y son 8. Al repo no entran así:
git guarda cada versión para siempre. Lo que sí entra es

- un clip recomprimido (mismo contenido, mucho menos peso) para probar el
  pipeline completo, y
- unos pocos frames sueltos en JPG, que es lo que de verdad se usa para
  calibrar colores (calibrar es mirar un frame, no un video).

Los originales se quedan en datos/originales/, que está en .gitignore. Las
subcarpetas (rutaIdeal, desacarrilamiento, ...) se conservan en la salida,
porque dicen qué caso de prueba es cada video.

Uso:
    uv run python tools/preparar_videos.py                  # procesa datos/originales/ (con subcarpetas)
    uv run python tools/preparar_videos.py --ancho 480 --calidad 32 --frames 6

Necesita ffmpeg (viene con: brew install ffmpeg).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ORIGINALES = RAIZ / "datos" / "originales"
CLIPS = RAIZ / "datos" / "clips"
FRAMES = RAIZ / "datos" / "frames"
EXTENSIONES = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}


def mb(ruta: Path) -> float:
    return ruta.stat().st_size / 1_000_000


def comprimir(origen: Path, destino: Path, ancho: int, calidad: int, fps: int) -> None:
    """Recomprime con H.264: reescala, baja los fps y quita el audio.

    `calidad` es el CRF de x264: más alto = más comprimido y más feo.
    28-32 se ve bien para calibrar; el color, que es lo que nos importa,
    casi no se toca.
    """
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(origen),
            # min(iw, ancho): nunca agranda un video que ya es pequeño
            "-vf", f"scale='min(iw,{ancho})':-2",
            "-r", str(fps),
            "-c:v", "libx264", "-crf", str(calidad), "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-an",
            str(destino),
        ],
        check=True,
    )


def extraer_frames(origen: Path, carpeta: Path, cantidad: int, ancho: int) -> int:
    """Guarda `cantidad` frames repartidos a lo largo del video.

    Se reparten en el tiempo para tener luces y curvas distintas, no diez
    fotos del mismo pedazo de pista.
    """
    duracion = duracion_segundos(origen)

    if duracion <= 0:
        return 0

    guardados = 0

    for indice in range(cantidad):
        # Se evita el primer y el último instante: suelen estar movidos.
        momento = duracion * (indice + 0.5) / cantidad
        salida = carpeta / f"{origen.stem}_{indice:02d}.jpg"

        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-ss", f"{momento:.2f}",
                "-i", str(origen),
                "-frames:v", "1",
                "-vf", f"scale='min(iw,{ancho})':-2",
                "-q:v", "3",
                str(salida),
            ],
            check=True,
        )
        guardados += 1

    return guardados


def duracion_segundos(video: Path) -> float:
    salida = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        capture_output=True, text=True, check=True,
    )
    try:
        return float(salida.stdout.strip())
    except ValueError:
        return 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ancho", type=int, default=640,
                        help="ancho maximo de salida en pixeles (nunca agranda)")
    parser.add_argument("--calidad", type=int, default=30, help="CRF de x264: mas alto, mas comprimido")
    parser.add_argument("--fps", type=int, default=20, help="fotogramas por segundo del clip")
    parser.add_argument("--frames", type=int, default=5, help="frames de calibracion por video")
    argumentos = parser.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        sys.exit("Falta ffmpeg. Instalalo con: brew install ffmpeg")

    CLIPS.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(parents=True, exist_ok=True)

    videos = sorted(v for v in ORIGINALES.rglob("*") if v.suffix.lower() in EXTENSIONES)

    if not videos:
        sys.exit(f"No hay videos en {ORIGINALES.relative_to(RAIZ)}/. Pon ahi los del profesor.")

    total_antes = total_despues = 0.0

    for video in videos:
        # Se conservan las subcarpetas (rutaIdeal, desacarrilamiento, ...):
        # dicen qué caso de prueba es cada video.
        relativa = video.relative_to(ORIGINALES).parent
        carpeta_clips = CLIPS / relativa
        carpeta_frames = FRAMES / relativa
        carpeta_clips.mkdir(parents=True, exist_ok=True)
        carpeta_frames.mkdir(parents=True, exist_ok=True)

        destino = carpeta_clips / f"{video.stem}.mp4"
        comprimir(video, destino, argumentos.ancho, argumentos.calidad, argumentos.fps)
        guardados = extraer_frames(video, carpeta_frames, argumentos.frames, argumentos.ancho)

        total_antes += mb(video)
        total_despues += mb(destino)

        etiqueta = str(video.relative_to(ORIGINALES))
        print(
            f"{etiqueta}: {mb(video):.1f} MB -> {mb(destino):.1f} MB"
            f" ({100 * mb(destino) / mb(video):.0f}%), {guardados} frames"
        )

    print(f"\nTotal: {total_antes:.1f} MB -> {total_despues:.1f} MB")
    print(f"Clips en  {CLIPS.relative_to(RAIZ)}/  y frames en {FRAMES.relative_to(RAIZ)}/")
    print("Los originales no se suben al repo (datos/originales/ esta en .gitignore).")


if __name__ == "__main__":
    main()

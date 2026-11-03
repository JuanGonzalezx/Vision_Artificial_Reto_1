"""Prepara los recortes de las señales para entrenar la CNN (Reto 2).

Toma las fotos de `datos/senales/<CLASE>/`, ubica la señal con las máscaras de
color (la misma localización que usa el pipeline en vivo: rojo, verde y
amarillo) y guarda el recorte con margen, aplanado al tamaño de entrada de la
CNN, en `datos/senales_recortes/<CLASE>/`. Así el entrenamiento y la inferencia
recortan igual la señal.

    uv run python tools/preparar_senales.py
    uv run python tools/preparar_senales.py --origen datos/senales --destino datos/senales_recortes

Las fotos que no dan candidato se listan al final para revisarlas a mano.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from reto.clasificador import recorte_con_margen  # noqa: E402
from reto.config import Config  # noqa: E402
from reto.senales import proponer_candidatos  # noqa: E402

EXTENSIONES = (".jpg", ".jpeg", ".png")


def clases_de(origen: Path) -> list[str]:
    """Subcarpetas de clase, que son los nombres que usa el entrenamiento."""
    return sorted(p.name for p in origen.iterdir() if p.is_dir())


def imagenes_de(carpeta: Path) -> list[Path]:
    return sorted(p for p in carpeta.iterdir()
                  if p.is_file() and p.suffix.lower() in EXTENSIONES)


def preparar_imagen(ruta: Path, destino: Path, config: Config) -> bool:
    """Recorta la señal de una foto. Devuelve False si no encontró candidato."""
    imagen = cv2.imread(str(ruta))
    if imagen is None:
        raise ValueError(f"No se pudo leer la imagen: {ruta}")

    candidatos, _ = proponer_candidatos(imagen, config)
    if not candidatos:
        return False

    recorte = recorte_con_margen(imagen, candidatos[0]["caja"], config.margen_candidato_senal)
    ancho, alto = config.tamano_entrada_senales
    recorte = cv2.resize(recorte, (ancho, alto))

    destino.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(destino / f"{ruta.stem}.jpg"), recorte)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara los recortes de las señales para la CNN.")
    parser.add_argument("--origen", default="datos/senales", help="carpeta con una subcarpeta por clase.")
    parser.add_argument("--destino", default="datos/senales_recortes", help="carpeta de recortes de salida.")
    argumentos = parser.parse_args()

    origen, destino = Path(argumentos.origen), Path(argumentos.destino)
    if not origen.is_dir():
        sys.exit(f"No existe la carpeta de origen: {origen}")

    clases = clases_de(origen)
    if not clases:
        sys.exit(f"No hay subcarpetas de clase en {origen}")

    config = Config()
    sin_candidato = []

    for clase in clases:
        # Se vacía la carpeta de la clase: los recortes son un artefacto generado
        # y así no quedan los de una corrida anterior con otros nombres.
        carpeta_destino = destino / clase
        if carpeta_destino.exists():
            shutil.rmtree(carpeta_destino)
        resultados = [(ruta, preparar_imagen(ruta, carpeta_destino, config))
                      for ruta in imagenes_de(origen / clase)]
        recortes = sum(1 for _, hecho in resultados if hecho)
        print(f"{clase:14s} {recortes}/{len(resultados)} recortes")
        sin_candidato += [f"{clase}/{ruta.name}" for ruta, hecho in resultados if not hecho]

    if sin_candidato:
        print("\nSin candidato (revisar a mano):")
        print("\n".join(f"  {nombre}" for nombre in sin_candidato))

    print(f"\nRecortes en {destino}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

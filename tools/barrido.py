"""Prueba varios valores de un parámetro sobre todos los clips y compara.

Es la forma de elegir un umbral con datos en vez de a ojo, y de poder
responder "¿por qué 110 y no 130?" con una tabla.

    uv run python tools/barrido.py vmax 90 100 110 120 130
    uv run python tools/barrido.py zona_muerta 0.05 0.10 0.15 0.20
    uv run python tools/barrido.py --lista

Qué mirar en la tabla:
- `linea_%` sube: bien, pero solo si `saltos` no sube con él.
- `saltos`: veces que la desviación pega un brinco entre dos frames. Eso no
  lo puede hacer el carro moviéndose: es la máscara yéndose a una sombra.
- `recuperacion`: de los 5 clips de descarrilamiento, en cuántos busca hacia
  el lado correcto. Si baja de 5, el valor no sirve aunque el resto mejore.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from reto.config import Config  # noqa: E402

# Cada parámetro dice cómo se escribe en la configuración.
PARAMETROS = {
    "vmax": ("V maximo de la linea (que tan oscuro tiene que ser)",
             lambda c, v: setattr(c, "hsv_linea", (c.hsv_linea[0], (179, c.hsv_linea[1][1], int(v))))),
    "smax": ("S maximo de la linea (que tan gris tiene que ser)",
             lambda c, v: setattr(c, "hsv_linea", (c.hsv_linea[0], (179, int(v), c.hsv_linea[1][2])))),
    "area_minima_linea": ("area minima para aceptar un contorno como linea",
                          lambda c, v: setattr(c, "area_minima_linea", int(v))),
    "zona_muerta": ("desviacion que se considera 'centrado'",
                    lambda c, v: setattr(c, "zona_muerta", float(v))),
    "ganancia_giro": ("cuanto gira por unidad de desviacion",
                      lambda c, v: setattr(c, "ganancia_giro", float(v))),
    "peso_linea_lejana": ("cuanto pesa la franja lejana (anticipar curvas)",
                          lambda c, v: setattr(c, "peso_linea_lejana", float(v))),
    "frames_para_buscar": ("frames sin linea antes de entrar a BUSCANDO",
                           lambda c, v: setattr(c, "frames_para_buscar", int(v))),
    "suavizado": ("promedio movil de la desviacion, en frames",
                  lambda c, v: setattr(c, "suavizado_desviacion", int(v))),
    "area_minima_senal": ("area minima para aceptar una senal",
                          lambda c, v: setattr(c, "area_minima_senal", int(v))),
}


def cargar_evaluador():
    """Reutiliza las métricas de tools/evaluar.py sin duplicarlas."""
    ruta = RAIZ / "tools" / "evaluar.py"
    spec = importlib.util.spec_from_file_location("evaluar", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parametro", nargs="?", help="que parametro barrer")
    parser.add_argument("valores", nargs="*", help="valores a probar")
    parser.add_argument("--carpeta", default="datos/clips")
    parser.add_argument("--config", default=None, help="JSON base sobre el que se varia")
    parser.add_argument("--lista", action="store_true", help="muestra los parametros disponibles")
    argumentos = parser.parse_args()

    if argumentos.lista or not argumentos.parametro:
        print("Parametros que se pueden barrer:\n")
        for nombre, (descripcion, _) in PARAMETROS.items():
            print(f"  {nombre:<20} {descripcion}")
        return

    if argumentos.parametro not in PARAMETROS:
        sys.exit(f"No conozco '{argumentos.parametro}'. Corre con --lista para ver cuales hay.")

    if not argumentos.valores:
        sys.exit("Faltan los valores a probar, por ejemplo: barrido.py vmax 100 110 120")

    evaluar = cargar_evaluador()
    clips = sorted(Path(argumentos.carpeta).rglob("*.mp4"))

    if not clips:
        sys.exit(f"No hay clips en {argumentos.carpeta}/")

    descripcion, aplicar = PARAMETROS[argumentos.parametro]
    print(f"{argumentos.parametro}: {descripcion}")
    print(f"{len(clips)} clips\n")
    print(f"{'valor':>12} {'linea_%':>9} {'saltos':>7} {'desv_media':>11} {'zigzag/s':>9} "
          f"{'recuperacion':>13}")

    for valor in argumentos.valores:
        config = Config.desde_json(argumentos.config) if argumentos.config else Config()
        aplicar(config, valor)

        filas = [evaluar.evaluar_clip(clip, config) for clip in clips]
        total = sum(f["frames"] for f in filas)
        con_linea = sum(f["frames"] * f["linea_%"] / 100 for f in filas)
        saltos = sum(f["saltos_por_s"] * f["duracion_s"] for f in filas)
        zigzag = sum(f["zigzag_por_s"] * f["duracion_s"] for f in filas)
        desviacion = sum(f["desviacion_media"] * f["frames"] for f in filas) / total
        revision = evaluar.revisar_lado_de_busqueda(filas)
        bien = sum(1 for linea in revision if linea.strip().startswith("OK"))

        print(f"{valor:>12} {100 * con_linea / total:>8.1f}% {saltos:>7.0f} {desviacion:>11.3f} "
              f"{zigzag / sum(f['duracion_s'] for f in filas):>9.2f} {bien:>10}/{len(revision)}")

    print("\nRegla: preferir el valor con mas linea_% y menos saltos, sin perder recuperaciones.")


if __name__ == "__main__":
    main()

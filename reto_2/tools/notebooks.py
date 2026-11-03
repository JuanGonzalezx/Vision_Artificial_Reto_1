"""Utilidades para los notebooks del profesor.

Los .ipynb originales pesan megas porque llevan imágenes incrustadas en
base64 dentro del texto (y las salidas de cada celda). Aquí se generan dos
versiones livianas que sí entran al repo:

- `limpiar`: el mismo notebook sin salidas y sin las imágenes en base64
  (queda en KB, conserva el texto y el código, se puede abrir en Colab).
- `extraer`: un .py con el código, con el texto del profesor como comentarios.

Las imágenes solo están en el notebook original, que queda fuera del repo
(ver docs/reto/tecnicas-permitidas.md).

Uso:
    uv run python tools/notebooks.py limpiar <entrada.ipynb> <salida.ipynb>
    uv run python tools/notebooks.py extraer <entrada.ipynb> <salida.py>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

NOTA_IMAGEN = "_(imagen en el notebook original)_"

# <img src="data:image/png;base64,...."> y ![...](data:image/png;base64,....)
PATRON_IMG_HTML = re.compile(r"<img[^>]*src=\"data:image/[^\"]*\"[^>]*>", re.I)
PATRON_IMG_MD = re.compile(r"!\[[^\]]*\]\(data:image/[^)]*\)")


def quitar_imagenes(texto: str) -> str:
    """Reemplaza las imágenes en base64 por una nota corta."""
    texto = PATRON_IMG_HTML.sub(NOTA_IMAGEN, texto)
    texto = PATRON_IMG_MD.sub(NOTA_IMAGEN, texto)
    return texto


def limpiar(entrada: Path, salida: Path) -> None:
    """Quita salidas, contadores de ejecución e imágenes incrustadas."""
    nb = json.loads(entrada.read_text(encoding="utf8"))

    for celda in nb.get("cells", []):
        celda.pop("attachments", None)
        celda["source"] = quitar_imagenes("".join(celda.get("source", []))).splitlines(True)

        if celda.get("cell_type") == "code":
            celda["outputs"] = []
            celda["execution_count"] = None

    salida.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf8")


def extraer(entrada: Path, salida: Path) -> None:
    """Escribe un .py con el código y el texto del profesor como comentarios."""
    nb = json.loads(entrada.read_text(encoding="utf8"))
    lineas = [
        '"""Codigo extraido de ' + entrada.name + " (notebook del profesor).",
        "",
        "Generado con tools/notebooks.py; no editar a mano.",
        '"""',
        "",
    ]

    for celda in nb.get("cells", []):
        fuente = quitar_imagenes("".join(celda.get("source", []))).strip()

        if not fuente:
            continue

        if celda["cell_type"] == "markdown":
            lineas.append("")
            lineas += ["# " + linea for linea in fuente.splitlines()]
            lineas.append("")
        else:
            lineas.append(fuente)
            lineas.append("")

    salida.write_text("\n".join(lineas) + "\n", encoding="utf8")


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in {"limpiar", "extraer"}:
        print(__doc__)
        raise SystemExit(1)

    accion, entrada, salida = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    (limpiar if accion == "limpiar" else extraer)(entrada, salida)
    print(f"{accion}: {entrada.name} -> {salida}")


if __name__ == "__main__":
    main()

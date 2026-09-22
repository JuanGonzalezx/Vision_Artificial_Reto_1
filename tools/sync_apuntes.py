"""Copia los apuntes de cada clase al repo del reto.

Los apuntes se escriben en la carpeta de la materia (claseN/README.md) y se
copian aquí para que el equipo —y los agentes— tengan todo en un solo sitio.

Uso (desde la raíz del repo):
    uv run python tools/sync_apuntes.py

Solo funciona en la máquina donde existe la carpeta de la materia; para los
demás, las copias ya están versionadas en docs/clases/.
"""

from __future__ import annotations

import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CARPETA_MATERIA = RAIZ.parents[1]          # .../visionArtificial
DESTINO = RAIZ / "docs" / "clases"


def arreglar_enlaces(texto: str) -> str:
    """Ajusta los enlaces relativos de los apuntes a su nueva ubicación."""
    for n in range(1, 9):
        texto = texto.replace(f"../clase{n}/README.md", f"clase{n}.md")

    texto = texto.replace(
        "../contenidoClase/FundamentosVisionArtificial.pdf",
        "los slides del profesor (fuera del repo, en contenidoClase/)",
    )
    # Enlaces al repo del reto: desde docs/clases/ el repo queda dos niveles arriba.
    texto = texto.replace("../reto_1/Vision_Artificial_Reto_1/docs/", "../")
    return texto


def main() -> None:
    if not (CARPETA_MATERIA / "contenidoClase").exists():
        print(f"No encontré la carpeta de la materia en {CARPETA_MATERIA}; nada que copiar.")
        return

    DESTINO.mkdir(parents=True, exist_ok=True)

    for origen in sorted(CARPETA_MATERIA.glob("clase*/README.md")):
        clase = origen.parent.name
        destino = DESTINO / f"{clase}.md"
        destino.write_text(arreglar_enlaces(origen.read_text(encoding="utf8")), encoding="utf8")

        # Las imágenes de los apuntes viajan con ellos.
        for imagen in sorted((origen.parent / "img").glob("*")):
            (DESTINO / "img").mkdir(exist_ok=True)
            shutil.copyfile(imagen, DESTINO / "img" / imagen.name)

        print(f"{clase} -> {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()

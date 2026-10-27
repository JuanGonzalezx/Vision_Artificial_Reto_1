"""Entrena las CNN de clase sobre los recortes de las señales (Reto 2).

Usa sin modificar el pipeline del profesor (`5_cnns/cnn_trainer.py`): le apunta
`dataset_dir` a `datos/senales/` (una carpeta por clase) y guarda los resultados
—modelo `.keras`, matriz de confusión, curva de pérdida y reporte— en
`modelos/entrenamiento/<experimento>/<modelo>/`.

    uv run python tools/entrenar_senales.py --modelos MobileNet
    uv run python tools/entrenar_senales.py            # todas las arquitecturas

Al terminar, copia el `.keras` elegido a `modelos/senales.keras` para que el
pipeline lo use (ver `modelos/README.md`).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "5_cnns"))

from cnn_trainer import MODELOS, CNNTrainer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Entrena las CNN de las señales (Reto 2).")
    parser.add_argument("--datos", default="datos/senales", help="carpeta con una subcarpeta por clase.")
    parser.add_argument("--salida", default="modelos/entrenamiento", help="carpeta de resultados.")
    parser.add_argument("--experimento", default="senales_reto2", help="nombre del experimento.")
    parser.add_argument("--epocas", type=int, default=50, help="máximo de épocas (hay early stopping).")
    parser.add_argument("--modelos", nargs="*", default=None,
                        help=f"arquitecturas a entrenar; por defecto todas: {list(MODELOS)}")
    argumentos = parser.parse_args()

    trainer = CNNTrainer(
        dataset_dir=argumentos.datos,
        output_dir=argumentos.salida,
        experimento=argumentos.experimento,
        max_epochs=argumentos.epocas,
        patience=5,
        batch_size=32,
        learning_rate=1e-3,
        img_size=(224, 224),
        val_split=0.2,
        test_split=0.1,
        seed=42,
    )
    trainer.entrenar_todos(argumentos.modelos)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

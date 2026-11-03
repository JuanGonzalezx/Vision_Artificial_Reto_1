"""Elige los 2 mejores modelos por val_loss y los compara en test (Reto 2).

Lee `resultados.csv` y `particiones.csv` del experimento (los deja `tools/entrenar_senales.py`),
ordena las arquitecturas por `val_loss` (el test NO interviene en la elección), y para cada una:

- métricas sobre la partición test: accuracy, y precisión/recall/F1 por clase y macro;
- tiempo de inferencia por imagen (lote de 1, modelo ya caliente, CPU/GPU de esta máquina).

Los tiempos se miden en las 5 arquitecturas para justificar el modelo integrado; las
métricas completas se calculan solo para el top-2. Escribe `comparativa_top2.md` y
`tiempos_inferencia.csv` dentro del experimento.

    uv run python tools/evaluar_modelos.py
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "cnn"))

import numpy as np  # noqa: E402
import tensorflow as tf  # noqa: E402
from sklearn.metrics import precision_recall_fscore_support  # noqa: E402

from cnn_trainer import MODELOS  # noqa: E402

NOMBRES_CLASE = ("PARE", "SIGA", "ZONA_ESCOLAR", "VELOCIDAD_60")
IMG_SIZE = (224, 224)


def cargar_imagen(ruta: Path) -> np.ndarray:
    img = tf.io.decode_image(tf.io.read_file(str(ruta)), channels=3, expand_animations=False)
    return tf.cast(tf.image.resize(img, IMG_SIZE), tf.float32).numpy()


def leer_csv(ruta: Path) -> list[dict]:
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def medir_tiempo(modelo, muestra: np.ndarray, repeticiones: int) -> tuple[float, float]:
    """(mediana, p95) en ms de una inferencia con lote de 1, sin contar el calentamiento."""
    for _ in range(5):
        modelo(muestra, training=False)
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        modelo(muestra, training=False).numpy()
        tiempos.append((time.perf_counter() - t0) * 1000)
    tiempos.sort()
    return statistics.median(tiempos), tiempos[int(0.95 * (len(tiempos) - 1))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Top-2 por val_loss, métricas en test y tiempos.")
    parser.add_argument("--datos", default="cnn/dataset")
    parser.add_argument("--experimento", default="modelos/entrenamiento/senales_reto2")
    parser.add_argument("--repeticiones", type=int, default=50)
    parser.add_argument("--top", type=int, default=2)
    argumentos = parser.parse_args()

    datos = RAIZ / argumentos.datos
    exp = RAIZ / argumentos.experimento
    resultados = sorted(leer_csv(exp / "resultados.csv"), key=lambda r: float(r["val_loss"]))
    top = [r["modelo"] for r in resultados[: argumentos.top]]
    print(f"Orden por val_loss: {[r['modelo'] for r in resultados]}")
    print(f"Top-{argumentos.top}: {top}")

    test = [f["archivo"] for f in leer_csv(exp / "particiones.csv") if f["particion"] == "test"]
    y_true = np.array([int(a.split("/")[0]) for a in test])
    imagenes = np.stack([cargar_imagen(datos / a) for a in test])
    print(f"Test: {len(test)} imágenes")

    filas_tiempo, metricas = [], {}
    for r in resultados:
        nombre = r["modelo"]
        modelo = tf.keras.models.load_model(exp / nombre / f"{nombre}.keras")
        preprocesar = MODELOS[nombre][1]
        x = preprocesar(imagenes.copy())
        mediana, p95 = medir_tiempo(modelo, x[:1], argumentos.repeticiones)
        filas_tiempo.append({"modelo": nombre, "val_loss": float(r["val_loss"]),
                             "mediana_ms": round(mediana, 1), "p95_ms": round(p95, 1),
                             "parametros_M": round(modelo.count_params() / 1e6, 1)})
        print(f"{nombre}: {mediana:.1f} ms (p95 {p95:.1f}), {modelo.count_params() / 1e6:.1f} M parámetros")
        if nombre in top:
            y_pred = np.argmax(modelo.predict(x, batch_size=16, verbose=0), axis=1)
            p, rc, f1, _ = precision_recall_fscore_support(
                y_true, y_pred, labels=range(len(NOMBRES_CLASE)), zero_division=0)
            metricas[nombre] = {
                "accuracy": float((y_true == y_pred).mean()),
                "clases": list(zip(p, rc, f1)),
                "macro": (p.mean(), rc.mean(), f1.mean()),
            }

    with open(exp / "tiempos_inferencia.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas_tiempo[0]))
        escritor.writeheader()
        escritor.writerows(filas_tiempo)

    lineas = [f"# Comparativa de los {argumentos.top} mejores modelos (test, {len(test)} imágenes)", "",
              "Elegidos por menor `val_loss`; el test no interviene en la elección.", "",
              "| Modelo | val_loss | Accuracy | Precisión macro | Recall macro | F1 macro | Mediana (ms) | p95 (ms) | Parámetros (M) |",
              "|---|---|---|---|---|---|---|---|---|"]
    por_nombre = {f["modelo"]: f for f in filas_tiempo}
    for nombre in top:
        m, t = metricas[nombre], por_nombre[nombre]
        lineas.append(f"| {nombre} | {t['val_loss']:.5f} | {m['accuracy']:.4f} | {m['macro'][0]:.4f} | "
                      f"{m['macro'][1]:.4f} | {m['macro'][2]:.4f} | {t['mediana_ms']} | {t['p95_ms']} | {t['parametros_M']} |")
    for nombre in top:
        lineas += ["", f"## {nombre} · por clase", "", "| Clase | Precisión | Recall | F1 | Soporte |", "|---|---|---|---|---|"]
        for i, (p, rc, f1) in enumerate(metricas[nombre]["clases"]):
            lineas.append(f"| {NOMBRES_CLASE[i]} | {p:.4f} | {rc:.4f} | {f1:.4f} | {(y_true == i).sum()} |")
    lineas += ["", "## Tiempo de inferencia (las 5 arquitecturas, lote de 1)", "",
               "| Modelo | val_loss | Mediana (ms) | p95 (ms) | Parámetros (M) |", "|---|---|---|---|---|"]
    for t in sorted(filas_tiempo, key=lambda t: t["mediana_ms"]):
        lineas.append(f"| {t['modelo']} | {t['val_loss']:.5f} | {t['mediana_ms']} | {t['p95_ms']} | {t['parametros_M']} |")
    (exp / "comparativa_top2.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Escrito {exp / 'comparativa_top2.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

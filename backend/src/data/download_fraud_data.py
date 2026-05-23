# src/data/download_fraud_data.py
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def download_openml_creditcard(out_path: Path, dataset_id: int = 43627) -> Path:
    """
    Descarga el dataset 'credit-card-fraud-detection' desde OpenML y lo guarda como CSV.
    Maneja correctamente el target aunque OpenML no lo marque como default.
    """
    try:
        import openml
    except ImportError as e:
        raise SystemExit("No se encontró 'openml'. Instala con: pip install openml") from e

    ds = openml.datasets.get_dataset(dataset_id)

    # Cargamos TODO el dataframe
    df, *_ = ds.get_data(dataset_format="dataframe")

    # Normalizamos nombre de la columna target
    target_col = None
    for c in df.columns:
        if c.lower() == "class":
            target_col = c
            break

    if target_col is None:
        raise RuntimeError(f"No se encontró columna target 'Class' en el dataset. Columnas: {df.columns.tolist()}")

    # Aseguramos tipo correcto
    df[target_col] = pd.to_numeric(df[target_col], errors="coerce").astype(int)

    # Renombramos a 'Class' por consistencia
    if target_col != "Class":
        df = df.rename(columns={target_col: "Class"})

    # Normalización mínima
    if "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga el dataset de fraude (ULB creditcard) desde OpenML.")
    parser.add_argument("--out", type=str, default="data/raw/creditcard_openml.csv", help="Ruta de salida CSV")
    parser.add_argument("--dataset-id", type=int, default=43627, help="OpenML dataset id (default: 43627)")
    args = parser.parse_args()

    out_path = Path(args.out)
    saved = download_openml_creditcard(out_path=out_path, dataset_id=args.dataset_id)

    # Resumen rápido
    df = pd.read_csv(saved)
    n = len(df)
    pos = int(df["Class"].sum())
    print(f"✅ Dataset guardado en: {saved.resolve()}")
    print(f"Filas: {n} | Fraudes (Class=1): {pos} | % fraude: {pos / n:.6f}")
    print(f"Columnas: {df.columns.tolist()[:10]} ... (total {df.shape[1]})")


if __name__ == "__main__":
    main()

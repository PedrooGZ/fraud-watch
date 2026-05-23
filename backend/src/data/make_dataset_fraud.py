# src/data/make_dataset_fraud.py
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara dataset de fraude (OpenML creditcard).")
    parser.add_argument("--in", dest="in_path", type=str, default="data/raw/creditcard_openml.csv", help="CSV raw")
    parser.add_argument("--out", dest="out_path", type=str, default="data/processed/creditcard_processed.csv", help="CSV processed")
    args = parser.parse_args()

    in_path = Path(args.in_path)
    out_path = Path(args.out_path)

    df = pd.read_csv(in_path)

    if "Class" not in df.columns:
        raise RuntimeError("No existe columna 'Class' en el CSV.")

    # Limpieza mínima
    df = df.dropna().reset_index(drop=True)

    # Asegura tipo target
    df["Class"] = pd.to_numeric(df["Class"], errors="coerce").astype(int)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    n = len(df)
    pos = int(df["Class"].sum())
    print(f"✅ Dataset procesado guardado en: {out_path.resolve()}")
    print(f"Filas: {n} | Fraudes: {pos} | % fraude: {pos / n:.6f}")
    print(f"Columnas: {df.columns.tolist()}")


if __name__ == "__main__":
    main()

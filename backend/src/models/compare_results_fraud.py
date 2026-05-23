from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
METRIC_COLS = ["pr_auc", "recall@1%", "recall@0.5%", "best_f1"]
def load_baselines(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns={"baseline": "model"})
    for c in METRIC_COLS:
        if c not in df.columns:
            raise RuntimeError(f"Baselines: falta columna '{c}' en {path}")
    return df[["model"] + METRIC_COLS]
def load_single_model(path: Path, model_name_col: str = "model") -> pd.DataFrame:
    df = pd.read_csv(path)
    if model_name_col not in df.columns:
        raise RuntimeError(f"Falta columna '{model_name_col}' en {path}")
    for c in METRIC_COLS:
        if c not in df.columns:
            raise RuntimeError(f"Modelo: falta columna '{c}' en {path}")
    out = df.groupby(model_name_col)[METRIC_COLS].mean().reset_index().rename(columns={model_name_col: "model"})
    return out
def main() -> None:
    parser = argparse.ArgumentParser(description="Comparativa final fraude: baselines + logistic + HGB.")
    parser.add_argument("--baselines", type=str, default="docs/fraud_baselines.csv")
    parser.add_argument("--logreg", type=str, default="docs/fraud_logreg_results.csv")
    parser.add_argument("--hgb", type=str, default="docs/fraud_hgb_results.csv")
    parser.add_argument("--out", type=str, default="docs/fraud_summary_models.csv")
    args = parser.parse_args()
    parts = [
        load_baselines(Path(args.baselines)),
        load_single_model(Path(args.logreg)),
        load_single_model(Path(args.hgb)),
    ]
    summary = pd.concat(parts, ignore_index=True)
    summary = summary.sort_values(["pr_auc", "best_f1"], ascending=False).reset_index(drop=True)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.out, index=False)
if __name__ == "__main__":
    main()

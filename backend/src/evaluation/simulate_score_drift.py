from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.core.config import ARTIFACTS_DIR, DOCS_DIR, MODEL_PATH, PROCESSED_DATA_DIR


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    eps = 1e-8
    q = np.linspace(0, 1, bins + 1)
    cuts = np.quantile(expected, q)
    cuts[0], cuts[-1] = -np.inf, np.inf

    exp_counts, _ = np.histogram(expected, bins=cuts)
    act_counts, _ = np.histogram(actual, bins=cuts)

    exp_dist = exp_counts / max(1, exp_counts.sum())
    act_dist = act_counts / max(1, act_counts.sum())

    exp_dist = np.clip(exp_dist, eps, None)
    act_dist = np.clip(act_dist, eps, None)

    return float(np.sum((act_dist - exp_dist) * np.log(act_dist / exp_dist)))


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else path.resolve()


def main() -> None:
    default_data_path = PROCESSED_DATA_DIR / "creditcard_processed.csv"
    default_model_path = MODEL_PATH
    default_ref_scores_path = ARTIFACTS_DIR / "ref_scores.npy"
    default_new_scores_path = ARTIFACTS_DIR / "new_scores.npy"
    default_summary_path = DOCS_DIR / "fraud_drift_summary.csv"

    parser = argparse.ArgumentParser(
        description="Simula drift cambiando la distribución de Amount y calcula PSI."
    )
    parser.add_argument("--data", type=str, default=str(default_data_path))
    parser.add_argument("--model", type=str, default=str(default_model_path))
    parser.add_argument("--ref", type=str, default=str(default_ref_scores_path))
    parser.add_argument("--out", type=str, default=str(default_new_scores_path))
    parser.add_argument("--summary", type=str, default=str(default_summary_path))
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--n", type=int, default=20000, help="Tamaño del lote nuevo")
    parser.add_argument("--amount-mult", type=float, default=3.0, help="Multiplicador de Amount para simular drift")
    parser.add_argument("--bins", type=int, default=10)

    args = parser.parse_args()

    data_path = resolve_path(args.data)
    model_path = resolve_path(args.model)
    ref_scores_path = resolve_path(args.ref)
    new_scores_path = resolve_path(args.out)
    summary_path = resolve_path(args.summary)

    rng = np.random.default_rng(args.seed)

    if not data_path.exists():
        raise FileNotFoundError(f"No existe el dataset procesado: {data_path}")

    if not model_path.exists():
        raise FileNotFoundError(f"No existe el modelo: {model_path}")

    if not ref_scores_path.exists():
        raise FileNotFoundError(f"No existe el archivo de scores de referencia: {ref_scores_path}")

    df = pd.read_csv(data_path)

    bundle = joblib.load(model_path)
    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    X = df[feature_cols].to_numpy(dtype=float)
    idx = rng.choice(len(X), size=min(args.n, len(X)), replace=False)
    X_new = X[idx].copy()

    if "Amount" in feature_cols:
        amount_idx = feature_cols.index("Amount")
        X_new[:, amount_idx] = X_new[:, amount_idx] * args.amount_mult

    new_scores = model.predict_proba(X_new)[:, 1].astype(float)

    ref_scores = np.load(ref_scores_path)
    psi_value = psi(ref_scores, new_scores, bins=args.bins)

    new_scores_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(new_scores_path, new_scores)

    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(
        [
            {
                "psi": psi_value,
                "bins": args.bins,
                "sample_size": len(new_scores),
                "amount_multiplier": args.amount_mult,
                "ref_mean": float(ref_scores.mean()),
                "ref_p95": float(np.quantile(ref_scores, 0.95)),
                "new_mean": float(new_scores.mean()),
                "new_p95": float(np.quantile(new_scores, 0.95)),
                "status": classify_psi(psi_value),
            }
        ]
    )
    summary.to_csv(summary_path, index=False)

    print("Nuevo lote generado y guardado en:", new_scores_path.resolve())
    print("Resumen de drift guardado en:", summary_path.resolve())
    print("PSI =", psi_value)
    print("Guía: <0.1 estable | 0.1-0.25 alerta | >0.25 drift probable")
    print("Estado:", classify_psi(psi_value))
    print("Ref mean/p95:", float(ref_scores.mean()), float(np.quantile(ref_scores, 0.95)))
    print("New mean/p95:", float(new_scores.mean()), float(np.quantile(new_scores, 0.95)))


def classify_psi(value: float) -> str:
    if value < 0.1:
        return "stable"
    if value < 0.25:
        return "warning"
    return "probable_drift"


if __name__ == "__main__":
    main()
# src/evaluation/shap_fraud.py
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV


def stratified_split(y: np.ndarray, test_size: float, seed: int):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    pos_idx = idx[y == 1]
    neg_idx = idx[y == 0]
    rng.shuffle(pos_idx); rng.shuffle(neg_idx)
    n_pos_test = int(len(pos_idx) * test_size)
    n_neg_test = int(len(neg_idx) * test_size)
    test_idx = np.concatenate([pos_idx[:n_pos_test], neg_idx[:n_neg_test]])
    train_idx = np.setdiff1d(idx, test_idx)
    return train_idx, test_idx


def main() -> None:
    parser = argparse.ArgumentParser(description="SHAP explicabilidad para fraude.")
    parser.add_argument("--data", type=str, default="data/processed/creditcard_processed.csv")
    parser.add_argument("--outdir", type=str, default="docs/shap")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--n-samples", type=int, default=2000, help="Muestras SHAP (default: 2000)")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data)
    X = df.drop(columns=["Class"])
    y = df["Class"].to_numpy().astype(int)

    train_idx, test_idx = stratified_split(y, args.test_size, args.seed)

    X_train, y_train = X.iloc[train_idx], y[train_idx]
    X_test, y_test = X.iloc[test_idx], y[test_idx]

    # Entrenamos HGB
    pos = (y_train == 1).sum()
    neg = (y_train == 0).sum()
    w_pos = neg / max(1, pos)
    sample_weight = np.where(y_train == 1, w_pos, 1.0)

    hgb = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_depth=6,
        min_samples_leaf=50,
        random_state=args.seed,
    )

    hgb.fit(X_train, y_train, sample_weight=sample_weight)

    # Calibración isotónica
    hgb_cal = CalibratedClassifierCV(hgb, method="isotonic", cv=5)
    hgb_cal.fit(X_train, y_train)

    # Submuestreo para SHAP (más rápido)
    rng = np.random.default_rng(args.seed)
    sample_idx = rng.choice(len(X_test), size=min(args.n_samples, len(X_test)), replace=False)
    X_shap = X_test.iloc[sample_idx]

    # SHAP TreeExplainer
    explainer = shap.Explainer(hgb)
    shap_values = explainer(X_shap)

    # ---------- GLOBAL ----------
    plt.figure()
    shap.plots.bar(shap_values, max_display=15, show=False)
    plt.tight_layout()
    plt.savefig(outdir / "shap_global_bar.png", dpi=150)
    plt.close()

    plt.figure()
    shap.plots.beeswarm(shap_values, max_display=15, show=False)
    plt.tight_layout()
    plt.savefig(outdir / "shap_global_beeswarm.png", dpi=150)
    plt.close()

    # ---------- LOCAL ----------
    # Ejemplo: transacción con mayor probabilidad predicha
    probs = hgb_cal.predict_proba(X_shap)[:, 1]
    idx_max = int(np.argmax(probs))

    plt.figure()
    shap.plots.waterfall(shap_values[idx_max], show=False)
    plt.tight_layout()
    plt.savefig(outdir / "shap_local_waterfall.png", dpi=150)
    plt.close()

    print("✅ SHAP generado correctamente.")
    print("Gráficos guardados en:", outdir.resolve())
    print("Top prob fraude:", float(probs[idx_max]))


if __name__ == "__main__":
    main()

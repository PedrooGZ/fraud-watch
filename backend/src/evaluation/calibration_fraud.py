# src/evaluation/calibration_fraud.py
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss, average_precision_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


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


def fit_models(X_train, y_train, seed):
    # Logistic
    logreg = Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(class_weight="balanced", max_iter=3000))
    ])

    # HistGradientBoosting (con sample_weight)
    pos = (y_train == 1).sum()
    neg = (y_train == 0).sum()
    w_pos = neg / max(1, pos)
    sample_weight = np.where(y_train == 1, w_pos, 1.0)

    hgb = HistGradientBoostingClassifier(
        max_iter=300,
        learning_rate=0.05,
        max_depth=6,
        min_samples_leaf=50,
        random_state=seed,
    )

    logreg.fit(X_train, y_train)
    hgb.fit(X_train, y_train, sample_weight=sample_weight)

    return logreg, hgb


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibración de probabilidades para fraude.")
    parser.add_argument("--data", type=str, default="data/processed/creditcard_processed.csv")
    parser.add_argument("--out", type=str, default="docs/fraud_calibration_summary.csv")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    X = df.drop(columns=["Class"]).to_numpy()
    y = df["Class"].to_numpy().astype(int)

    train_idx, test_idx = stratified_split(y, args.test_size, args.seed)
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    logreg, hgb = fit_models(X_train, y_train, args.seed)

    models = {
        "logreg_raw": logreg,
        "hgb_raw": hgb,
        "logreg_platt": CalibratedClassifierCV(logreg, method="sigmoid", cv=5),
        "logreg_isotonic": CalibratedClassifierCV(logreg, method="isotonic", cv=5),
        "hgb_platt": CalibratedClassifierCV(hgb, method="sigmoid", cv=5),
        "hgb_isotonic": CalibratedClassifierCV(hgb, method="isotonic", cv=5),
    }

    rows = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        probs = model.predict_proba(X_test)[:, 1]

        brier = brier_score_loss(y_test, probs)
        ap = average_precision_score(y_test, probs)

        rows.append({
            "model": name,
            "brier_score": brier,
            "pr_auc": ap,
        })

    res = pd.DataFrame(rows).sort_values("brier_score")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)

    print("✅ Calibración evaluada. Guardado en:", out_path.resolve())
    print(res.to_string(index=False, float_format=lambda x: f"{x:.6f}"))


if __name__ == "__main__":
    main()

from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import average_precision_score, brier_score_loss
def stratified_split(y: np.ndarray, test_size: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    pos, neg = idx[y == 1], idx[y == 0]
    rng.shuffle(pos); rng.shuffle(neg)
    tpos, tneg = int(len(pos) * test_size), int(len(neg) * test_size)
    test_idx = np.concatenate([pos[:tpos], neg[:tneg]])
    train_idx = np.setdiff1d(idx, test_idx)
    return train_idx, test_idx
def main() -> None:
    p = argparse.ArgumentParser(description="Entrena y serializa el modelo final (HGB + Isotonic).")
    p.add_argument("--data", type=str, default="data/processed/creditcard_processed.csv")
    p.add_argument("--out-model", type=str, default="artifacts/fraud_model.joblib")
    p.add_argument("--out-metadata", type=str, default="artifacts/fraud_model_metadata.json")
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--max-iter", type=int, default=300)
    p.add_argument("--learning-rate", type=float, default=0.05)
    p.add_argument("--max-depth", type=int, default=6)
    p.add_argument("--min-samples-leaf", type=int, default=50)
    args = p.parse_args()
    df = pd.read_csv(args.data)
    feature_cols = [c for c in df.columns if c != "Class"]
    X = df[feature_cols].to_numpy(dtype=float)
    y = df["Class"].to_numpy(dtype=int)
    train_idx, test_idx = stratified_split(y, args.test_size, args.seed)
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    pos = int((y_train == 1).sum()); neg = int((y_train == 0).sum())
    pos_weight = neg / max(1, pos)
    sw = np.where(y_train == 1, pos_weight, 1.0)
    base = HistGradientBoostingClassifier(
        max_iter=args.max_iter,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.seed,
    )
    base.fit(X_train, y_train, sample_weight=sw)
    model = CalibratedClassifierCV(base, method="isotonic", cv=5)
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)[:, 1]
    pr_auc = float(average_precision_score(y_test, probs))
    brier = float(brier_score_loss(y_test, probs))
    out_model = Path(args.out_model); out_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_cols": feature_cols}, out_model, compress=3)
    meta = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_type": "HistGradientBoosting + Isotonic",
        "seed": args.seed,
        "test_size": args.test_size,
        "holdout_metrics": {"pr_auc": pr_auc, "brier_score": brier},
        "n_features": len(feature_cols),
    }
    out_meta = Path(args.out_metadata); out_meta.parent.mkdir(parents=True, exist_ok=True)
    out_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")
if __name__ == "__main__":
    main()

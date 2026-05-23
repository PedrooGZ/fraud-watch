from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve
def recall_at_k(y_true: np.ndarray, scores: np.ndarray, k_frac: float) -> float:
    n = len(scores)
    k = max(1, int(n * k_frac))
    idx = np.argsort(scores)[::-1][:k]
    return float(y_true[idx].sum() / max(1, y_true.sum()))
def best_f1(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    p, r, t = precision_recall_curve(y_true, scores)
    f1 = (2 * p[:-1] * r[:-1]) / np.maximum(1e-12, (p[:-1] + r[:-1]))
    i = int(np.nanargmax(f1))
    return float(f1[i]), float(t[i])
def stratified_split(y: np.ndarray, test_size: float, seed: int):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    pos_idx = idx[y == 1]
    neg_idx = idx[y == 0]
    rng.shuffle(pos_idx)
    rng.shuffle(neg_idx)
    n_pos_test = int(len(pos_idx) * test_size)
    n_neg_test = int(len(neg_idx) * test_size)
    test_idx = np.concatenate([pos_idx[:n_pos_test], neg_idx[:n_neg_test]])
    train_idx = np.setdiff1d(idx, test_idx)
    return train_idx, test_idx
def main() -> None:
    parser = argparse.ArgumentParser(description="HistGradientBoosting para detección de fraude (PR-AUC).")
    parser.add_argument("--data", type=str, default="data/processed/creditcard_processed.csv")
    parser.add_argument("--out", type=str, default="docs/fraud_hgb_results.csv")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iter", type=int, default=300)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--min-samples-leaf", type=int, default=50)
    parser.add_argument("--l2-regularization", type=float, default=0.0)
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    X = df.drop(columns=["Class"]).to_numpy()
    y = df["Class"].to_numpy().astype(int)
    train_idx, test_idx = stratified_split(y, args.test_size, args.seed)
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    pos = (y_train == 1).sum()
    neg = (y_train == 0).sum()
    w_pos = neg / max(1, pos)
    sample_weight = np.where(y_train == 1, w_pos, 1.0)
    clf = HistGradientBoostingClassifier(
        max_iter=args.max_iter,
        learning_rate=args.learning_rate,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        l2_regularization=args.l2_regularization,
        random_state=args.seed,
    )
    clf.fit(X_train, y_train, sample_weight=sample_weight)
    scores = clf.predict_proba(X_test)[:, 1]
    ap = average_precision_score(y_test, scores)
    r1 = recall_at_k(y_test, scores, 0.01)
    r005 = recall_at_k(y_test, scores, 0.005)
    f1b, thr = best_f1(y_test, scores)
    res = pd.DataFrame([{
        "model": "hist_gradient_boosting",
        "pr_auc": ap,
        "recall@1%": r1,
        "recall@0.5%": r005,
        "best_f1": f1b,
        "best_thr": thr,
        "max_iter": args.max_iter,
        "learning_rate": args.learning_rate,
        "max_depth": args.max_depth,
        "min_samples_leaf": args.min_samples_leaf,
        "l2_regularization": args.l2_regularization,
        "pos_weight_used": w_pos,
    }])
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)
    print("✅ HistGradientBoosting evaluado. Guardado en:", out_path.resolve())
if __name__ == "__main__":
    main()

from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
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
    parser = argparse.ArgumentParser(description="Logistic Regression para detección de fraude (PR-AUC).")
    parser.add_argument("--data", type=str, default="data/processed/creditcard_processed.csv")
    parser.add_argument("--out", type=str, default="docs/fraud_logreg_results.csv")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--c", type=float, default=1.0)
    parser.add_argument("--max-iter", type=int, default=3000)
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    X = df.drop(columns=["Class"]).to_numpy()
    y = df["Class"].to_numpy().astype(int)
    train_idx, test_idx = stratified_split(y, args.test_size, args.seed)
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    clf = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(
                C=args.c,
                max_iter=args.max_iter,
                class_weight="balanced",
                n_jobs=-1
            )),
        ]
    )
    clf.fit(X_train, y_train)
    scores = clf.predict_proba(X_test)[:, 1]
    ap = average_precision_score(y_test, scores)
    r1 = recall_at_k(y_test, scores, 0.01)
    r005 = recall_at_k(y_test, scores, 0.005)
    f1b, thr = best_f1(y_test, scores)
    res = pd.DataFrame([{
        "model": "logistic_regression",
        "pr_auc": ap,
        "recall@1%": r1,
        "recall@0.5%": r005,
        "best_f1": f1b,
        "best_thr": thr,
    }])
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)
    print("✅ Logistic Regression evaluada. Guardado en:", out_path.resolve())
    print(res.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
if __name__ == "__main__":
    main()

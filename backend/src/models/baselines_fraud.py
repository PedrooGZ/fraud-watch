# src/models/baselines_fraud.py
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve
def recall_at_k(y_true: np.ndarray, scores: np.ndarray, k_frac: float) -> float:
    """Recall@K%: de las K% transacciones con más score, cuántos fraudes recupero."""
    n = len(scores)
    k = max(1, int(n * k_frac))
    idx = np.argsort(scores)[::-1][:k]
    return float(y_true[idx].sum() / max(1, y_true.sum()))
def best_f1(y_true: np.ndarray, scores: np.ndarray) -> tuple[float, float]:
    """Devuelve (best_f1, threshold) buscando el umbral que maximiza F1."""
    p, r, t = precision_recall_curve(y_true, scores)
    # t tiene longitud len(p)-1
    f1 = (2 * p[:-1] * r[:-1]) / np.maximum(1e-12, (p[:-1] + r[:-1]))
    i = int(np.nanargmax(f1))
    return float(f1[i]), float(t[i])
def main() -> None:
    parser = argparse.ArgumentParser(description="Baselines fraude (PR-AUC, Recall@K, Best-F1).")
    parser.add_argument("--data", type=str, default="data/processed/creditcard_processed.csv", help="CSV processed")
    parser.add_argument("--out", type=str, default="docs/fraud_baselines.csv", help="Salida CSV")
    parser.add_argument("--test-size", type=float, default=0.2, help="Tamaño test (default 0.2)")
    parser.add_argument("--seed", type=int, default=42, help="Semilla")
    args = parser.parse_args()
    df = pd.read_csv(args.data)
    y = df["Class"].to_numpy().astype(int)
    # Split estratificado simple (el dataset no es temporal)
    rng = np.random.default_rng(args.seed)
    idx = np.arange(len(df))
    # Estratificación manual simple
    pos_idx = idx[y == 1]
    neg_idx = idx[y == 0]
    rng.shuffle(pos_idx); rng.shuffle(neg_idx)
    n_pos_test = int(len(pos_idx) * args.test_size)
    n_neg_test = int(len(neg_idx) * args.test_size)
    test_idx = np.concatenate([pos_idx[:n_pos_test], neg_idx[:n_neg_test]])
    y_test = y[test_idx]
    rows = []
    # 1) always_legit -> score=0 para todos
    scores_legit = np.zeros_like(y_test, dtype=float)
    ap_legit = average_precision_score(y_test, scores_legit)
    r1 = recall_at_k(y_test, scores_legit, 0.01)
    r005 = recall_at_k(y_test, scores_legit, 0.005)
    f1b, thr = best_f1(y_test, scores_legit)
    rows.append({"baseline": "always_legit", "pr_auc": ap_legit, "recall@1%": r1, "recall@0.5%": r005, "best_f1": f1b, "best_thr": thr})
    # 2) amount_rule -> score = Amount (si existe)
    if "Amount" in df.columns:
        scores_amt = pd.to_numeric(df.loc[test_idx, "Amount"], errors="coerce").fillna(0).to_numpy().astype(float)
        ap_amt = average_precision_score(y_test, scores_amt)
        r1 = recall_at_k(y_test, scores_amt, 0.01)
        r005 = recall_at_k(y_test, scores_amt, 0.005)
        f1b, thr = best_f1(y_test, scores_amt)
        rows.append({"baseline": "amount_rule", "pr_auc": ap_amt, "recall@1%": r1, "recall@0.5%": r005, "best_f1": f1b, "best_thr": thr})
    res = pd.DataFrame(rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)
    print("✅ Baselines guardados en:", out_path.resolve())
    print(res.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
if __name__ == "__main__":
    main()

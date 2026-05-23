from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import requests

# Allow importing `src.*` even when launching from repository root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.core.config import SCORES_DIR


def main() -> None:
    p = argparse.ArgumentParser(
        description="Scorea un CSV de transacciones usando la Fraud Scoring API."
    )
    p.add_argument("--in", dest="inp", required=True, help="CSV de entrada")
    p.add_argument(
        "--url",
        default="http://127.0.0.1:8000/predict_batch",
        help="Endpoint batch de la API",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="Timeout HTTP en segundos",
    )
    args = p.parse_args()

    in_path = Path(args.inp)
    if not in_path.exists():
        raise SystemExit(f"No existe el CSV de entrada: {in_path}")

    scores_dir = SCORES_DIR
    scores_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    input_name = in_path.stem
    out_path = scores_dir / f"scored_{input_name}_{ts}.csv"

    df = pd.read_csv(in_path)

    transactions = []
    for _, row in df.iterrows():
        feats = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                continue
            try:
                feats[col] = float(val)
            except Exception:
                continue
        transactions.append({"features": feats})

    payload = {"transactions": transactions}

    r = requests.post(args.url, json=payload, timeout=args.timeout)
    try:
        r.raise_for_status()
    except Exception:
        raise SystemExit(f"Error HTTP {r.status_code}: {r.text}")

    res = r.json()

    summary_keys = [
        "threshold_cost",
        "max_alerts",
        "n_total",
        "n_valid",
        "n_invalid",
        "n_candidates",
        "n_review",
    ]
    summary = {k: res.get(k) for k in summary_keys}

    proba = [None] * len(df)
    review = [None] * len(df)
    rank = [None] * len(df)
    is_valid = [False] * len(df)
    missing = [""] * len(df)

    for item in res.get("results_valid", []):
        i = int(item["index"])
        proba[i] = item.get("proba_fraud")
        review[i] = item.get("review")
        rank[i] = item.get("rank")
        is_valid[i] = True

    for item in res.get("results_invalid", []):
        i = int(item["index"])
        is_valid[i] = False
        missing[i] = ",".join(item.get("missing_features", []))

    out_df = df.copy()
    out_df["proba_fraud"] = proba
    out_df["review"] = review
    out_df["rank"] = rank
    out_df["is_valid"] = is_valid
    out_df["missing_features"] = missing

    out_df["review"] = out_df["review"].fillna(0).astype(int).astype(bool)
    out_df["rank"] = pd.to_numeric(out_df["rank"], errors="coerce")

    n_review = int(summary.get("n_review") or 0)
    max_alerts = int(summary.get("max_alerts") or 0)

    if n_review >= max_alerts and max_alerts > 0:
        out_df = out_df.sort_values(
            by=["review", "rank", "proba_fraud"],
            ascending=[False, True, False],
            na_position="last",
        )
    else:
        out_df = out_df.sort_values(
            by=["is_valid", "proba_fraud"],
            ascending=[False, False],
            na_position="last",
        )

    out_df.to_csv(out_path, index=False)

    print("CSV scoreado guardado en:", out_path.resolve())
    print("Resumen:", summary)


if __name__ == "__main__":
    main()

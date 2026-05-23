from __future__ import annotations

import csv
import json
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.config import DOCS_DIR, MODEL_METADATA_PATH
from src.repositories.analytics_repository import (
    get_classification_summary_counts,
    get_risk_distribution_counts,
    list_fraud_evolution_by_day,
)
from src.repositories.policy_repository import get_active_policy


DEFAULT_POLICY_THRESHOLD = 0.02
HIGH_RISK_THRESHOLD = 0.5
DEFAULT_VARIABLE_IMPORTANCE = [
    {"feature": "V14", "importance": 0.31},
    {"feature": "V10", "importance": 0.27},
    {"feature": "V12", "importance": 0.24},
    {"feature": "Amount", "importance": 0.20},
    {"feature": "V17", "importance": 0.18},
    {"feature": "V4", "importance": 0.16},
    {"feature": "V11", "importance": 0.14},
    {"feature": "V3", "importance": 0.13},
    {"feature": "V16", "importance": 0.11},
    {"feature": "V2", "importance": 0.10},
]

FEATURE_COL_CANDIDATES = ("feature", "variable", "name", "column")
IMPORTANCE_COL_CANDIDATES = ("importance", "mean_abs_shap", "mean_abs_value", "value", "score")


def get_analytics_fraud_evolution(db: Session, *, days: int) -> dict:
    rows = list_fraud_evolution_by_day(db, days=days)
    points: list[dict] = []

    for row in rows:
        date_value = row["date"]
        points.append(
            {
                "date": date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value),
                "total_predictions": int(row["total_predictions"]),
                "review_count": int(row["review_count"]),
                "invalid_count": int(row["invalid_count"]),
            }
        )

    return {
        "period_days": int(days),
        "points": points,
    }


def get_analytics_risk_distribution(db: Session) -> dict:
    active_policy = get_active_policy(db)
    policy_threshold = float(active_policy.threshold_cost) if active_policy is not None else DEFAULT_POLICY_THRESHOLD

    counts = get_risk_distribution_counts(
        db,
        policy_threshold=policy_threshold,
        high_threshold=HIGH_RISK_THRESHOLD,
    )

    return {
        **counts,
        "thresholds": {
            "policy_threshold": policy_threshold,
            "high_threshold": HIGH_RISK_THRESHOLD,
        },
    }


def get_analytics_classification_summary(db: Session) -> dict:
    return get_classification_summary_counts(db)


def _parse_importance_csv(csv_path: Path) -> list[dict]:
    try:
        with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames or []
            if not fieldnames:
                return []

            field_map = {name.lower().strip(): name for name in fieldnames}

            feature_col = next(
                (field_map[candidate] for candidate in FEATURE_COL_CANDIDATES if candidate in field_map),
                None,
            )
            importance_col = next(
                (field_map[candidate] for candidate in IMPORTANCE_COL_CANDIDATES if candidate in field_map),
                None,
            )

            if feature_col is None or importance_col is None:
                if len(fieldnames) >= 2:
                    feature_col, importance_col = fieldnames[0], fieldnames[1]
                else:
                    return []

            items = []
            for row in reader:
                feature = str(row.get(feature_col, "")).strip()
                if not feature:
                    continue
                try:
                    importance = float(row.get(importance_col, ""))
                except (TypeError, ValueError):
                    continue
                items.append({"feature": feature, "importance": importance})

            return sorted(items, key=lambda item: item["importance"], reverse=True)
    except OSError:
        return []


def _load_from_shap_files(limit: int) -> list[dict]:
    csv_candidates = sorted(
        {
            *DOCS_DIR.glob("shap/*.csv"),
            *DOCS_DIR.glob("*shap*.csv"),
            *DOCS_DIR.glob("*importance*.csv"),
        }
    )

    for candidate in csv_candidates:
        items = _parse_importance_csv(candidate)
        if items:
            return items[:limit]

    return []


def _load_from_metadata(limit: int) -> list[dict]:
    if not MODEL_METADATA_PATH.exists():
        return []

    try:
        metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    raw_items = metadata.get("variable_importance")
    if isinstance(raw_items, list):
        parsed = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            feature = str(item.get("feature", "")).strip()
            if not feature:
                continue
            try:
                importance = float(item.get("importance"))
            except (TypeError, ValueError):
                continue
            parsed.append({"feature": feature, "importance": importance})
        return sorted(parsed, key=lambda item: item["importance"], reverse=True)[:limit]

    if isinstance(raw_items, dict):
        parsed = []
        for feature, value in raw_items.items():
            feature_name = str(feature).strip()
            if not feature_name:
                continue
            try:
                importance = float(value)
            except (TypeError, ValueError):
                continue
            parsed.append({"feature": feature_name, "importance": importance})
        return sorted(parsed, key=lambda item: item["importance"], reverse=True)[:limit]

    return []


def get_analytics_variable_importance(*, limit: int) -> dict:
    safe_limit = max(1, int(limit))

    shap_items = _load_from_shap_files(safe_limit)
    if shap_items:
        return {"source": "shap_file", "items": shap_items}

    metadata_items = _load_from_metadata(safe_limit)
    if metadata_items:
        return {"source": "metadata", "items": metadata_items}

    return {
        "source": "fallback",
        "items": DEFAULT_VARIABLE_IMPORTANCE[:safe_limit],
    }

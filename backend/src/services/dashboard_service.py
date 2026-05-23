from sqlalchemy.orm import Session

from src.repositories.dashboard_repository import (
    get_batch_job_counts,
    get_prediction_counts,
    list_priority_cases,
)
from src.repositories.model_repository import get_active_model_version
from src.repositories.policy_repository import get_active_policy


DEFAULT_POLICY = {
    "threshold_cost": 0.02,
    "max_alerts": 500,
    "priority_mode": "risk",
    "error_cost_mode": "balanced",
}


def get_dashboard_summary(db: Session) -> dict:
    prediction_counts = get_prediction_counts(db)
    batch_counts = get_batch_job_counts(db)
    active_policy = get_active_policy(db)
    active_model = get_active_model_version(db)

    policy_payload = (
        {
            "threshold_cost": float(active_policy.threshold_cost),
            "max_alerts": int(active_policy.max_alerts),
            "priority_mode": active_policy.priority_mode,
            "error_cost_mode": active_policy.error_cost_mode,
        }
        if active_policy is not None
        else DEFAULT_POLICY
    )

    model_payload = (
        {
            "id": active_model.id,
            "name": active_model.name,
            "model_type": active_model.model_type,
            "pr_auc": float(active_model.pr_auc),
            "brier_score": float(active_model.brier_score),
            "n_features": int(active_model.n_features),
            "created_at": active_model.created_at,
        }
        if active_model is not None
        else None
    )

    return {
        **prediction_counts,
        **batch_counts,
        "active_policy": policy_payload,
        "active_model": model_payload,
    }


def get_dashboard_priority_cases(
    db: Session,
    *,
    limit: int,
    offset: int,
    only_review: bool,
) -> list[dict]:
    rows = list_priority_cases(db, limit=limit, offset=offset, only_review=only_review)
    return [
        {
            "id": item.id,
            "batch_job_id": item.batch_job_id,
            "model_version_id": item.model_version_id,
            "transaction_id": item.transaction_id,
            "proba_fraud": item.proba_fraud,
            "review": bool(item.review),
            "rank": item.rank,
            "is_valid": bool(item.is_valid),
            "created_at": item.created_at,
        }
        for item in rows
    ]

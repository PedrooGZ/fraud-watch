from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from src.db.session import SessionLocal
from src.repositories.policy_repository import create_policy_history, get_active_policy, list_policy_history
from src.services.audit_service import write_audit_event_best_effort


def _load_policy_from_json(policy_path: Path) -> dict:
    policy = {"threshold_cost": 0.02, "max_alerts": 500}
    if policy_path.exists():
        try:
            policy.update(json.loads(policy_path.read_text(encoding="utf-8")))
        except Exception:
            pass
    policy["threshold_cost"] = float(policy["threshold_cost"])
    policy["max_alerts"] = int(policy["max_alerts"])
    return policy


def get_policy_with_fallback(policy_path: Path) -> dict:
    try:
        with SessionLocal() as db:
            active_policy = get_active_policy(db)
            if active_policy is not None:
                return {
                    "threshold_cost": float(active_policy.threshold_cost),
                    "max_alerts": int(active_policy.max_alerts),
                    "priority_mode": active_policy.priority_mode,
                    "error_cost_mode": active_policy.error_cost_mode,
                    "source": "database",
                }
    except SQLAlchemyError:
        pass
    except Exception:
        pass

    json_policy = _load_policy_from_json(policy_path)
    json_policy["source"] = "json_fallback"
    return json_policy


def update_active_policy(
    *,
    threshold_cost: float,
    max_alerts: int,
    priority_mode: str | None = None,
    error_cost_mode: str | None = None,
    reason: str | None = None,
) -> dict:
    with SessionLocal() as db:
        policy = get_active_policy(db)
        if policy is None:
            raise ValueError("No active policy found in database.")

        old_values = {
            "threshold_cost": float(policy.threshold_cost),
            "max_alerts": int(policy.max_alerts),
            "priority_mode": policy.priority_mode,
            "error_cost_mode": policy.error_cost_mode,
        }

        policy.threshold_cost = float(threshold_cost)
        policy.max_alerts = int(max_alerts)
        if priority_mode is not None:
            policy.priority_mode = priority_mode
        if error_cost_mode is not None:
            policy.error_cost_mode = error_cost_mode

        new_values = {
            "threshold_cost": float(policy.threshold_cost),
            "max_alerts": int(policy.max_alerts),
            "priority_mode": policy.priority_mode,
            "error_cost_mode": policy.error_cost_mode,
        }

        create_policy_history(
            db,
            policy_id=policy.id,
            changed_by_user_id=None,
            old_values_json=old_values,
            new_values_json=new_values,
            reason=reason,
        )

        db.commit()
        db.refresh(policy)

    write_audit_event_best_effort(
        event_type="POLICY_UPDATED",
        entity_type="policy",
        entity_id=str(policy.id),
        details_json={
            "old_values_json": old_values,
            "new_values_json": new_values,
            "reason": reason,
        },
        user_id=None,
    )

    return {
        "id": policy.id,
        "threshold_cost": float(policy.threshold_cost),
        "max_alerts": int(policy.max_alerts),
        "priority_mode": policy.priority_mode,
        "error_cost_mode": policy.error_cost_mode,
        "is_active": bool(policy.is_active),
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
    }


def get_policy_history(*, limit: int, offset: int) -> list:
    with SessionLocal() as db:
        return list_policy_history(db, limit=limit, offset=offset)

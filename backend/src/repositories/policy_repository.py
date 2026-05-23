from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.db.models import Policy, PolicyHistory


def get_active_policy(db: Session) -> Policy | None:
    stmt = (
        select(Policy)
        .where(Policy.is_active.is_(True))
        .order_by(Policy.updated_at.desc(), Policy.created_at.desc())
    )
    return db.scalar(stmt)


def create_policy_history(
    db: Session,
    *,
    policy_id: int,
    old_values_json: dict,
    new_values_json: dict,
    reason: str | None,
    changed_by_user_id: int | None = None,
) -> PolicyHistory:
    history = PolicyHistory(
        policy_id=policy_id,
        changed_by_user_id=changed_by_user_id,
        old_values_json=old_values_json,
        new_values_json=new_values_json,
        reason=reason,
    )
    db.add(history)
    return history


def list_policy_history(db: Session, *, limit: int, offset: int) -> list[PolicyHistory]:
    stmt = (
        select(PolicyHistory)
        .order_by(desc(PolicyHistory.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())

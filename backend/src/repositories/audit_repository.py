from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.db.models import AuditEvent


def create_audit_event(
    db: Session,
    *,
    user_id: int | None,
    event_type: str,
    entity_type: str | None,
    entity_id: str | None,
    details_json: dict | list | None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=details_json,
    )
    db.add(event)
    return event


def list_audit_events(
    db: Session,
    *,
    limit: int,
    offset: int,
    event_type: str | None = None,
    entity_type: str | None = None,
) -> list[AuditEvent]:
    stmt = select(AuditEvent)
    if event_type is not None:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    if entity_type is not None:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    stmt = stmt.order_by(desc(AuditEvent.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())

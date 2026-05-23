from __future__ import annotations

import logging

from sqlalchemy.exc import SQLAlchemyError

from src.db.session import SessionLocal
from src.repositories.audit_repository import create_audit_event

logger = logging.getLogger(__name__)


def write_audit_event_best_effort(
    *,
    event_type: str,
    entity_type: str | None,
    entity_id: str | None,
    details_json: dict | list | None,
    user_id: int | None = None,
) -> None:
    try:
        with SessionLocal() as db:
            create_audit_event(
                db,
                user_id=user_id,
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                details_json=details_json,
            )
            db.commit()
    except SQLAlchemyError as exc:
        logger.warning("No se pudo registrar audit_event (%s): %s", event_type, exc)
    except Exception as exc:
        logger.warning("Error inesperado registrando audit_event (%s): %s", event_type, exc)

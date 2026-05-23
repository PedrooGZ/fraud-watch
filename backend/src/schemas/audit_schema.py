from datetime import datetime

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: int
    user_id: int | None
    event_type: str
    entity_type: str | None
    entity_id: str | None
    details_json: dict | list | None
    created_at: datetime

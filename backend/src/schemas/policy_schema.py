from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PolicyResponse(BaseModel):
    threshold_cost: float
    max_alerts: int
    priority_mode: str | None = None
    error_cost_mode: str | None = None
    source: str | None = None


class PolicyUpdateRequest(BaseModel):
    threshold_cost: float = Field(..., ge=0.0, le=1.0)
    max_alerts: int = Field(..., ge=0)
    priority_mode: Literal["risk", "impact", "mixed"] | None = None
    error_cost_mode: Literal["balanced", "reduce_fp", "reduce_fn"] | None = None
    reason: str | None = None


class PolicyHistoryResponse(BaseModel):
    id: int
    policy_id: int
    changed_by_user_id: int | None
    old_values_json: dict
    new_values_json: dict
    reason: str | None
    created_at: datetime

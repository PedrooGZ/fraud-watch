from datetime import datetime

from pydantic import BaseModel


class DriftRunResponse(BaseModel):
    id: int
    psi: float
    status: str
    bins: int
    sample_size: int
    amount_multiplier: float
    ref_mean: float
    ref_p95: float
    new_mean: float
    new_p95: float
    summary_path: str | None
    created_at: datetime

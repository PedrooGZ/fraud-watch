from datetime import datetime

from pydantic import BaseModel


class PredictionSummaryResponse(BaseModel):
    id: int
    batch_job_id: int | None
    model_version_id: int | None
    transaction_id: str | None
    proba_fraud: float | None
    review: bool
    rank: int | None
    is_valid: bool
    missing_features_json: list[str] | dict | None
    created_at: datetime


class PredictionDetailResponse(PredictionSummaryResponse):
    input_features_json: dict

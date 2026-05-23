from datetime import datetime

from pydantic import BaseModel


class BatchJobResponse(BaseModel):
    id: int
    filename: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    review_count: int
    error_message: str | None
    created_at: datetime
    finished_at: datetime | None


class BatchUploadPreviewItem(BaseModel):
    index: int
    proba_fraud: float | None
    review: bool
    rank: int | None
    is_valid: bool
    missing_features: list[str] | None


class BatchUploadResponse(BaseModel):
    batch_job_id: int
    filename: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    review_count: int
    threshold_cost: float
    max_alerts: int
    results_preview: list[BatchUploadPreviewItem]

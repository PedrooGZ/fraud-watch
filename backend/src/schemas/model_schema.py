from datetime import datetime

from pydantic import BaseModel


class ModelVersionResponse(BaseModel):
    id: int
    name: str
    model_type: str
    artifact_path: str
    metadata_path: str
    pr_auc: float
    brier_score: float
    n_features: int
    is_active: bool
    created_at: datetime

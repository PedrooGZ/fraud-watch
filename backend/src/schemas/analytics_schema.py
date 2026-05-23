from pydantic import BaseModel


class AnalyticsFraudEvolutionPoint(BaseModel):
    date: str
    total_predictions: int
    review_count: int
    invalid_count: int


class AnalyticsFraudEvolutionResponse(BaseModel):
    period_days: int
    points: list[AnalyticsFraudEvolutionPoint]


class AnalyticsRiskDistributionThresholds(BaseModel):
    policy_threshold: float
    high_threshold: float


class AnalyticsRiskDistributionResponse(BaseModel):
    low: int
    medium: int
    high: int
    total: int
    thresholds: AnalyticsRiskDistributionThresholds


class AnalyticsClassificationSummaryResponse(BaseModel):
    review: int
    no_review: int
    invalid: int
    total: int


class AnalyticsVariableImportanceItem(BaseModel):
    feature: str
    importance: float


class AnalyticsVariableImportanceResponse(BaseModel):
    source: str
    items: list[AnalyticsVariableImportanceItem]

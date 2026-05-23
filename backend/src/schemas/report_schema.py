from datetime import datetime

from pydantic import BaseModel, field_validator

ALLOWED_REPORT_SECTIONS = {
    "summary",
    "analytics",
    "drift",
    "model",
    "policy_changes",
    "audit",
    "batch_jobs",
}


class ReportResponse(BaseModel):
    id: int
    report_code: str
    period: str
    format: str
    detail_level: str
    sections_json: list | dict
    file_path: str | None
    generated_by_user_id: int | None
    created_at: datetime


class ReportCreateRequest(BaseModel):
    period: str = "last_30_days"
    format: str = "json"
    detail_level: str = "executive"
    sections: list[str]

    @field_validator("format")
    @classmethod
    def validate_format(cls, value: str) -> str:
        allowed = {"json", "csv"}
        if value not in allowed:
            raise ValueError(f"format must be one of: {sorted(allowed)}.")
        return value

    @field_validator("detail_level")
    @classmethod
    def validate_detail_level(cls, value: str) -> str:
        allowed = {"executive", "operational", "complete"}
        if value not in allowed:
            raise ValueError(f"detail_level must be one of: {sorted(allowed)}.")
        return value

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        allowed = {"today", "last_7_days", "last_30_days", "all"}
        if value not in allowed:
            raise ValueError(f"period must be one of: {sorted(allowed)}.")
        return value

    @field_validator("sections")
    @classmethod
    def validate_sections(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("sections cannot be empty.")
        unknown = [item for item in value if item not in ALLOWED_REPORT_SECTIONS]
        if unknown:
            raise ValueError(f"Unknown sections: {unknown}.")
        return value

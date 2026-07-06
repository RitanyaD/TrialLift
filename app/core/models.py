from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field

from app.core.config import DEFAULT_COMPANY_PROFILE


Intent = Literal["funnel", "cohort", "feature_usage", "monetization", "experiment", "fallback"]


class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=3)
    company_profile: dict[str, Any] = Field(default_factory=lambda: DEFAULT_COMPANY_PROFILE.copy())


class AnalyzeResponse(BaseModel):
    question: str
    intent: Intent
    selected_agent: str
    sql: str | None
    rows: list[dict[str, Any]]
    answer: str
    token_usage: dict[str, int]
    errors: list[str]


class TrialLiftState(TypedDict, total=False):
    question: str
    company_profile: dict[str, Any]
    intent: Intent
    selected_agent: str
    sql: str
    rows: list[dict[str, Any]]
    answer: str
    token_usage: dict[str, int]
    errors: list[str]
    retry_count: int
    _started_at: int

from fastapi import FastAPI

from app.core.config import DEFAULT_COMPANY_PROFILE
from app.core.models import AnalyzeRequest, AnalyzeResponse
from app.core.supervisor import analyze_question
from app.data.database import fetch_all, get_connection, initialize_database


app = FastAPI(
    title="TrialLift API",
    description="Multi-agent SaaS trial conversion analytics API.",
    version="1.0.0",
)


@app.on_event("startup")
def startup() -> None:
    with get_connection() as connection:
        initialize_database(connection)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/company-profile")
def company_profile() -> dict:
    return DEFAULT_COMPANY_PROFILE


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    result = analyze_question(
        {
            "question": request.question,
            "company_profile": request.company_profile,
        }
    )
    return AnalyzeResponse(
        question=result["question"],
        intent=result.get("intent", "fallback"),
        selected_agent=result.get("selected_agent", "unknown"),
        sql=result.get("sql"),
        rows=result.get("rows", []),
        answer=result.get("answer", ""),
        token_usage=result.get("token_usage", {}),
        errors=result.get("errors", []),
    )


@app.get("/metrics/overview")
def metrics_overview() -> dict:
    with get_connection() as connection:
        rows = fetch_all(
            connection,
            """
            SELECT
                COUNT(DISTINCT organization_id) AS trials,
                SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid_customers,
                ROUND(100.0 * SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) / COUNT(*), 1) AS conversion_rate
            FROM subscriptions
            """,
        )
    return rows[0] if rows else {"trials": 0, "paid_customers": 0, "conversion_rate": 0}


@app.get("/logs")
def logs() -> list[dict]:
    with get_connection() as connection:
        return fetch_all(
            connection,
            """
            SELECT question, intent, selected_agent, token_estimate, latency_ms, created_at
            FROM analytics_logs
            ORDER BY id DESC
            LIMIT 20
            """,
        )

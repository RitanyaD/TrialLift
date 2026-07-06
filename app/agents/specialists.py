from typing import Any

from app.agents.query_templates import (
    COHORT_SQL,
    EXPERIMENT_SQL,
    FEATURE_USAGE_SQL,
    FUNNEL_SQL,
    MONETIZATION_SQL,
)
from app.core.models import TrialLiftState
from app.core.token_usage import add_token_usage


def intent_agent(state: TrialLiftState) -> TrialLiftState:
    question = state["question"].lower()
    intent = "fallback"
    if any(word in question for word in ["funnel", "drop", "convert", "conversion", "trial"]):
        intent = "funnel"
    if any(word in question for word in ["cohort", "segment", "smb", "mid-market", "enterprise"]):
        intent = "cohort"
    if any(word in question for word in ["feature", "usage", "activation", "integration", "invite"]):
        intent = "feature_usage"
    if any(word in question for word in ["pricing", "checkout", "paid", "plan", "monetization", "revenue"]):
        intent = "monetization"
    if any(word in question for word in ["experiment", "ab test", "a/b", "recommend"]):
        intent = "experiment"

    return {
        **state,
        "intent": intent,
        "token_usage": add_token_usage(state.get("token_usage"), "intent_agent", state["question"]),
    }


def funnel_agent(state: TrialLiftState) -> TrialLiftState:
    return _with_sql(state, "funnel_analyst_agent", FUNNEL_SQL)


def cohort_agent(state: TrialLiftState) -> TrialLiftState:
    return _with_sql(state, "cohort_analyst_agent", COHORT_SQL)


def feature_usage_agent(state: TrialLiftState) -> TrialLiftState:
    return _with_sql(state, "feature_usage_agent", FEATURE_USAGE_SQL)


def monetization_agent(state: TrialLiftState) -> TrialLiftState:
    return _with_sql(state, "monetization_agent", MONETIZATION_SQL)


def experiment_agent(state: TrialLiftState) -> TrialLiftState:
    return _with_sql(state, "experiment_recommendation_agent", EXPERIMENT_SQL)


def fallback_agent(state: TrialLiftState) -> TrialLiftState:
    answer = (
        "I could not map the question to one specialist, so start with the trial funnel, "
        "then compare activated vs non-activated accounts. The strongest TrialLift signal is usually whether "
        "a company reached the activation goal from the company profile."
    )
    return {
        **state,
        "selected_agent": "fallback_agent",
        "rows": [],
        "answer": answer,
        "errors": [*state.get("errors", []), "Fallback route used."],
        "token_usage": add_token_usage(state.get("token_usage"), "fallback_agent", state["question"], answer),
    }


def summarize_answer(state: TrialLiftState) -> TrialLiftState:
    rows = state.get("rows", [])
    profile = state.get("company_profile", {})
    intent = state.get("intent", "fallback")
    answer = _build_answer(intent, rows, profile)
    return {
        **state,
        "answer": answer,
        "token_usage": add_token_usage(state.get("token_usage"), "answer_summarizer", state["question"], answer),
    }


def _with_sql(state: TrialLiftState, agent_name: str, sql: str) -> TrialLiftState:
    return {
        **state,
        "selected_agent": agent_name,
        "sql": sql.strip(),
        "token_usage": add_token_usage(state.get("token_usage"), agent_name, state["question"], sql),
    }


def _build_answer(intent: str, rows: list[dict[str, Any]], profile: dict[str, Any]) -> str:
    activation_goal = profile.get("activation_goal", "the activation goal")
    if not rows:
        return "No rows were returned. Check whether the database has been seeded."

    if intent == "funnel":
        weakest = min(rows[1:], key=lambda row: row["pct_of_signups"]) if len(rows) > 1 else rows[0]
        return (
            f"The biggest conversion concern is around `{weakest['event_name']}`, where only "
            f"{weakest['pct_of_signups']}% of signup organizations remain. Because activation is defined as "
            f"{activation_goal}, prioritize onboarding nudges that move users into that behavior before pricing."
        )
    if intent == "cohort":
        best = max(rows, key=lambda row: row["conversion_rate"])
        worst = min(rows, key=lambda row: row["conversion_rate"])
        return (
            f"{best['segment']} in {best['signup_month']} converts best at {best['conversion_rate']}%, while "
            f"{worst['segment']} in {worst['signup_month']} converts lowest at {worst['conversion_rate']}%. "
            "Use this to tailor lifecycle messaging by segment instead of sending one generic trial sequence."
        )
    if intent == "feature_usage":
        top = rows[0]
        return (
            f"`{top['feature_name']}` has the largest paid-vs-unpaid usage gap at {top['usage_gap']} actions. "
            f"This suggests the activation path should push users toward {activation_goal} earlier in the trial."
        )
    if intent == "monetization":
        top = rows[0]
        return (
            f"The `{top['plan_name']}` plan has the strongest observed conversion rate at {top['conversion_rate']}%. "
            "Compare pricing-page views to checkout starts to find whether the leak is value communication or purchase friction."
        )
    if intent == "experiment":
        experiment = rows[0]
        return (
            f"Recommended next experiment: `{experiment['name']}` for {experiment['target_segment']}. "
            f"Hypothesis: {experiment['hypothesis']} Track `{experiment['metric']}` as the primary metric."
        )
    return "Start with funnel conversion, then inspect feature usage for activated versus non-activated trials."

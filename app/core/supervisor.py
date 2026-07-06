from langgraph.graph import END, StateGraph

from app.agents.specialists import (
    cohort_agent,
    experiment_agent,
    fallback_agent,
    feature_usage_agent,
    funnel_agent,
    intent_agent,
    monetization_agent,
    summarize_answer,
)
from app.agents.sql_validator import validate_readonly_sql
from app.core.analytics_logger import log_interaction, now_ms
from app.core.models import TrialLiftState
from app.core.token_usage import add_token_usage
from app.data.database import fetch_all, get_connection


def route_by_intent(state: TrialLiftState) -> str:
    routes = {
        "funnel": "funnel_agent",
        "cohort": "cohort_agent",
        "feature_usage": "feature_usage_agent",
        "monetization": "monetization_agent",
        "experiment": "experiment_agent",
    }
    return routes.get(state.get("intent", "fallback"), "fallback_agent")


def validate_sql_node(state: TrialLiftState) -> TrialLiftState:
    sql = state.get("sql", "")
    is_valid, error = validate_readonly_sql(sql)
    if is_valid:
        return {
            **state,
            "token_usage": add_token_usage(state.get("token_usage"), "sql_validator_agent", sql),
        }

    errors = [*state.get("errors", []), error or "Invalid SQL."]
    retry_count = state.get("retry_count", 0) + 1
    return {
        **state,
        "errors": errors,
        "retry_count": retry_count,
        "token_usage": add_token_usage(state.get("token_usage"), "sql_validator_agent", sql, error or ""),
    }


def after_validation(state: TrialLiftState) -> str:
    if "sql" not in state:
        return "fallback_agent"
    if state.get("retry_count", 0) > 0:
        return "fallback_agent"
    return "execute_sql"


def execute_sql_node(state: TrialLiftState) -> TrialLiftState:
    with get_connection() as connection:
        rows = fetch_all(connection, state["sql"])
    return {**state, "rows": rows}


def log_node(state: TrialLiftState) -> TrialLiftState:
    token_total = sum(state.get("token_usage", {}).values())
    started_at = state.get("_started_at", now_ms())
    latency_ms = max(1, now_ms() - started_at)
    log_interaction(
        question=state["question"],
        intent=state.get("intent", "fallback"),
        selected_agent=state.get("selected_agent", "unknown"),
        token_estimate=token_total,
        latency_ms=latency_ms,
    )
    return state


def build_graph():
    graph = StateGraph(TrialLiftState)
    graph.add_node("intent_agent", intent_agent)
    graph.add_node("funnel_agent", funnel_agent)
    graph.add_node("cohort_agent", cohort_agent)
    graph.add_node("feature_usage_agent", feature_usage_agent)
    graph.add_node("monetization_agent", monetization_agent)
    graph.add_node("experiment_agent", experiment_agent)
    graph.add_node("fallback_agent", fallback_agent)
    graph.add_node("validate_sql", validate_sql_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("summarize_answer", summarize_answer)
    graph.add_node("log_interaction", log_node)

    graph.set_entry_point("intent_agent")
    graph.add_conditional_edges("intent_agent", route_by_intent)

    for node in [
        "funnel_agent",
        "cohort_agent",
        "feature_usage_agent",
        "monetization_agent",
        "experiment_agent",
    ]:
        graph.add_edge(node, "validate_sql")

    graph.add_conditional_edges("validate_sql", after_validation)
    graph.add_edge("execute_sql", "summarize_answer")
    graph.add_edge("summarize_answer", "log_interaction")
    graph.add_edge("fallback_agent", "log_interaction")
    graph.add_edge("log_interaction", END)
    return graph.compile()


triallift_graph = build_graph()


def analyze_question(state: TrialLiftState) -> TrialLiftState:
    return triallift_graph.invoke({**state, "_started_at": now_ms(), "token_usage": {}, "errors": [], "retry_count": 0})

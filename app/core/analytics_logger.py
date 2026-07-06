import time

from app.data.database import execute_write, get_connection


def now_ms() -> int:
    return int(time.perf_counter() * 1000)


def log_interaction(question: str, intent: str, selected_agent: str, token_estimate: int, latency_ms: int) -> None:
    with get_connection() as connection:
        execute_write(
            connection,
            """
            INSERT INTO analytics_logs (question, intent, selected_agent, token_estimate, latency_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (question, intent, selected_agent, token_estimate, latency_ms),
        )

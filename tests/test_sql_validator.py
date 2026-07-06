from app.agents.sql_validator import validate_readonly_sql


def test_allows_select_query() -> None:
    is_valid, error = validate_readonly_sql("SELECT * FROM events LIMIT 5")
    assert is_valid is True
    assert error is None


def test_blocks_delete_query() -> None:
    is_valid, error = validate_readonly_sql("DELETE FROM events")
    assert is_valid is False
    assert "Only SELECT" in error


def test_blocks_keyword_inside_cte() -> None:
    is_valid, error = validate_readonly_sql("WITH x AS (SELECT 1) DROP TABLE users")
    assert is_valid is False
    assert "drop" in error

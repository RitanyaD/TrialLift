from app.agents.specialists import intent_agent


def test_routes_feature_usage_question() -> None:
    state = intent_agent({"question": "Which features are tied to activation?", "token_usage": {}})
    assert state["intent"] == "feature_usage"


def test_routes_experiment_question() -> None:
    state = intent_agent({"question": "Recommend an experiment to improve conversion", "token_usage": {}})
    assert state["intent"] == "experiment"

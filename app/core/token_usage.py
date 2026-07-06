def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()) + len(text) // 12)


def add_token_usage(current: dict[str, int] | None, agent_name: str, *texts: str) -> dict[str, int]:
    usage = dict(current or {})
    usage[agent_name] = usage.get(agent_name, 0) + sum(estimate_tokens(text) for text in texts)
    return usage

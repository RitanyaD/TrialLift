import re


BLOCKED_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "attach",
    "detach",
    "pragma",
}


def validate_readonly_sql(sql: str) -> tuple[bool, str | None]:
    normalized = re.sub(r"\s+", " ", sql.strip().lower())
    if not normalized.startswith("select") and not normalized.startswith("with"):
        return False, "Only SELECT analytics queries are allowed."
    if ";" in normalized[:-1]:
        return False, "Multiple SQL statements are not allowed."
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", normalized):
            return False, f"Blocked unsafe SQL keyword: {keyword}."
    return True, None

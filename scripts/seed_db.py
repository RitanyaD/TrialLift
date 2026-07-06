from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

from app.core.config import DB_PATH
from app.data.database import get_connection, initialize_database


EVENT_SEQUENCE = [
    "signed_up",
    "created_workspace",
    "invited_teammate",
    "connected_integration",
    "created_project",
    "exported_report",
    "viewed_pricing",
    "started_checkout",
    "upgraded_to_paid",
]


def reset_database(connection: sqlite3.Connection) -> None:
    for table in [
        "analytics_logs",
        "experiments",
        "feature_usage",
        "events",
        "subscriptions",
        "plans",
        "users",
        "organizations",
    ]:
        connection.execute(f"DROP TABLE IF EXISTS {table}")
    connection.commit()
    initialize_database(connection)


def choose_trial_events(segment: str) -> tuple[list[str], bool, bool]:
    activation_score = 0
    converted = False
    cancelled = False
    selected_events = EVENT_SEQUENCE[:2]

    if random.random() < (0.75 if segment != "Enterprise" else 0.65):
        selected_events.append("invited_teammate")
        activation_score += 1
    if random.random() < (0.64 if segment == "Mid-Market" else 0.48):
        selected_events.append("connected_integration")
        activation_score += 1
    if random.random() < 0.58:
        selected_events.append("created_project")
        activation_score += 1
    if random.random() < 0.38:
        selected_events.append("exported_report")
        activation_score += 1
    if random.random() < 0.44:
        selected_events.append("viewed_pricing")
    if random.random() < 0.28 + (activation_score * 0.09):
        selected_events.append("started_checkout")
    if "started_checkout" in selected_events and random.random() < 0.58 + (activation_score * 0.05):
        selected_events.append("upgraded_to_paid")
        converted = True
    elif random.random() < 0.3:
        selected_events.append("cancelled_trial")
        cancelled = True

    return selected_events, converted, cancelled


def build_mock_rows() -> tuple[list, list, list, list, list]:
    segments = ["SMB", "Mid-Market", "Enterprise"]
    industries = ["Marketing", "Finance", "Healthcare", "Education", "Developer Tools"]
    channels = ["organic", "paid_search", "partner", "content", "sales_outbound"]
    base_day = date(2026, 1, 1)

    org_rows = []
    user_rows = []
    subscription_rows = []
    event_rows = []
    feature_rows = []

    event_id = 1
    user_id = 1

    for org_id in range(1, 91):
        segment = random.choices(segments, weights=[50, 35, 15], k=1)[0]
        created_at = base_day + timedelta(days=random.randint(0, 120))
        org_rows.append((org_id, f"Company {org_id}", segment, random.choice(industries), created_at.isoformat()))

        user_rows.append(
            (
                user_id,
                org_id,
                f"user{user_id}@company{org_id}.com",
                random.choice(["founder", "ops_lead", "analyst", "product_manager"]),
                created_at.isoformat(),
                random.choice(channels),
            )
        )

        selected_events, converted, cancelled = choose_trial_events(segment)
        for offset, event_name in enumerate(selected_events):
            event_rows.append((event_id, user_id, org_id, event_name, (created_at + timedelta(days=offset + 1)).isoformat(), "{}"))
            event_id += 1

        trial_end = created_at + timedelta(days=14)
        converted_at = (created_at + timedelta(days=random.randint(5, 13))).isoformat() if converted else None
        cancelled_at = trial_end.isoformat() if cancelled else None
        status = "paid" if converted else "cancelled" if cancelled else "trial_expired"
        subscription_rows.append(
            (org_id, org_id, random.choice([1, 2, 2, 3]), status, created_at.isoformat(), trial_end.isoformat(), converted_at, cancelled_at)
        )

        feature_rows.extend(
            [
                (None, org_id, "team_invites", random.randint(0, 12), random.randint(0, 8), (created_at + timedelta(days=7)).isoformat()),
                (None, org_id, "integrations", random.randint(0, 7), random.randint(0, 6), (created_at + timedelta(days=8)).isoformat()),
                (None, org_id, "projects", random.randint(0, 18), random.randint(1, 10), (created_at + timedelta(days=9)).isoformat()),
                (None, org_id, "report_exports", random.randint(0, 9), random.randint(0, 5), (created_at + timedelta(days=10)).isoformat()),
            ]
        )
        user_id += 1

    return org_rows, user_rows, subscription_rows, event_rows, feature_rows


def seed() -> None:
    random.seed(42)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection(DB_PATH)
    reset_database(connection)

    connection.executemany(
        "INSERT INTO plans VALUES (?, ?, ?, ?)",
        [
            (1, "Starter", 29, 5),
            (2, "Growth", 99, 25),
            (3, "Enterprise", 299, 100),
        ],
    )

    org_rows, user_rows, subscription_rows, event_rows, feature_rows = build_mock_rows()
    connection.executemany("INSERT INTO organizations VALUES (?, ?, ?, ?, ?)", org_rows)
    connection.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", user_rows)
    connection.executemany("INSERT INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", subscription_rows)
    connection.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)", event_rows)
    connection.executemany("INSERT INTO feature_usage VALUES (?, ?, ?, ?, ?, ?)", feature_rows)
    connection.executemany(
        "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "Activation Checklist", "Guided setup will increase integration completion.", "SMB", "planned", "activation_rate"),
            (2, "Pricing Nudge", "Showing ROI proof before checkout will increase paid conversion.", "Mid-Market", "planned", "checkout_conversion"),
            (3, "Team Invite Prompt", "Earlier team invite prompts will increase activation.", "All", "running", "invite_rate"),
        ],
    )
    connection.commit()
    connection.close()
    print(f"Seeded TrialLift database at {DB_PATH}")


if __name__ == "__main__":
    seed()

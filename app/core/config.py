from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "triallift.db"


DEFAULT_COMPANY_PROFILE = {
    "business_model": "B2B SaaS",
    "trial_length_days": 14,
    "activation_goal": "connected_integration + invited_teammate",
    "pricing_plans": ["Starter", "Growth", "Enterprise"],
    "key_features": [
        "workspace creation",
        "team invites",
        "integrations",
        "project creation",
        "report export",
    ],
    "target_customer_segment": "SMB and mid-market teams",
}

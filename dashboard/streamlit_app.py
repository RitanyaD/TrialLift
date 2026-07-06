import requests
import streamlit as st


API_URL = "http://localhost:8000"


st.set_page_config(page_title="TrialLift", layout="wide")
st.title("TrialLift")
st.caption("Multi-agent SaaS trial conversion analyst")

with st.sidebar:
    st.header("Company Profile")
    business_model = st.selectbox("Business model", ["B2B SaaS", "B2C SaaS"])
    trial_length = st.selectbox("Trial length", [7, 14, 30], index=1)
    activation_goal = st.text_input("Activation goal", "connected_integration + invited_teammate")
    target_segment = st.text_input("Target segment", "SMB and mid-market teams")

profile = {
    "business_model": business_model,
    "trial_length_days": trial_length,
    "activation_goal": activation_goal,
    "pricing_plans": ["Starter", "Growth", "Enterprise"],
    "key_features": ["team_invites", "integrations", "projects", "report_exports"],
    "target_customer_segment": target_segment,
}

question = st.text_input("Ask TrialLift", "Why are trial users not converting?")

if st.button("Analyze", type="primary"):
    response = requests.post(f"{API_URL}/analyze", json={"question": question, "company_profile": profile}, timeout=20)
    response.raise_for_status()
    result = response.json()

    st.subheader("Recommendation")
    st.write(result["answer"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Intent", result["intent"])
    col2.metric("Agent", result["selected_agent"])
    col3.metric("Token Estimate", sum(result["token_usage"].values()))

    if result["rows"]:
        st.subheader("Evidence")
        st.dataframe(result["rows"], use_container_width=True)

    with st.expander("SQL and routing details"):
        st.code(result.get("sql") or "No SQL generated", language="sql")
        st.json(result["token_usage"])
        if result["errors"]:
            st.warning(result["errors"])

st.divider()

try:
    overview = requests.get(f"{API_URL}/metrics/overview", timeout=5).json()
    logs = requests.get(f"{API_URL}/logs", timeout=5).json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Trials", overview["trials"])
    c2.metric("Paid Customers", overview["paid_customers"])
    c3.metric("Conversion Rate", f"{overview['conversion_rate']}%")
    st.subheader("Recent Agent Runs")
    st.dataframe(logs, use_container_width=True)
except requests.RequestException:
    st.info("Start the FastAPI server to load metrics and recent agent runs.")

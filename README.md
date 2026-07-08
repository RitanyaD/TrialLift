# TrialLift
```text
TrialLift is a multi-agent platform for SaaS teams that identifies why trial users fail to convert to paid customers.

It uses a LangGraph supervisor to route product analytics questions to specialist agents for 
i)funnel analysis
ii)cohort comparison
iii)feature usage analysis
1v)monetization opportunity detection
v)experiment recommendation. 
The system validates SQL before execution, logs token usage and user interactions, and uses a configurable company profile to personalize recommendations.
```
## Example request flow
```text
TrialLift follows a full-stack analytics pipeline. The user interacts with a Streamlit frontend, while the backend handles API requests, multi-agent routing, SQL validation, database querying, and analytics logging.

User opens Streamlit dashboard
  ↓
User asks: "Why are trial users not converting?"
  ↓
Dashboard sends request to FastAPI
  ↓
FastAPI calls the LangGraph supervisor
  ↓
Intent Agent classifies the question as "funnel"
  ↓
Supervisor routes the request to the Funnel Analyst Agent
  ↓
Funnel Analyst Agent selects the funnel analysis SQL query
  ↓
SQL Validator Agent checks that the query is read-only and safe
  ↓
SQLite database runs the approved query
  ↓
Summarizer converts query results into a business recommendation
  ↓
Analytics Logger records intent, selected agent, token estimate, and latency
  ↓
FastAPI returns the final response
  ↓
Dashboard displays the answer, evidence table, SQL, and token usage
```
## Multi-Agent Pattern
```text
TrialLift uses a supervisor orchestration pattern.

i)The supervisor/intent agent inspects the user's question
ii)routes it to the best specialist agent
iii)validates SQL before execution
iv)retries invalid agent output once, and falls back to a general analytics agent if routing fails.

## How The Components Work Together
The frontend dashboard is responsible for collecting the user's question and company profile. It does not directly access the database or run agents. Instead, it sends the request to the FastAPI backend.
FastAPI acts as the application server. It receives the request, validates the input, calls the LangGraph workflow, and returns a structured response to the dashboard.
LangGraph acts as the multi-agent orchestration layer. The supervisor first calls the Intent Agent to understand the question, then routes the request to the correct specialist agent.
| Agent | Responsibility |
| --- | --- |
| Intent Agent | Classifies the user's analytics question |
| Funnel Analyst Agent | Finds conversion drop-offs across trial funnel events |
| Cohort Analyst Agent | Compares conversion by signup cohort and segment |
| Feature Usage Agent | Analyzes feature adoption and activation behavior |
| Monetization Agent | Finds pricing, checkout, and plan upgrade opportunities |
| Experiment Recommendation Agent | Suggests A/B tests based on analytics findings |
| SQL Validator Agent | Blocks unsafe SQL and allows only read-only analytics queries |
| Fallback Agent | Produces a general answer when specialist routing fails |

After the specialist agent selects an analytics query, the SQL Validator Agent checks that the query is safe and read-only. The backend then runs the query against the SQLite product analytics database.
Finally, the system summarizes the results into a business recommendation and logs the interaction. The logger records the question, detected intent, selected agent, estimated token usage, and response latency. This makes the system easier to debug and demonstrates cost-awareness.
```
## State Management

TrialLift starts with shared global state because the capstone uses a supervisor pattern with a controlled set of agents.

Each agent can read the full graph state, but writes only to specific keys:

| State Key | Written By |
| --- | --- |
| `question` | API layer |
| `company_profile` | API layer |
| `intent` | Intent Agent |
| `sql` | Specialist agents |
| `rows` | SQL execution step |
| `answer` | Specialist or fallback agent |
| `token_usage` | Supervisor and logger |
| `errors` | Validator, retry, and fallback steps |

## Failure Handling

TrialLift includes three failure-handling mechanisms:

1. SQL validation blocks destructive queries.
2. Invalid outputs are retried once with a stricter prompt.
3. A fallback analytics agent responds if a specialist route fails.

## Token and Cost Controls
TrialLift includes:
- deterministic SQL templates for common analytics questions
- short agent prompts
- route-first orchestration to avoid calling every agent
- token usage estimation per request
- persistent analytics logs for question, intent, latency, token estimate, and selected agent

## Dataset

The mock SaaS dataset includes:

- `users`
- `organizations`
- `plans`
- `subscriptions`
- `events`
- `feature_usage`
- `experiments`
- `analytics_logs`

Example events include:

- `signed_up`
- `created_workspace`
- `invited_teammate`
- `connected_integration`
- `created_project`
- `exported_report`
- `viewed_pricing`
- `started_checkout`
- `upgraded_to_paid`
- `cancelled_trial`

## Run Locally

Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Seed the database:

```bash
python scripts/seed_db.py
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Open the dashboard:

```bash
streamlit run dashboard/streamlit_app.py
```
```text
Frontend app open at:
http://localhost:8501
The API will be at:
http://localhost:8000
Quick check that backend is alive:
http://localhost:8000/health
```
## Example Questions

- Why are trial users not converting?
- Compare conversion for SMB and mid-market cohorts.
- Which features are most associated with paid upgrades?
- Where is the checkout funnel leaking?
- Recommend experiments to improve trial conversion.

## API Example

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Why are trial users not converting?\"}"
```

## Project Structure

```text
app/
  agents/
  core/
  data/
  main.py
dashboard/
scripts/
tests/
```


# 💰 Autonomous AI Revenue Recovery Agent

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange?style=for-the-badge&logo=google)](https://ai.google.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?style=for-the-badge&logo=postgresql)](https://postgresql.org)
[![Razorpay](https://img.shields.io/badge/Payment-Razorpay-0C2340?style=for-the-badge&logo=razorpay)](https://razorpay.com)
[![Stripe](https://img.shields.io/badge/Payment-Stripe-635BFF?style=for-the-badge&logo=stripe)](https://stripe.com)

An autonomous, AI-driven Revenue Recovery & Intelligent Dunning Platform engineered to detect payment failures, diagnose root causes with customer context, execute personalized multi-channel recovery workflows (Razorpay UPI / Stripe Links, Email, SMS, Slack), and automatically close the revenue loop upon payment verification.

---

## 🌟 Key Highlights & Architecture

- 🧠 **Context-Enriched AI Diagnostics (Google Gemini 1.5/2.0 Flash)**: Combines customer LTV, tenure, subscription tier, and 90-day failure patterns to determine the optimal recovery cadence.
- ⚡ **Deterministic Rules + LLM Fallback (Hybrid Engine)**: Instant rule resolution for standard error codes (`insufficient_funds`, `card_expired`, `suspected_fraud`) with fallback to Gemini for ambiguous edge cases.
- 💳 **Dual-Gateway Orchestration (Razorpay + Stripe)**: Native support for Razorpay payment links (Cards, NetBanking, UPI) and Stripe payment intents.
- 🔄 **Autonomous Auto-Resolution Loop**: Listens for inbound payment success webhooks (`payment_intent.succeeded`, `payment.captured`, `payment_link.paid`) to automatically mark cases as `resolved`, update recovery metrics, and broadcast Slack celebrations.
- 🛡️ **Policy Engine & Guardrails**: Dynamic retry caps (5 retries for High-LTV, 1 retry for Free Trial) and automated human escalation for high-risk or high-value anomalies.
- 📊 **Interactive Operations Console & 1-Click Sandbox**: Live web console with real-time KPI metrics, audit trail timelines, and an interactive simulation bar to test recovery flows with 1 click.
- 🗄️ **Zero-Friction Dual Database Layer**: Production-grade async PostgreSQL (`asyncpg`) with automated migration on startup and zero-config local SQLite fallback.

---

## 🏗️ End-to-End System Workflow

```mermaid
flowchart TD
    A[Payment Failure Event<br/>Stripe / Razorpay / ERP] --> B[FastAPI Ingestion Webhook]
    B --> C[PostgreSQL / SQLite Database]
    C --> D[Orchestrator Engine]
    
    subgraph Intelligence["🧠 Context & Diagnosis"]
        D --> E[Fetch Customer Context<br/>LTV, Plan, 90d History]
        E --> F{Deterministic Rule Match?}
        F -- Yes --> G[Apply Segment Strategy]
        F -- No --> H[Invoke Google Gemini LLM]
        G --> I[Policy Engine Guardrails]
        H --> I
    end
    
    subgraph Execution["📲 Multi-Channel Execution"]
        I --> J[Generate Razorpay / Stripe Link]
        J --> K[SendGrid Email Outreach]
        J --> L[Twilio SMS Outreach]
        I --> M[Slack Operations Escalation]
    end
    
    subgraph Resolution["🎉 Closed-Loop Auto-Resolution"]
        N[Inbound Payment Webhook<br/>payment.captured / payment_intent.succeeded] --> O[Auto-Resolve Case]
        O --> P[Update Recovered Revenue KPI]
        O --> Q[Broadcast Slack Celebration]
    end
```

---

## 📂 Project Structure

```text
ai-revenue-v1/
├── app/
│   ├── actions.py         # Multi-channel dispatch (Razorpay Links, Stripe, SendGrid, Twilio, Slack)
│   ├── db.py              # Async PostgreSQL pool with automatic schema migration & SQLite fallback
│   ├── llm_client.py      # Google Gemini client with customer context prompt engineering
│   ├── main.py            # FastAPI server, webhooks, simulation engine, and live UI console
│   ├── orchestrator.py    # State machine (Detect → Diagnose → Decide → Execute → Auto-Resolve)
│   ├── poller.py          # Background worker for ERP / billing overdue invoice ingestion
│   ├── schemas.py         # Pydantic schemas & event types
│   └── seed_data.py       # Rich customer directory & demo data seeder
├── tests/
│   ├── test_engine.py     # End-to-end engine test suite
│   └── test_api.py        # Async FastAPI API & simulator route tests
├── .env.example           # Environment configuration template
├── requirements.txt       # Project dependencies
└── run_server.py          # Uvicorn server launcher
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- (Optional) PostgreSQL database (falls back to local SQLite if not configured)
- (Optional) Google Gemini, SendGrid, Twilio, Slack, Razorpay, or Stripe API keys

### 2. Setup Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate      # On Windows
# source venv/bin/activate   # On Linux/macOS

pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file (copied from `.env.example`):
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/revenue_db
GEMINI_API_KEY=your_gemini_api_key
DRY_RUN=true

# Email & SMS (Optional for live dispatch)
FROM_EMAIL=recovery@yourdomain.com
SENDGRID_API_KEY=SG.your_key
TWILIO_ACCOUNT_SID=AC_your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# Gateways & Slack (Optional)
PREFERRED_PSP=stripe # or razorpay
STRIPE_API_KEY=sk_test_your_key
RAZORPAY_KEY_ID=rzp_test_your_id
RAZORPAY_KEY_SECRET=your_secret
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

> **Note:** With `DRY_RUN=true`, the system executes full state transitions, generates mock payment links, and logs simulated email/SMS/Slack dispatches without making external paid API requests.

### 4. Seed Database
```bash
python -m app.seed_data
```

### 5. Run the Server
```bash
python run_server.py
```
- **Live Operations Dashboard**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing & 1-Click Simulation

### Run Automated Test Suite
```bash
python -m tests.test_engine
python -m tests.test_api
```

### Test 1-Click Scenarios via API or Dashboard
Open [http://localhost:8000/dashboard](http://localhost:8000/dashboard) and click any scenario in the simulation bar, or trigger via curl:

```bash
# 1. High-LTV ($499 Payday 72h Retry + VIP Email)
curl -X POST "http://localhost:8000/admin/simulate?scenario=high_ltv_insufficient_funds"

# 2. Repeat Failure (Billing Date Switch Strategy)
curl -X POST "http://localhost:8000/admin/simulate?scenario=repeat_failure"

# 3. Expired Card (Payment Update Link)
curl -X POST "http://localhost:8000/admin/simulate?scenario=expired_card"

# 4. Suspected Fraud (Instant Slack Escalation)
curl -X POST "http://localhost:8000/admin/simulate?scenario=fraud"

# 5. Free Trial (1-Shot Gentle Retry)
curl -X POST "http://localhost:8000/admin/simulate?scenario=trial_user"

# 6. Inbound Payment Succeeded (Auto-Resolution Loop)
curl -X POST "http://localhost:8000/admin/simulate?scenario=payment_succeeded"
```

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/webhooks/psp` | Ingests Stripe & Razorpay payment failure & payment success webhooks |
| `POST` | `/webhooks/billing` | Ingests overdue invoice events from ERP/Billing systems |
| `POST` | `/admin/simulate` | 1-Click simulator to test all recovery scenarios |
| `POST` | `/admin/process` | Manually trigger pending and scheduled case processing cycles |
| `POST` | `/admin/resolve/{case_id}` | Manually mark a case as resolved |
| `GET` | `/admin/action-logs` | Retrieve detailed communication audit trail (Email, SMS, Slack, Links) |
| `GET` | `/dashboard/stats` | Real-time recovery KPI metrics ($ at risk, $ recovered, recovery rate) |
| `GET` | `/dashboard/cases` | Latest case list with customer profiles and AI reasoning |
| `GET` | `/dashboard` | Interactive Operations Dashboard UI |
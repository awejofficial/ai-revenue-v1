# 💰 Autonomous AI Revenue Recovery Agent

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20%2F%203.6%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Config-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Razorpay](https://img.shields.io/badge/Payment-Razorpay-0C2340?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com)
[![Stripe](https://img.shields.io/badge/Payment-Stripe-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com)

**An autonomous, context-aware Revenue Recovery & Intelligent Dunning Platform designed for modern SaaS & E-Commerce businesses.**  
*Detects payment declines in real-time, diagnoses root causes with customer context, executes hyper-personalized recovery actions, and autonomously closes the revenue loop.*

[Architecture](#-system-architecture) • [Latest Updates](#-what-we-have-updated) • [Quick Start](#-quick-start-guide) • [Operations Console](#-operations-console--simulation) • [Roadmap](#-next-phases--roadmap) • [API Reference](#-api-reference)

</div>

---

## 📌 Executive Summary

Failed recurring payments and involuntary churn cost subscription businesses **up to 9% of annual revenue**. Traditional dunning tools rely on dumb, blind retry schedules (e.g., retrying every 24 hours until failure), which alienate customers, trigger bank fraud blocks, and exhaust gateway limits.

The **Autonomous AI Revenue Recovery Agent** bridges deterministic payment logic with modern generative intelligence (**Google Gemini 3.5/3.6 Flash**):
1. **Context-Aware Decisions**: Incorporates customer Lifetime Value (LTV), subscription tier, 90-day failure velocity, and past behavior.
2. **Hybrid Engine**: Instant zero-latency rule matching for known failures (`insufficient_funds`, `card_expired`, `suspected_fraud`) with smart LLM fallback for ambiguous or rare processor declines.
3. **Multi-Channel Orchestration**: Dispatches personalized Razorpay UPI/NetBanking links, Stripe payment update links, SMS via Twilio, email via SendGrid, and automated Slack ops escalation.
4. **Closed-Loop Resolution**: Ingests inbound payment success webhooks to automatically resolve cases, calculate recovery metrics, and stop unnecessary outreach.

---

## 🌟 Key Features

| Capability | Description |
| :--- | :--- |
| 🧠 **Context-Enriched AI Diagnostics** | Evaluates customer profile (LTV, plan, history) via Google Gemini 3.5/3.6 Flash to determine whether to retry, re-route, contact, or escalate. |
| ⚡ **Deterministic Rules + LLM Fallback** | Instant deterministic execution for standard failure codes with automated Gemini fallback for edge-case decline codes. |
| 💳 **Dual-Gateway Support (Stripe + Razorpay)** | Native support for Razorpay payment links (Cards, UPI, NetBanking) and Stripe payment intents with currency detection (`INR`, `USD`, etc.). |
| 🛡️ **Policy Engine & Guardrails** | Segment-specific retry caps (e.g., up to 5 retries for High-LTV, 1 retry for Free Trials) preventing customer annoyance and compliance violations. |
| 🔄 **Closed-Loop Auto-Resolution** | Ingests `payment_intent.succeeded` or `payment.captured` webhooks to automatically mark cases resolved and calculate recovered revenue. |
| 📊 **Real-Time Operations Console** | Embedded web dashboard with KPI counters ($ at Risk, $ Recovered, Recovery Rate), interactive 1-click simulation bar, and full audit timelines. |
| 🗄️ **Dual Database Architecture** | Zero-friction local development using SQLite fallback with automated startup migrations, and production-ready async PostgreSQL (`asyncpg`). |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Ingestion Layer"]
        A1[Stripe Webhook] --> B[FastAPI Webhook Intake]
        A2[Razorpay Webhook] --> B
        A3[ERP / Billing Poller] --> B
    end

    subgraph Storage["2. Storage & State Layer"]
        B --> C[(PostgreSQL / SQLite)]
    end

    subgraph Orchestration["3. Intelligence & Policy Engine"]
        C --> D[Orchestrator State Machine]
        D --> E[Customer Context Fetcher<br/>LTV, Segment, 90-Day History]
        E --> F{Deterministic Rule Match?}
        F -- "Yes (Standard Code)" --> G[Deterministic Strategy]
        F -- "No (Rare / Complex Code)" --> H[Google Gemini 3.5/3.6 Flash]
        G --> I[Policy Engine Guardrails<br/>Retry Limits & Segment Constraints]
        H --> I
    end

    subgraph Execution["4. Multi-Channel Execution"]
        I --> J1[Razorpay UPI / Link]
        I --> J2[Stripe Payment Link]
        I --> J3[SendGrid Email Dispatch]
        I --> J4[Twilio SMS Dispatch]
        I --> J5[Slack Ops Escalation]
    end

    subgraph AutoResolution["5. Closed-Loop Auto-Resolution"]
        K[Inbound Payment Succeeded Webhook] --> L[Auto-Resolve Case]
        L --> M[Update Revenue KPI & Stop Dunning]
        L --> N[Post Slack Celebration Alert]
    end
```

---

## 🚀 What We Have Updated

### 1. 🧠 Upgraded to High-Speed Google Gemini 3.5/3.6 Models
- Configured dynamic model prioritization (`gemini-3.5-flash`, `gemini-3.6-flash`) in `app/llm_client.py`.
- Tested and achieved ultra-low diagnostic latency (**~1.34 seconds**) with full JSON schema validation.
- Validated real-time reasoning for enterprise customers and ambiguous gateway declines.

### 2. 🔒 Git Sanitization & Security Hardening
- Scrubbed repository history, removing legacy commits and author logs.
- Hardened `.gitignore` to prevent any exposure of `.env`, SQLite databases (`*.sqlite`, `*.db`), logs (`*.log`), and virtual environments (`venv/`).
- Initialized clean `main` branch ready for official deployment and open-source contribution.

### 3. 💳 Dual-Gateway & Multi-Channel Dispatch
- Unified payment link creation across both Razorpay (UPI, NetBanking, Cards in INR/USD) and Stripe.
- Configured multi-channel notifications (SendGrid email templates, Twilio SMS with shortlinks, Slack incident channels).
- Added `DRY_RUN` mode for safe local testing and sandbox demonstrations.

### 4. 📊 Operations Console & Simulation Sandbox
- Built a live dashboard with recovery metrics, active case tracking, and timeline event audit logs.
- Integrated a 1-click simulation toolbar to test scenarios like High-LTV Payday Retries, Card Expiry, Fraud Escalation, and Auto-Resolution.

---

## 📂 Repository Structure

```text
ai-revenue-v1/
├── app/
│   ├── actions.py         # Multi-channel dispatch (Razorpay, Stripe, SendGrid, Twilio, Slack)
│   ├── db.py              # Dual DB layer (Async PostgreSQL + SQLite fallback with auto-migrations)
│   ├── llm_client.py      # Google Gemini 3.5/3.6 client with context-aware prompt engineering
│   ├── main.py            # FastAPI server, webhook endpoints, and Live Operations Console
│   ├── orchestrator.py    # State machine (Detect → Diagnose → Guardrail → Execute → Auto-Resolve)
│   ├── poller.py          # Background worker for ERP / billing overdue invoice ingestion
│   ├── schemas.py         # Pydantic models for webhooks, cases, and API responses
│   └── seed_data.py       # Realistic customer directory & demo scenario seeder
├── tests/
│   ├── test_engine.py     # End-to-end engine unit and integration test suite
│   └── test_api.py        # Async FastAPI API & simulator route tests
├── .env.example           # Configuration template for credentials & features
├── .gitignore             # Comprehensive security & environment ignore rules
├── requirements.txt       # Production dependencies
└── run_server.py          # Server entrypoint launcher
```

---

## 🛠️ Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- (Optional) **Google Gemini API Key** for AI diagnostics ([Get API Key](https://aistudio.google.com))
- (Optional) **PostgreSQL** (if not provided, uses local zero-config SQLite automatically)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
cd ai-revenue-v1

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate      # On Windows
# source venv/bin/activate   # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

Configure your `.env` settings:
```env
# AI Diagnostics (Recommended)
GEMINI_API_KEY=your_gemini_api_key

# Execution Mode (Set true for mock simulation, false for live APIs)
DRY_RUN=true

# Database (Optional - leave blank or unset for automatic SQLite)
DATABASE_URL=postgresql://postgres:password@localhost:5432/revenue_db

# Gateways (Optional)
PREFERRED_PSP=stripe # or razorpay
STRIPE_API_KEY=sk_test_...
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Communications (Optional)
FROM_EMAIL=recovery@yourdomain.com
SENDGRID_API_KEY=SG....
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 4. Seed Seed Data & Launch
```bash
# Seed demo customer accounts and baseline history
python -m app.seed_data

# Start the application server
python run_server.py
```

- 🌐 **Live Operations Console**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- 📖 **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🕹️ Operations Console & Simulation

You can test every recovery flow in real-time either through the web dashboard at `http://127.0.0.1:8000/dashboard` or via `curl`:

```bash
# Scenario 1: High-LTV ($499 Payday 72h Retry + VIP Email)
curl -X POST "http://localhost:8000/admin/simulate?scenario=high_ltv_insufficient_funds"

# Scenario 2: Repeat Failure (Billing Date Switch Recommendation)
curl -X POST "http://localhost:8000/admin/simulate?scenario=repeat_failure"

# Scenario 3: Expired Card (Secure Payment Method Update Link)
curl -X POST "http://localhost:8000/admin/simulate?scenario=expired_card"

# Scenario 4: Suspected Fraud (Instant Slack Escalation to Operations Team)
curl -X POST "http://localhost:8000/admin/simulate?scenario=fraud"

# Scenario 5: Free Trial (Gentle 1-Shot Retry with Low Aggressiveness)
curl -X POST "http://localhost:8000/admin/simulate?scenario=trial_user"

# Scenario 6: Inbound Payment Succeeded (Auto-Resolution Closed-Loop)
curl -X POST "http://localhost:8000/admin/simulate?scenario=payment_succeeded"
```

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/webhooks/psp` | Ingests Stripe & Razorpay webhook events (`payment_failed`, `charge.failed`, `payment_intent.succeeded`). |
| `POST` | `/webhooks/billing` | Ingests overdue invoices and billing anomalies from ERP systems. |
| `POST` | `/admin/simulate` | 1-Click test harness to simulate payment failure and resolution workflows. |
| `POST` | `/admin/process` | Triggers immediate evaluation and processing of pending/scheduled recovery actions. |
| `POST` | `/admin/resolve/{case_id}` | Manually resolves an open case and marks invoice as recovered. |
| `GET` | `/admin/action-logs` | Fetches the real-time communication audit trail (Email, SMS, Slack, Links). |
| `GET` | `/dashboard/stats` | Returns live KPI telemetry ($ at Risk, $ Recovered, Recovery Rate, Active Cases). |
| `GET` | `/dashboard/cases` | Retrieves active and historical recovery cases with AI reasoning logs. |
| `GET` | `/dashboard` | Interactive Web Operations Console. |

---

## 🗺️ Next Phases & Roadmap

```mermaid
timeline
    title AI Revenue Recovery Platform Evolution
    Phase 1 : Hybrid Rules + Gemini LLM Diagnostics
            : Dual-Gateway Razorpay & Stripe Links
            : Live Web Operations Dashboard
            : Closed-Loop Webhook Auto-Resolution
    Phase 2 : Predictive Pre-Dunning (15d Card Expiry Alerts)
            : Multi-PSP Smart Retry Routing (Approval Rate AI)
            : Dynamic Payday Scheduling Algorithm
    Phase 3 : WhatsApp Business Interactive Recovery Links
            : Autonomous AI Voice Agent for Enterprise Overdue
            : Dynamic Churn-Sensitive Smart Discounts
    Phase 4 : Multi-Tenant SaaS & Role-Based Access Control (RBAC)
            : Native Connectors (Zuora, NetSuite, Salesforce Billing)
            : SOC2 & PCI-DSS Compliance Exportable Audit Vault
```

### 🔮 Detailed Phase Breakdown

#### **Phase 2: Predictive Pre-Dunning & Smart Routing (Next Up)**
- [ ] **Predictive Pre-Dunning**: Trigger automated, gentle card update alerts 15 days before expiration based on gateway card lifecycle metadata.
- [ ] **Smart Payment Gateway Routing**: If a transaction fails on Gateway A (e.g., Stripe) due to network or routing issues, automatically attempt the retry via Gateway B (e.g., Razorpay/Adyen) based on live issuer authorization rates.
- [ ] **Payday & Timezone ML Alignment**: Automatically align retries with regional salary cycles (1st/15th of the month or Fridays) and customer local timezones to maximize recovery probability.

#### **Phase 3: Conversational & Multi-Modal Recovery**
- [ ] **WhatsApp Business Interactive Messages**: Send direct WhatsApp messages with 1-tap UPI and Apple Pay / Google Pay payment buttons for high conversion.
- [ ] **Autonomous AI Voice Agent**: AI agent calls accounts for overdue enterprise invoices (>$5,000) to confirm billing details and offer automated payment link dispatch.
- [ ] **Dynamic Retention Discounting**: Dynamically attach smart, time-limited retention offers (e.g., "Renew today for 15% off next 3 months") when churn probability is critical.

#### **Phase 4: Enterprise Scale & Ecosystem Integrations**
- [ ] **Multi-Tenant SaaS Architecture**: Complete workspace separation with custom merchant branding, custom domain links, and individual API keys.
- [ ] **Native Billing Connectors**: Plug-and-play integrations with NetSuite, Zuora, Chargebee, Recurly, and Salesforce Revenue Cloud.
- [ ] **SOC2 / PCI-DSS Compliance Vault**: End-to-end encrypted audit logging, immutable action history, and exportable regulatory compliance packages.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request:
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the **MIT License**.
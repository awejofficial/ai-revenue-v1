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
*Find revenue that’s slipping away and win it back: From payment degradation and failed subscriptions to B2B receivables and checkout drop-offs.*

[Track 03 Alignment](#-track-03-challenge-alignment) • [Architecture](#-system-architecture) • [3 Recovery Vectors](#-three-core-recovery-vectors) • [Web Portals](#-web-operations--analytics-portals) • [Quick Start](#-quick-start-guide) • [Simulation Sandbox](#-operations-console--simulation-sandbox) • [API Reference](#-api-reference) • [Roadmap](#-next-phases--roadmap)

</div>

---

## 🎯 Track 03: AI Revenue Recovery — Challenge Alignment

> **"Find revenue that’s slipping away and win it back."**  
> *Build an agent that detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow: from payment failures and checkout abandonment to overdue receivables.*

### ⚡ Why Now?
Revenue loss rarely happens in one clean step. A payment degrades, a checkout gets abandoned, a subscription fails, or an invoice goes overdue. Traditional dunning tools rely on blind, static retry timers that frustrate customers, damage merchant reputations, and cause chargebacks.  
**Modern AI closes the loop**: detecting degradation $\rightarrow$ diagnosing root causes with customer context $\rightarrow$ selecting bounded, compliant interventions $\rightarrow$ automatically verifying recovery.

### 🏆 Meeting "The Bar"

| Evaluation Criterion ("The Bar") | How This System Exceeds It |
| :--- | :--- |
| **Don’t just identify the problem — recover the money** | Autonomous closed-loop auto-resolution that listens for inbound webhook events (`payment_intent.succeeded`, `payment.captured`, `payment_link.paid`) to automatically close cases, update recovered revenue, and terminate dunning sequences. |
| **Measured money recovered across a batch** | Live real-time KPI ledger tracking **$ At Risk**, **$ Recovered**, and **Recovery Rate (%)** across real and batch simulated event streams. |
| **Compliant escalation** | Dynamic policy engine that triggers instant white-glove Slack operations handoffs for high-risk anomalies, fraud flags, and enterprise accounts ($5,000+ LTV). |
| **Strict stopping rules** | Segment-specific retry caps (1 retry for Trials, 3 for Standard, 5 for Enterprise) and hard failure breakers to prevent spamming or brand erosion. |
| **Complete audit trail** | Immutable, searchable `action_logs` recording every outbound touchpoint (Email, SMS, Payment Link, Slack alert) with timestamped delivery state. |

---

## 📌 Executive Summary

Failed recurring payments, abandoned checkouts, and overdue invoices cost online businesses **up to 9% of annual revenue**. Traditional dunning tools rely on dumb, blind retry schedules (e.g., retrying every 24 hours until failure), which alienate customers, trigger bank fraud blocks, and exhaust gateway limits.

The **Autonomous AI Revenue Recovery Agent** bridges deterministic payment logic with modern generative intelligence (**Google Gemini 3.5/3.6 Flash**):
1. **Context-Aware Decisions**: Incorporates customer Lifetime Value (LTV), subscription tier, 90-day failure velocity, and past behavior.
2. **Hybrid Engine**: Instant zero-latency rule matching for known failure patterns (`insufficient_funds`, `card_expired`, `checkout_drop_off`, `suspected_fraud`) with smart LLM fallback for ambiguous or rare processor declines.
3. **Multi-Channel Orchestration**: Dispatches personalized Razorpay UPI/NetBanking links, Stripe payment update links, SMS via Twilio, responsive HTML email via SendGrid with dynamic promo codes, and automated Slack ops escalation.
4. **Closed-Loop Resolution**: Ingests inbound payment success webhooks to automatically resolve cases, calculate recovery metrics, and stop unnecessary outreach.
5. **Unified Operations Suite**: Three dedicated web portals for real-time monitoring, customer 360 intelligence, and conversion funnel analytics.

---

## 🌟 Key Features

| Capability | Description |
| :--- | :--- |
| 🧠 **Context-Enriched AI Diagnostics** | Evaluates customer profile (LTV, plan, history) via Google Gemini 3.5/3.6 Flash to determine whether to retry, re-route, contact, or escalate. |
| ⚡ **Deterministic Rules + LLM Fallback** | Instant deterministic execution across 7 rule sets with automated Gemini fallback for edge-case decline codes. |
| 🛒 **Checkout Drop-Off Recovery** | Detects abandoned carts and 3DS verification drop-offs, instantly generating 1-click recovery links with dynamic VIP discounts (`RECOVER10`). |
| 👥 **Customer 360 Risk Directory** | Real-time risk profiling classifying customers into Safe, Moderate, High, and Critical risk tiers with 90-day failure telemetry. |
| 📈 **Recovery Funnel & Analytics** | Multi-stage conversion funnel tracking drop-offs across Detection $\rightarrow$ Diagnosis $\rightarrow$ Outreach $\rightarrow$ Recovery with gateway performance metrics. |
| 💳 **Dual-Gateway Support (Stripe + Razorpay)** | Native support for Razorpay payment links (Cards, UPI, NetBanking) and Stripe payment intents with automatic currency detection (`INR`, `USD`). |
| 🛡️ **Policy Engine & Guardrails** | Segment-specific retry caps (up to 5 retries for High-LTV, 1 retry for Free Trials) preventing customer annoyance and compliance violations. |
| 🔄 **Closed-Loop Auto-Resolution** | Ingests `payment_intent.succeeded` or `payment.captured` webhooks to automatically mark cases resolved and calculate recovered revenue. |
| 🗄️ **Dual Database Architecture** | Zero-friction local development using SQLite fallback with automated startup migrations, and production-ready async PostgreSQL (`asyncpg`). |

---

## 🎯 Three Core Recovery Vectors

The platform handles revenue leakage across three distinct vectors:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   REVENUE LEAKAGE VECTORS                                        │
├──────────────────────────────┬──────────────────────────────────┬────────────────────────────────┤
│ 1. Subscription & Dunning    │ 2. Checkout Drop-Off & Carts     │ 3. B2B Overdue Receivables     │
├──────────────────────────────┼──────────────────────────────────┼────────────────────────────────┤
│ • Involuntary churn          │ • 3DS authentication drop-offs   │ • Overdue Net-30 / Net-60      │
│ • Expired credit cards       │ • Checkout friction timeouts     │ • High-value enterprise unpaid │
│ • Insufficient funds         │ • 1-click cart recovery links    │ • Automated ERP polling worker │
│ • Smart payday 72h alignment │ • Dynamic VIP discounts (10% off)│ • Operations team escalation   │
└──────────────────────────────┴──────────────────────────────────┴────────────────────────────────┘
```

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Multi-Vector Ingestion Layer"]
        A1[Stripe Webhooks<br/>payment_failed, charge.failed] --> B[FastAPI Webhook & Ingestion Intake]
        A2[Razorpay Webhooks<br/>payment.failed, order.paid] --> B
        A3[Checkout Telemetry<br/>checkout_drop_off, 3DS friction] --> B
        A4[ERP / Billing Poller<br/>Overdue Net-30 Invoices] --> B
    end

    subgraph Storage["2. Storage & State Layer"]
        B --> C[(PostgreSQL / SQLite<br/>Async Connection Pool)]
    end

    subgraph Orchestration["3. Intelligence & Policy Engine"]
        C --> D[Orchestrator State Machine]
        D --> E[Customer 360 Context Fetcher<br/>LTV, Segment, 90-Day Velocity]
        E --> F{7 Deterministic Rules Match?}
        F -- "Yes (Known Pattern)" --> G[Deterministic Strategy<br/>Payday Retry / Cart Link / Expired]
        F -- "No (Rare / Complex Decline)" --> H[Google Gemini 3.5/3.6 Flash<br/>JSON Diagnostics & Action Plan]
        G --> I[Policy Engine Guardrails<br/>Segment Caps, Max Retries & Value Limits]
        H --> I
    end

    subgraph Execution["4. Multi-Channel & Incentive Execution"]
        I --> J1[Razorpay UPI / NetBanking / Card Link]
        I --> J2[Stripe 1-Click Payment Link / Intent]
        I --> J3[SendGrid Responsive HTML Email<br/>Dynamic VIP Promo Code Engine]
        I --> J4[Twilio SMS Instant Shortlinks]
        I --> J5[Slack Ops Team Escalation]
    end

    subgraph AutoResolution["5. Closed-Loop Auto-Resolution"]
        K[Inbound Payment Succeeded Webhook<br/>Stripe / Razorpay / Link Paid] --> L[Auto-Resolve Case Engine]
        L --> M[Update Revenue KPI Ledger & Stop Dunning]
        L --> N[Broadcast Slack Recovery Celebration]
    end

    subgraph Portals["6. Operations & Analytics Suite"]
        C --> P1[Live Operations Console<br/>/dashboard]
        C --> P2[Customer 360 Risk Directory<br/>/customers]
        C --> P3[Recovery Funnel & Analytics<br/>/analytics]
    end
```

---

## 🖥️ Web Operations & Analytics Portals

The application provides three built-in browser portals for business teams:

### 1. 🎛️ Live Operations Console (`/dashboard` or `/`)
- **Real-Time KPI Ledger**: Live counters for **$ At Risk**, **$ Recovered**, **Active Cases**, and **Recovery Rate %**.
- **Interactive 1-Click Simulation Toolbar**: Test 7 scenarios in real time (High LTV Payday, Cart Drop-Off, Expired Card, Fraud, etc.).
- **Active & Historical Cases Table**: Shows AI reasoning, retry counts, scheduled execution time, and case status.
- **Audit Timeline Stream**: Timestamped log of outbound communications across Email, SMS, Slack, and Gateways.

### 2. 👥 Customer 360 & Risk Intelligence Directory (`/customers`)
- **Risk Classification Matrix**: Dynamically categorizes customer accounts into **Safe**, **Moderate Risk**, **High Risk**, and **Critical Risk**.
- **Customer Profiles**: Displays Lifetime Value (LTV), subscription plan, company, and 90-day failure velocity.
- **Direct Intervention Triggers**: 1-click direct recovery trigger buttons per customer.

### 3. 📈 Recovery Funnel & Gateway Analytics Portal (`/analytics`)
- **4-Stage Recovery Funnel**: Visual conversion tracking from **Detected Cases** $\rightarrow$ **Diagnosed** $\rightarrow$ **Outreach Dispatched** $\rightarrow$ **Auto-Recovered**.
- **Gateway Distribution**: Real-time breakdown of transactions processed across **Stripe** (USD) and **Razorpay** (INR / UPI).
- **Channel Utilization**: Dispatched counts across **Email**, **SMS**, **Slack Alerts**, and **Payment Links**.
- **Failure Code Telemetry**: Categorized failure reasons (Checkout Drop-Off, Insufficient Funds, Card Expired, Fraud, etc.).

---

## 🚀 What We Have Updated

### 1. 🛒 Added Checkout Drop-Off & Cart Abandonment Recovery
- Built detection and automated 1-click recovery for checkout drop-offs and 3DS friction.
- Integrated dynamic promotional incentives (e.g. `RECOVER10` 10% instant discount for high-value carts) within email and SMS touchpoints.

### 2. 👥 Customer 360 Risk Intelligence Portal
- Added `/customers` web portal and `/api/customers` API endpoint providing a holistic view of accounts, LTV tiers, and failure history.

### 3. 📈 Recovery Funnel & Gateway Analytics Suite
- Built `/analytics` web portal and `/api/analytics` telemetry API tracking end-to-end recovery conversion rates and channel effectiveness.

### 4. 🧠 High-Speed Google Gemini 3.5/3.6 Integration
- Configured dynamic model prioritization (`gemini-3.5-flash`, `gemini-3.6-flash`) in `app/llm_client.py` with structured JSON diagnostic output.
- Ultra-low latency diagnostics (~1.34s) for ambiguous gateway declines.

### 5. 💳 Resilient Dual-Gateway & Multi-Channel Dispatch
- Resilient payment link creation across Stripe and Razorpay (UPI, NetBanking, Cards).
- Multi-channel alerts via SendGrid, Twilio, and Slack with automatic fallback for sandbox/test environments.

---

## 📂 Repository Structure

```text
ai-revenue-v1/
├── app/
│   ├── actions.py         # Multi-channel dispatch (Razorpay, Stripe, SendGrid, Twilio, Slack)
│   ├── db.py              # Dual DB layer (Async PostgreSQL + SQLite fallback with auto-migrations)
│   ├── llm_client.py      # Google Gemini 3.5/3.6 client with context-aware prompt engineering
│   ├── main.py            # FastAPI server, webhooks, and Operations / Customers / Analytics Portals
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

### 4. Seed Data & Launch
```bash
# Seed demo customer accounts and baseline history
python -m app.seed_data

# Start the application server
python run_server.py
```

- 🎛️ **Live Operations Console**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- 👥 **Customer 360 Risk Directory**: [http://127.0.0.1:8000/customers](http://127.0.0.1:8000/customers)
- 📈 **Recovery Funnel Analytics**: [http://127.0.0.1:8000/analytics](http://127.0.0.1:8000/analytics)
- 📖 **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🕹️ Operations Console & Simulation Sandbox

You can test every recovery flow in real-time either through the web dashboard or via `curl`:

```bash
# Scenario 1: High-LTV ($499 Payday 72h Retry + Concierge Link)
curl -X POST "http://localhost:8000/admin/simulate?scenario=high_ltv_insufficient_funds"

# Scenario 2: Checkout Drop-Off (1-Click Recovery Link + 10% VIP Discount Code RECOVER10)
curl -X POST "http://localhost:8000/admin/simulate?scenario=checkout_drop_off"

# Scenario 3: Repeat Failure (Billing Date Switch Recommendation)
curl -X POST "http://localhost:8000/admin/simulate?scenario=repeat_failure"

# Scenario 4: Expired Card (Secure Payment Method Update Link)
curl -X POST "http://localhost:8000/admin/simulate?scenario=expired_card"

# Scenario 5: Suspected Fraud (Instant Slack Escalation to Operations Team)
curl -X POST "http://localhost:8000/admin/simulate?scenario=fraud"

# Scenario 6: Free Trial (Gentle 1-Shot Retry with Low Aggressiveness)
curl -X POST "http://localhost:8000/admin/simulate?scenario=trial_user"

# Scenario 7: Inbound Payment Succeeded (Auto-Resolution Closed-Loop)
curl -X POST "http://localhost:8000/admin/simulate?scenario=payment_succeeded"
```

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` / `/dashboard` | Interactive Live Operations Console with 1-click simulation sandbox. |
| `GET` | `/customers` | Customer 360 & Risk Intelligence Directory UI. |
| `GET` | `/analytics` | Recovery Funnel & Gateway Analytics Portal UI. |
| `GET` | `/api/customers` | Returns holistic customer 360 data, LTV, segment, and risk tier categorization. |
| `GET` | `/api/analytics` | Returns recovery funnel conversion rates, gateway volumes, and channel metrics. |
| `POST` | `/webhooks/psp` | Ingests Stripe & Razorpay webhooks (`payment_failed`, `charge.failed`, `payment_intent.succeeded`). |
| `POST` | `/webhooks/billing` | Ingests overdue invoices and billing anomalies from ERP systems. |
| `POST` | `/admin/simulate` | 1-Click test harness to simulate payment failures, drop-offs, and auto-resolutions. |
| `POST` | `/admin/process` | Triggers immediate evaluation and processing of pending/scheduled recovery actions. |
| `POST` | `/admin/resolve/{case_id}` | Manually resolves an open case and marks invoice as recovered. |
| `GET` | `/admin/action-logs` | Fetches the real-time communication audit trail (Email, SMS, Slack, Links). |
| `GET` | `/dashboard/stats` | Returns live KPI telemetry ($ at Risk, $ Recovered, Recovery Rate, Active Cases). |
| `GET` | `/dashboard/cases` | Retrieves active and historical recovery cases with AI reasoning logs. |
| `GET` | `/health` | Server health check endpoint. |

---

## 🗺️ Next Phases & Roadmap

```mermaid
timeline
    title AI Revenue Recovery Platform Evolution
    Phase 1 : Hybrid Rules + Gemini LLM Diagnostics
            : Dual-Gateway Razorpay & Stripe Links
            : Checkout Drop-Off & 3DS Friction Recovery
            : 3 Operations Portals (Console, 360, Funnel)
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
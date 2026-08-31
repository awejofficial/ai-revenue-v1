# 💰 Autonomous AI Revenue Recovery Agent

<div align="center">

[![Status](https://img.shields.io/badge/Status-Production%20Ready-00C853?style=for-the-badge&logo=checkmarx&logoColor=white)](#-production-readiness)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev)
[![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-Components-000000?style=for-the-badge&logo=shadcnui&logoColor=white)](https://ui.shadcn.com)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.7%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Config-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Stripe](https://img.shields.io/badge/Stripe-Live%20Ready-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com)
[![Razorpay](https://img.shields.io/badge/Razorpay-Live%20Ready-0C2340?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)

**An autonomous, production-ready Revenue Recovery & Intelligent Dunning Platform for modern SaaS & E-Commerce businesses.**  
*Find revenue that's slipping away and win it back: From payment degradation and failed subscriptions to B2B receivables and checkout drop-offs.*

[Production Readiness](#-production-readiness) • [Architecture](#-system-architecture) • [3 Recovery Vectors](#-three-core-recovery-vectors) • [Modern Frontend](#-modern-react-frontend) • [Quick Start](#-quick-start-guide) • [Go Live](#-going-live-production-deployment) • [API Reference](#-api-reference) • [Roadmap](#-next-phases--roadmap)

</div>

---

## ✅ Production Readiness

> **This platform is production-ready.** All core integrations are fully coded, tested, and wired end-to-end. The system ships in a safe `DRY_RUN=true` simulation mode — flip one environment variable and supply your API keys to go live with real money.

### Integration Status

| Integration | Status | Details |
| :--- | :---: | :--- |
| **Google Gemini 3.7 Flash** | 🟢 Live | Context-aware AI diagnostics with structured JSON output. Fallback chain: 3.7 → 3.6 → 3.5 Flash. |
| **Stripe Gateway (USD)** | 🟢 Live Ready | Real `PaymentIntent.create()` calls. Parses live webhook payloads (`payment_intent.succeeded`, `charge.failed`). |
| **Razorpay Gateway (INR / UPI)** | 🟢 Live Ready | Real `payment_link.create()` calls supporting Cards, UPI, NetBanking. Parses live webhook payloads (`payment.captured`, `order.paid`). |
| **SendGrid Email** | 🟢 Live Ready | Personalized HTML recovery emails with dynamic payment links and promo codes. |
| **Twilio SMS** | 🟢 Live Ready | Shortlink SMS recovery messages with customer context. |
| **Slack Ops Escalation** | 🟢 Live Ready | Rich Slack webhook payloads with 1-click resolve feedback links for operations teams. |
| **PostgreSQL (asyncpg)** | 🟢 Live | Async connection pooling with auto-migrations on startup (supports Render Managed PostgreSQL). |
| **SQLite (Zero-Config)** | 🟢 Live | Automatic fallback for local development — no database install required. |
| **Webhook Intake** | 🟢 Live | `/webhooks/psp` (Stripe & Razorpay) and `/webhooks/billing` (ERP/Invoicing) endpoints ready to receive production traffic. |
| **Closed-Loop Auto-Resolution** | 🟢 Live | Inbound success webhooks automatically resolve cases, update recovery metrics, and terminate dunning sequences. |
| **Render & Vercel Deployment** | 🟢 Live | Cloud infrastructure with Render (FastAPI + Managed PostgreSQL) and Vercel (React 19 Vite SPA). |
| **React 19 + shadcn/ui Frontend** | 🟢 Live | Modern, accessible SPA with dark mode, responsive design, and real-time polling. |

### The `DRY_RUN` Switch

```env
# In your .env file:
DRY_RUN=true   # ← SIMULATION MODE (default): Generates mock payment links, mock emails, mock SMS. Safe to test.
DRY_RUN=false  # ← PRODUCTION MODE: Calls real Stripe, Razorpay, SendGrid, Twilio, and Slack APIs.
```

When `DRY_RUN=true` (or when API keys are missing), the system gracefully falls back to mock responses — generating realistic-looking links and logging every action for full audit trail visibility without touching real money.

---

## 🎯 Track 03: AI Revenue Recovery — Challenge Alignment

> **"Find revenue that's slipping away and win it back."**  
> *Build an agent that detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow: from payment failures and checkout abandonment to overdue receivables.*

### ⚡ Why Now?
Revenue loss rarely happens in one clean step. A payment degrades, a checkout gets abandoned, a subscription fails, or an invoice goes overdue. Traditional dunning tools rely on blind, static retry timers that frustrate customers, damage merchant reputations, and cause chargebacks.  
**Modern AI closes the loop**: detecting degradation → diagnosing root causes with customer context → selecting bounded, compliant interventions → automatically verifying recovery.

### 🏆 Meeting "The Bar"

| Evaluation Criterion ("The Bar") | How This System Exceeds It |
| :--- | :--- |
| **Don't just identify the problem — recover the money** | Autonomous closed-loop auto-resolution that listens for inbound webhook events (`payment_intent.succeeded`, `payment.captured`, `payment_link.paid`) to automatically close cases, update recovered revenue, and terminate dunning sequences. |
| **Measured money recovered across a batch** | Live real-time KPI ledger tracking **$ At Risk**, **$ Recovered**, and **Recovery Rate (%)** across real and batch simulated event streams. |
| **Compliant escalation** | Dynamic policy engine that triggers instant white-glove Slack operations handoffs with direct resolve feedback links for high-risk anomalies, fraud flags, and enterprise accounts ($5,000+ LTV). |
| **Strict stopping rules & DND compliance** | Segment-specific retry caps (1 retry for Trials, 3 for Standard, 5 for Enterprise), hard failure breakers, and channel-level DND/opt-out gates preventing customer spam or brand erosion. |
| **Complete audit trail** | Immutable, searchable `action_logs` recording every outbound touchpoint (Email, SMS, Payment Link, Slack alert) with timestamped delivery state. Exportable to CSV. |

---

## 📌 Executive Summary

Failed recurring payments, abandoned checkouts, and overdue invoices cost online businesses **up to 9% of annual revenue**. Traditional dunning tools rely on dumb, blind retry schedules (e.g., retrying every 24 hours until failure), which alienate customers, trigger bank fraud blocks, and exhaust gateway limits.

The **Autonomous AI Revenue Recovery Agent** bridges deterministic payment logic with modern generative intelligence (**Google Gemini 3.7 / 3.6 / 3.5 Flash**):
1. **Context-Aware Decisions**: Incorporates customer Lifetime Value (LTV), subscription tier, 90-day failure velocity, and past behavior.
2. **Hybrid Engine**: Instant zero-latency rule matching for known failure patterns (`insufficient_funds`, `card_expired`, `checkout_drop_off`, `suspected_fraud`) with smart LLM fallback for ambiguous or rare processor declines.
3. **Multi-Channel Orchestration**: Dispatches personalized Razorpay UPI/NetBanking links, Stripe payment update links, SMS via Twilio, responsive HTML email via SendGrid, and automated Slack ops escalation with resolve links.
4. **Channel Preference & DND Compliance**: Honors customer communication preferences, suppressing opted-out channels and falling back gracefully.
5. **Closed-Loop Resolution**: Ingests inbound payment success webhooks to automatically resolve cases, calculate recovery metrics, and stop unnecessary outreach.
6. **Modern React Frontend**: Full-featured SPA built with React 19, TypeScript, Vite, and shadcn/ui — featuring dark mode, real-time data polling, CSV export, responsive design, and accessibility.

---

## 🌟 Key Features

| Capability | Description |
| :--- | :--- |
| 🧠 **Context-Enriched AI Diagnostics** | Evaluates customer profile (LTV, plan, history) via Google Gemini 3.7 / 3.6 / 3.5 Flash to determine whether to retry, re-route, contact, or escalate. |
| ⚡ **Deterministic Rules + LLM Fallback** | Instant deterministic execution for standard failure codes with automated Gemini fallback for edge-case decline codes. |
| 🛒 **Checkout Drop-Off Recovery** | Detects abandoned carts and 3DS verification drop-offs, instantly generating 1-click recovery links with dynamic VIP incentives. |
| 👥 **Customer 360 Risk Directory** | Real-time risk profiling classifying customers into Safe, Moderate, High, and Critical risk tiers with 90-day failure telemetry. |
| 📈 **Recovery Funnel & Analytics** | Multi-stage conversion funnel tracking drop-offs across Detection → Diagnosis → Outreach → Recovery with gateway performance metrics. |
| 💳 **Dual-Gateway Support (Stripe + Razorpay)** | Native support for Razorpay payment links (Cards, UPI, NetBanking) and Stripe payment intents with automatic currency detection (`INR`, `USD`). |
| 🛡️ **Policy Engine & DND Guardrails** | Segment retry caps (up to 5 for High-LTV, 1 for Free Trials) and channel-level opt-out (DND) preference gates to prevent spam and ensure compliance. |
| 🔄 **Closed-Loop Auto-Resolution** | Ingests `payment_intent.succeeded` or `payment.captured` webhooks to automatically mark cases resolved and calculate recovered revenue. |
| 🗄️ **Dual Database Architecture** | Zero-friction local development using SQLite fallback with automated startup migrations, and production-ready async PostgreSQL (`asyncpg`). |
| ⚛️ **Modern React 19 + shadcn/ui Frontend** | Accessible, responsive SPA with dark/light theme toggle, real-time polling, CSV log export, and mobile-optimized touch targets. |
| 📋 **CSV Audit Log Export** | Export recent action logs to CSV with formula injection protection for secure offline analysis and compliance reporting. |
| 🚀 **Render & Vercel Cloud Deployment** | Zero-hassle cloud deployment with Render (FastAPI + Managed PostgreSQL) and Vercel (React 19 Vite SPA). |

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
    subgraph Ingestion["1. Multi-Vector Ingestion & Idempotency"]
        A1[Stripe Webhook<br/>payment_failed, charge.failed] --> B[FastAPI Intake & Normalization]
        A2[Razorpay Webhook<br/>payment.failed, order.paid] --> B
        A3[ERP / Billing Invoices<br/>Net-30 overdue poll] --> B
        B -- "Idempotency Dedup<br/>(ON CONFLICT DO NOTHING)" --> DB_RAW
    end

    subgraph Storage["2. Storage & State Schema"]
        DB_RAW[("raw_events<br/>• event_id (UNIQUE)<br/>• canonical_event<br/>• is_processed")]
        DB_CASES[("cases<br/>• case_id, status<br/>• amount_usd, retries<br/>• scheduled_next_action_at")]
        DB_CUST[("customers<br/>• customer_id, LTV<br/>• segment, CRM data<br/>• contact_preferences")]
        DB_LOGS[("action_logs<br/>• case_id, channel<br/>• payload, status<br/>• immutable audit")]
    end

    subgraph Intelligence["3. Intelligence & Policy Engine"]
        DB_RAW --> ORCH[Orchestrator State Machine]
        DB_CUST --> CTX[Customer 360 Context Fetcher<br/>LTV, Segment, 90d Velocity]
        ORCH --> CTX
        CTX --> RULE_CHECK{Deterministic<br/>Rule Match?}
        RULE_CHECK -- "Yes (Known Pattern)" --> DET_STRAT[Deterministic Strategy<br/>Payday 72h / Expired / Cart Link]
        RULE_CHECK -- "No (Complex Decline)" --> LLM[Google Gemini 3.7/3.6 Flash<br/>JSON Diagnostics & Reasoning]
        DET_STRAT --> POLICY[Policy Engine Guardrails<br/>Segment Retry Caps & Value Limits]
        LLM --> POLICY
        POLICY --> RETRY_CHECK{Retries >= Max<br/>or Security Risk?}
        RETRY_CHECK -- "Yes" --> ESCALATE[Escalate to Human Team]
        RETRY_CHECK -- "No" --> EXEC_GATE[Channel Preference Gate<br/>DND / Opt-Out Check]
    end

    subgraph Execution["4. Multi-Channel Execution"]
        EXEC_GATE --> CH_RZP[Razorpay UPI / Link]
        EXEC_GATE --> CH_STRIPE[Stripe 1-Click Link]
        EXEC_GATE --> CH_EMAIL[SendGrid HTML Email]
        EXEC_GATE --> CH_SMS[Twilio SMS Shortlink]
        ESCALATE --> CH_SLACK[Slack Ops Escalation<br/>with Resolve Feedback Link]
    end

    subgraph WriteBacks["5. State Transitions & Audit Write-Backs"]
        ORCH -. "1. Update Case Status & Decision" .-> DB_CASES
        CH_RZP -. "2. Log Action" .-> DB_LOGS
        CH_STRIPE -. "2. Log Action" .-> DB_LOGS
        CH_EMAIL -. "2. Log Action" .-> DB_LOGS
        CH_SMS -. "2. Log Action" .-> DB_LOGS
        CH_SLACK -. "2. Log Escalation" .-> DB_LOGS
    end

    subgraph FeedbackLoops["6. Closed-Loop Resolution & Scheduled Retries"]
        POLLER[Background Worker<br/>Polls scheduled_next_action_at] --> DB_CASES
        DB_CASES -. "Scheduled Retry Due" .-> ORCH
        CH_SLACK -. "Ops Manual Resolve<br/>POST /admin/resolve" .-> DB_CASES
        WH_SUCCESS[Inbound Payment Success Webhook] --> AUTO_RES[Auto-Resolve Engine]
        AUTO_RES --> DB_CASES
        AUTO_RES --> DB_LOGS
        AUTO_RES --> CELEBRATE[Broadcast Slack Celebration]
    end

    subgraph Frontend["7. Modern React 19 Frontend (Vite + shadcn/ui)"]
        DB_CASES --> P1[Dashboard View<br/>Live KPIs, Cases, Logs]
        DB_LOGS --> P1
        DB_CUST --> P2[Customer 360 View<br/>Risk Profiles & Interventions]
        DB_CASES --> P2
        DB_CASES --> P3[Analytics View<br/>Recovery Funnel & Metrics]
        DB_LOGS --> P3
    end
```

---

## ⚛️ Modern React Frontend

The platform includes a **full-featured modern SPA** built with industry-standard tools:

| Technology | Purpose |
| :--- | :--- |
| **React 19** | Component architecture with hooks and concurrent features |
| **TypeScript** | End-to-end type safety |
| **Vite 8** | Lightning-fast HMR and optimized production builds |
| **shadcn/ui** | Accessible, composable component library (Radix UI + Tailwind CSS) |
| **Recharts** | Data visualization for analytics and funnel charts |
| **Dark / Light Theme** | System-aware theme toggle with smooth transitions |

### Frontend Views

| View | Route | Features |
| :--- | :--- | :--- |
| **Dashboard** | `/` | Real-time KPIs ($ At Risk, $ Recovered, Recovery Rate), active cases ledger, recent action logs with CSV export, 1-click simulation toolbar |
| **Customers** | `/customers` | Customer 360 risk directory, LTV profiling, direct intervention triggers, risk classification (Safe → Critical) |
| **Analytics** | `/analytics` | Recovery funnel waterfall, gateway distribution, channel utilization, failure code telemetry |
| **Settings** | Dialog | Engine health monitor, integration status, theme toggle |

### Frontend Highlights
- **Real-time Data Polling**: Auto-refreshes dashboard data with Page Visibility API to pause polling on inactive tabs (battery/bandwidth friendly).
- **CSV Export**: Export action logs with built-in formula injection protection (`=`, `+`, `-`, `@` prefix sanitization) for secure compliance reporting.
- **Responsive Design**: Mobile-optimized with ≥36px touch targets, responsive grid layouts, and collapsible navigation.
- **Accessibility**: ARIA roles, keyboard navigation, semantic HTML lists, and proper focus management.
- **Memory-Safe Downloads**: Uses `Blob` URLs with automatic cleanup instead of data URIs.

---

## 🖥️ Web Operations & Analytics Portals

### 1. 🎛️ Live Operations Console (Dashboard — `/`)
- **Real-Time KPI Ledger**: Live counters for **$ At Risk**, **$ Recovered**, **Active Cases**, and **Recovery Rate %**.
- **Interactive 1-Click Simulation Toolbar**: Test 7 scenarios in real time (High LTV Payday, Cart Drop-Off, Expired Card, Fraud, etc.).
- **Active & Historical Cases Table**: Shows AI reasoning, retry counts, scheduled execution time, and case status.
- **Recent Logs with CSV Export**: Timestamped log of outbound communications across Email, SMS, Slack, and Gateways — exportable to CSV.

### 2. 👥 Customer 360 & Risk Intelligence Directory (`/customers`)
- **Risk Classification Matrix**: Dynamically categorizes customer accounts into **Safe**, **Moderate Risk**, **High Risk**, and **Critical Risk**.
- **Customer Profiles**: Displays Lifetime Value (LTV), subscription plan, company, and 90-day failure velocity.
- **Direct Intervention Triggers**: 1-click direct recovery trigger buttons per customer.

### 3. 📈 Recovery Funnel & Gateway Analytics Portal (`/analytics`)
- **4-Stage Recovery Funnel**: Visual conversion tracking from **Detected Cases** → **Diagnosed** → **Outreach Dispatched** → **Auto-Recovered**.
- **Gateway Distribution**: Real-time breakdown of transactions processed across **Stripe** (USD) and **Razorpay** (INR / UPI).
- **Channel Utilization**: Dispatched counts across **Email**, **SMS**, **Slack Alerts**, and **Payment Links**.
- **Failure Code Telemetry**: Categorized failure reasons (Checkout Drop-Off, Insufficient Funds, Card Expired, Fraud, etc.).

---

## 📂 Repository Structure

```text
ai-revenue-v1/
├── app/
│   ├── actions.py         # Multi-channel dispatch (Razorpay, Stripe, SendGrid, Twilio, Slack)
│   ├── db.py              # Dual DB layer (Async PostgreSQL + SQLite fallback with auto-migrations)
│   ├── llm_client.py      # Google Gemini 3.7/3.6/3.5 client with context-aware prompt engineering
│   ├── main.py            # FastAPI server, webhooks, REST API, and simulation endpoints
│   ├── orchestrator.py    # State machine (Detect → Diagnose → Guardrail → Execute → Auto-Resolve)
│   ├── poller.py          # Background worker for ERP / billing overdue invoice ingestion
│   ├── schemas.py         # Pydantic models for webhooks, cases, and API responses
│   └── seed_data.py       # Realistic customer directory & demo scenario seeder
├── frontend/              # Modern React 19 SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/    # DashboardView, CasesLedger, RecentLogsCard, CompactDeclineCard
│   │   │   ├── customers/    # CustomerView, CustomerDrawer
│   │   │   ├── analytics/    # AnalyticsView, FunnelWaterfall
│   │   │   ├── layout/       # Header, Sidebar, MobileNav, SettingsDialog
│   │   │   └── ui/           # shadcn/ui primitives (Button, Card, Badge, Dialog, etc.)
│   │   ├── App.tsx           # Root app with routing and theme provider
│   │   └── main.tsx          # Vite entry point
│   ├── package.json          # React 19, Vite 8, shadcn/ui, Recharts
│   ├── vercel.json           # Vercel SPA routing rewrites configuration
│   └── vite.config.ts        # Vite config with API proxy to backend
├── tests/
│   ├── test_engine.py     # End-to-end engine unit and integration test suite
│   └── test_api.py        # Async FastAPI API & simulator route tests
├── render.yaml            # Render Infrastructure-as-Code Blueprint (Backend + DB)
├── .env.example           # Configuration template for credentials & features
├── .gitignore             # Comprehensive security & environment ignore rules
├── requirements.txt       # Production Python dependencies
└── run_server.py          # Server entrypoint launcher
```

---

## 🛠️ Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** (for the React frontend)
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

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
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

# Execution Mode
DRY_RUN=true          # Set to false for live production API calls

# Database (Optional - leave blank or unset for automatic SQLite)
DATABASE_URL=postgresql://postgres:password@localhost:5432/revenue_db

# Payment Gateways (Required for live mode)
PREFERRED_PSP=stripe  # or razorpay
STRIPE_API_KEY=sk_test_...
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Communications (Required for live mode)
FROM_EMAIL=recovery@yourdomain.com
SENDGRID_API_KEY=SG....
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 4. Run Locally (Recommended for Development)

**Terminal 1 — Start the Backend:**
```bash
cd ai-revenue-v1
.\venv\Scripts\python.exe run_server.py     # Windows
# python run_server.py                      # Linux/macOS
```

**Terminal 2 — Start the Frontend:**
```bash
cd ai-revenue-v1/frontend
npm run dev
```

Access the application:
- 🎛️ **Dashboard**: [http://localhost:5173](http://localhost:5173)
- 📖 **API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🚀 Cloud Deployment (Render + Vercel)

The platform is designed to deploy seamlessly with zero infrastructure headache:

### Part 1: Deploy Backend & PostgreSQL on Render

1. **Create Managed PostgreSQL Database:**
   - On [Render](https://dashboard.render.com), click **New +** → **PostgreSQL**.
   - Set Name: `ai-revenue-db`, Database: `revenue_db`, Plan: **Free**.
   - Copy the **Internal Database URL**.

2. **Deploy FastAPI Web Service:**
   - Click **New +** → **Web Service** and connect your GitHub repo.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run_server.py`
   - Add Environment Variables:
     - `DATABASE_URL`: *(paste PostgreSQL URL from Step 1)*
     - `GEMINI_API_KEY`: *(your Gemini API key)*
     - `DRY_RUN`: `true` *(or `false` for live mode)*
     - `PYTHON_VERSION`: `3.11.9`
   - Copy your public backend URL (e.g. `https://ai-revenue-backend.onrender.com`).

### Part 2: Deploy React Frontend on Vercel

1. On [Vercel](https://vercel.com), click **Add New...** → **Project** and import this repo.
2. Edit **Root Directory** → Select **`frontend`**.
3. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://ai-revenue-backend.onrender.com` *(your Render backend URL)*
4. Click **Deploy**.

---

## 🚀 Going Live — Production Gateways

To switch from simulation to processing real payments:

### Step 1: Set Your API Keys
```env
DRY_RUN=false
STRIPE_API_KEY=sk_live_xxxxx
RAZORPAY_KEY_ID=rzp_live_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
SENDGRID_API_KEY=SG.xxxxx
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### Step 2: Configure Webhook Endpoints
Point your payment gateway webhooks to your deployed Render URL:

| Gateway | Webhook URL | Events to Subscribe |
| :--- | :--- | :--- |
| **Stripe** | `https://ai-revenue-backend.onrender.com/webhooks/psp` | `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.failed`, `charge.succeeded`, `checkout.session.completed`, `invoice.payment_succeeded` |
| **Razorpay** | `https://ai-revenue-backend.onrender.com/webhooks/psp` | `payment.captured`, `payment.failed`, `payment_link.paid`, `order.paid` |
| **ERP / Billing** | `https://ai-revenue-backend.onrender.com/webhooks/billing` | Overdue invoices, billing anomalies |

### What Happens When You Go Live
1. **Real Stripe PaymentIntents** are created via `stripe.PaymentIntent.create()`
2. **Real Razorpay Payment Links** are generated via `razorpay_client.payment_link.create()`
3. **Real Emails** are sent through SendGrid with personalized recovery content
4. **Real SMS** messages are dispatched via Twilio with shortlinks
5. **Real Slack Alerts** fire to your operations channel with resolve buttons
6. **Inbound success webhooks** auto-resolve cases and update recovery metrics in real-time

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
| `GET` | `/api/health` | Server health check with integration status. |
| `GET` | `/dashboard/stats` | Returns live KPI telemetry ($ at Risk, $ Recovered, Recovery Rate, Active Cases). |
| `GET` | `/dashboard/cases` | Retrieves active and historical recovery cases with AI reasoning logs. |
| `GET` | `/admin/action-logs` | Fetches the real-time communication audit trail (Email, SMS, Slack, Links). |
| `GET` | `/api/customers` | Returns holistic customer 360 data, LTV, segment, and risk tier categorization. |
| `GET` | `/api/analytics` | Returns recovery funnel conversion rates, gateway volumes, and channel metrics. |
| `POST` | `/webhooks/psp` | Ingests Stripe & Razorpay webhooks (`payment_failed`, `charge.failed`, `payment_intent.succeeded`). |
| `POST` | `/webhooks/billing` | Ingests overdue invoices and billing anomalies from ERP systems. |
| `POST` | `/admin/simulate` | 1-Click test harness to simulate payment failures, drop-offs, and auto-resolutions. |
| `POST` | `/admin/process` | Triggers immediate evaluation and processing of pending/scheduled recovery actions. |
| `POST` | `/admin/resolve/{case_id}` | Manually resolves an open case and marks invoice as recovered. |

---

## 🗺️ Next Phases & Roadmap

```mermaid
timeline
    title AI Revenue Recovery Platform Evolution
    Phase 1 (Complete) : Hybrid Rules + Gemini LLM Diagnostics
            : Dual-Gateway Razorpay & Stripe Links
            : Checkout Drop-Off & 3DS Friction Recovery
            : Modern React 19 + shadcn/ui Frontend
            : Closed-Loop Webhook Auto-Resolution
            : Render & Vercel Cloud Deployment
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
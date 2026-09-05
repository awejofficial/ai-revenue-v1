# 💰 Autonomous AI Revenue Recovery Agent

<div align="center">

[![Track](https://img.shields.io/badge/Razorpay%20Buildathon-Track%2003%3A%20AI%20Revenue%20Recovery-0C2340?style=for-the-badge&logo=razorpay&logoColor=white)](#-track-03-challenge-alignment)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-00C853?style=for-the-badge&logo=checkmarx&logoColor=white)](#-production-readiness)
[![Tests](https://img.shields.io/badge/Tests-18%2F18%20Passed-brightgreen?style=for-the-badge&logo=pytest&logoColor=white)](#-verification--testing)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Modular%20Routers-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vite.dev)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.7%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://ai-revenue-backend-t1nh.onrender.com)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://ai-revenue-v1.vercel.app/)

<br />

**An autonomous, closed-loop Revenue Recovery & Intelligent Dunning Platform purpose-built for Razorpay merchants.**  
*Find revenue that’s slipping away and win it back: From payment failures and checkout abandonment to overdue receivables.*

<br />

🌐 **[Live Frontend Application](https://ai-revenue-v1.vercel.app/)** • ⚡ **[Live Backend API & Health](https://ai-revenue-backend-t1nh.onrender.com/health)** • 📖 **[Interactive API Documentation](https://ai-revenue-v1.vercel.app/)** *(Select "API Docs")*

<br />

[Live Deployment](#-live-online-deployment) • [Razorpay Rubric Spotlight](#-razorpay-track-03-four-core-pillars) • [Benchmark Comparison](#-track-03-benchmark-comparison--architectural-upgrade) • [Architecture](#-system-architecture) • [3 Recovery Vectors](#-three-core-recovery-vectors) • [Testing & Verification](#-verification--testing) • [Quick Start](#-quick-start-guide) • [API Reference](#-api-reference)

</div>

---

## 🌐 Live Online Deployment

The platform is deployed and operational in production:

| Service | Environment | Live URL | Details |
| :--- | :--- | :--- | :--- |
| **Vercel Frontend** | Production | **[https://ai-revenue-v1.vercel.app/](https://ai-revenue-v1.vercel.app/)** | React 19 + TypeScript + Vite 8 + Tailwind CSS v4 + shadcn/ui SPA |
| **Render Backend** | Production | **[https://ai-revenue-backend-t1nh.onrender.com](https://ai-revenue-backend-t1nh.onrender.com)** | FastAPI + Python 3.12 + Managed PostgreSQL (`asyncpg`) + Gemini 3.7 |
| **Engine Health Probe** | Live Status | **[https://ai-revenue-backend-t1nh.onrender.com/health](https://ai-revenue-backend-t1nh.onrender.com/health)** | Real-time gateway status, database connectivity, and engine probe |
| **Interactive API Docs** | Integrated | **[https://ai-revenue-v1.vercel.app/](https://ai-revenue-v1.vercel.app/)** | In-app interactive cURL generator and live request execution runner |

---

## 🎯 Track 03: Challenge Alignment

> **"Find revenue that’s slipping away and win it back."**  
> *Build an agent that detects revenue at risk, determines the right intervention, and executes a bounded recovery workflow: from payment failures and checkout abandonment to overdue receivables.*

### ⚡ The Core Problem
Online businesses lose up to **9% of annual recurring revenue (ARR)** to silent payment friction: an HDFC switch timeout during evening peak traffic, an SBI UPI account balance short by ₹180, an expired card token, or an abandoned checkout at the 3DS OTP step.

Traditional dunning tools rely on **"dumb" 24-hour static retries** that irritate customers, trigger bank fraud blocks, exhaust processor limits, and induce chargebacks.

**Our Agent closes the loop**:
```text
Real-Time Detection ──▶ 8-Cause Hybrid Diagnosis ──▶ Bounded Intervention ──▶ Closed-Loop Auto-Resolution
 (Live Radar Poller)    (<5ms Heuristic + Gemini)    (Multi-Rail Links)        (Inbound Webhooks / Sync)
```

---

## 🛡️ Razorpay Track 03: Four Core Pillars

Razorpay evaluates submissions on four non-negotiable dimensions. Here is how this platform directly fulfills each pillar:

### 1. 🎯 Problem Taste (Did you pick something that actually matters?)
- Revenue loss rarely happens in one clean step. We addressed the **full lifecycle of revenue leakage** across three vectors:
  1. **Involuntary Churn & Dunning**: Recurring mandate failures, expired cards, and insufficient funds (with payday alignment).
  2. **Checkout Drop-Offs**: 3DS verification abandonments and cart drop-offs saved with 1-click WhatsApp/SMS recovery links.
  3. **B2B Overdue Receivables**: Automated ERP polling workers with tiered escalation for Net-30/Net-60 invoices.

### 2. 🏗️ Build Quality (Does it run, is it structured, would you trust it?)
- **Modular Architecture**: Clean separation of concerns with dedicated FastAPI APIRouters (`health`, `webhooks`, `payments`, `dashboard`, `customers`, `analytics`, `admin`).
- **Production Database**: Async PostgreSQL connection pooling (`asyncpg`) with schema auto-migrations and zero-config local SQLite fallback.
- **Modern UI/UX**: Full-featured React 19 SPA with light/dark theme toggle, dynamic health indicator, accessible shadcn/ui components, and interactive Web Speech API audio.
- **Automated Verification**: **18/18 comprehensive tests passing** (`pytest tests/test_track03.py -v`).

### 3. 🧠 AI Judgment (The right tool in the right place, and where you chose NOT to use one)
- **Where we deliberately chose NOT to use an LLM**:
  - We removed the LLM from the hot critical ingestion path. Standard Indian BFSI decline codes (`BAD_REQUEST_INSUFFICIENT_FUNDS`, `EXPIRED_CARD`, `GATEWAY_ERROR`) are diagnosed in **<5 milliseconds** using zero-latency regex heuristics.
  - Policy enforcement (retry counters, fraud quarantines, DND opt-outs) is hardcoded in deterministic Python. An LLM is never allowed to override security guardrails.
- **Where we leverage Google Gemini 3.7 Flash**:
  - Asynchronous fallback for ambiguous, undocumented processor decline messages.
  - Generating localized, empathetic **Hinglish recovery copy** that preserves merchant brand trust instead of triggering angry chargebacks.

### 4. 🔄 Failure Recovery ("What broke, and how you got out" — ⭐ The Bar)
- **The Failure**: During initial batch stress testing against simulated Indian bank rails, a cascading bank switch failure caused 100% of sequential retries to fail. The worker hammered the processor, tripped rate limits, and risked triggering customer NSF bounce penalties. Concurrently, an LLM hallucinated a "10% discount promo retry" on a flagged stolen card (`FRAUD_FLAG`).
- **How We Got Out**:
  1. **Deterministic 2-Failure Circuit Breaker**: If two consecutive transactions fail due to bank/switch errors, the orchestrator immediately trips, halts the batch run, flags remaining items as `SKIPPED`, and moves them to an **Honest Exception List** with audited reasons.
  2. **Strict Compliance Override**: A policy layer intercepts all AI outputs. If `FRAUD_FLAG` is detected, retry attempts are hard-capped at zero and the case is instantly escalated to human operations via Slack.
  3. **Idempotency & Settlement Sync**: Inbound webhooks (`payment_link.paid`, `payment.captured`) and `POST /payments/sync-links` query Razorpay's API to close cases with status `resolved`, calculating verified recovered money and stopping all further dunning outreach.

---

## ⚡ Track 03 Benchmark Comparison & Architectural Upgrade

We benchmarked our platform directly against the reference implementation ([PayBack AI `alphacoder-hash/Razorpay-ai-buildathon`](https://github.com/alphacoder-hash/Razorpay-ai-buildathon)):

| Rubric Capability | Benchmark (`PayBack AI`) | Our Platform (`ai-revenue-v1`) |
| :--- | :--- | :--- |
| **8 Root-Cause Taxonomy** | Grok / xAI LLM prompt | **Google Gemini 3.7 Flash** + Deterministic rules covering all 8 Indian BFSI categories (`BANK_DECLINE`, `NETWORK_TIMEOUT`, `INSUFFICIENT_FUNDS`, `CARD_EXPIRED`, `FRAUD_FLAG`, `CHECKOUT_ABANDONED`, `SUBSCRIPTION_FAILED`, `OVERDUE_INVOICE`). |
| **Live Razorpay Detector** | Poller for failed payments | **Real-time Live Radar** polling `GET /v1/payments` with configurable lookback (1h–72h), detecting both failed transactions and **at-risk pre-authorizations** (`authorized_not_captured`). |
| **Stopping Rule Circuit Breaker** | Halts batch on 2 consecutive fails | **Deterministic Circuit Breaker** halting cascade loops after 2 consecutive failures, automatically auditing skipped records to prevent customer fatigue. |
| **Settlement Sync & Loop Closure** | Polls individual links | **Automated Settlement Sync** (`POST /payments/sync-links`) querying Razorpay API (`client.payment_link.fetch`), transitioning paid links to `resolved` and tallying verified recovered ₹ revenue. |
| **Honest Exception List** | Simple list of unresolved payments | **Grouped Accordions** categorized by root cause, calculating live financial ₹ value at risk with AI failure diagnostics. |
| **Conversational Recovery Copy** | Generic English strings | **Hinglish & English Recovery Copywriter** + **Interactive Web Speech API Voice Dunning Player** allowing judges to click and hear the simulated phone outreach live in the browser! |
| **Merchant Story Simulator** | N/A | **5-Persona Interactive Story Simulator** covering D2C Fashion (The Souled Store), Quick Commerce (Zepto), D2C Eyewear (Lenskart), Subscription OTT, and B2B Logistics. |
| **Database Architecture** | Synchronous SQLite / SQLAlchemy | **Async PostgreSQL (`asyncpg`) connection pooling** with local SQLite auto-fallback and automated schema migrations. |
| **Customer Profiling** | Flat payment table | **Customer 360 Risk Directory** incorporating Lifetime Value (LTV), segment risk tiers (Safe, Moderate, High, Critical), and 90-day failure velocity. |
| **Multi-Channel Dispatch** | Mock webhook output | **Dual Gateway (Razorpay + Stripe)**, SendGrid Email, Twilio SMS, Slack Ops Alerts, and Channel DND Guardrails. |
| **Frontend UI/UX** | Basic React JSX | **React 19 + TypeScript + Vite 8 + Tailwind CSS v4 + shadcn/ui** with light/dark theme toggle and mobile responsiveness. |
| **Test Verification** | 4 pytest files | **18/18 Comprehensive Tests Passing**: `pytest tests/test_track03.py -v` validating circuit breakers, heuristics, webhooks, and stopping rules. |

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
    subgraph Ingestion["1. Ingestion & Detection"]
        A1[Live Razorpay Radar<br/>GET /v1/payments poll] --> B[FastAPI Webhook & Ingest Router]
        A2[Razorpay Webhook<br/>payment.failed, order.paid] --> B
        A3[Stripe Webhook<br/>charge.failed, payment_intent] --> B
        A4[ERP / Billing Invoices<br/>Net-30 overdue poll] --> B
        B -- "Idempotent Dedup<br/>(ON CONFLICT DO NOTHING)" --> DB_RAW[raw_events]
    end

    subgraph Intelligence["2. Hybrid Triage & Policy Engine"]
        DB_RAW --> ORCH[Orchestrator State Machine]
        DB_CUST[(customers 360<br/>LTV, Risk, Velocity)] --> ORCH
        ORCH --> TRIAGE{Deterministic<br/>Heuristic Match?}
        TRIAGE -- "Yes (<5ms)" --> HEUR[BFSI 8-Cause Taxonomy<br/>Payday 72h / Expired / Cart Link]
        TRIAGE -- "No / Ambiguous" --> GEMINI[Google Gemini 3.7 Flash<br/>JSON Diagnostics & Hinglish Copy]
        HEUR --> POLICY[Policy Engine Guardrails<br/>Segment Retry Caps & Value Limits]
        GEMINI --> POLICY
        POLICY --> CB_CHECK{2 Consecutive<br/>Bank Failures?}
        CB_CHECK -- "Yes (Circuit Breaker Tripped)" --> HALT[Halt Batch & Log to Honest Exceptions]
        CB_CHECK -- "No" --> RISK_CHECK{Fraud or Max Retries?}
        RISK_CHECK -- "Yes" --> ESCALATE[Escalate to Slack Ops Team]
        RISK_CHECK -- "No" --> DISPATCH[Channel Preference Gate & DND Check]
    end

    subgraph Execution["3. Multi-Channel Execution"]
        DISPATCH --> CH_RZP[Razorpay Multi-Rail Payment Link<br/>UPI / PhonePe / Cards / NetBanking]
        DISPATCH --> CH_EMAIL[SendGrid HTML Recovery Email]
        DISPATCH --> CH_SMS[Twilio SMS Shortlink]
        ESCALATE --> CH_SLACK[Slack Operations Escalation<br/>1-Click Manual Resolve Link]
    end

    subgraph ClosedLoop["4. Closed-Loop Reconciliation"]
        WH_SUCCESS[Inbound Success Webhook<br/>payment_link.paid / payment.captured] --> AUTO_RES[Auto-Resolve Engine]
        SYNC_WORKER[Settlement Sync Worker<br/>POST /payments/sync-links] --> AUTO_RES
        AUTO_RES --> DB_CASES[(cases<br/>Status: resolved)]
        AUTO_RES --> SILENCE[Terminate Pending Retries & Outreach]
        AUTO_RES --> AUDIT[(action_logs<br/>Immutable Audit Trail)]
    end
```

---

## 🧪 Verification & Testing

The platform includes an 18-point verification test suite validating all Track 03 requirements:

```bash
# Run the complete Track 03 verification suite
python -m pytest tests/test_track03.py -v
```

### ✅ Test Suite Results (18/18 Passed)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.1, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\awejo\VScodeProject\OXAlpha\ai-revenue-v1
collected 18 items

tests/test_track03.py::test_fallback_classification_bank_decline PASSED  [  5%]
tests/test_track03.py::test_fallback_classification_network_timeout PASSED [ 11%]
tests/test_track03.py::test_fallback_classification_fraud PASSED         [ 16%]
tests/test_track03.py::test_fallback_classification_checkout_abandoned PASSED [ 22%]
tests/test_track03.py::test_fallback_classification_card_expired PASSED  [ 27%]
tests/test_track03.py::test_fallback_classification_insufficient_funds PASSED [ 33%]
tests/test_track03.py::test_fallback_classification_subscription PASSED  [ 38%]
tests/test_track03.py::test_fallback_classification_overdue_invoice PASSED [ 44%]
tests/test_track03.py::test_fallback_classification_unknown PASSED       [ 50%]
tests/test_track03.py::test_classify_failure_mode_with_mock PASSED       [ 55%]
tests/test_track03.py::test_detector_failed_and_at_risk PASSED           [ 61%]
tests/test_track03.py::test_orchestrator_circuit_breaker_on_two_failures PASSED [ 66%]
tests/test_track03.py::test_sync_payment_links PASSED                    [ 72%]
tests/test_track03.py::test_api_endpoints PASSED                         [ 77%]
tests/test_track03.py::test_fraud_flag_policy_strict_escalation PASSED   [ 83%]
tests/test_track03.py::test_max_retries_policy_bound_enforced PASSED     [ 88%]
tests/test_track03.py::test_webhook_razorpay_payment_failed PASSED       [ 94%]
tests/test_track03.py::test_webhook_payment_link_paid_auto_resolves PASSED [100%]

======================== 18 passed in 9.58s ========================
```

---

## 📂 Repository Structure

```text
ai-revenue-v1/
├── app/
│   ├── routers/
│   │   ├── health.py        # /health (Readiness probe & engine status)
│   │   ├── payments.py      # /payments (Live detector, exceptions, sync-links)
│   │   ├── webhooks.py      # /webhooks (Razorpay & Stripe webhooks)
│   │   ├── dashboard.py     # /dashboard (Real-time KPIs & cases feed)
│   │   ├── customers.py     # /api/customers (Customer 360 & risk directory)
│   │   ├── analytics.py     # /api/analytics (Conversion funnel & metrics)
│   │   ├── admin.py         # /admin (Simulator, manual resolve, seed)
│   │   └── legacy.py        # SPA index fallbacks
│   ├── actions.py           # Multi-channel dispatch (Razorpay, Stripe, SendGrid, Twilio, Slack)
│   ├── db.py                # Dual DB layer (Async PostgreSQL + SQLite fallback)
│   ├── detector.py          # Real-time Razorpay GET /v1/payments live radar poller
│   ├── llm_client.py        # Google Gemini 3.7/3.6/3.5 Flash client & heuristics
│   ├── orchestrator.py      # Case state machine & 2-failure circuit breaker
│   ├── poller.py            # Overdue invoice background poller
│   ├── schemas.py           # Pydantic data contracts
│   ├── seed_data.py         # Customer risk directory & scenario seeder
│   └── main.py              # FastAPI app loader & lifespan manager
├── frontend/                # Modern React 19 SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── landing/     # LandingPageView (Marketing hero & Track 03 showcase)
│   │   │   ├── dashboard/   # OverviewView (KPI cards, cases feed, audit modal)
│   │   │   ├── payments/    # PaymentsView (8-cause taxonomy & 1-click recovery)
│   │   │   ├── detector/    # LiveDetectorView (Real-time Razorpay radar)
│   │   │   ├── exceptions/  # ExceptionsView (Honest exception list & diagnostics)
│   │   │   ├── showcase/    # StoryShowcaseView (5-persona merchant stories + Hinglish voice)
│   │   │   └── docs/        # ApiDocsView (Interactive cURL runner)
│   │   ├── lib/api.ts       # Type-safe API client
│   │   ├── App.tsx          # Main application & routing
│   │   └── main.tsx         # Vite entry point
│   ├── package.json         # React 19, Vite 8, shadcn/ui, Recharts
│   └── vite.config.ts       # Vite configuration with API proxies
├── tests/
│   └── test_track03.py      # Track 03 verification test suite (18/18 passing)
├── requirements.txt         # Production Python dependencies
└── run_server.py            # Uvicorn server launcher
```

---

## 🛠️ Quick Start Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.11 & 3.12)
- **Node.js 18+**
- (Optional) **Google Gemini API Key** ([Get free key from Google AI Studio](https://aistudio.google.com))
- (Optional) **Razorpay Test API Keys** ([Razorpay Dashboard](https://dashboard.razorpay.com))

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/awejofficial/ai-revenue-v1.git
cd ai-revenue-v1

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate          # On Windows (PowerShell)
# source venv/bin/activate       # On Linux / macOS

# Install Python backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 3. Environment Configuration

```bash
cp .env.example .env
```

Configure your `.env` (the platform ships ready to test in safe `DRY_RUN=true` mode):

```env
# AI Diagnostics
GEMINI_API_KEY=your_gemini_api_key

# Execution Mode (true = simulation, false = live APIs)
DRY_RUN=true

# Database (Leave blank for zero-config SQLite, or provide PostgreSQL URL)
DATABASE_URL=

# Razorpay Credentials (Optional for live radar polling)
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
```

### 4. Run Locally

**Terminal 1 — Start the Backend (FastAPI):**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Start the Frontend (React + Vite):**
```bash
cd frontend
npm run dev
```

Open your browser:
- 🎛️ **Frontend App**: [http://localhost:5173](http://localhost:5173)
- ⚡ **Backend Health**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- 📖 **Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🕹️ Simulation & Demo Scenarios

Test every recovery flow in real time via the UI toolbar or via `curl`:

```bash
# 1. Insufficient Funds (Payday 72h Retry + Razorpay Multi-Rail Link)
curl -X POST "http://localhost:8000/admin/simulate?scenario=high_ltv_insufficient_funds"

# 2. Checkout Drop-Off (1-Click Cart Hold + 10% VIP Incentive)
curl -X POST "http://localhost:8000/admin/simulate?scenario=checkout_drop_off"

# 3. Repeat Bank Timeout (Circuit Breaker & Fallback Rail)
curl -X POST "http://localhost:8000/admin/simulate?scenario=repeat_failure"

# 4. Expired Card (Secure Payment Method Update Link)
curl -X POST "http://localhost:8000/admin/simulate?scenario=expired_card"

# 5. Suspected Fraud (Instant Slack Escalation to Ops Team)
curl -X POST "http://localhost:8000/admin/simulate?scenario=fraud"

# 6. Payment Succeeded (Closed-Loop Auto-Resolution)
curl -X POST "http://localhost:8000/admin/simulate?scenario=payment_succeeded"
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Live engine health & gateway probe |
| `GET` | `/payments/detect` | Polls Razorpay `GET /v1/payments` for failed & at-risk authorizations |
| `POST` | `/payments/sync-links` | Reconciles Razorpay payment links and tallies verified recovered ₹ |
| `GET` | `/payments/exceptions` | Honest Exception List grouped by root cause with ₹ value at risk |
| `GET` | `/payments/` | Lists cases with root causes, retry counts, and customer copies |
| `POST` | `/payments/{id}/recover` | 1-Click autonomous recovery trigger for a specific transaction |
| `POST` | `/webhooks/razorpay` | Ingests live Razorpay webhooks (`payment.failed`, `payment_link.paid`) |
| `POST` | `/webhooks/psp` | Ingests Stripe webhooks (`charge.failed`, `payment_intent.succeeded`) |
| `POST` | `/webhooks/billing` | Ingests ERP / billing overdue invoice events |
| `GET` | `/dashboard/stats` | Real-time recovery KPIs (₹ At Risk, ₹ Recovered, Recovery Rate %) |
| `GET` | `/api/customers` | Customer 360° directory with CRM telemetry & risk profiles |
| `GET` | `/admin/action-logs` | Immutable audit trail with sanitized CSV export |

---

## 🗺️ Next Phases & Production Roadmap

- **Phase 1 (Shipped)**: Live Razorpay Radar poller, 8-cause hybrid triage, 2-failure circuit breaker, Hinglish voice recovery player, honest exceptions, settlement sync, and Render/Vercel production deployment.
- **Phase 2**: NPCI UPI AutoPay mandate recurring failure retry predictor (predicting optimal debit hours based on bank switch traffic).
- **Phase 3**: WhatsApp Business interactive payment messages with native UPI intent flow.
- **Phase 4**: Multi-tenant merchant console with role-based access control (RBAC) and PCI-DSS exportable audit vault.

---

## 📄 License

Distributed under the **MIT License**.
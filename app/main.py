# app/main.py
"""
Revenue Recovery Agent - FastAPI Webhook Server & Live Console
"""

import json
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from app.db import init_db, get_pool
from app.orchestrator import (
    process_pending_events,
    process_scheduled_cases,
    process_event,
    resolve_case
)
from app.poller import ingest_overdue_invoices


# --- Lifespan Manager (Startup / Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Process any initial pending items
    asyncio.create_task(process_pending_events())
    
    async def background_worker():
        print("[Worker] Background Orchestrator active. Checking events every 15 seconds...")
        while True:
            try:
                await process_pending_events()
                await process_scheduled_cases()
            except Exception as e:
                print(f"[Worker] Background poller error: {e}")
            await asyncio.sleep(15)
    
    worker_task = asyncio.create_task(background_worker())
    
    yield  # Application runs
    
    # Shutdown
    worker_task.cancel()
    print("[Worker] Background Orchestrator stopped.")


app = FastAPI(
    title="Autonomous AI Revenue Recovery Agent",
    version="1.0.0",
    description="Autonomous AI-driven dunning and revenue recovery engine with Stripe, Razorpay, SendGrid, Twilio, and Slack integrations.",
    lifespan=lifespan
)


# --- Health Check ---
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "message": "Autonomous AI Revenue Recovery Agent is online.",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }


# ============================================================
# 1. PSP WEBHOOK (Stripe & Razorpay - Failure + Success)
# ============================================================
@app.post("/webhooks/psp")
async def psp_webhook(request: Request):
    """
    Ingests payment gateway webhooks for Stripe & Razorpay.
    Handles payment failure events (to initiate recovery) AND payment success events (to auto-resolve cases).
    """
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = raw_body.get('type') or raw_body.get('event') or 'unknown'
    event_id = raw_body.get('id') or f"wh_{int(datetime.utcnow().timestamp())}"
    
    # ----------------------------------------------------
    # A. SUCCESS / AUTO-RESOLUTION EVENTS
    # ----------------------------------------------------
    success_events = [
        "payment_intent.succeeded", "charge.succeeded", "checkout.session.completed", "invoice.payment_succeeded",
        "payment.captured", "payment_link.paid", "order.paid"
    ]
    
    if any(s in event_type.lower() for s in success_events):
        # Extract customer & amount
        customer_id = None
        amount = 0.0
        case_id = None
        
        # Stripe Success Payload
        if "data" in raw_body and "object" in raw_body["data"]:
            obj = raw_body["data"]["object"]
            customer_id = obj.get("customer") or obj.get("customer_id")
            amount = (obj.get("amount") or obj.get("amount_received") or 0) / 100.0
            meta = obj.get("metadata", {})
            if meta.get("case_id"):
                try:
                    case_id = int(meta["case_id"])
                except Exception:
                    pass
        
        # Razorpay Success Payload
        elif "payload" in raw_body:
            entity = (
                raw_body.get("payload", {}).get("payment", {}).get("entity") or
                raw_body.get("payload", {}).get("payment_link", {}).get("entity") or {}
            )
            customer_id = entity.get("customer_id") or entity.get("notes", {}).get("customer_id")
            amount = (entity.get("amount") or 0) / 100.0
            notes = entity.get("notes", {})
            if notes.get("case_id"):
                try:
                    case_id = int(notes["case_id"])
                except Exception:
                    pass
        
        if customer_id or case_id:
            res = await resolve_case(
                customer_id=customer_id,
                amount_recovered=amount,
                payment_reference=f"{event_type}:{event_id}",
                case_id=case_id
            )
            return {"status": "auto_resolved", "resolution": res}
        
        return {"status": "success_event_recorded", "message": "No matching customer found to resolve."}
    
    # ----------------------------------------------------
    # B. FAILURE / DUNNING EVENTS
    # ----------------------------------------------------
    customer_id = None
    amount = 0.0
    currency = "USD"
    failure_code = None
    failure_message = None
    
    # Stripe Failure Payload
    if "data" in raw_body and "object" in raw_body["data"]:
        obj = raw_body["data"]["object"]
        customer_id = obj.get("customer") or obj.get("customer_id")
        amount = (obj.get("amount") or 0) / 100.0
        currency = obj.get("currency", "USD").upper()
        failure_code = obj.get("failure_code") or (obj.get("last_payment_error") or {}).get("code")
        failure_message = obj.get("failure_message") or (obj.get("last_payment_error") or {}).get("message")
        
    # Razorpay Failure Payload
    elif "payload" in raw_body:
        entity = raw_body.get("payload", {}).get("payment", {}).get("entity", {})
        customer_id = entity.get("customer_id") or entity.get("notes", {}).get("customer_id") or "cus_rzp_unknown"
        amount = (entity.get("amount") or 0) / 100.0
        currency = entity.get("currency", "INR").upper()
        failure_code = entity.get("error_code") or "payment_failed"
        failure_message = entity.get("error_description") or "Razorpay payment failed"
        
    if not customer_id:
        customer_id = raw_body.get("customer_id", "cus_unknown")
    
    canonical_event = {
        "event_id": event_id,
        "customer_id": customer_id,
        "event_type": "payment_failed",
        "amount_usd": amount,
        "currency": currency,
        "raw_error_code": failure_code or "card_declined",
        "raw_error_message": failure_message or "Payment was declined by issuing bank"
    }
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO raw_events (event_id, event_type, customer_id, payload, canonical_event, is_processed) 
            VALUES ($1, $2, $3, $4, $5, FALSE)
            ON CONFLICT (event_id) DO NOTHING
            """,
            event_id,
            canonical_event["event_type"],
            customer_id,
            json.dumps(raw_body),
            json.dumps(canonical_event)
        )
    
    # Trigger autonomous processing in background immediately
    asyncio.create_task(process_event(event_id))
    
    return {"status": "ingested", "event_id": event_id, "customer_id": customer_id}


# ============================================================
# 2. BILLING SYSTEM OVERDUE INVOICE WEBHOOK
# ============================================================
@app.post("/webhooks/billing")
async def billing_webhook(request: Request):
    """Endpoint for internal Billing / ERP overdue invoice events."""
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    customer_id = raw_body.get('customer_id')
    invoice_id = raw_body.get('invoice_id')
    amount = float(raw_body.get('amount_due', 0))
    currency = raw_body.get('currency', 'USD')
    days_overdue = raw_body.get('days_overdue', 1)
    
    if not customer_id or not invoice_id:
        raise HTTPException(status_code=400, detail="customer_id and invoice_id are required")
    
    event_id = f"inv_{invoice_id}"
    canonical_event = {
        "event_id": event_id,
        "customer_id": customer_id,
        "event_type": "invoice_overdue",
        "amount_usd": amount,
        "currency": currency,
        "raw_error_code": "invoice_overdue",
        "raw_error_message": f"Invoice overdue by {days_overdue} days"
    }
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO raw_events (event_id, event_type, customer_id, payload, canonical_event, is_processed) 
            VALUES ($1, $2, $3, $4, $5, FALSE)
            ON CONFLICT (event_id) DO NOTHING
            """,
            event_id,
            canonical_event["event_type"],
            customer_id,
            json.dumps(raw_body),
            json.dumps(canonical_event)
        )
    
    asyncio.create_task(process_event(event_id))
    return {"status": "ingested", "event_id": event_id}


# ============================================================
# 3. ADMIN & SIMULATION CONTROLS
# ============================================================
@app.post("/admin/simulate")
async def simulate_event(
    scenario: str = Query(
        "high_ltv_insufficient_funds",
        description="Scenario to simulate: 'high_ltv_insufficient_funds', 'repeat_failure', 'expired_card', 'fraud', 'trial_user', 'payment_succeeded'"
    )
):
    """
    1-Click Simulator: Generates and executes test scenarios to demonstrate the AI recovery engine in real-time.
    """
    ts = int(datetime.utcnow().timestamp())
    
    if scenario == "high_ltv_insufficient_funds":
        ev = {
            "id": f"sim_high_ltv_{ts}",
            "customer_id": "cus_high_ltv_01",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "customer": "cus_high_ltv_01",
                    "amount": 49900,
                    "currency": "usd",
                    "failure_code": "insufficient_funds",
                    "failure_message": "Not enough balance in checking account"
                }
            }
        }
        
    elif scenario == "repeat_failure":
        ev = {
            "id": f"sim_repeat_{ts}",
            "customer_id": "cus_repeat_04",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "customer": "cus_repeat_04",
                    "amount": 8900,
                    "currency": "usd",
                    "failure_code": "insufficient_funds",
                    "failure_message": "Account balance below minimum threshold (3rd attempt)"
                }
            }
        }
    elif scenario == "expired_card":
        ev = {
            "id": f"sim_expired_{ts}",
            "customer_id": "cus_standard_02",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "customer": "cus_standard_02",
                    "amount": 4900,
                    "currency": "usd",
                    "failure_code": "card_expired",
                    "failure_message": "Card expiration date is in the past"
                }
            }
        }
    elif scenario == "fraud":
        ev = {
            "id": f"sim_fraud_{ts}",
            "customer_id": "cus_fraud_05",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "customer": "cus_fraud_05",
                    "amount": 35000,
                    "currency": "usd",
                    "failure_code": "suspected_fraud",
                    "failure_message": "High risk transaction flagged by automated fraud shield"
                }
            }
        }
    elif scenario == "trial_user":
        ev = {
            "id": f"sim_trial_{ts}",
            "customer_id": "cus_trial_03",
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "customer": "cus_trial_03",
                    "amount": 1900,
                    "currency": "usd",
                    "failure_code": "do_not_honor",
                    "failure_message": "Bank declined transaction for trial conversion"
                }
            }
        }
    elif scenario == "payment_succeeded":
        # Simulates inbound success for latest case
        pool = await get_pool()
        async with pool.acquire() as conn:
            open_case = await conn.fetchrow("""
                SELECT customer_id, amount_usd, case_id FROM cases 
                WHERE status IN ('awaiting_input', 'retrying', 'diagnosing', 'new')
                ORDER BY updated_at DESC LIMIT 1
            """)
            if open_case:
                res = await resolve_case(
                    customer_id=open_case['customer_id'],
                    amount_recovered=float(open_case['amount_usd'] or 0),
                    payment_reference=f"sim_stripe_success_{ts}",
                    case_id=open_case['case_id']
                )
                return {"status": "simulated_success", "scenario": scenario, "result": res}
            else:
                return {"status": "no_open_cases", "message": "No active open case found to resolve. Trigger a failure scenario first!"}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario '{scenario}'")
    
    # Process failure scenario
    canonical = {
        "event_id": ev["id"],
        "customer_id": ev["customer_id"],
        "event_type": "payment_failed",
        "amount_usd": ev["data"]["object"]["amount"] / 100.0,
        "currency": ev["data"]["object"].get("currency", "USD").upper(),
        "raw_error_code": ev["data"]["object"]["failure_code"],
        "raw_error_message": ev["data"]["object"]["failure_message"]
    }
    
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO raw_events (event_id, event_type, customer_id, payload, canonical_event, is_processed) 
            VALUES ($1, $2, $3, $4, $5, FALSE)
            ON CONFLICT (event_id) DO NOTHING
            """,
            ev["id"],
            "payment_failed",
            ev["customer_id"],
            json.dumps(ev),
            json.dumps(canonical)
        )
    
    await process_event(ev["id"])
    
    return {
        "status": "simulated_and_processed",
        "scenario": scenario,
        "event_id": ev["id"],
        "customer_id": ev["customer_id"]
    }


@app.post("/admin/process")
async def manual_process():
    """Manually triggers pending event processing and scheduled cases."""
    await process_pending_events()
    await process_scheduled_cases()
    return {"status": "processing_completed"}


@app.post("/admin/resolve/{case_id}")
async def manual_resolve(case_id: int):
    """Manually marks a case as resolved."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        case = await conn.fetchrow("SELECT * FROM cases WHERE case_id = $1", case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        res = await resolve_case(
            customer_id=case['customer_id'],
            amount_recovered=float(case['amount_usd'] or 0),
            payment_reference="Manual_Admin_Override",
            case_id=case_id
        )
        return res


@app.get("/admin/action-logs")
@app.get("/admin/action-logs/")
async def get_action_logs(limit: int = 50):
    """Fetches real-time communication logs (Email, SMS, Slack, Payment Links)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        logs = await conn.fetch("""
            SELECT id, case_id, customer_id, action_type, channel, recipient, status, details, created_at
            FROM action_logs
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)
        return [dict(log) for log in logs]


# ============================================================
# 4. DASHBOARD STATS & FEED APIS
# ============================================================
@app.get("/dashboard/stats")
@app.get("/dashboard/stats/")
async def dashboard_stats():
    """Returns real-time revenue recovery metrics."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) AS total_cases,
                COALESCE(COUNT(CASE WHEN status IN ('new', 'diagnosing', 'retrying', 'awaiting_input') THEN 1 END), 0) AS in_progress_cases,
                COALESCE(COUNT(CASE WHEN status = 'resolved' THEN 1 END), 0) AS resolved_cases,
                COALESCE(COUNT(CASE WHEN status = 'escalated' THEN 1 END), 0) AS escalated_cases,
                COALESCE(SUM(CASE WHEN status IN ('new', 'diagnosing', 'retrying', 'awaiting_input') THEN amount_usd ELSE 0 END), 0) AS at_risk,
                COALESCE(SUM(CASE WHEN status = 'resolved' THEN amount_usd ELSE 0 END), 0) AS recovered,
                COALESCE(SUM(CASE WHEN status = 'escalated' THEN amount_usd ELSE 0 END), 0) AS escalated,
                COALESCE(ROUND((SUM(CASE WHEN status = 'resolved' THEN amount_usd ELSE 0 END) / 
                       NULLIF(SUM(CASE WHEN status IN ('new', 'diagnosing', 'retrying', 'awaiting_input', 'resolved', 'escalated') THEN amount_usd ELSE 0 END), 0) * 100), 2), 0) AS recovery_rate
            FROM cases
        """)
        return dict(stats)


@app.get("/dashboard/cases")
@app.get("/dashboard/cases/")
async def dashboard_cases(limit: int = 30):
    """Returns the latest cases list."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        cases = await conn.fetch("""
            SELECT 
                case_id,
                customer_id,
                case_type,
                status,
                amount_usd,
                current_retry_count,
                max_retries,
                last_action,
                scheduled_next_action_at,
                llm_reasoning,
                created_at,
                updated_at
            FROM cases
            ORDER BY updated_at DESC
            LIMIT $1
        """, limit)
        return [dict(c) for c in cases]


# ============================================================
# 5. LIVE DASHBOARD CONSOLE (HTML)
# ============================================================
@app.get("/")
@app.get("/dashboard")
@app.get("/dashboard/")
async def dashboard_page():
    """Serves the live interactive revenue recovery dashboard."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Revenue Recovery Agent — Operations Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#F5F3EC;
    --paper-2:#EFEBDF;
    --card:#FFFFFF;
    --ink:#1C2321;
    --ink-soft:#5B6360;
    --hair:#DAD5C6;
    --hair-strong:#C6C0AC;
    --emerald:#0B6E4F;
    --emerald-100:#DCEBE3;
    --amber:#9C6B1F;
    --amber-100:#F3E6CC;
    --brick:#8C2F2F;
    --brick-100:#F1DCDA;
    --ledger:#2B4C7E;
    --ledger-100:#DCE4EF;
    --mono:'IBM Plex Mono',monospace;
    --serif:'Fraunces',serif;
    --sans:'Inter',sans-serif;
  }
  *{box-sizing:border-box;}
  body{
    margin:0;
    background:var(--paper);
    color:var(--ink);
    font-family:var(--sans);
    -webkit-font-smoothing:antialiased;
  }
  .wrap{max-width:1240px;margin:0 auto;padding:28px 24px 60px;}

  header{
    display:flex;justify-content:space-between;align-items:flex-end;
    border-bottom:1.5px solid var(--ink);
    padding-bottom:16px;margin-bottom:20px;
    gap:20px;flex-wrap:wrap;
  }
  .brand-eyebrow{
    font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;
    color:var(--ink-soft);margin-bottom:4px;
  }
  h1{
    font-family:var(--serif);font-weight:500;font-size:30px;margin:0;
    letter-spacing:-.01em;
  }
  .run-controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
  button{
    font-family:var(--sans);font-size:12px;padding:8px 12px;border-radius:4px;
    border:1px solid var(--ink);background:var(--ink);color:var(--paper);cursor:pointer;
    font-weight:500;transition:all .15s ease;
  }
  button:hover{background:#333c39;}
  button.secondary{background:var(--card);color:var(--ink);border-color:var(--hair-strong);}
  button.secondary:hover{background:var(--paper-2);}
  button.accent{background:var(--emerald);color:white;border-color:var(--emerald);}
  button.accent:hover{background:#09583f;}

  /* Simulation Toolbar */
  .sim-bar{
    background:var(--card);border:1px solid var(--hair-strong);border-radius:6px;
    padding:12px 16px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between;
    flex-wrap:wrap;gap:12px;
  }
  .sim-title{font-family:var(--mono);font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:600;}
  .sim-buttons{display:flex;gap:8px;flex-wrap:wrap;}
  .sim-btn{
    font-size:11.5px;padding:6px 10px;background:var(--paper-2);color:var(--ink);
    border:1px solid var(--hair-strong);border-radius:4px;cursor:pointer;
  }
  .sim-btn:hover{background:var(--paper);border-color:var(--ink);}

  .ledger-strip{
    display:grid;grid-template-columns:repeat(5,1fr);
    border:1px solid var(--hair-strong);border-radius:6px;overflow:hidden;
    background:var(--card);margin-bottom:24px;
  }
  @media (max-width:768px){.ledger-strip{grid-template-columns:1fr 1fr;}}
  .metric{padding:14px 16px;border-right:1px solid var(--hair);}
  .metric:last-child{border-right:none;}
  .metric-label{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft);margin-bottom:6px;}
  .metric-value{font-family:var(--serif);font-size:24px;font-weight:500;}
  .metric-value.emerald{color:var(--emerald);}
  .metric-value.brick{color:var(--brick);}
  .metric-sub{font-family:var(--mono);font-size:10.5px;color:var(--ink-soft);margin-top:2px;}

  .grid{display:grid;grid-template-columns:1.2fr 1fr;gap:20px;align-items:start;}
  @media (max-width:960px){.grid{grid-template-columns:1fr;}}

  .panel{background:var(--card);border:1px solid var(--hair-strong);border-radius:6px;overflow:hidden;}
  .panel-head{
    display:flex;justify-content:space-between;align-items:center;
    padding:12px 16px;border-bottom:1px solid var(--hair);background:var(--card);
  }
  .panel-head h2{font-family:var(--serif);font-size:16px;font-weight:500;margin:0;}
  .panel-head .count{font-family:var(--mono);font-size:11px;color:var(--ink-soft);}

  .feed{max-height:600px;overflow-y:auto;}
  .case-row{
    padding:12px 16px;border-bottom:1px solid var(--hair);
    display:grid;grid-template-columns:auto 1fr auto;gap:12px;align-items:center;
    cursor:pointer;position:relative;transition:background .15s;
  }
  .case-row:hover{background:var(--paper-2);}
  .case-row.selected{background:var(--ledger-100);}
  .case-id{font-family:var(--mono);font-size:11px;color:var(--ink-soft);white-space:nowrap;}
  .case-main .case-cust{font-size:13.5px;font-weight:500;}
  .case-main .case-meta{font-family:var(--mono);font-size:11px;color:var(--ink-soft);margin-top:2px;line-height:1.4;}
  .amount{font-family:var(--mono);font-size:13px;text-align:right;white-space:nowrap;}
  .stamp{
    font-family:var(--mono);font-weight:600;font-size:10px;letter-spacing:.09em;
    padding:2px 7px;border-radius:2px;border:1.4px solid;
    display:inline-block;text-transform:uppercase;margin-top:4px;
  }
  .stamp.recovered{color:var(--emerald);border-color:var(--emerald);background:var(--emerald-100);}
  .stamp.promised{color:var(--amber);border-color:var(--amber);background:var(--amber-100);}
  .stamp.escalated{color:var(--ledger);border-color:var(--ledger);background:var(--ledger-100);}
  .stamp.retrying{color:#92400e;border-color:#f59e0b;background:#fef3c7;}
  .stamp.lost{color:var(--ink-soft);border-color:var(--hair-strong);background:var(--paper-2);}

  .drawer{padding:18px;font-size:13px;}
  .drawer-empty{padding:40px 16px;text-align:center;color:var(--ink-soft);font-size:13px;}
  .drawer h3{font-family:var(--serif);font-size:18px;font-weight:500;margin:0 0 4px;}
  .drawer .sub{font-family:var(--mono);font-size:11px;color:var(--ink-soft);margin-bottom:14px;}
  .kv{display:grid;grid-template-columns:110px 1fr;gap:6px 10px;font-size:12px;margin-bottom:16px;}
  .kv div:nth-child(odd){color:var(--ink-soft);font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;padding-top:1px;}
  .timeline{border-left:2px solid var(--hair-strong);margin-left:6px;padding-left:14px;}
  .tl-item{position:relative;padding-bottom:14px;}
  .tl-item:last-child{padding-bottom:0;}
  .tl-item::before{content:'';position:absolute;left:-19px;top:4px;width:8px;height:8px;border-radius:50%;background:var(--ledger);border:2px solid var(--card);}
  .tl-item.win::before{background:var(--emerald);}
  .tl-item.stop::before{background:var(--brick);}
  .tl-time{font-family:var(--mono);font-size:10px;color:var(--ink-soft);}
  .tl-label{font-size:12.5px;font-weight:600;margin:1px 0;}
  .tl-detail{font-size:12px;color:var(--ink-soft);line-height:1.4;}

  .toast{position:fixed;bottom:20px;right:20px;background:var(--ink);color:white;padding:10px 16px;border-radius:4px;font-size:12px;font-family:var(--mono);display:none;z-index:999;}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div>
      <div class="brand-eyebrow">Autonomous AI Revenue Recovery Engine</div>
      <h1>Ledger Console</h1>
    </div>
    <div class="run-controls">
      <button class="secondary" id="refreshBtn">🔄 Refresh</button>
      <button class="secondary" id="processBtn">⚡ Run Background Cycle</button>
    </div>
  </header>

  <!-- Interactive 1-Click Simulation Sandbox -->
  <div class="sim-bar">
    <div class="sim-title">⚡ 1-Click Scenario Simulator</div>
    <div class="sim-buttons">
      <button class="sim-btn" onclick="triggerSim('high_ltv_insufficient_funds')">💎 High-LTV ($499 Payday Retry)</button>
      <button class="sim-btn" onclick="triggerSim('repeat_failure')">🔁 Repeat Offender (Billing Date Switch)</button>
      <button class="sim-btn" onclick="triggerSim('expired_card')">💳 Expired Card (Update Link)</button>
      <button class="sim-btn" onclick="triggerSim('fraud')">🚨 Fraud Risk (Slack Escalation)</button>
      <button class="sim-btn" onclick="triggerSim('trial_user')">⏳ Free Trial (1-Shot Retry)</button>
      <button class="sim-btn" style="background:var(--emerald-100);border-color:var(--emerald);color:var(--emerald);font-weight:600;" onclick="triggerSim('payment_succeeded')">✅ Inbound Payment (Auto-Resolve)</button>
    </div>
  </div>

  <div class="ledger-strip">
    <div class="metric">
      <div class="metric-label">Revenue at risk</div>
      <div class="metric-value" id="mAtRisk">$0.00</div>
      <div class="metric-sub" id="mCases">0 cases</div>
    </div>
    <div class="metric">
      <div class="metric-label">Recovered</div>
      <div class="metric-value emerald" id="mRecovered">$0.00</div>
      <div class="metric-sub" id="mRecoveredPct">0% of at-risk</div>
    </div>
    <div class="metric">
      <div class="metric-label">In Progress</div>
      <div class="metric-value" id="mInProgress">0</div>
      <div class="metric-sub">awaiting action / retrying</div>
    </div>
    <div class="metric">
      <div class="metric-label">Escalated</div>
      <div class="metric-value" id="mEscalated">0</div>
      <div class="metric-sub">human team intervention</div>
    </div>
    <div class="metric">
      <div class="metric-label">Recovery Rate</div>
      <div class="metric-value" id="mRecoveryRate">0%</div>
      <div class="metric-sub">success conversion</div>
    </div>
  </div>

  <div class="grid">
    <!-- Cases Feed -->
    <div class="panel">
      <div class="panel-head">
        <h2>Case feed</h2>
        <span class="count" id="feedCount">0 cases</span>
      </div>
      <div class="feed" id="feed">
        <div style="padding:30px;text-align:center;color:var(--ink-soft);">Loading cases...</div>
      </div>
    </div>

    <!-- Case Details & Audit Timeline -->
    <div class="panel">
      <div class="panel-head">
        <h2>Autonomous Audit Trail</h2>
        <span class="count" id="auditStatus">Select case</span>
      </div>
      <div id="drawer">
        <div class="drawer-empty">Click any case on the left to inspect customer context, AI reasoning, and execution logs.</div>
      </div>
    </div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
const feedEl = document.getElementById('feed');
const drawerEl = document.getElementById('drawer');
let allCases = [];
let selectedId = null;

function showToast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(()=>t.style.display='none', 3500);
}

function money(n){ return '$' + Number(n).toFixed(2); }
function fmtDate(d){ return d ? new Date(d).toLocaleString() : 'N/A'; }

function statusToStamp(status){
  const map = {
    'resolved': 'recovered',
    'escalated': 'escalated',
    'retrying': 'retrying',
    'awaiting_input': 'promised',
    'diagnosing': 'promised',
    'new': 'promised'
  };
  return map[status] || 'lost';
}

function statusLabel(status){
  const map = {
    'resolved': 'Recovered',
    'escalated': 'Escalated',
    'retrying': 'Retrying',
    'awaiting_input': 'Awaiting Action',
    'diagnosing': 'Diagnosing',
    'new': 'New'
  };
  return map[status] || status;
}

async function loadData(){
  try {
    const statsRes = await fetch('/dashboard/stats');
    const stats = await statsRes.json();
    
    document.getElementById('mAtRisk').textContent = money(stats.at_risk || 0);
    document.getElementById('mCases').textContent = (stats.total_cases || 0) + ' total cases';
    document.getElementById('mRecovered').textContent = money(stats.recovered || 0);
    const totalExposure = Number(stats.at_risk || 0) + Number(stats.recovered || 0);
    document.getElementById('mRecoveredPct').textContent = totalExposure > 0 ? ((Number(stats.recovered || 0) / totalExposure) * 100).toFixed(1) + '% conversion' : '0%';
    document.getElementById('mInProgress').textContent = stats.in_progress_cases || 0;
    document.getElementById('mEscalated').textContent = stats.escalated_cases || 0;
    document.getElementById('mRecoveryRate').textContent = (stats.recovery_rate || 0) + '%';

    const casesRes = await fetch('/dashboard/cases?limit=30');
    const cases = await casesRes.json();
    allCases = cases;
    document.getElementById('feedCount').textContent = cases.length + ' cases';
    
    feedEl.innerHTML = '';
    if (cases.length === 0) {
      feedEl.innerHTML = '<div style="padding:30px;text-align:center;color:var(--ink-soft);">No cases found. Click a simulation button above to trigger an event!</div>';
      return;
    }

    cases.forEach(c => {
      const stamp = statusToStamp(c.status);
      const label = statusLabel(c.status);
      const row = document.createElement('div');
      row.className = 'case-row' + (c.case_id === selectedId ? ' selected' : '');
      row.dataset.id = c.case_id;
      row.innerHTML = `
        <div class="case-id">#${c.case_id}</div>
        <div class="case-main">
          <div class="case-cust">${c.customer_id} <span style="font-size:11px;color:var(--ink-soft);">· ${c.case_type}</span></div>
          <div class="case-meta">${c.llm_reasoning || c.last_action || 'Processing...'}</div>
        </div>
        <div style="text-align:right;">
          <div class="amount">${money(c.amount_usd)}</div>
          <div class="stamp ${stamp}">${label}</div>
        </div>`;
      row.addEventListener('click', ()=>selectCase(c.case_id));
      feedEl.appendChild(row);
    });

    if (!selectedId && cases.length > 0) {
      selectCase(cases[0].case_id);
    } else if (selectedId) {
      const existing = cases.find(x => x.case_id === selectedId);
      if (existing) renderDrawer(existing);
    }

  } catch(e) {
    console.error('Failed to load dashboard data:', e);
  }
}

function selectCase(id){
  selectedId = id;
  document.querySelectorAll('.case-row').forEach(r => r.classList.toggle('selected', parseInt(r.dataset.id) === id));
  const c = allCases.find(x => x.case_id === id);
  if (c) renderDrawer(c);
}

function renderDrawer(c){
  const stamp = statusToStamp(c.status);
  const label = statusLabel(c.status);
  
  const items = [
    { time: fmtDate(c.created_at), label: 'Detected', detail: `Payment failure event ingested. Amount at risk: ${money(c.amount_usd)}.`, cls: '' },
    { time: fmtDate(c.updated_at), label: 'Diagnosed & Policy', detail: c.llm_reasoning || 'Rules/Gemini diagnosis evaluated.', cls: '' },
    { time: fmtDate(c.updated_at), label: 'Action Executed', detail: c.last_action || 'Action in progress.', cls: '' }
  ];

  if (c.status === 'resolved') {
    items.push({ time: fmtDate(c.updated_at), label: '✅ Revenue Recovered', detail: `Inbound payment confirmed. ${money(c.amount_usd)} recovered. Case closed.`, cls: 'win' });
  } else if (c.status === 'escalated') {
    items.push({ time: fmtDate(c.updated_at), label: '🚨 Human Escalation', detail: `Case dispatched to Slack for operations/account team review.`, cls: 'stop' });
  }

  let tlHtml = items.map(t => `
    <div class="tl-item ${t.cls}">
      <div class="tl-time">${t.time}</div>
      <div class="tl-label">${t.label}</div>
      <div class="tl-detail">${t.detail}</div>
    </div>`).join('');

  drawerEl.innerHTML = `
    <div class="drawer">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div>
          <h3>${c.customer_id}</h3>
          <div class="sub">Case #${c.case_id} · ${c.case_type} · ${money(c.amount_usd)}</div>
        </div>
        ${c.status !== 'resolved' ? `<button class="accent" style="font-size:11px;padding:4px 8px;" onclick="resolveManually(${c.case_id})">Mark Resolved</button>` : ''}
      </div>
      <div class="kv">
        <div>Status</div><div><span class="stamp ${stamp}">${label}</span></div>
        <div>Retries</div><div>${c.current_retry_count || 0} / ${c.max_retries || 3}</div>
        <div>Next Action</div><div>${fmtDate(c.scheduled_next_action_at)}</div>
        <div>AI Reason</div><div>${c.llm_reasoning || 'Deterministic rule'}</div>
        <div>Last Action</div><div>${c.last_action || 'None'}</div>
      </div>
      <h4 style="font-family:var(--serif);font-size:14px;margin:16px 0 8px;">Lifecycle Timeline</h4>
      <div class="timeline">${tlHtml}</div>
    </div>`;
}

async function triggerSim(scenario){
  showToast(`Simulating scenario: ${scenario}...`);
  try {
    const res = await fetch(`/admin/simulate?scenario=${scenario}`, {method: 'POST'});
    const data = await res.json();
    showToast(`Simulation complete: ${scenario}`);
    setTimeout(loadData, 300);
  } catch(e) {
    showToast(`Simulation error: ${e}`);
  }
}

async function resolveManually(caseId){
  try {
    const res = await fetch(`/admin/resolve/${caseId}`, {method: 'POST'});
    showToast(`Case #${caseId} resolved!`);
    loadData();
  } catch(e) {
    showToast(`Resolution error: ${e}`);
  }
}

document.getElementById('refreshBtn').addEventListener('click', loadData);
document.getElementById('processBtn').addEventListener('click', async ()=>{
  showToast('Running background cycle...');
  await fetch('/admin/process', {method: 'POST'});
  showToast('Cycle completed.');
  loadData();
});

loadData();
setInterval(loadData, 10000);
</script>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)
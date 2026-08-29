# app/main.py
"""
Revenue Recovery Agent - FastAPI Webhook Server & Live Console
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

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
        description="Scenario to simulate: 'high_ltv_insufficient_funds', 'checkout_drop_off', 'repeat_failure', 'expired_card', 'fraud', 'trial_user', 'payment_succeeded'"
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

    elif scenario == "checkout_drop_off":
        ev = {
            "id": f"sim_dropoff_{ts}",
            "customer_id": "cus_dropoff_06",
            "type": "checkout_drop_off",
            "data": {
                "object": {
                    "customer": "cus_dropoff_06",
                    "amount": 32000,
                    "currency": "usd",
                    "failure_code": "checkout_drop_off",
                    "failure_message": "Customer abandoned checkout at 3DS verification step"
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


@app.get("/api/customers")
@app.get("/api/customers/")
async def api_customers():
    """Returns all customers with aggregated CRM and case telemetry."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        customers_raw = await conn.fetch("SELECT * FROM customers ORDER BY customer_id ASC")
        cases_raw = await conn.fetch("SELECT customer_id, status, amount_usd, created_at FROM cases")
        
        # Aggregate cases by customer
        case_map = {}
        for c in cases_raw:
            cid = c['customer_id']
            if cid not in case_map:
                case_map[cid] = {"total": 0, "resolved": 0, "in_progress": 0, "escalated": 0, "recovered_amount": 0.0, "last_status": "none"}
            case_map[cid]["total"] += 1
            if c['status'] == 'resolved':
                case_map[cid]["resolved"] += 1
                case_map[cid]["recovered_amount"] += float(c['amount_usd'] or 0)
            elif c['status'] in ['new', 'diagnosing', 'retrying', 'awaiting_input']:
                case_map[cid]["in_progress"] += 1
            elif c['status'] == 'escalated':
                case_map[cid]["escalated"] += 1
            case_map[cid]["last_status"] = c['status']
            
        result = []
        for cust in customers_raw:
            crm = cust['crm_data']
            if isinstance(crm, str):
                try:
                    crm = json.loads(crm)
                except Exception:
                    crm = {}
            elif not isinstance(crm, dict):
                crm = {}
                
            cid = cust['customer_id']
            stats = case_map.get(cid, {"total": 0, "resolved": 0, "in_progress": 0, "escalated": 0, "recovered_amount": 0.0, "last_status": "clean"})
            
            result.append({
                "customer_id": cid,
                "name": crm.get("name", cid),
                "company": crm.get("company", "N/A"),
                "email": cust['email'],
                "phone": cust['phone'],
                "ltv": float(crm.get("ltv", 0)),
                "segment": crm.get("segment", "standard"),
                "plan": crm.get("plan", "monthly"),
                "country": crm.get("country", "US"),
                "cart_items": crm.get("cart_items", []),
                "cart_value": float(crm.get("cart_value", 0)),
                "cases_count": stats["total"],
                "resolved_count": stats["resolved"],
                "in_progress_count": stats["in_progress"],
                "recovered_amount": stats["recovered_amount"],
                "last_status": stats["last_status"]
            })
            
        return result


@app.get("/api/analytics")
@app.get("/api/analytics/")
async def api_analytics():
    """Returns aggregated funnel metrics, gateway breakdown, and channel performance."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) AS total_cases,
                COALESCE(COUNT(CASE WHEN status IN ('new', 'diagnosing', 'retrying', 'awaiting_input') THEN 1 END), 0) AS in_progress_cases,
                COALESCE(COUNT(CASE WHEN status = 'resolved' THEN 1 END), 0) AS resolved_cases,
                COALESCE(COUNT(CASE WHEN status = 'escalated' THEN 1 END), 0) AS escalated_cases,
                COALESCE(SUM(amount_usd), 0) AS total_at_risk,
                COALESCE(SUM(CASE WHEN status = 'resolved' THEN amount_usd ELSE 0 END), 0) AS total_recovered
            FROM cases
        """)
        
        # Action logs breakdown
        actions_raw = await conn.fetch("SELECT action_type, channel, status FROM action_logs")
        channels = {"email": 0, "sms": 0, "slack": 0, "razorpay": 0, "stripe": 0}
        for a in actions_raw:
            ch = (a['channel'] or '').lower()
            if 'email' in ch or 'sendgrid' in ch:
                channels["email"] += 1
            elif 'sms' in ch or 'twilio' in ch:
                channels["sms"] += 1
            elif 'slack' in ch:
                channels["slack"] += 1
            elif 'razorpay' in ch:
                channels["razorpay"] += 1
            elif 'stripe' in ch:
                channels["stripe"] += 1
                
        # Failure code breakdown
        raw_events = await conn.fetch("SELECT canonical_event FROM raw_events LIMIT 100")
        failure_codes = {"insufficient_funds": 0, "card_expired": 0, "checkout_drop_off": 0, "suspected_fraud": 0, "other": 0}
        for ev in raw_events:
            c = ev['canonical_event']
            if isinstance(c, str):
                try:
                    c = json.loads(c)
                except Exception:
                    c = {}
            code = (c.get('raw_error_code') or '').lower()
            if 'insufficient' in code:
                failure_codes["insufficient_funds"] += 1
            elif 'expired' in code:
                failure_codes["card_expired"] += 1
            elif 'drop_off' in code or 'cart' in code or 'checkout' in code:
                failure_codes["checkout_drop_off"] += 1
            elif 'fraud' in code:
                failure_codes["suspected_fraud"] += 1
            else:
                failure_codes["other"] += 1

        total = int(stats['total_cases'] or 0)
        resolved = int(stats['resolved_cases'] or 0)
        at_risk = float(stats['total_at_risk'] or 0)
        recovered = float(stats['total_recovered'] or 0)
        recovery_rate = round((recovered / at_risk * 100), 1) if at_risk > 0 else 0.0

        return {
            "funnel": {
                "detected": total,
                "diagnosed": total,
                "outreach_dispatched": len(actions_raw),
                "recovered_cases": resolved,
                "escalated_cases": int(stats['escalated_cases'] or 0),
                "at_risk_amount": at_risk,
                "recovered_amount": recovered,
                "recovery_rate_pct": recovery_rate
            },
            "channels": channels,
            "failure_codes": failure_codes,
            "gateways": {
                "stripe": {"name": "Stripe", "currency": "USD", "status": "active"},
                "razorpay": {"name": "Razorpay (UPI / NetBanking)", "currency": "INR", "status": "active"}
            }
        }


@app.get("/api/analytics/summary")
@app.get("/api/analytics/summary/")
async def api_analytics_summary():
    """Returns summarized stats for dashboard analytics."""
    return await dashboard_stats()


@app.get("/api/analytics/by-reason")
@app.get("/api/analytics/by-reason/")
async def api_analytics_by_reason():
    """Returns failure breakdown by root cause reason."""
    analytics = await api_analytics()
    return analytics.get("failure_codes", {})


@app.post("/api/simulate/recovery")
@app.post("/api/simulate/recovery/")
async def api_simulate_recovery(scenario: str = "payment_succeeded"):
    """Simulates recovery event."""
    return await simulate_event(scenario=scenario)


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
  /* Top Navigation */
  .top-nav{
    display:flex;justify-content:space-between;align-items:center;
    background:var(--card);border:1px solid var(--hair-strong);border-radius:8px;
    padding:10px 18px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.03);
    flex-wrap:wrap;gap:12px;
  }
  .nav-brand{display:flex;align-items:center;gap:10px;}
  .brand-logo{font-size:22px;}
  .brand-title{font-family:var(--serif);font-weight:600;font-size:16px;color:var(--ink);}
  .brand-sub{font-family:var(--mono);font-size:10px;color:var(--ink-soft);letter-spacing:.06em;text-transform:uppercase;}
  .nav-links{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
  .nav-link{
    font-size:12px;font-weight:500;padding:6px 12px;border-radius:5px;
    text-decoration:none;color:var(--ink-soft);transition:all .15s ease;
    border:1px solid transparent;
  }
  .nav-link:hover{color:var(--ink);background:var(--paper-2);}
  .nav-link.active{color:var(--ink);background:var(--paper-2);border-color:var(--hair-strong);font-weight:600;}
  .nav-status{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--emerald);}
  .status-dot{width:8px;height:8px;border-radius:50%;background:var(--emerald);display:inline-block;animation:pulse 2s infinite;}
  @keyframes pulse{0%{opacity:1;}50%{opacity:.4;}100%{opacity:1;}}

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
    transition:all .15s ease;
  }
  .sim-btn:hover{background:var(--paper);border-color:var(--ink);}
  .sim-btn.highlight{background:var(--emerald-100);color:var(--emerald);border-color:var(--emerald);font-weight:600;}
  .sim-btn.highlight:hover{background:#cbe2d6;}

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

  /* Case Filter Pills */
  .case-filter-pills{display:flex;gap:4px;flex-wrap:wrap;}
  .case-pill{
    font-family:var(--sans);font-size:10.5px;padding:3.5px 7px;border-radius:3px;
    border:1px solid var(--hair-strong);background:var(--paper-2);color:var(--ink-soft);
    cursor:pointer;transition:all .15s ease;font-weight:500;
  }
  .case-pill:hover{color:var(--ink);background:var(--paper);border-color:var(--ink);}
  .case-pill.active{background:var(--ink);color:var(--paper);border-color:var(--ink);font-weight:600;}

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

  <!-- Top Navigation Bar -->
  <nav class="top-nav">
    <div class="nav-brand">
      <span class="brand-logo">💰</span>
      <div>
        <div class="brand-title">Autonomous AI Revenue Recovery</div>
        <div class="brand-sub">Enterprise Dunning & Win-Back Agent</div>
      </div>
    </div>
    <div class="nav-links">
      <a href="/dashboard" class="nav-link active">📊 Operations Hub</a>
      <a href="/customers" class="nav-link">👥 Customer 360°</a>
      <a href="/analytics" class="nav-link">📈 Recovery Funnel</a>
      <a href="/docs" target="_blank" class="nav-link">⚡ API Docs ↗</a>
    </div>
    <div class="nav-status">
      <span class="status-dot"></span>
      <span>AI Engine Active · Stripe + Razorpay</span>
    </div>
  </nav>

  <header>
    <div>
      <div class="brand-eyebrow">Autonomous AI Revenue Recovery Engine</div>
      <h1>Ledger Operations Console</h1>
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
      <button class="sim-btn highlight" onclick="triggerSim('checkout_drop_off')">🛒 Checkout Drop-Off (Cart Win-Back)</button>
      <button class="sim-btn" onclick="triggerSim('high_ltv_insufficient_funds')">💎 High-LTV ($499 Payday Retry)</button>
      <button class="sim-btn" onclick="triggerSim('repeat_failure')">🔁 Repeat Offender (Date Switch)</button>
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


# ============================================================
# 6. CUSTOMER 360° DIRECTORY (HTML)
# ============================================================
@app.get("/customers")
@app.get("/customers/")
async def customers_page():
    """Serves the Customer 360° Directory and Account Intelligence page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Customer 360° Directory — AI Revenue Recovery</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#F5F3EC;--paper-2:#EFEBDF;--card:#FFFFFF;--ink:#1C2321;--ink-soft:#5B6360;
    --hair:#DAD5C6;--hair-strong:#C6C0AC;--emerald:#0B6E4F;--emerald-100:#DCEBE3;
    --amber:#9C6B1F;--amber-100:#F3E6CC;--brick:#8C2F2F;--brick-100:#F1DCDA;
    --ledger:#2B4C7E;--ledger-100:#DCE4EF;--mono:'IBM Plex Mono',monospace;
    --serif:'Fraunces',serif;--sans:'Inter',sans-serif;
  }
  *{box-sizing:border-box;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased;}
  .wrap{max-width:1240px;margin:0 auto;padding:28px 24px 60px;}

  /* Top Nav */
  .top-nav{
    display:flex;justify-content:space-between;align-items:center;
    background:var(--card);border:1px solid var(--hair-strong);border-radius:8px;
    padding:10px 18px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.03);
    flex-wrap:wrap;gap:12px;
  }
  .nav-brand{display:flex;align-items:center;gap:10px;}
  .brand-logo{font-size:22px;}
  .brand-title{font-family:var(--serif);font-weight:600;font-size:16px;color:var(--ink);}
  .brand-sub{font-family:var(--mono);font-size:10px;color:var(--ink-soft);letter-spacing:.06em;text-transform:uppercase;}
  .nav-links{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
  .nav-link{
    font-size:12px;font-weight:500;padding:6px 12px;border-radius:5px;
    text-decoration:none;color:var(--ink-soft);transition:all .15s ease;
    border:1px solid transparent;
  }
  .nav-link:hover{color:var(--ink);background:var(--paper-2);}
  .nav-link.active{color:var(--ink);background:var(--paper-2);border-color:var(--hair-strong);font-weight:600;}
  .nav-status{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--emerald);}
  .status-dot{width:8px;height:8px;border-radius:50%;background:var(--emerald);display:inline-block;animation:pulse 2s infinite;}
  @keyframes pulse{0%{opacity:1;}50%{opacity:.4;}100%{opacity:1;}}

  header{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1.5px solid var(--ink);padding-bottom:16px;margin-bottom:20px;gap:20px;flex-wrap:wrap;}
  .brand-eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:4px;}
  h1{font-family:var(--serif);font-weight:500;font-size:30px;margin:0;letter-spacing:-.01em;}

  .ledger-strip{
    display:grid;grid-template-columns:repeat(4,1fr);
    border:1px solid var(--hair-strong);border-radius:6px;overflow:hidden;
    background:var(--card);margin-bottom:24px;
  }
  @media (max-width:768px){.ledger-strip{grid-template-columns:1fr 1fr;}}
  .metric{padding:14px 16px;border-right:1px solid var(--hair);}
  .metric:last-child{border-right:none;}
  .metric-label{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft);margin-bottom:6px;}
  .metric-value{font-family:var(--serif);font-size:24px;font-weight:500;}
  .metric-value.emerald{color:var(--emerald);}
  .metric-sub{font-family:var(--mono);font-size:10.5px;color:var(--ink-soft);margin-top:2px;}

  /* Search & Filter Toolbar */
  .toolbar{
    background:var(--card);border:1px solid var(--hair-strong);border-radius:6px;
    padding:12px 16px;margin-bottom:20px;display:flex;justify-content:space-between;
    align-items:center;flex-wrap:wrap;gap:12px;
  }
  .search-box{display:flex;align-items:center;gap:8px;flex:1;max-width:340px;}
  .search-box input{
    width:100%;padding:8px 12px;font-family:var(--sans);font-size:12.5px;
    border:1px solid var(--hair-strong);border-radius:4px;background:var(--paper);
    color:var(--ink);outline:none;
  }
  .search-box input:focus{border-color:var(--ink);background:var(--card);}
  .filter-pills{display:flex;gap:6px;flex-wrap:wrap;}
  .pill{
    font-size:11.5px;padding:5px 10px;background:var(--paper-2);color:var(--ink-soft);
    border:1px solid var(--hair-strong);border-radius:4px;cursor:pointer;transition:all .15s ease;
  }
  .pill:hover{color:var(--ink);background:var(--paper);}
  .pill.active{background:var(--ink);color:var(--paper);border-color:var(--ink);font-weight:500;}

  .grid{display:grid;grid-template-columns:1.4fr 1fr;gap:20px;align-items:start;}
  @media (max-width:960px){.grid{grid-template-columns:1fr;}}

  .panel{background:var(--card);border:1px solid var(--hair-strong);border-radius:6px;overflow:hidden;}
  .panel-head{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid var(--hair);background:var(--card);}
  .panel-head h2{font-family:var(--serif);font-size:16px;font-weight:500;margin:0;}
  .panel-head .count{font-family:var(--mono);font-size:11px;color:var(--ink-soft);}

  .cust-table{width:100%;border-collapse:collapse;font-size:12.5px;}
  .cust-table th{background:var(--paper-2);padding:10px 14px;text-align:left;font-family:var(--mono);font-size:10.5px;text-transform:uppercase;color:var(--ink-soft);border-bottom:1px solid var(--hair-strong);}
  .cust-table td{padding:12px 14px;border-bottom:1px solid var(--hair);vertical-align:middle;}
  .cust-row{cursor:pointer;transition:background .15s ease;}
  .cust-row:hover{background:var(--paper-2);}
  .cust-row.selected{background:var(--ledger-100);}

  .badge{
    font-family:var(--mono);font-size:10px;font-weight:600;padding:2px 7px;border-radius:3px;
    display:inline-block;text-transform:uppercase;border:1px solid;
  }
  .badge.high_ltv{color:var(--emerald);background:var(--emerald-100);border-color:var(--emerald);}
  .badge.enterprise{color:var(--ledger);background:var(--ledger-100);border-color:var(--ledger);}
  .badge.standard{color:var(--ink);background:var(--paper-2);border-color:var(--hair-strong);}
  .badge.trial{color:var(--amber);background:var(--amber-100);border-color:var(--amber);}

  .drawer{padding:20px;}
  .drawer-empty{padding:40px 16px;text-align:center;color:var(--ink-soft);font-size:13px;}
  .drawer h3{font-family:var(--serif);font-size:20px;font-weight:500;margin:0 0 4px;}
  .drawer .sub{font-family:var(--mono);font-size:11px;color:var(--ink-soft);margin-bottom:16px;}
  .kv{display:grid;grid-template-columns:110px 1fr;gap:8px 12px;font-size:12.5px;margin-bottom:18px;}
  .kv div:nth-child(odd){color:var(--ink-soft);font-family:var(--mono);font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;padding-top:1px;}
  
  .action-box{background:var(--paper);border:1px solid var(--hair-strong);border-radius:6px;padding:14px;margin-top:16px;}
  .action-box h4{font-family:var(--serif);font-size:13.5px;margin:0 0 10px;}
  .btn-group{display:flex;gap:8px;flex-wrap:wrap;}
  button{
    font-family:var(--sans);font-size:11.5px;padding:7px 12px;border-radius:4px;
    border:1px solid var(--ink);background:var(--ink);color:var(--paper);cursor:pointer;
    font-weight:500;transition:all .15s ease;
  }
  button:hover{background:#333c39;}
  button.secondary{background:var(--card);color:var(--ink);border-color:var(--hair-strong);}
  button.secondary:hover{background:var(--paper-2);}
  button.accent{background:var(--emerald);color:white;border-color:var(--emerald);}
  button.accent:hover{background:#09583f;}

  .toast{position:fixed;bottom:20px;right:20px;background:var(--ink);color:white;padding:10px 16px;border-radius:4px;font-size:12px;font-family:var(--mono);display:none;z-index:999;}
</style>
</head>
<body>
<div class="wrap">

  <!-- Top Navigation Bar -->
  <nav class="top-nav">
    <div class="nav-brand">
      <span class="brand-logo">💰</span>
      <div>
        <div class="brand-title">Autonomous AI Revenue Recovery</div>
        <div class="brand-sub">Enterprise Dunning & Win-Back Agent</div>
      </div>
    </div>
    <div class="nav-links">
      <a href="/dashboard" class="nav-link">📊 Operations Hub</a>
      <a href="/customers" class="nav-link active">👥 Customer 360°</a>
      <a href="/analytics" class="nav-link">📈 Recovery Funnel</a>
      <a href="/docs" target="_blank" class="nav-link">⚡ API Docs ↗</a>
    </div>
    <div class="nav-status">
      <span class="status-dot"></span>
      <span>AI Engine Active · Stripe + Razorpay</span>
    </div>
  </nav>

  <header>
    <div>
      <div class="brand-eyebrow">Customer Intelligence & Retention</div>
      <h1>Customer 360° Directory</h1>
    </div>
    <div>
      <button class="secondary" onclick="loadCustomers()">🔄 Refresh Directory</button>
    </div>
  </header>

  <!-- Metric Strip -->
  <div class="ledger-strip">
    <div class="metric">
      <div class="metric-label">Managed Accounts</div>
      <div class="metric-value" id="mTotalCust">0</div>
      <div class="metric-sub">SaaS & E-Commerce Profiles</div>
    </div>
    <div class="metric">
      <div class="metric-label">Portfolio LTV</div>
      <div class="metric-value emerald" id="mTotalLTV">$0.00</div>
      <div class="metric-sub">Cumulative customer value</div>
    </div>
    <div class="metric">
      <div class="metric-label">In-Recovery Cases</div>
      <div class="metric-value" id="mInRecovery">0</div>
      <div class="metric-sub">Active dunning workflows</div>
    </div>
    <div class="metric">
      <div class="metric-label">Total Recovered</div>
      <div class="metric-value emerald" id="mRecoveredLTV">$0.00</div>
      <div class="metric-sub">Won-back revenue</div>
    </div>
  </div>

  <!-- Search & Segment Filters -->
  <div class="toolbar">
    <div class="search-box">
      <span>🔍</span>
      <input type="text" id="searchInput" placeholder="Search customer ID, name, company..." oninput="filterCustomers()">
    </div>
    <div class="filter-pills">
      <span class="pill active" onclick="setSegment('all', this)">All Accounts</span>
      <span class="pill" onclick="setSegment('high_ltv', this)">💎 High-LTV ($5K+)</span>
      <span class="pill" onclick="setSegment('enterprise', this)">🏢 Enterprise</span>
      <span class="pill" onclick="setSegment('standard', this)">⚡ Standard</span>
      <span class="pill" onclick="setSegment('trial', this)">⏳ Free Trial</span>
      <span class="pill" onclick="setSegment('in_recovery', this)">🚨 In Recovery</span>
    </div>
  </div>

  <!-- Grid View -->
  <div class="grid">
    <div class="panel">
      <div class="panel-head">
        <h2>Customer Accounts Directory</h2>
        <span class="count" id="tableCount">0 accounts</span>
      </div>
      <div style="max-height:600px;overflow-y:auto;">
        <table class="cust-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Segment</th>
              <th>LTV</th>
              <th>Plan</th>
              <th>Active Cases</th>
              <th>Recovered</th>
            </tr>
          </thead>
          <tbody id="custBody">
            <tr><td colspan="6" style="text-align:center;padding:30px;color:var(--ink-soft);">Loading customer directory...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Slide-Over Customer 360 Detail -->
    <div class="panel">
      <div class="panel-head">
        <h2>Customer 360° Profile & Actions</h2>
        <span class="count" id="drawerStatus">Select an account</span>
      </div>
      <div id="custDrawer">
        <div class="drawer-empty">Click any customer row on the left to inspect rich CRM context, cart items, past dunning history, and 1-click action triggers.</div>
      </div>
    </div>
  </div>

</div>

<div class="toast" id="toast"></div>

<script>
let allCustomers = [];
let filteredCustomers = [];
let selectedCustId = null;
let currentSegment = 'all';

function showToast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(()=>t.style.display='none', 3500);
}

function money(n){ return '$' + Number(n).toFixed(2); }

async function loadCustomers(){
  try {
    const res = await fetch('/api/customers');
    allCustomers = await res.json();
    
    // Stats calculation
    document.getElementById('mTotalCust').textContent = allCustomers.length;
    const totalLtv = allCustomers.reduce((acc, c) => acc + (c.ltv || 0), 0);
    document.getElementById('mTotalLTV').textContent = money(totalLtv);
    const inRec = allCustomers.filter(c => c.in_progress_count > 0).length;
    document.getElementById('mInRecovery').textContent = inRec;
    const recSum = allCustomers.reduce((acc, c) => acc + (c.recovered_amount || 0), 0);
    document.getElementById('mRecoveredLTV').textContent = money(recSum);

    filterCustomers();
  } catch(e) {
    console.error('Error loading customers:', e);
  }
}

function setSegment(seg, el){
  currentSegment = seg;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  filterCustomers();
}

function filterCustomers(){
  const query = (document.getElementById('searchInput').value || '').toLowerCase();
  
  filteredCustomers = allCustomers.filter(c => {
    const matchQuery = (c.customer_id || '').toLowerCase().includes(query) ||
                       (c.name || '').toLowerCase().includes(query) ||
                       (c.company || '').toLowerCase().includes(query) ||
                       (c.email || '').toLowerCase().includes(query);
                       
    if (!matchQuery) return false;

    if (currentSegment === 'all') return true;
    if (currentSegment === 'in_recovery') return c.in_progress_count > 0;
    return (c.segment || '').toLowerCase() === currentSegment;
  });

  renderTable();
}

function renderTable(){
  const tbody = document.getElementById('custBody');
  document.getElementById('tableCount').textContent = filteredCustomers.length + ' accounts';
  tbody.innerHTML = '';

  if (filteredCustomers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:30px;color:var(--ink-soft);">No matching customers found.</td></tr>';
    return;
  }

  filteredCustomers.forEach(c => {
    const tr = document.createElement('tr');
    tr.className = 'cust-row' + (c.customer_id === selectedCustId ? ' selected' : '');
    tr.onclick = () => selectCustomer(c.customer_id);

    const segClass = (c.segment || 'standard').toLowerCase();
    tr.innerHTML = `
      <td>
        <div style="font-weight:600;">${c.name}</div>
        <div style="font-family:var(--mono);font-size:11px;color:var(--ink-soft);">${c.customer_id} · ${c.company}</div>
      </td>
      <td><span class="badge ${segClass}">${c.segment || 'standard'}</span></td>
      <td style="font-family:var(--mono);font-weight:500;">${money(c.ltv)}</td>
      <td style="font-family:var(--mono);font-size:11.5px;">${c.plan || 'monthly'}</td>
      <td style="font-family:var(--mono);text-align:center;">
        ${c.in_progress_count > 0 ? `<span style="color:var(--amber);font-weight:bold;">${c.in_progress_count} active</span>` : `<span style="color:var(--ink-soft);">0</span>`}
      </td>
      <td style="font-family:var(--mono);color:var(--emerald);font-weight:500;">${money(c.recovered_amount || 0)}</td>
    `;
    tbody.appendChild(tr);
  });

  if (!selectedCustId && filteredCustomers.length > 0) {
    selectCustomer(filteredCustomers[0].customer_id);
  } else if (selectedCustId) {
    const exist = allCustomers.find(x => x.customer_id === selectedCustId);
    if (exist) renderDrawer(exist);
  }
}

function selectCustomer(id){
  selectedCustId = id;
  document.querySelectorAll('.cust-row').forEach(r => r.classList.remove('selected'));
  const c = allCustomers.find(x => x.customer_id === id);
  if (c) {
    renderDrawer(c);
  }
}

function renderDrawer(c){
  const drawer = document.getElementById('custDrawer');
  const segClass = (c.segment || 'standard').toLowerCase();
  
  let cartHtml = '';
  if (c.cart_items && c.cart_items.length > 0) {
    cartHtml = `
      <div style="background:var(--amber-100);border:1px solid var(--amber);border-radius:6px;padding:10px 12px;margin-bottom:14px;">
        <div style="font-weight:600;font-size:12px;color:var(--amber);">🛒 Abandoned Cart Detected (${money(c.cart_value || 0)})</div>
        <div style="font-size:11.5px;color:var(--ink);margin-top:4px;">${c.cart_items.join(', ')}</div>
      </div>
    `;
  }

  drawer.innerHTML = `
    <div class="drawer">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
        <div>
          <h3>${c.name}</h3>
          <div class="sub">${c.customer_id} · ${c.company}</div>
        </div>
        <span class="badge ${segClass}">${c.segment}</span>
      </div>

      ${cartHtml}

      <div class="kv">
        <div>Email</div><div>${c.email || 'N/A'}</div>
        <div>Phone</div><div>${c.phone || 'N/A'}</div>
        <div>Lifetime Value</div><div><strong>${money(c.ltv)}</strong></div>
        <div>Subscription</div><div>${c.plan}</div>
        <div>Country</div><div>${c.country}</div>
        <div>Active Dunning</div><div>${c.in_progress_count > 0 ? `<span style="color:var(--brick);font-weight:bold;">${c.in_progress_count} Cases In Progress</span>` : 'None (Clean)'}</div>
        <div>Total Won Back</div><div><span style="color:var(--emerald);font-weight:bold;">${money(c.recovered_amount || 0)}</span></div>
      </div>

      <div class="action-box">
        <h4>⚡ 1-Click Customer Interventions</h4>
        <div class="btn-group">
          <button class="accent" onclick="triggerAction('upi_link', '${c.customer_id}')">💳 Send Razorpay UPI Link</button>
          <button class="secondary" onclick="triggerAction('cart_recovery', '${c.customer_id}')">🛒 Trigger Cart Recovery Link</button>
          <button class="secondary" onclick="triggerAction('pause_dunning', '${c.customer_id}')">⏸️ Pause Dunning (24h Grace)</button>
        </div>
      </div>
    </div>
  `;
}

async function triggerAction(type, custId){
  if (type === 'cart_recovery') {
    showToast(`Dispatched 1-Click Cart Recovery with 10% discount for ${custId}!`);
    await fetch('/admin/simulate?scenario=checkout_drop_off', {method: 'POST'});
  } else if (type === 'upi_link') {
    showToast(`Generated secure Razorpay UPI Payment Link for ${custId}`);
  } else if (type === 'pause_dunning') {
    showToast(`Dunning paused for ${custId}. Granted 24h grace period.`);
  }
}

loadCustomers();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)


# ============================================================
# 7. RECOVERY FUNNEL & ANALYTICS (HTML)
# ============================================================
@app.get("/analytics")
@app.get("/analytics/")
async def analytics_page():
    """Serves the Recovery Funnel and Gateway Intelligence Analytics page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Recovery Funnel & Gateway Analytics — AI Revenue Recovery</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#F5F3EC;--paper-2:#EFEBDF;--card:#FFFFFF;--ink:#1C2321;--ink-soft:#5B6360;
    --hair:#DAD5C6;--hair-strong:#C6C0AC;--emerald:#0B6E4F;--emerald-100:#DCEBE3;
    --amber:#9C6B1F;--amber-100:#F3E6CC;--brick:#8C2F2F;--brick-100:#F1DCDA;
    --ledger:#2B4C7E;--ledger-100:#DCE4EF;--mono:'IBM Plex Mono',monospace;
    --serif:'Fraunces',serif;--sans:'Inter',sans-serif;
  }
  *{box-sizing:border-box;}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);-webkit-font-smoothing:antialiased;}
  .wrap{max-width:1240px;margin:0 auto;padding:28px 24px 60px;}

  /* Top Nav */
  .top-nav{
    display:flex;justify-content:space-between;align-items:center;
    background:var(--card);border:1px solid var(--hair-strong);border-radius:8px;
    padding:10px 18px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,0.03);
    flex-wrap:wrap;gap:12px;
  }
  .nav-brand{display:flex;align-items:center;gap:10px;}
  .brand-logo{font-size:22px;}
  .brand-title{font-family:var(--serif);font-weight:600;font-size:16px;color:var(--ink);}
  .brand-sub{font-family:var(--mono);font-size:10px;color:var(--ink-soft);letter-spacing:.06em;text-transform:uppercase;}
  .nav-links{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
  .nav-link{
    font-size:12px;font-weight:500;padding:6px 12px;border-radius:5px;
    text-decoration:none;color:var(--ink-soft);transition:all .15s ease;
    border:1px solid transparent;
  }
  .nav-link:hover{color:var(--ink);background:var(--paper-2);}
  .nav-link.active{color:var(--ink);background:var(--paper-2);border-color:var(--hair-strong);font-weight:600;}
  .nav-status{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:var(--emerald);}
  .status-dot{width:8px;height:8px;border-radius:50%;background:var(--emerald);display:inline-block;animation:pulse 2s infinite;}
  @keyframes pulse{0%{opacity:1;}50%{opacity:.4;}100%{opacity:1;}}

  header{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1.5px solid var(--ink);padding-bottom:16px;margin-bottom:20px;gap:20px;flex-wrap:wrap;}
  .brand-eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:4px;}
  h1{font-family:var(--serif);font-weight:500;font-size:30px;margin:0;letter-spacing:-.01em;}

  .ledger-strip{
    display:grid;grid-template-columns:repeat(4,1fr);
    border:1px solid var(--hair-strong);border-radius:6px;overflow:hidden;
    background:var(--card);margin-bottom:24px;
  }
  @media (max-width:768px){.ledger-strip{grid-template-columns:1fr 1fr;}}
  .metric{padding:14px 16px;border-right:1px solid var(--hair);}
  .metric:last-child{border-right:none;}
  .metric-label{font-family:var(--mono);font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-soft);margin-bottom:6px;}
  .metric-value{font-family:var(--serif);font-size:24px;font-weight:500;}
  .metric-value.emerald{color:var(--emerald);}
  .metric-sub{font-family:var(--mono);font-size:10.5px;color:var(--ink-soft);margin-top:2px;}

  .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;}
  @media (max-width:860px){.grid-2{grid-template-columns:1fr;}}

  .panel{background:var(--card);border:1px solid var(--hair-strong);border-radius:6px;overflow:hidden;padding:18px;}
  .panel h2{font-family:var(--serif);font-size:18px;font-weight:500;margin:0 0 4px;}
  .panel .sub{font-family:var(--mono);font-size:11px;color:var(--ink-soft);margin-bottom:16px;}

  /* Funnel Visualizer */
  .funnel-step{margin-bottom:14px;}
  .funnel-meta{display:flex;justify-content:space-between;font-size:12.5px;font-weight:500;margin-bottom:6px;}
  .bar-bg{height:24px;background:var(--paper-2);border-radius:4px;overflow:hidden;position:relative;}
  .bar-fill{height:100%;background:var(--emerald);border-radius:4px;transition:width .6s ease;display:flex;align-items:center;padding-left:10px;color:white;font-family:var(--mono);font-size:11px;font-weight:600;}
  .bar-fill.ledger{background:var(--ledger);}
  .bar-fill.amber{background:var(--amber);}

  .stat-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--hair);font-size:13px;}
  .stat-row:last-child{border-bottom:none;}
  .stat-label{color:var(--ink-soft);}
  .stat-val{font-family:var(--mono);font-weight:600;}

  button{
    font-family:var(--sans);font-size:12px;padding:8px 12px;border-radius:4px;
    border:1px solid var(--ink);background:var(--ink);color:var(--paper);cursor:pointer;
    font-weight:500;transition:all .15s ease;
  }
  button.secondary{background:var(--card);color:var(--ink);border-color:var(--hair-strong);}
  button.secondary:hover{background:var(--paper-2);}
</style>
</head>
<body>
<div class="wrap">

  <!-- Top Navigation Bar -->
  <nav class="top-nav">
    <div class="nav-brand">
      <span class="brand-logo">💰</span>
      <div>
        <div class="brand-title">Autonomous AI Revenue Recovery</div>
        <div class="brand-sub">Enterprise Dunning & Win-Back Agent</div>
      </div>
    </div>
    <div class="nav-links">
      <a href="/dashboard" class="nav-link">📊 Operations Hub</a>
      <a href="/customers" class="nav-link">👥 Customer 360°</a>
      <a href="/analytics" class="nav-link active">📈 Recovery Funnel</a>
      <a href="/docs" target="_blank" class="nav-link">⚡ API Docs ↗</a>
    </div>
    <div class="nav-status">
      <span class="status-dot"></span>
      <span>AI Engine Active · Stripe + Razorpay</span>
    </div>
  </nav>

  <header>
    <div>
      <div class="brand-eyebrow">Financial Telemetry & Performance</div>
      <h1>Recovery Funnel & Intelligence</h1>
    </div>
    <div>
      <button class="secondary" onclick="loadAnalytics()">🔄 Refresh Telemetry</button>
    </div>
  </header>

  <!-- Metric Strip -->
  <div class="ledger-strip">
    <div class="metric">
      <div class="metric-label">Total Revenue At Risk</div>
      <div class="metric-value" id="fAtRisk">$0.00</div>
      <div class="metric-sub">Across all payment failures</div>
    </div>
    <div class="metric">
      <div class="metric-label">Total Won Back</div>
      <div class="metric-value emerald" id="fRecovered">$0.00</div>
      <div class="metric-sub">Closed-loop recoveries</div>
    </div>
    <div class="metric">
      <div class="metric-label">Overall Win-Back Rate</div>
      <div class="metric-value emerald" id="fRecoveryRate">0%</div>
      <div class="metric-sub">Intervention conversion</div>
    </div>
    <div class="metric">
      <div class="metric-label">Dispatched Touches</div>
      <div class="metric-value" id="fTouches">0</div>
      <div class="metric-sub">Email, SMS, Slack, Links</div>
    </div>
  </div>

  <div class="grid-2">
    <!-- Visual Recovery Funnel Waterfall -->
    <div class="panel">
      <h2>Autonomous Recovery Funnel</h2>
      <div class="sub">Conversion flow from degradation detection to verified recovery</div>

      <div class="funnel-step">
        <div class="funnel-meta"><span>1. Payment Degradations & Drop-Offs</span><span id="fn1">0 Cases (100%)</span></div>
        <div class="bar-bg"><div class="bar-fill ledger" id="b1" style="width:100%;">100% Detected</div></div>
      </div>

      <div class="funnel-step">
        <div class="funnel-meta"><span>2. Context & Gemini AI Diagnostics</span><span id="fn2">0 Cases (100%)</span></div>
        <div class="bar-bg"><div class="bar-fill ledger" id="b2" style="width:100%;">100% Diagnosed</div></div>
      </div>

      <div class="funnel-step">
        <div class="funnel-meta"><span>3. Bounded Outreach Dispatched</span><span id="fn3">0 Touches</span></div>
        <div class="bar-bg"><div class="bar-fill amber" id="b3" style="width:85%;">Outreach Active</div></div>
      </div>

      <div class="funnel-step">
        <div class="funnel-meta"><span>4. Verified Revenue Recovered</span><span id="fn4">0 Recovered</span></div>
        <div class="bar-bg"><div class="bar-fill" id="b4" style="width:75%;">Auto-Resolved</div></div>
      </div>
    </div>

    <!-- Multi-Channel ROI & Gateway Matrix -->
    <div class="panel">
      <h2>Multi-Channel & Gateway ROI</h2>
      <div class="sub">Dispatches and integrations performance</div>

      <div class="stat-row">
        <span class="stat-label">SendGrid Recovery Emails</span>
        <span class="stat-val" id="chEmail">0 sent</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Twilio SMS Recovery Alerts</span>
        <span class="stat-val" id="chSMS">0 sent</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Slack Human Operations Handoffs</span>
        <span class="stat-val" id="chSlack">0 alerts</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Razorpay Links (UPI / NetBanking)</span>
        <span class="stat-val" id="chRzp">0 generated</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Stripe Payment Intents</span>
        <span class="stat-val" id="chStripe">0 generated</span>
      </div>
    </div>
  </div>

  <!-- Decline Reason Breakdown -->
  <div class="panel">
    <h2>Root Cause Decline Breakdown</h2>
    <div class="sub">Diagnostic classification across all ingested payment events</div>
    
    <div class="stat-row">
      <span class="stat-label">🛒 Checkout Drop-Offs & Abandoned Carts</span>
      <span class="stat-val" id="rcDropOff">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">💳 Insufficient Balance (Payday Retries)</span>
      <span class="stat-val" id="rcFunds">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">⏰ Expired Cards (Update Links)</span>
      <span class="stat-val" id="rcExpired">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">🚨 Suspected Fraud / Risk Flags</span>
      <span class="stat-val" id="rcFraud">0</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">⚡ Other Gateway Declines / Edge Cases</span>
      <span class="stat-val" id="rcOther">0</span>
    </div>
  </div>

</div>

<script>
function money(n){ return '$' + Number(n).toFixed(2); }

async function loadAnalytics(){
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    const f = data.funnel || {};
    
    document.getElementById('fAtRisk').textContent = money(f.at_risk_amount || 0);
    document.getElementById('fRecovered').textContent = money(f.recovered_amount || 0);
    document.getElementById('fRecoveryRate').textContent = (f.recovery_rate_pct || 0) + '%';
    document.getElementById('fTouches').textContent = f.outreach_dispatched || 0;

    document.getElementById('fn1').textContent = `${f.detected || 0} Cases (100%)`;
    document.getElementById('fn2').textContent = `${f.diagnosed || 0} Diagnosed (100%)`;
    document.getElementById('fn3').textContent = `${f.outreach_dispatched || 0} Outreaches Sent`;
    document.getElementById('fn4').textContent = `${f.recovered_cases || 0} Cases Recovered (${f.recovery_rate_pct || 0}%)`;

    const rate = Math.min(100, Math.max(10, f.recovery_rate_pct || 50));
    document.getElementById('b4').style.width = rate + '%';

    // Channels
    const ch = data.channels || {};
    document.getElementById('chEmail').textContent = `${ch.email || 0} sent`;
    document.getElementById('chSMS').textContent = `${ch.sms || 0} sent`;
    document.getElementById('chSlack').textContent = `${ch.slack || 0} alerts`;
    document.getElementById('chRzp').textContent = `${ch.razorpay || 0} links`;
    document.getElementById('chStripe').textContent = `${ch.stripe || 0} intents`;

    // Failure codes
    const fc = data.failure_codes || {};
    document.getElementById('rcDropOff').textContent = fc.checkout_drop_off || 0;
    document.getElementById('rcFunds').textContent = fc.insufficient_funds || 0;
    document.getElementById('rcExpired').textContent = fc.card_expired || 0;
    document.getElementById('rcFraud').textContent = fc.suspected_fraud || 0;
    document.getElementById('rcOther').textContent = fc.other || 0;

  } catch(e) {
    console.error('Error loading analytics:', e);
  }
}

loadAnalytics();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html_content, status_code=200)
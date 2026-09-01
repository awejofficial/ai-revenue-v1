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
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

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
    
    # Auto-seed database if customer directory is empty
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            cust_count = await conn.fetchval("SELECT COUNT(*) FROM customers")
            if not cust_count or cust_count == 0:
                print("[Lifespan] No customers detected in database. Auto-seeding initial profiles & demo cases...")
                from app.seed_data import seed
                await seed()
    except Exception as e:
        print(f"[Lifespan] Auto-seed check notice: {e}")

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

# Enable CORS for external frontends (e.g., Vercel, custom domains, and local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve compiled authentic shadcn/ui frontend static assets if available
dist_assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "assets"))
if os.path.exists(dist_assets_dir):
    app.mount("/assets", StaticFiles(directory=dist_assets_dir), name="assets")


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


@app.post("/admin/seed")
@app.get("/api/seed")
async def seed_database():
    """Seeds the customer directory and sample demo cases if empty or manually requested."""
    try:
        from app.seed_data import seed
        await seed()
        return {"status": "success", "message": "Customer directory and demo cases seeded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customers")
@app.get("/api/customers/")
async def api_customers():
    """Returns all customers with aggregated CRM and case telemetry."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        customers_raw = await conn.fetch("SELECT * FROM customers ORDER BY customer_id ASC")
        if not customers_raw:
            try:
                from app.seed_data import seed
                await seed()
                customers_raw = await conn.fetch("SELECT * FROM customers ORDER BY customer_id ASC")
            except Exception as e:
                print(f"[api_customers] Auto-seed notice: {e}")
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
                
        # Failure code breakdown across all raw events
        raw_events = await conn.fetch("SELECT canonical_event FROM raw_events")
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
    """Serves the live interactive revenue recovery dashboard using shadcn/ui design tokens."""
    dist_index = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html"))
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Revenue Recovery Agent — Operations Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --background: #FFFFFF;
    --foreground: #000000;
    --card: #FFFFFF;
    --card-foreground: #000000;
    --popover: #FFFFFF;
    --popover-foreground: #000000;
    --primary: #0000EE;
    --primary-foreground: #FFFFFF;
    --secondary: #F1F5FA;
    --secondary-foreground: #000000;
    --muted: #F1F5FA;
    --muted-foreground: #768EA7;
    --accent: #F1F5FA;
    --accent-foreground: #0000EE;
    --destructive: #D52B1E;
    --destructive-foreground: #FFFFFF;
    --success: #006C3F;
    --success-foreground: #FFFFFF;
    --success-muted: #E6F4EA;
    --border: #D0E0FF;
    --input: #D0E0FF;
    --ring: #0000EE;
    --dark-surface: #192839;
    --dark-foreground: #FFFFFF;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius: 8px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--background);
    color: var(--foreground);
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    min-height: 100vh;
  }

  /* shadcn Dark Surface Header */
  .shadcn-header {
    background: var(--dark-surface);
    color: var(--dark-foreground);
    border-bottom: 1px solid #283C50;
    position: sticky;
    top: 0;
    z-index: 50;
  }
  .header-container {
    max-width: 1320px;
    margin: 0 auto;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  .brand-lockup {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-badge {
    background: var(--primary);
    color: var(--primary-foreground);
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
    box-shadow: 0 2px 4px rgba(0,0,238,0.25);
  }
  .brand-text h1 {
    font-size: 15px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
  }
  .brand-text p {
    font-size: 11px;
    color: var(--muted-foreground);
    font-family: var(--font-mono);
  }

  /* Navigation Tabs in Header */
  .nav-tabs-list {
    display: flex;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
  }
  .nav-tab-trigger {
    color: #A0B2C6;
    text-decoration: none;
    font-size: 12.5px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 6px;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .nav-tab-trigger:hover {
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.05);
  }
  .nav-tab-trigger.active {
    color: var(--primary-foreground);
    background: var(--primary);
    font-weight: 600;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2);
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 108, 63, 0.15);
    border: 1px solid rgba(0, 108, 63, 0.35);
    color: #10B981;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 500;
    padding: 5px 10px;
    border-radius: 9999px;
  }
  .status-pulse {
    width: 6px;
    height: 6px;
    background: #10B981;
    border-radius: 50%;
    animation: pulse-ring 2s infinite;
  }
  @keyframes pulse-ring {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.3); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.8; }
  }

  /* Main Layout */
  .main-wrapper {
    max-width: 1320px;
    margin: 0 auto;
    padding: 24px;
  }

  /* Page Header Title */
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
    gap: 16px;
    flex-wrap: wrap;
  }
  .page-header-title h2 {
    font-size: 24px;
    font-weight: 700;
    color: var(--foreground);
    letter-spacing: -0.02em;
  }
  .page-header-title p {
    font-size: 13px;
    color: var(--muted-foreground);
    margin-top: 2px;
  }
  .page-header-actions {
    display: flex;
    gap: 8px;
  }

  /* shadcn Buttons */
  .btn {
    font-family: var(--font-sans);
    font-size: 12.5px;
    font-weight: 500;
    padding: 8px 14px;
    border-radius: var(--radius);
    border: 1px solid transparent;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: all 0.15s ease;
    text-decoration: none;
  }
  .btn-default {
    background: var(--primary);
    color: var(--primary-foreground);
    box-shadow: 0 1px 2px rgba(0, 0, 238, 0.2);
  }
  .btn-default:hover {
    background: #0000C8;
  }
  .btn-secondary {
    background: var(--secondary);
    color: var(--foreground);
    border-color: var(--border);
  }
  .btn-secondary:hover {
    background: #E4ECF6;
  }
  .btn-outline {
    background: #FFFFFF;
    color: var(--foreground);
    border-color: var(--border);
  }
  .btn-outline:hover {
    background: var(--muted);
  }
  .btn-destructive {
    background: var(--destructive);
    color: var(--destructive-foreground);
  }
  .btn-destructive:hover {
    background: #B52317;
  }
  .btn-success {
    background: var(--success);
    color: var(--success-foreground);
  }
  .btn-success:hover {
    background: #005431;
  }
  .btn-sm {
    font-size: 11.5px;
    padding: 5px 10px;
    border-radius: 6px;
  }

  /* shadcn Cards */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
  }
  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .card-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--foreground);
  }
  .card-description {
    font-size: 12px;
    color: var(--muted-foreground);
  }
  .card-content {
    padding: 20px;
  }

  /* Simulation Toolbar Card */
  .simulator-card {
    background: var(--muted);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px 18px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }
  .simulator-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--foreground);
    font-family: var(--font-mono);
  }
  .simulator-actions {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
  }

  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }
  @media (max-width: 1024px) {
    .kpi-grid { grid-template-columns: repeat(3, 1fr); }
  }
  @media (max-width: 640px) {
    .kpi-grid { grid-template-columns: 1fr; }
  }
  .kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03);
    position: relative;
    overflow: hidden;
  }
  .kpi-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-family: var(--font-mono);
    margin-bottom: 6px;
  }
  .kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: var(--foreground);
    letter-spacing: -0.02em;
  }
  .kpi-value.primary { color: var(--primary); }
  .kpi-value.success { color: var(--success); }
  .kpi-value.destructive { color: var(--destructive); }
  .kpi-subtitle {
    font-size: 11.5px;
    color: var(--muted-foreground);
    margin-top: 4px;
  }

  /* Two Column Grid */
  .split-grid {
    display: grid;
    grid-template-columns: 1.35fr 1fr;
    gap: 20px;
    align-items: start;
  }
  @media (max-width: 960px) {
    .split-grid { grid-template-columns: 1fr; }
  }

  /* Cases Feed */
  .cases-scroll {
    max-height: 620px;
    overflow-y: auto;
  }
  .case-item {
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 14px;
    align-items: center;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .case-item:hover {
    background: #F8FAFD;
  }
  .case-item.active {
    background: var(--secondary);
    border-left: 4px solid var(--primary);
  }
  .case-id-badge {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    color: var(--muted-foreground);
    background: var(--muted);
    border: 1px solid var(--border);
    padding: 3px 6px;
    border-radius: 4px;
  }
  .case-cust-title {
    font-size: 13.5px;
    font-weight: 600;
    color: var(--foreground);
  }
  .case-meta-line {
    font-size: 12px;
    color: var(--muted-foreground);
    margin-top: 3px;
    line-height: 1.4;
  }

  /* shadcn Badges */
  .badge {
    display: inline-flex;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    padding: 2.5px 8px;
    border-radius: 9999px;
    border: 1px solid transparent;
  }
  .badge-success {
    background: var(--success-muted);
    color: var(--success);
    border-color: #A8D5BA;
  }
  .badge-destructive {
    background: #FDEBEB;
    color: var(--destructive);
    border-color: #F5C2C2;
  }
  .badge-warning {
    background: #FEF7E0;
    color: #B06000;
    border-color: #FCE293;
  }
  .badge-default {
    background: var(--secondary);
    color: var(--primary);
    border-color: var(--border);
  }

  /* Drawer Details */
  .drawer-content {
    padding: 20px;
  }
  .drawer-empty {
    padding: 60px 20px;
    text-align: center;
    color: var(--muted-foreground);
    font-size: 13px;
  }
  .kv-table {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 8px 12px;
    font-size: 12.5px;
    margin: 16px 0 20px;
    padding: 14px;
    background: var(--muted);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  .kv-key {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .kv-val {
    font-weight: 500;
    color: var(--foreground);
    word-break: break-word;
  }

  /* Timeline */
  .tl-container {
    border-left: 2px solid var(--border);
    margin-left: 8px;
    padding-left: 16px;
  }
  .tl-node {
    position: relative;
    padding-bottom: 16px;
  }
  .tl-node:last-child {
    padding-bottom: 0;
  }
  .tl-node::before {
    content: '';
    position: absolute;
    left: -21px;
    top: 3px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--primary);
    border: 2px solid var(--card);
  }
  .tl-node.win::before { background: var(--success); }
  .tl-node.alert::before { background: var(--destructive); }
  .tl-time {
    font-family: var(--font-mono);
    font-size: 10.5px;
    color: var(--muted-foreground);
  }
  .tl-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--foreground);
    margin: 2px 0;
  }
  .tl-desc {
    font-size: 12px;
    color: var(--muted-foreground);
    line-height: 1.4;
  }

  /* Toast notification */
  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--dark-surface);
    color: var(--dark-foreground);
    border: 1px solid #344B62;
    padding: 10px 18px;
    border-radius: var(--radius);
    font-size: 12.5px;
    font-family: var(--font-mono);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    display: none;
    z-index: 100;
  }
</style>
</head>
<body>

  <!-- Top Dark Surface Header -->
  <header class="shadcn-header">
    <div class="header-container">
      <div class="brand-lockup">
        <div class="brand-badge">⚡</div>
        <div class="brand-text">
          <h1>Autonomous Revenue Recovery</h1>
          <p>Intelligent Dunning & Win-Back Agent</p>
        </div>
      </div>

      <nav class="nav-tabs-list">
        <a href="/dashboard" class="nav-tab-trigger active">📊 Operations Hub</a>
        <a href="/customers" class="nav-tab-trigger">👥 Customer 360°</a>
        <a href="/analytics" class="nav-tab-trigger">📈 Recovery Funnel</a>
        <a href="/docs" target="_blank" class="nav-tab-trigger">⚡ OpenAPI Docs ↗</a>
      </nav>

      <div class="header-actions">
        <div class="status-pill">
          <span class="status-pulse"></span>
          <span>Engine Active · Stripe + Razorpay</span>
        </div>
      </div>
    </div>
  </header>

  <main class="main-wrapper">
    
    <!-- Page Title & Background Controls -->
    <div class="page-header">
      <div class="page-header-title">
        <h2>Operations Console & Telemetry</h2>
        <p>Real-time autonomous revenue recovery stream and dunning lifecycle supervisor.</p>
      </div>
      <div class="page-header-actions">
        <button class="btn btn-outline" id="refreshBtn">🔄 Refresh Data</button>
        <button class="btn btn-default" id="processBtn">⚡ Run Background Worker</button>
      </div>
    </div>

    <!-- 1-Click Interactive Scenario Simulator -->
    <div class="simulator-card">
      <div class="simulator-label">
        <span>🕹️</span>
        <span>1-Click Test Harness:</span>
      </div>
      <div class="simulator-actions">
        <button class="btn btn-default btn-sm" onclick="triggerSim('checkout_drop_off')">🛒 Cart Drop-Off</button>
        <button class="btn btn-outline btn-sm" onclick="triggerSim('high_ltv_insufficient_funds')">💎 High-LTV Payday Retry</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerSim('repeat_failure')">🔁 Repeat Offender</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerSim('expired_card')">💳 Expired Card</button>
        <button class="btn btn-destructive btn-sm" onclick="triggerSim('fraud')">🚨 Suspected Fraud</button>
        <button class="btn btn-secondary btn-sm" onclick="triggerSim('trial_user')">⏳ Free Trial</button>
        <button class="btn btn-success btn-sm" onclick="triggerSim('payment_succeeded')">✅ Payment Success (Auto-Resolve)</button>
      </div>
    </div>

    <!-- KPI Metric Cards Strip -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Revenue At Risk</div>
        <div class="kpi-value destructive" id="mAtRisk">$0.00</div>
        <div class="kpi-subtitle" id="mCases">0 total cases</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Won Back (Recovered)</div>
        <div class="kpi-value success" id="mRecovered">$0.00</div>
        <div class="kpi-subtitle" id="mRecoveredPct">0% conversion</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">In Progress</div>
        <div class="kpi-value primary" id="mInProgress">0</div>
        <div class="kpi-subtitle">Active outreach & timers</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Escalated to Ops</div>
        <div class="kpi-value" id="mEscalated">0</div>
        <div class="kpi-subtitle">Slack handoffs dispatched</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Recovery Rate</div>
        <div class="kpi-value success" id="mRecoveryRate">0%</div>
        <div class="kpi-subtitle">Intervention efficiency</div>
      </div>
    </div>

    <!-- Split Grid: Case Feed & Detail Inspector -->
    <div class="split-grid">
      
      <!-- Cases Feed Card -->
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">Live Case Ledger</h3>
            <p class="card-description">Autonomous state transitions and diagnostic assessments</p>
          </div>
          <span class="badge badge-default" id="feedCount">0 cases</span>
        </div>
        <div class="cases-scroll" id="feed">
          <div style="padding: 40px; text-align: center; color: var(--muted-foreground);">Loading cases...</div>
        </div>
      </div>

      <!-- Case Detail & Audit Timeline -->
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">Autonomous Audit Trail</h3>
            <p class="card-description">Verified execution log and customer telemetry</p>
          </div>
          <span class="badge badge-default" id="auditStatus">Select case</span>
        </div>
        <div id="drawer">
          <div class="drawer-empty">Click any case from the feed on the left to inspect customer context, AI reasoning, and multi-channel audit logs.</div>
        </div>
      </div>

    </div>

  </main>

  <!-- Toast notification -->
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

function statusToBadge(status){
  const map = {
    'resolved': 'badge-success',
    'escalated': 'badge-destructive',
    'retrying': 'badge-warning',
    'awaiting_input': 'badge-default',
    'diagnosing': 'badge-default',
    'new': 'badge-default'
  };
  return map[status] || 'badge-default';
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
      feedEl.innerHTML = '<div style="padding:40px;text-align:center;color:var(--muted-foreground);">No cases found. Click a scenario button above to trigger an event!</div>';
      return;
    }

    cases.forEach(c => {
      const badgeCls = statusToBadge(c.status);
      const label = statusLabel(c.status);
      const item = document.createElement('div');
      item.className = 'case-item' + (c.case_id === selectedId ? ' active' : '');
      item.dataset.id = c.case_id;
      item.innerHTML = `
        <div class="case-id-badge">#${c.case_id}</div>
        <div>
          <div class="case-cust-title">${c.customer_id} <span style="font-size:11.5px;color:var(--muted-foreground);font-weight:normal;">· ${c.case_type}</span></div>
          <div class="case-meta-line">${c.llm_reasoning || c.last_action || 'Evaluating autonomous bounds...'}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-family:var(--font-mono);font-size:13.5px;font-weight:700;">${money(c.amount_usd)}</div>
          <div style="margin-top:4px;"><span class="badge ${badgeCls}">${label}</span></div>
        </div>`;
      item.addEventListener('click', ()=>selectCase(c.case_id));
      feedEl.appendChild(item);
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
  document.querySelectorAll('.case-item').forEach(r => r.classList.toggle('active', parseInt(r.dataset.id) === id));
  const c = allCases.find(x => x.case_id === id);
  if (c) renderDrawer(c);
}

function renderDrawer(c){
  const badgeCls = statusToBadge(c.status);
  const label = statusLabel(c.status);
  
  const items = [
    { time: fmtDate(c.created_at), label: 'Payment Degradation Detected', detail: `Failure event ingested into raw_events. Amount at risk: ${money(c.amount_usd)}.`, cls: '' },
    { time: fmtDate(c.updated_at), label: 'Diagnosis & Policy Check', detail: c.llm_reasoning || 'Deterministic rule matched with customer context.', cls: '' },
    { time: fmtDate(c.updated_at), label: 'Autonomous Outreach Dispatched', detail: c.last_action || 'Touchpoints sent.', cls: '' }
  ];

  if (c.status === 'resolved') {
    items.push({ time: fmtDate(c.updated_at), label: '✅ Inbound Revenue Recovered', detail: `Inbound payment verified. ${money(c.amount_usd)} recovered. Case closed.`, cls: 'win' });
  } else if (c.status === 'escalated') {
    items.push({ time: fmtDate(c.updated_at), label: '🚨 Dispatched to Human Operations', detail: `Case escalated to Slack for operations review.`, cls: 'alert' });
  }

  let tlHtml = items.map(t => `
    <div class="tl-node ${t.cls}">
      <div class="tl-time">${t.time}</div>
      <div class="tl-title">${t.label}</div>
      <div class="tl-desc">${t.detail}</div>
    </div>`).join('');

  drawerEl.innerHTML = `
    <div class="drawer-content">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
        <div>
          <h3 style="font-size:18px;font-weight:700;color:var(--foreground);">${c.customer_id}</h3>
          <div style="font-size:12px;color:var(--muted-foreground);font-family:var(--font-mono);margin-top:2px;">Case #${c.case_id} · ${c.case_type} · ${money(c.amount_usd)}</div>
        </div>
        ${c.status !== 'resolved' ? `<button class="btn btn-success btn-sm" onclick="resolveManually(${c.case_id})">✅ Mark Resolved</button>` : ''}
      </div>

      <div class="kv-table">
        <div class="kv-key">Status</div><div class="kv-val"><span class="badge ${badgeCls}">${label}</span></div>
        <div class="kv-key">Retries</div><div class="kv-val">${c.current_retry_count || 0} / ${c.max_retries || 3}</div>
        <div class="kv-key">Next Action</div><div class="kv-val">${fmtDate(c.scheduled_next_action_at)}</div>
        <div class="kv-key">AI Reasoning</div><div class="kv-val">${c.llm_reasoning || 'Deterministic rule'}</div>
        <div class="kv-key">Last Action</div><div class="kv-val">${c.last_action || 'None'}</div>
      </div>

      <h4 style="font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:0.04em;color:var(--muted-foreground);font-family:var(--font-mono);margin-bottom:12px;">Lifecycle Timeline</h4>
      <div class="tl-container">${tlHtml}</div>
    </div>`;
}

async function triggerSim(scenario){
  showToast(`Simulating: ${scenario}...`);
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
  showToast('Running background worker cycle...');
  await fetch('/admin/process', {method: 'POST'});
  showToast('Cycle completed.');
  loadData();
});

loadData();
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
    """Serves the Customer 360° Directory and Account Intelligence page using shadcn/ui design tokens."""
    dist_index = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html"))
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Customer 360° Directory — AI Revenue Recovery</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --background: #FFFFFF;
    --foreground: #000000;
    --card: #FFFFFF;
    --card-foreground: #000000;
    --popover: #FFFFFF;
    --popover-foreground: #000000;
    --primary: #0000EE;
    --primary-foreground: #FFFFFF;
    --secondary: #F1F5FA;
    --secondary-foreground: #000000;
    --muted: #F1F5FA;
    --muted-foreground: #768EA7;
    --accent: #F1F5FA;
    --accent-foreground: #0000EE;
    --destructive: #D52B1E;
    --destructive-foreground: #FFFFFF;
    --success: #006C3F;
    --success-foreground: #FFFFFF;
    --success-muted: #E6F4EA;
    --border: #D0E0FF;
    --input: #D0E0FF;
    --ring: #0000EE;
    --dark-surface: #192839;
    --dark-foreground: #FFFFFF;
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    --radius: 8px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--background);
    color: var(--foreground);
    font-family: var(--font-sans);
    -webkit-font-smoothing: antialiased;
    min-height: 100vh;
  }

  /* shadcn Dark Surface Header */
  .shadcn-header {
    background: var(--dark-surface);
    color: var(--dark-foreground);
    border-bottom: 1px solid #283C50;
    position: sticky;
    top: 0;
    z-index: 50;
  }
  .header-container {
    max-width: 1320px;
    margin: 0 auto;
    padding: 12px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  .brand-lockup {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-badge {
    background: var(--primary);
    color: var(--primary-foreground);
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
  }
  .brand-text h1 {
    font-size: 15px;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: -0.01em;
  }
  .brand-text p {
    font-size: 11px;
    color: var(--muted-foreground);
    font-family: var(--font-mono);
  }

  .nav-tabs-list {
    display: flex;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 3px;
    gap: 2px;
  }
  .nav-tab-trigger {
    color: #A0B2C6;
    text-decoration: none;
    font-size: 12.5px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 6px;
    transition: all 0.15s ease;
  }
  .nav-tab-trigger:hover {
    color: #FFFFFF;
    background: rgba(255, 255, 255, 0.05);
  }
  .nav-tab-trigger.active {
    color: var(--primary-foreground);
    background: var(--primary);
    font-weight: 600;
  }

  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(0, 108, 63, 0.15);
    border: 1px solid rgba(0, 108, 63, 0.35);
    color: #10B981;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 500;
    padding: 5px 10px;
    border-radius: 9999px;
  }
  .status-pulse {
    width: 6px;
    height: 6px;
    background: #10B981;
    border-radius: 50%;
    animation: pulse-ring 2s infinite;
  }
  @keyframes pulse-ring {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.3); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.8; }
  }

  /* Main Wrapper */
  .main-wrapper {
    max-width: 1320px;
    margin: 0 auto;
    padding: 24px;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
    gap: 16px;
    flex-wrap: wrap;
  }
  .page-header-title h2 {
    font-size: 24px;
    font-weight: 700;
    color: var(--foreground);
    letter-spacing: -0.02em;
  }
  .page-header-title p {
    font-size: 13px;
    color: var(--muted-foreground);
    margin-top: 2px;
  }

  /* Buttons */
  .btn {
    font-family: var(--font-sans);
    font-size: 12.5px;
    font-weight: 500;
    padding: 8px 14px;
    border-radius: var(--radius);
    border: 1px solid transparent;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    transition: all 0.15s ease;
    text-decoration: none;
  }
  .btn-default { background: var(--primary); color: var(--primary-foreground); }
  .btn-default:hover { background: #0000C8; }
  .btn-secondary { background: var(--secondary); color: var(--foreground); border-color: var(--border); }
  .btn-secondary:hover { background: #E4ECF6; }
  .btn-outline { background: #FFFFFF; color: var(--foreground); border-color: var(--border); }
  .btn-outline:hover { background: var(--muted); }
  .btn-destructive { background: var(--destructive); color: var(--destructive-foreground); }
  .btn-success { background: var(--success); color: var(--success-foreground); }
  .btn-sm { font-size: 11.5px; padding: 5px 10px; border-radius: 6px; }

  /* KPI Grid */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }
  @media (max-width: 1024px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
  @media (max-width: 640px) { .kpi-grid { grid-template-columns: 1fr; } }
  .kpi-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.03);
  }
  .kpi-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-family: var(--font-mono);
    margin-bottom: 6px;
  }
  .kpi-value {
    font-size: 26px;
    font-weight: 700;
    color: var(--foreground);
    letter-spacing: -0.02em;
  }
  .kpi-value.primary { color: var(--primary); }
  .kpi-value.success { color: var(--success); }
  .kpi-subtitle {
    font-size: 11.5px;
    color: var(--muted-foreground);
    margin-top: 4px;
  }

  /* Search & Segment Filter Toolbar */
  .search-filter-card {
    background: var(--muted);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 18px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  .search-input-group {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    max-width: 380px;
    background: #FFFFFF;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 6px 12px;
  }
  .search-input-group input {
    width: 100%;
    border: none;
    outline: none;
    font-family: var(--font-sans);
    font-size: 13px;
    color: var(--foreground);
    background: transparent;
  }
  .filter-pills {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
  .pill-trigger {
    font-size: 12px;
    padding: 5px 12px;
    background: #FFFFFF;
    color: var(--muted-foreground);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    cursor: pointer;
    transition: all 0.15s ease;
    font-weight: 500;
  }
  .pill-trigger:hover {
    color: var(--foreground);
    background: #F8FAFD;
  }
  .pill-trigger.active {
    background: var(--primary);
    color: var(--primary-foreground);
    border-color: var(--primary);
    font-weight: 600;
  }

  /* Split Grid */
  .split-grid {
    display: grid;
    grid-template-columns: 1.45fr 1fr;
    gap: 20px;
    align-items: start;
  }
  @media (max-width: 960px) { .split-grid { grid-template-columns: 1fr; } }

  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
  }
  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .card-title { font-size: 15px; font-weight: 600; color: var(--foreground); }
  .card-description { font-size: 12px; color: var(--muted-foreground); }

  /* shadcn Table */
  .table-responsive {
    max-height: 600px;
    overflow-y: auto;
  }
  .shadcn-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
  }
  .shadcn-table th {
    background: var(--muted);
    padding: 10px 14px;
    text-align: left;
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--muted-foreground);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .shadcn-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }
  .cust-table-row {
    cursor: pointer;
    transition: background 0.15s ease;
  }
  .cust-table-row:hover { background: #F8FAFD; }
  .cust-table-row.active {
    background: var(--secondary);
    border-left: 4px solid var(--primary);
  }

  /* Badges */
  .badge {
    display: inline-flex;
    align-items: center;
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    padding: 2.5px 8px;
    border-radius: 9999px;
    border: 1px solid transparent;
  }
  .badge-high { background: var(--success-muted); color: var(--success); border-color: #A8D5BA; }
  .badge-enterprise { background: var(--secondary); color: var(--primary); border-color: var(--border); }
  .badge-standard { background: var(--muted); color: #334155; border-color: var(--border); }
  .badge-trial { background: #FEF7E0; color: #B06000; border-color: #FCE293; }

  /* Drawer Details */
  .drawer-content { padding: 20px; }
  .drawer-empty { padding: 60px 20px; text-align: center; color: var(--muted-foreground); font-size: 13px; }
  .kv-table {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 8px 12px;
    font-size: 12.5px;
    margin: 16px 0 20px;
    padding: 14px;
    background: var(--muted);
    border: 1px solid var(--border);
    border-radius: var(--radius);
  }
  .kv-key {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--muted-foreground);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .kv-val { font-weight: 500; color: var(--foreground); }

  .action-box {
    background: var(--muted);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    margin-top: 18px;
  }
  .action-box h4 {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 10px;
    color: var(--foreground);
  }

  .toast {
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: var(--dark-surface);
    color: var(--dark-foreground);
    border: 1px solid #344B62;
    padding: 10px 18px;
    border-radius: var(--radius);
    font-size: 12.5px;
    font-family: var(--font-mono);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    display: none;
    z-index: 100;
  }
</style>
</head>
<body>

  <!-- Top Dark Surface Header -->
  <header class="shadcn-header">
    <div class="header-container">
      <div class="brand-lockup">
        <div class="brand-badge">⚡</div>
        <div class="brand-text">
          <h1>Autonomous Revenue Recovery</h1>
          <p>Intelligent Dunning & Win-Back Agent</p>
        </div>
      </div>

      <nav class="nav-tabs-list">
        <a href="/dashboard" class="nav-tab-trigger">📊 Operations Hub</a>
        <a href="/customers" class="nav-tab-trigger active">👥 Customer 360°</a>
        <a href="/analytics" class="nav-tab-trigger">📈 Recovery Funnel</a>
        <a href="/docs" target="_blank" class="nav-tab-trigger">⚡ OpenAPI Docs ↗</a>
      </nav>

      <div class="header-actions">
        <div class="status-pill">
          <span class="status-pulse"></span>
          <span>Directory Synchronized</span>
        </div>
      </div>
    </div>
  </header>

  <main class="main-wrapper">
    
    <div class="page-header">
      <div class="page-header-title">
        <h2>Customer 360° & Risk Intelligence Directory</h2>
        <p>Holistic account profiling, Lifetime Value (LTV) telemetry, and channel compliance preferences.</p>
      </div>
      <div>
        <button class="btn btn-outline" onclick="loadCustomers()">🔄 Refresh Directory</button>
      </div>
    </div>

    <!-- Metric Strip -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Managed Accounts</div>
        <div class="kpi-value primary" id="mTotalCust">0</div>
        <div class="kpi-subtitle">SaaS & E-Commerce Profiles</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Portfolio Lifetime Value</div>
        <div class="kpi-value success" id="mTotalLTV">$0.00</div>
        <div class="kpi-subtitle">Cumulative customer value</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">In-Recovery Accounts</div>
        <div class="kpi-value" id="mInRecovery">0</div>
        <div class="kpi-subtitle">Active dunning workflows</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-title">Recovered Lifetime Revenue</div>
        <div class="kpi-value success" id="mRecoveredLTV">$0.00</div>
        <div class="kpi-subtitle">Total won-back cash</div>
      </div>
    </div>

    <!-- Search & Segment Filters -->
    <div class="search-filter-card">
      <div class="search-input-group">
        <span>🔍</span>
        <input type="text" id="searchInput" placeholder="Search customer ID, name, company..." oninput="filterCustomers()">
      </div>
      <div class="filter-pills">
        <button class="pill-trigger active" onclick="setSegment('all', this)">All Accounts</button>
        <button class="pill-trigger" onclick="setSegment('high_ltv', this)">💎 High-LTV ($5K+)</button>
        <button class="pill-trigger" onclick="setSegment('enterprise', this)">🏢 Enterprise</button>
        <button class="pill-trigger" onclick="setSegment('standard', this)">⚡ Standard</button>
        <button class="pill-trigger" onclick="setSegment('trial', this)">⏳ Free Trial</button>
        <button class="pill-trigger" onclick="setSegment('in_recovery', this)">🚨 In Recovery</button>
      </div>
    </div>

    <!-- Grid View -->
    <div class="split-grid">
      
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">Customer Accounts Directory</h3>
            <p class="card-description">Directory list with failure risk and LTV classification</p>
          </div>
          <span class="badge badge-default" id="tableCount">0 accounts</span>
        </div>
        <div class="table-responsive">
          <table class="shadcn-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Segment</th>
                <th>LTV</th>
                <th>Plan</th>
                <th>Compliance / DND</th>
                <th>Recovered</th>
              </tr>
            </thead>
            <tbody id="custBody">
              <tr><td colspan="6" style="text-align:center;padding:40px;color:var(--muted-foreground);">Loading customer directory...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Detail Card -->
      <div class="card">
        <div class="card-header">
          <div>
            <h3 class="card-title">Customer 360° Profile</h3>
            <p class="card-description">CRM attributes, recovery telemetry, and direct triggers</p>
          </div>
        </div>
        <div id="custDrawer">
          <div class="drawer-empty">Click any customer from the table on the left to inspect CRM data, failure velocity, and trigger interventions.</div>
        </div>
      </div>

    </div>

  </main>

  <div class="toast" id="toast"></div>

<script>
let allCustomers = [];
let selectedCustId = null;
let currentSegment = 'all';

function showToast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(()=>t.style.display='none', 3500);
}

function money(n){ return '$' + Number(n).toFixed(2); }

function segmentBadge(seg){
  const map = {
    'high_ltv': 'badge-high',
    'enterprise': 'badge-enterprise',
    'standard': 'badge-standard',
    'trial': 'badge-trial'
  };
  return map[seg] || 'badge-standard';
}

function segmentLabel(seg){
  const map = {
    'high_ltv': 'High LTV',
    'enterprise': 'Enterprise',
    'standard': 'Standard',
    'trial': 'Free Trial'
  };
  return map[seg] || seg;
}

async function loadCustomers(){
  try {
    const res = await fetch('/api/customers');
    const data = await res.json();
    allCustomers = data;

    let totalLTV = 0;
    let inRecov = 0;
    let recovLTV = 0;

    data.forEach(c => {
      totalLTV += (c.ltv || 0);
      inRecov += (c.in_progress_count || 0);
      recovLTV += (c.recovered_amount || 0);
    });

    document.getElementById('mTotalCust').textContent = data.length;
    document.getElementById('mTotalLTV').textContent = money(totalLTV);
    document.getElementById('mInRecovery').textContent = inRecov;
    document.getElementById('mRecoveredLTV').textContent = money(recovLTV);

    filterCustomers();

    if (!selectedCustId && data.length > 0) {
      selectCustomer(data[0].customer_id);
    } else if (selectedCustId) {
      const existing = data.find(x => x.customer_id === selectedCustId);
      if (existing) renderCustDrawer(existing);
    }

  } catch(e) {
    console.error('Failed to load customers:', e);
  }
}

function setSegment(seg, btn){
  currentSegment = seg;
  document.querySelectorAll('.pill-trigger').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  filterCustomers();
}

function filterCustomers(){
  const query = (document.getElementById('searchInput').value || '').toLowerCase();
  const filtered = allCustomers.filter(c => {
    const matchQuery = (c.customer_id.toLowerCase().includes(query)) ||
                       (c.name && c.name.toLowerCase().includes(query)) ||
                       (c.company && c.company.toLowerCase().includes(query));
    if (!matchQuery) return false;

    if (currentSegment === 'all') return true;
    if (currentSegment === 'in_recovery') return (c.in_progress_count > 0);
    return c.segment === currentSegment;
  });

  renderTable(filtered);
}

function renderTable(list){
  const tbody = document.getElementById('custBody');
  document.getElementById('tableCount').textContent = list.length + ' accounts';
  tbody.innerHTML = '';

  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--muted-foreground);">No matching customer accounts found.</td></tr>';
    return;
  }

  list.forEach(c => {
    const tr = document.createElement('tr');
    tr.className = 'cust-table-row' + (c.customer_id === selectedCustId ? ' active' : '');
    tr.dataset.id = c.customer_id;
    
    const dndEmail = c.contact_preferences ? c.contact_preferences.email : true;
    const dndSms = c.contact_preferences ? c.contact_preferences.sms : true;
    const dndBadge = (dndSms === false) ? '<span class="badge badge-warning">SMS DND</span>' : '<span class="badge badge-success">ALL OK</span>';

    tr.innerHTML = `
      <td>
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
    dist_index = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "index.html"))
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
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
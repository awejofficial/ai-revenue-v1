# app/routers/admin.py
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

from app.db import get_pool
from app.orchestrator import (
    process_pending_events,
    process_scheduled_cases,
    process_event,
    resolve_case
)

router = APIRouter(tags=["Admin"])


@router.post("/admin/simulate")
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


@router.post("/admin/process")
async def manual_process():
    """Manually triggers pending event processing and scheduled cases."""
    await process_pending_events()
    await process_scheduled_cases()
    return {"status": "processing_completed"}


@router.post("/admin/resolve/{case_id}")
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


@router.get("/admin/action-logs")
@router.get("/admin/action-logs/")
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


@router.post("/admin/seed")
@router.get("/api/seed")
async def seed_database():
    """Seeds the customer directory and sample demo cases if empty or manually requested."""
    try:
        from app.seed_data import seed
        await seed()
        return {"status": "success", "message": "Customer directory and demo cases seeded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/simulate/recovery")
@router.post("/api/simulate/recovery/")
async def api_simulate_recovery(scenario: str = "payment_succeeded"):
    """Simulates recovery event."""
    return await simulate_event(scenario=scenario)

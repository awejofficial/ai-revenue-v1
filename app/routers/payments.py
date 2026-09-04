# app/routers/payments.py
"""
Payments, Live Detector & Honest Exception List Router (Track 03)
Provides Razorpay live failure detection, link settlement sync, and honest exception reporting.
"""

from fastapi import APIRouter, HTTPException, Query
from app.db import get_pool
from app.detector import detect_failed_payments, get_payment_status
from app.actions import sync_payment_links
from app.orchestrator import ingest_live_payment, process_event

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/detect")
async def detect_live_failures(
    hours_back: int = Query(24, ge=1, le=168, description="Lookback window in hours")
):
    """
    Polls the real Razorpay test-mode API (GET /v1/payments) for recent
    failed payments and authorized-not-captured (at-risk) transactions.
    """
    try:
        return detect_failed_payments(hours_back=hours_back)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/ingest-live")
async def ingest_and_recover_live(payment_data: dict):
    """
    Ingests a live payment detected from Razorpay API and immediately triggers
    autonomous recovery on it.
    """
    try:
        return await ingest_live_payment(payment_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest and recovery failed: {str(e)}")


@router.post("/sync-links")
async def sync_links():
    """
    Reconciles settlement status for all pending Razorpay payment links.
    Transitions paid links to RECOVERED and computes verified recovered revenue.
    """
    try:
        return await sync_payment_links()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Link settlement sync failed: {str(e)}")


@router.get("/exceptions")
async def list_honest_exceptions():
    """
    Honest Exception List: Surfaces all payments the agent could NOT resolve.
    Grouped by root_cause with total ₹ value at risk and AI reasoning.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        unresolved = await conn.fetch("""
            SELECT case_id, event_id, customer_id, amount_usd, currency, status,
                   root_cause, recovery_action, payment_link_id, recovery_message,
                   current_retry_count, llm_reasoning, last_action, created_at
            FROM cases
            WHERE status IN ('escalated', 'lost', 'failed')
            ORDER BY created_at DESC
        """)
        
        by_cause: dict = {}
        total_at_risk = 0.0
        
        for r in unresolved:
            cause = r.get("root_cause") or "UNKNOWN"
            amt = float(r.get("amount_usd") or 0.0)
            total_at_risk += amt
            
            if cause not in by_cause:
                by_cause[cause] = {
                    "root_cause": cause,
                    "count": 0,
                    "total_value": 0.0,
                    "payments": []
                }
            by_cause[cause]["count"] += 1
            by_cause[cause]["total_value"] = round(by_cause[cause]["total_value"] + amt, 2)
            by_cause[cause]["payments"].append({
                "id": r["event_id"],
                "case_id": r["case_id"],
                "amount": amt,
                "currency": r.get("currency", "INR"),
                "status": r["status"].upper(),
                "recovery_action": r["recovery_action"] or r["last_action"],
                "gemini_reasoning": r["llm_reasoning"],
                "recovery_message": r["recovery_message"],
                "payment_link_id": r["payment_link_id"],
                "retry_count": r["current_retry_count"],
                "customer_email": r["customer_id"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            })
            
        return {
            "total_exceptions": len(unresolved),
            "total_value_at_risk": round(total_at_risk, 2),
            "by_cause": list(by_cause.values()),
        }


@router.get("/")
async def list_payments(status: str = None, search: str = None, limit: int = 150):
    """Lists payments/cases with root causes, retry counts, and customer copies."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = """
            SELECT case_id, event_id, customer_id, amount_usd, currency, status,
                   root_cause, recovery_action, payment_link_id, recovery_message,
                   current_retry_count, llm_reasoning, last_action, created_at
            FROM cases
        """
        clauses = []
        params = []
        if status and status.upper() != "ALL":
            clauses.append(f"UPPER(status) = ${len(params) + 1}")
            params.append(status.upper())
        if search and search.strip():
            clauses.append(f"(LOWER(customer_id) LIKE ${len(params) + 1} OR LOWER(event_id) LIKE ${len(params) + 1} OR LOWER(COALESCE(root_cause, '')) LIKE ${len(params) + 1})")
            params.append(f"%{search.strip().lower()}%")
        
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT " + str(min(limit, 300))
        
        rows = await conn.fetch(query, *params)
        return [
            {
                "id": r["event_id"] if (r.get("event_id") and str(r["event_id"]).startswith("pay_")) else f"pay_{r.get('event_id', '') or str(r['case_id'])}",
                "payment_id": r["event_id"] if (r.get("event_id") and str(r["event_id"]).startswith("pay_")) else f"pay_{r.get('event_id', '') or str(r['case_id'])}",
                "case_id": r["case_id"],
                "customer_email": r["customer_id"],
                "amount": float(r["amount_usd"] or 0.0),
                "currency": r.get("currency", "INR"),
                "status": r["status"].upper(),
                "root_cause": r.get("root_cause") or "UNKNOWN",
                "recovery_action": r.get("recovery_action") or r.get("last_action") or "ESCALATED",
                "gemini_reasoning": r.get("llm_reasoning") or "",
                "recovery_message": r.get("recovery_message") or "",
                "payment_link_id": r.get("payment_link_id"),
                "retry_count": r.get("current_retry_count") or 0,
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]


@router.get("/{payment_id}")
async def get_payment(payment_id: str):
    """Retrieves full details for a single payment."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.fetchrow("""
            SELECT case_id, event_id, customer_id, amount_usd, currency, status,
                   root_cause, recovery_action, payment_link_id, recovery_message,
                   current_retry_count, llm_reasoning, last_action, created_at
            FROM cases
            WHERE event_id = $1 OR CAST(case_id AS TEXT) = $1
        """, payment_id)
        if not r:
            raise HTTPException(status_code=404, detail="Payment not found")
        return {
            "id": r["event_id"],
            "case_id": r["case_id"],
            "customer_email": r["customer_id"],
            "amount": float(r["amount_usd"] or 0.0),
            "currency": r.get("currency", "INR"),
            "status": r["status"].upper(),
            "root_cause": r.get("root_cause") or "UNKNOWN",
            "recovery_action": r.get("recovery_action") or r.get("last_action"),
            "gemini_reasoning": r.get("llm_reasoning") or "",
            "recovery_message": r.get("recovery_message") or "",
            "payment_link_id": r.get("payment_link_id"),
            "retry_count": r["current_retry_count"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }


@router.post("/{payment_id}/recover")
async def recover_single_payment(payment_id: str):
    """1-Click manual recovery execution for a single payment."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        case = await conn.fetchrow("""
            SELECT case_id, event_id, customer_id, status FROM cases 
            WHERE event_id = $1 OR CAST(case_id AS TEXT) = $1
        """, payment_id)
        if not case:
            raise HTTPException(status_code=404, detail="Payment not found")
        if case["status"] in ("resolved", "recovered"):
            return {"status": "ALREADY_RESOLVED", "message": "Payment is already recovered."}
        
        # Reset event processed flag and trigger process_event
        ev_id = case["event_id"]
        await conn.execute("UPDATE raw_events SET is_processed = FALSE WHERE event_id = $1", ev_id)
        
    await process_event(ev_id)
    
    async with pool.acquire() as conn:
        updated = await conn.fetchrow("SELECT * FROM cases WHERE event_id = $1", ev_id)
        return {
            "status": updated["status"].upper() if updated else "PROCESSED",
            "action": updated["recovery_action"] if updated else None,
            "payment_id": ev_id,
            "root_cause": updated["root_cause"] if updated else None,
            "customer_message": updated["recovery_message"] if updated else None,
            "payment_link_id": updated["payment_link_id"] if updated else None
        }

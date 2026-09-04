# app/routers/webhooks.py
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

from app.db import get_pool
from app.orchestrator import process_event, resolve_case

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/psp")
@router.post("/razorpay")
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
    
    asyncio.create_task(process_event(event_id))
    
    return {"status": "ingested", "event_id": event_id, "customer_id": customer_id}


@router.post("/billing")
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

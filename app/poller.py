# app/poller.py
"""
Background Poller for Invoicing & ERP Systems (Odoo, Stripe Invoicing, SAP, Custom Billing)
Periodically ingests overdue invoices and triggers the AI Revenue Recovery Agent.
"""

import json
import asyncio
from datetime import datetime
from app.db import get_pool
from app.orchestrator import process_event


async def fetch_overdue_invoices_from_erp() -> list[dict]:
    """
    Simulates or calls an external billing/ERP API to find overdue invoices.
    Replace with actual external HTTP calls (e.g. via httpx) when integrating with live ERP.
    """
    # Demo simulated batch
    return [
        {
            "invoice_id": "INV-2024-001",
            "customer_id": "cus_high_ltv_01",
            "amount_due": 1250.00,
            "currency": "USD",
            "days_overdue": 5,
            "description": "Enterprise Subscription - Monthly"
        }
    ]


async def ingest_overdue_invoices() -> int:
    """Ingests newly discovered overdue invoices into the raw_events table."""
    overdue_list = await fetch_overdue_invoices_from_erp()
    pool = await get_pool()
    ingested_count = 0
    
    async with pool.acquire() as conn:
        for inv in overdue_list:
            event_id = f"erp_inv_{inv['invoice_id']}"
            
            # Check if already ingested
            exists = await conn.fetchrow("SELECT event_id FROM raw_events WHERE event_id = $1", event_id)
            if exists:
                continue
                
            canonical_event = {
                "event_id": event_id,
                "customer_id": inv['customer_id'],
                "event_type": "invoice_overdue",
                "amount_usd": inv['amount_due'],
                "currency": inv.get('currency', 'USD'),
                "raw_error_code": "invoice_unpaid",
                "raw_error_message": f"Invoice #{inv['invoice_id']} overdue by {inv['days_overdue']} days"
            }
            
            await conn.execute(
                """
                INSERT INTO raw_events (event_id, event_type, customer_id, payload, canonical_event, is_processed) 
                VALUES ($1, $2, $3, $4, $5, FALSE)
                ON CONFLICT (event_id) DO NOTHING
                """,
                event_id,
                "invoice_overdue",
                inv['customer_id'],
                json.dumps(inv),
                json.dumps(canonical_event)
            )
            ingested_count += 1
            print(f"[Poller] Ingested overdue invoice event: {event_id}")
            
    return ingested_count


async def poll_billing_system(interval_seconds: int = 3600):
    """Continuous background worker that runs periodically."""
    print(f"[Poller] Billing system poller worker started (Interval: {interval_seconds}s).")
    while True:
        try:
            count = await ingest_overdue_invoices()
            if count > 0:
                print(f"[Poller] Ingested {count} new overdue invoice(s).")
        except Exception as e:
            print(f"[Poller] Ingestion error: {e}")
            
        await asyncio.sleep(interval_seconds)
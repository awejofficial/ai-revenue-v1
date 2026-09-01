# app/routers/analytics.py
import json
from fastapi import APIRouter
from app.db import get_pool
from app.routers.dashboard import dashboard_stats

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("")
@router.get("/")
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


@router.get("/summary")
@router.get("/summary/")
async def api_analytics_summary():
    """Returns summarized stats for dashboard analytics."""
    return await dashboard_stats()


@router.get("/by-reason")
@router.get("/by-reason/")
async def api_analytics_by_reason():
    """Returns failure breakdown by root cause reason."""
    analytics = await api_analytics()
    return analytics.get("failure_codes", {})

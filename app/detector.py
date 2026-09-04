# app/detector.py
"""
Live Razorpay Payment Failure & Revenue At-Risk Detector
Polls Razorpay test-mode API (GET /v1/payments) for:
  1. Failed payments in the last N hours
  2. Authorized-but-not-captured payments (at-risk of authorization expiry)
  3. Captured payments for reconciliation telemetry
"""

import os
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

_client = None

def get_razorpay_client():
    global _client
    if _client:
        return _client
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        try:
            import razorpay
            _client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        except Exception as e:
            logger.warning(f"[Detector] Failed to init Razorpay client: {e}")
    return _client


def detect_failed_payments(hours_back: int = 24, max_count: int = 100) -> dict:
    """
    Polls Razorpay GET /v1/payments for failed & at-risk payments in the last N hours.
    Returns structured data for the Live Detector UI and agent recovery pipeline.
    """
    polled_at = datetime.now(timezone.utc).isoformat()
    client = get_razorpay_client()
    
    if not client:
        return {
            "source": "razorpay_live_poll",
            "polled_at": polled_at,
            "hours_back": hours_back,
            "error": "Razorpay API credentials not configured. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env.",
            "note": "Running in dry-run mode. Add Razorpay test keys to poll live test transactions.",
            "total_fetched": 0,
            "failed_count": 0,
            "authorized_not_captured": 0,
            "captured_count": 0,
            "failed_payments": [],
            "at_risk_payments": [],
        }

    try:
        from_ts = int((datetime.now(timezone.utc) - timedelta(hours=hours_back)).timestamp())
        params = {
            "count": min(max_count, 100),
            "from": from_ts,
        }
        response = client.payment.all(params)
        all_payments = response.get("items", []) if isinstance(response, dict) else []

        failed = [p for p in all_payments if p.get("status") == "failed"]
        authorized = [p for p in all_payments if p.get("status") == "authorized"]
        captured = [p for p in all_payments if p.get("status") == "captured"]

        return {
            "source": "razorpay_live_poll",
            "polled_at": polled_at,
            "hours_back": hours_back,
            "total_fetched": len(all_payments),
            "failed_count": len(failed),
            "authorized_not_captured": len(authorized),
            "captured_count": len(captured),
            "failed_payments": [
                {
                    "id": p.get("id"),
                    "amount": (p.get("amount") or 0) / 100.0,
                    "currency": p.get("currency", "INR"),
                    "status": p.get("status", "failed").upper(),
                    "error_code": p.get("error_code") or "GATEWAY_ERROR",
                    "error_description": p.get("error_description") or "Live payment failure on Razorpay gateway",
                    "email": p.get("email") or "customer@example.com",
                    "contact": p.get("contact") or "+919999999999",
                    "method": p.get("method", "card"),
                    "created_at": datetime.fromtimestamp(p["created_at"], tz=timezone.utc).isoformat() if p.get("created_at") else polled_at,
                }
                for p in failed
            ],
            "at_risk_payments": [
                {
                    "id": p.get("id"),
                    "amount": (p.get("amount") or 0) / 100.0,
                    "currency": p.get("currency", "INR"),
                    "status": p.get("status", "authorized").upper(),
                    "risk": "authorized_not_captured",
                    "method": p.get("method", "card"),
                    "created_at": datetime.fromtimestamp(p["created_at"], tz=timezone.utc).isoformat() if p.get("created_at") else polled_at,
                }
                for p in authorized
            ],
        }
    except Exception as e:
        logger.error(f"[Detector] Razorpay API call failed: {e}")
        return {
            "source": "razorpay_live_poll",
            "polled_at": polled_at,
            "hours_back": hours_back,
            "error": str(e),
            "note": "Check that your Razorpay Key ID and Secret are valid test mode credentials.",
            "total_fetched": 0,
            "failed_count": 0,
            "authorized_not_captured": 0,
            "captured_count": 0,
            "failed_payments": [],
            "at_risk_payments": [],
        }


def get_payment_status(payment_id: str) -> dict:
    """Fetches real-time status of a specific Razorpay payment."""
    if not _client:
        return {"error": "Razorpay client not configured", "payment_id": payment_id}
    try:
        p = _client.payment.fetch(payment_id)
        return {
            "id": p.get("id"),
            "amount": (p.get("amount") or 0) / 100.0,
            "currency": p.get("currency", "INR"),
            "status": p.get("status"),
            "error_code": p.get("error_code"),
            "error_description": p.get("error_description"),
            "method": p.get("method"),
            "created_at": datetime.fromtimestamp(p["created_at"], tz=timezone.utc).isoformat() if p.get("created_at") else None,
        }
    except Exception as e:
        logger.error(f"[Detector] Failed to fetch payment {payment_id}: {e}")
        return {"error": str(e), "payment_id": payment_id}

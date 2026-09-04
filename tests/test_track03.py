# tests/test_track03.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
import httpx

from app.db import init_db, get_pool
from app.llm_client import llm_diagnose, get_heuristic_classification
from app.detector import detect_failed_payments
from app.orchestrator import run_batch, ingest_live_payment
from app.actions import sync_payment_links
from app.main import app

# ── 1. Classifier & Diagnostic Fallback Tests ──────────────────────────────

def test_fallback_classification_bank_decline():
    res = get_heuristic_classification("BAD_REQUEST_ERROR", "Payment declined by bank issuer")
    assert res["root_cause"] == "BANK_DECLINE"
    assert res["confidence"] >= 0.7
    assert "recovery_message" in res
    assert "payment" in res["recovery_message"].lower() or "bank" in res["recovery_message"].lower()

def test_fallback_classification_network_timeout():
    res = get_heuristic_classification("GATEWAY_ERROR", "Network switch timeout during 3DS")
    assert res["root_cause"] == "NETWORK_TIMEOUT"

def test_fallback_classification_fraud():
    res = get_heuristic_classification("BAD_REQUEST_ERROR", "Payment flagged as suspicious high risk activity")
    assert res["root_cause"] == "FRAUD_FLAG"
    assert res["action"] in ("human_handoff", "ESCALATE_TO_HUMAN")

def test_fallback_classification_checkout_abandoned():
    res = get_heuristic_classification("CHECKOUT_ABANDONED", "Customer abandoned payment checkout session")
    assert res["root_cause"] == "CHECKOUT_ABANDONED"

def test_fallback_classification_card_expired():
    res = get_heuristic_classification("BAD_REQUEST_ERROR", "Card expired or validity ended")
    assert res["root_cause"] == "CARD_EXPIRED"

def test_fallback_classification_insufficient_funds():
    res = get_heuristic_classification("BAD_REQUEST_ERROR", "Insufficient balance in customer account")
    assert res["root_cause"] == "INSUFFICIENT_FUNDS"

def test_fallback_classification_subscription():
    res = get_heuristic_classification("SUBSCRIPTION_ERROR", "Mandate debit failed for monthly renewal")
    assert res["root_cause"] == "SUBSCRIPTION_FAILED"

def test_fallback_classification_overdue_invoice():
    res = get_heuristic_classification("INVOICE_OVERDUE", "B2B Invoice #INV-882 past 15 days due date")
    assert res["root_cause"] == "OVERDUE_INVOICE"

def test_fallback_classification_unknown():
    res = get_heuristic_classification("UNKNOWN_XYZ", "Some weird undocumented error")
    assert res["root_cause"] == "UNKNOWN"

# ── 2. Async Classifier with Gemini Mocking ─────────────────────────────────

@pytest.mark.asyncio
async def test_classify_failure_mode_with_mock():
    mock_model = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '```json\n{"root_cause": "BANK_DECLINE", "confidence": 0.94, "action": "GENERATE_PAYMENT_LINK", "customer_message": "Namaste! Aapka payment bank issue ki wajah se atak gaya hai. Kripya naye link se complete karein.", "reasoning": "Issuer bank declined 3DS auth.", "delay_hours": 24}\n```'
    mock_model.generate_content.return_value = mock_resp

    with patch("app.llm_client.model", mock_model), patch("app.llm_client.GEMINI_API_KEY", "test-key"):
        res = await llm_diagnose("BAD_REQUEST_ERROR", "Bank declined auth", 4500.0, "INR")
        assert res["root_cause"] == "BANK_DECLINE"
        assert res["confidence"] == 0.94
        assert "Namaste" in res["customer_message"]
        assert res["action"] == "GENERATE_PAYMENT_LINK"

# ── 3. Live Razorpay Detector Unit Tests ────────────────────────────────────

@pytest.mark.asyncio
async def test_detector_failed_and_at_risk():
    fake_failed_payment = {
        "id": "pay_fake_123",
        "amount": 299900,
        "currency": "INR",
        "status": "failed",
        "method": "card",
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Issuer bank declined transaction",
        "email": "test@domain.com",
        "contact": "+919876543210",
        "created_at": 1725400000,
    }
    fake_auth_payment = {
        "id": "pay_auth_456",
        "amount": 899900,
        "currency": "INR",
        "status": "authorized",
        "method": "upi",
        "captured": False,
        "email": "auth@domain.com",
        "contact": "+919123456780",
        "created_at": 1725400000,
    }

    mock_client = MagicMock()
    mock_client.payment.all.return_value = {
        "items": [fake_failed_payment, fake_auth_payment]
    }

    with patch("app.detector.get_razorpay_client", return_value=mock_client):
        data = detect_failed_payments(hours_back=24)
        assert data["total_fetched"] == 2
        assert len(data["failed_payments"]) == 1
        assert data["failed_payments"][0]["id"] == "pay_fake_123"
        assert data["failed_payments"][0]["amount"] == 2999.0
        assert len(data["at_risk_payments"]) == 1
        assert data["at_risk_payments"][0]["id"] == "pay_auth_456"

# ── 4. Batch Orchestrator & Stopping Rule Circuit Breaker ───────────────────

@pytest.mark.asyncio
async def test_orchestrator_circuit_breaker_on_two_failures():
    await init_db()

    call_count = {"n": 0}

    async def mock_process(conn, payment):
        call_count["n"] += 1
        if call_count["n"] in (1, 2):
            return {
                "id": payment["id"],
                "status": "FAILED",
                "root_cause": "BANK_DECLINE",
                "action": "AUTO_RETRY",
                "amount": payment["amount"],
            }
        return {
            "id": payment["id"],
            "status": "RECOVERED",
            "root_cause": "BANK_DECLINE",
            "action": "GENERATE_PAYMENT_LINK",
            "amount": payment["amount"],
        }

    with patch("app.orchestrator._process_single_payment", side_effect=mock_process):
        result = await run_batch(count=5)

    assert result["stopped_early"] is True
    assert result["stopped_at_index"] == 1
    assert result["failed"] == 2
    assert result["skipped"] == 3
    assert result["total"] == 5

# ── 5. Payment Link Settlement Sync ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_sync_payment_links():
    pool = await init_db()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO cases (event_id, customer_id, case_type, amount_usd, currency, status, payment_link_id)
            VALUES ('evt_sync_test_99', 'cus_sync_test', 'payment_failed', 1500.0, 'INR', 'awaiting_input', 'plink_test_999')
            ON CONFLICT (event_id) DO UPDATE SET status = 'awaiting_input', payment_link_id = 'plink_test_999'
            RETURNING case_id
            """
        )
        case_id = row["case_id"]

    mock_client = MagicMock()
    mock_client.payment_link.fetch.return_value = {
        "id": "plink_test_999",
        "status": "paid",
        "amount_paid": 150000,
    }

    with patch("app.actions.razorpay_client", mock_client):
        sync_res = await sync_payment_links()
        assert sync_res["links_checked"] >= 1
        assert sync_res["newly_recovered"] >= 1
        assert sync_res["money_recovered"] >= 1500.0

    async with pool.acquire() as conn:
        updated = await conn.fetchrow("SELECT status FROM cases WHERE case_id = $1", case_id)
        assert updated["status"] == "resolved"

# ── 6. FastAPI Router Integration Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_api_endpoints():
    await init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /payments/exceptions
        res_exc = await client.get("/payments/exceptions")
        assert res_exc.status_code == 200
        data = res_exc.json()
        assert "total_exceptions" in data
        assert "by_cause" in data

        # GET /agent/runs
        res_runs = await client.get("/agent/runs")
        assert res_runs.status_code == 200
        assert isinstance(res_runs.json(), list)

        # POST /payments/sync-links
        mock_client = MagicMock()
        mock_client.payment_link.fetch.return_value = {"status": "created"}
        with patch("app.actions.razorpay_client", mock_client):
            res_sync = await client.post("/payments/sync-links")
            assert res_sync.status_code == 200
            assert "newly_recovered" in res_sync.json()

# ── 7. Policy Guardrails & Compliance Tests ─────────────────────────────────

def test_fraud_flag_policy_strict_escalation():
    from app.orchestrator import apply_policy
    case_data = {"current_retry_count": 0, "amount_usd": 1500.0}
    diagnosis = {"root_cause": "FRAUD_FLAG", "action": "retry_payment", "delay_hours": 24}
    context = {"segment": "high_ltv", "plan": "enterprise"}

    policy = apply_policy(case_data, diagnosis, context)
    assert policy["root_cause"] == "FRAUD_FLAG"
    assert policy["action"] == "human_handoff"
    assert policy["delay_hours"] == 0
    assert "strict compliance" in policy["reasoning"].lower()

def test_max_retries_policy_bound_enforced():
    from app.orchestrator import apply_policy
    case_data = {"current_retry_count": 3, "amount_usd": 499.0}
    diagnosis = {"root_cause": "BANK_DECLINE", "action": "retry_payment", "delay_hours": 24}
    context = {"segment": "standard", "plan": "pro"}

    policy = apply_policy(case_data, diagnosis, context)
    assert policy["action"] == "human_handoff"
    assert "maximum allowed retries" in policy["reasoning"].lower()

# ── 8. Webhook Processing Integration Tests ─────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_razorpay_payment_failed():
    await init_db()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "event": "payment.failed",
            "id": "wh_rzp_test_01",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_wh_test_01",
                        "amount": 499900,
                        "currency": "INR",
                        "status": "failed",
                        "email": "wh_customer@example.com",
                        "contact": "+919876543210",
                        "error_code": "BAD_REQUEST_ERROR",
                        "error_description": "Bank declined payment",
                        "notes": {"customer_id": "wh_customer@example.com"}
                    }
                }
            }
        }
        res = await client.post("/webhooks/razorpay", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ingested"
        assert data["event_id"] == "wh_rzp_test_01"

@pytest.mark.asyncio
async def test_webhook_payment_link_paid_auto_resolves():
    pool = await init_db()

    # Pre-create case with payment link
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO cases (event_id, customer_id, case_type, amount_usd, currency, status, payment_link_id)
            VALUES ('evt_wh_plink_01', 'cus_wh_plink', 'payment_failed', 3499.0, 'INR', 'awaiting_input', 'plink_wh_999')
            ON CONFLICT (event_id) DO UPDATE SET status = 'awaiting_input', payment_link_id = 'plink_wh_999'
            RETURNING case_id
        """)
        cid = row["case_id"]

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "event": "payment_link.paid",
            "id": "wh_plink_paid_01",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_wh_999",
                        "amount": 349900,
                        "status": "paid",
                        "notes": {"case_id": str(cid), "customer_id": "cus_wh_plink"}
                    }
                }
            }
        }
        res = await client.post("/webhooks/razorpay", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "auto_resolved"

    # Verify resolved in DB
    async with pool.acquire() as conn:
        updated = await conn.fetchrow("SELECT status FROM cases WHERE case_id = $1", cid)
        assert updated["status"] == "resolved"


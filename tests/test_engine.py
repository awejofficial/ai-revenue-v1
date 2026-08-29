# tests/test_engine.py
import asyncio
import json
import sys
import time

# Ensure UTF-8 output encoding if possible
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.db import init_db, get_pool
from app.orchestrator import (
    get_customer_context,
    diagnose_root_case,
    apply_policy,
    process_event,
    resolve_case
)
from app.actions import (
    create_razorpay_payment_link,
    retry_payment,
    send_email,
    send_sms,
    escalate_to_human
)

async def test_all():
    print("==================================================")
    print("[TEST] RUNNING AI REVENUE RECOVERY ENGINE TEST SUITE")
    print("==================================================")

    pool = await init_db()

    # 1. Test Customer Context Retrieval
    print("\n--- 1. Testing Customer Context Retrieval ---")
    ctx_high = await get_customer_context("cus_high_ltv_01")
    print(f"High LTV Context: Segment={ctx_high['segment']}, LTV=${ctx_high['ltv']}, Plan={ctx_high['plan']}")
    assert ctx_high['segment'] == 'high_ltv', f"Expected high_ltv, got {ctx_high['segment']}"
    assert ctx_high['ltv'] == 8500, f"Expected 8500, got {ctx_high['ltv']}"
    print("[PASS] Customer Context test passed!")

    # 2. Test Rules Diagnosis
    print("\n--- 2. Testing Diagnosis Engine (Deterministic Rules) ---")
    diag_high = await diagnose_root_case("insufficient_funds", "Declined", 499.0, "USD", "payment_failed", ctx_high)
    print(f"High-LTV Insufficient Funds Diagnosis: {diag_high['action']} in {diag_high['delay_hours']}h - {diag_high['reasoning']}")
    assert diag_high['action'] == 'retry_payment'
    assert diag_high['delay_hours'] == 72, "High LTV should get 72h payday retry"

    ctx_fraud = await get_customer_context("cus_fraud_05")
    diag_fraud = await diagnose_root_case("suspected_fraud", "Fraud detected", 350.0, "USD", "payment_failed", ctx_fraud)
    print(f"Fraud Diagnosis: {diag_fraud['action']} - {diag_fraud['reasoning']}")
    assert diag_fraud['action'] == 'human_handoff'

    print("[PASS] Rules Diagnosis tests passed!")

    # 3. Test Policy Guardrails
    print("\n--- 3. Testing Policy Engine Bounds ---")
    case_trial = {"current_retry_count": 1, "amount_usd": 19.0, "max_retries": 1}
    ctx_trial = {"segment": "trial", "plan": "free_trial"}
    pol_trial = apply_policy(case_trial, {"action": "retry_payment"}, ctx_trial)
    print(f"Trial Policy: {pol_trial['action']} - {pol_trial.get('reasoning')}")
    assert pol_trial['action'] == 'human_handoff', "Trial user exceeding 1 retry must escalate"

    print("[PASS] Policy Engine tests passed!")

    # 4. Test Dual-Gateway Links (Razorpay & Stripe)
    print("\n--- 4. Testing Multi-Gateway Actions ---")
    rzp_res = await create_razorpay_payment_link("cus_high_ltv_01", 249.00, "INR", "test@example.com", "+919876543210", 101)
    print(f"Razorpay Link Result: {rzp_res}")
    assert rzp_res['success'] is True
    assert "payment_link" in rzp_res

    stripe_res = await retry_payment("cus_standard_02", 49.00, "USD", email="test2@example.com", case_id=102)
    print(f"Stripe Link Result: {stripe_res}")
    assert stripe_res['success'] is True
    assert "payment_link" in stripe_res

    print("[PASS] Dual Gateway actions passed!")

    # 5. Test Auto-Resolution Loop
    print("\n--- 5. Testing Auto-Resolution Loop ---")
    ts = int(time.time() * 1000)
    ev_id = f"test_res_loop_{ts}"
    canonical = {
        "event_id": ev_id,
        "customer_id": "cus_standard_02",
        "event_type": "payment_failed",
        "amount_usd": 49.00,
        "currency": "USD",
        "raw_error_code": "card_expired",
        "raw_error_message": "Card expired"
    }
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO raw_events (event_id, event_type, customer_id, payload, canonical_event, is_processed) 
            VALUES ($1, $2, $3, $4, $5, FALSE)
            """,
            ev_id, "payment_failed", "cus_standard_02", json.dumps(canonical), json.dumps(canonical)
        )
    await process_event(ev_id)

    # Now simulate payment succeeded webhook
    res_result = await resolve_case(customer_id="cus_standard_02", amount_recovered=49.00, payment_reference="test_stripe_charge_999")
    print(f"Resolution Result: {res_result}")
    assert res_result['success'] is True

    async with pool.acquire() as conn:
        resolved_case = await conn.fetchrow("SELECT * FROM cases WHERE customer_id = 'cus_standard_02' ORDER BY updated_at DESC LIMIT 1")
        print(f"Case #{resolved_case['case_id']} Status: {resolved_case['status']}")
        assert resolved_case['status'] == 'resolved'

    print("[PASS] Auto-Resolution loop test passed!")

    print("\n==================================================")
    print("[SUCCESS] ALL TESTS PASSED! ENGINE IS 100% OPERATIONAL.")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_all())

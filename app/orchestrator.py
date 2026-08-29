# app/orchestrator.py
"""
Revenue Recovery Agent - Orchestrator Core
Full autonomous lifecycle: Detect → Diagnose → Decide → Execute → Audit → Auto-Resolve
Uses Rules-First + Google Gemini Fallback for context-enriched intelligence.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from app.db import get_pool
from app.actions import (
    retry_payment,
    send_email,
    send_sms,
    escalate_to_human,
    notify_recovery_success,
    get_customer_contact,
    log_action
)
from app.llm_client import llm_diagnose


# ============================================================
# STEP 0: CONTEXT FETCHER (CRM + Historical Failures)
# ============================================================
async def get_customer_context(customer_id: str) -> dict:
    """
    Fetches rich customer context from the database:
    - LTV (Lifetime Value)
    - Segment (high_ltv, standard, trial)
    - 90-day failure & recovery track record
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # 1. Fetch CRM data
        crm_row = await conn.fetchrow(
            "SELECT crm_data FROM customers WHERE customer_id = $1",
            customer_id
        )
        
        crm_data = {}
        if crm_row and crm_row['crm_data']:
            crm = crm_row['crm_data']
            crm_data = crm if isinstance(crm, dict) else json.loads(crm)
        
        # 2. Fetch past case history
        history = await conn.fetch("""
            SELECT status, amount_usd, created_at 
            FROM cases 
            WHERE customer_id = $1 
              AND created_at > NOW() - INTERVAL '3 months'
            ORDER BY created_at DESC
        """, customer_id)
        
        total_attempts = len(history)
        failed_attempts = sum(1 for h in history if h['status'] in ['escalated', 'lost', 'retrying', 'awaiting_input'])
        resolved_attempts = sum(1 for h in history if h['status'] == 'resolved')
        
        ltv = float(crm_data.get('ltv', 0))
        segment = crm_data.get('segment', 'standard')
        plan = crm_data.get('plan', 'monthly')
        
        # Auto-detect high LTV if threshold reached
        if ltv >= 5000:
            segment = 'high_ltv'
        
        return {
            "customer_id": customer_id,
            "ltv": ltv,
            "segment": segment,
            "plan": plan,
            "total_attempts": total_attempts,
            "failed_attempts": failed_attempts,
            "resolved_attempts": resolved_attempts,
            "is_repeat_offender": failed_attempts >= 2,
            "is_first_failure": failed_attempts == 0,
            "recent_failure_amounts": [float(h['amount_usd'] or 0) for h in history[:3]]
        }


# ============================================================
# STEP 1: DIAGNOSIS ENGINE (Rules + Gemini LLM)
# ============================================================
async def diagnose_root_case(
    error_code: str | None, 
    error_message: str | None, 
    amount: float, 
    currency: str,
    event_type: str,
    context: dict
) -> dict:
    """
    Hybrid diagnosis using deterministic rules for fast execution,
    with instant fallback to Gemini LLM for rare/complex failure patterns.
    """
    code = (error_code or "").lower().strip()
    
    # Rule 1: High-LTV First-time Insufficient Balance -> 72h Payday retry
    if code in ["insufficient_funds", "card_declined_insufficient_funds"] and context.get('is_first_failure') and context.get('segment') == 'high_ltv':
        return {
            "action": "retry_payment",
            "delay_hours": 72,
            "reasoning": f"First-time failure for High-LTV customer (LTV: ${context['ltv']}). Scheduled 72h payday retry with concierge payment link."
        }
    
    # Rule 2: Repeat Insufficient Funds -> Offer billing date switch
    if code in ["insufficient_funds", "card_declined_insufficient_funds"] and context.get('is_repeat_offender'):
        return {
            "action": "send_email",
            "delay_hours": 48,
            "reasoning": f"Repeat insufficient-funds failure ({context['failed_attempts']} previous). Offering billing date switch and UPI/card update."
        }
    
    # Rule 3: Expired Card -> Send instant update link
    if code in ["card_expired", "expired_card"]:
        return {
            "action": "send_email",
            "delay_hours": 24,
            "reasoning": "Card expired. Dispatched priority payment method update link."
        }
    
    # Rule 4: Suspected Fraud / Stolen Card / Dispute -> Immediate Human Escalation
    if code in ["suspected_fraud", "stolen_card", "lost_card", "pickup_card", "fraudulent"]:
        return {
            "action": "human_handoff",
            "delay_hours": 0,
            "reasoning": f"Security risk ({code}). Immediate human escalation required."
        }
    
    # Rule 5: Free Trial Customer -> Single gentle retry
    if context.get('plan') == 'free_trial':
        return {
            "action": "retry_payment",
            "delay_hours": 4,
            "reasoning": "Free trial subscription. Scheduled 1 single gentle retry in 4 hours."
        }

    # Rule 6: Checkout Drop-Off / Cart Abandonment -> Instant 1-Click Recovery Link with personalized incentive
    if event_type in ["cart_abandoned", "checkout_drop_off"] or code in ["checkout_drop_off", "cart_abandoned", "3ds_auth_timeout", "checkout_friction"]:
        incentive = "10% VIP instant discount (Code: RECOVER10)" if (context.get('ltv', 0) > 1000 or amount >= 100) else "Free express checkout & priority link"
        return {
            "action": "send_checkout_recovery",
            "delay_hours": 1,
            "reasoning": f"Checkout dropped at payment step (Cart Value: ${amount:.2f}). Triggered instant 1-click recovery with {incentive}."
        }
    
    # Rule 7: Fallback to Google Gemini for ambiguous / rare codes
    print(f"[Orchestrator] Invoking Google Gemini for code: '{code}' (Segment: {context.get('segment')})")
    llm_result = await llm_diagnose(
        error_code=error_code,
        error_message=error_message,
        amount=amount,
        currency=currency,
        event_type=event_type,
        context=context
    )
    return llm_result


# ============================================================
# STEP 2: POLICY ENGINE & SAFETY BOUNDS
# ============================================================
def apply_policy(case_data: dict, diagnosis: dict, context: dict) -> dict:
    """Enforces dynamic max retries, customer caps, and risk guardrails."""
    current_retries = case_data.get('current_retry_count', 0)
    
    # 1. Dynamic max retry cap
    max_retries = 3
    if context.get('segment') == 'high_ltv':
        max_retries = 5
    elif context.get('plan') == 'free_trial':
        max_retries = 1
    
    # 2. Check retry bound
    if current_retries >= max_retries:
        return {
            "action": "human_handoff",
            "delay_hours": 0,
            "reasoning": f"Maximum allowed retries ({max_retries}) reached for {context.get('segment')} customer. Escalating to human team."
        }
    
    # 3. High Transaction Value Guardrail
    amount = float(case_data.get('amount_usd') or 0)
    if amount > 5000 and context.get('segment') != 'high_ltv':
        return {
            "action": "human_handoff",
            "delay_hours": 0,
            "reasoning": f"High value transaction (${amount:.2f}) from unverified customer. Escalating to human team for safety."
        }
    
    return diagnosis


# ============================================================
# STEP 3: MAIN ORCHESTRATOR (State Machine)
# ============================================================
async def process_event(event_id: str):
    """
    Processes a raw event through the complete autonomous workflow:
    Detect → Fetch Context → Diagnose → Policy Guardrails → Execute → Audit
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        
        # 1. DETECT
        event = await conn.fetchrow(
            "SELECT * FROM raw_events WHERE event_id = $1 AND is_processed = FALSE",
            event_id
        )
        if not event:
            return
        
        canonical = event['canonical_event']
        if isinstance(canonical, str):
            canonical = json.loads(canonical)
        
        customer_id = canonical.get('customer_id', 'unknown')
        amount = float(canonical.get('amount_usd') or 0)
        currency = canonical.get('currency', 'USD')
        event_type = canonical.get('event_type', 'payment_failed')
        
        print(f"\n[Orchestrator] Processing Event: {event_id} | Customer: {customer_id} | Amount: {currency} {amount}")
        
        # 2. CASE INITIALIZATION
        existing_case = await conn.fetchrow(
            "SELECT * FROM cases WHERE event_id = $1",
            event_id
        )
        
        if not existing_case:
            await conn.execute(
                """
                INSERT INTO cases (event_id, customer_id, case_type, amount_usd, status, max_retries)
                VALUES ($1, $2, $3, $4, 'diagnosing', 3)
                """,
                event_id,
                customer_id,
                event_type,
                amount
            )
        
        case = await conn.fetchrow("SELECT * FROM cases WHERE event_id = $1", event_id)
        case_id = case['case_id']
        
        # 3. FETCH CUSTOMER CONTEXT
        context = await get_customer_context(customer_id)
        
        # 4. HYBRID DIAGNOSIS
        diagnosis = await diagnose_root_case(
            error_code=canonical.get('raw_error_code'),
            error_message=canonical.get('raw_error_message'),
            amount=amount,
            currency=currency,
            event_type=event_type,
            context=context
        )
        
        # 5. POLICY GUARDRAILS
        decision = apply_policy(dict(case), diagnosis, context)
        print(f"[Orchestrator] Case #{case_id} Decision: {decision['action']} | Reasoning: {decision['reasoning']}")
        
        # 6. EXECUTION
        contact = await get_customer_contact(customer_id)
        email = contact.get('email')
        phone = contact.get('phone')
        
        new_status = "awaiting_input"
        last_action = ""
        schedule_next = None
        retry_increment = 0
        delay_hrs = decision.get("delay_hours", 24)
        
        if decision['action'] == 'retry_payment':
            # Generate smart recovery payment link
            link_res = await retry_payment(
                customer_id=customer_id,
                amount_usd=amount,
                currency=currency,
                email=email,
                phone=phone,
                case_id=case_id,
                description=f"Recovery for Case #{case_id}"
            )
            
            pay_url = link_res.get('payment_link', '')
            action_parts = []
            
            # Send Email
            if email:
                email_html = f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
                  <h2 style="color: #1a1a1a;">Payment Recovery Notification</h2>
                  <p>Dear Customer,</p>
                  <p>Your recent payment of <strong>{currency} {amount:.2f}</strong> could not be completed.</p>
                  <p style="margin: 24px 0;">
                    <a href="{pay_url}" style="background-color: #0B6E4F; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">
                      Complete Secure Payment
                    </a>
                  </p>
                  <p style="color: #666; font-size: 12px;">This secure recovery link is valid for 72 hours. If you have any questions, reply to this email.</p>
                </div>
                """
                await send_email(email, f"Action Required: Complete your payment of {currency} {amount:.2f}", email_html, pay_url, case_id, customer_id)
                action_parts.append(f"Email sent to {email}")
            
            # Send SMS
            if phone:
                sms_text = f"Payment of {currency} {amount:.2f} failed. Pay securely here: {pay_url}"
                await send_sms(phone, sms_text, case_id, customer_id)
                action_parts.append(f"SMS sent to {phone}")
            
            last_action = f"Generated {link_res.get('gateway', 'PSP')} link: {', '.join(action_parts) if action_parts else pay_url}"
            new_status = 'awaiting_input' if (email or phone) else 'retrying'
            schedule_next = datetime.utcnow() + timedelta(hours=delay_hrs)
            retry_increment = 1
            
        elif decision['action'] == 'send_checkout_recovery':
            # Generate 1-click checkout recovery link
            link_res = await retry_payment(
                customer_id=customer_id,
                amount_usd=amount,
                currency=currency,
                email=email,
                phone=phone,
                case_id=case_id,
                description=f"Checkout Recovery for Case #{case_id}"
            )
            pay_url = link_res.get('payment_link', '')
            action_parts = []
            
            has_discount = "RECOVER10" in decision.get('reasoning', '')
            discount_badge = '<div style="background:#E6F4EA;color:#137333;padding:8px 12px;border-radius:4px;font-weight:bold;margin:12px 0;">🎉 Applied Promo Code: RECOVER10 (10% Instant Off)</div>' if has_discount else ''
            
            if email:
                email_html = f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e0e0e0; border-radius: 8px;">
                  <h2 style="color: #1a1a1a; margin-top:0;">You left items in your cart!</h2>
                  <p>Hi there, we noticed you started checkout for <strong>{currency} {amount:.2f}</strong> but didn't finish.</p>
                  {discount_badge}
                  <p style="margin: 24px 0;">
                    <a href="{pay_url}" style="background-color: #0B6E4F; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                      Complete 1-Click Checkout
                    </a>
                  </p>
                  <p style="color: #666; font-size: 12px;">Your reserved cart and preferred items are saved for the next 24 hours.</p>
                </div>
                """
                await send_email(email, f"🛒 Complete your order of {currency} {amount:.2f} (Saved for you)", email_html, pay_url, case_id, customer_id)
                action_parts.append(f"Cart Recovery Email sent to {email}")
            
            if phone:
                sms_text = f"You left items in your cart ({currency} {amount:.2f})! Complete checkout in 1 tap: {pay_url}"
                await send_sms(phone, sms_text, case_id, customer_id)
                action_parts.append(f"Cart Recovery SMS sent to {phone}")
                
            last_action = f"Dispatched 1-Click Checkout Recovery: {', '.join(action_parts) if action_parts else pay_url}"
            new_status = 'awaiting_input'
            schedule_next = datetime.utcnow() + timedelta(hours=delay_hrs)
            retry_increment = 1

        elif decision['action'] == 'send_email':
            if email:
                html = f"""
                <p>Dear Customer,</p>
                <p>We noticed an issue processing your subscription payment of {currency} {amount:.2f}.</p>
                <p>Please update your default payment method or choose a different billing date to avoid service disruption.</p>
                <p>Thank you,<br>Accounts Team</p>
                """
                await send_email(email, "Important: Please update your payment method", html, None, case_id, customer_id)
                last_action = f"Sent payment update email to {email}"
                new_status = 'awaiting_input'
                schedule_next = datetime.utcnow() + timedelta(hours=delay_hrs)
            else:
                decision['action'] = 'human_handoff'
                
        elif decision['action'] == 'send_sms':
            if phone:
                await send_sms(phone, f"Action needed: Please update payment method for your account. Amount due: {currency} {amount:.2f}", case_id, customer_id)
                last_action = f"Sent SMS alert to {phone}"
                new_status = 'awaiting_input'
                schedule_next = datetime.utcnow() + timedelta(hours=delay_hrs)
            else:
                decision['action'] = 'human_handoff'
        
        if decision['action'] == 'human_handoff':
            await escalate_to_human(
                customer_id=customer_id,
                reason=decision.get('reasoning', 'Autonomous bounds exceeded.'),
                case_id=case_id,
                amount=amount,
                segment=context.get('segment', 'standard')
            )
            last_action = "Escalated to human operations team via Slack."
            new_status = 'escalated'
            schedule_next = None
        
        # 7. AUDIT & UPDATE CASE
        await conn.execute(
            """
            UPDATE cases 
            SET status = $1, 
                last_action = $2, 
                scheduled_next_action_at = $3,
                current_retry_count = current_retry_count + $4,
                llm_reasoning = $5,
                updated_at = NOW()
            WHERE case_id = $6
            """,
            new_status,
            last_action,
            schedule_next,
            retry_increment,
            decision.get('reasoning', ''),
            case_id
        )
        
        # 8. MARK RAW EVENT PROCESSED
        await conn.execute("UPDATE raw_events SET is_processed = TRUE WHERE event_id = $1", event_id)
        print(f"[Orchestrator] Case #{case_id} updated. Status: {new_status}\n")


# ============================================================
# STEP 4: AUTO-RESOLVE LOOP (Inbound Payment Success)
# ============================================================
async def resolve_case(
    customer_id: str,
    amount_recovered: float,
    payment_reference: str = "PSP_Webhook",
    case_id: int | None = None
) -> dict:
    """
    Handles inbound payment success events from Stripe or Razorpay.
    Closes the loop: transitions case to 'resolved', stops future retries, logs recovery.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        target_case = None
        
        if case_id:
            target_case = await conn.fetchrow("SELECT * FROM cases WHERE case_id = $1", case_id)
        elif customer_id:
            # Find latest open case for this customer
            target_case = await conn.fetchrow("""
                SELECT * FROM cases 
                WHERE customer_id = $1 
                  AND status IN ('new', 'diagnosing', 'retrying', 'awaiting_input', 'escalated')
                ORDER BY updated_at DESC LIMIT 1
            """, customer_id)
        
        if not target_case:
            print(f"[Orchestrator] No active open case found to resolve for customer: {customer_id}")
            return {"success": False, "reason": "No open case found"}
        
        cid = target_case['case_id']
        actual_cust = target_case['customer_id']
        
        await conn.execute("""
            UPDATE cases 
            SET status = 'resolved',
                last_action = $1,
                scheduled_next_action_at = NULL,
                updated_at = NOW()
            WHERE case_id = $2
        """, f"Payment verified via {payment_reference}", cid)
        
        # Log to action_logs
        await log_action(
            case_id=cid,
            customer_id=actual_cust,
            action_type="case_resolved",
            channel="payment_gateway",
            recipient=actual_cust,
            payload={"amount_recovered": amount_recovered, "reference": payment_reference},
            status="success",
            details=f"Case #{cid} marked as RESOLVED. Recovered: ${amount_recovered:.2f}"
        )
        
        # Notify team in Slack
        await notify_recovery_success(actual_cust, cid, amount_recovered, payment_reference)
        print(f"[Orchestrator] Case #{cid} successfully RESOLVED. Amount: ${amount_recovered:.2f}")
        return {"success": True, "case_id": cid, "recovered_amount": amount_recovered}


# ============================================================
# STEP 5: BACKGROUND SCHEDULED POLLERS
# ============================================================
async def process_pending_events():
    """Worker: Picks up fresh unprocessed raw events and triggers the orchestrator."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        events = await conn.fetch(
            "SELECT event_id FROM raw_events WHERE is_processed = FALSE ORDER BY ingested_at ASC LIMIT 10"
        )
        for event in events:
            try:
                await process_event(event['event_id'])
            except Exception as e:
                print(f"[Orchestrator] Error processing pending event {event['event_id']}: {e}")


async def process_scheduled_cases():
    """Worker: Re-evaluates cases due for scheduled follow-up / retry."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        cases = await conn.fetch("""
            SELECT case_id, event_id, customer_id, current_retry_count, max_retries, amount_usd 
            FROM cases 
            WHERE status IN ('retrying', 'awaiting_input') 
              AND scheduled_next_action_at IS NOT NULL 
              AND scheduled_next_action_at <= NOW()
            LIMIT 10
        """)
        
        for case in cases:
            case_id = case['case_id']
            print(f"[Poller] Case #{case_id} reached scheduled retry time.")
            
            # If retries exceeded, escalate
            if case['current_retry_count'] >= case['max_retries']:
                await conn.execute("""
                    UPDATE cases 
                    SET status = 'escalated',
                        last_action = 'Max scheduled retries reached. Escalated to human team.',
                        scheduled_next_action_at = NULL,
                        updated_at = NOW()
                    WHERE case_id = $1
                """, case_id)
                await escalate_to_human(case['customer_id'], "Max scheduled retries exceeded.", case_id, float(case['amount_usd'] or 0))
            else:
                # Reset raw_event to re-evaluate with current context
                await conn.execute("UPDATE raw_events SET is_processed = FALSE WHERE event_id = $1", case['event_id'])
                await process_event(case['event_id'])
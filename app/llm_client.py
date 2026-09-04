# app/llm_client.py
import os
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
model = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Try prioritized modern Gemini models (Gemini 3.7 / 3.6 / 3.5 Flash)
        for model_name in ['gemini-3.7-flash', 'gemini-3.6-flash', 'gemini-3.5-flash', 'gemini-flash-latest']:
            try:
                model = genai.GenerativeModel(model_name)
                print(f"[LLM] Configured Google Gemini model: '{model_name}'")
                break
            except Exception:
                continue
    except Exception as e:
        print(f"[LLM] Initialization warning: {e}")
else:
    print("[LLM] WARNING: GEMINI_API_KEY not set. Operating in intelligent rules-fallback mode.")


VALID_CAUSES = [
    "BANK_DECLINE",
    "NETWORK_TIMEOUT",
    "INSUFFICIENT_FUNDS",
    "CARD_EXPIRED",
    "FRAUD_FLAG",
    "CHECKOUT_ABANDONED",
    "SUBSCRIPTION_FAILED",
    "OVERDUE_INVOICE",
    "UNKNOWN",
]

async def llm_diagnose(
    error_code: str | None, 
    error_message: str | None, 
    amount: float, 
    currency: str = "INR",
    event_type: str = "payment_failed",
    context: dict = None
) -> dict:
    """
    Calls Google Gemini to diagnose payment failures, classify root cause across
    8 Indian BFSI categories, and craft personalized Hinglish/English recovery copy.
    """
    ctx = context or {}
    code_str = str(error_code or "").lower()
    
    # Fast heuristic root cause determination if LLM is unavailable
    fallback_cause = "UNKNOWN"
    if "timeout" in code_str or "gateway" in code_str:
        fallback_cause = "NETWORK_TIMEOUT"
    elif "insufficient" in code_str or "balance" in code_str:
        fallback_cause = "INSUFFICIENT_FUNDS"
    elif "expired" in code_str:
        fallback_cause = "CARD_EXPIRED"
    elif "fraud" in code_str or "suspicious" in code_str:
        fallback_cause = "FRAUD_FLAG"
    elif "abandon" in code_str or "drop" in code_str or event_type == "checkout_drop_off":
        fallback_cause = "CHECKOUT_ABANDONED"
    elif "mandate" in code_str or "subscri" in code_str:
        fallback_cause = "SUBSCRIPTION_FAILED"
    elif "invoice" in code_str or "overdue" in code_str:
        fallback_cause = "OVERDUE_INVOICE"
    elif "decline" in code_str or "do_not_honor" in code_str:
        fallback_cause = "BANK_DECLINE"

    if not model or not GEMINI_API_KEY:
        is_fraud = fallback_cause == "FRAUD_FLAG"
        action = "human_handoff" if is_fraud else ("retry_payment" if ctx.get("is_first_failure") else "send_email")
        return {
            "root_cause": fallback_cause,
            "confidence": 0.85,
            "action": action,
            "delay_hours": 0 if is_fraud else 24,
            "reasoning": f"Rules Heuristic: Root cause classified as {fallback_cause}. Action bounded by compliance policy.",
            "customer_message": "Namaste! Aapka payment process nahi ho paya. Kripya is secure link se transaction complete karein."
        }

    prompt = f"""
You are an expert Autonomous AI Revenue Recovery Agent for the Razorpay AI Buildathon (Track 03).

Classify this payment failure into exactly ONE root cause from this list:
{VALID_CAUSES}

--- TRANSACTION & CUSTOMER CONTEXT ---
- Amount: {currency} {amount:,.2f}
- Error Code: {error_code or 'UNKNOWN'}
- Error Description: {error_message or 'No gateway explanation provided'}
- Customer ID: {ctx.get('customer_id', 'unknown')}
- Segment: {ctx.get('segment', 'standard')} (high_ltv, standard, trial, enterprise)
- Customer LTV: ₹{ctx.get('ltv', 0):,.2f}
- Plan: {ctx.get('plan', 'monthly')}
- Total Attempts: {ctx.get('total_attempts', 0)}
- Prior Failures: {ctx.get('failed_attempts', 0)}

--- COMPLIANCE & RECOVERY POLICY RULES ---
1. "FRAUD_FLAG": Strict Zero-Auto-Retry policy. Always action="human_handoff", delay_hours=0.
2. "NETWORK_TIMEOUT": Immediate retry or alternate rail (action="retry_payment", delay_hours=0).
3. "BANK_DECLINE": Delayed retry with 2-hour backoff window (action="retry_payment", delay_hours=2).
4. "INSUFFICIENT_FUNDS": Payment link via SMS/Email (action="send_email" or "send_sms", delay_hours=24).
5. "CARD_EXPIRED": Request payment method update (action="send_email", delay_hours=24).
6. "CHECKOUT_ABANDONED": 1-click cart hold recovery link (action="send_checkout_recovery", delay_hours=1).
7. "SUBSCRIPTION_FAILED": Mandate swap link (action="send_email", delay_hours=24).
8. "OVERDUE_INVOICE": B2B progressive dunning with 7-day grace period (action="send_email", delay_hours=168).

Respond ONLY with a valid JSON object:
{{
  "root_cause": "<ONE_OF_THE_8_CAUSES>",
  "confidence": <0.0-1.0>,
  "action": "retry_payment" | "send_email" | "send_sms" | "human_handoff" | "send_checkout_recovery",
  "delay_hours": <integer>,
  "reasoning": "<concise explanation of technical root cause and policy bound>",
  "customer_message": "<polite, high-converting 1-2 sentence recovery copy tailored for an Indian customer in natural conversational Hinglish or professional English>"
}}
"""

    try:
        def _call_gemini():
            response = model.generate_content(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2
                }
            )
            return response.text

        raw_text = await asyncio.to_thread(_call_gemini)
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        parsed = json.loads(cleaned.strip())
        
        root_cause = parsed.get("root_cause", fallback_cause)
        if root_cause not in VALID_CAUSES:
            root_cause = fallback_cause
            
        action = parsed.get("action", "retry_payment")
        if root_cause == "FRAUD_FLAG":
            action = "human_handoff"
            parsed["delay_hours"] = 0
            
        return {
            "root_cause": root_cause,
            "confidence": float(parsed.get("confidence", 0.9)),
            "action": action,
            "delay_hours": int(parsed.get("delay_hours", 24)),
            "reasoning": parsed.get("reasoning", f"Root cause: {root_cause}."),
            "customer_message": parsed.get("customer_message", "Namaste! Please complete your transaction using this secure link.")
        }
        
    except Exception as e:
        print(f"[LLM] Gemini generation error: {e}")
        is_fraud = fallback_cause == "FRAUD_FLAG"
        action = "human_handoff" if is_fraud else "retry_payment"
        return {
            "root_cause": fallback_cause,
            "confidence": 0.7,
            "action": action,
            "delay_hours": 0 if is_fraud else 24,
            "reasoning": f"Heuristic classification due to LLM timeout ({e}).",
            "customer_message": "Namaste! Please complete your pending transaction using this secure link."
        }


def get_heuristic_classification(error_code: str | None, error_message: str | None, event_type: str = "payment_failed") -> dict:
    code_str = (str(error_code or "") + " " + str(error_message or "")).lower()
    fallback_cause = "UNKNOWN"
    if "timeout" in code_str or "gateway" in code_str or "network" in code_str:
        fallback_cause = "NETWORK_TIMEOUT"
    elif "insufficient" in code_str or "balance" in code_str:
        fallback_cause = "INSUFFICIENT_FUNDS"
    elif "expired" in code_str:
        fallback_cause = "CARD_EXPIRED"
    elif "fraud" in code_str or "suspicious" in code_str or "risk" in code_str:
        fallback_cause = "FRAUD_FLAG"
    elif "abandon" in code_str or "drop" in code_str or event_type == "checkout_drop_off":
        fallback_cause = "CHECKOUT_ABANDONED"
    elif "mandate" in code_str or "subscri" in code_str or "renewal" in code_str:
        fallback_cause = "SUBSCRIPTION_FAILED"
    elif "invoice" in code_str or "overdue" in code_str:
        fallback_cause = "OVERDUE_INVOICE"
    elif "decline" in code_str or "do_not_honor" in code_str or "bad_request" in code_str:
        fallback_cause = "BANK_DECLINE"

    is_fraud = fallback_cause == "FRAUD_FLAG"
    action = "human_handoff" if is_fraud else "retry_payment"
    return {
        "root_cause": fallback_cause,
        "confidence": 0.85,
        "action": action,
        "delay_hours": 0 if is_fraud else 24,
        "reasoning": f"Heuristic: {fallback_cause}",
        "recovery_message": "Namaste! Please complete your pending payment using this secure link.",
    }


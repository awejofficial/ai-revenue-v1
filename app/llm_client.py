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


async def llm_diagnose(
    error_code: str | None, 
    error_message: str | None, 
    amount: float, 
    currency: str = "USD",
    event_type: str = "payment_failed",
    context: dict = None
) -> dict:
    """
    Calls Google Gemini to diagnose ambiguous or rare payment failure codes,
    incorporating customer LTV, tenure, historical churn risk, and billing cycles.
    """
    ctx = context or {}
    
    if not model or not GEMINI_API_KEY:
        return {
            "action": "retry_payment" if ctx.get("is_first_failure") else "send_email",
            "delay_hours": 24,
            "reasoning": f"Rules Fallback (No LLM key): First failure={ctx.get('is_first_failure', True)}, Segment={ctx.get('segment', 'standard')}. Scheduled 24h recovery."
        }

    prompt = f"""
You are an expert Autonomous AI Revenue Recovery & Intelligent Dunning Agent for SaaS & E-Commerce companies.

--- CUSTOMER PROFILE & CONTEXT ---
- Customer ID: {ctx.get('customer_id', 'unknown')}
- Segment: {ctx.get('segment', 'standard')} (Options: high_ltv, standard, trial, enterprise)
- Customer Lifetime Value (LTV): ${ctx.get('ltv', 0)}
- Subscription Plan: {ctx.get('plan', 'monthly')}
- Total Prior Attempts (Last 90d): {ctx.get('total_attempts', 0)}
- Past Failures: {ctx.get('failed_attempts', 0)}
- Is First Failure: {"Yes" if ctx.get('is_first_failure') else "No"}
- Is Repeat Offender: {"Yes" if ctx.get('is_repeat_offender') else "No"}

--- PAYMENT FAILURE DETAILS ---
- Event Type: {event_type}
- Amount: {currency} {amount:.2f}
- Error Code: {error_code or 'UNKNOWN_DECLINE'}
- Error Message: {error_message or 'No gateway explanation provided'}

--- AVAILABLE ACTIONS ---
1. "retry_payment" -> Automatic gateway retry after delay (specify delay_hours, e.g. 24, 48, 72).
2. "send_email" -> Send customer personalized recovery email with payment update link.
3. "send_sms" -> Send quick SMS alert with secure payment link.
4. "human_handoff" -> Escalate to human operations/account team via Slack.

--- DECISION GUIDELINES ---
- High-LTV ($5000+): Prioritize white-glove retention. Never aggressively spam. Align retries with salary/paydays (72h) or priority outreach.
- Repeat Insufficient Funds (2+ times): Avoid blind retries. Ask customer to switch billing date or choose UPI/alternate card.
- Hard Declines (stolen card, closed account, suspected fraud): Instant "human_handoff" (0 delay).
- Soft Technical Declines (network timeout, bank server down): Short retry (2-6 hours).
- Free Trial: 1 single gentle retry, no aggressive dunning.

Respond ONLY with a valid JSON object in the following format:
{{
  "action": "retry_payment" | "send_email" | "send_sms" | "human_handoff",
  "delay_hours": <integer_hours>,
  "reasoning": "<clear concise explanation citing customer context and failure reason>"
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
        
        # Clean any markdown code fences if returned
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        parsed = json.loads(cleaned.strip())
        
        action = parsed.get("action", "retry_payment")
        if action not in ["retry_payment", "send_email", "send_sms", "human_handoff"]:
            action = "retry_payment"
            
        return {
            "action": action,
            "delay_hours": int(parsed.get("delay_hours", 24)),
            "reasoning": parsed.get("reasoning", "Gemini evaluated customer profile and error diagnostics.")
        }
        
    except Exception as e:
        print(f"[LLM] Gemini generation failed: {e}")
        # Safe fallback
        fallback_action = "human_handoff" if "fraud" in str(error_code).lower() else "retry_payment"
        return {
            "action": fallback_action,
            "delay_hours": 24 if fallback_action == "retry_payment" else 0,
            "reasoning": f"LLM Fallback due to API error ({str(e)}). Defaulted to {fallback_action}."
        }

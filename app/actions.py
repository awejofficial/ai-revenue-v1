# app/actions.py
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
PREFERRED_PSP = os.getenv("PREFERRED_PSP", "stripe").lower()

# --- Initialize Stripe ---
import stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

# --- Initialize Razorpay ---
razorpay_client = None
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    try:
        import razorpay
        razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception as e:
        print(f"[Actions] Razorpay client initialization error: {e}")

# --- Initialize Twilio ---
twilio_client = None
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        from twilio.rest import Client
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        print(f"[Actions] Twilio client initialization error: {e}")

# --- Initialize SendGrid ---
sendgrid_client = None
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
if SENDGRID_API_KEY:
    try:
        from sendgrid import SendGridAPIClient
        sendgrid_client = SendGridAPIClient(SENDGRID_API_KEY)
    except Exception as e:
        print(f"[Actions] SendGrid client initialization error: {e}")

# --- Initialize Slack ---
slack_client = None
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
if SLACK_WEBHOOK_URL:
    try:
        from slack_sdk.webhook import WebhookClient
        slack_client = WebhookClient(SLACK_WEBHOOK_URL)
    except Exception as e:
        print(f"[Actions] Slack client initialization error: {e}")


# ============================================================
# ACTION LOGGER (Database Audit)
# ============================================================
async def log_action(
    case_id: int | None,
    customer_id: str,
    action_type: str,
    channel: str,
    recipient: str | None = None,
    payload: dict | None = None,
    status: str = "sent",
    details: str | None = None
):
    """Records an executed action into the action_logs table."""
    try:
        from app.db import get_pool
        pool = await get_pool()
        payload_json = json.dumps(payload) if isinstance(payload, (dict, list)) else (payload or "{}")
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO action_logs (case_id, customer_id, action_type, channel, recipient, payload, status, details)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                case_id,
                customer_id,
                action_type,
                channel,
                recipient,
                payload_json,
                status,
                details
            )
    except Exception as e:
        print(f"[ActionLog] Failed to log action: {e}")


# ============================================================
# 1. PAYMENT LINKS & RETRY (Razorpay + Stripe)
# ============================================================

async def create_razorpay_payment_link(
    customer_id: str,
    amount: float,
    currency: str = "INR",
    email: str = None,
    phone: str = None,
    case_id: int = None,
    description: str = None
) -> dict:
    """Generate a Razorpay Payment Link supporting Cards, NetBanking, and UPI."""
    print(f"[ACTION][Razorpay] Generating payment link for {customer_id} ({currency} {amount})")

    if DRY_RUN or not razorpay_client:
        mock_link = f"https://rzp.io/i/mock_case_{case_id or customer_id}"
        print(f"   [DRY RUN / Mock] Razorpay Payment Link: {mock_link}")
        await log_action(case_id, customer_id, "payment_link_created", "razorpay", email or phone, {"mock": True, "url": mock_link}, "success", "Mock Razorpay link generated")
        return {"success": True, "gateway": "razorpay", "payment_link": mock_link, "dry_run": True}

    try:
        # Razorpay amount is in paise (1 INR = 100 paise)
        amount_paise = int(round(amount * 100))
        customer_payload = {"name": customer_id}
        if email:
            customer_payload["email"] = email
        if phone:
            customer_payload["contact"] = phone

        payload = {
            "amount": amount_paise,
            "currency": currency.upper(),
            "accept_partial": False,
            "description": description or f"Revenue Recovery for Case #{case_id or customer_id}",
            "customer": customer_payload,
            "notify": {"sms": bool(phone), "email": bool(email)},
            "reminder_enable": True,
            "notes": {
                "case_id": str(case_id or ""),
                "customer_id": str(customer_id),
                "recovered_by": "ai_revenue_recovery_agent"
            }
        }

        # Run synchronous SDK call in thread
        link_response = await asyncio.to_thread(razorpay_client.payment_link.create, payload)
        short_url = link_response.get("short_url") or link_response.get("url")
        link_id = link_response.get("id")
        print(f"   [Razorpay] Payment link created: {short_url} (ID: {link_id})")

        await log_action(case_id, customer_id, "payment_link_created", "razorpay", email or phone, link_response, "success", f"Live Razorpay Link: {short_url}")
        return {"success": True, "gateway": "razorpay", "payment_link": short_url, "link_id": link_id}

    except Exception as e:
        print(f"   [Razorpay] Error generating payment link: {e}")
        await log_action(case_id, customer_id, "payment_link_failed", "razorpay", email or phone, {"error": str(e)}, "failed", str(e))
        return {"success": False, "gateway": "razorpay", "error": str(e)}


async def retry_payment(
    customer_id: str,
    amount_usd: float,
    currency: str = "usd",
    metadata: dict = None,
    email: str = None,
    phone: str = None,
    case_id: int = None,
    description: str = None
) -> dict:
    """Unified payment retry / payment link generator supporting Stripe and Razorpay."""
    # Route based on currency or preferred gateway
    if currency.lower() in ["inr", "rs"] or PREFERRED_PSP == "razorpay":
        return await create_razorpay_payment_link(
            customer_id=customer_id,
            amount=amount_usd,
            currency=currency.upper() if currency else "INR",
            email=email,
            phone=phone,
            case_id=case_id,
            description=description
        )

    print(f"[ACTION][Stripe] Generating payment link for {customer_id} (${amount_usd})")
    
    if DRY_RUN or not stripe.api_key:
        mock_link = f"https://checkout.stripe.com/pay/test_case_{case_id or customer_id}"
        print(f"   [DRY RUN / Mock] Stripe Payment Link: {mock_link}")
        await log_action(case_id, customer_id, "payment_link_created", "stripe", email or phone, {"mock": True, "url": mock_link}, "success", "Mock Stripe link generated")
        return {"success": True, "gateway": "stripe", "payment_link": mock_link, "dry_run": True}
    
    try:
        amount_cents = int(round(amount_usd * 100))
        meta = metadata or {}
        meta["case_id"] = str(case_id or "")
        meta["customer_id"] = str(customer_id)

        intent = await asyncio.to_thread(
            stripe.PaymentIntent.create,
            amount=amount_cents,
            currency=currency.lower(),
            customer=customer_id if customer_id.startswith("cus_") else None,
            description=description or f"Revenue Recovery for Case #{case_id}",
            metadata=meta
        )
        pay_url = f"https://checkout.stripe.com/pay/{intent.id}"
        print(f"   [Stripe] PaymentIntent created: {intent.id}")
        await log_action(case_id, customer_id, "payment_link_created", "stripe", email or phone, {"intent_id": intent.id}, "success", pay_url)
        return {"success": True, "gateway": "stripe", "payment_intent_id": intent.id, "status": intent.status, "payment_link": pay_url}
    except Exception as e:
        print(f"   [Stripe] Error: {e}")
        await log_action(case_id, customer_id, "payment_link_failed", "stripe", email or phone, {"error": str(e)}, "failed", str(e))
        return {"success": False, "gateway": "stripe", "error": str(e)}


# ============================================================
# 2. EMAIL (SendGrid)
# ============================================================
async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    payment_link: str = None,
    case_id: int = None,
    customer_id: str = "unknown"
) -> dict:
    """Dispatches a recovery email via SendGrid with payment link integration."""
    if payment_link and "{{PAYMENT_LINK}}" in html_content:
        html_content = html_content.replace("{{PAYMENT_LINK}}", payment_link)
    
    print(f"[ACTION][Email] Sending email to {to_email} - Subject: {subject}")
    
    sender_email = os.getenv("FROM_EMAIL", os.getenv("SENDGRID_FROM_EMAIL", "recovery@oxalpha.io"))

    if DRY_RUN or not sendgrid_client:
        print(f"   [DRY RUN] Would send email from <{sender_email}> to <{to_email}> with link: {payment_link}")
        await log_action(case_id, customer_id, "email_sent", "sendgrid", to_email, {"subject": subject, "mock": True}, "success", "Mock email dispatched")
        return {"success": True, "dry_run": True}
    
    try:
        from sendgrid.helpers.mail import Mail
        message = Mail(
            from_email=sender_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        response = await asyncio.to_thread(sendgrid_client.send, message)
        success = response.status_code in [200, 201, 202]
        print(f"   [SendGrid] Email status: {response.status_code}")
        await log_action(case_id, customer_id, "email_sent", "sendgrid", to_email, {"status_code": response.status_code}, "success" if success else "failed")
        return {"success": success, "status_code": response.status_code}
    except Exception as e:
        print(f"   [SendGrid] Email error: {e}")
        await log_action(case_id, customer_id, "email_failed", "sendgrid", to_email, {"error": str(e)}, "failed", str(e))
        return {"success": False, "error": str(e)}


# ============================================================
# 3. SMS (Twilio)
# ============================================================
async def send_sms(
    to_phone: str,
    message: str,
    case_id: int = None,
    customer_id: str = "unknown"
) -> dict:
    """Dispatches an SMS notification via Twilio."""
    print(f"[ACTION][SMS] Sending SMS to {to_phone}")
    
    if DRY_RUN or not twilio_client:
        print(f"   [DRY RUN] Would send SMS to {to_phone}: {message[:80]}...")
        await log_action(case_id, customer_id, "sms_sent", "twilio", to_phone, {"message": message, "mock": True}, "success", "Mock SMS sent")
        return {"success": True, "dry_run": True}
    
    try:
        twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
        msg_obj = await asyncio.to_thread(
            twilio_client.messages.create,
            body=message,
            from_=twilio_phone,
            to=to_phone
        )
        print(f"   [Twilio] SMS sent. SID: {msg_obj.sid}")
        await log_action(case_id, customer_id, "sms_sent", "twilio", to_phone, {"sid": msg_obj.sid}, "success")
        return {"success": True, "sid": msg_obj.sid}
    except Exception as e:
        print(f"   [Twilio] SMS error: {e}")
        await log_action(case_id, customer_id, "sms_failed", "twilio", to_phone, {"error": str(e)}, "failed", str(e))
        return {"success": False, "error": str(e)}


# ============================================================
# 4. SLACK (Human Escalation & Celebration Notifications)
# ============================================================
async def escalate_to_human(
    customer_id: str,
    reason: str,
    case_id: int,
    amount: float = 0.0,
    segment: str = "standard"
) -> dict:
    """Alerts operations and account managers in Slack for human intervention."""
    print(f"[ACTION][Slack] Escalating Case #{case_id} ({customer_id}) to human team.")
    
    text = (
        f"🚨 *Revenue Recovery Escalation*\n"
        f"• *Customer:* `{customer_id}` ({segment.upper()} segment)\n"
        f"• *Case ID:* `#{case_id}`\n"
        f"• *Amount at Risk:* `${amount:.2f}`\n"
        f"• *Reason:* {reason}\n"
        f"👉 *Action Required:* Please review case in dashboard and contact the customer directly."
    )
    
    if DRY_RUN or not slack_client:
        print(f"   [DRY RUN] Would send Slack alert: {reason}")
        await log_action(case_id, customer_id, "escalated_to_slack", "slack", "ops_channel", {"reason": reason, "mock": True}, "success", "Mock Slack escalation")
        return {"success": True, "dry_run": True}
    
    try:
        response = await asyncio.to_thread(slack_client.send, text=text)
        success = response.status_code == 200
        print(f"   [Slack] Escalation sent. Status: {response.status_code}")
        await log_action(case_id, customer_id, "escalated_to_slack", "slack", "ops_channel", {"status_code": response.status_code}, "success" if success else "failed")
        return {"success": success}
    except Exception as e:
        print(f"   [Slack] Error: {e}")
        await log_action(case_id, customer_id, "slack_failed", "slack", "ops_channel", {"error": str(e)}, "failed", str(e))
        return {"success": False, "error": str(e)}


async def notify_recovery_success(
    customer_id: str,
    case_id: int,
    amount: float,
    payment_reference: str = None
) -> dict:
    """Broadcasts a successful revenue recovery celebration to the team."""
    print(f"[ACTION][Slack] Broadcasting recovery celebration for Case #{case_id} (${amount})")
    
    text = (
        f"🎉 *Revenue Recovered!* 🎉\n"
        f"• *Customer:* `{customer_id}`\n"
        f"• *Case ID:* `#{case_id}`\n"
        f"• *Recovered Amount:* *${amount:.2f}*\n"
        f"• *Reference:* `{payment_reference or 'N/A'}`\n"
        f"✅ Case marked as RESOLVED by AI Revenue Recovery Agent."
    )
    
    if DRY_RUN or not slack_client:
        print(f"   [DRY RUN] Would send Slack recovery celebration: ${amount}")
        return {"success": True, "dry_run": True}
    
    try:
        response = await asyncio.to_thread(slack_client.send, text=text)
        return {"success": response.status_code == 200}
    except Exception as e:
        print(f"   [Slack] Celebration send error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# HELPER: CUSTOMER LOOKUP
# ============================================================
async def get_customer_contact(customer_id: str) -> dict:
    """Fetches customer email, phone, and CRM profile from the database."""
    from app.db import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT email, phone, crm_data FROM customers WHERE customer_id = $1",
            customer_id
        )
        if row:
            crm = row['crm_data']
            if isinstance(crm, str):
                try:
                    crm = json.loads(crm)
                except Exception:
                    crm = {}
            return {
                "email": row['email'],
                "phone": row['phone'],
                "crm_data": crm or {}
            }
    return {"email": None, "phone": None, "crm_data": {}}
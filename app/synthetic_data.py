# app/synthetic_data.py
"""
Synthetic Batch Generator for Razorpay AI Buildathon (Track 03: AI Revenue Recovery)
Generates realistic Indian BFSI transactions across 8 distinct failure scenarios.
"""

import random
import uuid
from datetime import datetime, timezone

INDIAN_FIRST_NAMES = [
    "Aarav", "Priya", "Rahul", "Ananya", "Rohan", "Sneha", "Vikram", "Neha",
    "Aditya", "Pooja", "Arjun", "Kavita", "Siddharth", "Meera", "Karan", "Divya",
    "Rajesh", "Sunita", "Amit", "Ritu", "Deepak", "Swati", "Nikhil", "Shreya"
]

INDIAN_LAST_NAMES = [
    "Sharma", "Verma", "Sen", "Patel", "Gupta", "Reddy", "Iyer", "Nair",
    "Mukherjee", "Singh", "Joshi", "Bose", "Mehta", "Chopra", "Kulkarni", "Deshmukh"
]

CITIES = ["Mumbai", "Bengaluru", "Delhi NCR", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad"]

ERROR_SCENARIOS = [
    {
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Your payment has been declined by the bank.",
        "root_cause": "BANK_DECLINE",
        "weight": 24,
    },
    {
        "error_code": "GATEWAY_ERROR",
        "error_description": "Network timeout while processing payment with issuer bank switch.",
        "root_cause": "NETWORK_TIMEOUT",
        "weight": 18,
    },
    {
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Insufficient funds in customer account for debit attempt.",
        "root_cause": "INSUFFICIENT_FUNDS",
        "weight": 14,
    },
    {
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Card on file has expired.",
        "root_cause": "CARD_EXPIRED",
        "weight": 8,
    },
    {
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Payment flagged for suspicious velocity / proxy IP activity.",
        "root_cause": "FRAUD_FLAG",
        "weight": 4,
    },
    {
        "error_code": "CHECKOUT_ABANDONED",
        "error_description": "Customer reached checkout but dropped off at 2FA / OTP step.",
        "root_cause": "CHECKOUT_ABANDONED",
        "weight": 12,
    },
    {
        "error_code": "SUBSCRIPTION_ERROR",
        "error_description": "Auto-debit mandate failed; recurring renewal debit rejected by NPCI rail.",
        "root_cause": "SUBSCRIPTION_FAILED",
        "weight": 9,
    },
    {
        "error_code": "INVOICE_OVERDUE",
        "error_description": "Invoice overdue by 14+ days. Outstanding enterprise B2B balance for services.",
        "root_cause": "OVERDUE_INVOICE",
        "weight": 6,
    },
    {
        "error_code": "SERVER_ERROR",
        "error_description": "An unexpected gateway error occurred during processing.",
        "root_cause": "UNKNOWN",
        "weight": 5,
    },
]

def generate_indian_customer():
    first = random.choice(INDIAN_FIRST_NAMES)
    last = random.choice(INDIAN_LAST_NAMES)
    city = random.choice(CITIES)
    name = f"{first} {last}"
    email = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@gmail.com"
    phone = f"+9198{random.randint(10000000, 99999999)}"
    return name, email, phone, city

def generate_batch(count: int = 60) -> list[dict]:
    """Generates a batch of failed payment scenarios for autonomous recovery testing."""
    weights = [s["weight"] for s in ERROR_SCENARIOS]
    payments = []
    
    for i in range(count):
        scenario = random.choices(ERROR_SCENARIOS, weights=weights, k=1)[0]
        name, email, phone, city = generate_indian_customer()
        
        # Invoices have higher ticket size
        if scenario["root_cause"] == "OVERDUE_INVOICE":
            amount = round(random.uniform(15000, 125000), 2)
            plan = "enterprise"
            segment = "high_ltv"
            ltv = round(random.uniform(75000, 500000), 2)
        elif scenario["root_cause"] == "SUBSCRIPTION_FAILED":
            amount = round(random.choice([999, 1499, 2999, 4999, 9999]), 2)
            plan = "annual"
            segment = "standard"
            ltv = amount * random.randint(2, 6)
        elif scenario["root_cause"] == "CHECKOUT_ABANDONED":
            amount = round(random.uniform(499, 8500), 2)
            plan = "ecommerce"
            segment = "trial" if random.random() < 0.5 else "standard"
            ltv = round(random.uniform(1000, 15000), 2)
        else:
            amount = round(random.uniform(250, 45000), 2)
            segment = "high_ltv" if amount > 15000 else ("standard" if random.random() < 0.7 else "trial")
            plan = "monthly"
            ltv = round(random.uniform(2000, 50000), 2)

        unique_suffix = uuid.uuid4().hex[:12]
        payments.append({
            "id": f"pay_{unique_suffix}",
            "order_id": f"order_{unique_suffix[:8]}",
            "merchant_id": f"merchant_{random.randint(1, 10):03d}",
            "customer_name": name,
            "customer_email": email,
            "customer_phone": phone,
            "customer_city": city,
            "customer_segment": segment,
            "customer_plan": plan,
            "customer_ltv": ltv,
            "amount": amount,
            "currency": "INR",
            "status": "FAILED",
            "error_code": scenario["error_code"],
            "error_description": scenario["error_description"],
            "root_cause": scenario["root_cause"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        
    return payments

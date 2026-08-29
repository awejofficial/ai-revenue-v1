# app/seed_data.py
import asyncio
import json
from app.db import init_db, get_pool

SAMPLE_CUSTOMERS = [
    {
        "customer_id": "cus_high_ltv_01",
        "email": "ravi.sharma@example.com",
        "phone": "+919876543210",
        "crm_data": {
            "name": "Ravi Sharma",
            "company": "Apex Technologies",
            "ltv": 8500,
            "segment": "high_ltv",
            "plan": "enterprise_annual",
            "country": "IN"
        }
    },
    {
        "customer_id": "cus_standard_02",
        "email": "priya.patel@example.com",
        "phone": "+919811223344",
        "crm_data": {
            "name": "Priya Patel",
            "company": "Design Studio",
            "ltv": 650,
            "segment": "standard",
            "plan": "pro_monthly",
            "country": "IN"
        }
    },
    {
        "customer_id": "cus_trial_03",
        "email": "amit.trial@example.com",
        "phone": "+919700112233",
        "crm_data": {
            "name": "Amit Verma",
            "company": "Solo Dev",
            "ltv": 0,
            "segment": "trial",
            "plan": "free_trial",
            "country": "IN"
        }
    },
    {
        "customer_id": "cus_repeat_04",
        "email": "vikram.repeat@example.com",
        "phone": "+919988776655",
        "crm_data": {
            "name": "Vikram Singh",
            "company": "Logistics Co",
            "ltv": 1200,
            "segment": "standard",
            "plan": "growth_monthly",
            "country": "IN"
        }
    },
    {
        "customer_id": "cus_fraud_05",
        "email": "suspicious.user@mailinator.com",
        "phone": "+15551234567",
        "crm_data": {
            "name": "Anonymous Buyer",
            "company": "None",
            "ltv": 150,
            "segment": "standard",
            "plan": "starter_monthly",
            "country": "US"
        }
    },
    {
        "customer_id": "cus_dropoff_06",
        "email": "sarah.connor@cyberdyne.io",
        "phone": "+14155552671",
        "crm_data": {
            "name": "Sarah Connor",
            "company": "Cyberdyne Systems",
            "ltv": 3200,
            "segment": "high_ltv",
            "plan": "scale_annual",
            "country": "US",
            "cart_items": ["Scale Plan Annual Upgrade", "Dedicated Support Add-on"],
            "cart_value": 320.00
        }
    },
    {
        "customer_id": "cus_enterprise_07",
        "email": "david.k@cloudinfra.com",
        "phone": "+14085558900",
        "crm_data": {
            "name": "David Kim",
            "company": "CloudInfra Global",
            "ltv": 18500,
            "segment": "enterprise",
            "plan": "enterprise_custom",
            "country": "US"
        }
    },
    {
        "customer_id": "cus_b2b_08",
        "email": "finance@metrologistics.in",
        "phone": "+919833445566",
        "crm_data": {
            "name": "Karan Malhotra",
            "company": "Metro Logistics Pvt Ltd",
            "ltv": 4500,
            "segment": "standard",
            "plan": "b2b_freight_saas",
            "country": "IN"
        }
    }
]

async def seed():
    print("[Seed] Initializing database...")
    pool = await init_db()
    
    async with pool.acquire() as conn:
        print("[Seed] Seeding customer directory...")
        for c in SAMPLE_CUSTOMERS:
            await conn.execute(
                """
                INSERT INTO customers (customer_id, email, phone, crm_data) 
                VALUES ($1, $2, $3, $4) 
                ON CONFLICT (customer_id) DO NOTHING
                """,
                c['customer_id'], 
                c['email'], 
                c['phone'], 
                json.dumps(c['crm_data'])
            )
            
        print(f"[Seed] Successfully seeded {len(SAMPLE_CUSTOMERS)} diverse customer profiles.")

        # Seed initial failed events for instant demo
        seed_events = [
            {
                "event_id": "demo_fail_001",
                "customer_id": "cus_high_ltv_01",
                "event_type": "payment_failed",
                "amount_usd": 249.00,
                "currency": "USD",
                "raw_error_code": "insufficient_funds",
                "raw_error_message": "Card declined due to insufficient account balance"
            },
            {
                "event_id": "demo_fail_002",
                "customer_id": "cus_standard_02",
                "event_type": "payment_failed",
                "amount_usd": 49.00,
                "currency": "USD",
                "raw_error_code": "card_expired",
                "raw_error_message": "The customer's card has expired (08/26)"
            }
        ]
        
        for ev in seed_events:
            await conn.execute(
                """
                INSERT INTO raw_events (event_id, event_type, customer_id, payload, canonical_event, is_processed) 
                VALUES ($1, $2, $3, $4, $5, FALSE)
                ON CONFLICT (event_id) DO NOTHING
                """,
                ev['event_id'],
                ev['event_type'],
                ev['customer_id'],
                json.dumps(ev),
                json.dumps(ev)
            )
            
        print("[Seed] Seed events queued for orchestrator processing.")
        
        # Verify
        cust_count = await conn.fetchval("SELECT COUNT(*) FROM customers")
        event_count = await conn.fetchval("SELECT COUNT(*) FROM raw_events")
        print(f"[Seed] DB status: {cust_count} customers, {event_count} raw events.")

if __name__ == "__main__":
    asyncio.run(seed())

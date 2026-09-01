# app/routers/customers.py
import json
from fastapi import APIRouter
from app.db import get_pool

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("")
@router.get("/")
async def api_customers():
    """Returns all customers with aggregated CRM and case telemetry."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        customers_raw = await conn.fetch("SELECT * FROM customers ORDER BY customer_id ASC")
        if not customers_raw:
            try:
                from app.seed_data import seed
                await seed()
                customers_raw = await conn.fetch("SELECT * FROM customers ORDER BY customer_id ASC")
            except Exception as e:
                print(f"[api_customers] Auto-seed notice: {e}")
        cases_raw = await conn.fetch("SELECT customer_id, status, amount_usd, created_at FROM cases")
        
        # Aggregate cases by customer
        case_map = {}
        for c in cases_raw:
            cid = c['customer_id']
            if cid not in case_map:
                case_map[cid] = {"total": 0, "resolved": 0, "in_progress": 0, "escalated": 0, "recovered_amount": 0.0, "last_status": "none"}
            case_map[cid]["total"] += 1
            if c['status'] == 'resolved':
                case_map[cid]["resolved"] += 1
                case_map[cid]["recovered_amount"] += float(c['amount_usd'] or 0)
            elif c['status'] in ['new', 'diagnosing', 'retrying', 'awaiting_input']:
                case_map[cid]["in_progress"] += 1
            elif c['status'] == 'escalated':
                case_map[cid]["escalated"] += 1
            case_map[cid]["last_status"] = c['status']
            
        result = []
        for cust in customers_raw:
            crm = cust['crm_data']
            if isinstance(crm, str):
                try:
                    crm = json.loads(crm)
                except Exception:
                    crm = {}
            elif not isinstance(crm, dict):
                crm = {}
                
            cid = cust['customer_id']
            stats = case_map.get(cid, {"total": 0, "resolved": 0, "in_progress": 0, "escalated": 0, "recovered_amount": 0.0, "last_status": "clean"})
            
            result.append({
                "customer_id": cid,
                "name": crm.get("name", cid),
                "company": crm.get("company", "N/A"),
                "email": cust['email'],
                "phone": cust['phone'],
                "ltv": float(crm.get("ltv", 0)),
                "segment": crm.get("segment", "standard"),
                "plan": crm.get("plan", "monthly"),
                "country": crm.get("country", "US"),
                "cart_items": crm.get("cart_items", []),
                "cart_value": float(crm.get("cart_value", 0)),
                "cases_count": stats["total"],
                "resolved_count": stats["resolved"],
                "in_progress_count": stats["in_progress"],
                "recovered_amount": stats["recovered_amount"],
                "last_status": stats["last_status"]
            })
            
        return result

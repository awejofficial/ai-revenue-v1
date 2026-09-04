# app/routers/dashboard.py
from fastapi import APIRouter
from app.db import get_pool

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats")
@router.get("/dashboard/stats/")
async def dashboard_stats():
    """Returns real-time revenue recovery metrics."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) AS total_cases,
                COALESCE(COUNT(CASE WHEN status IN ('new', 'diagnosing', 'retrying', 'awaiting_input') THEN 1 END), 0) AS in_progress_cases,
                COALESCE(COUNT(CASE WHEN status = 'resolved' THEN 1 END), 0) AS resolved_cases,
                COALESCE(COUNT(CASE WHEN status = 'escalated' THEN 1 END), 0) AS escalated_cases,
                COALESCE(SUM(CASE WHEN status IN ('new', 'diagnosing', 'retrying', 'awaiting_input') THEN amount_usd ELSE 0 END), 0) AS at_risk,
                COALESCE(SUM(CASE WHEN status = 'resolved' THEN amount_usd ELSE 0 END), 0) AS recovered,
                COALESCE(SUM(CASE WHEN status = 'escalated' THEN amount_usd ELSE 0 END), 0) AS escalated,
                COALESCE(ROUND((SUM(CASE WHEN status = 'resolved' THEN amount_usd ELSE 0 END) / 
                       NULLIF(SUM(CASE WHEN status IN ('new', 'diagnosing', 'retrying', 'awaiting_input', 'resolved', 'escalated') THEN amount_usd ELSE 0 END), 0) * 100), 2), 0) AS recovery_rate
            FROM cases
        """)
        return dict(stats)


@router.get("/dashboard/cases")
@router.get("/dashboard/cases/")
async def dashboard_cases(limit: int = 50):
    """Returns the latest cases list with explicit payment IDs and AI diagnostics."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        cases = await conn.fetch("""
            SELECT 
                case_id,
                event_id,
                COALESCE(event_id, 'pay_' || SUBSTR(MD5(case_id::text), 1, 10)) AS payment_id,
                customer_id,
                case_type,
                status,
                amount_usd,
                currency,
                root_cause,
                recovery_action,
                payment_link_id,
                recovery_message,
                current_retry_count,
                max_retries,
                last_action,
                scheduled_next_action_at,
                llm_reasoning,
                created_at,
                updated_at
            FROM cases
            ORDER BY updated_at DESC
            LIMIT $1
        """, limit)
        return [dict(c) for c in cases]

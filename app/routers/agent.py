# app/routers/agent.py
"""
Batch Agent Execution & Historical Runs Router (Track 03)
Provides batch execution with stopping rules and audit visibility.
"""

from fastapi import APIRouter, HTTPException, Query
from app.db import get_pool
from app.orchestrator import run_batch

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post("/run-batch")
async def execute_batch(
    count: int = Query(60, ge=1, le=200, description="Batch size (1 to 200 failed payments)")
):
    """
    Executes autonomous recovery across a synthetic Indian BFSI batch.
    Includes the 2-consecutive-failure stopping rule circuit breaker.
    """
    try:
        result = await run_batch(count=count)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch execution failed: {str(e)}")


@router.get("/runs")
async def list_batch_runs():
    """Returns historical batch runs with recovery rates and stopping rule triggers."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        runs = await conn.fetch("""
            SELECT id, run_id, total, recovered, escalated, failed, skipped,
                   money_recovered, recovery_rate, stopped_early, stopped_at_index,
                   started_at, completed_at
            FROM batch_runs
            ORDER BY started_at DESC
            LIMIT 50
        """)
        return [
            {
                "run_id": r["run_id"],
                "total": r["total"],
                "recovered": r["recovered"],
                "escalated": r["escalated"],
                "failed": r["failed"],
                "skipped": r["skipped"] or 0,
                "money_recovered": float(r["money_recovered"] or 0.0),
                "recovery_rate": float(r["recovery_rate"] or 0.0),
                "stopped_early": bool(r["stopped_early"]),
                "stopped_at_index": r["stopped_at_index"],
                "started_at": r["started_at"].isoformat() if r["started_at"] else None,
                "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
            }
            for r in runs
        ]


@router.get("/runs/{run_id}")
async def get_batch_run(run_id: str):
    """Retrieves execution details for a specific batch run."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        r = await conn.fetchrow("""
            SELECT id, run_id, total, recovered, escalated, failed, skipped,
                   money_recovered, recovery_rate, stopped_early, stopped_at_index,
                   started_at, completed_at
            FROM batch_runs
            WHERE run_id = $1
        """, run_id)
        if not r:
            raise HTTPException(status_code=404, detail="Batch run not found")
        return {
            "run_id": r["run_id"],
            "total": r["total"],
            "recovered": r["recovered"],
            "escalated": r["escalated"],
            "failed": r["failed"],
            "skipped": r["skipped"] or 0,
            "money_recovered": float(r["money_recovered"] or 0.0),
            "recovery_rate": float(r["recovery_rate"] or 0.0),
            "stopped_early": bool(r["stopped_early"]),
            "stopped_at_index": r["stopped_at_index"],
            "started_at": r["started_at"].isoformat() if r["started_at"] else None,
            "completed_at": r["completed_at"].isoformat() if r["completed_at"] else None,
        }

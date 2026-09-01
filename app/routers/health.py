# app/routers/health.py
from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
@router.get("/api/health")
async def health_check():
    """Engine health and readiness probe."""
    return {
        "message": "Autonomous AI Revenue Recovery Agent is online.",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }

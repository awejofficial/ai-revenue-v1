# app/main.py
"""
Autonomous AI Revenue Recovery Agent — FastAPI Application
"""

import sys
import os
import asyncio
from contextlib import asynccontextmanager

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db, get_pool
from app.orchestrator import (
    process_pending_events,
    process_scheduled_cases,
)
from app.routers import (
    health,
    webhooks,
    dashboard,
    customers,
    analytics,
    admin,
    agent,
    payments,
    legacy,
)


# --- Lifespan Manager (Startup / Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Auto-seed database if customer directory is empty
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            cust_count = await conn.fetchval("SELECT COUNT(*) FROM customers")
            if not cust_count or cust_count == 0:
                print("[Lifespan] No customers detected in database. Auto-seeding initial profiles & demo cases...")
                from app.seed_data import seed
                await seed()
    except Exception as e:
        print(f"[Lifespan] Auto-seed check notice: {e}")

    # Process any initial pending items
    asyncio.create_task(process_pending_events())
    
    async def background_worker():
        print("[Worker] Background Orchestrator active. Checking events every 15 seconds...")
        while True:
            try:
                await process_pending_events()
                await process_scheduled_cases()
            except Exception as e:
                print(f"[Worker] Background poller error: {e}")
            await asyncio.sleep(15)
    
    worker_task = asyncio.create_task(background_worker())
    
    yield  # Application runs
    
    # Shutdown
    worker_task.cancel()
    print("[Worker] Background Orchestrator stopped.")


app = FastAPI(
    title="Autonomous AI Revenue Recovery Agent",
    version="1.0.0",
    description="Autonomous AI-driven dunning and revenue recovery engine with Stripe, Razorpay, SendGrid, Twilio, and Slack integrations.",
    lifespan=lifespan
)

# Enable CORS for external frontends (e.g., Vercel, custom domains, and local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve compiled authentic shadcn/ui frontend static assets if available
dist_assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", "assets"))
if os.path.exists(dist_assets_dir):
    app.mount("/assets", StaticFiles(directory=dist_assets_dir), name="assets")

# Include Modular Routers
app.include_router(health.router)
app.include_router(payments.router)
app.include_router(agent.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(legacy.router)
# tests/test_api.py
import asyncio
import sys
import httpx

# Ensure UTF-8 output encoding if possible
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.main import app
from app.db import init_db

async def test_api_routes():
    print("==================================================")
    print("[TEST] RUNNING FASTAPI ASYNC API & SIMULATOR TEST SUITE")
    print("==================================================")

    await init_db()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res_health = await client.get("/health")
        print(f"GET /health -> Status {res_health.status_code}: {res_health.json()}")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

        # 2. Dashboard HTML on root /
        res_root = await client.get("/")
        print(f"GET / (Root Dashboard) -> Status {res_root.status_code} (HTML returned)")
        assert res_root.status_code == 200
        assert "<!DOCTYPE html>" in res_root.text

        # 3. Stats
        res_stats = await client.get("/dashboard/stats")
        print(f"GET /dashboard/stats -> Status {res_stats.status_code}: {res_stats.json()}")
        assert res_stats.status_code == 200
        assert "at_risk" in res_stats.json()
        assert "recovered" in res_stats.json()

        # 4. Simulate High-LTV failure
        res_sim1 = await client.post("/admin/simulate?scenario=high_ltv_insufficient_funds")
        print(f"POST /admin/simulate (High-LTV) -> Status {res_sim1.status_code}: {res_sim1.json()}")
        assert res_sim1.status_code == 200

        # 5. Simulate Fraud failure
        res_sim2 = await client.post("/admin/simulate?scenario=fraud")
        print(f"POST /admin/simulate (Fraud) -> Status {res_sim2.status_code}: {res_sim2.json()}")
        assert res_sim2.status_code == 200

        # 6. Simulate Inbound Payment Success
        res_sim3 = await client.post("/admin/simulate?scenario=payment_succeeded")
        print(f"POST /admin/simulate (Payment Succeeded) -> Status {res_sim3.status_code}: {res_sim3.json()}")
        assert res_sim3.status_code == 200

        # 7. Action logs
        res_logs = await client.get("/admin/action-logs?limit=10")
        print(f"GET /admin/action-logs -> Status {res_logs.status_code}: Found {len(res_logs.json())} logs")
        assert res_logs.status_code == 200
        assert len(res_logs.json()) > 0

        # 8. Dashboard cases feed
        res_cases = await client.get("/dashboard/cases?limit=10")
        print(f"GET /dashboard/cases -> Status {res_cases.status_code}: Found {len(res_cases.json())} cases")
        assert res_cases.status_code == 200
        assert len(res_cases.json()) > 0

        # 9. Dashboard HTML on /dashboard
        res_html = await client.get("/dashboard")
        print(f"GET /dashboard -> Status {res_html.status_code} (HTML content returned)")
        assert res_html.status_code == 200
        assert "<!DOCTYPE html>" in res_html.text

    print("\n==================================================")
    print("[SUCCESS] ALL API & SIMULATOR ENDPOINTS VERIFIED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_api_routes())

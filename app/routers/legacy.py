# app/routers/legacy.py
import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter(tags=["Legacy Pages"])

DIST_INDEX = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist", "index.html"))


def serve_spa_or_fallback(fallback_html: str):
    if os.path.exists(DIST_INDEX):
        return FileResponse(DIST_INDEX)
    return HTMLResponse(content=fallback_html, status_code=200)


@router.get("/")
@router.get("/dashboard")
@router.get("/dashboard/")
async def dashboard_page():
    """Serves the interactive operations dashboard SPA or legacy HTML fallback."""
    if os.path.exists(DIST_INDEX):
        return FileResponse(DIST_INDEX)
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Revenue Recovery Agent — Operations Console</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body { font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; text-align: center; }
  .card { max-width: 600px; margin: 40px auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 32px; }
  h1 { font-size: 24px; font-weight: 700; margin-bottom: 12px; color: #38bdf8; }
  p { color: #94a3b8; font-size: 14px; line-height: 1.6; }
  a { display: inline-block; margin-top: 20px; background: #3b82f6; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; }
</style>
</head>
<body>
  <div class="card">
    <h1>Autonomous AI Revenue Recovery Agent</h1>
    <p>The backend API server is online. Access the interactive React SPA frontend or API documentation below.</p>
    <a href="/docs">View Interactive API Docs</a>
  </div>
</body>
</html>
    """, status_code=200)


@router.get("/customers")
@router.get("/customers/")
async def customers_page():
    """Serves the Customer 360° Directory SPA or legacy HTML fallback."""
    if os.path.exists(DIST_INDEX):
        return FileResponse(DIST_INDEX)
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Customer 360° Directory — AI Revenue Recovery</title>
<style>
  body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; text-align: center; }
  a { color: #38bdf8; }
</style>
</head>
<body>
  <h1>Customer 360° Directory</h1>
  <p>Please visit the <a href="/docs">API Documentation</a> or load the React SPA frontend.</p>
</body>
</html>
    """, status_code=200)


@router.get("/analytics")
@router.get("/analytics/")
async def analytics_page():
    """Serves the Recovery Funnel Analytics SPA or legacy HTML fallback."""
    if os.path.exists(DIST_INDEX):
        return FileResponse(DIST_INDEX)
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Recovery Funnel Analytics — AI Revenue Recovery</title>
<style>
  body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; text-align: center; }
  a { color: #38bdf8; }
</style>
</head>
<body>
  <h1>Recovery Funnel Analytics</h1>
  <p>Please visit the <a href="/docs">API Documentation</a> or load the React SPA frontend.</p>
</body>
</html>
    """, status_code=200)

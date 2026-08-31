# app/db.py
import os
import re
import json
import sqlite3
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "")

pool = None

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    email TEXT,
    phone TEXT,
    crm_data JSONB,
    contact_preferences JSONB
);

CREATE TABLE IF NOT EXISTS raw_events (
    id SERIAL PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    canonical_event JSONB NOT NULL,
    ingested_at TIMESTAMP DEFAULT NOW(),
    is_processed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS cases (
    case_id SERIAL PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    customer_id TEXT NOT NULL,
    case_type TEXT NOT NULL,
    amount_usd NUMERIC DEFAULT 0,
    status TEXT DEFAULT 'new',
    max_retries INT DEFAULT 3,
    current_retry_count INT DEFAULT 0,
    last_action TEXT,
    scheduled_next_action_at TIMESTAMP,
    llm_reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS action_logs (
    id SERIAL PRIMARY KEY,
    case_id INT,
    customer_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    channel TEXT,
    recipient TEXT,
    payload JSONB,
    status TEXT DEFAULT 'sent',
    details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_events_unprocessed 
ON raw_events (is_processed, ingested_at);

CREATE INDEX IF NOT EXISTS idx_cases_customer 
ON cases (customer_id);

CREATE INDEX IF NOT EXISTS idx_cases_status 
ON cases (status);
"""

class SQLiteRow(dict):
    def __getitem__(self, item):
        if isinstance(item, int):
            return list(self.values())[item]
        return super().__getitem__(item)

class SQLiteConn:
    def __init__(self, db_path="revenue_db.sqlite"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _convert_sql(self, sql):
        # Convert PostgreSQL $1, $2 params to SQLite ?
        sql = re.sub(r'\$(\d+)', '?', sql)
        # Convert NOW() - INTERVAL '3 months' to datetime('now', '-3 months')
        sql = re.sub(r"NOW\(\)\s*-\s*INTERVAL\s*'(\d+)\s+(\w+)'", r"datetime('now', '-\1 \2')", sql, flags=re.IGNORECASE)
        sql = sql.replace("NOW()", "CURRENT_TIMESTAMP")
        sql = sql.replace("JSONB", "TEXT")
        sql = sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        sql = sql.replace("NUMERIC", "REAL")
        return sql

    def _sanitize_args(self, args):
        sanitized = []
        for arg in args:
            if isinstance(arg, (dict, list)):
                sanitized.append(json.dumps(arg))
            elif isinstance(arg, datetime):
                sanitized.append(arg.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                sanitized.append(arg)
        return sanitized

    async def execute(self, sql, *args):
        csql = self._convert_sql(sql)
        cursor = self.conn.cursor()
        s_args = self._sanitize_args(args)
        cursor.execute(csql, s_args)
        self.conn.commit()
        return cursor

    async def fetch(self, sql, *args):
        csql = self._convert_sql(sql)
        cursor = self.conn.cursor()
        s_args = self._sanitize_args(args)
        cursor.execute(csql, s_args)
        rows = cursor.fetchall()
        return [SQLiteRow(dict(r)) for r in rows]

    async def fetchrow(self, sql, *args):
        rows = await self.fetch(sql, *args)
        return rows[0] if rows else None

    async def fetchval(self, sql, *args):
        row = await self.fetchrow(sql, *args)
        if row:
            return list(row.values())[0]
        return None

class SQLitePool:
    def __init__(self, db_path="revenue_db.sqlite"):
        self.db_path = db_path
        self._conn = SQLiteConn(db_path)

    def acquire(self):
        class ConnContext:
            def __init__(ctx, conn):
                ctx.conn = conn
            async def __aenter__(ctx):
                return ctx.conn
            async def __aexit__(ctx, exc_type, exc, tb):
                pass
        return ConnContext(self._conn)

    async def execute(self, sql, *args):
        return await self._conn.execute(sql, *args)

    async def fetch(self, sql, *args):
        return await self._conn.fetch(sql, *args)

    async def fetchrow(self, sql, *args):
        return await self._conn.fetchrow(sql, *args)

    async def fetchval(self, sql, *args):
        return await self._conn.fetchval(sql, *args)


async def ensure_schema(db_pool):
    """Ensures all tables and indexes exist on startup."""
    async with db_pool.acquire() as conn:
        for statement in SCHEMA_SQL.split(";"):
            stmt = statement.strip()
            if stmt:
                try:
                    await conn.execute(stmt)
                except Exception as e:
                    print(f"[DB] Schema migration notice on '{stmt[:30]}...': {e}")
        
        # Migration: Ensure contact_preferences column exists on customers table
        try:
            await conn.execute("ALTER TABLE customers ADD COLUMN contact_preferences TEXT")
        except Exception:
            pass  # Already exists or dialect handles it


async def init_db():
    global pool
    db_url = DATABASE_URL
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    if db_url and db_url.startswith("postgresql"):
        try:
            import asyncpg
            pool = await asyncpg.create_pool(db_url, min_size=2, max_size=20, timeout=10.0)
            print("[DB] Connected to PostgreSQL pool successfully.")
            await ensure_schema(pool)
            return pool
        except Exception as e:
            print(f"[DB] Could not connect to PostgreSQL ({e}). Falling back to local SQLite database...")
    
    pool = SQLitePool()
    print("[DB] Local SQLite database pool initialized.")
    await ensure_schema(pool)
    return pool

async def get_pool():
    global pool
    if pool is None:
        await init_db()
    return pool

# ===============================================================
# Pulse AI — Database Layer (db.py)
# ===============================================================
# Provides a lightweight async interface for database operations.
# Compatible with Supabase or any Postgres instance.
# Uses 'databases' and 'asyncpg' under the hood.
# ===============================================================

import os
import logging
import asyncio
from databases import Database

# ===============================================================
# Configuration
# ===============================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "❌ DATABASE_URL environment variable not set. "
        "Please configure it in your Render service."
    )

# Create a database instance
db = Database(DATABASE_URL)
logger = logging.getLogger("uvicorn.error")


# ===============================================================
# Database connection management
# ===============================================================
async def connect_db():
    """Connect to the database (called on app startup)."""
    try:
        if not db.is_connected:
            await db.connect()
            logger.info("✅ Database connection established.")
    except Exception as e:
        logger.exception(f"❌ Database connection failed: {e}")


async def disconnect_db():
    """Disconnect from the database (called on app shutdown)."""
    try:
        if db.is_connected:
            await db.disconnect()
            logger.info("🟡 Database disconnected.")
    except Exception as e:
        logger.warning(f"Database disconnect error: {e}")


# ===============================================================
# Helper functions for convenience
# ===============================================================
async def execute(query: str, values: dict | None = None):
    """
    Execute INSERT, UPDATE, or DELETE statements.
    Returns None.
    """
    if not db.is_connected:
        await connect_db()
    try:
        await db.execute(query=query, values=values or {})
    except Exception as e:
        logger.exception(f"❌ Database execute error: {e}")
        raise


async def fetch_all(query: str, values: dict | None = None):
    """
    Fetch multiple rows from the database.
    Returns a list of dict-like objects.
    """
    if not db.is_connected:
        await connect_db()
    try:
        rows = await db.fetch_all(query=query, values=values or {})
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.exception(f"❌ Database fetch_all error: {e}")
        raise


async def fetch_one(query: str, values: dict | None = None):
    """
    Fetch a single row from the database.
    Returns a dict or None.
    """
    if not db.is_connected:
        await connect_db()
    try:
        row = await db.fetch_one(query=query, values=values or {})
        return dict(row._mapping) if row else None
    except Exception as e:
        logger.exception(f"❌ Database fetch_one error: {e}")
        raise


# ===============================================================
# Utility: test connection (manual use)
# ===============================================================
async def test_connection():
    """Quick test to verify DB connectivity."""
    try:
        await connect_db()
        result = await db.fetch_one("SELECT NOW() AS now;")
        logger.info(f"🧠 DB connected successfully — server time: {result['now']}")
    except Exception as e:
        logger.error(f"DB test failed: {e}")
    finally:
        await disconnect_db()


# ===============================================================
# Optional: integrate with FastAPI lifecycle hooks
# ===============================================================
def setup_db_events(app):
    """
    Attach startup and shutdown events to a FastAPI app.
    Example:
        from app.db import setup_db_events
        setup_db_events(app)
    """
    @app.on_event("startup")
    async def startup():
        await connect_db()

    @app.on_event("shutdown")
    async def shutdown():
        await disconnect_db()

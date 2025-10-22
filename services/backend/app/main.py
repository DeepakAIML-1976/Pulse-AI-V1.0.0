# ===============================================================
# Pulse AI — Main Application Entry Point (Production)
# ===============================================================
# This file initializes the FastAPI app, sets up CORS, connects
# to the database, and auto-loads all API routers dynamically
# from app/api/. Compatible with Render deployment.
# ===============================================================

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from importlib import import_module
from pathlib import Path

from app.db import setup_db_events

# ===============================================================
# Application Setup
# ===============================================================

app = FastAPI(
    title="Pulse AI Backend",
    description="Backend for Pulse AI Emotional Health Companion",
    version="1.0.0",
)

# ===============================================================
# CORS Configuration
# ===============================================================

# CORS origins: include both production and localhost URLs
BACKEND_CORS_ORIGINS = os.getenv(
    "BACKEND_CORS_ORIGINS",
    "https://pulse-ai-v1-0-0.vercel.app,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================================================
# Database Connection (lifecycle management)
# ===============================================================
setup_db_events(app)

# ===============================================================
# Dynamic Router Auto-Loading
# ===============================================================
# Automatically includes all routers from app/api/
# so you don’t need to manually import each route file.

from fastapi import APIRouter

router = APIRouter()
api_path = Path(__file__).parent / "api"

for file in api_path.glob("*.py"):
    if file.stem.startswith("__"):
        continue
    module_name = f"app.api.{file.stem}"
    try:
        module = import_module(module_name)
        if hasattr(module, "router"):
            router.include_router(getattr(module, "router"))
            print(f"✅ Loaded router: {module_name}")
    except Exception as e:
        print(f"⚠️ Skipped {module_name}: {e}")

app.include_router(router)

# ===============================================================
# Root Health Check Endpoint
# ===============================================================
@app.get("/")
async def root():
    """Simple endpoint to confirm backend health."""
    return {
        "status": "ok",
        "message": "Pulse AI backend is running 🚀",
        "version": "1.0.0",
        "routers_loaded": [f.stem for f in api_path.glob('*.py') if not f.stem.startswith('__')]
    }

# ===============================================================
# Optional: OpenAPI Metadata Override
# ===============================================================
app.openapi_tags = [
    {"name": "chat", "description": "AI-powered conversational endpoints"},
    {"name": "mood", "description": "Mood detection and recommendation endpoints"},
]

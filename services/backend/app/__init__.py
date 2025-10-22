"""
App package initializer for Pulse backend.
Auto-discovers and registers routers from the `api` package.
"""
from fastapi import APIRouter
from importlib import import_module
from pathlib import Path

router = APIRouter()

# Dynamically import all routers under app/api/
api_path = Path(__file__).parent / "api"

for file in api_path.glob("*.py"):
    if file.stem.startswith("__"):
        continue  # skip __init__.py
    module_name = f"app.api.{file.stem}"
    try:
        module = import_module(module_name)
        if hasattr(module, "router"):
            router.include_router(getattr(module, "router"))
    except Exception as e:
        print(f"⚠️  Skipped {file.stem}: {e}")

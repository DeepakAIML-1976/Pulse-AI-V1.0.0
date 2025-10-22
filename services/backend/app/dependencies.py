import os
import httpx
import logging
from fastapi import Header, HTTPException

logger = logging.getLogger("uvicorn.error")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

async def get_current_user_dependency(authorization: str | None = Header(None)):
    """Validate Supabase access token and return current user."""
    if not SUPABASE_URL:
        logger.warning("SUPABASE_URL not set — using dev user.")
        return {"id": "dev-user", "email": "dev@pulse.local"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]
    headers = {"Authorization": f"Bearer {token}", "apikey": SUPABASE_ANON_KEY or ""}
    url = f"{SUPABASE_URL}/auth/v1/user"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning(f"Supabase auth failed: {resp.text}")
            raise HTTPException(status_code=401, detail="Invalid Supabase token")
        data = resp.json()
        return {"id": data.get("id"), "email": data.get("email")}
    except Exception as e:
        logger.exception("Error validating token with Supabase")
        raise HTTPException(status_code=500, detail="Auth validation error")

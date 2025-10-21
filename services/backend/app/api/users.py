# services/backend/app/api/users.py
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Optional
from ..core.config import settings
from ..db import get_session
from ..models import User
import httpx

router = APIRouter(prefix="/api/users", tags=["users"])

async def _supabase_get_user(access_token: str) -> Optional[Dict]:
    """
    Call Supabase /auth/v1/user to verify token and fetch user metadata.
    Returns None if Supabase not configured or token invalid.
    """
    if not settings.SUPABASE_URL:
        return None
    url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {"Authorization": f"Bearer {access_token}", "apikey": settings.SUPABASE_ANON_KEY or ""}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, headers=headers)
        if r.status_code != 200:
            return None
        return r.json()

@router.post("/sync")
async def sync_user(payload: Dict = Body(...)):
    """
    Body: { "access_token": "<supabase_access_token>" }
    Ensures a backend User row exists for the Supabase user id.
    """
    access_token = payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="access_token required")

    sup_user = await _supabase_get_user(access_token)
    if not sup_user:
        raise HTTPException(status_code=401, detail="Invalid Supabase token or Supabase not configured")

    user_id = sup_user.get("id")
    email = sup_user.get("email")
    # Supabase may store metadata in user_metadata
    name = sup_user.get("user_metadata", {}).get("full_name") or sup_user.get("email")

    with get_session() as session:
        existing = session.get(User, user_id)
        if existing:
            # update email/display_name if missing or changed
            updated = False
            if existing.email != email:
                existing.email = email
                updated = True
            if existing.display_name != name:
                existing.display_name = name
                updated = True
            if updated:
                session.add(existing)
                session.commit()
                session.refresh(existing)
            return {"id": existing.id, "email": existing.email, "display_name": existing.display_name}
        # create
        user = User(id=user_id, email=email, display_name=name)
        session.add(user)
        session.commit()
        session.refresh(user)
        return {"id": user.id, "email": user.email, "display_name": user.display_name}

"""
app/api/mood.py
Handles mood snapshots (text/audio input → detection → DB persistence → history retrieval)
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from services.backend.app.db import database as db  # Adjust import paths
from services.backend.app.auth import get_current_user
from services.backend.app.ai_utils import analyze_mood_text, generate_empathy_response

router = APIRouter()


# ============================
# MODELS
# ============================

class MoodRequest(BaseModel):
    source: str
    raw_text: str | None = None
    audio_s3_key: str | None = None


class MoodResponse(BaseModel):
    assistant_message: str
    detected_emotion: str
    confidence: float | None = None
    timestamp: str


class MoodHistoryItem(BaseModel):
    id: str
    detected_emotion: str | None
    confidence: float | None
    raw_text: str | None
    created_at: str


# ============================
# ROUTES
# ============================

@router.post("/mood", response_model=MoodResponse)
async def process_mood(request: MoodRequest, user=Depends(get_current_user)):
    """
    POST /mood
    Process user's mood input, detect emotion, save to DB, and return AI response.
    """
    try:
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized user")

        detected_emotion, confidence = await analyze_mood_text(request.raw_text)
        ai_response = await generate_empathy_response(detected_emotion, request.raw_text)

        entry_id = str(uuid.uuid4())
        now = datetime.utcnow()

        await db.execute(
            """
            INSERT INTO moodsnapshot 
            (id, user_id, source, raw_text, audio_s3_key, detected_emotion, confidence, meta_data, created_at)
            VALUES (:id, :user_id, :source, :raw_text, :audio_s3_key, :detected_emotion, :confidence, :meta_data, :created_at)
            """,
            {
                "id": entry_id,
                "user_id": user.id,
                "source": request.source or "text",
                "raw_text": request.raw_text,
                "audio_s3_key": request.audio_s3_key,
                "detected_emotion": detected_emotion,
                "confidence": confidence,
                "meta_data": None,
                "created_at": now,
            },
        )

        return MoodResponse(
            assistant_message=ai_response,
            detected_emotion=detected_emotion,
            confidence=confidence,
            timestamp=now.isoformat(),
        )

    except Exception as e:
        print(f"❌ Error processing mood: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================
# MOOD HISTORY ENDPOINT
# ============================

@router.get("/mood/history", response_model=list[MoodHistoryItem])
async def get_mood_history(limit: int = 20, user=Depends(get_current_user)):
    """
    GET /mood/history
    Fetch recent mood snapshots for the current user (default: last 20 entries)
    """
    try:
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized user")

        query = """
        SELECT id, detected_emotion, confidence, raw_text, created_at
        FROM moodsnapshot
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT :limit
        """
        rows = await db.fetch_all(query, {"uid": user.id, "limit": limit})

        return [
            {
                "id": r["id"],
                "detected_emotion": r["detected_emotion"],
                "confidence": r["confidence"],
                "raw_text": r["raw_text"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]

    except Exception as e:
        print(f"❌ Error fetching mood history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch mood history")

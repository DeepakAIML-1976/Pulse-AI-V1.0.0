# ===============================================================
# Universal Import Guard — works both locally and on Render
# ===============================================================
import os, sys
from pathlib import Path

# Ensure backend root directory (the folder containing `app/`) is in Python path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# ===============================================================
# Safe imports for dependencies and database
# ===============================================================
try:
    from app.dependencies import get_current_user_dependency
    from app.database import db
except ModuleNotFoundError:
    from ..dependencies import get_current_user_dependency
    from ..database import db

# ===============================================================
# Core dependencies
# ===============================================================
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
import httpx
import logging
import uuid

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

# ===============================================================
# Configuration
# ===============================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


# ===============================================================
# Pydantic Schema for incoming requests
# ===============================================================
class ChatRequest(BaseModel):
    content: str
    session_id: str | None = None  # optional session grouping


# ===============================================================
# Helper: detect emotion using OpenAI
# ===============================================================
async def detect_emotion_from_text(message: str) -> str | None:
    """
    Uses OpenAI (gpt-4o-mini) to categorize user emotion from text.
    Returns one-word label like happy, sad, anxious, angry, calm, tired, or neutral.
    """
    if not OPENAI_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an emotion detector. "
                                "Return only one emotion word (happy, sad, anxious, angry, calm, tired, neutral) "
                                "based on the text provided. Do not explain."
                            ),
                        },
                        {"role": "user", "content": message},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 5,
                },
            )
        if r.status_code == 200:
            reply = r.json()["choices"][0]["message"]["content"].strip().lower()
            return reply.split()[0] if reply else None
        else:
            logger.warning(f"Emotion detection failed: {r.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Emotion detection error: {e}")
        return None


# ===============================================================
# Main AI Chat Endpoint
# ===============================================================
@router.post("/api/chat")
async def chat_with_ai(payload: ChatRequest, user=Depends(get_current_user_dependency)):
    """
    AI-powered chat endpoint for Pulse.
    • Stores user & AI messages in `chatmessage` table
    • Detects emotion for each user message
    • Returns AI reply, session_id, and detected emotion
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Missing OpenAI API key")

    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized user")

    user_msg = payload.content.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Empty message")

    session_id = payload.session_id or str(uuid.uuid4())
    created_at = datetime.utcnow()

    # -----------------------------------------------------------
    # Step 1: Detect emotion for user message
    # -----------------------------------------------------------
    detected_emotion = await detect_emotion_from_text(user_msg)

    # -----------------------------------------------------------
    # Step 2: Store user message
    # -----------------------------------------------------------
    try:
        await db.execute(
            """
            INSERT INTO chatmessage (id, user_id, session_id, role, content, detected_emotion, created_at)
            VALUES (:id, :uid, :sid, :role, :content, :emotion, :ts)
            """,
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "sid": session_id,
                "role": "user",
                "content": user_msg,
                "emotion": detected_emotion,
                "ts": created_at,
            },
        )
    except Exception as e:
        logger.warning(f"Could not save user message: {e}")

    # -----------------------------------------------------------
    # Step 3: Retrieve context (last few messages)
    # -----------------------------------------------------------
    try:
        history = await db.fetch_all(
            """
            SELECT role, content FROM chatmessage
            WHERE user_id = :uid AND session_id = :sid
            ORDER BY created_at DESC
            LIMIT 6
            """,
            {"uid": user_id, "sid": session_id},
        )
        messages = [{"role": row["role"], "content": row["content"]} for row in reversed(history)]
    except Exception as e:
        logger.warning(f"Failed to fetch chat history: {e}")
        messages = []

    # -----------------------------------------------------------
    # Step 4: Add AI system instruction
    # -----------------------------------------------------------
    messages.insert(
        0,
        {
            "role": "system",
            "content": (
                "You are Pulse, an empathetic emotional health companion. "
                "Respond warmly and reflectively. "
                "If the user seems sad, anxious, or tired, respond with empathy "
                "and optionally suggest calming Hindi or English songs or movies. "
                "Keep responses short, natural, and human-like."
            ),
        },
    )

    # -----------------------------------------------------------
    # Step 5: Generate AI reply
    # -----------------------------------------------------------
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.8,
                    "max_tokens": 300,
                },
            )

        if r.status_code != 200:
            logger.error(f"OpenAI API error {r.status_code}: {r.text}")
            raise HTTPException(status_code=502, detail="OpenAI API request failed")

        ai_reply = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("Error generating AI reply")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")

    # -----------------------------------------------------------
    # Step 6: Store AI reply
    # -----------------------------------------------------------
    try:
        await db.execute(
            """
            INSERT INTO chatmessage (id, user_id, session_id, role, content, detected_emotion, created_at)
            VALUES (:id, :uid, :sid, :role, :content, NULL, :ts)
            """,
            {
                "id": str(uuid.uuid4()),
                "uid": user_id,
                "sid": session_id,
                "role": "bot",
                "content": ai_reply,
                "ts": datetime.utcnow(),
            },
        )
    except Exception as e:
        logger.warning(f"Could not save AI reply: {e}")

    # -----------------------------------------------------------
    # Step 7: Return response (same structure + emotion)
    # -----------------------------------------------------------
    return {
        "assistant_message": ai_reply,
        "session_id": session_id,
        "detected_emotion": detected_emotion or "neutral",
    }

# ===============================================================
# Pulse AI — Chat API Endpoint (Production Version)
# ===============================================================
# This file defines the /api/chat endpoint for Pulse.
# It uses OpenAI for chat responses and emotion detection,
# and Supabase (PostgreSQL) for message persistence.
# Compatible with Render + Vercel full-stack deployment.
# ===============================================================

import os
import sys
from pathlib import Path
from datetime import datetime
import uuid
import logging
import httpx

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# ===============================================================
# Universal Import Guard — works in Render, Docker, or local dev
# ===============================================================
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from app.dependencies import get_current_user_dependency
    from app.db import db  # ✅ Updated reference
except ModuleNotFoundError:
    # fallback for relative import contexts
    from ..dependencies import get_current_user_dependency
    from ..db import db  # ✅ Updated reference

# ===============================================================
# Router registration
# ===============================================================
router = APIRouter(prefix="/api", tags=["chat"])

# ===============================================================
# Config
# ===============================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

logger = logging.getLogger("uvicorn.error")


# ===============================================================
# Schema for incoming chat requests
# ===============================================================
class ChatRequest(BaseModel):
    content: str
    session_id: str | None = None  # optional session grouping


# ===============================================================
# Helper: detect emotion using OpenAI (gpt-4o-mini)
# ===============================================================
async def detect_emotion_from_text(message: str) -> str | None:
    """Return a one-word emotion label (happy, sad, calm, etc.) for a message."""
    if not OPENAI_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
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
                                "You are an emotion detector. Return only one emotion word "
                                "(happy, sad, anxious, angry, calm, tired, neutral) "
                                "based on the user text. Do not explain."
                            ),
                        },
                        {"role": "user", "content": message},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 5,
                },
            )

        if response.status_code == 200:
            detected = response.json()["choices"][0]["message"]["content"].strip().lower()
            return detected.split()[0] if detected else None
        else:
            logger.warning(f"Emotion detection failed: {response.status_code}")
            return None
    except Exception as e:
        logger.warning(f"Emotion detection error: {e}")
        return None


# ===============================================================
# Main Chat Endpoint
# ===============================================================
@router.post("/chat")
async def chat_with_ai(payload: ChatRequest, user=Depends(get_current_user_dependency)):
    """
    Handles user chat requests:
      • Stores messages in Supabase (chatmessage table)
      • Detects emotion for user messages
      • Generates empathetic AI responses
      • Returns both AI message + detected emotion
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

    # Step 1: Detect emotion
    detected_emotion = await detect_emotion_from_text(user_msg)

    # Step 2: Save user message
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

    # Step 3: Retrieve conversation history
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

    # Step 4: Add AI system prompt
    messages.insert(
        0,
        {
            "role": "system",
            "content": (
                "You are Pulse, an empathetic emotional health companion. "
                "Respond kindly, help users manage their feelings, and suggest calming "
                "music or movies (Hindi or English) when appropriate. Keep responses short, warm, and natural."
            ),
        },
    )

    # Step 5: Generate AI reply
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            ai_response = await client.post(
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

        if ai_response.status_code != 200:
            logger.error(f"OpenAI API error {ai_response.status_code}: {ai_response.text}")
            raise HTTPException(status_code=502, detail="OpenAI API request failed")

        ai_reply = ai_response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("Error generating AI reply")
        raise HTTPException(status_code=500, detail="Failed to generate AI response")

    # Step 6: Save AI reply
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

    # Step 7: Return response
    return {
        "assistant_message": ai_reply,
        "session_id": session_id,
        "detected_emotion": detected_emotion or "neutral",
    }


# ===============================================================
# Health Check Route (optional)
# ===============================================================
@router.get("/chat/ping")
async def ping_chat_api():
    """Simple endpoint to confirm the chat route is live."""
    return {"status": "ok", "message": "Chat API is active 🚀"}

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.dependencies import get_current_user_dependency
from app.database import db
from datetime import datetime
import os, httpx, logging

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

class ChatRequest(BaseModel):
    content: str

@router.post("/api/chat")
async def chat_with_ai(payload: ChatRequest, user=Depends(get_current_user_dependency)):
    """Handles chat between user and AI + stores conversation."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key missing.")

    user_id = user.get("id")
    user_msg = payload.content.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Empty message.")

    # Save user's message
    await db.execute(
        "INSERT INTO chat_messages (user_id, role, content, created_at) VALUES (:uid, :r, :c, :t)",
        {"uid": user_id, "r": "user", "c": user_msg, "t": datetime.utcnow()},
    )

    # Fetch last few messages for context (user + bot)
    rows = await db.fetch_all(
        """
        SELECT role, content FROM chat_messages
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT 5
        """,
        {"uid": user_id},
    )
    messages = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    # Add system instruction for consistent AI personality
    messages.insert(0, {
        "role": "system",
        "content": (
            "You are Pulse, an empathetic emotional health companion. "
            "You provide warm, understanding responses to users' emotional states. "
            "If the user seems sad, anxious, or tired, be supportive and kind. "
            "When asked for music or movie recommendations, consider their mood "
            "and provide both English and Hindi options where relevant."
        ),
    })

    # Make OpenAI call
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
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

        if response.status_code != 200:
            logger.error(f"OpenAI error {response.status_code}: {response.text}")
            raise HTTPException(status_code=502, detail="OpenAI API request failed.")

        data = response.json()
        ai_reply = data["choices"][0]["message"]["content"].strip()

        # Save bot reply
        await db.execute(
            "INSERT INTO chat_messages (user_id, role, content, created_at) VALUES (:uid, :r, :c, :t)",
            {"uid": user_id, "r": "bot", "c": ai_reply, "t": datetime.utcnow()},
        )

        logger.info(f"AI replied to {user_id[:8]}: {ai_reply[:80]}...")
        return {"assistant_message": ai_reply}

    except Exception as e:
        logger.exception("Error generating AI reply")
        raise HTTPException(status_code=500, detail="Failed to generate AI response.")

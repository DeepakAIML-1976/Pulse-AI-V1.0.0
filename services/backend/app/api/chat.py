# services/backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict
from ..core.config import settings
from ..db import get_session
from ..models import ChatMessage
from sqlmodel import select
import httpx, json
from .mood import _classify_text_with_openai, _heuristic_text_classify, get_current_user_dependency
from ..utils.recommendations import get_recommendations_for_emotion

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("", status_code=201)
async def post_message(
    body: Dict = Body(...),  # expects { content: str, session_id?: str }
    current_user: dict = Depends(get_current_user_dependency)
):
    content = body.get("content")
    session_id = body.get("session_id")
    if not content:
        raise HTTPException(status_code=400, detail="content required")

    # detect emotion for the user's message
    cls = await _classify_text_with_openai(content) or _heuristic_text_classify(content)
    emotion = cls.get("label")
    confidence = float(cls.get("confidence", 0.6))

    # store the user message
    with get_session() as session:
        user_msg = ChatMessage(
            user_id=current_user["id"],
            session_id=session_id,
            role="user",
            content=content,
            detected_emotion=emotion
        )
        session.add(user_msg)
        session.commit()
        session.refresh(user_msg)

    # build context from recent messages (last 6)
    context_messages = []
    with get_session() as s:
        stmt = select(ChatMessage).where(ChatMessage.user_id == current_user["id"]).order_by(ChatMessage.created_at.desc()).limit(6)
        rows = s.exec(stmt).all()
        # reverse chronological -> chronological
        for r in reversed(rows):
            context_messages.append({"role": r.role, "content": r.content})

    # system prompt for assistant persona
    system_prompt = (
        "You are Pulse, a helpful empathetic assistant. Use CBT-informed, non-clinical tone. "
        "Offer small practical nudges and suggestions. If user describes serious self-harm intent, respond with crisis resources."
    )

    # generate assistant reply via OpenAI if key available
    reply_text = "Sorry — I couldn't reach the assistant right now."
    if settings.OPENAI_API_KEY:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": content})
        payload = {"model": "gpt-4o-mini", "messages": messages, "temperature": 0.7, "max_tokens": 300}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                try:
                    reply_text = resp.json()["choices"][0]["message"]["content"]
                except Exception:
                    reply_text = "Thanks — can you say a bit more?"
            else:
                reply_text = "I'm here but couldn't reach the model. Try again."

    # detect emotion of assistant reply (optional)
    reply_cls = await _classify_text_with_openai(reply_text) if settings.OPENAI_API_KEY else _heuristic_text_classify(reply_text)
    reply_emotion = reply_cls.get("label") if reply_cls else None

    # store assistant message
    with get_session() as session:
        assistant_msg = ChatMessage(
            user_id=current_user["id"],
            session_id=session_id,
            role="assistant",
            content=reply_text,
            detected_emotion=reply_emotion
        )
        session.add(assistant_msg)
        session.commit()
        session.refresh(assistant_msg)

    # recommendations (Spotify + TMDB) for the detected emotion of the user message
    recs = await get_recommendations_for_emotion(emotion or "neutral")

    return {
        "user_message": user_msg.dict(),
        "assistant_message": assistant_msg.dict(),
        "recommendations": recs
    }

@router.get("/history", response_model=List[dict])
def chat_history(limit: int = 50, current_user: dict = Depends(get_current_user_dependency)):
    with get_session() as session:
        stmt = select(ChatMessage).where(ChatMessage.user_id == current_user["id"]).order_by(ChatMessage.created_at.desc()).limit(limit)
        rows = session.exec(stmt).all()
        return [r.dict() for r in rows]

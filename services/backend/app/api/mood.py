from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, Form, Header, Path
)

from typing import Optional, List
from sqlmodel import select
from ..models import MoodSnapshot
from ..db import get_session
from ..core.config import settings
import uuid, json, boto3, httpx, redis

router = APIRouter(prefix="/api/mood", tags=["mood"])

# -----------------------------
# AUTH: Supabase token verifier
# -----------------------------
async def get_current_user_dependency(authorization: str | None = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization.split(" ", 1)[1]
    if not settings.SUPABASE_URL:
        return {"id": "dev-user-1", "email": "dev@pulse.local"}

    url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {"Authorization": f"Bearer {token}", "apikey": settings.SUPABASE_ANON_KEY or ""}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Supabase token")
        data = resp.json()
        return {"id": data.get("id"), "email": data.get("email")}

# -----------------------------
# HELPERS
# -----------------------------
def _s3_client():
    if not settings.S3_ENDPOINT:
        return None
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )

def _redis_client():
    try:
        return redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception:
        return None

async def _classify_text_with_openai(text: str):
    if not settings.OPENAI_API_KEY:
        return None
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    prompt = (
        "Classify the emotion of the following text into one of: calm, happy, sad, anxious, angry, neutral. "
        "Respond JSON: {\"label\": \"<label>\", \"confidence\": <float>}\n\nText: " + text
    )
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            return None
        try:
            content = r.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            return None

def _heuristic_text_classify(text: str):
    t = text.lower()
    if any(w in t for w in ["panic", "anxious", "stressed", "worried"]):
        return {"label": "anxious", "confidence": 0.85}
    if any(w in t for w in ["sad", "depressed", "lonely"]):
        return {"label": "sad", "confidence": 0.8}
    if any(w in t for w in ["happy", "glad", "great", "awesome"]):
        return {"label": "happy", "confidence": 0.9}
    if any(w in t for w in ["angry", "mad", "furious"]):
        return {"label": "angry", "confidence": 0.8}
    return {"label": "neutral", "confidence": 0.6}

# -----------------------------
# ROUTES
# -----------------------------
@router.post("", status_code=201)
async def create_mood_snapshot(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user_dependency)
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide text or file")

    s3_key = None
    if file:
        filename = f"audio/{uuid.uuid4().hex}_{file.filename}"
        contents = await file.read()
        client = _s3_client()
        if client:
            client.put_object(Bucket=settings.S3_BUCKET, Key=filename, Body=contents)
            s3_key = filename

    classification = None
    if text:
        classification = await _classify_text_with_openai(text)
    if classification is None:
        classification = _heuristic_text_classify(text or "")

    snapshot = MoodSnapshot(
        user_id=current_user["id"],
        source="voice" if file else "text",
        raw_text=text,
        audio_s3_key=s3_key,
        detected_emotion=classification["label"],
        confidence=float(classification["confidence"]),
        meta_data=json.dumps({"source_hint": "mvp"}),
    )

    with get_session() as session:
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)

    # publish transcription job if audio uploaded
    if s3_key:
        rc = _redis_client()
        if rc:
            job = {"snapshot_id": snapshot.id, "audio_s3_key": s3_key}
            rc.publish("pulse:transcribe_jobs", json.dumps(job))

    return {
        "id": snapshot.id,
        "detected_emotion": snapshot.detected_emotion,
        "confidence": snapshot.confidence,
        "created_at": snapshot.created_at.isoformat(),
        "raw_text": snapshot.raw_text,
        "audio_s3_key": snapshot.audio_s3_key
    }

@router.get("", response_model=List[dict])
def list_snapshots(current_user: dict = Depends(get_current_user_dependency)):
    with get_session() as session:
        statement = select(MoodSnapshot).where(MoodSnapshot.user_id == current_user["id"]).order_by(MoodSnapshot.created_at.desc())
        results = session.exec(statement).all()
        out = []
        for s in results:
            out.append({
                "id": s.id,
                "source": s.source,
                "raw_text": s.raw_text,
                "detected_emotion": s.detected_emotion,
                "confidence": s.confidence,
                "created_at": s.created_at.isoformat()
            })
        return out

@router.post("/{snapshot_id}/transcription")
async def transcription_callback(
    snapshot_id: str = Path(...),
    payload: dict = None,
    x_service_key: Optional[str] = Header(None)
):
    if settings.BACKEND_SERVICE_KEY and x_service_key != settings.BACKEND_SERVICE_KEY:
        raise HTTPException(status_code=403, detail="Invalid service key")

    if not payload or "transcribed_text" not in payload:
        raise HTTPException(status_code=400, detail="Invalid payload")

    text = payload["transcribed_text"]
    with get_session() as session:
        res = session.exec(select(MoodSnapshot).where(MoodSnapshot.id == snapshot_id)).one_or_none()
        if not res:
            raise HTTPException(status_code=404, detail="Not found")

        res.raw_text = res.raw_text or text
        meta = json.loads(res.meta_data or "{}")
        meta.update({"transcribed": True})
        res.meta_data = json.dumps(meta)

        cls = await _classify_text_with_openai(text) or _heuristic_text_classify(text)
        res.detected_emotion = cls["label"]
        res.confidence = float(cls["confidence"])

        session.add(res)
        session.commit()
        session.refresh(res)

    return {"status": "ok", "id": snapshot_id, "emotion": res.detected_emotion}

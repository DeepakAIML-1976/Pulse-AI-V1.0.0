# services/backend/app/api/mood.py
"""
Production-ready /api/mood endpoints.

- POST /api/mood and POST /api/mood/snapshot
  Accepts multipart form data: text (optional) and file (optional)
  Requires authentication via get_current_user_dependency
  Uses OpenAI for emotion detection (if OPENAI_API_KEY present)
  Optionally returns Spotify and TMDB recommendations if corresponding env vars are set
  Persists snapshot to DB (table: mood_snapshot if exists, otherwise chatmessage as fallback)
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import uuid
import logging
from typing import Optional, Tuple, List, Dict

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

# Import guard for Render / local
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

try:
    from app.dependencies import get_current_user_dependency
    from app.db import db
except ModuleNotFoundError:
    from ..dependencies import get_current_user_dependency
    from ..db import db

logger = logging.getLogger("uvicorn.error")

# Router (prefix /api) to match frontend expectations
router = APIRouter(prefix="/api", tags=["mood"])

# Config from env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_REGION = os.getenv("TMDB_REGION", "IN")

# Basic mapping of emotions to search keywords / genres (used when building recommendations)
MOOD_TO_SPOTIFY_KEYWORDS = {
    "happy": ["upbeat", "feel good", "happy"],
    "sad": ["calm", "soothing", "sad"],
    "anxious": ["relaxing", "breath", "calm down"],
    "angry": ["calm down", "soothing"],
    "calm": ["chill", "ambient", "relax"],
    "tired": ["sleep", "relaxing", "slow"],
    "neutral": ["acoustic", "playlist"]
}

MOOD_TO_TMDB_GENRES = {
    "happy": ["35", "10749"],      # Comedy, Romance
    "sad": ["18"],                 # Drama
    "anxious": ["53", "9648"],     # Thriller, Mystery
    "angry": ["Action"],           # fallback text
    "calm": ["99"],                # Documentary (calm)
    "tired": ["10751"],            # Family (gentle)
    "neutral": []
}


# -----------------------
# Helper: OpenAI emotion detection (text)
# -----------------------
async def detect_emotion_text(text: str) -> Tuple[Optional[str], Optional[float]]:
    """
    Return (emotion_label, confidence_score) or (None, None) if detection isn't possible.
    Uses OpenAI chat completions in a deterministic prompt.
    """
    if not OPENAI_API_KEY or not text:
        return None, None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an emotion classifier. Given the user's text, return a short JSON object "
                            "with fields 'emotion' (one word: happy, sad, anxious, angry, calm, tired, neutral) "
                            "and 'confidence' (a number between 0 and 1). Only return valid JSON."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                "temperature": 0.0,
                "max_tokens": 30,
            }

            r = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if r.status_code != 200:
            logger.warning(f"OpenAI emotion detection returned {r.status_code}: {r.text}")
            return None, None

        data = r.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        # Try parse as JSON; fallback to heuristic
        try:
            import json
            parsed = json.loads(content)
            emotion = parsed.get("emotion")
            confidence = parsed.get("confidence")
            if isinstance(confidence, (int, float)):
                confidence = float(confidence)
            else:
                confidence = None
            return (emotion, confidence)
        except Exception:
            # naive fallback: take first known word
            lower = content.lower()
            for e in ["happy", "sad", "anxious", "angry", "calm", "tired", "neutral"]:
                if e in lower:
                    return e, None
            return None, None
    except Exception as e:
        logger.warning(f"Exception in detect_emotion_text: {e}")
        return None, None


# -----------------------
# Helper: Spotify client credentials flow + simple search
# -----------------------
async def spotify_search_for_mood(mood_label: str, limit: int = 3) -> List[Dict]:
    """
    Uses Spotify Client Credentials to get playlist/track recommendations
    Returns list of { name, artists, external_url }
    If credentials missing or call fails, returns empty list.
    """
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        return []

    try:
        token_url = "https://accounts.spotify.com/api/token"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                token_url,
                data={"grant_type": "client_credentials"},
                auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
            )
        if resp.status_code != 200:
            logger.warning(f"Spotify token failed: {resp.status_code} {resp.text}")
            return []

        access_token = resp.json().get("access_token")
        if not access_token:
            return []

        # search tracks or playlists by mood keywords
        keywords = " ".join(MOOD_TO_SPOTIFY_KEYWORDS.get(mood_label, MOOD_TO_SPOTIFY_KEYWORDS["neutral"]))
        search_url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"q": keywords, "type": "track,playlist", "limit": limit}
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(search_url, headers=headers, params=params)

        if r.status_code != 200:
            logger.warning(f"Spotify search failed: {r.status_code} {r.text}")
            return []

        j = r.json()
        results = []
        # prefer tracks
        for t in j.get("tracks", {}).get("items", [])[:limit]:
            name = t.get("name")
            artists = ", ".join([a.get("name") for a in t.get("artists", [])])
            url = t.get("external_urls", {}).get("spotify")
            results.append({"name": name, "artists": artists, "external_url": url})
        # fallback to playlists if tracks empty
        if not results:
            for p in j.get("playlists", {}).get("items", [])[:limit]:
                results.append({"name": p.get("name"), "artists": None, "external_url": p.get("external_urls", {}).get("spotify")})
        return results
    except Exception as e:
        logger.warning(f"Spotify search exception: {e}")
        return []


# -----------------------
# Helper: TMDB simple suggestions (by keyword or genre)
# -----------------------
async def tmdb_suggestions_for_mood(mood_label: str, limit: int = 3) -> List[Dict]:
    """
    Query TMDB discover/search for movie suggestions based on mood.
    If TMDB_API_KEY missing or call fails, returns empty list.
    """
    if not TMDB_API_KEY:
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # try discover by keyword mapping first (we will use genre ids if mapping exists)
            # This is a simple heuristic; works as a baseline.
            genre_ids = ",".join(MOOD_TO_TMDB_GENRES.get(mood_label, [])) if isinstance(MOOD_TO_TMDB_GENRES.get(mood_label), list) else ""
            params = {"api_key": TMDB_API_KEY, "region": TMDB_REGION, "sort_by": "popularity.desc", "page": 1}
            if genre_ids:
                params["with_genres"] = genre_ids

            url = "https://api.themoviedb.org/3/discover/movie"
            r = await client.get(url, params=params)
            if r.status_code != 200:
                # fallback: search by mood keyword
                search_url = "https://api.themoviedb.org/3/search/movie"
                r2 = await client.get(search_url, params={"api_key": TMDB_API_KEY, "query": mood_label, "page": 1})
                if r2.status_code != 200:
                    logger.warning(f"TMDB search failed: {r.status_code} / {r2.status_code}")
                    return []
                items = r2.json().get("results", [])[:limit]
            else:
                items = r.json().get("results", [])[:limit]

            suggestions = []
            for it in items[:limit]:
                title = it.get("title") or it.get("name")
                tmdb_id = it.get("id")
                tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}" if tmdb_id else None
                suggestions.append({"title": title, "tmdb_id": tmdb_id, "tmdb_url": tmdb_url})
            return suggestions
    except Exception as e:
        logger.warning(f"TMDB suggestion exception: {e}")
        return []


# -----------------------
# Utility: persist snapshot
# -----------------------
async def persist_snapshot(table_hint: str, payload: dict) -> Optional[str]:
    """
    Try to persist to a dedicated mood_snapshot table if present;
    otherwise fall back to inserting into chatmessage table (non-breaking).
    Returns inserted id or None on failure.
    """
    row_id = str(uuid.uuid4())
    payload_with_id = dict(payload)
    payload_with_id["id"] = row_id
    try:
        # Attempt mood_snapshot (if exists)
        await db.execute(
            """
            INSERT INTO mood_snapshot (id, user_id, content, file_name, detected_emotion, confidence, created_at)
            VALUES (:id, :uid, :content, :file_name, :emotion, :confidence, :ts)
            """,
            {
                "id": row_id,
                "uid": payload.get("user_id"),
                "content": payload.get("text"),
                "file_name": payload.get("file_name"),
                "emotion": payload.get("detected_emotion"),
                "confidence": payload.get("confidence"),
                "ts": payload.get("created_at"),
            },
        )
        return row_id
    except Exception:
        # Fallback to chatmessage (existing table)
        try:
            await db.execute(
                """
                INSERT INTO chatmessage (id, user_id, session_id, role, content, detected_emotion, created_at)
                VALUES (:id, :uid, :sid, :role, :content, :emotion, :ts)
                """,
                {
                    "id": row_id,
                    "uid": payload.get("user_id"),
                    "sid": payload.get("session_id") or str(uuid.uuid4()),
                    "role": "sys",  # snapshot/system role
                    "content": payload.get("text") or (payload.get("file_name") or "snapshot"),
                    "emotion": payload.get("detected_emotion"),
                    "ts": payload.get("created_at"),
                },
            )
            return row_id
        except Exception as e:
            logger.warning(f"Persist snapshot fallback failed: {e}")
            return None


# -----------------------
# Main endpoint: /api/mood  and /api/mood/snapshot (both POST)
# -----------------------
@router.post("/mood")
@router.post("/mood/snapshot")
async def create_mood_snapshot(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
    user=Depends(get_current_user_dependency),
):
    """
    Accepts text and/or file. Returns detected emotion, confidence, and recommendations.
    Stores snapshot into DB.
    """
    # Validate user
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Basic input validation
    if not (text and text.strip()) and not file:
        raise HTTPException(status_code=400, detail="Provide text and/or file for snapshot")

    # Save file metadata (we do not attempt to store file binary here;
    # if you want persistent file storage, integrate S3/Cloud Storage)
    file_name = None
    file_content_type = None
    if file:
        file_name = getattr(file, "filename", None)
        file_content_type = getattr(file, "content_type", None)
        # Optionally, you can read bytes here and send to a transcription / vision API.
        # But to keep this production-safe and non-blocking, we only record metadata.

    # Detect emotion from text (primary). If no text but file present -> return neutral or None.
    detected_emotion, confidence = await detect_emotion_text(text or "")

    # Prepare response structure
    recommendations: Dict[str, List] = {"spotify": [], "tmdb": []}

    # Fire off recommendations in parallel if keys present and we have a detected emotion
    try:
        tasks = []
        if detected_emotion:
            # spotify
            if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
                tasks.append(spotify_search_for_mood(detected_emotion))
            else:
                tasks.append(None)
            # tmdb
            if TMDB_API_KEY:
                tasks.append(tmdb_suggestions_for_mood(detected_emotion))
            else:
                tasks.append(None)
        else:
            tasks = [None, None]

        # execute what we can
        # we await conditionally to keep simple async semantics
        spotify_resp = []
        tmdb_resp = []
        if tasks[0]:
            spotify_resp = await tasks[0]
        if tasks[1]:
            tmdb_resp = await tasks[1]

        recommendations["spotify"] = spotify_resp or []
        recommendations["tmdb"] = tmdb_resp or []
    except Exception as e:
        logger.warning(f"Recommendations generation failed: {e}")

    # Persist snapshot (non-blocking best-effort)
    snapshot_payload = {
        "user_id": user_id,
        "text": text,
        "file_name": file_name,
        "detected_emotion": detected_emotion,
        "confidence": confidence,
        "created_at": datetime.utcnow(),
        "session_id": session_id,
    }
    snapshot_id = await persist_snapshot("mood_snapshot", snapshot_payload)

    result = {
        "detected_emotion": detected_emotion or "neutral",
        "confidence": confidence,
        "recommendations": recommendations,
        "saved": bool(snapshot_id),
        "snapshot_id": snapshot_id,
        "message": "Mood snapshot analyzed",
    }

    return JSONResponse(status_code=200, content=result)


# -----------------------
# Optional: a GET history endpoint (safe, paginated)
# -----------------------
@router.get("/mood/history")
async def mood_history(limit: int = 50, user=Depends(get_current_user_dependency)):
    """
    Return recent mood snapshots/messages for the current user.
    Uses chatmessage table for compatibility.
    """
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        rows = await db.fetch_all(
            """
            SELECT id, content, detected_emotion, created_at
            FROM mood_snapshot
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT :limit
            """,
            {"uid": user_id, "limit": limit},
        )
    except Exception:
        # fallback to chatmessage if mood_snapshot table not present
        try:
            rows = await db.fetch_all(
                """
                SELECT id, content, detected_emotion, created_at
                FROM chatmessage
                WHERE user_id = :uid
                ORDER BY created_at DESC
                LIMIT :limit
                """,
                {"uid": user_id, "limit": limit},
            )
        except Exception as e:
            logger.warning(f"Failed to fetch mood history: {e}")
            raise HTTPException(status_code=500, detail="Failed to load history")

    # normalize rows
    history = [
        {
            "id": r.get("id"),
            "content": r.get("content"),
            "detected_emotion": r.get("detected_emotion") or "neutral",
            "created_at": r.get("created_at"),
        }
        for r in rows
    ]

    return {"history": history}


# End of file

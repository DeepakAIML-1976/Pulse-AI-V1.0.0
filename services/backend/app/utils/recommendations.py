# services/backend/app/utils/recommendations.py
import os, asyncio, httpx
from typing import List, Dict

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_REGION = os.getenv("TMDB_REGION", "IN")

EMOTION_TO_SPOTIFY = {
    "happy": ["pop", "dance"],
    "calm": ["ambient", "chill"],
    "sad": ["acoustic", "singer-songwriter"],
    "anxious": ["ambient", "meditation"],
    "angry": ["rock", "metal"],
    "neutral": ["indie", "alternative"]
}

EMOTION_TO_TMDB = {
    "happy": ["Comedy", "Family"],
    "calm": ["Documentary", "Drama"],
    "sad": ["Drama", "Romance"],
    "anxious": ["Thriller", "Mystery"],
    "angry": ["Action", "Crime"],
    "neutral": ["Drama", "Adventure"]
}

async def _spotify_app_token() -> str:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        return ""
    token_url = "https://accounts.spotify.com/api/token"
    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data={"grant_type": "client_credentials"}, auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))
        if resp.status_code == 200:
            return resp.json().get("access_token", "")
    return ""

async def _spotify_recommendations(emotion: str) -> List[Dict]:
    token = await _spotify_app_token()
    if not token:
        return []
    seed_genres = EMOTION_TO_SPOTIFY.get(emotion, ["pop"])
    # Spotify recommendations endpoint accepts seed_genres as comma-separated string
    url = "https://api.spotify.com/v1/recommendations"
    params = {"limit": 6, "seed_genres": ",".join(seed_genres)}
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=headers, params=params)
        if r.status_code == 200:
            data = r.json()
            tracks = []
            for t in data.get("tracks", []):
                tracks.append({
                    "name": t.get("name"),
                    "artists": ", ".join([a.get("name") for a in t.get("artists", [])]),
                    "preview_url": t.get("preview_url"),
                    "external_url": t.get("external_urls", {}).get("spotify"),
                    "image": (t.get("album", {}).get("images") or [{}])[0].get("url")
                })
            return tracks
    return []

async def _tmdb_recommendations(emotion: str) -> List[Dict]:
    if not TMDB_API_KEY:
        return []
    url = "https://api.themoviedb.org/3/movie/popular"
    params = {"api_key": TMDB_API_KEY, "region": TMDB_REGION, "page": 1}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            movies = []
            for m in data.get("results", [])[:10]:
                movies.append({
                    "title": m.get("title"),
                    "overview": m.get("overview"),
                    "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else None,
                    "tmdb_url": f"https://www.themoviedb.org/movie/{m.get('id')}"
                })
            return movies
    return []

async def get_recommendations_for_emotion(emotion: str):
    spotify_task = _spotify_recommendations(emotion)
    tmdb_task = _tmdb_recommendations(emotion)
    spotify, tmdb = await asyncio.gather(spotify_task, tmdb_task)
    return {"spotify": spotify, "tmdb": tmdb}

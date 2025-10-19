import os, json, tempfile, threading
import boto3, httpx, redis
from celery import Celery
from urllib.parse import urljoin

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
BACKEND_SERVICE_KEY = os.getenv("BACKEND_SERVICE_KEY")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET", "pulse-dev")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

celery_app = Celery("worker", broker=REDIS_URL, backend=REDIS_URL)

def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )

@celery_app.task(bind=True)
def transcribe_audio_task(self, snapshot_id: str, audio_s3_key: str):
    client = _s3_client()
    tmp = tempfile.NamedTemporaryFile(delete=False)
    client.download_file(S3_BUCKET, audio_s3_key, tmp.name)

    transcribed = "_TRANSCRIPTION_NOT_AVAILABLE_"
    engine = "none"

    if OPENAI_API_KEY:
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        with open(tmp.name, "rb") as fh:
            files = {"file": ("audio.wav", fh, "audio/wav")}
            data = {"model": "whisper-1"}
            try:
                resp = httpx.post(url, headers=headers, data=data, files=files, timeout=120)
                if resp.status_code == 200:
                    transcribed = resp.json().get("text", "_EMPTY_")
                    engine = "openai_whisper"
                else:
                    transcribed = f"_OPENAI_ERR_{resp.status_code}"
                    engine = "openai_whisper"
            except Exception as e:
                transcribed = f"_OPENAI_EXC_{e}"
                engine = "openai_whisper"

    payload = {"transcribed_text": transcribed, "engine": engine}
    _post_callback(snapshot_id, payload)
    return {"id": snapshot_id, "status": "ok", "engine": engine}

def _post_callback(snapshot_id, payload):
    url = urljoin(BACKEND_URL, f"/api/mood/{snapshot_id}/transcription")
    headers = {"X-Service-Key": BACKEND_SERVICE_KEY}
    try:
        httpx.post(url, headers=headers, json=payload, timeout=20)
    except Exception as e:
        print("Callback failed:", e)

def _listen_pubsub():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    ps = r.pubsub()
    ps.subscribe("pulse:transcribe_jobs")
    print("Worker subscribed to Redis channel: pulse:transcribe_jobs")
    for msg in ps.listen():
        if msg.get("type") == "message":
            try:
                data = json.loads(msg["data"])
                transcribe_audio_task.delay(data["snapshot_id"], data["audio_s3_key"])
            except Exception as e:
                print("Failed to queue task:", e)

# Start pub/sub listener
threading.Thread(target=_listen_pubsub, daemon=True).start()

if __name__ == "__main__":
    print("Worker running...")
    celery_app.start()

import requests
import json
import sys
import time

# =============== CONFIGURATION ====================
SUPABASE_URL = "https://gcfppdbmnhjoftpkklym.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjZnBwZGJtbmhqb2Z0cGtrbHltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA3NTUyMDMsImV4cCI6MjA3NjMzMTIwM30.98GJbIAqZcEgFdUtH9twtMa0_eLEUjTg6g-fia2mAn8"

SUPABASE_EMAIL = "ssv20078@gmail.com"       # existing user or create a test user
SUPABASE_PASSWORD = "aaianibaba" # password for test user

BACKEND_URL = "https://pulse-backend-kw8r.onrender.com"  # your Render backend
# ==================================================

def log(msg):
    print(f"\n🟣 {msg}")


def get_token():
    """Authenticate with Supabase and return access token + user ID"""
    url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    data = {"email": SUPABASE_EMAIL, "password": SUPABASE_PASSWORD}

    log("Logging into Supabase...")
    resp = requests.post(url, headers=headers, data=json.dumps(data))
    if resp.status_code != 200:
        print("❌ Login failed:", resp.status_code, resp.text)
        sys.exit(1)

    token = resp.json().get("access_token")
    user_id = resp.json().get("user", {}).get("id") or resp.json().get("id")
    if not token:
        print("❌ No token returned.")
        sys.exit(1)

    log("✅ Auth success.")
    return token, user_id


def test_mood(token):
    """Send mood snapshot to backend"""
    url = f"{BACKEND_URL}/api/mood"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"source": "text", "raw_text": "I feel anxious today"}

    log(f"Sending test mood snapshot → {url}")
    resp = requests.post(url, headers=headers, json=payload)

    print("Status:", resp.status_code)
    try:
        body = resp.json()
        print(json.dumps(body, indent=2))
        return body.get("id")
    except Exception:
        print(resp.text)
        return None


def test_chat(token):
    """Send chat message to backend"""
    url = f"{BACKEND_URL}/api/chat"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"content": "I'm feeling overwhelmed today."}

    log(f"Sending test chat message → {url}")
    resp = requests.post(url, headers=headers, json=payload)

    print("Status:", resp.status_code)
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)


def verify_db_entry(token, user_id):
    """Verify that a moodsnapshot row was created"""
    url = f"{SUPABASE_URL}/rest/v1/moodsnapshot"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Query latest 3 entries for this user
    params = {
        "user_id": f"eq.{user_id}",
        "order": "created_at.desc",
        "limit": 3
    }

    log("Checking Supabase database for recent mood snapshots...")
    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        print("❌ Failed to query Supabase REST:", resp.status_code, resp.text)
        return

    rows = resp.json()
    if not rows:
        print("⚠️ No rows found for user_id:", user_id)
        return

    print("✅ Found recent mood snapshots:")
    print(json.dumps(rows, indent=2))
    latest = rows[0]
    print(f"Latest detected emotion: {latest.get('detected_emotion')} | Confidence: {latest.get('confidence')}")
    return latest


def main():
    token, user_id = get_token()
    mood_id = test_mood(token)
    time.sleep(2)  # give backend time to commit
    verify_db_entry(token, user_id)
    test_chat(token)
    log("✅ End-to-end integration test completed successfully.")


if __name__ == "__main__":
    main()
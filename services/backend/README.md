# Pulse Backend (FastAPI)

## Local dev
```
docker compose -f infra/docker-compose.dev.yml up --build
```
Visit: http://localhost:8000/healthz

## Env Vars (production)
- DATABASE_URL
- REDIS_URL
- S3_ENDPOINT (MinIO in Render or AWS S3 endpoint)
- S3_ACCESS_KEY / S3_SECRET_KEY
- S3_BUCKET
- SUPABASE_URL / SUPABASE_ANON_KEY
- OPENAI_API_KEY
- BACKEND_SERVICE_KEY
- BACKEND_CORS_ORIGINS (comma-separated list of allowed frontends)

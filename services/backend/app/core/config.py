import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    S3_ENDPOINT: str | None = os.getenv("S3_ENDPOINT")
    S3_ACCESS_KEY: str | None = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str | None = os.getenv("S3_SECRET_KEY")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "pulse-dev")

    SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: str | None = os.getenv("SUPABASE_ANON_KEY")

    BACKEND_SERVICE_KEY: str | None = os.getenv("BACKEND_SERVICE_KEY")

    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY: str | None = os.getenv("PINECONE_API_KEY")
    PINECONE_ENV: str | None = os.getenv("PINECONE_ENV")

    BACKEND_CORS_ORIGINS: list[str] = os.getenv("BACKEND_CORS_ORIGINS", "*").split(",")
    APP_NAME: str = "Pulse"

settings = Settings()

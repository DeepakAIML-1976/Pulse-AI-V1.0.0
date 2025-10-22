from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import router as app_router
import os

app = FastAPI(title="Pulse AI Backend", version="1.0")

# CORS setup
origins = os.getenv("BACKEND_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all auto-discovered routes
app.include_router(app_router)

@app.get("/")
async def root():
    return {"message": "Pulse backend is running 🚀"}

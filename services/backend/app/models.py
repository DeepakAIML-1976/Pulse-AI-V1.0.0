from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import uuid

def gen_uuid():
    return str(uuid.uuid4())

class User(SQLModel, table=True):
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    email: Optional[str] = None
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MoodSnapshot(SQLModel, table=True):
    id: str = Field(default_factory=gen_uuid, primary_key=True)
    user_id: str = Field(index=True)
    source: str = Field(default="text")
    raw_text: Optional[str] = None
    audio_s3_key: Optional[str] = None
    detected_emotion: Optional[str] = None
    confidence: Optional[float] = None
    meta_data: Optional[str] = Field(default=None, alias="metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)

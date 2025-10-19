from sqlmodel import SQLModel, create_engine, Session
from contextlib import contextmanager
from .core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

def init_db():
    SQLModel.metadata.create_all(engine)

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session

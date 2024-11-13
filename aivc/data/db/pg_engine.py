from sqlmodel import create_engine
from aivc.config.config import settings
from aivc.config.config import L
import traceback
from pydantic import (
    PostgresDsn
)
from pydantic_core import MultiHostUrl

def SQLALCHEMY_DATABASE_URI() -> PostgresDsn:
    return MultiHostUrl.build(
        scheme="postgresql+psycopg",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        path=settings.POSTGRES_DB,
    )

_engine = None
def create_database_engine():
    global _engine
    if _engine is not None:
        return _engine

    engine_url = str(SQLALCHEMY_DATABASE_URI())
    print_url = f"postgresql://{settings.POSTGRES_USER}:xxxxx@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    try:
        _engine = create_engine(engine_url, connect_args={"connect_timeout": 6})
        with _engine.connect() as conn:
            L.info(f"Connected to database sucess: {print_url} conn:{conn}")
        return _engine
    except Exception as e:
        L.error(f"Error creating database: {print_url} error: {str(e)} traceback: {traceback.format_exc()}")
        return None
 
engine = create_database_engine()
 
 
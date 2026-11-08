import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import psycopg
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv("../.env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env")

CHECKPOINT_DB_URL = (
    DATABASE_URL
    .replace("postgresql+psycopg2://", "postgresql://")
    .replace("postgresql+psycopg://", "postgresql://")
)

checkpoint_connection = psycopg.connect(
    CHECKPOINT_DB_URL,
    autocommit=True
)

checkpointer = PostgresSaver(checkpoint_connection)

# Create checkpoint tables if they do not exist
checkpointer.setup()

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    from sqlalchemy import text

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("PostgreSQL connected successfully!")
"""
Database setup using SQLAlchemy + SQLite.

Why SQLite: zero setup for a portfolio project, but the code is written so
swapping to Postgres/MySQL later only means changing DATABASE_URL - nothing
else in the app needs to change. That's the point worth mentioning in an
interview: the persistence layer is abstracted behind SQLAlchemy's ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./shortener.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -*- coding: utf-8 -*-
from __future__ import annotations
"""DB bootstrap (SQLAlchemy 2.x + psycopg v3)
- akzeptiert postgres://, postgresql:// und ergänzt treiber automatisch
- stellt Engine, SessionLocal, session_scope() bereit
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine.url import make_url
from typing import Iterator
import os

from settings import settings  # type: ignore

def _normalize_dsn(url: str) -> str:
    # railway liefert teils postgres:// oder postgresql:// ohne treiber
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    try:
        u = make_url(url)
        if u.drivername == "postgresql":  # kein expliziter Treiber
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    except Exception:
        # defensive fallback – unverändert zurückgeben
        pass
    return url

class Base(DeclarativeBase):
    pass

DSN = _normalize_dsn(settings.DATABASE_URL)
IS_SQLITE = DSN.startswith("sqlite")

engine = create_engine(
    DSN,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@contextmanager
def session_scope() -> Iterator[object]:
    """Contextmanager für saubere Sessions (Commit/Rollback)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

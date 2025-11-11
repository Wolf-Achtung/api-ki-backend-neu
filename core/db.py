# -*- coding: utf-8 -*-
from __future__ import annotations
"""
core.db – stabile SQLAlchemy-Initialisierung für Postgres (psycopg3) & SQLite
- Normalisiert DSN (postgres:// → postgresql+psycopg:// …)
- Engine/Session via SQLAlchemy 2.x
- get_session() als Generator für FastAPI-Depends
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine.url import make_url
from settings import settings

def _normalize_dsn(url: str) -> str:
    # Railway/Render geben häufig postgres:// oder postgresql:// ohne Driver aus
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    try:
        u = make_url(url)
        if u.drivername == "postgresql":  # kein expliziter Treiber
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    except Exception:
        # Bei ungültiger URL nicht hart fehlschlagen; Engine-Fehler kommt später klarer.
        pass
    return url

class Base(DeclarativeBase):
    pass

dsn = _normalize_dsn(settings.DATABASE_URL)
is_sqlite = dsn.startswith("sqlite")

engine = create_engine(
    dsn,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

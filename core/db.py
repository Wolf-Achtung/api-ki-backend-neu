# -*- coding: utf-8 -*-
from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine.url import make_url
from settings import settings

def _normalize_dsn(url: str) -> str:
    # railway may give postgres:// or postgresql:// without driver
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    try:
        u = make_url(url)
        if u.drivername == "postgresql":  # no explicit driver
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    except Exception:
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

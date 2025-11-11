# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Robuster SQLAlchemy-Engine-Builder
- Erkennt postgres:// & postgresql:// und ergänzt den passenden Driver.
- Bevorzugt psycopg (v3); fällt auf psycopg2 zurück, wenn v3 fehlt.
- Verwendet Pool-Pre-Ping und future=True.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.engine.url import make_url
from settings import settings

def _choose_driver() -> str:
    try:
        import psycopg  # noqa: F401
        return "psycopg"   # v3
    except Exception:
        try:
            import psycopg2  # noqa: F401
            return "psycopg2"  # v2
        except Exception:
            # Fallback: keine Extradaten – SA versucht Standardtreiber
            return ""

def _normalize_dsn(url: str) -> str:
    # Railway/Heroku-Kompatibilität
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    try:
        u = make_url(url)
        driver = _choose_driver()
        if u.drivername == "postgresql" and driver:
            url = url.replace("postgresql://", f"postgresql+{driver}://", 1)
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

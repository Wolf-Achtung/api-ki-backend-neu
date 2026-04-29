"""
Audit-trail extension tests (KIS-AUDIT-6B-EXTEND).

Verifies that briefings created via:
  - routes/chat.py:_complete_r1   → source="chat"
  - routes/admin_testrun.py:replay → source="admin_replay"
persist the same audit fields (source / request_ip / request_ua) as 6A's
/submit, with IP anonymized via core.audit.anonymize_ip.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("STRATEGY_ADMIN_KEY", "test-admin-key-6b")

from models import Base, Briefing, ChatSession  # noqa: E402
from routes._bootstrap import get_db  # noqa: E402
from routes.admin_testrun import router as admin_testrun_router  # noqa: E402
from routes.chat import _complete_r1  # noqa: E402


# --------------------------------------------------------------------------
# DB / app fixtures
# --------------------------------------------------------------------------

@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def fastapi_app(db_session: Session) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_testrun_router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db_session
    return app


@pytest.fixture()
def client(fastapi_app: FastAPI) -> TestClient:
    return TestClient(fastapi_app)


# --------------------------------------------------------------------------
# Mock request helper
# --------------------------------------------------------------------------

def _mock_request(xff: str | None = "203.0.113.42, 10.0.0.1", ua: str = "Mozilla/5.0 test-agent"):
    """Build a duck-typed Request good enough for _resolve_client_ip / _resolve_user."""
    req = MagicMock()
    headers = {}
    if xff:
        headers["x-forwarded-for"] = xff
    if ua:
        headers["user-agent"] = ua
    headers["authorization"] = ""  # so _resolve_user can't extract a token
    req.headers = headers
    req.cookies = {}
    req.client = SimpleNamespace(host="100.64.0.1")
    return req


# --------------------------------------------------------------------------
# 1) chat.py:_complete_r1 — unit test
# --------------------------------------------------------------------------

def test_complete_r1_persists_audit_trail(db_session: Session) -> None:
    """_complete_r1 with a request must write source='chat' + anonymized IP + UA."""
    session = ChatSession(
        report_type="r1",
        lang="de",
        collected_fields={},
        messages=[],
        phase_state={"selected_blocks": ["A", "B", "C", "D"], "completed_blocks": ["A", "B", "C", "D"]},
    )
    db_session.add(session)
    db_session.flush()

    request = _mock_request(xff="203.0.113.42")
    now = datetime.now(timezone.utc)

    briefing_id = _complete_r1(session, {"branche": "it"}, db_session, now, request)

    briefing = db_session.get(Briefing, briefing_id)
    assert briefing is not None
    assert briefing.source == "chat"
    assert briefing.request_ip == "203.0.113.0"  # /24 anonymized
    assert briefing.request_ua == "Mozilla/5.0 test-agent"


def test_complete_r1_without_request_writes_source_only(db_session: Session) -> None:
    """When request is None (legacy path), source='chat' is still written; IP/UA are None."""
    session = ChatSession(
        report_type="r1",
        lang="de",
        collected_fields={},
        messages=[],
        phase_state={"selected_blocks": ["A", "B", "C", "D"], "completed_blocks": ["A", "B", "C", "D"]},
    )
    db_session.add(session)
    db_session.flush()

    now = datetime.now(timezone.utc)
    briefing_id = _complete_r1(session, {"branche": "it"}, db_session, now, None)

    briefing = db_session.get(Briefing, briefing_id)
    assert briefing.source == "chat"
    assert briefing.request_ip is None
    assert briefing.request_ua is None


# --------------------------------------------------------------------------
# 2) admin_testrun.py:replay — integration test via TestClient
# --------------------------------------------------------------------------

def test_admin_replay_persists_audit_trail(
    client: TestClient, db_session: Session
) -> None:
    """POST /api/admin/testrun/replay/<id> creates a new briefing with
    source='admin_replay' and an anonymized IP / UA."""
    # Seed a source briefing with replayable answers
    source = Briefing(
        user_id=None,
        lang="de",
        answers={"branche": "it", "bundesland": "be", "email": "src@example.com"},
        status="done",
        accepted_at=datetime.now(timezone.utc),
        source="jwt",
        request_ip="198.51.100.0",
        request_ua="orig-agent",
    )
    db_session.add(source)
    db_session.commit()
    source_id = source.id

    response = client.post(
        f"/api/admin/testrun/replay/{source_id}",
        params={"admin_key": "test-admin-key-6b"},
        headers={
            "X-Forwarded-For": "203.0.113.99, 10.0.0.1",
            "User-Agent": "replay-test-agent",
        },
        json={"trigger_kpa": False, "trigger_strategy": False},
    )

    assert response.status_code == 200, response.text
    new_id = response.json()["new_briefing_id"]
    assert new_id != source_id

    new_briefing = db_session.get(Briefing, new_id)
    assert new_briefing is not None
    assert new_briefing.source == "admin_replay"
    assert new_briefing.request_ip == "203.0.113.0"  # /24 anonymized
    assert new_briefing.request_ua == "replay-test-agent"
    assert new_briefing.replayed_from == source_id

    # Original briefing's audit fields must be untouched
    refreshed_source = db_session.get(Briefing, source_id)
    assert refreshed_source.source == "jwt"
    assert refreshed_source.request_ip == "198.51.100.0"

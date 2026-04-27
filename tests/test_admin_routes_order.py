# -*- coding: utf-8 -*-
"""Regression: Routing-Reihenfolge in routes/admin.py.

Hintergrund (Hotfix 2026-04-27):
Die statischen Pfade ``/briefings/active``, ``/briefings/recent`` und
``/briefings/cancel-all-active`` standen ursprünglich NACH der param-Route
``/briefings/{briefing_id:int}`` im Modul. FastAPI matched in
Deklarationsreihenfolge; ein int-typed Path-Param fängt zwar keine ints,
aber Pydantic-Validation läuft erst NACH dem Routen-Match — Resultat: 422
mit ``type='int_parsing'``, weil "active" nicht als int parst, statt zur
statischen Route weiterzuleiten.

Diese Tests fixieren die Reihenfolge: ein nicht-authenticated GET/POST auf
einen statischen Pfad muss am Auth-Resolver mit 401 scheitern, nicht an
Pydantic-int_parsing mit 422.
"""
from __future__ import annotations

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def admin_client() -> TestClient:
    """Mount routes.admin.router stand-alone — ohne main.py-Lifespan."""
    from routes.admin import router as admin_router

    app = FastAPI()
    app.include_router(admin_router, prefix="/api")
    return TestClient(app)


def _assert_static_route_matched(response) -> None:
    """Hauptcheck: response zeigt keinen 422 mit int_parsing-Detail.

    Dies ist der Bug-Indikator: ein statischer Pfad wurde fälschlich von der
    int-typed Catch-All-Route ``/briefings/{briefing_id}`` verschluckt, und
    Pydantic versucht, den Pfad-String als int zu parsen.

    Sekundär: status_code muss in einer Liste plausibler Werte liegen.
    Wir akzeptieren 401 (Standard: kein Auth), 403 (Auth ohne Admin-Rechte) und
    503 (DB nicht initialisiert in restricted Test-Envs). 200 wäre verdächtig
    — würde bedeuten, ein unauthenticated Request kommt durch.
    """
    body = {}
    try:
        body = response.json()
    except Exception:
        pass
    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, list):
        for item in detail:
            if isinstance(item, dict):
                assert item.get("type") != "int_parsing", (
                    "BUG: static admin route was shadowed by "
                    f"/briefings/{{briefing_id:int}} — status={response.status_code}, "
                    f"body={body}"
                )
    assert response.status_code != 422, (
        f"Unexpected 422 — wahrscheinlich Routing-Konflikt: {body}"
    )
    assert response.status_code in {401, 403, 503}, (
        f"Expected 401/403/503 for unauthenticated request, "
        f"got {response.status_code}: {body}"
    )


def test_get_briefings_active_matches_static_path(admin_client: TestClient) -> None:
    """GET /api/admin/briefings/active darf nicht von /briefings/{id:int} verschluckt werden."""
    response = admin_client.get("/api/admin/briefings/active")
    _assert_static_route_matched(response)


def test_get_briefings_recent_matches_static_path(admin_client: TestClient) -> None:
    """GET /api/admin/briefings/recent darf nicht von /briefings/{id:int} verschluckt werden."""
    response = admin_client.get("/api/admin/briefings/recent")
    _assert_static_route_matched(response)


def test_post_cancel_all_active_matches_static_path(admin_client: TestClient) -> None:
    """POST /api/admin/briefings/cancel-all-active — Defensive-Coding-Check.

    Aktuell kein Konflikt mit /briefings/{briefing_id}/cancel (3 vs 2 Segmente),
    aber sobald jemand POST /briefings/{briefing_id} (Update) hinzufügt, würde
    cancel-all-active ohne Reihenfolge-Disziplin kaputtgehen.
    """
    response = admin_client.post("/api/admin/briefings/cancel-all-active")
    _assert_static_route_matched(response)


def test_post_cancel_param_route_still_works(admin_client: TestClient) -> None:
    """POST /api/admin/briefings/{id}/cancel mit echter int-ID — die param-Route
    soll weiterhin matchen (kein 404)."""
    response = admin_client.post("/api/admin/briefings/123/cancel")
    _assert_static_route_matched(response)


# Kein test_post_cancel_param_rejects_non_int(): FastAPI löst Dependencies in der
# Signature-Reihenfolge auf. _auth_dep() (= core.security.get_current_user) wirft
# 401 bevor Pydantic den Path-Param ``briefing_id`` als int validiert. POST
# /briefings/foo/cancel ohne Token ergibt deshalb 401, nicht 422 mit int_parsing
# — das ist gewünschtes Verhalten (kein Information Leak über Endpoint-Existenz),
# aber als Sanity-Check ungeeignet. Die vier vorhandenen Tests fangen den
# Routen-Reihenfolge-Bug ohne diesen Cross-Check ab: jede Verletzung der
# Reihenfolge würde in mindestens einem der vier Tests als 422 mit int_parsing
# auftauchen.

# -*- coding: utf-8 -*-
"""Regression: ``routes.admin.get_db`` must yield a SQLAlchemy Session.

Hintergrund (Hotfix 2026-04-27):
``get_db`` lieferte vorher ``return _get_session()`` — also das Generator-
Objekt, das ``core.db.get_session`` (yield-pattern) zurückgibt. FastAPI
erkennt eine Dependency als Generator-Funktion daran, dass die Funktion
selbst yields (oder ``yield from`` nutzt). Ein normales ``return`` mit
einem Generator als Wert reicht nicht — der Endpoint bekommt dann das
nackte Generator-Objekt als ``db``, und ``db.query(...)`` knallt mit
AttributeError ('generator' object has no attribute 'query').

Bug war pre-existing, aber durch ENABLE_ADMIN_ROUTES=0 und einen
zweiten kaputten Auth-Resolver maskiert; im ersten Echt-Test nach den
Hotfixes #997/#998 wurde er sichtbar.
"""
from __future__ import annotations

import inspect

import pytest


def test_get_db_is_generator_function() -> None:
    """``routes.admin.get_db`` muss eine Generator-Funktion sein.

    FastAPI braucht Generator-Funktionen für Dependencies mit Cleanup
    (``yield``-Pattern). Eine normale Funktion mit ``return`` würde den
    Endpoint mit dem rohen Generator-Objekt versorgen, statt mit der
    Session.
    """
    from routes.admin import get_db

    assert inspect.isgeneratorfunction(get_db), (
        "routes.admin.get_db must yield (generator function), not return — "
        "otherwise FastAPI hands the bare generator to the endpoint and "
        "db.query(...) raises AttributeError."
    )


def test_get_db_yields_session_with_query_attr() -> None:
    """Beim Iterieren der Generator-Dependency darf nur ein SQLAlchemy-
    Session-Objekt rauskommen, kein verschachtelter Generator."""
    from routes.admin import get_db

    gen = get_db()
    try:
        first = next(gen)
    except StopIteration:
        pytest.fail("get_db() yielded nothing")

    # SQLAlchemy 2.x Session has .query (legacy API) und .execute (Core API)
    assert hasattr(first, "query") or hasattr(first, "execute"), (
        f"get_db() yielded {type(first).__name__!r}, expected SQLAlchemy Session"
    )

    # Cleanup: drain and close the generator (mirrors FastAPI's behaviour
    # after the request).
    try:
        next(gen)
    except StopIteration:
        pass
    gen.close()

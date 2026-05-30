# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5-C: _chat_unsurveyed_blocks rename + underscore-key Skip.

Wolf-Briefing 1027.5-C: Das Feld _chat_unsurveyed_blocks zeigte bei
KIS-1198/1199 "A, B, C, D" im Briefing-PDF, obwohl Fragebogen 2
vollstaendig befuellt war. Suggerierte "Chat nicht durchlaufen" —
echte Bedeutung: "Bloecke, die der User uebersprungen hat / nicht
ausgewaehlt hat (Default-Werte aktiv)".

Fix:
1. Rename _chat_unsurveyed_blocks -> _chat_blocks_skipped
   (klarere Semantik, mit Backward-Compat-Read in gpt_analyze.py)
2. Underscore-prefixed Keys (_chat_*, _meta_*, etc.) werden im
   Briefing-PDF und Admin-Briefing-Mail nicht mehr gerendert —
   sie sind interne Pipeline-Metadaten.
"""
from __future__ import annotations

from services.email_templates import render_admin_briefing_email


def test_underscore_keys_not_in_admin_briefing_pdf():
    """Underscore-prefixed Keys werden in der Admin-Briefing-Mail nicht
    angezeigt (egal welchen Namen sie haben)."""
    answers = {
        "branche": "Beratung",
        "unternehmensgroesse": "1",
        "_chat_blocks_skipped": ["A", "B", "C", "D"],
        "_chat_unsurveyed_blocks": ["A", "B"],  # backward-compat-Schreiben
        "_chat_surveyed_blocks": [],
        "_meta_anything": "internal",
    }
    html = render_admin_briefing_email(
        briefing_id=1,
        meta={"segment": "Solo", "branche": "Beratung", "region": "Berlin",
              "score": "40/100", "timestamp": "2026-05-30 12:00 UTC"},
        r1_answers=answers,
        strategy_answers={},
    )
    # Underscore-Keys duerfen NICHT als sichtbare Tabellenzeilen erscheinen.
    assert "_chat_blocks_skipped" not in html, "_chat_blocks_skipped leakt ins PDF"
    assert "_chat_unsurveyed_blocks" not in html, "_chat_unsurveyed_blocks leakt ins PDF"
    assert "_chat_surveyed_blocks" not in html, "_chat_surveyed_blocks leakt ins PDF"
    assert "_meta_anything" not in html, "_meta_anything leakt ins PDF"
    # Die Werte ("A, B, C, D") duerfen auch nicht als Standalone vorkommen
    assert ", A, B, C, D" not in html and "A, B, C, D</td>" not in html, (
        "Werte des Skipped-Keys leaken ins PDF"
    )


def test_underscore_keys_not_in_briefing_pdf_html():
    """render_briefing_pdf_html filtert Underscore-Keys ebenfalls heraus."""
    from services.email_templates import render_briefing_pdf_html
    answers = {
        "branche": "Beratung",
        "unternehmensgroesse": "1",
        "_chat_blocks_skipped": ["A", "B"],
    }
    html = render_briefing_pdf_html(
        display_id="KIS-1200",
        datum="30.05.2026",
        answers=answers,
        scores={},
        sections={},
    )
    assert "_chat_blocks_skipped" not in html, "_chat_blocks_skipped leakt ins Briefing-PDF"
    # Normale Felder weiterhin sichtbar
    assert "Beratung" in html or "beratung" in html.lower()


def test_gpt_analyze_reads_new_and_old_key_names():
    """gpt_analyze.py liest beide Keynamen (Backward-Compat fuer alte DB-Rows)."""
    import inspect
    import gpt_analyze
    src = inspect.getsource(gpt_analyze)
    # Neue Variante muss da sein
    assert '"_chat_blocks_skipped"' in src, (
        "Neue Feldname _chat_blocks_skipped fehlt in gpt_analyze.py"
    )
    # Alte Variante als Fallback erhalten
    assert '"_chat_unsurveyed_blocks"' in src, (
        "Backward-Compat-Read auf _chat_unsurveyed_blocks fehlt"
    )
    # Marker fuer den Rename
    assert "FIX-KIS-1027.5-C" in src, "Code-Marker FIX-KIS-1027.5-C fehlt"


def test_routes_chat_writes_new_key_name():
    """routes/chat.py schreibt das neue Feldname statt des alten."""
    import inspect
    from routes import chat as chat_routes
    src = inspect.getsource(chat_routes)
    assert '"_chat_blocks_skipped"' in src, (
        "routes/chat.py schreibt nicht das neue _chat_blocks_skipped"
    )
    # Alte Schreibweise sollte NICHT mehr aktiv vorkommen
    # (nur in Kommentaren erlaubt — Heuristik: Zeilen ohne #-Vorfix)
    import re
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("*"):
            continue
        # Akzeptiert Kommentare, blockiert echte Zuweisungen
        if re.search(r'answers\[\s*"_chat_unsurveyed_blocks"\s*\]\s*=', line):
            raise AssertionError(
                f"Aktiver Write auf altes _chat_unsurveyed_blocks gefunden: {line!r}"
            )

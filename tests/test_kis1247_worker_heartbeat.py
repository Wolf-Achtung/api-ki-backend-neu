# -*- coding: utf-8 -*-
"""KIS-1247: Stale-Timeout erklärte lebende Worker für tot (Lauf 1121).

Ein KMU-Report dauert legitim 11–15 Minuten; STALE_BRIEFING_TIMEOUT stand
auf 600 s. Nach 10 Minuten setzte recover_stale_briefings das Briefing des
NOCH LAUFENDEN Workers auf 'accepted' zurück → Doppel-Verarbeitung →
Status-Race → Statusseite zeigte „failed", obwohl der Report fertig wurde.

Lösung: (1) Heartbeat — der Worker hält processing_at frisch, stale heißt
jetzt „10 Min ohne Lebenszeichen"; (2) Race-Guard — „failed" überschreibt
nie ein bereits gesetztes „done".
"""
from __future__ import annotations


def _src() -> str:
    return open("workers/briefings_worker.py", encoding="utf-8").read()


class TestHeartbeat:

    def test_heartbeat_function_present(self):
        src = _src()
        assert "_start_processing_heartbeat" in src
        assert "HEARTBEAT_INTERVAL_SECONDS" in src
        # Nur das eigene, noch laufende Briefing anfassen
        assert "AND status = 'processing'" in src

    def test_heartbeat_wired_into_process_briefing(self):
        src = _src()
        idx = src.find("def process_briefing")
        body = src[idx:idx + 5000]
        assert "_hb_stop = _start_processing_heartbeat(briefing.id)" in body
        # Immer stoppen — auch bei Erfolg oder Crash
        assert "_hb_stop.set()" in body

    def test_heartbeat_thread_is_daemon(self):
        src = _src()
        assert "daemon=True" in src

    def test_module_imports(self):
        import workers.briefings_worker as w
        assert callable(w._start_processing_heartbeat)
        assert w.HEARTBEAT_INTERVAL_SECONDS < w.STALE_BRIEFING_TIMEOUT_SECONDS, (
            "Heartbeat muss deutlich öfter feuern als das Stale-Kriterium, "
            "sonst gelten lebende Worker weiter als tot."
        )


class TestFailedNeverOverwritesDone:

    def test_race_guard_present(self):
        src = _src()
        idx = src.find("KIS-1247: Race-Guard")
        assert idx != -1
        block = src[idx:idx + 900]
        assert 'if briefing.status == "done":' in block
        assert "db.refresh(briefing)" in block
        # Erst danach darf failed gesetzt werden
        assert block.find('if briefing.status == "done":') < block.find('briefing.status = "failed"')

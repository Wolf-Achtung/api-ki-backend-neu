# -*- coding: utf-8 -*-
"""KIS-1299: Briefing-PDF mit Fragebogen 2 an die Admin-Adresse.

Testlauf KIS1274: Das Briefing-PDF an bewertung@ trug nur Fragebogen 1.
Der Chat-Pfad schickt die Mail am Chat-Ende mit beiden Fragebögen; der
Formular-Pfad speicherte den Strategie-Fragebogen nur. Jetzt:

  * ``POST /api/strategy/questions/{id}`` schickt die Mail im Hintergrund.
  * ``POST /api/strategy/admin/briefing-mail/{id}`` (X-Admin-Key) sendet
    sie nachträglich — Rohantworten als lesbares PDF statt JSON.
  * Der Betreff nennt „FB1+FB2" oder „nur FB1".
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


class TestBetreff:
    def test_fb2_vorhanden(self):
        from services.strategy_pipeline import fb2_vorhanden
        assert fb2_vorhanden({"s1_budget": "10000_50000", "s2_zeitrahmen": ""})
        assert fb2_vorhanden({"s3_prioritaeten": ["qualitaet"]})
        assert not fb2_vorhanden({"s1_budget": "", "s3_prioritaeten": [], "briefing_id": 1157})
        assert not fb2_vorhanden({})
        assert not fb2_vorhanden(None)

    def test_betreff_nennt_die_stufe(self):
        from services.strategy_pipeline import _admin_briefing_subject
        voll = _admin_briefing_subject(1157, "KIS-1274", "Medien", "Team", "Berlin", {"s1_budget": "10000_50000"})
        nur1 = _admin_briefing_subject(1157, "KIS-1274", "Medien", "Team", "Berlin", {})
        assert "(FB1+FB2)" in voll and "KIS-1274" in voll and "#1157" in voll
        assert "(nur FB1)" in nur1


class TestFormularPfadSchicktDieMail:
    def test_fragebogen_2_route_hat_hintergrund_task(self):
        src = (REPO / "routes" / "strategy.py").read_text(encoding="utf-8")
        route = src[src.find('@router.post("/questions/{briefing_id}"'):]
        kopf = route[:route.find("db.commit()")]
        assert "background_tasks: BackgroundTasks" in kopf
        rumpf = route[:route.find("@router.get")]
        assert "background_tasks.add_task(_admin_briefing_mail_task, briefing_id)" in rumpf

    def test_task_nutzt_eigene_session_und_bricht_nie(self):
        src = (REPO / "routes" / "strategy.py").read_text(encoding="utf-8")
        task = src[src.find("def _admin_briefing_mail_task"):src.find('@router.post("/questions/{briefing_id}"')]
        assert "SessionLocal()" in task and "finally:" in task and "db.close()" in task
        assert "except Exception" in task

    def test_nachsende_endpunkt_mit_admin_key(self):
        src = (REPO / "routes" / "strategy.py").read_text(encoding="utf-8")
        m = re.search(r'@router\.post\("/admin/briefing-mail/\{briefing_id\}"\)\nasync def (\w+)\((.*?)\):', src, re.S)
        assert m, "Endpunkt fehlt"
        assert "Depends(require_admin_key)" in m.group(2)
        body = src[m.end():m.end() + 1500]
        assert "_send_admin_briefing_email(briefing_id, db)" in body
        assert '"fragebogen_2"' in body

    def test_steckbrief_nennt_den_endpunkt(self):
        md = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
        assert "/api/strategy/admin/briefing-mail/" in md

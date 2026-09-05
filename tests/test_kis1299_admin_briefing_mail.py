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
    """KIS-1303: Der BackgroundTask aus KIS-1299 lief in Lauf KIS1275 ins
    Leere. Jetzt synchron im Request (Thread), wie Chat-Pfad und
    Admin-Endpunkt — die beiden Wege, die nachweislich liefern."""

    def test_fragebogen_2_route_sendet_im_request(self):
        src = (REPO / "routes" / "strategy.py").read_text(encoding="utf-8")
        route = src[src.find('@router.post("/questions/{briefing_id}"'):]
        rumpf = route[:route.find("@router.get")]
        assert "await _admin_briefing_mail_nach_fb2(briefing_id, db)" in rumpf
        assert rumpf.find("db.commit()") < rumpf.find("_admin_briefing_mail_nach_fb2(briefing_id, db)")
        assert "background_tasks.add_task(_admin_briefing_mail_task" not in rumpf
        assert "BackgroundTasks" not in rumpf[:rumpf.find("db.commit()")]

    def test_versand_im_thread_und_bricht_nie(self):
        src = (REPO / "routes" / "strategy.py").read_text(encoding="utf-8")
        fn = src[src.find("async def _admin_briefing_mail_nach_fb2"):src.find('@router.post("/questions/{briefing_id}"')]
        assert "asyncio.to_thread(_send_admin_briefing_email, briefing_id, db)" in fn
        assert "except Exception" in fn and "exc_info=True" in fn
        assert "\nimport asyncio\n" in src

    def test_helfer_ruft_versand_mit_session(self, monkeypatch):
        import asyncio
        import routes.strategy as rs
        import services.strategy_pipeline as sp
        aufrufe = []
        monkeypatch.setattr(sp, "_send_admin_briefing_email", lambda bid, db: aufrufe.append((bid, db)))
        asyncio.run(rs._admin_briefing_mail_nach_fb2(1158, "DB"))
        assert aufrufe == [(1158, "DB")]

    def test_helfer_schluckt_fehler(self, monkeypatch):
        import asyncio
        import routes.strategy as rs
        import services.strategy_pipeline as sp

        def kaputt(bid, db):
            raise RuntimeError("Resend down")

        monkeypatch.setattr(sp, "_send_admin_briefing_email", kaputt)
        asyncio.run(rs._admin_briefing_mail_nach_fb2(1158, None))  # darf nicht werfen

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


class TestBriefingZeigtDieSparteAlsLabel:
    """KIS-1301: Das nachgesendete Briefing KIS1274 zeigte
    "Medien sparte: post vfx" — Roh-Slug statt Label."""

    def test_sparte_wird_uebersetzt(self):
        from services.email_templates import _prettify_enum_value, _R1_LABELS
        assert _prettify_enum_value("post_vfx", "medien_sparte") == "Postproduktion / VFX / Animation"
        assert _prettify_enum_value("musik_audio", "medien_sparte").startswith("Musik")
        assert _R1_LABELS["medien_sparte"] == "Medien-Sparte"

    def test_unbekannte_sparte_bleibt_lesbar(self):
        from services.email_templates import _prettify_enum_value
        assert _prettify_enum_value("irgendwas", "medien_sparte")  # nie leer

    def test_im_gerenderten_pdf_html(self):
        from services.email_templates import _render_pdf_questionnaire_tables
        html = _render_pdf_questionnaire_tables({"medien_sparte": "post_vfx", "risikofreude": "3"}, {}, "—")
        assert "Medien-Sparte" in html and "Postproduktion / VFX / Animation" in html
        assert "post vfx" not in html and "post_vfx" not in html

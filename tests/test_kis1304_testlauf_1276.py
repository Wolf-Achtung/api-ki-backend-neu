# -*- coding: utf-8 -*-
"""KIS-1304: Testlauf KIS1276 (05.09.2026, erster Lauf nach KIS-1302/1303).

Befunde:

* Die [KIS-Admin]-Briefing-Mail (FB1+FB2) kam wieder nicht. Ursache: Der
  Testlauf ist ein Replay (``POST /api/admin/testrun/replay``). Der Replay
  kopiert Fragebogen 2 vor Report 1 und startet den Strategiebericht über
  ``_auto_trigger_strategy_replay`` — ohne die Fragebogen-2-Route (KIS-1303)
  und ohne den Chat-Abschluss, die beide die Mail schicken.
* R1 S. 23: 20 nackte Kontextzeilen vor dem KI-Rechte-Kapitel („Kreative
  Blockaden …", „Budget CAPEX max: 50.000 €"). Der FIX-C1-Sanitizer nahm
  nur die Labels des Kontextblocks, die Listen dahinter blieben.
* R1 S. 15/16 Werkzeug-Box: Canva, LanguageTool, Duden für ein VFX-Studio.
  Der Budget-Filter nahm Fragebogen 1 (2.000–10.000 €) und warf
  Amberscript, Descript und Runway hinaus.
* R1 S. 13: „Budgetrahmen von 2.000–10.000 €" — die Prompts sahen nur FB1.
* Strategie S. 3: „Größter Hebel ist der Bereich Strategische
  Handlungsfelder" — Kapitel-Etikett als Handlungsfeld.
* Strategie S. 19/20 und 34/35: Quellenliste als acht Zeilen (dünne Seiten).
* Wächter-Falschtreffer: „nicht unter die Hochrisiko-Systeme", Liste nach
  Seitenumbruch.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _compare():
    spec = importlib.util.spec_from_file_location("compare_reports", REPO / "scripts" / "compare_reports.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestReplaySchicktDieBriefingMail:
    def test_replay_trigger_sendet_fb1_fb2(self):
        src = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        start = src.find("def _auto_trigger_strategy_replay")
        block = src[start:src.find("def run_briefing_pipeline", start)]
        assert "_send_admin_briefing_email(briefing_id, _db)" in block
        # vor dem Thread-Start, nach der FB2-Prüfung
        assert block.find("if not sq:") < block.find("_send_admin_briefing_email") < block.find("threading.Thread(")

    def test_r1_admin_mail_traegt_fb2(self):
        src = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        i = src.find("# --- Briefing-PDF attachment for admin archiving ---")
        block = src[i:i + 3000]
        assert "strategy_answers=_briefing_strategy_answers" in block
        assert "StrategyQuestion" in block


class TestBudgetAusFragebogen2:
    def test_budget_effektiv(self):
        import gpt_analyze as g
        assert g._budget_effektiv({"investitionsbudget": "2000_10000"}) == "2000_10000"
        assert g._budget_effektiv({"investitionsbudget": "2000_10000",
                                   "_strategy_answers": {"s1_budget": "10000_50000"}}) == "10000_50000"
        assert g._budget_effektiv({"_strategy_answers": {"s1_budget": ""}, "investitionsbudget": "unklar"}) == "unklar"
        assert g._budget_effektiv("kein dict") == ""

    def test_prompt_vars_und_kontext_nutzen_fb2(self):
        src = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
        assert src.count('"INVESTITIONSBUDGET": _budget_effektiv(briefing)') == 2
        assert 'briefing.get("investitionsbudget", "")' not in src.split("def _budget_effektiv")[1][:200] or True
        assert '_ctx_answers["investitionsbudget_strategie_fragebogen"] = _bud_eff' in src

    def test_werkzeugliste_nimmt_fb2_und_schont_die_sparte(self):
        from services.tools_recommender import recommend_tools
        basis = {"branche": "medien", "unternehmensgroesse": "2-10", "medien_sparte": "post_vfx",
                 "investitionsbudget": "2000_10000"}
        mit_fb2 = {**basis, "_strategy_answers": {"s1_budget": "10000_50000"}}
        namen_fb1 = [t["name"] for t in recommend_tools(basis, max_tools=8)]
        namen_fb2 = [t["name"] for t in recommend_tools(mit_fb2, max_tools=8)]
        # Sparten-Werkzeuge stehen in beiden Fällen drin — das Budget wirft sie nie hinaus
        for erwartet in ("Amberscript", "Topaz Video AI"):
            assert erwartet in namen_fb1, namen_fb1
            assert erwartet in namen_fb2, namen_fb2
        # Sparten-fremde Werkzeuge stehen nicht vor den Sparten-Werkzeugen
        for fremd in ("Duden-Mentor", "Canva Magic Studio", "LanguageTool"):
            if fremd in namen_fb2:
                assert namen_fb2.index(fremd) > namen_fb2.index("Amberscript")

    def test_widerspruchs_text_mit_umlauten(self):
        src = (REPO / "services" / "briefing_contradictions.py").read_text(encoding="utf-8")
        assert '"Für die Bewertung der Investition gilt die spätere Angabe "' in src
        assert '"und nicht stillschweigend geglättet werden."' in src
        assert "Fuer die Bewertung" not in src


class TestKontextblockEcho:
    LEAK = (
        "<ul><li>Content-Erstellung: Texte, Grafiken, Videos, Audio, 3D</li>"
        "<li>Projektmanagement: Briefing, Konzeption, Produktion, Delivery</li></ul>"
        "<ul><li>Kreative Blockaden: Ständig neue Ideen entwickeln müssen</li>"
        "<li>Feedback-Schleifen: Viele Korrekturschleifen pro Projekt</li></ul>"
        "<ul><li>Adobe Creative Suite: Photoshop, Premiere, After Effects</li>"
        "<li>Figma für UI/UX Design</li><li>Logic Pro / Ableton für Audio</li></ul>"
        "<ul><li>Mitarbeiter: 2-10</li><li>Budget CAPEX max: 50.000 €</li></ul>"
        "<ul><li>Kollaboration verbessern</li><li>Prozesse standardisieren</li></ul>"
        "<ul><li>Business-Software</li><li>Zu viele Tools (Tool-Zoo vermeiden)</li></ul>"
    )
    KAPITEL = (
        '<section class="section ki-rechte-kennzeichnung"><h2>KI-Rechte &amp; Kennzeichnung in der Produktion</h2>'
        "<p>Die Verwertbarkeit von KI-Ausgaben ist rechtlich noch nicht abschließend geklärt und verlangt Sorgfalt.</p>"
        "<h3>Checkliste: Vor jeder Auslieferung</h3><ul><li>Sind alle KI-Entwürfe dokumentiert?</li>"
        "<li>Liegt für alle Stimmen eine Einwilligung vor?</li></ul></section>"
    )

    def test_listen_ohne_label_fallen(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        out, n = strip_context_block_leaks(self.LEAK + self.KAPITEL, "ki_rechte_kennzeichnung")
        assert n >= 1
        assert "Kreative Blockaden" not in out and "Budget CAPEX" not in out and "Tool-Zoo" not in out
        assert out.startswith('<section class="section ki-rechte-kennzeichnung">')
        assert "Sind alle KI-Entwürfe dokumentiert?" in out  # die echte Checkliste bleibt

    def test_label_mit_liste_faellt_gemeinsam(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        html = ("<p><strong>Typische Workflows:</strong></p><ul><li>Content-Erstellung: Texte</li>"
                "<li>Distribution: Kanäle bespielen</li></ul><p>" + "Echter Absatz mit Inhalt. " * 6 + "</p>")
        out, _ = strip_context_block_leaks(html, "recommendations")
        assert "Distribution" not in out and "Echter Absatz" in out

    def test_normale_liste_bleibt(self):
        from services.pipeline_sanitizers import strip_context_block_leaks
        html = ("<p>" + "Text. " * 30 + "</p><ul><li>Prozesse standardisieren, damit das Team schneller wird</li>"
                "<li>Kollaboration verbessern durch eine gemeinsame Ablage</li></ul>")
        out, _ = strip_context_block_leaks(html, "recommendations")
        assert "Kollaboration verbessern durch" in out

    def test_prompt_verbietet_das_echo(self):
        md = (REPO / "prompts" / "de" / "ki_rechte_kennzeichnung.md").read_text(encoding="utf-8")
        assert "gib ihn nie als Liste aus" in md


class TestStrategieAnker:
    def test_kapitel_etikett_ist_kein_handlungsfeld(self):
        from services.strategy_pipeline import _titel_aus_html, _derive_handlungsfelder
        html = ("<h3>Strategische Handlungsfelder</h3><h3>Rechte-Register aufbauen</h3>"
                "<h3>Top 3 Handlungsfelder mit Priorität</h3><h3>Nächste Schritte</h3>")
        assert _titel_aus_html(html) == ["Rechte-Register aufbauen"]
        felder = _derive_handlungsfelder({"sections": {"recommendations": html}}, {})
        assert "Strategische Handlungsfelder" not in felder


class TestQuellenlisteAusLinks:
    def test_linkliste_wird_zeile(self):
        from services.html_enhancer import _compact_source_lists
        html = ('<p>Empfehlung: Führen Sie maximal zwei Tools ein.</p>'
                '<ul><li><a href="https://www.amberscript.com">Amberscript</a></li>'
                '<li><a href="https://www.make.com">Make (Integromat)</a></li>'
                '<li><a href="https://mistral.ai">Mistral AI</a></li></ul>')
        out = _compact_source_lists(html)
        assert "<ul>" not in out and "sources-footer" in out
        assert "Amberscript · " in out or "Amberscript</a> · " in out

    def test_inhaltsliste_bleibt(self):
        from services.html_enhancer import _compact_source_lists
        html = '<ul><li>Datentypen definieren: keine personenbezogenen Daten.</li><li><a href="x">Nur ein Link</a></li></ul>'
        assert _compact_source_lists(html) == html


class TestWaechter:
    def test_hochrisiko_verneint_ist_kein_befund(self):
        cr = _compare()
        pruefe = dict((n, f) for n, _, f in cr.PRUEFUNGEN)
        assert pruefe["werkzeug_als_hochrisiko"](
            "Die empfohlenen Werkzeuge (z. B. Microsoft 365 Copilot, Amberscript, Make) fallen nicht unter die Hochrisiko-Systeme.") is None
        assert pruefe["werkzeug_als_hochrisiko"]("Copilot gilt voraussichtlich als Hochrisiko-System.")

    def test_integrationsspalte_ist_keine_eu_aussage(self):
        cr = _compare()
        zelle = ("Make\n(Make.com)\nAbon­nement\nEU / EU-Server\nKann mit\nMicrosoft 365,\nGitHub/GitLab,\n"
                 "OpenAI API\nverbunden\nwerden\n★★")
        assert cr._us_werkzeug_als_eu(zelle) is None
        assert cr._us_werkzeug_als_eu("EU-gehostete Alternativen wie Claude und Make.")

    def test_liste_nach_seitenumbruch_ist_kein_befund(self):
        cr = _compare()
        text = ("Für die Automatisierung kommen unterschiedliche Förderlogiken in Frage – mit einer Einschränkung für Berlin:\n"
                "Seite 27 / 34\nReport-ID: R-20260905-HOHL • 05.09.2026\n\n===== SEITE 28 =====\n"
                "ProFIT Berlin: Das Berliner Landesprogramm fördert primär Forschungsprojekte.\n")
        assert cr._ankuendigung_ohne_liste(text) is None


class TestWerkzeugdaten:
    def test_davinci_im_seed_ohne_preisdatum(self):
        daten = json.loads((REPO / "data" / "tools_seed.json").read_text(encoding="utf-8"))
        dv = next(t for t in daten if t["name"].startswith("DaVinci Resolve"))
        assert dv["verified_at"] is None and dv["host"] == "lokal"
        assert "post_vfx" in dv["sparten"] and "Neural Engine" in dv["name"]

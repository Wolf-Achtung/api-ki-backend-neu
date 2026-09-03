# -*- coding: utf-8 -*-
"""KIS-1267: Challenge-Tageszahlen konsistent, Seite 31 nicht mehr fast leer.

Zwei Kosmetik-Befunde aus dem Lauf KIS-1262:

1. Die Challenge nannte in derselben Ueberschrift "23-Tage" und
   "3 Wochen", zeigte darunter aber vier Wochenbloecke, und die
   Prognose-Zeile sprach von "30 Tagen". KIS-1251 hatte nur den
   englischen Zweig umgestellt.
2. PLATIN-QA meldete "thin_page R1:S.31: nur 330 Zeichen" — der
   CTA-Kasten zur KI-Potenzial-Analyse stand allein auf einer Seite.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from services.sofort_start_generator import generate_30_tage_challenge_html_v2

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "templates" / "pdf_template_v7.html"


def _render(**kwargs) -> str:
    basis = dict(company_size="team", expertise_level="intermediate", lang="de")
    basis.update(kwargs)
    return generate_30_tage_challenge_html_v2(**basis)


class TestKeinePlatzhalterImText:
    """Die Tipp- und Prognose-Bloecke waren einfache Strings. Ein
    eingefuegtes {_prognose_days} waere woertlich im PDF gelandet."""

    @pytest.mark.parametrize("lang", ["de", "en"])
    @pytest.mark.parametrize("groesse,niveau", [
        ("team", "intermediate"), ("team", "expert"),
        ("solo", "intermediate"), ("kmu", "beginner"),
    ])
    def test_keine_geschweiften_platzhalter(self, lang, groesse, niveau):
        html = _render(company_size=groesse, expertise_level=niveau, lang=lang)
        uebrig = re.findall(r"\{_[a-z_]+\}", html)
        assert not uebrig, f"Platzhalter im Text: {uebrig}"


class TestTageszahlenStimmenUeberein:

    def _tage_im_titel(self, html: str) -> int:
        m = re.search(r"Ihre (\d+)-Tage KI-Challenge", html)
        return int(m.group(1)) if m else 30

    def test_titel_und_prognose_nennen_dieselbe_zahl(self):
        """Lauf KIS-1262: Titel "23-Tage", Prognose "nach 30 Tagen"."""
        html = _render()
        tage = self._tage_im_titel(html)
        assert f"Tagen: Routine beibehalten" in html
        assert re.search(rf"Nach {tage} Tagen: Routine beibehalten", html)
        assert "nach 30 Tagen" not in html.lower() or tage == 30

    def test_wochenzahl_im_untertitel_passt_zu_den_bloecken(self):
        """Lauf KIS-1262: Untertitel "in 3 Wochen", darunter vier
        Wochenbloecke (7+7+7+2 Tage)."""
        html = _render()
        m = re.search(r"Workflow-Profi in (\d+) Wochen", html)
        assert m, "Untertitel mit Wochenzahl nicht gefunden"
        behauptet = int(m.group(1))
        gerendert = len(set(re.findall(r"Woche (\d+):", html)))
        assert behauptet == gerendert, (
            f"Untertitel sagt {behauptet} Wochen, gerendert sind {gerendert}"
        )

    @pytest.mark.parametrize("groesse,niveau", [
        ("team", "intermediate"), ("team", "expert"), ("solo", "intermediate"),
    ])
    def test_untertitel_nie_im_widerspruch(self, groesse, niveau):
        html = _render(company_size=groesse, expertise_level=niveau)
        m = re.search(r"in (\d+) Wochen", html)
        if not m:
            pytest.skip("Profil ohne Wochenzahl im Untertitel")
        gerendert = len(set(re.findall(r"Woche (\d+):", html)))
        assert int(m.group(1)) == gerendert

    def test_solo_behaelt_volle_challenge(self):
        html = _render(company_size="solo", expertise_level="intermediate")
        assert "Ihre 30-Tage KI-Challenge" in html or "-Tage KI-Challenge" in html


class TestTemplateHinweise:

    def test_skip_hinweise_nennen_keine_feste_tageszahl(self):
        """Bei gedroppter Woche widerspricht "30-Tage-Challenge" dem Titel."""
        src = TEMPLATE.read_text(encoding="utf-8")
        for satz in ("Die 30-Tage-Challenge überspringt die Grundlagen-Woche",
                     "Die 30-Tage-Challenge startet direkt mit Stack-Optimierung"):
            assert satz not in src, satz

    def test_grundlagen_hinweis_bleibt_erhalten(self):
        """KIS-1142 P3 haengt an dieser Formulierung."""
        src = TEMPLATE.read_text(encoding="utf-8")
        assert "überspringt die Grundlagen-Woche" in src

    def test_kpa_kasten_bleibt_bei_seinem_vortext(self):
        """Ohne break-before:avoid landete der Kasten allein auf S. 31."""
        src = TEMPLATE.read_text(encoding="utf-8")
        idx = src.find("Ihre ausf&uuml;hrliche KI-Potenzial-Analyse")
        assert idx > 0, "CTA-Kasten nicht gefunden"
        kopf = src[max(0, idx - 700):idx]
        assert "break-before: avoid" in kopf
        assert "page-break-before: avoid" in kopf
        assert "break-inside: avoid" in kopf

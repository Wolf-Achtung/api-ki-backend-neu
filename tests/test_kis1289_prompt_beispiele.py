# -*- coding: utf-8 -*-
"""KIS-1289 (Stufe 2 des Branchen-Audits): Kein Beispiel aus einer fremden Branche.

Am 03.09. hat ein Prompt-Beispiel („rechnen wir mit") den Report woertlich
gepraegt — gegen eine ausdrueckliche Regel. Ein Beispiel schlaegt jede
Regel. Zehn deutsche und vierzehn englische Prompt-Dateien trugen noch
Beispiele aus dem frueheren Mehrbranchen-System: Steuerberater (sieben
Stellen), Handwerk, Sanitaer, Industrie, „deutscher Mittelstand". Jedes
davon zog den Text vom Tonstudio, Verlag oder Games-Studio weg.

Nebenbefund derselben Klasse: Die Prompts empfahlen go-digital (in den
Daten ``expired``) und ZIM (bis 15.01.2027 ``paused``) — auch der
deutsche Foerder-Prompt fuer KMU. Der Rueckfall-Waechter in
compare_reports.py haette das erst im fertigen PDF gefunden.

Dieser Test haelt beides fest: keine Fremdbranchen-Beispiele, keine
ausgesetzten Programme als Empfehlung.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROMPTS = sorted(
    p for p in list((REPO / "prompts").glob("*/*.md")) + list((REPO / "prompts").glob("*.py"))
    if "_backup" not in str(p)
)

# Fremdbranchen als BEISPIEL — nicht als Eintrag einer Branchenliste.
_FREMD = re.compile(
    r"Steuerberat|Mandant|tax advis|tax consult|Handwerk(?!lich)|craftsm|plumb|Sanitär"
    r"|Mittelstandsbetrieb|Mittelstands-Benchmark|SME benchmark|KMU Produktion|SME manufactur",
    re.IGNORECASE,
)
# Ausgesetzte oder beendete Programme — als Empfehlung verboten, als Verbot erlaubt.
_PROGRAMM = re.compile(r"go[‑-]digital|\bZIM\b")
_VERBOT = re.compile(r"NIEMALS|NEVER|nicht nennen|do not name|Do NOT recommend|ausgesetzt|suspended")


def _zeilen(pfad: Path):
    return pfad.read_text(encoding="utf-8").split("\n")


class TestKeineFremdbranchenBeispiele:

    @pytest.mark.parametrize("pfad", PROMPTS, ids=lambda p: str(p.relative_to(REPO)))
    def test_prompt_ohne_fremdbranche(self, pfad):
        treffer = [
            (i + 1, z.strip()[:100]) for i, z in enumerate(_zeilen(pfad)) if _FREMD.search(z)
        ]
        assert not treffer, treffer

    def test_die_sieben_steuerberater_stellen_sind_weg(self):
        """Die dichteste Gruppe aus dem Audit."""
        for name in ("recommendations", "top_3_massnahmen", "roadmap_90d",
                     "unternehmensprofil_markt", "ai_act_summary"):
            text = (REPO / "prompts" / "de" / f"{name}.md").read_text(encoding="utf-8")
            assert "Steuerberat" not in text, name
        assert "Steuerberatung" not in (REPO / "prompts" / "strategy_prompts.py").read_text(encoding="utf-8")


class TestMedienBeispieleNachSparte:
    """Die Ersatz-Beispiele verteilen sich ueber die Sparten — kein
    einzelnes Beispiel darf die Tonlage vorgeben."""

    @pytest.mark.parametrize("pfad,stichworte", [
        ("prompts/de/recommendations.md", ("Postproduktion", "Verlag", "Tonstudio", "Games-Studio", "Agentur", "Content Creation")),
        ("prompts/en/recommendations.md", ("post-production", "publisher", "recording studio", "games studio", "agency", "content creation")),
        ("prompts/de/branch_deep_dive.md", ("Postproduktion", "Verlag", "Tonstudio", "Games")),
        ("prompts/en/branch_deep_dive.md", ("Post-production", "Publishing", "Recording studio", "Games")),
        ("prompts/de/gamechanger.md", ("Tonstudio", "Verlag", "Games-Studio")),
        ("prompts/en/gamechanger.md", ("recording studio", "publisher", "games studio")),
    ])
    def test_mehrere_sparten_genannt(self, pfad, stichworte):
        text = (REPO / pfad).read_text(encoding="utf-8")
        fehlend = [s for s in stichworte if s not in text]
        assert not fehlend, fehlend


class TestKeineAusgesetztenProgramme:

    @pytest.mark.parametrize("pfad", PROMPTS, ids=lambda p: str(p.relative_to(REPO)))
    def test_zim_und_go_digital_nur_als_verbot(self, pfad):
        treffer = [
            (i + 1, z.strip()[:100])
            for i, z in enumerate(_zeilen(pfad))
            if _PROGRAMM.search(z) and not _VERBOT.search(z)
        ]
        assert not treffer, treffer

    def test_de_foerder_prompt_kmu_ohne_zim(self):
        """Fuer KMU-Kunden stand ZIM als Empfehlung im deutschen Prompt —
        der PDF-Waechter haette es erst hinterher gefunden."""
        text = (REPO / "prompts" / "de" / "foerderpotenzial.md").read_text(encoding="utf-8")
        kmu = [z for z in text.split("\n") if z.startswith("- kmu:")]
        assert kmu and "ZIM" not in kmu[0], kmu


class TestKeinePreiseImEnglischenQuickWins:
    """Preis nur mit Pruefdatum (KIS-1280). Der englische Quick-Wins-Prompt
    trug noch Listenpreise (ChatGPT Plus €20/month, Jasper €49/month …);
    der deutsche war seit KIS-1244 bereinigt."""

    def test_keine_monatspreise(self):
        text = (REPO / "prompts" / "en" / "quick_wins.md").read_text(encoding="utf-8")
        block = text[text.find("## TOOL RECOMMENDATIONS"):text.find("## QUALITY CHECKS")]
        assert block, "Block nicht gefunden"
        assert not re.search(r"€\s?\d+/(month|user)", block), block

    def test_sparten_liste_vorhanden(self):
        text = (REPO / "prompts" / "en" / "quick_wins.md").read_text(encoding="utf-8")
        for s in ("Post-production", "Audio/podcast", "Publishing/agency", "Games"):
            assert s in text, s

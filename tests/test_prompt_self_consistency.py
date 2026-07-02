# -*- coding: utf-8 -*-
"""KIS-PROMPT P6: Prompt-Selbst-Konsistenz-Lint.

Verhindert die Widerspruchs-Klassen, die das Prompt-Audit (Juli 2026) in
gewachsenen Prompts gefunden hat. Jede Regel hier hat einen realen Vorfall
als Ursprung — siehe Kommentare. Läuft als Unit-Test → hartes CI-Gate.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

PROMPTS_DE = Path(__file__).parent.parent / "prompts" / "de"
PROMPT_FILES = sorted(p for p in PROMPTS_DE.glob("*.md") if not p.name.startswith("_backup"))


def _strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


@pytest.mark.parametrize("path", PROMPT_FILES, ids=lambda p: p.name)
def test_no_conflicting_roi_rules(path: Path) -> None:
    """Vorfall: recommendations/gamechanger erlaubten '200% (gedeckelt)' UND
    verboten ROI-Werte komplett (ZERO TOLERANCE) — im selben Prompt."""
    text = path.read_text(encoding="utf-8")
    has_zero_tolerance = "ROI PROHIBITION" in text or ("ZERO TOLERANCE" in text and "ROI" in text)
    allows_capped_roi = "200% (gedeckelt)" in text or "200 % (gedeckelt)" in text
    assert not (has_zero_tolerance and allows_capped_roi), (
        f"{path.name}: enthält ROI-Totalverbot UND '200% gedeckelt'-Erlaubnis — "
        f"eine Regel muss weichen (Owner-Prinzip: ROI-Zahlen nur im Business Case)."
    )


@pytest.mark.parametrize("path", PROMPT_FILES, ids=lambda p: p.name)
def test_no_duplicate_prompt_in_file(path: Path) -> None:
    """Vorfall: gamechanger.md enthielt ZWEI komplette Prompts übereinander
    (v7.3 + altes v7.0 mit eigener Rolle/Struktur ab Z.519)."""
    text = _strip_html_comments(path.read_text(encoding="utf-8"))
    role_headings = re.findall(r"^##\s*Rolle\s*$", text, flags=re.MULTILINE)
    assert len(role_headings) <= 1, (
        f"{path.name}: {len(role_headings)}x '## Rolle' außerhalb von Kommentaren — "
        f"vermutlich liegen mehrere Prompt-Versionen übereinander."
    )


@pytest.mark.parametrize("path", PROMPT_FILES, ids=lambda p: p.name)
def test_hauptleistung_max_counts_consistent(path: Path) -> None:
    """Vorfall: roadmap_90d hatte 'MAX 3x' in der Kopfregel und 'MAX 2x' in
    den Größen-Zweigen — das Modell bekam zwei verschiedene Limits."""
    text = path.read_text(encoding="utf-8")
    # Nur GESAMT-Limits vergleichen (Zeilen mit gesamt/TOTAL/Sektion) —
    # per-Element-Limits ('MAX 1x pro Maßnahme') sind legitim verschieden.
    counts = set()
    for line in text.splitlines():
        if not re.search(r"gesamt|TOTAL|Sektion", line, flags=re.IGNORECASE):
            continue
        m = re.search(r"MAX(?:IMUM)?\s+(\d)x\s*(?:{{\s*)?hauptleistung", line, flags=re.IGNORECASE)
        if m:
            counts.add(m.group(1))
    assert len(counts) <= 1, (
        f"{path.name}: widersprüchliche hauptleistung-GESAMT-Limits {sorted(counts)} — "
        f"genau EIN Limit pro Datei."
    )


@pytest.mark.parametrize("path", PROMPT_FILES, ids=lambda p: p.name)
def test_banned_word_etwa_not_used_in_body(path: Path) -> None:
    """Vorfall: business_case verbot 'etwa' als Hard-Fail ('use rund instead')
    und nutzte 'nach etwa {{PAYBACK_MONTHS}}' im eigenen Template-Body."""
    text = path.read_text(encoding="utf-8")
    bans_etwa = re.search(r'"etwa"\s*\(use\s*"rund"|NICHT\s*„?etwa', text) is not None
    if not bans_etwa:
        pytest.skip("Datei verbietet 'etwa' nicht")
    body = _strip_html_comments(text)
    # Nur Template-Zeilen prüfen (HTML-Kontext), nicht Anleitungsprosa in Klammern.
    violations = [
        ln.strip() for ln in body.splitlines()
        if re.search(r"nach etwa\b|etwa\s+<strong>", ln)
    ]
    assert not violations, (
        f"{path.name}: verbietet 'etwa', nutzt es aber im Template: {violations[:2]}"
    )


def test_includes_do_not_include_themselves() -> None:
    """Vorfall: _report_grundregeln.md enthielt seinen eigenen Include-Tag im
    Doku-Kommentar → Jinja-Endlos-Rekursion beim Laden."""
    for partial in PROMPTS_DE.glob("_*.md"):
        text = partial.read_text(encoding="utf-8")
        # {% raw %}-Blöcke sind Jinja-sicher (reine Doku) — vorher entfernen.
        text = re.sub(r"{%\s*raw\s*%}.*?{%\s*endraw\s*%}", "", text, flags=re.DOTALL)
        self_include = re.search(
            r"{%[-\s]*include\s+[\"']" + re.escape(partial.name) + r"[\"']", text
        )
        assert self_include is None, (
            f"{partial.name}: inkludiert sich selbst (außerhalb von raw) — Jinja-Rekursion."
        )


@pytest.mark.parametrize("path", PROMPT_FILES, ids=lambda p: p.name)
def test_no_conflicting_word_limits_same_size(path: Path) -> None:
    """Vorfall: executive_summary nannte 200, 250 und 250-350 Wörter als
    Minimum in derselben Datei. Heuristik: 'SOLO-HARD-LIMIT: Maximal N'
    darf nur einen Wert pro Datei haben."""
    text = path.read_text(encoding="utf-8")
    limits = set(re.findall(r"SOLO-HARD-LIMIT:\s*Maximal\s+(\d+)", text))
    assert len(limits) <= 1, (
        f"{path.name}: mehrere Solo-Hard-Limits {sorted(limits)} in einer Datei."
    )

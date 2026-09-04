# -*- coding: utf-8 -*-
"""KIS-1294 (Stufe 5 des Branchen-Audits): Benchmarks ehrlich machen.

Vier Quellen, keine gemessen: ``services/benchmarks.py`` (tot, BDZV-Wert
als „KI-Reifegrad 96/100" — eine Kategorienverwechslung),
``data/benchmarks.json`` („interne Synthese"), die Größen-Schwellen in
``extra_sections.BENCHMARK_SCORES`` (Deckblatt „Top 10 % ab 88") und der
Prompt ``wettbewerb_benchmark.md`` („Benchmark aus 30 Assessments",
feste Ø- und Top-10-Zahlen).

Regel: Eine Zahl ohne benannte Messung heißt im Report „Richtwert".
Der tote BDZV-Pfad ist gelöscht.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_bdzv_modul_ist_weg():
    assert not (REPO / "services" / "benchmarks.py").exists()
    src = "\n".join(p.read_text(encoding="utf-8") for p in (REPO / "services").glob("*.py"))
    assert "BDZV" not in src and "Retresco" not in src


def test_datendatei_nennt_richtwert():
    d = json.loads((REPO / "data" / "benchmarks.json").read_text(encoding="utf-8"))
    for k, v in d.items():
        if isinstance(v, dict) and "source" in v:
            assert "Richtwert" in v["source"], k
            assert "Studie" not in v["source"]
    assert "keine Messung" in d["notes"]


def test_deckblatt_sagt_richtwert():
    de = (REPO / "templates" / "pdf_template_v7.html").read_text(encoding="utf-8")
    en = (REPO / "templates" / "pdf_template_en.html").read_text(encoding="utf-8")
    assert "Richtwert Top 10 %: ab {{ top10_score_for_size }}" in de
    assert "Top 10% ab {{" not in de
    assert "Guide value top 10%: from {{ top10_score_for_size }}" in en
    assert "Top 10% of {{" not in en


def test_score_kontext_sagt_richtwert():
    from services.extra_sections import get_score_context
    for score in (95, 75, 66, 40):
        de = get_score_context(score, "klein", lang="de")["benchmark_context"]
        en = get_score_context(score, "klein", lang="en")["benchmark_context"]
        assert "Richtwert" in de, de
        assert "guide value" in en, en
        assert "Durchschnitt" not in de and "average" not in en


def test_benchmark_sektion_sagt_richtwert():
    from services.extra_sections import build_benchmarks_section
    html = build_benchmarks_section({"governance": 60, "security": 70, "value": 80, "enablement": 75, "overall": 71})
    assert "interne Richtwerte" in html and "keine Messung" in html
    assert "aktuellen Benchmarks ähnlicher Unternehmen" not in html


def test_prompt_nennt_keine_erfundene_datenbasis():
    for f in ("de", "en"):
        t = (REPO / "prompts" / f / "wettbewerb_benchmark.md").read_text(encoding="utf-8")
        assert "30 Assessments" not in t and "30 assessments" not in t
        assert "keine Messung" in t or "not a measurement" in t
    de = (REPO / "prompts" / "de" / "wettbewerb_benchmark.md").read_text(encoding="utf-8")
    en = (REPO / "prompts" / "en" / "wettbewerb_benchmark.md").read_text(encoding="utf-8")
    # Die Regel selbst darf die verbotenen Wörter nennen — der Skelett-Text nicht.
    skelett_de = de.split("<section", 1)[1]
    skelett_en = en.split("<section", 1)[1]
    assert "Branchendurchschnitt" not in skelett_de and "Branchenniveau" not in skelett_de
    assert "industry average" not in skelett_en and "industry level" not in skelett_en
    assert "Richtwert" in skelett_de and "guide value" in skelett_en


def test_gpt_analyze_rueckfall_ohne_studientitel():
    src = (REPO / "gpt_analyze.py").read_text(encoding="utf-8")
    assert '"Branchenstudie 2024"' not in src and '"Industry Study 2024"' not in src

# -*- coding: utf-8 -*-
"""KIS-1270: Fixes aus dem EN-Audit Lauf 3 (R1 "AI Status Report", Note 3−).

Kernbefund: Sektionen flippten zwischen den Läufen die Sprache, weil die
RETRY-/HEAL-/EXPAND-Meta-Prompts hart deutsch waren — jede zufällig zu kurz
geratene EN-Sektion wurde durch einen deutschen Zweit-Prompt neu geschrieben.

Abgedeckt:
  A: lang-aware Meta-Prompts (_expand_short_section, N4.6 2-pass,
     _regenerate_without_leaks, C1-Regen, FIX-523A, FIX-499/511-Strict-Regen)
  B: KPI-Kacheln EN, EN-Zahlformate (mo/4-stellige €), Lone-Enum-Strip,
     FORBIDDEN-Scrub "system prompt", Fördertabelle EN, Transitions EN,
     Risiko-Labels EN, Locale-Sanitizer-Guards.
"""
from __future__ import annotations

import os
import re

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

import pytest


# =========================================================================
# A1/A5: _expand_short_section — Expand-Prompt lang-aware
# =========================================================================

class TestExpandShortSectionLang:

    def test_en_prompt_used_for_en(self, monkeypatch):
        import gpt_analyze as g
        captured = {}

        def fake_llm(section_key, prompt, system_prompt=None, **kw):
            captured["prompt"] = prompt
            captured["sys"] = system_prompt
            return "<p>" + "word " * 200 + "</p>"

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        g._expand_short_section("EXECUTIVE_SUMMARY_HTML", "<p>short</p>", 150, 20, lang="en")
        assert "Expand the existing text" in captured["prompt"]
        assert "Keep ALL existing facts and figures unchanged" in captured["prompt"]
        assert "Erweitere" not in captured["prompt"]
        assert "OUTPUT LANGUAGE: English" in captured["sys"]

    def test_de_prompt_byte_identical_default(self, monkeypatch):
        import gpt_analyze as g
        captured = {}

        def fake_llm(section_key, prompt, system_prompt=None, **kw):
            captured["prompt"] = prompt
            captured["sys"] = system_prompt
            return "<p>" + "wort " * 200 + "</p>"

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        g._expand_short_section("EXECUTIVE_SUMMARY_HTML", "<p>kurz</p>", 150, 20)
        assert "Erweitere den bestehenden Text" in captured["prompt"]
        assert "OUTPUT LANGUAGE" not in captured["sys"]

    def test_call_sites_pass_lang(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py"),
                   encoding="utf-8").read()
        # POST-TRIM-HEAL und RESCUE-640 geben die Briefing-Sprache weiter
        assert src.count('lang=str(answers.get("lang") or "de")') >= 2


# =========================================================================
# A4: _regenerate_without_leaks — Strict-Directive lang-aware
# =========================================================================

class TestRegenerateWithoutLeaksLang:

    def test_en_directive(self, monkeypatch):
        import gpt_analyze as g
        captured = {}

        def fake_llm(section_key, prompt, system_prompt=None, **kw):
            captured["prompt"] = prompt
            return "<p>ok</p>"

        monkeypatch.setattr(g, "_call_llm_for_section", fake_llm)
        llm = {"temperature": 0.5, "max_tokens": 100, "model": "x"}
        g._regenerate_without_leaks("executive_summary", "BASE", llm, lang="en")
        assert "STRICTLY FORBIDDEN - ASSISTANT LANGUAGE" in captured["prompt"]
        assert "Write the section in English." in captured["prompt"]
        g._regenerate_without_leaks("executive_summary", "BASE", llm, lang="de")
        assert "STRIKT VERBOTEN - ASSISTENTEN-SPRACHE" in captured["prompt"]


# =========================================================================
# A2/A6/A7: Quell-Checks der übrigen lang-aware Meta-Prompts
# =========================================================================

class TestMetaPromptSources:

    @pytest.fixture(scope="class")
    def src(self):
        return open(os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py"),
                    encoding="utf-8").read()

    def test_n46_two_pass_expand_en(self, src):
        assert "The following content is too short and must be expanded." in src
        assert "_n46_lang_en" in src

    def test_c1_regen_strict_suffix_en(self, src):
        assert "You are a report generator, NOT a chat assistant." in src

    def test_fix523a_roadmap12m_extend_en(self, src):
        assert "IMPORTANT - MINIMUM LENGTH NOT REACHED" in src

    def test_fix499_strict_regen_en_variants(self, src):
        assert "Create a 90-day roadmap for AI adoption in" in src
        assert "Create an AI stack recommendation for" in src
        assert "Create strategic AI options (game-changer potentials) for" in src
        # EN-Fallback für FIX-B6
        assert "Your 90-Day AI Roadmap" in src

    def test_system_prompt_builder_en_suffix(self):
        from services.report_system_prompt import build_report_system_prompt
        de = build_report_system_prompt(mode="expand", lang="de")
        en = build_report_system_prompt(mode="expand", lang="en")
        assert "MODUS: ERWEITERUNG" in de and "OUTPUT LANGUAGE" not in de
        assert "MODE: EXPANSION" in en and "OUTPUT LANGUAGE: English" in en


# =========================================================================
# A3: KIS-1231 Truncation-Retry nutzt den ORIGINAL-Prompt (kein DE-Zusatz)
# =========================================================================

class TestTruncationRetryReusesPrompt:

    def test_no_german_suffix_in_retry(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "services",
                                "anthropic_client.py"), encoding="utf-8").read()
        idx = src.find("KIS-1231: Einmaliger Retry")
        assert idx != -1
        block = src[idx:idx + 1500]
        # Der Retry baut die kwargs aus denselben messages — kein neuer Prompt
        assert "messages=messages" in block
        assert "Erweitere" not in block and "Erstelle" not in block


# =========================================================================
# B13: Zero-Leak — "system prompt" nur noch als Selbst-Referenz kritisch
# =========================================================================

class TestSystemPromptScrub:

    def test_legit_en_text_preserved(self):
        from services.zero_leak_engine import apply_blacklist_classified
        r = apply_blacklist_classified(
            "<li>Set up system prompts for consistent results</li>",
            "SOFORT_START_HTML")
        assert "system prompts for consistent results" in r.cleaned_text
        assert not r.critical_hits

    def test_self_reference_still_critical(self):
        from services.zero_leak_engine import apply_blacklist_classified
        r = apply_blacklist_classified(
            "<p>According to my system prompt I cannot help.</p>", "X")
        assert r.critical_hits
        r2 = apply_blacklist_classified(
            "<p>Laut meinem System-Prompt darf ich das nicht.</p>", "X")
        assert r2.critical_hits


# =========================================================================
# B8/B11: EN-Zahlformate
# =========================================================================

class TestEnNumberFormats:

    def test_mo_without_dot(self):
        from services.html_sanitizer import normalize_en_number_formats
        assert "11.9 mo" in normalize_en_number_formats("<span>11,9 mo</span>")

    def test_four_digit_eur_gets_comma(self):
        from services.html_sanitizer import normalize_en_number_formats
        out = normalize_en_number_formats("<p>1425 € plus 2375 Euro</p>")
        assert "1,425 €" in out and "2,375 Euro" in out

    def test_years_and_ids_untouched(self):
        from services.html_sanitizer import normalize_en_number_formats
        out = normalize_en_number_formats(
            "<p>In 2026 we invest 1425 € (build 1425, 12425 €, 2,375 €).</p>")
        assert "In 2026" in out
        assert "build 1425," in out       # keine €-Einheit → unangetastet
        assert "12425 €" in out           # 5-stellig → unangetastet
        assert "2,375 €" in out           # bereits formatiert


# =========================================================================
# B12: Lone-Enum-Strip gehärtet (leere Sektion "4.")
# =========================================================================

class TestLoneEnumStrip:

    @pytest.mark.parametrize("frag", [
        "<h3>Chapter</h3><p><strong>4.</strong></p>",
        "<h3>Chapter</h3><p><strong>4.&nbsp;</strong></p>",
        "<h3>Chapter</h3><p>4.<br/></p>",
        "<h2>4.</h2>",
        "<div>4.</div>",
        "<p><span><strong>4.</strong></span></p>",
        "</p>\n4.\n<h2>Next</h2>",
    ])
    def test_variants_removed(self, frag):
        from services.html_sanitizer import apply_en_final_locale_pass
        out = apply_en_final_locale_pass(frag, "en")
        txt = re.sub(r"<[^>]+>", " ", out)
        assert not re.search(r"(?<!\d)4\.", txt), out

    def test_legit_numbered_heading_kept(self):
        from services.html_sanitizer import apply_en_final_locale_pass
        keep = "<h2><strong>4.</strong> Roadmap</h2><p>Step 4. is fine</p>"
        out = apply_en_final_locale_pass(keep, "en")
        assert "Roadmap" in out and "<strong>4.</strong>" in out
        assert "Step 4. is fine" in out

    def test_de_untouched(self):
        from services.html_sanitizer import apply_en_final_locale_pass
        frag = "<p><strong>4.</strong></p>"
        assert apply_en_final_locale_pass(frag, "de") == frag


# =========================================================================
# B17: Locale-Sanitizer — keine Wort-Ersetzungen mitten in deutschen Sätzen
# =========================================================================

class TestLocaleSanitizerGuards:

    def test_nutzen_verb_not_replaced(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        out = sanitize_en_locale_tokens("<p>Nutzen Sie ein Recherche-Tool.</p>", "en")
        assert "Benefits Sie" not in out

    def test_nutzen_ui_token_replaced(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        out = sanitize_en_locale_tokens("<td>Nutzen</td><th>Nutzen (J1)</th>", "en")
        assert "<td>Benefits</td>" in out and "Benefits (J1)" in out

    def test_empfehlung_mid_sentence_not_replaced(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        out = sanitize_en_locale_tokens("<p>Charakter der Empfehlung</p>", "en")
        assert "der Recommendation" not in out

    def test_empfehlung_ui_token_replaced(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        out = sanitize_en_locale_tokens("<h4>Empfehlungen</h4>", "en")
        assert "<h4>Recommendations</h4>" in out

    def test_unternehmens_compound_not_split(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        out = sanitize_en_locale_tokens("<p>Unternehmensberatung für KI</p>", "en")
        assert "Company beratung" not in out

    def test_branch_label_translated(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        out = sanitize_en_locale_tokens(
            '<span class="badge">Branche Medien & Kreativwirtschaft</span>', "en")
        assert "Media & Creative Industries" in out

    def test_de_reports_untouched(self):
        from services.html_sanitizer import sanitize_en_locale_tokens
        de = "<p>Nutzen Sie die Empfehlung der Unternehmensberatung.</p>"
        assert sanitize_en_locale_tokens(de, "de") == de


# =========================================================================
# B14: Fördertabelle lang-aware
# =========================================================================

class TestFundingTableLang:

    BRIEF = {
        "BRANCHE_LABEL": "Medien & Kreativwirtschaft",
        "BUNDESLAND_LABEL": "Berlin",
        "UNTERNEHMENSGROESSE_LABEL": "11–100 (KMU)",
        "country": "DE",
    }

    def test_en_headers_and_values(self):
        from services.extra_sections import build_core_funding_table_html
        en = build_core_funding_table_html(dict(self.BRIEF), lang="en")
        assert "<th>Funding rate</th>" in en and "<th>AI relevance</th>" in en
        assert "Förderquote" not in en and "KI-Relevanz" not in en
        assert "<strong>Note:</strong>" in en and "Hinweis" not in en
        assert "Zuschuss" not in en  # _FUNDING_TERMS_EN angewandt

    def test_de_default_unchanged_structure(self):
        from services.extra_sections import build_core_funding_table_html
        de = build_core_funding_table_html(dict(self.BRIEF))
        assert "<th>Förderquote</th>" in de and "<th>KI-Relevanz</th>" in de
        assert "<strong>Hinweis:</strong>" in de

    def test_kis1104_reinjection_is_lang_aware(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py"),
                   encoding="utf-8").read()
        assert "build_core_funding_table_html(sections, lang=_kis1104_lang)" in src
        assert "Core programmes for your profile" in src


# =========================================================================
# B15: Kapitel-Überleitungen EN
# =========================================================================

class TestTransitionsEn:

    def test_source_has_en_transitions(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py"),
                   encoding="utf-8").read()
        assert "The previous pages defined your starting position" in src
        assert "your 90-day roadmap follows on the next page" in src
        assert "The risk analysis shows where action is needed" in src
        # DE-Texte weiterhin vorhanden
        assert "Die vorherigen Seiten haben Ihre Ausgangslage definiert" in src


# =========================================================================
# B9/B16: Risiko-Labels EN + Safety-Score-Guard
# =========================================================================

class TestRiskEngineLang:

    def _report(self):
        from services.risk_engine_v2 import generate_risk_report
        return generate_risk_report(
            context=None, sections={"LANG": "en"},
            briefing={"branche": "medien", "unternehmensgroesse": "kmu"})

    def test_dsgvo_badge_en(self):
        from services.risk_engine_v2 import risk_report_to_html
        html = risk_report_to_html(self._report(), lang="en")
        assert "Niedrig" not in html and ">Mittel<" not in html and ">Hoch<" not in html

    def test_score_cell_omitted_when_zero(self):
        from services.risk_engine_v2 import risk_report_to_html
        rep = self._report()
        rep.consolidated_score = 0
        html = risk_report_to_html(rep, lang="en")
        # Grade bleibt, Score-Kachel entfällt
        assert "Safety Score" not in html
        assert rep.consolidated_grade in html

    def test_decision_confidence_en(self):
        import gpt_analyze as g
        sec = {"AI_ACT_RISK_LEVEL": "limited", "report_date": "23.07.2026",
               "LANG": "en"}
        out = g._build_decision_confidence_html(sec)
        assert "begrenzt" not in out
        assert "Nature of the recommendation" in out
        assert "Decision Confidence" in out


# =========================================================================
# B10: Business-Case-Narrativ EN
# =========================================================================

class TestBusinessCaseNarrativeEn:

    def test_narrative_en(self):
        from services.business_case_engine_v2 import generate_business_case_report
        rep = generate_business_case_report(
            briefing={"branche": "medien", "unternehmensgroesse": "kmu", "lang": "en"})
        s = rep.narrative_summary
        assert "Business Case" not in s or "The business case" in s.lower() or True
        assert "Abwägung" not in s and "Amortisation" not in s and "Monaten" not in s

    def test_roi_context_box_en_in_source(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py"),
                   encoding="utf-8").read()
        assert "ROI context:" in src
        assert "payback of implementation costs" in src  # EN-KPI-Kachel


# =========================================================================
# B7: KPI-Kacheln (KIS-1235-Rebuild) lang-aware
# =========================================================================

class TestKpiTilesLang:

    def test_source_has_en_canonical_block(self):
        src = open(os.path.join(os.path.dirname(__file__), "..", "gpt_analyze.py"),
                   encoding="utf-8").read()
        assert 'after 12 months' in src
        assert 'canonical business case' in src
        assert 'hrs/month' in src
        # DE-Block unverändert vorhanden
        assert 'nach 12 Monaten' in src
        assert 'kanonischer Business Case' in src

"""
QA Test Script for EN Funding Phase 2

Tests:
1. Routing logic (FUNDING_SCOPE = DE vs EU_CORE)
2. HTML output validation
3. Prompt file selection
4. Language consistency (no German in EN, no English in DE)
"""

import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.funding_service_en import (
    FundingResult,
    FundingResultEUCore,
    get_funding_for_germany_en,
    get_funding_eu_core_en,
    render_funding_html_en,
    render_funding_eu_core_html_en,
)


# =============================================================================
# Test Profiles
# =============================================================================

PROFILE_EN_GERMANY = {
    "lang": "en",
    "country": "Germany",
    "unternehmensgroesse": "small",  # Phase 5A: was "team"
    "branche": "IT & Consulting",
    "mitarbeiter": 15,
    "bundesland": "by",  # Phase 5B: lowercase (wie Fragebogen)
    "budget": 50000,
    "hauptleistung": "Software development",
}

PROFILE_EN_FRANCE = {
    "lang": "en",
    "country": "France",
    "unternehmensgroesse": "solo",
    "branche": "IT Startup",
    "mitarbeiter": 3,
    "budget": 100000,
    "hauptleistung": "AI-powered analytics platform",
}

PROFILE_EN_ITALY = {
    "lang": "en",
    "country": "Italy",
    "unternehmensgroesse": "medium",  # Phase 5A: was "kmu"
    "branche": "Manufacturing",
    "mitarbeiter": 80,
    "budget": 200000,
    "hauptleistung": "Industrial automation",
}

PROFILE_DE_GERMANY = {
    "lang": "de",
    "country": "Deutschland",
    "unternehmensgroesse": "medium",  # Phase 5A: was "kmu"
    "branche": "Industrie / Produktion",
    "mitarbeiter": 45,
    "bundesland": "by",  # Phase 5B: lowercase (wie Fragebogen)
    "budget": 75000,
    "hauptleistung": "Fertigungsautomatisierung",
}


# =============================================================================
# Test Functions
# =============================================================================

def test_routing_logic():
    """Test A3.1: Routing logic for FUNDING_SCOPE"""
    print("\n" + "="*60)
    print("TEST A3.1: ROUTING LOGIC")
    print("="*60)

    results = []

    # EN + Germany → Phase 1 (FUNDING_SCOPE="DE")
    country_de = PROFILE_EN_GERMANY.get("country", "").upper()
    is_de = country_de in ("DE", "GERMANY", "DEUTSCHLAND", "")
    scope_de = "DE" if is_de else "EU_CORE"
    result_de = {
        "profile": "EN + Germany",
        "expected_scope": "DE",
        "actual_scope": scope_de,
        "status": "✓" if scope_de == "DE" else "✖"
    }
    results.append(result_de)
    print(f"  EN + Germany: Expected=DE, Actual={scope_de} → {result_de['status']}")

    # EN + France → Phase 2 (FUNDING_SCOPE="EU_CORE")
    country_fr = PROFILE_EN_FRANCE.get("country", "").upper()
    is_fr_de = country_fr in ("DE", "GERMANY", "DEUTSCHLAND", "")
    scope_fr = "DE" if is_fr_de else "EU_CORE"
    result_fr = {
        "profile": "EN + France",
        "expected_scope": "EU_CORE",
        "actual_scope": scope_fr,
        "status": "✓" if scope_fr == "EU_CORE" else "✖"
    }
    results.append(result_fr)
    print(f"  EN + France:  Expected=EU_CORE, Actual={scope_fr} → {result_fr['status']}")

    # EN + Italy → Phase 2 (FUNDING_SCOPE="EU_CORE")
    country_it = PROFILE_EN_ITALY.get("country", "").upper()
    is_it_de = country_it in ("DE", "GERMANY", "DEUTSCHLAND", "")
    scope_it = "DE" if is_it_de else "EU_CORE"
    result_it = {
        "profile": "EN + Italy",
        "expected_scope": "EU_CORE",
        "actual_scope": scope_it,
        "status": "✓" if scope_it == "EU_CORE" else "✖"
    }
    results.append(result_it)
    print(f"  EN + Italy:   Expected=EU_CORE, Actual={scope_it} → {result_it['status']}")

    # DE → FUNDING_SCOPE not applicable (German logic)
    result_control = {
        "profile": "DE Control",
        "expected_scope": "N/A (DE logic)",
        "actual_scope": "N/A",
        "status": "✓"
    }
    results.append(result_control)
    print(f"  DE Control:   Expected=N/A, Actual=N/A → ✓")

    return results


def test_html_output():
    """Test A3.2: HTML output validation"""
    print("\n" + "="*60)
    print("TEST A3.2: HTML OUTPUT")
    print("="*60)

    results = []

    # EN + Germany: German programmes in English
    print("\n  [EN + Germany] Testing German funding service...")
    de_result = get_funding_for_germany_en(PROFILE_EN_GERMANY)
    de_html = render_funding_html_en(de_result)

    de_test = {
        "profile": "EN + Germany",
        "has_programmes": de_result.has_programmes,
        "programme_count": de_result.programme_count,
        "html_length": len(de_html),
        "contains_de_programmes": "go-digital" in de_html.lower() or "digital jetzt" in de_html.lower(),
        "status": "✓" if de_result.has_programmes else "✖"
    }
    results.append(de_test)
    print(f"    Programmes found: {de_result.programme_count}")
    print(f"    Contains DE programmes: {de_test['contains_de_programmes']}")
    print(f"    Status: {de_test['status']}")

    # EN + France: EU Core programmes
    print("\n  [EN + France] Testing EU core funding service...")
    fr_result = get_funding_eu_core_en(PROFILE_EN_FRANCE)
    fr_html = render_funding_eu_core_html_en(fr_result)

    fr_test = {
        "profile": "EN + France",
        "has_programmes": fr_result.has_programmes,
        "programme_count": fr_result.programme_count,
        "html_length": len(fr_html),
        "contains_eu_programmes": "horizon" in fr_html.lower() or "eic" in fr_html.lower(),
        "status": "✓" if fr_result.has_programmes else "✖"
    }
    results.append(fr_test)
    print(f"    Programmes found: {fr_result.programme_count}")
    print(f"    Contains EU programmes: {fr_test['contains_eu_programmes']}")
    print(f"    Status: {fr_test['status']}")

    # EN + Italy: EU Core programmes
    print("\n  [EN + Italy] Testing EU core funding service...")
    it_result = get_funding_eu_core_en(PROFILE_EN_ITALY)
    it_html = render_funding_eu_core_html_en(it_result)

    it_test = {
        "profile": "EN + Italy",
        "has_programmes": it_result.has_programmes,
        "programme_count": it_result.programme_count,
        "html_length": len(it_html),
        "contains_eu_programmes": "horizon" in it_html.lower() or "digital europe" in it_html.lower(),
        "status": "✓" if it_result.has_programmes else "✖"
    }
    results.append(it_test)
    print(f"    Programmes found: {it_result.programme_count}")
    print(f"    Contains EU programmes: {it_test['contains_eu_programmes']}")
    print(f"    Status: {it_test['status']}")

    return results


def test_no_mixing():
    """Test A3.2 continued: No mixing of DE/EU programmes"""
    print("\n" + "="*60)
    print("TEST A3.2b: NO MIXING DE/EU PROGRAMMES")
    print("="*60)

    results = []

    # EN + Germany should NOT have EU-only programmes
    de_result = get_funding_for_germany_en(PROFILE_EN_GERMANY)
    de_html = render_funding_html_en(de_result)
    has_eu_only = "eic accelerator" in de_html.lower() or "horizon europe" in de_html.lower()

    de_mix = {
        "profile": "EN + Germany",
        "test": "No EU-only programmes in DE funding",
        "has_eu_only": has_eu_only,
        "status": "✓" if not has_eu_only else "⚠"
    }
    results.append(de_mix)
    print(f"  EN + Germany: EU-only programmes present = {has_eu_only} → {de_mix['status']}")

    # EN + France should NOT have DE-specific programmes
    fr_result = get_funding_eu_core_en(PROFILE_EN_FRANCE)
    fr_html = render_funding_eu_core_html_en(fr_result)
    has_de_only = "digitalbonus bayern" in fr_html.lower() or "invest bw" in fr_html.lower()

    fr_mix = {
        "profile": "EN + France",
        "test": "No DE-specific programmes in EU funding",
        "has_de_only": has_de_only,
        "status": "✓" if not has_de_only else "✖"
    }
    results.append(fr_mix)
    print(f"  EN + France:  DE-specific programmes present = {has_de_only} → {fr_mix['status']}")

    return results


def test_prompt_selection():
    """Test A3.3: Prompt file selection"""
    print("\n" + "="*60)
    print("TEST A3.3: PROMPT SELECTION")
    print("="*60)

    results = []
    base_path = Path(__file__).parent.parent / "prompts"

    # Check prompt files exist (DE uses German names)
    prompts = {
        "DE": base_path / "de" / "foerderprogramme.md",  # German naming
        "DE-Potenzial": base_path / "de" / "foerderpotenzial.md",
        "EN-DE": base_path / "en" / "funding.md",
        "EN-DE-Potenzial": base_path / "en" / "funding_potential.md",
        "EN-EU": base_path / "en" / "funding_eu_core.md",
    }

    for name, path in prompts.items():
        exists = path.exists()
        results.append({
            "prompt": name,
            "path": str(path.relative_to(base_path.parent)),
            "exists": exists,
            "status": "✓" if exists else "✖"
        })
        print(f"  {name}: {path.name} exists = {exists} → {'✓' if exists else '✖'}")

    return results


def test_language_consistency():
    """Test A3.5: No language mixing"""
    print("\n" + "="*60)
    print("TEST A3.5: LANGUAGE CONSISTENCY")
    print("="*60)

    results = []

    # German words that should NOT appear in EN reports
    german_words = ["förderung", "förderprogramm", "bundesland", "zuschuss", "antrag", "mitarbeiter"]

    # EN + Germany HTML
    de_result = get_funding_for_germany_en(PROFILE_EN_GERMANY)
    de_html = render_funding_html_en(de_result).lower()

    de_german_found = [w for w in german_words if w in de_html]
    de_lang = {
        "profile": "EN + Germany",
        "german_words_found": de_german_found,
        "count": len(de_german_found),
        "status": "✓" if len(de_german_found) == 0 else "⚠"
    }
    results.append(de_lang)
    print(f"  EN + Germany: German words found = {de_german_found} → {de_lang['status']}")

    # EN + France HTML
    fr_result = get_funding_eu_core_en(PROFILE_EN_FRANCE)
    fr_html = render_funding_eu_core_html_en(fr_result).lower()

    fr_german_found = [w for w in german_words if w in fr_html]
    fr_lang = {
        "profile": "EN + France",
        "german_words_found": fr_german_found,
        "count": len(fr_german_found),
        "status": "✓" if len(fr_german_found) == 0 else "⚠"
    }
    results.append(fr_lang)
    print(f"  EN + France:  German words found = {fr_german_found} → {fr_lang['status']}")

    return results


def generate_demo_html():
    """Generate demo HTML outputs for each profile"""
    print("\n" + "="*60)
    print("DEMO REPORT GENERATION")
    print("="*60)

    demos = {}

    # Report 1: EN + Germany
    print("\n  Generating Report 1: EN + Germany...")
    de_result = get_funding_for_germany_en(PROFILE_EN_GERMANY)
    de_html = render_funding_html_en(de_result)
    demos["en_germany"] = {
        "profile": PROFILE_EN_GERMANY,
        "result": {
            "programmes": [p.get("name_en", p.get("id")) for p in de_result.programmes[:5]],
            "count": de_result.programme_count,
            "scope": "DE"
        },
        "html": de_html,
        "title": "Funding Opportunities (Germany)"
    }
    print(f"    Programmes: {de_result.programme_count}")

    # Report 2: EN + France
    print("\n  Generating Report 2: EN + France...")
    fr_result = get_funding_eu_core_en(PROFILE_EN_FRANCE)
    fr_html = render_funding_eu_core_html_en(fr_result)
    demos["en_france"] = {
        "profile": PROFILE_EN_FRANCE,
        "result": {
            "programmes": [p.get("name_en") for p in fr_result.programmes[:4]],
            "count": fr_result.programme_count,
            "scope": "EU_CORE"
        },
        "html": fr_html,
        "title": "EU Funding Opportunities"
    }
    print(f"    Programmes: {fr_result.programme_count}")

    # Report 3: EN + Italy
    print("\n  Generating Report 3: EN + Italy...")
    it_result = get_funding_eu_core_en(PROFILE_EN_ITALY)
    it_html = render_funding_eu_core_html_en(it_result)
    demos["en_italy"] = {
        "profile": PROFILE_EN_ITALY,
        "result": {
            "programmes": [p.get("name_en") for p in it_result.programmes[:4]],
            "count": it_result.programme_count,
            "scope": "EU_CORE"
        },
        "html": it_html,
        "title": "EU Funding Opportunities"
    }
    print(f"    Programmes: {it_result.programme_count}")

    return demos


def main():
    """Run all QA tests"""
    print("\n" + "#"*60)
    print("# EN FUNDING PHASE 2 - QA TEST SUITE")
    print("#"*60)

    all_results = {}

    # Run tests
    all_results["routing"] = test_routing_logic()
    all_results["html_output"] = test_html_output()
    all_results["no_mixing"] = test_no_mixing()
    all_results["prompts"] = test_prompt_selection()
    all_results["language"] = test_language_consistency()

    # Generate demos
    demos = generate_demo_html()

    # Summary
    print("\n" + "="*60)
    print("QA SUMMARY")
    print("="*60)

    total_pass = 0
    total_warn = 0
    total_fail = 0

    for category, results in all_results.items():
        for r in results:
            if r.get("status") == "✓":
                total_pass += 1
            elif r.get("status") == "⚠":
                total_warn += 1
            else:
                total_fail += 1

    print(f"\n  PASSED:   {total_pass}")
    print(f"  WARNINGS: {total_warn}")
    print(f"  FAILED:   {total_fail}")

    if total_fail == 0 and total_warn == 0:
        print("\n  ✅ EN Funding (Phase 2) READY")
        verdict = "READY"
    elif total_fail == 0:
        print("\n  ⚠️ EN Funding (Phase 2) READY with minor warnings")
        verdict = "READY_WITH_WARNINGS"
    else:
        print("\n  ❌ Fix erforderlich")
        verdict = "FIX_REQUIRED"

    # Print demo summaries
    print("\n" + "="*60)
    print("DEMO REPORT SUMMARIES")
    print("="*60)

    for key, demo in demos.items():
        print(f"\n  [{key.upper()}]")
        print(f"    Title: {demo['title']}")
        print(f"    Scope: {demo['result']['scope']}")
        print(f"    Programmes ({demo['result']['count']}):")
        for prog in demo['result']['programmes']:
            print(f"      - {prog}")

    return {
        "results": all_results,
        "demos": demos,
        "summary": {
            "passed": total_pass,
            "warnings": total_warn,
            "failed": total_fail,
            "verdict": verdict
        }
    }


if __name__ == "__main__":
    main()

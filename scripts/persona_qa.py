#!/usr/bin/env python3
"""
Persona QA Script (Solo / Team / KMU) – DE & EN

- Lädt vordefinierte Testprofile (solo, team, kmu – de/en)
- Schickt sie an /api/briefings/submit
- Triggert /api/analyze/run
- Holt das Ergebnis (sections)
- Prüft leichtgewichtige Persona-Eigenschaften:

  - Tonalität (Suche nach bestimmten Schlüsselwörtern)
  - Governance-Level (Solo ≠ KMU)
  - Vorhandensein der neuen Sections (Monetarisierung, Skillplan, Templates)
"""

import json
import argparse
import requests
from pathlib import Path
from typing import Any, Dict, List

TEST_PROFILES = [
    # DE Solo
    {
        "name": "DE_solo",
        "path": "data/test_profiles_gold/solo_beratung_ki_assessments.json",
        "expected_size": "solo",
        "lang": "de",
    },
    # DE KMU
    {
        "name": "DE_kmu",
        "path": "data/test_profiles_gold/kmu_industrie_production_advisory.json",
        "expected_size": "kmu",
        "lang": "de",
    },
    # EN Solo
    {
        "name": "EN_solo",
        "path": "data/test_profiles_gold/solo_consulting_en_gold.json",
        "expected_size": "solo",
        "lang": "en",
    },
    # EN KMU
    {
        "name": "EN_kmu",
        "path": "data/test_profiles_gold/kmu_industry_en_gold.json",
        "expected_size": "kmu",
        "lang": "en",
    },
]

def load_profile(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
        return data

def submit_briefing(api_base: str, profile: dict) -> str:
    url = f"{api_base}/briefings/submit"
    r = requests.post(url, json=profile, timeout=60)
    r.raise_for_status()
    data = r.json()
    briefing_id: str = data.get("briefing_id", "")
    return briefing_id

def run_analysis(api_base: str, briefing_id: str) -> Dict[str, Any]:
    url = f"{api_base}/analyze/run"
    r = requests.post(url, json={"briefing_id": briefing_id}, timeout=300)
    r.raise_for_status()
    result: Dict[str, Any] = r.json()
    return result

def persona_checks(sections: dict, expected_size: str, lang: str) -> Dict[str, Any]:
    """
    Sehr einfache Heuristiken für QA:
    - Solo: keine schweren Governance-Wörter, Monetarisierungsblock vorhanden, Skillplan vorhanden
    - KMU: Governance-Wörter erlaubt, Texte etwas länger
    """
    warnings: List[str] = []
    results: Dict[str, Any] = {
        "monetarisierung_present": bool(sections.get("MONETARISIERUNG_HTML")),
        "skillplan_present": bool(sections.get("KI_SKILLPLAN_HTML")),
        "starter_templates_present": bool(sections.get("STARTER_TEMPLATES_HTML")),
        "ai_policy_present": bool(sections.get("AI_POLICY_MINI_HTML")),
        "warnings": warnings,
    }

    text_governance = sections.get("STRATEGIE_GOVERNANCE_HTML", "") or ""
    text_org = sections.get("ORG_CHANGE_HTML", "") or ""

    heavy_terms = ["Governance Framework", "Rollenmodell", "Verantwortlichkeitsmatrix"]
    lite_terms = ["Checkliste", "leichte Regeln", "Mini-Richtlinie"]

    # Solo: darf keine schweren Begriffe enthalten
    if expected_size == "solo":
        if any(term.lower() in (text_governance + text_org).lower() for term in heavy_terms):
            warnings.append("Solo: too heavy governance wording detected.")
        if not any(term.lower() in (text_governance + text_org).lower() for term in lite_terms):
            warnings.append("Solo: no light governance keywords found.")

    # KMU: sollte eher schwerere Begriffe enthalten
    if expected_size == "kmu":
        if not any(term.lower() in (text_governance + text_org).lower() for term in heavy_terms):
            warnings.append("KMU: governance text might be too light (no heavy terms).")

    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True, help="Backend API base URL, e.g. https://.../api")
    parser.add_argument("--email", required=False, help="Email (nur für Kontext/Logging)")
    args = parser.parse_args()

    api_base = args.base_url.rstrip("/")
    print(f"Persona QA – using API base: {api_base}")

    qa_results = []

    for cfg in TEST_PROFILES:
        name = cfg["name"]
        print(f"\n=== Persona Test: {name} ===")
        profile = load_profile(cfg["path"])

        # sicherstellen, dass lang & size stimmen
        answers = profile.get("answers", {})
        size = answers.get("unternehmensgroesse", cfg["expected_size"])
        lang = profile.get("lang", cfg["lang"])

        try:
            briefing_id = submit_briefing(api_base, profile)
            print(f"  → briefing_id: {briefing_id}")
            analysis = run_analysis(api_base, briefing_id)
            sections = analysis.get("sections", analysis)  # je nach API-Form

            checks = persona_checks(sections, expected_size=size, lang=lang)
            qa_results.append((name, size, lang, checks))

            print(f"  monetarisierung_present: {checks['monetarisierung_present']}")
            print(f"  skillplan_present:       {checks['skillplan_present']}")
            print(f"  starter_templates:       {checks['starter_templates_present']}")
            print(f"  ai_policy_present:       {checks['ai_policy_present']}")
            if checks["warnings"]:
                print("  WARNINGS:")
                for w in checks["warnings"]:
                    print(f"   - {w}")
            else:
                print("  No persona warnings.")

        except Exception as e:
            print(f"  ERROR during persona test {name}: {e}")

    print("\n=== Persona QA Summary ===")
    for name, size, lang, checks in qa_results:
        print(f"- {name} ({lang}, {size}) → "
              f"Monetarisierung={checks['monetarisierung_present']}, "
              f"Skillplan={checks['skillplan_present']}, "
              f"Templates={checks['starter_templates_present']}, "
              f"AI-Policy={checks['ai_policy_present']}, "
              f"Warnings={len(checks['warnings'])}")

if __name__ == "__main__":
    main()

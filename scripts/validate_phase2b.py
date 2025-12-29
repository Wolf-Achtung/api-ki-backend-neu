#!/usr/bin/env python3
"""
validate_phase2b.py – Validiert Phase 2b: Top-3 Maßnahmen + Executive Summary

Prüft dass:
1. Generische Phrasen wie "Minimal-Stack" entfernt wurden
2. hauptleistung und zeitersparnis_prioritaet individualisiert werden
3. Die Prompt-Dateien die neuen Regeln enthalten

Usage:
    python scripts/validate_phase2b.py
"""

import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# BRIEFING 369 SIMULATION
# ============================================================================
BRIEFING_369_MOCK = {
    "briefing_id": 369,
    "branche": "beratung",
    "unternehmensgroesse": "solo",
    "hauptleistung": "Fragebogen-Erstellung und GPT-gestützte Auswertung für Unternehmen",
    "zeitersparnis_prioritaet": "Umsetzung/Programmierung individueller Kundenprojekte",
    "ki_guardrails": "Keine Gesundheitsprognosen, keine Finanzberatung",
    "vision_3_jahre": "Skalierbare KI-Beratung mit automatisierten Analyse-Pipelines",
    "strategische_ziele": "Produktisierung, Content-Velocity, Wissensprozesse",
}

# ============================================================================
# VERBOTENE PHRASEN (müssen entfernt sein)
# ============================================================================
FORBIDDEN_PHRASES = [
    "Minimal-Stack festlegen",
    "Minimal-Stack definieren",
    "Standard-Workflow etablieren",
    "Review-Regel einführen",
    "Klarheit vor Komplexität",
    "Ein zentrales Tool",
    "Input → KI-Entwurf → Review",
]

# ============================================================================
# ERWARTETE INDIVIDUELLE BEGRIFFE (sollten vorhanden sein)
# ============================================================================
EXPECTED_INDIVIDUAL_TERMS = [
    "hauptleistung",
    "ZEITERSPARNIS_PRIORITAET",
    "KI_GUARDRAILS",
    "Fragebogen",  # Bezug zu Briefing 369
    "Template",
    "Bibliothek",
]


def validate_prompt_files():
    """Validiert die Prompt-Dateien."""

    print("=" * 70)
    print("🎯 PHASE 2b VALIDIERUNG: Prompt-Dateien")
    print("=" * 70)
    print()

    results = []

    # ========================================================================
    # CHECK 1: recommendations.md
    # ========================================================================
    print("=== CHECK 1: prompts/de/recommendations.md ===")

    recommendations_path = "prompts/de/recommendations.md"
    with open(recommendations_path, "r", encoding="utf-8") as f:
        recommendations_content = f.read()

    # Check 1.1: Forbidden phrases in HTML template removed
    check1_1_passed = True
    found_forbidden = []
    for phrase in FORBIDDEN_PHRASES:
        # Nur im HTML-Template prüfen, nicht in den Kommentaren
        # Suche nach phrase außerhalb von <!-- --> Kommentaren
        if phrase in recommendations_content:
            # Zähle Vorkommen außerhalb von Kommentaren
            lines = recommendations_content.split('\n')
            in_comment = False
            for line in lines:
                if '<!--' in line:
                    in_comment = True
                if '-->' in line:
                    in_comment = False
                if not in_comment and phrase in line:
                    check1_1_passed = False
                    found_forbidden.append(phrase)
                    break

    if check1_1_passed:
        results.append(("PASSED", "Forbidden phrases removed from HTML template"))
        print("  ✅ PASSED: Generische Phrasen aus HTML-Template entfernt")
    else:
        results.append(("FAILED", f"Forbidden phrases still in HTML: {found_forbidden}"))
        print(f"  ❌ FAILED: Generische Phrasen noch vorhanden: {found_forbidden}")

    # Check 1.2: Individual terms added
    check1_2_passed = True
    missing_terms = []
    for term in ["hauptleistung", "ZEITERSPARNIS_PRIORITAET", "KI_GUARDRAILS"]:
        if "{{" + term + "}}" not in recommendations_content:
            check1_2_passed = False
            missing_terms.append(term)

    if check1_2_passed:
        results.append(("PASSED", "Individual terms added to recommendations"))
        print("  ✅ PASSED: Individualisierungs-Variablen vorhanden")
    else:
        results.append(("FAILED", f"Missing terms: {missing_terms}"))
        print(f"  ❌ FAILED: Fehlende Variablen: {missing_terms}")

    # Check 1.3: PHASE 2b marker present
    if "PHASE 2b" in recommendations_content:
        results.append(("PASSED", "PHASE 2b marker present"))
        print("  ✅ PASSED: PHASE 2b Marker vorhanden")
    else:
        results.append(("FAILED", "PHASE 2b marker missing"))
        print("  ❌ FAILED: PHASE 2b Marker fehlt")

    print()

    # ========================================================================
    # CHECK 2: executive_summary.md
    # ========================================================================
    print("=== CHECK 2: prompts/de/executive_summary.md ===")

    exec_path = "prompts/de/executive_summary.md"
    with open(exec_path, "r", encoding="utf-8") as f:
        exec_content = f.read()

    # Check 2.1: Minimal-Stack example removed
    if '"3. Minimal-Stack festlegen"' in exec_content:
        results.append(("FAILED", "Minimal-Stack example still in executive_summary"))
        print("  ❌ FAILED: 'Minimal-Stack festlegen' Beispiel noch vorhanden")
    else:
        results.append(("PASSED", "Minimal-Stack example removed"))
        print("  ✅ PASSED: 'Minimal-Stack festlegen' Beispiel entfernt")

    # Check 2.2: ZEITERSPARNIS_PRIORITAET referenced
    if "{{ZEITERSPARNIS_PRIORITAET}}" in exec_content:
        results.append(("PASSED", "ZEITERSPARNIS_PRIORITAET referenced"))
        print("  ✅ PASSED: ZEITERSPARNIS_PRIORITAET wird referenziert")
    else:
        results.append(("FAILED", "ZEITERSPARNIS_PRIORITAET not referenced"))
        print("  ❌ FAILED: ZEITERSPARNIS_PRIORITAET nicht referenziert")

    # Check 2.3: hauptleistung referenced
    if "{{hauptleistung}}" in exec_content:
        results.append(("PASSED", "hauptleistung referenced"))
        print("  ✅ PASSED: hauptleistung wird referenziert")
    else:
        results.append(("FAILED", "hauptleistung not referenced"))
        print("  ❌ FAILED: hauptleistung nicht referenziert")

    # Check 2.4: PHASE 2b improvements added
    if "PHASE 2b" in exec_content:
        results.append(("PASSED", "PHASE 2b improvements present"))
        print("  ✅ PASSED: PHASE 2b Verbesserungen vorhanden")
    else:
        results.append(("FAILED", "PHASE 2b improvements missing"))
        print("  ❌ FAILED: PHASE 2b Verbesserungen fehlen")

    # Check 2.5: Konkrete Beispiele vorhanden
    if "KI-Berater:" in exec_content and "Steuerberater:" in exec_content:
        results.append(("PASSED", "Concrete examples added"))
        print("  ✅ PASSED: Konkrete Beispiele pro Branche vorhanden")
    else:
        results.append(("FAILED", "Concrete examples missing"))
        print("  ❌ FAILED: Konkrete Beispiele fehlen")

    print()

    # ========================================================================
    # GESAMTBEWERTUNG
    # ========================================================================
    print("=== GESAMTBEWERTUNG ===")
    print()

    passed_count = len([r for r in results if r[0] == "PASSED"])
    failed_count = len([r for r in results if r[0] == "FAILED"])
    total_count = len(results)

    print(f"Checks bestanden: {passed_count}/{total_count}")
    print(f"Checks fehlgeschlagen: {failed_count}")
    print()

    if failed_count == 0:
        print("🎉 STATUS: PHASE 2b PROMPT-ÄNDERUNGEN ERFOLGREICH!")
        print()
        print("Die Prompt-Dateien wurden aktualisiert:")
        print("- recommendations.md: Generische MUSS-Maßnahmen → Dynamisch")
        print("- executive_summary.md: ZEITERSPARNIS_PRIORITAET explizit")
        print()
        print("✅ READY FOR TESTING")
    else:
        print("⚠️  STATUS: NOCH PROBLEME GEFUNDEN")
        print()
        print("Fehlgeschlagene Checks:")
        for r in results:
            if r[0] == "FAILED":
                print(f"  - {r[1]}")

    # Speichere Ergebnis
    with open("/tmp/phase2b_prompt_validation.txt", "w", encoding="utf-8") as f:
        f.write("=== PHASE 2b PROMPT VALIDIERUNG ===\n\n")
        for r in results:
            status = "✅" if r[0] == "PASSED" else "❌"
            f.write(f"{status} {r[0]}: {r[1]}\n")
        f.write(f"\nGesamt: {passed_count}/{total_count} bestanden\n")

    print()
    print(f"✅ Validierung gespeichert: /tmp/phase2b_prompt_validation.txt")

    return failed_count == 0


if __name__ == "__main__":
    success = validate_prompt_files()
    sys.exit(0 if success else 1)

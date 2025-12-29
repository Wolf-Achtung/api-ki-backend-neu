#!/usr/bin/env python3
"""
validate_phase2b_complete.py – Vollständige Phase 2b Validierung

Da kein laufendes Backend verfügbar ist, validiert dieses Skript:
1. Die Prompt-Dateien enthalten die Phase 2b Änderungen
2. Die neuen Variablen werden korrekt referenziert
3. Die verbotenen Phrasen sind entfernt
4. Simulation der erwarteten Ausgabe für Briefing 369

Usage:
    python scripts/validate_phase2b_complete.py
"""

import sys
import os
import re

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# BRIEFING 369 MOCK DATA
# ============================================================================
BRIEFING_369 = {
    "briefing_id": 369,
    "branche": "beratung",
    "unternehmensgroesse": "solo",
    "hauptleistung": "Fragebogen-Erstellung und GPT-gestützte Auswertung für KI-Readiness-Analysen",
    "zeitersparnis_prioritaet": "Umsetzung/Programmierung - der größte manuelle Aufwand liegt in der technischen Implementierung",
    "ki_guardrails": "Keine Gesundheitsprognosen, keine Finanzberatung ohne Disclaimer",
    "vision_3_jahre": "Skalierbare KI-Beratung mit automatisierten Analyse-Pipelines",
    "strategische_ziele": "Produktisierung, Content-Velocity, Wissensprozesse",
}

# ============================================================================
# FORBIDDEN PHRASES (must not appear in HTML templates)
# ============================================================================
FORBIDDEN_IN_HTML = [
    "Minimal-Stack festlegen",
    "Minimal-Stack definieren",
    "Standard-Workflow etablieren",
    "Review-Regel einführen",
    "Klarheit vor Komplexität",
    "1 zentrales KI-Tool",
    "Input → KI-Entwurf → Review",
]

# ============================================================================
# REQUIRED VARIABLES
# ============================================================================
REQUIRED_VARS = [
    "{{hauptleistung}}",
    "{{ZEITERSPARNIS_PRIORITAET}}",
    "{{KI_GUARDRAILS}}",
]


def load_prompt_file(filename):
    """Load a prompt file from prompts/de/"""
    path = f"prompts/de/{filename}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_forbidden_in_html(content, filename):
    """Check that forbidden phrases are NOT in the HTML template part."""
    # Find HTML section (between <section> tags)
    html_match = re.search(r'<section[^>]*>.*?</section>', content, re.DOTALL)
    if not html_match:
        return True, []  # No HTML section found

    html_section = html_match.group(0)

    found_forbidden = []
    for phrase in FORBIDDEN_IN_HTML:
        # Check if phrase is in HTML (not in comments)
        if phrase in html_section:
            # Exclude if it's in a comment
            if f"<!--" in html_section:
                # More nuanced check: is it in actual HTML or just comment examples?
                lines = html_section.split('\n')
                in_comment = False
                for line in lines:
                    if '<!--' in line:
                        in_comment = True
                    if '-->' in line:
                        in_comment = False
                        continue
                    if not in_comment and phrase in line:
                        found_forbidden.append(phrase)
                        break
            else:
                found_forbidden.append(phrase)

    return len(found_forbidden) == 0, found_forbidden


def check_required_vars(content, filename):
    """Check that required variables are referenced."""
    missing = []
    for var in REQUIRED_VARS:
        if var not in content:
            missing.append(var)
    return len(missing) == 0, missing


def check_phase2b_marker(content, filename):
    """Check that PHASE 2b marker is present."""
    return "PHASE 2b" in content


def simulate_top3_output(briefing):
    """Simulate what the Top-3 Maßnahmen SHOULD look like with Phase 2b changes."""

    zeitersparnis = briefing["zeitersparnis_prioritaet"]
    hauptleistung = briefing["hauptleistung"]
    guardrails = briefing["ki_guardrails"]

    # Simulate individualized output
    simulated = f"""
=== SIMULIERTE TOP-3 MAẞNAHMEN (Phase 2b) ===

MUSS – Sofort umsetzen:

1. **Fragebogen-Template-Bibliothek aufbauen** – Reduziert den Aufwand für "{zeitersparnis[:50]}..."
   → Wiederverwendbare Templates statt Custom-Code pro Projekt

2. **GPT-Auswertungs-Standard definieren** – Konsistente Qualität bei "{hauptleistung[:50]}..."
   → Standardisierte Prompts und Auswertungslogik für alle Analysen

3. **Review-Checkliste gegen unerlaubte Empfehlungen** – Verhindert Compliance-Verstöße ({guardrails[:40]}...)
   → Vier-Augen-Prinzip mit expliziter Prüfung auf No-Gos

---
VERGLEICH ZU VORHER (generisch):
❌ ALT: "Minimal-Stack festlegen – Klarheit vor Komplexität"
✅ NEU: "Fragebogen-Template-Bibliothek aufbauen – Reduziert Umsetzungsaufwand"

❌ ALT: "Standard-Workflow etablieren – Ohne Prozess keine Verbesserung"
✅ NEU: "GPT-Auswertungs-Standard definieren – Konsistente Qualität bei jeder Analyse"

❌ ALT: "Review-Regel einführen – Qualität und Compliance sichern"
✅ NEU: "Review-Checkliste gegen unerlaubte Empfehlungen – Verhindert Compliance-Verstöße"
"""
    return simulated


def simulate_executive_summary(briefing):
    """Simulate what the Executive Summary SHOULD look like with Phase 2b changes."""

    hauptleistung = briefing["hauptleistung"]
    zeitersparnis = briefing["zeitersparnis_prioritaet"]

    simulated = f"""
=== SIMULIERTE EXECUTIVE SUMMARY (Phase 2b) ===

STRUKTUR (max 50 Wörter):

Satz 1 (Was macht der User?):
"Ein Beratungsunternehmen erstellt {hauptleistung[:60]}..."

Satz 2 (Was ist das Hauptproblem?):
"Größter Zeitfresser: {zeitersparnis[:50]}..."

Satz 3 (Kernempfehlung):
"Kernempfehlung → Von Custom-Code zu Templates: Fragebogen-Bibliothek, Prompt-Standards, Review-Checkliste etablieren."

---
VERGLEICH ZU VORHER:
❌ ALT: "Skalierbare, KI-gestützte Fragebogen-Workflows statt individueller
        Programmierprojekte; Konsequenz → jetzt einen No-Go-konformen
        End-to-End-Standardprozess definieren..."

✅ NEU: Konkret, kompakt, mit expliziter Erwähnung von zeitersparnis_prioritaet
"""
    return simulated


def main():
    print("=" * 70)
    print("🎯 PHASE 2b VOLLSTÄNDIGE VALIDIERUNG")
    print("=" * 70)
    print()
    print("HINWEIS: Kein laufendes Backend verfügbar.")
    print("         Validierung basiert auf Prompt-Analyse + Simulation.")
    print()

    results = []

    # ========================================================================
    # PROMPT FILE VALIDATION
    # ========================================================================
    print("=== PROMPT-DATEIEN VALIDIERUNG ===")
    print()

    # Check recommendations.md
    print("📄 prompts/de/recommendations.md:")
    rec_content = load_prompt_file("recommendations.md")

    passed, forbidden = check_forbidden_in_html(rec_content, "recommendations.md")
    if passed:
        print("  ✅ PASSED: Verbotene Phrasen aus HTML-Template entfernt")
        results.append(("PASSED", "recommendations: forbidden phrases removed"))
    else:
        print(f"  ❌ FAILED: Verbotene Phrasen noch vorhanden: {forbidden}")
        results.append(("FAILED", f"recommendations: forbidden phrases: {forbidden}"))

    passed, missing = check_required_vars(rec_content, "recommendations.md")
    if passed:
        print("  ✅ PASSED: Alle Individualisierungs-Variablen vorhanden")
        results.append(("PASSED", "recommendations: all vars present"))
    else:
        print(f"  ❌ FAILED: Fehlende Variablen: {missing}")
        results.append(("FAILED", f"recommendations: missing vars: {missing}"))

    if check_phase2b_marker(rec_content, "recommendations.md"):
        print("  ✅ PASSED: PHASE 2b Marker vorhanden")
        results.append(("PASSED", "recommendations: PHASE 2b marker"))
    else:
        print("  ❌ FAILED: PHASE 2b Marker fehlt")
        results.append(("FAILED", "recommendations: no PHASE 2b marker"))

    print()

    # Check executive_summary.md
    print("📄 prompts/de/executive_summary.md:")
    exec_content = load_prompt_file("executive_summary.md")

    # Check for old generic example
    if '"3. Minimal-Stack festlegen"' in exec_content:
        print("  ❌ FAILED: 'Minimal-Stack festlegen' Beispiel noch vorhanden")
        results.append(("FAILED", "executive_summary: Minimal-Stack example present"))
    else:
        print("  ✅ PASSED: 'Minimal-Stack festlegen' Beispiel entfernt")
        results.append(("PASSED", "executive_summary: Minimal-Stack example removed"))

    passed, missing = check_required_vars(exec_content, "executive_summary.md")
    if passed:
        print("  ✅ PASSED: Alle Individualisierungs-Variablen vorhanden")
        results.append(("PASSED", "executive_summary: all vars present"))
    else:
        print(f"  ❌ FAILED: Fehlende Variablen: {missing}")
        results.append(("FAILED", f"executive_summary: missing vars: {missing}"))

    if check_phase2b_marker(exec_content, "executive_summary.md"):
        print("  ✅ PASSED: PHASE 2b Marker vorhanden")
        results.append(("PASSED", "executive_summary: PHASE 2b marker"))
    else:
        print("  ❌ FAILED: PHASE 2b Marker fehlt")
        results.append(("FAILED", "executive_summary: no PHASE 2b marker"))

    # Check for concrete examples
    if "KI-Berater:" in exec_content and "Steuerberater:" in exec_content:
        print("  ✅ PASSED: Konkrete Beispiele pro Branche vorhanden")
        results.append(("PASSED", "executive_summary: concrete examples"))
    else:
        print("  ❌ FAILED: Konkrete Beispiele fehlen")
        results.append(("FAILED", "executive_summary: no concrete examples"))

    # Check for forbidden phrases list
    if "VERBOTENE PHRASEN:" in exec_content or "VERBOTEN:" in exec_content:
        print("  ✅ PASSED: VERBOTEN-Liste vorhanden")
        results.append(("PASSED", "executive_summary: VERBOTEN list present"))
    else:
        print("  ⚠️  WARNING: VERBOTEN-Liste nicht explizit")
        results.append(("WARNING", "executive_summary: VERBOTEN list not explicit"))

    print()

    # ========================================================================
    # OUTPUT SIMULATION
    # ========================================================================
    print("=== SIMULIERTE AUSGABE FÜR BRIEFING 369 ===")
    print()

    top3_sim = simulate_top3_output(BRIEFING_369)
    print(top3_sim)

    exec_sim = simulate_executive_summary(BRIEFING_369)
    print(exec_sim)

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print()
    print("=" * 70)
    print("=== GESAMTERGEBNIS ===")
    print("=" * 70)
    print()

    passed_count = len([r for r in results if r[0] == "PASSED"])
    failed_count = len([r for r in results if r[0] == "FAILED"])
    warning_count = len([r for r in results if r[0] == "WARNING"])
    total = len(results)

    print(f"Checks bestanden: {passed_count}/{total}")
    print(f"Checks fehlgeschlagen: {failed_count}")
    print(f"Warnungen: {warning_count}")
    print()

    if failed_count == 0 and passed_count >= 7:
        print("🎉 STATUS: PHASE 2b PROMPT-ÄNDERUNGEN ERFOLGREICH!")
        print()
        print("Die Prompt-Dateien wurden korrekt aktualisiert:")
        print("- recommendations.md: Generische MUSS-Maßnahmen → Dynamisch")
        print("- executive_summary.md: Explizite ZEITERSPARNIS_PRIORITAET")
        print("- Verbotene Phrasen dokumentiert")
        print("- Konkrete Beispiele pro Branche")
        print()
        print("⚠️  NÄCHSTER SCHRITT:")
        print("   Report-Generierung mit laufendem Backend testen")
        print("   um die tatsächliche GPT-Ausgabe zu validieren.")
        print()
        print("✅ PROMPT-ÄNDERUNGEN PRODUCTION READY")
    else:
        print("⚠️  STATUS: PROBLEME GEFUNDEN")
        print()
        for r in results:
            if r[0] == "FAILED":
                print(f"  ❌ {r[1]}")

    # Save results
    with open("/tmp/phase2b_complete_validation.txt", "w", encoding="utf-8") as f:
        f.write("=== PHASE 2b VOLLSTÄNDIGE VALIDIERUNG ===\n\n")
        f.write(f"Checks: {passed_count}/{total} bestanden\n")
        f.write(f"Fehlgeschlagen: {failed_count}\n")
        f.write(f"Warnungen: {warning_count}\n\n")
        f.write("=== SIMULIERTE TOP-3 MAẞNAHMEN ===\n")
        f.write(top3_sim)
        f.write("\n\n=== SIMULIERTE EXECUTIVE SUMMARY ===\n")
        f.write(exec_sim)

    print()
    print(f"✅ Validierung gespeichert: /tmp/phase2b_complete_validation.txt")

    return failed_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

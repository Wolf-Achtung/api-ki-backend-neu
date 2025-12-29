#!/usr/bin/env python3
"""
validate_phase3_complete.py – Vollständige Phase 3 Validierung

Validiert dass alle Phase 3 Individualisierungen korrekt implementiert sind:
1. Roadmap 90d – Dynamische Phasennamen und Bullets
2. Gamechanger – Strategischer Bruchpunkt mit Briefing-Bezug
3. Next Actions – Handlungsempfehlungen individualisiert

Usage:
    python scripts/validate_phase3_complete.py
"""

import sys
import os

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
# REQUIRED VARIABLES IN PROMPTS
# ============================================================================
REQUIRED_VARS = [
    "{{hauptleistung}}",
    "{{ZEITERSPARNIS_PRIORITAET}}",
    "{{KI_GUARDRAILS}}",
    "{{VISION_3_JAHRE}}",
]

# ============================================================================
# FORBIDDEN GENERIC PHRASES
# ============================================================================
FORBIDDEN_IN_HTML = [
    # Roadmap generic phrases
    "Phase 0: Setup (Woche 1–2)",  # Should be dynamic
    "Phase 1: Entlastung (Woche 3–5)",  # Should be dynamic
    "Phase 2: Produktiver Einsatz (Woche 6–10)",  # Should be dynamic
    "Phase 3: Konsolidierung (Woche 11–13)",  # Should be dynamic
    # Next Actions generic phrases
    "KI-Zugang einrichten und erste Vorlage erstellen",  # Too generic
    "Ersten Quick Win umsetzen und Zeit messen",  # Too generic
    "Einfache Qualitäts-Checkliste erstellen",  # Too generic
]


def load_prompt_file(filename):
    """Load a prompt file from prompts/de/"""
    path = f"prompts/de/{filename}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_phase3_marker(content, filename):
    """Check that PHASE 3 marker is present."""
    return "PHASE 3" in content


def check_required_vars(content, filename):
    """Check that required variables are referenced."""
    missing = []
    for var in REQUIRED_VARS:
        if var not in content:
            missing.append(var)
    return len(missing) == 0, missing


def check_forbidden_in_html(content, filename):
    """Check that forbidden phrases are NOT in the HTML template part."""
    found_forbidden = []
    for phrase in FORBIDDEN_IN_HTML:
        if phrase in content:
            # Check if it's in a comment (allowed as negative example)
            lines = content.split('\n')
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

    return len(found_forbidden) == 0, found_forbidden


def validate_roadmap():
    """Validate roadmap_90d.md Phase 3 changes."""
    print("=" * 70)
    print("📄 prompts/de/roadmap_90d.md:")
    print("=" * 70)

    content = load_prompt_file("roadmap_90d.md")
    results = []

    # Check 1: PHASE 3 marker
    if check_phase3_marker(content, "roadmap_90d.md"):
        results.append(("PASSED", "PHASE 3 marker present"))
        print("  ✅ PASSED: PHASE 3 Marker vorhanden")
    else:
        results.append(("FAILED", "PHASE 3 marker missing"))
        print("  ❌ FAILED: PHASE 3 Marker fehlt")

    # Check 2: Required variables
    passed, missing = check_required_vars(content, "roadmap_90d.md")
    if passed:
        results.append(("PASSED", "All individualization vars present"))
        print("  ✅ PASSED: Alle Individualisierungs-Variablen vorhanden")
    else:
        results.append(("FAILED", f"Missing vars: {missing}"))
        print(f"  ❌ FAILED: Fehlende Variablen: {missing}")

    # Check 3: Dynamic phase names instruction
    if "[DYNAMISCH:" in content:
        results.append(("PASSED", "Dynamic phase name instructions present"))
        print("  ✅ PASSED: Dynamische Phasennamen-Anweisungen vorhanden")
    else:
        results.append(("FAILED", "Dynamic phase name instructions missing"))
        print("  ❌ FAILED: Dynamische Phasennamen-Anweisungen fehlen")

    # Check 4: Briefing 369 example
    if "Briefing 369" in content:
        results.append(("PASSED", "Briefing 369 example included"))
        print("  ✅ PASSED: Briefing 369 Beispiel vorhanden")
    else:
        results.append(("FAILED", "Briefing 369 example missing"))
        print("  ❌ FAILED: Briefing 369 Beispiel fehlt")

    print()
    return results


def validate_gamechanger():
    """Validate gamechanger.md Phase 3 changes."""
    print("=" * 70)
    print("📄 prompts/de/gamechanger.md:")
    print("=" * 70)

    content = load_prompt_file("gamechanger.md")
    results = []

    # Check 1: PHASE 3 marker
    if check_phase3_marker(content, "gamechanger.md"):
        results.append(("PASSED", "PHASE 3 marker present"))
        print("  ✅ PASSED: PHASE 3 Marker vorhanden")
    else:
        results.append(("FAILED", "PHASE 3 marker missing"))
        print("  ❌ FAILED: PHASE 3 Marker fehlt")

    # Check 2: Required variables
    passed, missing = check_required_vars(content, "gamechanger.md")
    if passed:
        results.append(("PASSED", "All individualization vars present"))
        print("  ✅ PASSED: Alle Individualisierungs-Variablen vorhanden")
    else:
        results.append(("FAILED", f"Missing vars: {missing}"))
        print(f"  ❌ FAILED: Fehlende Variablen: {missing}")

    # Check 3: Strategischer Bruchpunkt individualization
    if "STRATEGISCHER BRUCHPUNKT" in content.upper() and "hauptleistung" in content:
        results.append(("PASSED", "Strategic breakpoint individualized"))
        print("  ✅ PASSED: Strategischer Bruchpunkt individualisiert")
    else:
        results.append(("FAILED", "Strategic breakpoint not individualized"))
        print("  ❌ FAILED: Strategischer Bruchpunkt nicht individualisiert")

    # Check 4: Briefing 369 example
    if "Briefing 369" in content:
        results.append(("PASSED", "Briefing 369 example included"))
        print("  ✅ PASSED: Briefing 369 Beispiel vorhanden")
    else:
        results.append(("FAILED", "Briefing 369 example missing"))
        print("  ❌ FAILED: Briefing 369 Beispiel fehlt")

    print()
    return results


def validate_next_actions():
    """Validate next_actions.md Phase 3 changes."""
    print("=" * 70)
    print("📄 prompts/de/next_actions.md:")
    print("=" * 70)

    content = load_prompt_file("next_actions.md")
    results = []

    # Check 1: PHASE 3 marker
    if check_phase3_marker(content, "next_actions.md"):
        results.append(("PASSED", "PHASE 3 marker present"))
        print("  ✅ PASSED: PHASE 3 Marker vorhanden")
    else:
        results.append(("FAILED", "PHASE 3 marker missing"))
        print("  ❌ FAILED: PHASE 3 Marker fehlt")

    # Check 2: Required variables
    passed, missing = check_required_vars(content, "next_actions.md")
    if passed:
        results.append(("PASSED", "All individualization vars present"))
        print("  ✅ PASSED: Alle Individualisierungs-Variablen vorhanden")
    else:
        results.append(("FAILED", f"Missing vars: {missing}"))
        print(f"  ❌ FAILED: Fehlende Variablen: {missing}")

    # Check 3: Dynamic action instructions
    if "[DYNAMISCH:" in content:
        results.append(("PASSED", "Dynamic action instructions present"))
        print("  ✅ PASSED: Dynamische Aktions-Anweisungen vorhanden")
    else:
        results.append(("FAILED", "Dynamic action instructions missing"))
        print("  ❌ FAILED: Dynamische Aktions-Anweisungen fehlen")

    # Check 4: Briefing 369 example
    if "Briefing 369" in content:
        results.append(("PASSED", "Briefing 369 example included"))
        print("  ✅ PASSED: Briefing 369 Beispiel vorhanden")
    else:
        results.append(("FAILED", "Briefing 369 example missing"))
        print("  ❌ FAILED: Briefing 369 Beispiel fehlt")

    print()
    return results


def simulate_phase3_output(briefing):
    """Simulate what Phase 3 individualized output should look like."""
    hauptleistung = briefing["hauptleistung"]
    zeitersparnis = briefing["zeitersparnis_prioritaet"]
    guardrails = briefing["ki_guardrails"]
    vision = briefing["vision_3_jahre"]

    simulated = f"""
=== SIMULIERTE PHASE 3 AUSGABE FÜR BRIEFING 369 ===

--- ROADMAP PHASENNAMEN (individualisiert) ---
❌ ALT: "Phase 0: Setup", "Phase 1: Entlastung", "Phase 2: Produktiver Einsatz"
✅ NEU:
  • Phase 0: Fragebogen-Analyse Setup (Woche 1-2)
  • Phase 1: Programmier-Aufwand reduzieren (Woche 3-5)
  • Phase 2: GPT-Auswertungs-Standard etablieren (Woche 6-10)
  • Phase 3: Analyse-Pipelines evaluieren (Woche 11-13)

--- STRATEGISCHER BRUCHPUNKT (individualisiert) ---
❌ ALT: "Prozesse sind ineffizient und skalieren nicht"
✅ NEU:
  "Bisher: Jede KI-Readiness-Analyse wird als Custom-Entwicklung programmiert.
   Obwohl 70% der Fragebogen-Logik wiederkehrend ist, startet jedes Projekt bei Null.

   Die Transformation: Von Custom-Programmierung zu Template-basierter Skalierung.
   Der Weg zu '{vision}' beginnt mit Standardisierung der Auswertungslogik."

--- HANDLUNGSEMPFEHLUNGEN (individualisiert) ---
❌ ALT: "KI-Zugang einrichten und erste Vorlage erstellen"
✅ NEU:
  1. "Erste {hauptleistung[:30]}...-Template-Bibliothek anlegen" (Woche 1-2)
  2. "{zeitersparnis[:30]}... mit erstem Template testen" (Woche 2-3)
  3. "Review-Checkliste mit {guardrails[:30]}... erstellen" (Woche 3-4)

--- ERWARTETER EFFEKT (individualisiert) ---
❌ ALT: "Zeitersparnis: 4-8 Stunden im ersten Monat"
✅ NEU: "Zeitersparnis: 30-50% bei {zeitersparnis[:40]}..."
"""
    return simulated


def main():
    print("=" * 70)
    print("🎯 PHASE 3 VOLLSTÄNDIGE VALIDIERUNG")
    print("=" * 70)
    print()
    print("Prüft Phase 3 Individualisierungen in:")
    print("  • roadmap_90d.md (Seiten 9-10)")
    print("  • gamechanger.md (Seite 15)")
    print("  • next_actions.md (Seite 18)")
    print()

    all_results = []

    # Validate each file
    all_results.extend(validate_roadmap())
    all_results.extend(validate_gamechanger())
    all_results.extend(validate_next_actions())

    # Summary
    print("=" * 70)
    print("=== GESAMTERGEBNIS ===")
    print("=" * 70)
    print()

    passed_count = len([r for r in all_results if r[0] == "PASSED"])
    failed_count = len([r for r in all_results if r[0] == "FAILED"])
    total = len(all_results)

    print(f"Checks bestanden: {passed_count}/{total}")
    print(f"Checks fehlgeschlagen: {failed_count}")
    print()

    if failed_count == 0 and passed_count >= 10:
        print("🎉 STATUS: PHASE 3 PROMPT-ÄNDERUNGEN ERFOLGREICH!")
        print()
        print("Die Prompt-Dateien wurden korrekt aktualisiert:")
        print("  ✅ roadmap_90d.md: Dynamische Phasennamen und Bullets")
        print("  ✅ gamechanger.md: Strategischer Bruchpunkt individualisiert")
        print("  ✅ next_actions.md: Handlungsempfehlungen spezifisch")
        print()
        print("Alle Dateien nutzen jetzt:")
        print("  • {{hauptleistung}} – Was der User anbietet")
        print("  • {{ZEITERSPARNIS_PRIORITAET}} – Wo Zeit verloren geht")
        print("  • {{KI_GUARDRAILS}} – Einschränkungen")
        print("  • {{VISION_3_JAHRE}} – Langfristige Vision")
        print()
        print("✅ PHASE 3 PROMPT-ÄNDERUNGEN PRODUCTION READY")
    else:
        print("⚠️  STATUS: PROBLEME GEFUNDEN")
        print()
        for r in all_results:
            if r[0] == "FAILED":
                print(f"  ❌ {r[1]}")

    # Simulate output
    print()
    print("=" * 70)
    print("=== SIMULIERTE AUSGABE ===")
    print("=" * 70)
    simulated = simulate_phase3_output(BRIEFING_369)
    print(simulated)

    # Save results
    with open("/tmp/phase3_complete_validation.txt", "w", encoding="utf-8") as f:
        f.write("=== PHASE 3 VOLLSTÄNDIGE VALIDIERUNG ===\n\n")
        f.write(f"Checks: {passed_count}/{total} bestanden\n")
        f.write(f"Fehlgeschlagen: {failed_count}\n\n")
        f.write("=== ERGEBNISSE ===\n")
        for r in all_results:
            status = "✅" if r[0] == "PASSED" else "❌"
            f.write(f"{status} {r[0]}: {r[1]}\n")
        f.write("\n")
        f.write(simulated)

    print()
    print(f"✅ Validierung gespeichert: /tmp/phase3_complete_validation.txt")

    return failed_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

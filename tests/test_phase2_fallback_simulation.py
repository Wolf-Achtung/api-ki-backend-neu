#!/usr/bin/env python3
"""
PHASE 2: Fallback Simulation Test

Testet den neuen dynamischen Quick Wins Fallback OHNE Datenbankzugriff.
Simuliert verschiedene Briefings und zeigt die generierten Quick Wins.

Run with:
    python tests/test_phase2_fallback_simulation.py
"""

import sys
from pathlib import Path

# Minimale Mock-Umgebung für den Import
class MockSession:
    pass

# Patch sqlalchemy before import
class MockSQLAlchemy:
    class orm:
        Session = MockSession

sys.modules['sqlalchemy'] = type(sys)('sqlalchemy')
sys.modules['sqlalchemy'].orm = MockSQLAlchemy.orm
sys.modules['sqlalchemy.orm'] = MockSQLAlchemy.orm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def simulate_quick_wins_fallback():
    """
    Simuliert den Quick Wins Fallback für verschiedene Briefings.
    """
    print("=" * 70)
    print("PHASE 2: QUICK WINS FALLBACK SIMULATION")
    print("=" * 70)
    print()

    # ===== TEST BRIEFINGS =====
    briefings = [
        {
            "name": "KI-Berater (Briefing 368)",
            "briefing": {
                "branche": "Beratung",
                "BRANCHE_LABEL": "Beratung",
                "unternehmensgroesse": "solo",
                "UNTERNEHMENSGROESSE_LABEL": "Solo-Selbstständig",
                "hauptleistung": "Beratung von Unternehmen zur Integration von KI mittels Fragebogen und GPT-Auswertung",
                "zeitersparnis_prioritaet": "Umsetzung und Programmierung und überprüfen der Machbarkeit",
                "lang": "de",
            },
            "scores": {"security": 60, "governance": 70, "overall": 70},
        },
        {
            "name": "Social Media Manager",
            "briefing": {
                "branche": "Marketing",
                "BRANCHE_LABEL": "Marketing & Kommunikation",
                "unternehmensgroesse": "solo",
                "UNTERNEHMENSGROESSE_LABEL": "Solo-Selbstständig",
                "hauptleistung": "Social Media Management für lokale Restaurants, Content-Erstellung",
                "zeitersparnis_prioritaet": "Bildbearbeitung und Texterstellung für Posts",
                "lang": "de",
            },
            "scores": {"security": 70, "governance": 55, "overall": 65},
        },
        {
            "name": "Steuerberater (niedriger Security-Score)",
            "briefing": {
                "branche": "Finanzen",
                "BRANCHE_LABEL": "Finanzdienstleistungen",
                "unternehmensgroesse": "team",
                "UNTERNEHMENSGROESSE_LABEL": "Kleines Team (2-5)",
                "hauptleistung": "Steuerberatung für Freiberufler und kleine Unternehmen",
                "zeitersparnis_prioritaet": "Mandantenkorrespondenz und Dokumentenablage",
                "lang": "de",
            },
            "scores": {"security": 35, "governance": 60, "overall": 55},  # NIEDRIGER Security!
        },
    ]

    for test in briefings:
        print(f"\n{'='*70}")
        print(f"BRIEFING: {test['name']}")
        print(f"{'='*70}")
        print(f"hauptleistung: {test['briefing'].get('hauptleistung', '')[:60]}...")
        print(f"zeitersparnis: {test['briefing'].get('zeitersparnis_prioritaet', '')}")
        print(f"security_score: {test['scores'].get('security', 50)}")
        print()

        # Simuliere den Fallback-Handler direkt (kopiert aus gpt_analyze.py)
        quick_wins_html = generate_quick_wins_fallback(test['briefing'], test['scores'])

        print("GENERIERTE QUICK WINS:")
        print("-" * 70)
        # Bereinige HTML für Anzeige
        import re
        clean = re.sub(r'<[^>]+>', '', quick_wins_html)
        clean = re.sub(r'\n\s*\n', '\n', clean)
        for line in clean.strip().split('\n'):
            if line.strip():
                print(f"  {line.strip()[:75]}")
        print()


def generate_quick_wins_fallback(briefing, scores):
    """
    Direkte Kopie der neuen Quick Wins Fallback-Logik aus gpt_analyze.py
    """
    # Briefing-Daten extrahieren
    branche = briefing.get("BRANCHE_LABEL") or briefing.get("branche", "Unternehmen")
    size_label = briefing.get("UNTERNEHMENSGROESSE_LABEL") or briefing.get("unternehmensgroesse", "")
    hauptleistung = briefing.get("hauptleistung", "")
    zeitersparnis = briefing.get("zeitersparnis_prioritaet", "")
    score_security = scores.get("security", 50)
    score_governance = scores.get("governance", 50)

    # Size-Erkennung
    size_raw = size_label.lower()
    if "solo" in size_raw or "freiberuf" in size_raw:
        size_group = "solo"
    elif "team" in size_raw or "2" in size_raw:
        size_group = "team"
    else:
        size_group = "kmu"

    # Offering Label (vereinfacht)
    offering_label = hauptleistung[:30] + "..." if hauptleistung else "Ihre Kernleistung"

    # Dynamische Quick Wins generieren
    qw_items = []

    # Quick Win 1: IMMER basierend auf zeitersparnis_prioritaet
    if zeitersparnis:
        qw_items.append(f"""<li><strong>Prozessoptimierung für "{zeitersparnis[:50]}...":</strong>
KI-gestützte Automatisierung der zeitintensivsten Aufgabe, die Sie genannt haben.
Nutzen Sie Claude/GPT für Vorlagen und Standardisierung. <em>Ersparnis: 8-12 h/Monat</em></li>""")
    else:
        qw_items.append(f"""<li><strong>Kernprozess-Automatisierung:</strong>
Identifizieren Sie den zeitintensivsten wiederkehrenden Prozess in "{hauptleistung or branche}"
und erstellen Sie KI-gestützte Vorlagen. <em>Ersparnis: 8-12 h/Monat</em></li>""")

    # Quick Win 2: Basierend auf hauptleistung
    if hauptleistung:
        qw_items.append(f"""<li><strong>KI-Templates für {offering_label}:</strong>
Erstellen Sie strukturierte Vorlagen für "{hauptleistung[:60]}..." mit KI-Unterstützung.
Standardisierte Outputs bei gleichbleibender Qualität. <em>Ersparnis: 6-10 h/Monat</em></li>""")
    else:
        qw_items.append(f"""<li><strong>Dokumenten-Vorlagen standardisieren:</strong>
Nutzen Sie KI für wiederkehrende Dokumente und Berichte in Ihrem Bereich {branche}.
<em>Ersparnis: 6-10 h/Monat</em></li>""")

    # Quick Win 3: Score-abhängig (Security < 50 = Security Quick Win)
    if score_security < 50:
        qw_items.append(f"""<li><strong>🔒 KI-Sicherheitsrichtlinie erstellen:</strong>
Ihr Security-Score liegt bei {score_security}/100 - definieren Sie klare Regeln für den KI-Einsatz:
Welche Daten dürfen in welche Tools? Erstellen Sie eine einfache Checkliste. <em>Priorität: Hoch</em></li>""")
    elif score_governance < 50:
        qw_items.append(f"""<li><strong>📋 KI-Governance Light:</strong>
Ihr Governance-Score liegt bei {score_governance}/100 - legen Sie fest, wer welche KI-Tools nutzen darf
und wie Ergebnisse geprüft werden. Einfache Dokumentation reicht. <em>Priorität: Hoch</em></li>""")
    else:
        qw_items.append(f"""<li><strong>Meeting-Protokolle automatisieren:</strong>
Nutzen Sie Tools wie Otter.ai oder Fathom für automatische Transkription und Zusammenfassung.
<em>Ersparnis: 4-6 h/Monat</em></li>""")

    # Quick Win 4: Branchen-/Größen-spezifisch
    if size_group == "solo":
        qw_items.append(f"""<li><strong>Persönliche Prompt-Bibliothek:</strong>
Sammeln Sie Ihre besten Prompts für wiederkehrende Aufgaben in {branche}.
10-15 Vorlagen decken 80% Ihres Alltags ab. <em>Ersparnis: 3-5 h/Monat</em></li>""")
    elif size_group == "team":
        qw_items.append(f"""<li><strong>Team Prompt-Repository:</strong>
Erstellen Sie ein geteiltes Dokument mit den besten Prompts für Ihr Team.
Jedes Teammitglied trägt 2-3 bewährte Vorlagen bei. <em>Ersparnis: 5-8 h/Monat</em></li>""")
    else:
        qw_items.append(f"""<li><strong>KI-Wissenstransfer im Team:</strong>
Etablieren Sie einen monatlichen "KI-Learnings"-Austausch zwischen Abteilungen.
Erfolgreiche Anwendungen werden dokumentiert und geteilt. <em>Ersparnis: 10-15 h/Monat</em></li>""")

    qw_html = "\n".join(qw_items)

    return f"""<ul>
{qw_html}
</ul>
<p class="small muted">Individualisiert für {branche} · {size_label} · basierend auf Ihren Angaben</p>"""


def validate_results():
    """Validiere die generierten Quick Wins"""
    print()
    print("=" * 70)
    print("VALIDIERUNG")
    print("=" * 70)
    print()

    # Test: KI-Berater bekommt NICHT "E-Mail-Automatisierung"
    briefing = {
        "branche": "Beratung",
        "BRANCHE_LABEL": "Beratung",
        "hauptleistung": "KI-Beratung mittels Fragebogen",
        "zeitersparnis_prioritaet": "Programmierung",
        "UNTERNEHMENSGROESSE_LABEL": "Solo",
    }
    scores = {"security": 60, "governance": 70}

    result = generate_quick_wins_fallback(briefing, scores)

    checks = [
        ("E-Mail-Automatisierung" not in result, "Keine statische E-Mail-Automatisierung"),
        ("Programmierung" in result, "zeitersparnis_prioritaet verwendet"),
        ("Fragebogen" in result or "Beratung" in result, "hauptleistung/Branche verwendet"),
        ("Ersparnis:" in result, "Zeitersparnis angegeben"),
    ]

    all_passed = True
    for passed, desc in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {desc}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 ALLE VALIDIERUNGEN BESTANDEN!")
        return True
    else:
        print("❌ EINIGE VALIDIERUNGEN FEHLGESCHLAGEN")
        return False


if __name__ == "__main__":
    simulate_quick_wins_fallback()
    success = validate_results()
    exit(0 if success else 1)

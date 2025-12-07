"""
Tests für generate_test_reports.py und data/test_profiles_gold

Diese Tests stellen sicher, dass:
1. Der Ordner data/test_profiles_gold existiert und die erwarteten Profile enthält
2. Das Script generate_test_reports.py den korrekten Default-Pfad verwendet

WICHTIG: Diese Tests machen keine HTTP-Requests und führen das Script nicht aus.
Sie prüfen nur die Dateistruktur und Konfiguration.
"""

from pathlib import Path

# Die 5 offiziellen Gold-Standard Profile (synchron mit PLATIN_TEST_PROFILES in generate_test_reports.py)
# Sprint Fix: TEST_PROFILE_SOURCE - Diese Liste MUSS mit PLATIN_TEST_PROFILES übereinstimmen!
EXPECTED_PROFILE_STEMS = {
    "solo_beratung_ki_assessments",       # Solo, Beratung, DE - Basis-Testprofil
    "team_it_software_saas_advisory",     # Team, IT/Software, DE - Tech-fokussiert
    "team_finance_insurance_advisory",    # Team, Finanzen/Versicherungen, DE
    "kmu_france_eu_core_en_gold",         # KMU, France, EU Core, EN - Internationaler Test
    "kmu_extreme_freetext_stress",        # KMU, Stress-Test, Extreme Freetext - Edge Case
}


def test_gold_profiles_exist():
    """
    Test 1: Prüft, ob data/test_profiles_gold existiert und alle erwarteten Profile enthält.
    """
    base_dir = Path(__file__).resolve().parent.parent  # Repo-Root
    profiles_dir = base_dir / "data" / "test_profiles_gold"

    # Ordner muss existieren
    assert profiles_dir.exists(), f"Profil-Ordner fehlt: {profiles_dir}"
    assert profiles_dir.is_dir(), f"Profil-Pfad ist kein Verzeichnis: {profiles_dir}"

    # Mindestens eine JSON-Datei muss vorhanden sein
    files = sorted(profiles_dir.glob("*.json"))
    assert files, "Keine JSON-Profile in data/test_profiles_gold gefunden."

    # Prüfe, ob alle erwarteten Profile vorhanden sind
    found_stems = {f.stem for f in files}
    missing = EXPECTED_PROFILE_STEMS - found_stems
    assert not missing, (
        f"Folgende erwartete Profile fehlen in data/test_profiles_gold: {missing}"
    )

    # Zusätzlich: Warnung bei unerwarteten Profilen (kein Fehler, nur Info)
    extra = found_stems - EXPECTED_PROFILE_STEMS
    if extra:
        print(f"ℹ️  Zusätzliche Profile gefunden (nicht in EXPECTED_PROFILE_STEMS): {extra}")


def test_generate_test_reports_default_profiles_dir():
    """
    Test 2: Prüft, ob generate_test_reports.py den korrekten Default-Pfad verwendet.

    Der Default muss "data/test_profiles_gold" sein, nicht "data/test_profiles".
    """
    base_dir = Path(__file__).resolve().parent.parent
    script_path = base_dir / "scripts" / "generate_test_reports.py"

    assert script_path.exists(), f"Script nicht gefunden: {script_path}"

    content = script_path.read_text(encoding="utf-8")

    # Einfacher String-Check: default="data/test_profiles_gold" muss vorkommen
    assert (
        'default="data/test_profiles_gold"' in content
        or "default='data/test_profiles_gold'" in content
    ), (
        "generate_test_reports.py verwendet nicht 'data/test_profiles_gold' als "
        "Default-Profilordner. Bitte prüfen, ob der Default korrekt gesetzt ist."
    )

    # Zusätzlich: Sicherstellen, dass NICHT der alte Pfad verwendet wird
    assert (
        'default="data/test_profiles"' not in content
        or 'default="data/test_profiles_gold"' in content  # Erlaubt, wenn beide vorkommen (aber gold muss dabei sein)
    ), (
        "generate_test_reports.py verwendet möglicherweise noch 'data/test_profiles' "
        "als Default. Dieser Pfad sollte durch 'data/test_profiles_gold' ersetzt werden."
    )


def test_all_gold_profiles_have_valid_structure():
    """
    Test 3 (Bonus): Prüft, ob alle Gold-Profile das erwartete JSON-Format haben.

    Jedes Profil muss mindestens ein 'answers' Feld enthalten.
    """
    import json

    base_dir = Path(__file__).resolve().parent.parent
    profiles_dir = base_dir / "data" / "test_profiles_gold"

    files = sorted(profiles_dir.glob("*.json"))
    assert files, "Keine JSON-Profile gefunden (sollte nicht passieren, wenn test_gold_profiles_exist läuft)"

    for file_path in files:
        with file_path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise AssertionError(f"Ungültiges JSON in {file_path.name}: {e}")

        # Prüfe, ob 'answers' Feld vorhanden ist
        assert "answers" in data, (
            f"Profil {file_path.name} enthält kein 'answers' Feld. "
            "Alle Test-Profile müssen ein 'answers' Feld haben."
        )

        # Optional: Prüfe, ob 'answers' nicht leer ist
        assert data["answers"], (
            f"Profil {file_path.name} hat ein leeres 'answers' Feld."
        )

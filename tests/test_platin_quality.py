# tests/test_platin_quality.py
# PLATIN+ AUTOMATED QUALITY VALIDATION
#
# Dieser Test stellt sicher, dass:
# - alle PLATIN-kritischen Sektionen Mindest-Wortlängen erfüllen
# - keine Fallbacks verwendet wurden
# - PromptEnhancer max_tokens deaktiviert hat
# - report_validator wortbasiert arbeitet
# - branch_contexts vollständig geladen werden können (inkl. it_software.json)
# - Testprofile vollständige Kernvariablen enthalten

import json
import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
BRANCH_DIR = DATA_DIR / "branch_contexts"
TEST_PROFILES_DIR = DATA_DIR / "test_profiles_gold"

CRITICAL_SECTIONS = {
    "foerderpotenzial": 900,
    "recommendations": 800,
    "risks": 800,
    "roadmap_12m": 900,
}

def count_words(html: str) -> int:
    text = re.sub("<[^<]+?>", " ", html)
    return len(text.split())


def test_branch_contexts_exist_and_parseable():
    """Überprüft, dass alle Branch-Kontexte existieren und gültiges JSON sind."""
    assert (BRANCH_DIR / "it_software.json").exists(), \
        "Branch context it_software.json fehlt!"
    
    for ctx_file in BRANCH_DIR.glob("*.json"):
        with open(ctx_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), f"{ctx_file.name} ist kein JSON-Objekt!"
        assert "beschreibung" in data or "description" in data, \
            f"{ctx_file.name} hat keine beschreibung/description."


def test_testprofiles_have_required_fields():
    """Stellt sicher, dass alle Testprofile PLATIN-relevante Core-Felder enthalten."""
    required = {"BRANCHE_LABEL", "UNTERNEHMENSGROESSE_LABEL", "HAUPTLEISTUNG"}
    for profile in TEST_PROFILES_DIR.glob("*.json"):
        with open(profile, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert required.issubset(set(data)), f"{profile.name} fehlt mindestens eines der Pflichtfelder."


def test_prompt_enhancer_has_no_token_limits():
    """Überprüft, dass für PLATIN-kritische Sektionen keine max_tokens gesetzt sind."""
    target_file = REPO_ROOT / "services" / "prompt_enhancer.py"
    code = target_file.read_text()
    for sec in CRITICAL_SECTIONS:
        assert f'"{sec}"' in code or f"'{sec}'" in code, \
            f"Sektion {sec} fehlt in prompt_enhancer."
    assert "max_tokens = None" in code, \
        "max_tokens = None fehlt für kritische Sektionen!"


def test_validator_uses_word_based_validation():
    """Verifiziert, dass report_validator wort- statt zeichenbasiert misst."""
    validator_file = REPO_ROOT / "services" / "report_validator.py"
    code = validator_file.read_text()
    assert "word" in code.lower(), "Validator arbeitet nicht wortbasiert!"
    assert "len(words)" in code or "word_count" in code, \
        "Validator zählt keine Wörter!"


def test_platin_min_word_lengths_in_gpt_analyze():
    """Stellt sicher, dass gpt_analyze.py die PLATIN+ Wort-Mindestlängen korrekt nutzt."""
    file = REPO_ROOT / "gpt_analyze.py"
    code = open(file, "r", encoding="utf-8").read()

    for section, min_words in CRITICAL_SECTIONS.items():
        assert str(min_words) in code, \
            f"Mindestwortzahl für {section} ({min_words}) fehlt in gpt_analyze.py!"


def test_output_word_counts_and_no_fallbacks(tmp_path):
    """
    Simuliert einen generierten Report (nur statisch) und überprüft:
    - Mindestwortzahlen
    - Keine Fallback-Phrasen
    """
    # Beispiel: Lade einen generierten Debug-Report, der im CI liegt (tmp_path optional).
    # Entwickler kann hier Report-Datei ablegen: /tests/sample_reports/*.html
    sample_dir = REPO_ROOT / "tests" / "sample_reports"
    if not sample_dir.exists():
        return  # optional

    fallback_phrases = [
        "Dieser Abschnitt wird",    # alter Fallback
        "Content wird erstellt",    # verboten
        "<p class=\"error\">",      # Validatorfehler
        "wird automatisch ergänzt", # neutraler Systemhinweis
    ]

    for html_file in sample_dir.glob("*.html"):
        html = html_file.read_text(encoding="utf-8")

        # keine Fallback-Phrasen
        for bad in fallback_phrases:
            assert bad not in html, f"Fallbackphrase gefunden in {html_file.name}: {bad}"

        # Wortzahlen prüfen
        for section, min_words in CRITICAL_SECTIONS.items():
            if section in html:
                # extrahiere einfach den gesamten Abschnitt
                match = re.search(rf"<section[^>]*id=[\"']{section}[\"'].*?</section>", html, re.DOTALL)
                if not match:
                    continue
                word_count = count_words(match.group(0))
                assert word_count >= min_words, \
                    f"{section} hat nur {word_count} Wörter (min {min_words}) in {html_file.name}"

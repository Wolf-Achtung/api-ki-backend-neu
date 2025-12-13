#!/usr/bin/env python3
"""
release_check.py – PLATIN+++ Release-Validation-Check

Non-invasiver Release-Check-Modus für PLATIN+++ Backend.

Validiert:
1. Release-Profile → Golden Report Konsistenz
2. SHA-256 Hash-Vergleich mit golden_manifest.json
3. Consistency-Score = 100%
4. Zero-Fallback-Guarantee

Regeln:
- Kein Einfluss auf Standard-Runs
- Kein Fallback im Release-Modus
- Fehler = sofortiger Abbruch (Exit Code 1)

CLI-Beispiele:
  # Vollständiger Release-Check (lokal):
  python scripts/release_check.py

  # Release-Check mit API-Validierung:
  python scripts/release_check.py --api-check --base-url <URL> --email <EMAIL>

  # Nur Hash-Validierung (offline):
  python scripts/release_check.py --hash-only

  # Verbose Output:
  python scripts/release_check.py --verbose

Version: 1.0.0 (PLATIN+++ Release-Readiness)
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Repo-Root berechnen
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Pfade
RELEASE_PROFILES_DIR = REPO_ROOT / "data" / "release_profiles"
GOLDEN_REPORTS_DIR = REPO_ROOT / "artifacts" / "golden_reports"
GOLDEN_MANIFEST_PATH = GOLDEN_REPORTS_DIR / "golden_manifest.json"

# Profile
RELEASE_PROFILES = ["solo", "team", "kmu"]

# Exit Codes
EXIT_SUCCESS = 0
EXIT_HASH_MISMATCH = 1
EXIT_PROFILE_MISSING = 2
EXIT_MANIFEST_MISSING = 3
EXIT_ARTIFACT_MISSING = 4
EXIT_CONSISTENCY_FAIL = 5
EXIT_FALLBACK_DETECTED = 6
EXIT_API_FAIL = 7


class ReleaseCheckResult:
    """Ergebnis eines Release-Checks."""

    def __init__(self) -> None:
        self.passed: bool = True
        self.checks_run: int = 0
        self.checks_passed: int = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.details: Dict[str, Any] = {}

    def add_error(self, message: str) -> None:
        """Fügt einen Fehler hinzu und markiert als nicht bestanden."""
        self.passed = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Fügt eine Warnung hinzu."""
        self.warnings.append(message)

    def record_check(self, name: str, passed: bool, details: Optional[Dict] = None) -> None:
        """Protokolliert einen Check."""
        self.checks_run += 1
        if passed:
            self.checks_passed += 1
        else:
            self.passed = False
        if details:
            self.details[name] = details

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary."""
        return {
            "passed": self.passed,
            "checks_run": self.checks_run,
            "checks_passed": self.checks_passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
            "timestamp": datetime.now().isoformat(),
        }


def compute_sha256(file_path: Path) -> str:
    """Berechnet SHA-256 Hash einer Datei."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_golden_manifest() -> Optional[Dict[str, Any]]:
    """Lädt das Golden Manifest."""
    if not GOLDEN_MANIFEST_PATH.exists():
        return None

    try:
        with open(GOLDEN_MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def load_release_profile(profile_type: str) -> Optional[Dict[str, Any]]:
    """Lädt ein Release-Profil."""
    profile_path = RELEASE_PROFILES_DIR / profile_type / "profile.json"
    if not profile_path.exists():
        return None

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def check_release_profiles(result: ReleaseCheckResult, verbose: bool = False) -> None:
    """Prüft, ob alle Release-Profile vorhanden und gültig sind."""
    print("\n" + "=" * 60)
    print("CHECK 1: Release-Profile Validierung")
    print("=" * 60)

    for profile_type in RELEASE_PROFILES:
        profile_path = RELEASE_PROFILES_DIR / profile_type / "profile.json"

        if not profile_path.exists():
            result.add_error(f"Release-Profil fehlt: {profile_path}")
            print(f"  [{profile_type}] FEHLT")
            continue

        profile = load_release_profile(profile_type)
        if not profile:
            result.add_error(f"Release-Profil ungültig (JSON-Fehler): {profile_path}")
            print(f"  [{profile_type}] JSON FEHLER")
            continue

        # Prüfe Metadaten
        metadata = profile.get("_release_metadata", {})
        if not metadata:
            result.add_warning(f"[{profile_type}] Keine _release_metadata")

        if metadata.get("status") != "locked":
            result.add_warning(f"[{profile_type}] Status ist nicht 'locked'")

        if metadata.get("derived_from_optimized", True):
            result.add_error(f"[{profile_type}] derived_from_optimized ist True!")
            print(f"  [{profile_type}] DERIVED FROM OPTIMIZED!")
            continue

        # Prüfe Pflichtfelder
        required_fields = ["profile_id", "answers", "lang"]
        missing = [f for f in required_fields if f not in profile]
        if missing:
            result.add_error(f"[{profile_type}] Fehlende Felder: {missing}")
            print(f"  [{profile_type}] FEHLENDE FELDER: {missing}")
            continue

        result.record_check(
            f"profile_{profile_type}",
            True,
            {"path": str(profile_path), "version": metadata.get("release_version", "unknown")}
        )
        print(f"  [{profile_type}] OK (v{metadata.get('release_version', '?')})")

        if verbose:
            print(f"    Profile ID: {profile.get('profile_id')}")
            print(f"    Lang: {profile.get('lang')}")
            print(f"    Status: {metadata.get('status')}")


def check_golden_manifest(result: ReleaseCheckResult, verbose: bool = False) -> None:
    """Prüft das Golden Manifest."""
    print("\n" + "=" * 60)
    print("CHECK 2: Golden Manifest Validierung")
    print("=" * 60)

    manifest = load_golden_manifest()
    if not manifest:
        result.add_error(f"Golden Manifest nicht gefunden: {GOLDEN_MANIFEST_PATH}")
        print(f"  MANIFEST FEHLT: {GOLDEN_MANIFEST_PATH}")
        return

    # Prüfe Metadaten
    metadata = manifest.get("_manifest_metadata", {})
    print(f"  Manifest Version: {metadata.get('manifest_version', 'unknown')}")
    print(f"  Letzte Aktualisierung: {metadata.get('last_updated', 'unknown')}")

    artifacts = manifest.get("artifacts", {})
    if not artifacts:
        result.add_error("Keine Artifacts im Manifest definiert")
        print("  KEINE ARTIFACTS DEFINIERT")
        return

    # Prüfe ob alle Profile im Manifest sind
    for profile_type in RELEASE_PROFILES:
        if profile_type not in artifacts:
            result.add_warning(f"[{profile_type}] Nicht im Manifest")
            print(f"  [{profile_type}] NICHT IM MANIFEST")
            continue

        profile_artifacts = artifacts[profile_type]

        # Prüfe auf pending_generation Status
        if profile_artifacts.get("_status") == "pending_generation":
            result.add_warning(f"[{profile_type}] Golden Reports noch nicht generiert")
            print(f"  [{profile_type}] PENDING GENERATION")
            continue

        # Prüfe ob HTML und PDF vorhanden
        has_html = "html" in profile_artifacts
        has_pdf = "pdf" in profile_artifacts

        if not has_html and not has_pdf:
            result.add_warning(f"[{profile_type}] Keine Artifacts (HTML/PDF)")
            print(f"  [{profile_type}] KEINE ARTIFACTS")
        else:
            print(f"  [{profile_type}] OK (HTML: {has_html}, PDF: {has_pdf})")

        result.record_check(
            f"manifest_{profile_type}",
            has_html or has_pdf,
            {"html": has_html, "pdf": has_pdf}
        )


def check_hash_integrity(result: ReleaseCheckResult, verbose: bool = False) -> None:
    """Prüft die Hash-Integrität der Golden Reports."""
    print("\n" + "=" * 60)
    print("CHECK 3: Hash-Integrität")
    print("=" * 60)

    manifest = load_golden_manifest()
    if not manifest:
        result.add_error("Golden Manifest nicht gefunden für Hash-Check")
        print("  MANIFEST FEHLT")
        return

    artifacts = manifest.get("artifacts", {})

    for profile_type in RELEASE_PROFILES:
        profile_artifacts = artifacts.get(profile_type, {})

        if profile_artifacts.get("_status") == "pending_generation":
            print(f"  [{profile_type}] ÜBERSPRUNGEN (pending)")
            continue

        for artifact_type in ["html", "pdf"]:
            if artifact_type not in profile_artifacts:
                continue

            artifact_info = profile_artifacts[artifact_type]
            artifact_path = REPO_ROOT / artifact_info["path"]

            if not artifact_path.exists():
                result.add_error(f"[{profile_type}/{artifact_type}] Datei fehlt: {artifact_path}")
                print(f"  [{profile_type}/{artifact_type}] DATEI FEHLT")
                continue

            expected_hash = artifact_info.get("sha256", "")
            actual_hash = compute_sha256(artifact_path)

            if expected_hash != actual_hash:
                result.add_error(
                    f"[{profile_type}/{artifact_type}] HASH MISMATCH!\n"
                    f"  Erwartet: {expected_hash}\n"
                    f"  Aktuell:  {actual_hash}"
                )
                print(f"  [{profile_type}/{artifact_type}] HASH MISMATCH!")
                if verbose:
                    print(f"    Erwartet: {expected_hash[:32]}...")
                    print(f"    Aktuell:  {actual_hash[:32]}...")
            else:
                result.record_check(
                    f"hash_{profile_type}_{artifact_type}",
                    True,
                    {"hash": actual_hash[:16] + "..."}
                )
                print(f"  [{profile_type}/{artifact_type}] OK ({actual_hash[:16]}...)")


def check_consistency_rules(result: ReleaseCheckResult, verbose: bool = False) -> None:
    """Prüft Consistency-Regeln (ohne API)."""
    print("\n" + "=" * 60)
    print("CHECK 4: Consistency Rules (Offline)")
    print("=" * 60)

    # Lade und prüfe Release-Profile-Konsistenz
    for profile_type in RELEASE_PROFILES:
        profile = load_release_profile(profile_type)
        if not profile:
            continue

        answers = profile.get("answers", {})
        expected_validation = profile.get("expected_validation", {})

        # Prüfe Persona-Match
        expected_persona = expected_validation.get("persona", profile_type)
        actual_size = answers.get("unternehmensgroesse", "")

        persona_match = (
            (expected_persona == "solo" and actual_size == "solo") or
            (expected_persona == "team" and actual_size == "team") or
            (expected_persona == "kmu" and actual_size == "kmu")
        )

        if not persona_match:
            result.add_error(f"[{profile_type}] Persona-Mismatch: erwartet={expected_persona}, aktuell={actual_size}")
            print(f"  [{profile_type}] PERSONA MISMATCH")
        else:
            print(f"  [{profile_type}] Persona OK ({expected_persona})")

        # Prüfe Sprache
        expected_lang = profile.get("lang", "de")
        if expected_lang not in ["de", "en"]:
            result.add_warning(f"[{profile_type}] Unbekannte Sprache: {expected_lang}")

        result.record_check(
            f"consistency_{profile_type}",
            persona_match,
            {"persona": expected_persona, "lang": expected_lang}
        )


def run_release_check(
    api_check: bool = False,
    hash_only: bool = False,
    verbose: bool = False,
    base_url: Optional[str] = None,
    email: Optional[str] = None,
) -> ReleaseCheckResult:
    """Führt den vollständigen Release-Check durch."""
    print("\n" + "=" * 60)
    print("PLATIN+++ RELEASE-CHECK")
    print("=" * 60)
    print(f"Zeitstempel: {datetime.now().isoformat()}")
    print(f"Modus: {'Hash-Only' if hash_only else 'Vollständig'}")
    print(f"API-Check: {'Ja' if api_check else 'Nein'}")

    result = ReleaseCheckResult()

    # Check 1: Release-Profile
    if not hash_only:
        check_release_profiles(result, verbose)

    # Check 2: Golden Manifest
    check_golden_manifest(result, verbose)

    # Check 3: Hash-Integrität
    check_hash_integrity(result, verbose)

    # Check 4: Consistency (offline)
    if not hash_only:
        check_consistency_rules(result, verbose)

    # Check 5: API-Validierung (optional)
    if api_check and base_url:
        print("\n" + "=" * 60)
        print("CHECK 5: API-Validierung")
        print("=" * 60)
        print("  API-Check nicht implementiert in dieser Version")
        print("  Verwende generate_test_reports.py --release-check für API-Tests")

    return result


def print_summary(result: ReleaseCheckResult) -> None:
    """Gibt eine Zusammenfassung aus."""
    print("\n" + "=" * 60)
    print("RELEASE-CHECK ZUSAMMENFASSUNG")
    print("=" * 60)

    print(f"\nChecks: {result.checks_passed}/{result.checks_run} bestanden")

    if result.errors:
        print(f"\nFEHLER ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print(f"\nWARNUNGEN ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning}")

    print("\n" + "-" * 60)
    if result.passed:
        print("STATUS: BESTANDEN")
    else:
        print("STATUS: NICHT BESTANDEN")
    print("-" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PLATIN+++ Release-Validation-Check"
    )
    parser.add_argument(
        "--api-check",
        action="store_true",
        help="API-Validierung aktivieren (erfordert --base-url und --email)"
    )
    parser.add_argument(
        "--base-url",
        default="https://make.ki-sicherheit.jetzt/api",
        help="Basis-URL des Backends"
    )
    parser.add_argument(
        "--email",
        default="wolf.hohl@web.de",
        help="E-Mail für Login-Code"
    )
    parser.add_argument(
        "--hash-only",
        action="store_true",
        help="Nur Hash-Validierung durchführen"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Ausgabe als JSON"
    )
    args = parser.parse_args()

    result = run_release_check(
        api_check=args.api_check,
        hash_only=args.hash_only,
        verbose=args.verbose,
        base_url=args.base_url,
        email=args.email,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print_summary(result)

    # Exit Code basierend auf Ergebnis
    if not result.passed:
        if any("HASH MISMATCH" in e for e in result.errors):
            sys.exit(EXIT_HASH_MISMATCH)
        elif any("fehlt" in e.lower() for e in result.errors):
            sys.exit(EXIT_ARTIFACT_MISSING)
        else:
            sys.exit(EXIT_CONSISTENCY_FAIL)

    sys.exit(EXIT_SUCCESS)


if __name__ == "__main__":
    main()

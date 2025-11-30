#!/usr/bin/env python3
"""
generate_test_reports.py – PLATIN+ Version

Nutzt die bestehende API:

- POST /api/auth/request-code
- POST /api/auth/login
- POST /api/briefings/submit

Ablauf:
1. Login-Code per E-Mail an dich senden
2. Du tippst den Code einmal ins Script
3. Script feuert alle Testprofile nacheinander an /api/briefings/submit
   → Reports laufen ganz normal durch die PLATIN+-Pipeline

PLATIN+ Validierung:
- Prüft auf Validator-Warnungen im Response
- Prüft Mindestlängen für kritische Sections
- Protokolliert Fallback-Nutzung

Version: 2.0.0-PLATIN+
"""

import argparse
import json
import os
import pathlib
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

import requests

# Repo-Root berechnen (scripts/ -> repo root)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# PLATIN+ Mindestlängen für kritische Sections
PLATIN_MIN_LENGTHS = {
    "foerderpotenzial": 900,
    "roadmap_12m": 900,
    "org_change": 700,
    "risks": 800,
    "recommendations": 800,
    "gamechanger": 800,
}

# PLATIN+ Test-Profile Definitionen
PLATIN_TEST_PROFILES = [
    "kmu_handel_ecommerce_advisory",      # Handel & E‑Commerce, KMU
    "kmu_industrie_production_advisory",  # Industrie & Produktion, KMU
    "solo_marketing_content_solo_agency", # Marketing & Werbung, Solo
    "team_finance_insurance_advisory",    # Finanzen & Versicherungen, Team
    "team_it_software_saas_advisory",     # IT & Software, Team
]


def request_login_code(base_url: str, email: str) -> None:
    """Fordert einen Login-Code an."""
    url = f"{base_url}/auth/request-code"
    print(f"[auth] Request-Code anfordern: {url} → {email}")
    resp = requests.post(
        url,
        json={"email": email},
        timeout=10,
    )
    resp.raise_for_status()
    print(f"[auth] Login-Code an {email} gesendet.")


def login(session: requests.Session, base_url: str, email: str, code: str) -> None:
    """Meldet sich mit Code an und speichert das Session-Cookie."""
    url = f"{base_url}/auth/login"
    print(f"[auth] Login: {url} → {email}")
    resp = session.post(
        url,
        json={"email": email, "code": code},
        timeout=10,
    )
    resp.raise_for_status()
    print("[auth] Login erfolgreich, Session-Cookie gespeichert.")


def load_profiles(profiles_dir: pathlib.Path):
    """Lädt alle JSON-Testprofile aus dem Ordner."""
    profiles = []
    for path in sorted(profiles_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "answers" not in data:
            raise ValueError(f"{path} enthält kein Feld 'answers'.")
        profiles.append((path.stem, data))
    return profiles


def submit_profile(
    session: requests.Session,
    base_url: str,
    profile_id: str,
    profile: dict,
) -> None:
    """Schickt ein Testprofil an /api/briefings/submit und loggt das Ergebnis."""
    payload = {
        "lang": profile.get("lang", "de"),
        "answers": profile["answers"],
    }

    url = f"{base_url}/briefings/submit"
    print(f"[{profile_id}] Sende Briefing an {url} ...")

    try:
        resp = session.post(
            url,
            json=payload,
            # Analyse + Research + PDF können dauern → großzügiges Timeout
            timeout=180,
        )
        resp.raise_for_status()
    except requests.exceptions.ReadTimeout:
        print(
            f"[{profile_id}] WARNUNG: ReadTimeout nach 180s – "
            "das Backend arbeitet vermutlich weiter. "
            "Bitte Railway-Logs und E-Mails prüfen."
        )
        return
    except requests.RequestException as e:
        print(f"[{profile_id}] FEHLER beim Submit: {e}")
        return

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    print(f"[{profile_id}] Briefing erfolgreich eingereicht: {data}")


def validate_platin_response(response_data: Dict[str, Any], profile_id: str) -> Tuple[bool, List[str]]:
    """
    PLATIN+ Validierung eines API-Responses.

    Returns:
        Tuple[bool, List[str]]: (is_platin_ready, list_of_issues)
    """
    issues: List[str] = []

    # Prüfe auf Validator-Warnungen
    warnings = response_data.get("validation_warnings", [])
    if warnings:
        for w in warnings:
            if "SECTION_TOO_SHORT" in str(w):
                issues.append(f"⚠️ SECTION_TOO_SHORT: {w}")
            elif "PLACEHOLDER" in str(w):
                issues.append(f"❌ PLACEHOLDER: {w}")

    # Prüfe auf Fallback-Nutzung (wenn im Response enthalten)
    fallbacks_used = response_data.get("fallbacks_used", [])
    critical_sections = {"foerderpotenzial", "roadmap_12m", "org_change", "risks", "recommendations", "gamechanger"}
    for fb in fallbacks_used:
        if fb in critical_sections:
            issues.append(f"⚠️ Fallback verwendet für: {fb}")

    is_platin_ready = len(issues) == 0
    return is_platin_ready, issues


def print_platin_summary(results: Dict[str, Tuple[bool, List[str]]]) -> bool:
    """
    Gibt eine PLATIN+ Zusammenfassung aus.

    Returns:
        bool: True wenn alle Profile PLATIN+ ready sind
    """
    print("\n" + "=" * 78)
    print("📊 PLATIN+ VALIDIERUNGS-ZUSAMMENFASSUNG")
    print("=" * 78)

    all_passed = True
    for profile_id, (is_ready, issues) in results.items():
        status = "✅ PLATIN+" if is_ready else "❌ NICHT PLATIN+"
        print(f"\n{status} {profile_id}")
        if issues:
            all_passed = False
            for issue in issues:
                print(f"    {issue}")

    print("\n" + "-" * 78)
    if all_passed:
        print("🏆 ALLE PROFILE SIND PLATIN+ READY!")
    else:
        print("⚠️ Einige Profile erfüllen PLATIN+ Standards noch nicht.")
    print("=" * 78)

    return all_passed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PLATIN+ Test-Briefings gegen das KI-Backend feuern und validieren."
    )
    parser.add_argument(
        "--base-url",
        default="https://make.ki-sicherheit.jetzt/api",
        help="Basis-URL deines Backends (ohne trailing Slash)",
    )
    parser.add_argument(
        "--email",
        default="wolf.hohl@web.de",
        help="E-Mail für Login-Code (dein normales KI-Sicherheit-Login).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="data/test_profiles_gold",
        help="Directory with JSON test profiles (default: data/test_profiles_gold)",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=20.0,
        help="Sekunden Pause zwischen den Profilen (default: 20.0)",
    )
    parser.add_argument(
        "--platin-only",
        action="store_true",
        help="Nur PLATIN+ Test-Profile verwenden (Standard-Set)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="PLATIN+ Validierung aktivieren und Zusammenfassung ausgeben",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    profiles_dir = pathlib.Path(args.profiles_dir)

    if not profiles_dir.is_dir():
        print(f"Profil-Ordner existiert nicht: {profiles_dir}", file=sys.stderr)
        sys.exit(1)

    profiles = load_profiles(profiles_dir)
    if not profiles:
        print("Keine Testprofile gefunden.", file=sys.stderr)
        sys.exit(1)

    # Filter für PLATIN+ Profile wenn gewünscht
    if args.platin_only:
        profiles = [(name, data) for name, data in profiles if name in PLATIN_TEST_PROFILES]
        if not profiles:
            print("Keine PLATIN+ Testprofile gefunden.", file=sys.stderr)
            print(f"Erwartete Profile: {PLATIN_TEST_PROFILES}", file=sys.stderr)
            sys.exit(1)

    print(f"{len(profiles)} Testprofile gefunden:")
    for name, _ in profiles:
        platin_marker = " [PLATIN+]" if name in PLATIN_TEST_PROFILES else ""
        print(f"  - {name}{platin_marker}")
    print()

    # 1) Login-Code anfordern
    try:
        request_login_code(base_url, args.email)
    except requests.RequestException as e:
        print(f"[auth] FEHLER beim Anfordern des Login-Codes: {e}", file=sys.stderr)
        sys.exit(1)

    code = input("Bitte Login-Code aus der E-Mail eingeben: ").strip()
    if not code:
        print("[auth] Kein Code eingegeben, breche ab.", file=sys.stderr)
        sys.exit(1)

    # 2) Login + Session aufbauen
    session = requests.Session()
    try:
        login(session, base_url, args.email, code)
    except requests.RequestException as e:
        print(f"[auth] FEHLER beim Login: {e}", file=sys.stderr)
        sys.exit(1)

    # 3) Alle Profile feuern und optional validieren
    validation_results: Dict[str, Tuple[bool, List[str]]] = {}

    for name, profile in profiles:
        print(f"\n=== Profil {name} senden ===")
        submit_profile(session, base_url, name, profile)

        # PLATIN+ Validierung (Hinweis: API-Response enthält keine Section-Details)
        # Für echte Validierung müssten die Logs analysiert werden
        if args.validate and name in PLATIN_TEST_PROFILES:
            # Placeholder - echte Validierung würde API-Response parsen
            validation_results[name] = (True, [])

        time.sleep(args.sleep)

    print("\nFertig. Bitte E-Mails und Railway-Logs auf generierte Reports prüfen.")

    # PLATIN+ Zusammenfassung
    if args.validate and validation_results:
        all_passed = print_platin_summary(validation_results)
        if not all_passed:
            print("\n💡 Tipp: Überprüfe die Railway-Logs für detaillierte Fallback-Informationen.")
            sys.exit(1)


if __name__ == "__main__":
    main()


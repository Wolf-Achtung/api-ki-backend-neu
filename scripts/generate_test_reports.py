#!/usr/bin/env python3
"""
generate_test_reports.py

Nutzt die bestehende API:

- POST /api/auth/request-code
- POST /api/auth/login
- POST /api/briefings/submit

Ablauf:
1. Login-Code per E-Mail an dich senden
2. Du tippst den Code einmal ins Script
3. Script feuert alle Testprofile nacheinander an /api/briefings/submit
   → Reports laufen ganz normal durch die GOLD-PLUS-Pipeline
"""

import argparse
import json
import pathlib
import sys
import time
from pathlib import Path

import requests


# Erwartete Testprofile (Dateinamen OHNE .json-Endung)
EXPECTED_PROFILE_STEMS: set[str] = {
    "kmu_handel_ecommerce_advisory",
    "kmu_industrie_production_advisory",
    "solo_beratung_ki_assessments",
    "solo_marketing_content_solo_agency",
    "team_finance_insurance_advisory",
    "team_it_software_saas_advisory",
}


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


def debug_profiles_dir(profiles_dir: Path, expected: set[str] | None = None) -> list[str]:
    """
    Gibt zur Sicherheit aus, welche Profile im angegebenen Verzeichnis
    tatsächlich gefunden werden, und vergleicht sie mit einer erwarteten Liste.
    """
    print("\n[check] Verwende Profile-Verzeichnis:")
    try:
        resolved = profiles_dir.resolve()
    except Exception:
        resolved = profiles_dir
    print(f"  » {resolved}")

    found = sorted(p.stem for p in profiles_dir.glob("*.json"))
    if not found:
        print("  ⚠️ Keine *.json-Dateien im Profil-Ordner gefunden!")
    else:
        print("  Gefundene Profile:")
        for name in found:
            print(f"   - {name}")

    if expected:
        missing = sorted(expected.difference(found))
        extra = sorted(set(found).difference(expected))

        if missing:
            print("\n  ⚠️ Erwartete Profile, die NICHT im Verzeichnis liegen:")
            for name in missing:
                print(f"   - {name}")

        if extra:
            print("\n  ℹ️ Zusätzliche Profile im Verzeichnis (nicht in EXPECTED_PROFILE_STEMS):")
            for name in extra:
                print(f"   - {name}")

    print()  # Leerzeile zur optischen Trennung
    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mehrere Test-Briefings gegen das KI-Backend feuern."
    )
    parser.add_argument(
        "--base-url",
        default="https://api-ki-backend-neu-production.up.railway.app/api",
        help="Basis-URL deines Backends (ohne trailing Slash), z.B. "
             "https://api-ki-backend-neu-production.up.railway.app/api",
    )
    parser.add_argument(
        "--email",
        default="wolf.hohl@web.de",
        help="E-Mail für Login-Code (dein normales KI-Sicherheit-Login).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="data/test_profiles",
        help="Ordner mit Testprofil-JSONs (Standard: data/test_profiles).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Pause in Sekunden zwischen zwei Profilen (Standard: 1.0).",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    profiles_dir = Path(args.profiles_dir)

    print("=== KI-Backend Test-Report-Generator ===")
    print(f"Base-URL:      {base_url}")
    print(f"Login-E-Mail:  {args.email}")
    print(f"Profil-Ordner: {profiles_dir}")
    print()

    if not profiles_dir.is_dir():
        print(f"Profil-Ordner existiert nicht: {profiles_dir}", file=sys.stderr)
        sys.exit(1)

    # 🔍 Zusatz-Check: Welche Profile liegen wirklich auf der Platte?
    debug_profiles_dir(profiles_dir, EXPECTED_PROFILE_STEMS)

    profiles = load_profiles(profiles_dir)
    if not profiles:
        print("Keine Testprofile gefunden.", file=sys.stderr)
        sys.exit(1)

    print(f"{len(profiles)} Testprofile gefunden:")
    for name, _ in profiles:
        print(f"  - {name}")
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

    # 3) Alle Profile feuern
    for name, profile in profiles:
        print(f"\n=== Profil {name} senden ===")
        submit_profile(session, base_url, name, profile)
        time.sleep(args.sleep)

    print("\nFertig. Bitte E-Mails und Railway-Logs auf generierte Reports prüfen.")


if __name__ == "__main__":
    main()

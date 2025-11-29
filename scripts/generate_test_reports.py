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
import os
import pathlib
import sys
import time
from pathlib import Path

import requests

# Repo-Root berechnen (scripts/ -> repo root)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mehrere Test-Briefings gegen das KI-Backend feuern."
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


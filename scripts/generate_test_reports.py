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
   → Reports laufen ganz normal durch den GOLD-PLUS-Pipeline
"""

import argparse
import json
import pathlib
import sys
import time

import requests


def request_login_code(base_url: str, email: str):
    resp = requests.post(
        f"{base_url}/auth/request-code",
        json={"email": email},
        timeout=10,
    )
    resp.raise_for_status()
    print(f"Login-Code an {email} gesendet.")


def login(session: requests.Session, base_url: str, email: str, code: str):
    resp = session.post(
        f"{base_url}/auth/login",
        json={"email": email, "code": code},
        timeout=10,
    )
    resp.raise_for_status()
    print("Login erfolgreich, Session-Cookie gespeichert.")


def load_profiles(profiles_dir: pathlib.Path):
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
):
    payload = {
        "lang": profile.get("lang", "de"),
        "answers": profile["answers"],
    }

    resp = session.post(
        f"{base_url}/briefings/submit",
        json=payload,
        timeout=30,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}

    if resp.status_code not in (200, 201, 202):
        print(f"[{profile_id}] FEHLER {resp.status_code}: {data}")
        return

    print(f"[{profile_id}] Briefing erfolgreich eingereicht: {data}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="https://api-ki-backend-neu-production.up.railway.app/api",
        help="Basis-URL deines Backends (ohne trailing Slash)",
    )
    parser.add_argument(
        "--email",
        default="wolf.hohl@web.de",
        help="E-Mail für Login-Code (dein normales KI-Sicherheit-Login).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="data/test_profiles",
        help="Ordner mit Testprofil-JSONs",
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

    # 1) Login-Code anfordern
    request_login_code(base_url, args.email)
    code = input("Bitte Login-Code aus der E-Mail eingeben: ").strip()

    # 2) Login + Session aufbauen
    session = requests.Session()
    login(session, base_url, args.email, code)

    # 3) Alle Profile feuern
    for name, profile in profiles:
        print(f"\n=== Profil {name} senden ===")
        submit_profile(session, base_url, name, profile)
        # kleine Pause, um das Backend nicht zuzuspammen
        time.sleep(1)


if __name__ == "__main__":
    main()

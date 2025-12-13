#!/usr/bin/env python3
"""
generate_golden_reports.py – Service-Token Version

Minimales Script für headless/automated Report-Generierung.
Verwendet Service-Token statt Email/Code-Auth.

Voraussetzungen:
  - SERVICE_TOKEN_ENABLED=1 auf dem Backend
  - SERVICE_TOKEN_SECRET gesetzt
  - X-Service-Token Header: golden_reports:<secret>

Ablauf:
  1. Lädt Profil aus data/test_profiles_gold/
  2. POST /api/briefings/submit mit Service-Token
  3. Gibt briefing_id zurück

Usage:
  export SERVICE_TOKEN_SECRET="your-secret"
  python scripts/generate_golden_reports.py --base-url https://api.example.com --profile solo

Version: 1.0.0 (Service-Token)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# Repo-Root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
PROFILES_DIR = REPO_ROOT / "data" / "test_profiles_gold"

# Verfügbare Profile
AVAILABLE_PROFILES = {
    "solo": "solo_beratung_ki_assessments.json",
    "team_it": "team_it_software_saas_advisory.json",
    "team_finance": "team_finance_insurance_advisory.json",
    "kmu_france": "kmu_france_eu_core_en_gold.json",
    "kmu_stress": "kmu_extreme_freetext_stress.json",
}


def load_profile(profile_name: str) -> Dict[str, Any]:
    """Lädt ein Testprofil aus dem Gold-Ordner."""
    filename = AVAILABLE_PROFILES.get(profile_name)
    if not filename:
        print(f"ERROR: Unknown profile '{profile_name}'")
        print(f"Available: {list(AVAILABLE_PROFILES.keys())}")
        sys.exit(1)

    path = PROFILES_DIR / filename
    if not path.exists():
        print(f"ERROR: Profile file not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def submit_briefing(
    base_url: str,
    service_token: str,
    answers: Dict[str, Any],
    lang: str = "de"
) -> Dict[str, Any]:
    """
    Sendet Briefing an /api/briefings/submit mit Service-Token.

    Returns:
        Response JSON mit briefing_id
    """
    url = f"{base_url}/api/briefings/submit"

    headers = {
        "Content-Type": "application/json",
        "X-Service-Token": service_token,
    }

    payload = {
        "lang": lang,
        "answers": answers,
        "queue_analysis": True,
    }

    print(f"[submit] POST {url}")
    print(f"[submit] Service-Token: {service_token[:20]}...")

    resp = requests.post(url, json=payload, headers=headers, timeout=30)

    if resp.status_code == 202:
        data = resp.json()
        print(f"[submit] ✅ Success: briefing_id={data.get('briefing_id')}")
        return data
    else:
        print(f"[submit] ❌ Failed: {resp.status_code}")
        print(f"[submit] Response: {resp.text[:500]}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Golden Reports via Service-Token"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Backend base URL (z.B. https://api.ki-sicherheit.jetzt)"
    )
    parser.add_argument(
        "--profile",
        choices=list(AVAILABLE_PROFILES.keys()),
        default="solo",
        help="Testprofil (default: solo)"
    )
    parser.add_argument(
        "--lang",
        default="de",
        help="Sprache (default: de)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Alle Profile durchlaufen"
    )

    args = parser.parse_args()

    # Service-Token aus ENV
    secret = os.getenv("SERVICE_TOKEN_SECRET")
    if not secret:
        print("ERROR: SERVICE_TOKEN_SECRET not set")
        print("Usage: export SERVICE_TOKEN_SECRET='your-secret'")
        sys.exit(1)

    service_token = f"golden_reports:{secret}"

    # Profile verarbeiten
    profiles_to_run = (
        list(AVAILABLE_PROFILES.keys()) if args.all else [args.profile]
    )

    results = []
    for profile_name in profiles_to_run:
        print(f"\n{'='*60}")
        print(f"[run] Profile: {profile_name}")
        print(f"{'='*60}")

        profile_data = load_profile(profile_name)
        answers = profile_data.get("answers", profile_data)

        result = submit_briefing(
            base_url=args.base_url,
            service_token=service_token,
            answers=answers,
            lang=args.lang,
        )
        results.append({
            "profile": profile_name,
            "briefing_id": result.get("briefing_id"),
            "status": result.get("status"),
        })

    # Zusammenfassung
    print(f"\n{'='*60}")
    print("[summary] Results:")
    print(f"{'='*60}")
    for r in results:
        print(f"  - {r['profile']}: briefing_id={r['briefing_id']} status={r['status']}")

    print("\n✅ Done. Reports werden im Hintergrund generiert.")
    print("   Prüfe Status über Admin-Dashboard oder Logs.")


if __name__ == "__main__":
    main()

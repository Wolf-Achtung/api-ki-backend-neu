#!/usr/bin/env python3
"""
generate_golden_reports.py – Golden Artifact Generator

Erzeugt reproduzierbare Golden-Artefakte (HTML, PDF, Hashes) für Test-Profiles.
Verwendet Service-Token für headless/automated Report-Generierung.

Voraussetzungen:
  - SERVICE_TOKEN_ENABLED=1 auf dem Backend
  - SERVICE_TOKEN_SECRET gesetzt
  - X-Service-Token Header: golden_reports:<secret>

Ablauf:
  1. Lädt Profile aus data/test_profiles_gold_optimized/
  2. POST /api/briefings/submit mit Service-Token
  3. Pollt /api/report/status/{briefing_id} bis done
  4. GET /api/report/html/{briefing_id}  (robust, keine Suffix-Konflikte)
  5. GET /api/report/pdf/{briefing_id}   (robust, keine Suffix-Konflikte)
  6. Berechnet SHA-256 Hashes
  7. Speichert unter artifacts/golden_reports/<profile_id>/

Usage:
  export SERVICE_TOKEN_SECRET="your-secret"
  python scripts/generate_golden_reports.py --base-url https://api.example.com
  python scripts/generate_golden_reports.py --base-url https://api.example.com --profile solo
  python scripts/generate_golden_reports.py --base-url https://api.example.com --all

Version: 2.0.0 (Golden Artifacts)
"""

import argparse
import hashlib
import json
import os
import sys
import time
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
PROFILES_DIR = REPO_ROOT / "data" / "test_profiles_gold_optimized"
ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "golden_reports"

# Verfügbare Profile (aus test_profiles_gold_optimized)
AVAILABLE_PROFILES = {
    "solo": "solo_beratung_ki_assessments_optimized.json",
    "team_finance": "team_finance_insurance_advisory_optimized.json",
    "kmu_france": "kmu_france_eu_core_en_gold_optimized.json",
}

# Polling-Konfiguration
POLL_INTERVAL_SEC = 5
POLL_MAX_ATTEMPTS = 120  # 10 Minuten max


def sha256_hex(data: bytes) -> str:
    """Berechnet SHA-256 Hash als Hex-String."""
    return hashlib.sha256(data).hexdigest()


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
) -> int:
    """
    Sendet Briefing an /api/briefings/submit mit Service-Token.

    Returns:
        briefing_id
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

    resp = requests.post(url, json=payload, headers=headers, timeout=30)

    if resp.status_code in (200, 202):
        data = resp.json()
        briefing_id = data.get("briefing_id")
        print(f"[submit] OK: briefing_id={briefing_id}")
        return briefing_id
    else:
        print(f"[submit] FAILED: {resp.status_code}")
        print(f"[submit] Response: {resp.text[:500]}")
        sys.exit(1)


def poll_status(base_url: str, service_token: str, briefing_id: int) -> str:
    """
    Pollt /api/report/status/{briefing_id} bis done oder failed.

    Returns:
        Final status string
    """
    url = f"{base_url}/api/report/status/{briefing_id}"
    headers = {"X-Service-Token": service_token}

    print(f"[poll] Waiting for report generation...")

    for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                print(f"[poll] Attempt {attempt}/{POLL_MAX_ATTEMPTS}: status={status}")

                if status == "done":
                    return status
                elif status == "failed":
                    print(f"[poll] Report generation failed!")
                    return status
                # Continue polling for queued/running/pending
            else:
                print(f"[poll] Status check failed: {resp.status_code}")
        except requests.RequestException as e:
            print(f"[poll] Request error: {e}")

        time.sleep(POLL_INTERVAL_SEC)

    print(f"[poll] Timeout after {POLL_MAX_ATTEMPTS} attempts")
    return "timeout"


def download_html(base_url: str, service_token: str, briefing_id: int) -> Optional[bytes]:
    """Download HTML report via robust endpoint (no suffix conflicts)."""
    url = f"{base_url}/api/report/html/{briefing_id}"
    headers = {"X-Service-Token": service_token}

    print(f"[download] GET {url}")

    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code == 200:
        print(f"[download] HTML: {len(resp.content)} bytes")
        return resp.content
    else:
        print(f"[download] HTML failed: {resp.status_code} - {resp.text[:200]}")
        return None


def download_pdf(base_url: str, service_token: str, briefing_id: int) -> Optional[bytes]:
    """Download PDF report via robust endpoint (follows redirects, no suffix conflicts)."""
    url = f"{base_url}/api/report/pdf/{briefing_id}"
    headers = {"X-Service-Token": service_token}

    print(f"[download] GET {url}")

    resp = requests.get(url, headers=headers, timeout=120, allow_redirects=True)
    if resp.status_code == 200:
        # Check if we got a PDF
        content_type = resp.headers.get("content-type", "")
        if "pdf" in content_type.lower() or resp.content[:4] == b"%PDF":
            print(f"[download] PDF: {len(resp.content)} bytes")
            return resp.content
        else:
            print(f"[download] PDF: unexpected content-type: {content_type}")
            return None
    elif resp.status_code == 404:
        print(f"[download] PDF not available (404)")
        return None
    else:
        print(f"[download] PDF failed: {resp.status_code} - {resp.text[:200]}")
        return None


def save_artifacts(
    profile_id: str,
    briefing_id: int,
    html_bytes: Optional[bytes],
    pdf_bytes: Optional[bytes]
) -> Dict[str, Any]:
    """
    Speichert Artefakte und berechnet Hashes.

    Returns:
        hashes.json content
    """
    output_dir = ARTIFACTS_DIR / profile_id
    output_dir.mkdir(parents=True, exist_ok=True)

    hashes: Dict[str, Any] = {
        "profile_id": profile_id,
        "briefing_id": briefing_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    if html_bytes:
        html_path = output_dir / "report.html"
        html_path.write_bytes(html_bytes)
        hashes["html_sha256"] = sha256_hex(html_bytes)
        hashes["html_size"] = len(html_bytes)
        print(f"[save] HTML -> {html_path}")

    if pdf_bytes:
        pdf_path = output_dir / "report.pdf"
        pdf_path.write_bytes(pdf_bytes)
        hashes["pdf_sha256"] = sha256_hex(pdf_bytes)
        hashes["pdf_size"] = len(pdf_bytes)
        print(f"[save] PDF -> {pdf_path}")

    # Save hashes.json
    hashes_path = output_dir / "hashes.json"
    with open(hashes_path, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, ensure_ascii=False)
    print(f"[save] Hashes -> {hashes_path}")

    return hashes


def process_profile(
    profile_name: str,
    base_url: str,
    service_token: str,
    lang: str = "de"
) -> Dict[str, Any]:
    """
    Verarbeitet ein einzelnes Profil end-to-end.

    Returns:
        Result dict with status and hashes
    """
    print(f"\n{'='*60}")
    print(f"[profile] {profile_name}")
    print(f"{'='*60}")

    # 1. Load profile
    profile_data = load_profile(profile_name)
    answers = profile_data.get("answers", profile_data)

    # 2. Submit briefing
    briefing_id = submit_briefing(base_url, service_token, answers, lang)

    # 3. Poll until done
    status = poll_status(base_url, service_token, briefing_id)
    if status != "done":
        return {
            "profile": profile_name,
            "briefing_id": briefing_id,
            "status": status,
            "error": f"Report generation ended with status: {status}"
        }

    # 4. Download HTML
    html_bytes = download_html(base_url, service_token, briefing_id)

    # 5. Download PDF
    pdf_bytes = download_pdf(base_url, service_token, briefing_id)

    # 6. Save artifacts and compute hashes
    hashes = save_artifacts(profile_name, briefing_id, html_bytes, pdf_bytes)

    return {
        "profile": profile_name,
        "briefing_id": briefing_id,
        "status": "success",
        "hashes": hashes,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Golden Report Artifacts via Service-Token"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Backend base URL (e.g. https://api.ki-sicherheit.jetzt)"
    )
    parser.add_argument(
        "--profile",
        choices=list(AVAILABLE_PROFILES.keys()),
        help="Single profile to process"
    )
    parser.add_argument(
        "--lang",
        default="de",
        help="Language (default: de)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all profiles"
    )

    args = parser.parse_args()

    # Service-Token aus ENV
    secret = os.getenv("SERVICE_TOKEN_SECRET")
    if not secret:
        print("ERROR: SERVICE_TOKEN_SECRET not set")
        print("Usage: export SERVICE_TOKEN_SECRET='your-secret'")
        sys.exit(1)

    service_token = f"golden_reports:{secret}"

    # Determine profiles to run
    if args.all:
        profiles_to_run = list(AVAILABLE_PROFILES.keys())
    elif args.profile:
        profiles_to_run = [args.profile]
    else:
        print("ERROR: Specify --profile <name> or --all")
        sys.exit(1)

    # Process profiles
    results = []
    for profile_name in profiles_to_run:
        result = process_profile(profile_name, args.base_url, service_token, args.lang)
        results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("[summary] Results:")
    print(f"{'='*60}")

    success_count = 0
    for r in results:
        status_icon = "OK" if r.get("status") == "success" else "FAIL"
        print(f"  [{status_icon}] {r['profile']}: briefing_id={r.get('briefing_id')}")
        if r.get("status") == "success":
            success_count += 1
            hashes = r.get("hashes", {})
            if hashes.get("html_sha256"):
                print(f"       HTML: {hashes['html_sha256'][:16]}...")
            if hashes.get("pdf_sha256"):
                print(f"       PDF:  {hashes['pdf_sha256'][:16]}...")

    print(f"\nTotal: {success_count}/{len(results)} successful")
    print(f"Artifacts saved to: {ARTIFACTS_DIR}")

    # Exit with error if any failed
    if success_count < len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()

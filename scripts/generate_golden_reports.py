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
  4. [GATE] GET /api/report/summary/{briefing_id} - Qualitäts-Gate (nur bei --all)
  5. GET /api/report/html/{briefing_id}  (robust, keine Suffix-Konflikte)
  6. GET /api/report/pdf/{briefing_id}   (robust, keine Suffix-Konflikte)
  7. Berechnet SHA-256 Hashes
  8. Speichert unter artifacts/golden_reports/<profile_id>/

Usage:
  export SERVICE_TOKEN_SECRET="your-secret"
  python scripts/generate_golden_reports.py --base-url https://api.example.com
  python scripts/generate_golden_reports.py --base-url https://api.example.com --profile solo
  python scripts/generate_golden_reports.py --base-url https://api.example.com --all

Version: 2.1.0 (Golden Artifacts + Summary Gate)
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
MANIFEST_PATH = REPO_ROOT / "data" / "golden_profiles_manifest.json"

# ---------------------------------------------------------------------------
# GOLDEN PROFILES MANIFEST
# ---------------------------------------------------------------------------
# Golden Runs use profiles defined in: data/golden_profiles_manifest.json
# Changes to Golden profiles are review-required to ensure reproducibility.
# Do NOT add ad-hoc profiles here - update the manifest instead.
# ---------------------------------------------------------------------------

# Verfügbare Profile (aus test_profiles_gold_optimized)
# Must match profiles listed in golden_profiles_manifest.json
AVAILABLE_PROFILES = {
    "solo": "solo_beratung_ki_assessments_optimized.json",
    "team_finance": "team_finance_insurance_advisory_optimized.json",
    "kmu_france": "kmu_france_eu_core_en_gold_optimized.json",
}

# Polling-Konfiguration
POLL_INTERVAL_SEC = 5
POLL_MAX_ATTEMPTS = 120  # 10 Minuten max


# ---------------------------------------------------------------------------
# MANIFEST LOADING
# ---------------------------------------------------------------------------
def load_manifest() -> Dict[str, Any]:
    """
    Lädt das Golden Profiles Manifest.

    Returns:
        Manifest dict oder leeres dict wenn nicht vorhanden
    """
    if not MANIFEST_PATH.exists():
        print(f"[manifest] WARNING: Manifest not found: {MANIFEST_PATH}")
        return {}

    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"[manifest] Loaded: {len(manifest.get('profiles', []))} profiles")
        return manifest
    except Exception as e:
        print(f"[manifest] ERROR loading manifest: {e}")
        return {}


def is_profile_in_manifest(profile_name: str, manifest: Dict[str, Any]) -> bool:
    """Prüft ob ein Profil im Manifest enthalten ist."""
    if not manifest:
        return False

    profile_filename = AVAILABLE_PROFILES.get(profile_name)
    if not profile_filename:
        return False

    manifest_profiles = manifest.get("profiles", [])
    return profile_filename in manifest_profiles


# ---------------------------------------------------------------------------
# SUMMARY GATE (Quality Gate for Golden Runs)
# ---------------------------------------------------------------------------
def fetch_summary(base_url: str, service_token: str, briefing_id: int) -> Optional[str]:
    """
    Fetch plain-text summary from /api/report/summary/{briefing_id}.

    Returns:
        Summary text or None on error
    """
    url = f"{base_url}/api/report/summary/{briefing_id}"
    headers = {"X-Service-Token": service_token}

    print(f"[gate] GET {url}")

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            print(f"[gate] Summary received: {len(resp.text)} chars")
            return resp.text
        else:
            print(f"[gate] Summary fetch failed: {resp.status_code} - {resp.text[:200]}")
            return None
    except requests.RequestException as e:
        print(f"[gate] Summary fetch error: {e}")
        return None


def parse_summary(summary_text: str) -> Dict[str, Any]:
    """
    Parse plain-text summary into dict.

    Format: key: value (one per line)
    Special handling for lists like badges_missing: ['a', 'b']
    """
    parsed = {}

    for line in summary_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("  -"):
            # Skip empty lines and indented list items (warnings/errors details)
            continue

        if ": " in line:
            key, value = line.split(": ", 1)
            key = key.strip()
            value = value.strip()

            # Try to parse as int
            if value.isdigit():
                parsed[key] = int(value)
            # Try to parse as boolean
            elif value.lower() in ("true", "false"):
                parsed[key] = value.lower() == "true"
            # Try to parse as list (Python repr format)
            elif value.startswith("[") and value.endswith("]"):
                try:
                    # Handle Python list repr like ['a', 'b'] or []
                    parsed[key] = eval(value)  # Safe for our controlled format
                except Exception:
                    parsed[key] = value
            else:
                parsed[key] = value

    return parsed


def validate_summary_gate(parsed_summary: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate summary against Golden Gate rules.

    Rules (strict, for Golden Runs):
    - errors: 0
    - sections_missing: 0
    - badges_missing: [] (empty list)
    - json_valid: true
    - report_status: done (or 'none' is acceptable if analysis exists)
    - pdf_url_present: false is OK (PDF is on-demand)

    Returns:
        (passed: bool, failures: list of failure messages)
    """
    failures = []

    # Rule 1: errors must be 0
    errors = parsed_summary.get("errors", -1)
    if errors != 0:
        failures.append(f"errors: {errors} (expected: 0)")

    # Rule 2: sections_missing must be 0
    sections_missing = parsed_summary.get("sections_missing", -1)
    if sections_missing != 0:
        missing_list = parsed_summary.get("sections_missing_list", [])
        failures.append(f"sections_missing: {sections_missing} {missing_list}")

    # Rule 3: badges_missing must be empty
    badges_missing = parsed_summary.get("badges_missing", None)
    if badges_missing is None:
        failures.append("badges_missing: field not found")
    elif isinstance(badges_missing, list) and len(badges_missing) > 0:
        failures.append(f"badges_missing: {badges_missing}")
    elif isinstance(badges_missing, str) and badges_missing != "[]":
        failures.append(f"badges_missing: {badges_missing}")

    # Rule 4: json_valid must be true
    json_valid = parsed_summary.get("json_valid", False)
    if not json_valid:
        failures.append(f"json_valid: {json_valid} (expected: true)")

    # Rule 5: html_valid should be true
    html_valid = parsed_summary.get("html_valid", False)
    if not html_valid:
        failures.append(f"html_valid: {html_valid} (expected: true)")

    # Note: pdf_url_present: false is OK (PDF is generated on-demand)
    # Note: report_status: none is OK if analysis exists

    passed = len(failures) == 0
    return passed, failures


def save_summary_artifact(profile_id: str, summary_text: str) -> Path:
    """Save summary as artifact for debugging/CI."""
    output_dir = ARTIFACTS_DIR / profile_id
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "summary.txt"
    summary_path.write_text(summary_text, encoding="utf-8")
    print(f"[gate] Summary saved: {summary_path}")
    return summary_path


def run_summary_gate(
    base_url: str,
    service_token: str,
    briefing_id: int,
    profile_id: str,
) -> Tuple[bool, Optional[str]]:
    """
    Run the full Summary Gate check.

    Returns:
        (passed: bool, error_message: Optional[str])
    """
    print(f"\n[gate] Running Summary Gate for {profile_id}...")

    # 1. Fetch summary
    summary_text = fetch_summary(base_url, service_token, briefing_id)
    if not summary_text:
        return False, "Failed to fetch summary"

    # 2. Save as artifact (always, for debugging)
    save_summary_artifact(profile_id, summary_text)

    # 3. Parse summary
    parsed = parse_summary(summary_text)
    if not parsed:
        return False, "Failed to parse summary"

    # 4. Validate against gate rules
    passed, failures = validate_summary_gate(parsed)

    if passed:
        print(f"[gate] ✅ PASSED - All quality checks OK")
        return True, None
    else:
        print(f"[gate] ❌ FAILED - {len(failures)} issue(s):")
        for f in failures:
            print(f"[gate]   - {f}")
        return False, f"Gate failed: {'; '.join(failures)}"


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
    lang: str = "de",
    run_gate: bool = False,
) -> Dict[str, Any]:
    """
    Verarbeitet ein einzelnes Profil end-to-end.

    Args:
        profile_name: Name des Profils
        base_url: Backend URL
        service_token: Service-Token für Auth
        lang: Sprache (default: de)
        run_gate: Ob das Summary-Gate ausgeführt werden soll

    Returns:
        Result dict with status, hashes, and gate_result
    """
    print(f"\n{'='*60}")
    print(f"[profile] {profile_name}")
    if run_gate:
        print(f"[profile] Summary Gate: ENABLED (Golden Run)")
    else:
        print(f"[profile] Summary Gate: disabled (ad-hoc run)")
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

    # 4. Run Summary Gate (if enabled)
    gate_passed = True
    gate_error = None
    if run_gate:
        gate_passed, gate_error = run_summary_gate(
            base_url, service_token, briefing_id, profile_name
        )
        if not gate_passed:
            return {
                "profile": profile_name,
                "briefing_id": briefing_id,
                "status": "gate_failed",
                "error": gate_error,
            }

    # 5. Download HTML
    html_bytes = download_html(base_url, service_token, briefing_id)

    # 6. Download PDF
    pdf_bytes = download_pdf(base_url, service_token, briefing_id)

    # 7. Save artifacts and compute hashes
    hashes = save_artifacts(profile_name, briefing_id, html_bytes, pdf_bytes)

    return {
        "profile": profile_name,
        "briefing_id": briefing_id,
        "status": "success",
        "hashes": hashes,
        "gate_passed": gate_passed if run_gate else None,
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
        help="Process all profiles (enables Summary Gate)"
    )
    parser.add_argument(
        "--use-manifest",
        action="store_true",
        help="Enable Summary Gate for single profile if in manifest"
    )
    parser.add_argument(
        "--skip-gate",
        action="store_true",
        help="Skip Summary Gate even for --all (for debugging)"
    )

    args = parser.parse_args()

    # Service-Token aus ENV
    secret = os.getenv("SERVICE_TOKEN_SECRET")
    if not secret:
        print("ERROR: SERVICE_TOKEN_SECRET not set")
        print("Usage: export SERVICE_TOKEN_SECRET='your-secret'")
        sys.exit(1)

    service_token = f"golden_reports:{secret}"

    # Load manifest for gate decisions
    manifest = load_manifest()

    # Determine profiles to run and gate status
    if args.all:
        profiles_to_run = list(AVAILABLE_PROFILES.keys())
        # Gate is ENABLED for --all (unless --skip-gate)
        run_gate = not args.skip_gate
        print(f"\n[mode] Running ALL profiles (Golden Run)")
        print(f"[mode] Summary Gate: {'ENABLED' if run_gate else 'DISABLED (--skip-gate)'}")
    elif args.profile:
        profiles_to_run = [args.profile]
        # Gate is enabled for single profile only if:
        # - --use-manifest is set, OR
        # - profile is in manifest
        in_manifest = is_profile_in_manifest(args.profile, manifest)
        run_gate = (args.use_manifest or in_manifest) and not args.skip_gate
        print(f"\n[mode] Running single profile: {args.profile}")
        print(f"[mode] Profile in manifest: {in_manifest}")
        print(f"[mode] Summary Gate: {'ENABLED' if run_gate else 'disabled (ad-hoc)'}")
    else:
        print("ERROR: Specify --profile <name> or --all")
        sys.exit(1)

    # Process profiles
    results = []
    gate_failures = []
    for profile_name in profiles_to_run:
        result = process_profile(
            profile_name,
            args.base_url,
            service_token,
            args.lang,
            run_gate=run_gate,
        )
        results.append(result)

        # Track gate failures separately
        if result.get("status") == "gate_failed":
            gate_failures.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("[summary] Results:")
    print(f"{'='*60}")

    success_count = 0
    for r in results:
        status = r.get("status", "unknown")
        if status == "success":
            status_icon = "✅ OK"
            success_count += 1
        elif status == "gate_failed":
            status_icon = "🚫 GATE"
        else:
            status_icon = "❌ FAIL"

        print(f"  [{status_icon}] {r['profile']}: briefing_id={r.get('briefing_id')}")

        if status == "success":
            hashes = r.get("hashes", {})
            if hashes.get("html_sha256"):
                print(f"       HTML: {hashes['html_sha256'][:16]}...")
            if hashes.get("pdf_sha256"):
                print(f"       PDF:  {hashes['pdf_sha256'][:16]}...")
            if r.get("gate_passed"):
                print(f"       Gate: ✅ PASSED")
        elif status == "gate_failed":
            print(f"       Error: {r.get('error', 'unknown')}")

    print(f"\nTotal: {success_count}/{len(results)} successful")
    if run_gate:
        print(f"Gate Failures: {len(gate_failures)}")
    print(f"Artifacts saved to: {ARTIFACTS_DIR}")

    # Exit with error if any failed
    if success_count < len(results):
        if gate_failures:
            print(f"\n❌ GATE FAILED: {len(gate_failures)} profile(s) did not pass quality gate")
        sys.exit(1)

    if run_gate and success_count == len(results):
        print(f"\n✅ All {len(results)} Golden profiles passed the quality gate!")


if __name__ == "__main__":
    main()

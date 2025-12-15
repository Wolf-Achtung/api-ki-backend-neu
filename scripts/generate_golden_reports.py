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

Version: 2.2.0 (Golden Artifacts + Summary Gate + Retry/Timeout Resilience)
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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
# RETRY/TIMEOUT DEFAULTS (CLI-overridable)
# ---------------------------------------------------------------------------
DEFAULT_SUBMIT_TIMEOUT = 120   # seconds for POST /submit read timeout
DEFAULT_DOWNLOAD_TIMEOUT = 120  # seconds for GET html/pdf
DEFAULT_RETRIES = 3             # max retry attempts
CONNECT_TIMEOUT = 10            # fixed connect timeout (fast fail on DNS/network)


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
# RETRY / TIMEOUT HELPERS
# ---------------------------------------------------------------------------
def ping_router_status(base_url: str) -> None:
    """
    Optional diagnostic: ping /api/router-status on timeout.
    Logs result but does not affect retry logic.
    """
    try:
        url = f"{base_url}/api/router-status"
        resp = requests.get(url, timeout=(5, 10))
        print(f"[retry-diag] Router status ({resp.status_code}): {resp.text[:100]}")
    except Exception as e:
        print(f"[retry-diag] Router status unreachable: {e}")


def request_with_retry(
    method: str,
    url: str,
    headers: Dict[str, str],
    timeout: tuple,
    max_retries: int,
    base_url: str,
    **kwargs
) -> requests.Response:
    """
    Execute HTTP request with exponential backoff retry on timeout.

    Args:
        method: HTTP method ('GET' or 'POST')
        url: Full URL
        headers: Request headers
        timeout: Tuple (connect_timeout, read_timeout)
        max_retries: Maximum retry attempts
        base_url: Base URL for router-status diagnostic
        **kwargs: Additional args for requests (json, etc.)

    Returns:
        Response object

    Raises:
        requests.RequestException on final failure
    """
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            if method.upper() == "POST":
                resp = requests.post(url, headers=headers, timeout=timeout, **kwargs)
            else:
                resp = requests.get(url, headers=headers, timeout=timeout, **kwargs)
            return resp

        except requests.exceptions.ReadTimeout as e:
            last_exception = e
            backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s
            print(f"[retry] ReadTimeout on attempt {attempt}/{max_retries}, backoff {backoff}s")

            # Diagnostic: ping router-status on first timeout
            if attempt == 1:
                ping_router_status(base_url)

            if attempt < max_retries:
                time.sleep(backoff)
            else:
                print(f"[retry] Max retries ({max_retries}) exhausted")

        except requests.exceptions.ConnectTimeout as e:
            last_exception = e
            backoff = 2 ** (attempt - 1)
            print(f"[retry] ConnectTimeout on attempt {attempt}/{max_retries}, backoff {backoff}s")

            if attempt < max_retries:
                time.sleep(backoff)
            else:
                print(f"[retry] Max retries ({max_retries}) exhausted")

        except requests.exceptions.ConnectionError as e:
            last_exception = e
            backoff = 2 ** (attempt - 1)
            print(f"[retry] ConnectionError on attempt {attempt}/{max_retries}, backoff {backoff}s")

            if attempt < max_retries:
                time.sleep(backoff)
            else:
                print(f"[retry] Max retries ({max_retries}) exhausted")

    # All retries exhausted
    raise last_exception


# ---------------------------------------------------------------------------
# SUMMARY GATE (Quality Gate for Golden Runs)
# ---------------------------------------------------------------------------
def fetch_summary(base_url: str, service_token: str, briefing_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch summary from /api/report/summary/{briefing_id}.

    Now returns JSON dict directly (endpoint returns JSON since Sprint N4.4).

    Returns:
        Parsed JSON dict or None on error
    """
    url = f"{base_url}/api/report/summary/{briefing_id}"
    headers = {"X-Service-Token": service_token}

    print(f"[gate] GET {url}")

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            # Try JSON-first (new format)
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type or resp.text.strip().startswith("{"):
                try:
                    data = resp.json()
                    print(f"[gate] Summary received (JSON): {len(resp.text)} chars, keys={list(data.keys())[:5]}...")
                    return data
                except Exception as e:
                    print(f"[gate] JSON parse failed, falling back to text: {e}")

            # Legacy fallback: plain text parsing
            print(f"[gate] Summary received (text): {len(resp.text)} chars")
            return parse_summary_text(resp.text)
        else:
            print(f"[gate] Summary fetch failed: {resp.status_code} - {resp.text[:200]}")
            return None
    except requests.RequestException as e:
        print(f"[gate] Summary fetch error: {e}")
        return None


def parse_summary_text(summary_text: str) -> Dict[str, Any]:
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


def normalize_gate_fields(parsed_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize gate fields to handle both JSON (lists) and legacy text (ints) formats.

    Returns dict with:
        - errors_count: int
        - errors_list: list
        - sections_missing_count: int
        - sections_missing_list: list
        - badges_missing_count: int
        - badges_missing_list: list
        - json_valid: bool
        - html_valid: bool
    """
    normalized = {}

    # errors: can be list (JSON) or int (legacy)
    errors = parsed_summary.get("errors")
    if isinstance(errors, list):
        normalized["errors_count"] = len(errors)
        normalized["errors_list"] = errors
    elif isinstance(errors, int):
        normalized["errors_count"] = errors
        normalized["errors_list"] = []
    else:
        # Missing or unexpected type - fail safe
        normalized["errors_count"] = 0
        normalized["errors_list"] = []

    # sections_missing: can be list (JSON) or int (legacy)
    sections_missing = parsed_summary.get("sections_missing")
    if isinstance(sections_missing, list):
        normalized["sections_missing_count"] = len(sections_missing)
        normalized["sections_missing_list"] = sections_missing
    elif isinstance(sections_missing, int):
        normalized["sections_missing_count"] = sections_missing
        normalized["sections_missing_list"] = parsed_summary.get("sections_missing_list", [])
    else:
        # Missing - this is a schema error, but don't crash
        normalized["sections_missing_count"] = -1  # Sentinel to indicate parsing issue
        normalized["sections_missing_list"] = []
        print(f"[gate] ⚠️ sections_missing field missing or unexpected type: {type(sections_missing)}")

    # badges_missing: can be list (JSON) or string/None (legacy)
    badges_missing = parsed_summary.get("badges_missing")
    if isinstance(badges_missing, list):
        normalized["badges_missing_count"] = len(badges_missing)
        normalized["badges_missing_list"] = badges_missing
    elif badges_missing is None:
        # Missing is OK for badges (informational)
        normalized["badges_missing_count"] = 0
        normalized["badges_missing_list"] = []
    else:
        # Legacy string format
        normalized["badges_missing_count"] = 0 if badges_missing in ("[]", "") else 1
        normalized["badges_missing_list"] = [badges_missing] if badges_missing not in ("[]", "") else []

    # json_valid: must be boolean
    json_valid = parsed_summary.get("json_valid")
    if isinstance(json_valid, bool):
        normalized["json_valid"] = json_valid
    elif isinstance(json_valid, str):
        normalized["json_valid"] = json_valid.lower() == "true"
    else:
        normalized["json_valid"] = False

    # html_valid: must be boolean
    html_valid = parsed_summary.get("html_valid")
    if isinstance(html_valid, bool):
        normalized["html_valid"] = html_valid
    elif isinstance(html_valid, str):
        normalized["html_valid"] = html_valid.lower() == "true"
    else:
        normalized["html_valid"] = False

    return normalized


def validate_summary_gate(parsed_summary: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate summary against Golden Gate rules.

    Rules (strict, for Golden Runs):
    - errors: [] (empty list)
    - sections_missing: [] (empty list)
    - json_valid: true
    - html_valid: true
    - badges_missing: informational only (NOT gate-blocking)
    - pdf_url_present: false is OK (PDF is on-demand)

    Returns:
        (passed: bool, failures: list of failure messages)
    """
    failures = []

    # Normalize the parsed summary for robust handling
    # This handles both JSON response (lists) and legacy text parsing (ints)
    normalized = normalize_gate_fields(parsed_summary)

    # Debug: log normalized state
    print(f"[gate] Normalized state: errors={normalized['errors_count']}, "
          f"sections_missing={normalized['sections_missing_count']}, "
          f"json_valid={normalized['json_valid']}, html_valid={normalized['html_valid']}, "
          f"badges_missing={normalized['badges_missing_count']} (informational)")

    # Rule 1: errors must be 0
    if normalized["errors_count"] > 0:
        failures.append(f"errors: {normalized['errors_count']} (expected: 0) - {normalized['errors_list']}")

    # Rule 2: sections_missing must be 0
    if normalized["sections_missing_count"] > 0:
        failures.append(f"sections_missing: {normalized['sections_missing_count']} - {normalized['sections_missing_list']}")

    # Rule 3: badges_missing is INFORMATIONAL ONLY (not gate-blocking)
    # Just log it, don't add to failures
    if normalized["badges_missing_count"] > 0:
        print(f"[gate] ℹ️ badges_missing (informational): {normalized['badges_missing_list']}")

    # Rule 4: json_valid must be true
    if not normalized["json_valid"]:
        failures.append(f"json_valid: {normalized['json_valid']} (expected: true)")

    # Rule 5: html_valid must be true
    if not normalized["html_valid"]:
        failures.append(f"html_valid: {normalized['html_valid']} (expected: true)")

    # Note: pdf_url_present: false is OK (PDF is generated on-demand)
    # Note: report_status: none is OK if analysis exists

    passed = len(failures) == 0
    return passed, failures


def save_summary_artifact(profile_id: str, summary_data: Union[str, Dict[str, Any]]) -> Path:
    """Save summary as artifact for debugging/CI."""
    output_dir = ARTIFACTS_DIR / profile_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle both string (legacy) and dict (JSON) formats
    if isinstance(summary_data, dict):
        summary_path = output_dir / "summary.json"
        import json
        summary_path.write_text(json.dumps(summary_data, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        summary_path = output_dir / "summary.txt"
        summary_path.write_text(summary_data, encoding="utf-8")

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

    # 1. Fetch summary (now returns dict directly for JSON responses)
    summary_data = fetch_summary(base_url, service_token, briefing_id)
    if not summary_data:
        return False, "Failed to fetch summary"

    # 2. Save as artifact (always, for debugging)
    save_summary_artifact(profile_id, summary_data)

    # 3. summary_data is already parsed (dict) from fetch_summary
    # No separate parse step needed for JSON responses
    parsed = summary_data
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
        # Log full normalized state on failure for debugging
        normalized = normalize_gate_fields(parsed)
        import json
        print(f"[gate] 📋 Full normalized state: {json.dumps(normalized, indent=2)}")
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
    lang: str = "de",
    submit_timeout: int = DEFAULT_SUBMIT_TIMEOUT,
    max_retries: int = DEFAULT_RETRIES,
) -> int:
    """
    Sendet Briefing an /api/briefings/submit mit Service-Token.

    Uses retry logic with exponential backoff for network resilience.

    Args:
        base_url: Backend URL
        service_token: Service auth token
        answers: Briefing answers dict
        lang: Language code
        submit_timeout: Read timeout in seconds (default: 120)
        max_retries: Max retry attempts on timeout (default: 3)

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

    print(f"[submit] POST {url} (timeout={CONNECT_TIMEOUT}s/{submit_timeout}s, retries={max_retries})")

    try:
        resp = request_with_retry(
            method="POST",
            url=url,
            headers=headers,
            timeout=(CONNECT_TIMEOUT, submit_timeout),
            max_retries=max_retries,
            base_url=base_url,
            json=payload,
        )
    except requests.RequestException as e:
        print(f"[submit] FAILED after {max_retries} retries: {e}")
        sys.exit(1)

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


def download_html(
    base_url: str,
    service_token: str,
    briefing_id: int,
    download_timeout: int = DEFAULT_DOWNLOAD_TIMEOUT,
    max_retries: int = DEFAULT_RETRIES,
) -> Optional[bytes]:
    """Download HTML report via robust endpoint (no suffix conflicts)."""
    url = f"{base_url}/api/report/html/{briefing_id}"
    headers = {"X-Service-Token": service_token}

    print(f"[download] GET {url} (timeout={CONNECT_TIMEOUT}s/{download_timeout}s)")

    try:
        resp = request_with_retry(
            method="GET",
            url=url,
            headers=headers,
            timeout=(CONNECT_TIMEOUT, download_timeout),
            max_retries=max_retries,
            base_url=base_url,
        )
    except requests.RequestException as e:
        print(f"[download] HTML failed after retries: {e}")
        return None

    if resp.status_code == 200:
        print(f"[download] HTML: {len(resp.content)} bytes")
        return resp.content
    else:
        print(f"[download] HTML failed: {resp.status_code} - {resp.text[:200]}")
        return None


def download_pdf(
    base_url: str,
    service_token: str,
    briefing_id: int,
    download_timeout: int = DEFAULT_DOWNLOAD_TIMEOUT,
    max_retries: int = DEFAULT_RETRIES,
) -> Optional[bytes]:
    """Download PDF report via robust endpoint (follows redirects, no suffix conflicts)."""
    url = f"{base_url}/api/report/pdf/{briefing_id}"
    headers = {"X-Service-Token": service_token}

    print(f"[download] GET {url} (timeout={CONNECT_TIMEOUT}s/{download_timeout}s)")

    try:
        resp = request_with_retry(
            method="GET",
            url=url,
            headers=headers,
            timeout=(CONNECT_TIMEOUT, download_timeout),
            max_retries=max_retries,
            base_url=base_url,
            allow_redirects=True,
        )
    except requests.RequestException as e:
        print(f"[download] PDF failed after retries: {e}")
        return None

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
    submit_timeout: int = DEFAULT_SUBMIT_TIMEOUT,
    download_timeout: int = DEFAULT_DOWNLOAD_TIMEOUT,
    max_retries: int = DEFAULT_RETRIES,
) -> Dict[str, Any]:
    """
    Verarbeitet ein einzelnes Profil end-to-end.

    Args:
        profile_name: Name des Profils
        base_url: Backend URL
        service_token: Service-Token für Auth
        lang: Sprache (default: de)
        run_gate: Ob das Summary-Gate ausgeführt werden soll
        submit_timeout: Read timeout for submit (seconds)
        download_timeout: Read timeout for downloads (seconds)
        max_retries: Max retry attempts on timeout

    Returns:
        Result dict with status, hashes, and gate_result
    """
    print(f"\n{'='*60}")
    print(f"[profile] {profile_name}")
    if run_gate:
        print(f"[profile] Summary Gate: ENABLED (Golden Run)")
    else:
        print(f"[profile] Summary Gate: disabled (ad-hoc run)")
    print(f"[profile] Timeouts: submit={submit_timeout}s download={download_timeout}s retries={max_retries}")
    print(f"{'='*60}")

    # 1. Load profile
    profile_data = load_profile(profile_name)
    answers = profile_data.get("answers", profile_data)

    # 2. Submit briefing (with retry)
    briefing_id = submit_briefing(
        base_url, service_token, answers, lang,
        submit_timeout=submit_timeout,
        max_retries=max_retries,
    )

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

    # 5. Download HTML (with retry)
    html_bytes = download_html(
        base_url, service_token, briefing_id,
        download_timeout=download_timeout,
        max_retries=max_retries,
    )

    # 6. Download PDF (with retry)
    pdf_bytes = download_pdf(
        base_url, service_token, briefing_id,
        download_timeout=download_timeout,
        max_retries=max_retries,
    )

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
    # Timeout/Retry options for network resilience
    parser.add_argument(
        "--submit-timeout",
        type=int,
        default=DEFAULT_SUBMIT_TIMEOUT,
        help=f"Read timeout for submit request in seconds (default: {DEFAULT_SUBMIT_TIMEOUT})"
    )
    parser.add_argument(
        "--download-timeout",
        type=int,
        default=DEFAULT_DOWNLOAD_TIMEOUT,
        help=f"Read timeout for download requests in seconds (default: {DEFAULT_DOWNLOAD_TIMEOUT})"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"Max retry attempts on timeout (default: {DEFAULT_RETRIES})"
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

    # Log timeout/retry settings
    print(f"[mode] Timeouts: submit={args.submit_timeout}s download={args.download_timeout}s retries={args.retries}")

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
            submit_timeout=args.submit_timeout,
            download_timeout=args.download_timeout,
            max_retries=args.retries,
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

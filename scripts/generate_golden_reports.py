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
import ast
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

# Repo-Root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# Add repo root to path for imports
sys.path.insert(0, str(REPO_ROOT))

# =============================================================================
# FIX 1: PLATIN+++ v5.4 - Forbidden tokens that must not appear in final HTML/PDF
# =============================================================================
FORBIDDEN_TOKENS: List[str] = [
    "DEFAULT_STUNDENSATZ_EUR",
    "DEFAULT_",  # Any DEFAULT_ pattern
    "{{",        # Unresolved template placeholders
    "}}",
    "PLACEHOLDER_",
    "TODO:",
    "FIXME:",
    "__DEBUG__",
]

# =============================================================================
# TEIL 3.1.1 + 3.1.4: German UI strings that must NOT appear in EN reports
# Extended to 80+ strings for comprehensive locale validation
# =============================================================================
DE_UI_STRINGS_EN_HARDFAIL: List[str] = [
    # Report Header / Meta
    "KI-Status-Report",
    "Überblick",
    "Unternehmensgröße",
    "Reportdatum",
    "Unternehmen",
    "Branche",
    "Unternehmensprofil",
    # Core Sections
    "Handlungsempfehlungen",
    "Nächste Schritte",
    "Bewertung",
    "Reifegrad",
    "Kennzahlen",
    "Risiken",
    "Maßnahmen",
    "Hauptziel",
    "Zusammenfassung",
    "Kurzfazit",
    "Empfehlung",
    "Empfehlungen",
    # Compliance/Notes
    "DSGVO-konforme",
    "DSGVO",
    "Hinweis",
    "Näherungen",
    "Datenschutz",
    "Compliance",
    # Business Case / Financial
    "Einsparungen",
    "Konservativ",
    "Realistisch",
    "Optimistisch",
    "Zeithorizont",
    "Priorität",
    "Verantwortung",
    "Kosten",
    "Nutzen",
    "Investition",
    "Wirtschaftlichkeit",
    "Aufwand",
    "Nutzenpotenzial",
    "Amortisation",
    "Förderpotenzial",
    # Risk / Strategy
    "Risikolage",
    "Risiko-Matrix",
    "Risikoprofil",
    "Priorisierung",
    "Verantwortlich",
    "Zielbild",
    "Roadmap",
    "Zeitplan",
    # Time Units
    "Monat",
    "Monate",
    "Quartal",
    "Woche",
    "Wochen",
    # Table Headers
    "Vergleich",
    "Wert",
    "Quelle",
    "Schätzung",
    "Beschreibung",
    "Auswirkung",
    "Eintrittswahrscheinlichkeit",
    # Section Headers (German patterns)
    "Ihr Unternehmen",
    "Ihre Branche",
    "Ihre nächsten",
    "Ihre Rechte",
    "Wesentliche Risiken",
    # Action / Process Labels
    "Schwerpunkt",
    "Umsetzung",
    "Förderchance",
    "Förderprogramme",
    "Bundesland",
    # KPI Labels
    "Sicherheit",
    "Wertschöpfung",
    "Befähigung",
    "Gesamt",
    "Durchschnitt",
    "Top-Quartil",
    # Misc UI Labels
    "Sehr gut",
    "Solide",
    "Ausbaufähig",
    "Branchenstudie",
    "Ihr Kerngeschäft",
]

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

    max_retries = max(1, max_retries)

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
                    parsed[key] = ast.literal_eval(value)
                except (ValueError, SyntaxError):
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


# =============================================================================
# FIX 1: PLATIN+++ v5.4 - Final HTML Token Scan (Hard-Fail Gate)
# =============================================================================
def _strip_noncontent(html: str) -> str:
    """
    Strip <style>, <script>, and base64 data URIs before token scanning.

    This prevents false positives from:
    - CSS minification artifacts like '}}' or '{{' in style rules
    - JavaScript template literals or object syntax
    - Base64-encoded images containing token-like sequences

    TEIL 3.1.3: Token-Scan False Positive Fix
    """
    # Strip <style> blocks (CSS can contain }} from minification)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.IGNORECASE | re.DOTALL)
    # Strip <script> blocks (JS can contain template syntax)
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.IGNORECASE | re.DOTALL)
    # Neutralize base64 data URIs (can contain any byte sequence)
    html = re.sub(r"data:image/[^\"']+;base64,[^\"']+", "data:image/…;base64,…", html, flags=re.IGNORECASE)
    return html


def scan_html_for_forbidden_tokens(html_bytes: bytes, profile_id: str) -> Tuple[bool, List[str]]:
    """
    Scan final HTML for forbidden development tokens.

    This is the LAST line of defense - if tokens appear here, Gate MUST fail.
    No report with visible tokens should reach test users.

    Args:
        html_bytes: Raw HTML content as bytes
        profile_id: For logging

    Returns:
        (passed: bool, found_tokens: list of found token strings)
    """
    if not html_bytes:
        return True, []  # No HTML = nothing to scan

    try:
        html_text = html_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[token-scan] ⚠️ Failed to decode HTML for {profile_id}: {e}")
        return True, []  # Decode error = can't scan, let it pass

    # TEIL 3.1.3: Strip <style>/<script>/base64 before scanning to avoid false positives
    scan_text = _strip_noncontent(html_text)

    found_tokens = []
    for token in FORBIDDEN_TOKENS:
        if token in scan_text:
            # Find context (first occurrence, up to 100 chars around it)
            idx = html_text.find(token)
            start = max(0, idx - 30)
            end = min(len(html_text), idx + len(token) + 30)
            context = html_text[start:end].replace("\n", " ").strip()
            found_tokens.append(f"{token} (context: ...{context}...)")

    if found_tokens:
        print(f"[token-scan] ❌ FAILED for {profile_id} - {len(found_tokens)} forbidden token(s) found:")
        for t in found_tokens:
            print(f"[token-scan]   - {t}")
        return False, found_tokens
    else:
        print(f"[token-scan] ✅ PASSED for {profile_id} - no forbidden tokens")
        return True, []


# =============================================================================
# QA-Gate v1: Prompt-leak detection (LLM assistant phrases in final HTML)
# =============================================================================
PROMPT_LEAK_PHRASES: List[str] = [
    # German assistant waiting phrases
    "du hast noch keine frage",
    "du hast noch keine aufgabe",
    "sie haben noch keine frage",
    "bitte beschreibe, wobei ich dir helfen",
    "bitte beschreibe kurz, was du benötigst",
    "wie kann ich dir helfen",
    "wie kann ich ihnen helfen",
    "womit kann ich ihnen dienen",
    "ich stehe dir zur verfügung",
    "ich stehe ihnen zur verfügung",
    "keine eingabe erkannt",
    "keine anfrage erkannt",
    # German generic LLM responses
    "ich sehe keine konkrete frage",
    "als ki-assistent",
    "als sprachmodell kann ich",
    "ich bin ein ki-assistent",
    "ich bin ein sprachmodell",
    # English assistant waiting phrases
    "you haven't asked a question yet",
    "please describe what you need help with",
    "how can i help you",
    "how can i assist you",
    "i'm waiting for your input",
    "no input detected",
    "what can i do for you today",
    # English generic LLM responses
    "i don't see a specific question",
    "as an ai assistant",
    "as a language model",
    "i'm an ai language model",
    "i'm just an ai",
]


def scan_html_for_prompt_leaks(html_text: str, profile_id: str) -> Tuple[bool, List[str]]:
    """
    QA-Gate v1: Scan HTML for prompt-leak phrases.

    These are LLM assistant phrases that indicate the model didn't understand
    the task and output generic waiting/help text instead of report content.

    Args:
        html_text: Decoded HTML content
        profile_id: For logging

    Returns:
        (passed: bool, found_leaks: list of found leak phrases)
    """
    if not html_text:
        return True, []

    # Strip style/script/base64 before scanning
    scan_text = _strip_noncontent(html_text).lower()

    found_leaks = []
    for phrase in PROMPT_LEAK_PHRASES:
        if phrase.lower() in scan_text:
            found_leaks.append(phrase)

    if found_leaks:
        print(f"[prompt-leak] ❌ FAILED for {profile_id} - {len(found_leaks)} prompt-leak phrase(s) found:")
        for leak in found_leaks[:5]:
            print(f"[prompt-leak]   - \"{leak}\"")
        if len(found_leaks) > 5:
            print(f"[prompt-leak]   ... and {len(found_leaks) - 5} more")
        return False, found_leaks
    else:
        print(f"[prompt-leak] ✅ PASSED for {profile_id} - no prompt-leak phrases")
        return True, []


# =============================================================================
# Multilingual v1 Step 5: UI text extractor using html.parser
# =============================================================================
class _UITextExtractor(HTMLParser):
    """
    Extract text content from elements with data-ui="1" attribute.

    This enables 2-tier locale scanning:
    - UI text (strict): Hard fail if German found
    - Content text (soft): Score/warn only, no fail
    """

    def __init__(self):
        super().__init__()
        self.ui_texts: List[str] = []
        self.all_texts: List[str] = []
        self._ui_element_stack: List[str] = []  # Stack of UI element tags
        self._in_style_script = 0  # Skip style/script content

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        # Track style/script to skip their content
        if tag in ("style", "script"):
            self._in_style_script += 1
            return

        # Check for data-ui="1" attribute
        attr_dict = dict(attrs)
        if attr_dict.get("data-ui") == "1":
            self._ui_element_stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("style", "script"):
            self._in_style_script = max(0, self._in_style_script - 1)
            return

        # Pop UI element from stack when matching tag closes
        if self._ui_element_stack and self._ui_element_stack[-1] == tag:
            self._ui_element_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._in_style_script > 0:
            return  # Skip style/script content

        text = data.strip()
        if not text:
            return

        self.all_texts.append(text)
        if self._ui_element_stack:  # Inside a UI element
            self.ui_texts.append(text)


def _extract_ui_and_content_text(html: str) -> Tuple[str, str, bool]:
    """
    Extract UI text (from data-ui="1" elements) and content text separately.

    Args:
        html: Full HTML content

    Returns:
        (ui_text: str, content_text: str, has_ui_markers: bool)
        - ui_text: Combined text from data-ui="1" elements
        - content_text: All other visible text
        - has_ui_markers: Whether any data-ui="1" markers were found
    """
    try:
        parser = _UITextExtractor()
        parser.feed(html)

        ui_text = " ".join(parser.ui_texts)
        all_text = " ".join(parser.all_texts)

        # Content text = all text minus UI text occurrences
        # Simple approach: just use all_text for content, but flag UI separately
        has_ui_markers = len(parser.ui_texts) > 0

        # For content, we use all text but the gate logic will check UI separately
        content_text = all_text

        return ui_text, content_text, has_ui_markers
    except Exception as e:
        print(f"[locale-scan] ⚠️ HTML parsing failed: {e}")
        return "", "", False


# =============================================================================
# Multilingual v1 Step 5: 2-tier Locale scan (UI strict / Content soft)
# =============================================================================
def scan_html_for_locale_leaks(html_text: str, expected_lang: str, profile_id: str) -> Tuple[bool, List[str]]:
    """
    Scan HTML for German UI strings when expected_lang is 'en'.

    Multilingual v1 Step 5: 2-tier scanning:
    - UI-Strict: German in data-ui="1" elements → HARD FAIL
    - Content-Soft: German elsewhere → WARN (score logged), but NO FAIL

    This enables EN reports to pass the gate even if LLM-generated content
    contains some German, as long as UI labels are correctly translated.

    Args:
        html_text: Decoded HTML content
        expected_lang: Expected language from profile ("en" or "de")
        profile_id: For logging

    Returns:
        (passed: bool, found_leaks: list of found German strings)
        - passed: True if UI scan passed (content warnings don't cause failure)
        - found_leaks: German strings found in UI (for backward compat)
    """
    if expected_lang != "en":
        return True, []  # Only check EN profiles

    # Step 1: Extract UI text and content text
    ui_text, content_text, has_ui_markers = _extract_ui_and_content_text(html_text)

    # Step 2: Strip style/script/base64 from content (fallback for non-UI scan)
    content_text_clean = _strip_noncontent(html_text) if not has_ui_markers else content_text

    # ==========================================================================
    # UI-STRICT SCAN (Hard Fail)
    # ==========================================================================
    ui_leaks = []
    if has_ui_markers:
        for de_string in DE_UI_STRINGS_EN_HARDFAIL:
            if de_string in ui_text:
                # Find context in original HTML
                idx = html_text.find(de_string)
                if idx >= 0:
                    start = max(0, idx - 20)
                    end = min(len(html_text), idx + len(de_string) + 20)
                    context = html_text[start:end].replace("\n", " ").strip()
                    ui_leaks.append(f"{de_string} (context: ...{context}...)")

        if ui_leaks:
            print(f"[locale-scan-ui] ❌ FAILED for {profile_id} - {len(ui_leaks)} German UI string(s) in EN report:")
            for leak in ui_leaks[:5]:
                print(f"[locale-scan-ui]   - {leak}")
            if len(ui_leaks) > 5:
                print(f"[locale-scan-ui]   ... and {len(ui_leaks) - 5} more")
            return False, ui_leaks
        else:
            print(f"[locale-scan-ui] ✅ PASSED for {profile_id} - no German in UI elements")
    else:
        # =======================================================================
        # QA-Gate v1: No UI markers = HARD FAIL (must have data-ui="1" markers)
        # =======================================================================
        print(f"[locale-scan-ui] ❌ FAILED for {profile_id} - no data-ui=\"1\" markers found (template must have UI markers)")
        return False, ["NO_UI_MARKERS_FOUND"]

    # ==========================================================================
    # CONTENT-SOFT SCAN (Score/Warn, No Fail)
    # ==========================================================================
    content_leaks = []
    scan_source = content_text_clean

    for de_string in DE_UI_STRINGS_EN_HARDFAIL:
        # Skip if already found in UI (to avoid double-counting)
        if de_string in scan_source:
            # Only count if NOT in UI text (to get pure content leaks)
            if has_ui_markers and de_string in ui_text:
                continue  # Already counted in UI
            content_leaks.append(de_string)

    content_score = len(content_leaks)

    if content_score > 0:
        # Scoring thresholds
        if content_score <= 10:
            level = "OK"
            emoji = "✅"
        elif content_score <= 50:
            level = "WARN"
            emoji = "⚠️"
        else:
            level = "WARN_HIGH"
            emoji = "⚠️"

        print(f"[locale-scan-content] {emoji} {level} for {profile_id} - score={content_score} German strings in content")
        if content_score <= 10:
            for leak in content_leaks:
                print(f"[locale-scan-content]   - {leak}")
        else:
            print(f"[locale-scan-content]   First 5: {content_leaks[:5]}")
    else:
        print(f"[locale-scan-content] ✅ CLEAN for {profile_id} - no German strings in content")

    # ==========================================================================
    # Multilingual v2: Section-level scan for detailed attribution
    # ==========================================================================
    try:
        from services.locale_rewriter import scan_html_sections, load_locale_budget

        v2_scan = scan_html_sections(html_text, expected_lang)
        budget = load_locale_budget(expected_lang)

        # v2 output format
        if v2_scan.total_hits > 0:
            v2_status = "✅ OK" if v2_scan.total_hits <= budget.content_max_hits else "⚠️ OVER_BUDGET"
            print(f"[locale-v2] {v2_status} for {profile_id} - score={v2_scan.total_hits} (budget={budget.content_max_hits})")
            if v2_scan.hits_by_section:
                top_sections = sorted(v2_scan.hits_by_section.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"[locale-v2]   top_sections: {dict(top_sections)}")
            if v2_scan.top_terms:
                print(f"[locale-v2]   top_terms: {v2_scan.top_terms[:5]}")
        else:
            print(f"[locale-v2] ✅ CLEAN for {profile_id} - score=0 (budget={budget.content_max_hits})")
    except Exception as e:
        print(f"[locale-v2] ⚠️ SKIPPED for {profile_id} - {e}")

    # ==========================================================================
    # FINAL RESULT: UI scan determines pass/fail
    # ==========================================================================
    # If we got here, UI scan passed (or was skipped for legacy templates)
    print(f"[locale-scan] ✅ PASSED for {profile_id} - UI check passed (content score={content_score})")
    return True, []


def scan_html_lang_attribute(html_text: str, expected_lang: str, profile_id: str) -> Tuple[bool, str]:
    """
    Verify <html lang="..."> attribute matches expected language.

    For EN profiles: <html lang="en"> must exist.
    <html lang="de"> or missing lang = FAIL.

    Args:
        html_text: Decoded HTML content
        expected_lang: Expected language ("en" or "de")
        profile_id: For logging

    Returns:
        (passed: bool, error_message: str if failed)
    """
    if expected_lang != "en":
        return True, ""  # Only strict check for EN profiles

    import re
    # Look for <html ... lang="..." ...> in first 500 chars
    html_head = html_text[:500]
    match = re.search(r'<html[^>]*\slang=["\']([^"\']+)["\']', html_head, re.IGNORECASE)

    if not match:
        print(f"[lang-attr] ❌ FAILED for {profile_id} - no lang attribute in <html> tag")
        return False, "Missing lang attribute in <html> tag"

    found_lang = match.group(1).lower()
    if found_lang != "en":
        print(f"[lang-attr] ❌ FAILED for {profile_id} - <html lang=\"{found_lang}\"> (expected: en)")
        return False, f"Wrong lang attribute: found '{found_lang}', expected 'en'"

    print(f"[lang-attr] ✅ PASSED for {profile_id} - <html lang=\"en\">")
    return True, ""


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
    expected_lang: str = "de",  # TEIL 3.1.2: Expected lang from profile
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

    # TEIL 3.1.2: Verify summary.lang matches expected profile lang
    summary_lang = parsed.get("lang", "de")
    print(f"[gate] summary.lang = {summary_lang}, expected = {expected_lang}")
    if expected_lang == "en" and summary_lang != "en":
        return False, f"summary.lang mismatch: expected 'en', got '{summary_lang}'"

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

    # TEIL 3.1.2: Explicit lang logging for EN profiles
    print(f"[submit] Payload lang: {lang}")
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

    # PLATIN+++ v5.4: Use lang from profile if available (overrides CLI default)
    profile_lang = profile_data.get("lang", lang)
    if profile_lang != lang:
        print(f"[profile] Using profile lang '{profile_lang}' (override CLI default '{lang}')")

    # 2. Submit briefing (with retry)
    briefing_id = submit_briefing(
        base_url, service_token, answers, profile_lang,
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
        # TEIL 3.1.2: Pass expected_lang for strict EN validation
        gate_passed, gate_error = run_summary_gate(
            base_url, service_token, briefing_id, profile_name,
            expected_lang=profile_lang,
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

    # 5.5 PLATIN+++ v5.4: Token scan on final HTML (Hard-Fail Gate)
    # This catches ANY forbidden tokens that escaped earlier scrubbing
    if run_gate and html_bytes:
        token_scan_passed, found_tokens = scan_html_for_forbidden_tokens(html_bytes, profile_name)
        if not token_scan_passed:
            return {
                "profile": profile_name,
                "briefing_id": briefing_id,
                "status": "gate_failed",
                "error": f"Forbidden tokens in final HTML: {found_tokens}",
            }

    # 5.55 QA-Gate v1: Prompt-leak scan on final HTML (Hard-Fail Gate)
    # Catches LLM assistant phrases that indicate task misunderstanding
    if run_gate and html_bytes:
        html_text_for_leak = html_bytes.decode("utf-8", errors="replace")
        leak_scan_passed, found_leaks = scan_html_for_prompt_leaks(html_text_for_leak, profile_name)
        if not leak_scan_passed:
            return {
                "profile": profile_name,
                "briefing_id": briefing_id,
                "status": "gate_failed",
                "error": f"Prompt-leak phrases in final HTML: {found_leaks[:3]}",
            }

    # 5.6 TEIL 3.1.1: Locale scan for EN profiles (German UI = Hard-Fail)
    if run_gate and html_bytes and profile_lang == "en":
        html_text = html_bytes.decode("utf-8", errors="replace")

        # A1: Check for German UI strings in EN report
        locale_passed, found_de_strings = scan_html_for_locale_leaks(html_text, profile_lang, profile_name)
        if not locale_passed:
            return {
                "profile": profile_name,
                "briefing_id": briefing_id,
                "status": "gate_failed",
                "error": f"German UI strings in EN report: {found_de_strings[:3]}",
            }

        # A2: Check <html lang="en"> attribute
        lang_attr_passed, lang_attr_error = scan_html_lang_attribute(html_text, profile_lang, profile_name)
        if not lang_attr_passed:
            return {
                "profile": profile_name,
                "briefing_id": briefing_id,
                "status": "gate_failed",
                "error": f"HTML lang attribute error: {lang_attr_error}",
            }

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

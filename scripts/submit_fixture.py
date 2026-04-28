#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/submit_fixture.py - Submit JSON fixtures for report generation

P1 Automation Script: Robust, CI-compatible fixture submission.

Usage:
    python scripts/submit_fixture.py fixtures/solo_freelancer.json
    python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll
    python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll --download-pdf artifacts/
    python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll --output-json

Exit Codes:
    0 = Success (done)
    2 = Usage error / fixture invalid
    3 = Authentication failed
    4 = Timeout waiting for completion
    5 = Server returned failed status

Environment Variables (with fallback chain):
    API_BASE_URL / BACKEND_BASE / SMOKE_BASE_URL (default: http://localhost:8000)
    SERVICE_TOKEN / SMOKE_AUTH_TOKEN (required for remote)
    POLL_INTERVAL (default: 2)
    POLL_TIMEOUT (default: 300)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(2)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# =============================================================================
# EXIT CODES (P1 Requirement)
# =============================================================================

EXIT_SUCCESS = 0
EXIT_USAGE_ERROR = 2
EXIT_AUTH_FAILED = 3
EXIT_TIMEOUT = 4
EXIT_SERVER_FAILED = 5

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_API_BASE = "http://localhost:8000"
DEFAULT_POLL_INTERVAL = 2  # seconds
DEFAULT_POLL_TIMEOUT = 300  # seconds (5 minutes)

# Terminal status values
TERMINAL_STATUSES = {"done", "failed", "error", "skipped"}

# Required fixture fields (minimal validation)
REQUIRED_FIXTURE_FIELDS = ["answers"]


# =============================================================================
# ENV HELPERS (P1: Fallback Chain)
# =============================================================================

def get_api_base_url(cli_value: Optional[str] = None) -> str:
    """
    Get API base URL with fallback chain.

    Priority: CLI arg > API_BASE_URL > BACKEND_BASE > SMOKE_BASE_URL > default
    """
    if cli_value:
        return cli_value

    # Fallback chain per P1 spec
    for env_var in ["API_BASE_URL", "BACKEND_BASE", "SMOKE_BASE_URL"]:
        value = os.getenv(env_var)
        if value:
            log.debug("Using %s from env: %s", env_var, value)
            return value

    return DEFAULT_API_BASE


def get_service_token(cli_value: Optional[str] = None) -> Optional[str]:
    """
    Get service token with fallback chain.

    Priority: CLI arg > SERVICE_TOKEN > SMOKE_AUTH_TOKEN
    """
    if cli_value:
        return cli_value

    # Fallback chain per P1 spec
    for env_var in ["SERVICE_TOKEN", "SMOKE_AUTH_TOKEN"]:
        value = os.getenv(env_var)
        if value:
            log.debug("Using %s from env", env_var)
            return value

    return None


def normalize_base_url(url: str) -> str:
    """
    Normalize the base URL for consistent API calls.

    - Removes trailing slashes
    - Ensures scheme is present (defaults to https for non-localhost)
    - Strips whitespace
    """
    url = url.strip().rstrip("/")

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        # Use http for localhost, https otherwise
        if "localhost" in url or "127.0.0.1" in url:
            url = f"http://{url}"
        else:
            url = f"https://{url}"

    return url


def mask_token(token: str | None) -> str:
    """Mask a token for safe logging (show first 4 chars only)."""
    if not token:
        return "(none)"
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}...****"


# =============================================================================
# FIXTURE LOADING & VALIDATION
# =============================================================================

def load_fixture(fixture_path: str) -> Dict[str, Any]:
    """
    Load and validate a fixture JSON file.

    Args:
        fixture_path: Path to the fixture JSON file

    Returns:
        Dict containing fixture data

    Raises:
        FileNotFoundError: If fixture doesn't exist
        ValueError: If fixture is invalid
    """
    path = Path(fixture_path)
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {fixture_path}: {e}")

    # Validate required fields
    for field in REQUIRED_FIXTURE_FIELDS:
        if field not in data:
            raise ValueError(f"Fixture missing required field: {field}")

    # Validate answers has company size or similar
    answers = data.get("answers", {})
    if not answers.get("unternehmensgroesse") and not answers.get("company_size"):
        log.warning("Fixture has no company size field - will use defaults")

    log.info("Loaded fixture: %s", data.get("fixture_id", path.stem))
    return data


# =============================================================================
# API INTERACTION
# =============================================================================

def get_api_client(base_url: str, service_token: Optional[str] = None) -> httpx.Client:
    """
    Create an HTTP client with authentication headers.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if service_token:
        # Use X-Service-Token header ONLY (not Authorization: Bearer)
        # Authorization: Bearer is for JWT user tokens, not service tokens
        headers["X-Service-Token"] = service_token
        log.info("Using service token authentication: %s", mask_token(service_token))

    return httpx.Client(
        base_url=base_url,
        headers=headers,
        timeout=60.0,
    )


def submit_briefing(
    client: httpx.Client,
    fixture: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Submit a briefing to the API.
    """
    payload = {
        "lang": fixture.get("lang", "de"),
        "answers": fixture.get("answers", {}),
        "queue_analysis": True,
    }

    log.info("Submitting briefing to /api/briefings/submit...")
    response = client.post("/api/briefings/submit", json=payload)
    response.raise_for_status()

    result = response.json()
    log.info("Briefing submitted: ID=%s, status=%s",
             result.get("briefing_id"), result.get("status"))

    return result


def get_briefing_status(
    client: httpx.Client,
    briefing_id: int,
) -> Dict[str, Any]:
    """
    Get the current status of a briefing.
    """
    response = client.get(f"/api/briefings/{briefing_id}")
    response.raise_for_status()
    return response.json()


def get_validation_summary(
    client: httpx.Client,
    briefing_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Get validation summary for a briefing (if available).
    """
    try:
        response = client.get(f"/api/briefings/{briefing_id}/validation")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None


def poll_until_done(
    client: httpx.Client,
    briefing_id: int,
    interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_POLL_TIMEOUT,
) -> Dict[str, Any]:
    """
    Poll briefing status until it reaches a terminal state.
    """
    start_time = time.time()
    last_status = None

    log.info("Polling briefing %d (interval=%ds, timeout=%ds)...",
             briefing_id, int(interval), int(timeout))

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(
                f"Polling timed out after {timeout}s. Last status: {last_status}"
            )

        status = get_briefing_status(client, briefing_id)
        current_status = status.get("status")

        if current_status != last_status:
            log.info("Status: %s (elapsed: %.1fs)", current_status, elapsed)
            last_status = current_status

        if current_status in TERMINAL_STATUSES:
            log.info("Terminal status reached: %s", current_status)
            return status

        time.sleep(interval)


def download_pdf(
    client: httpx.Client,
    briefing_id: int,
    output_dir: str,
    fixture_id: str,
) -> Optional[str]:
    """
    Download the PDF for a briefing.

    Args:
        client: HTTP client
        briefing_id: Briefing ID
        output_dir: Directory to save PDF
        fixture_id: Fixture ID for filename

    Returns:
        Path to downloaded PDF or None if failed
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_filename = f"{fixture_id}_{briefing_id}.pdf"
    pdf_path = output_path / pdf_filename

    log.info("Downloading PDF to %s...", pdf_path)

    try:
        response = client.get(f"/api/report/pdf/{briefing_id}")
        response.raise_for_status()

        with open(pdf_path, "wb") as f:
            f.write(response.content)

        log.info("PDF saved: %s (%d bytes)", pdf_path, len(response.content))
        return str(pdf_path)

    except Exception as e:
        log.error("Failed to download PDF: %s", e)
        return None


def download_html(
    client: httpx.Client,
    briefing_id: int,
    output_dir: str,
    fixture_id: str,
) -> Optional[str]:
    """
    Download the rendered HTML for a briefing.

    Returns:
        Path to downloaded HTML or None if failed
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    html_filename = f"{fixture_id}_{briefing_id}.html"
    html_path = output_path / html_filename

    log.info("Downloading HTML to %s...", html_path)

    try:
        response = client.get(f"/api/report/html/{briefing_id}")
        response.raise_for_status()

        with open(html_path, "wb") as f:
            f.write(response.content)

        log.info("HTML saved: %s (%d bytes)", html_path, len(response.content))
        return str(html_path)

    except Exception as e:
        log.error("Failed to download HTML: %s", e)
        return None


def get_report_url(briefing_id: int, base_url: str) -> str:
    """Generate the report URL for a briefing."""
    return f"{base_url}/api/report/html/{briefing_id}"


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Submit JSON fixtures for report generation (P1 Automation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit Codes:
  0 = Success (done)
  2 = Usage error / fixture invalid
  3 = Authentication failed
  4 = Timeout waiting for completion
  5 = Server returned failed status

Environment Variables (with fallback):
  API_BASE_URL / BACKEND_BASE / SMOKE_BASE_URL
  SERVICE_TOKEN / SMOKE_AUTH_TOKEN
""",
    )
    parser.add_argument(
        "fixture",
        help="Path to fixture JSON file",
    )
    parser.add_argument(
        "--poll",
        action="store_true",
        help="Poll until report is done",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help=f"Polling timeout in seconds (default: {DEFAULT_POLL_TIMEOUT})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help=f"Polling interval in seconds (default: {DEFAULT_POLL_INTERVAL})",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="API base URL (overrides env vars)",
    )
    parser.add_argument(
        "--service-token",
        default=None,
        help="Service token for authentication (overrides env vars)",
    )
    parser.add_argument(
        "--download-pdf",
        metavar="DIR",
        default=None,
        help="Download PDF to specified directory",
    )
    parser.add_argument(
        "--download-html",
        metavar="DIR",
        default=None,
        help="Download rendered HTML to specified directory",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON (for CI/scripting)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Configuration with fallback chains (P1)
    raw_base_url = get_api_base_url(args.base_url)
    base_url = normalize_base_url(raw_base_url)
    service_token = get_service_token(args.service_token)
    poll_interval = args.interval or int(os.getenv("POLL_INTERVAL", str(DEFAULT_POLL_INTERVAL)))
    poll_timeout = args.timeout or int(os.getenv("POLL_TIMEOUT", str(DEFAULT_POLL_TIMEOUT)))

    log.info("Configuration: base_url=%s, token=%s, poll=%ds/%ds",
             base_url, mask_token(service_token), poll_interval, poll_timeout)

    # Warn if no token for remote URL
    if not service_token and "localhost" not in base_url and "127.0.0.1" not in base_url:
        log.warning("No SERVICE_TOKEN set for remote URL - auth may fail")

    try:
        # Load and validate fixture
        try:
            fixture = load_fixture(args.fixture)
        except (FileNotFoundError, ValueError) as e:
            log.error("Fixture error: %s", e)
            return EXIT_USAGE_ERROR

        fixture_id = fixture.get("fixture_id", Path(args.fixture).stem)

        # Create client
        client = get_api_client(base_url, service_token)

        # Submit briefing
        try:
            submit_result = submit_briefing(client, fixture)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                log.error("Authentication failed: %s", e.response.text[:200])
                return EXIT_AUTH_FAILED
            raise

        briefing_id = submit_result.get("briefing_id")

        if not briefing_id:
            log.error("No briefing_id in response: %s", submit_result)
            return EXIT_SERVER_FAILED

        result: Dict[str, Any] = {
            "briefing_id": briefing_id,
            "fixture_id": fixture_id,
            "expected_variant": fixture.get("expected_variant"),
            "submit_status": submit_result.get("status"),
        }

        # Poll if requested
        if args.poll:
            try:
                final_status = poll_until_done(
                    client,
                    briefing_id,
                    interval=poll_interval,
                    timeout=poll_timeout,
                )
                result["final_status"] = final_status.get("status")
                result["done_at"] = final_status.get("done_at")

                if final_status.get("status") == "done":
                    result["report_url"] = get_report_url(briefing_id, base_url)
                    result["pdf_url"] = f"{base_url}/api/report/pdf/{briefing_id}"
                    log.info("Report ready: %s", result["report_url"])
                    log.info("PDF ready: %s", result["pdf_url"])

                    # Download PDF if requested
                    if args.download_pdf:
                        pdf_path = download_pdf(
                            client, briefing_id, args.download_pdf, fixture_id
                        )
                        if pdf_path:
                            result["pdf_local_path"] = pdf_path

                    # Download HTML if requested
                    if args.download_html:
                        html_path = download_html(
                            client, briefing_id, args.download_html, fixture_id
                        )
                        if html_path:
                            result["html_local_path"] = html_path

                    # Get validation summary if available
                    validation = get_validation_summary(client, briefing_id)
                    if validation:
                        result["validation"] = validation

                elif final_status.get("status") == "failed":
                    result["error"] = final_status.get("error")
                    log.error("Report generation failed: %s", result["error"])
                    if args.output_json:
                        print(json.dumps(result, indent=2))
                    return EXIT_SERVER_FAILED

            except TimeoutError as e:
                log.error(str(e))
                result["error"] = "timeout"
                if args.output_json:
                    print(json.dumps(result, indent=2))
                return EXIT_TIMEOUT

        # Output
        if args.output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*50}")
            print(f"Briefing ID: {briefing_id}")
            print(f"Fixture: {fixture_id}")
            if result.get("final_status"):
                print(f"Status: {result['final_status']}")
            if result.get("report_url"):
                print(f"Report URL: {result['report_url']}")
            if result.get("pdf_url"):
                print(f"PDF URL: {result['pdf_url']}")
            if result.get("pdf_local_path"):
                print(f"PDF Local: {result['pdf_local_path']}")
            if result.get("html_local_path"):
                print(f"HTML Local: {result['html_local_path']}")
            print(f"{'='*50}\n")

        return EXIT_SUCCESS

    except httpx.HTTPStatusError as e:
        if e.response.status_code in (401, 403):
            log.error("Authentication failed: %s", e.response.text[:200])
            return EXIT_AUTH_FAILED
        log.error("HTTP error: %s %s - %s",
                  e.response.status_code,
                  e.response.reason_phrase,
                  e.response.text[:200])
        return EXIT_SERVER_FAILED
    except Exception as e:
        log.exception("Unexpected error: %s", e)
        return EXIT_SERVER_FAILED


if __name__ == "__main__":
    sys.exit(main())

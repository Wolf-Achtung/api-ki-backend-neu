#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/submit_fixture.py - Submit JSON fixtures for report generation

Usage:
    python scripts/submit_fixture.py fixtures/solo_freelancer.json
    python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll
    python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll --timeout 300

This script:
1. Reads a JSON fixture file
2. Authenticates using service token or env vars
3. POSTs to /api/briefings/submit
4. Returns briefing_id
5. Optionally polls until report is done

Environment Variables:
    API_BASE_URL: Base URL of the API (default: http://localhost:8000)
    SERVICE_TOKEN: Service token for authentication (format: scope:secret)
    POLL_INTERVAL: Seconds between status checks (default: 2)
    POLL_TIMEOUT: Max seconds to wait for completion (default: 300)
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
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_API_BASE = "http://localhost:8000"
DEFAULT_POLL_INTERVAL = 2  # seconds
DEFAULT_POLL_TIMEOUT = 300  # seconds (5 minutes)

# Terminal status values
TERMINAL_STATUSES = {"done", "failed", "error", "skipped"}


def normalize_base_url(url: str) -> str:
    """
    Normalize the base URL for consistent API calls.

    - Removes trailing slashes
    - Ensures scheme is present (defaults to https for non-localhost)
    - Strips whitespace

    Args:
        url: Raw URL input

    Returns:
        Normalized URL string
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
# FIXTURE LOADING
# =============================================================================

def load_fixture(fixture_path: str) -> Dict[str, Any]:
    """
    Load a fixture JSON file.

    Args:
        fixture_path: Path to the fixture JSON file

    Returns:
        Dict containing fixture data

    Raises:
        FileNotFoundError: If fixture doesn't exist
        json.JSONDecodeError: If fixture is invalid JSON
    """
    path = Path(fixture_path)
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    log.info("Loaded fixture: %s", data.get("fixture_id", path.stem))
    return data


# =============================================================================
# API INTERACTION
# =============================================================================

def get_api_client(base_url: str, service_token: Optional[str] = None) -> httpx.Client:
    """
    Create an HTTP client with authentication headers.

    Args:
        base_url: API base URL
        service_token: Optional service token for auth

    Returns:
        Configured httpx.Client
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if service_token:
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

    Args:
        client: HTTP client
        fixture: Fixture data containing answers

    Returns:
        API response with briefing_id

    Raises:
        httpx.HTTPStatusError: If submission fails
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

    Args:
        client: HTTP client
        briefing_id: The briefing ID to check

    Returns:
        Status dict with status, timestamps, etc.
    """
    response = client.get(f"/api/briefings/{briefing_id}")
    response.raise_for_status()
    return response.json()


def poll_until_done(
    client: httpx.Client,
    briefing_id: int,
    interval: float = DEFAULT_POLL_INTERVAL,
    timeout: float = DEFAULT_POLL_TIMEOUT,
) -> Dict[str, Any]:
    """
    Poll briefing status until it reaches a terminal state.

    Args:
        client: HTTP client
        briefing_id: The briefing ID to poll
        interval: Seconds between polls
        timeout: Maximum seconds to wait

    Returns:
        Final status dict

    Raises:
        TimeoutError: If timeout exceeded
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


def get_report_url(briefing_id: int, base_url: str) -> str:
    """Generate the report URL for a briefing."""
    return f"{base_url}/api/report/html/{briefing_id}"


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Submit JSON fixtures for report generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
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
        help=f"API base URL (default: {DEFAULT_API_BASE})",
    )
    parser.add_argument(
        "--service-token",
        default=None,
        help="Service token for authentication",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Output result as JSON (for scripting)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Configuration from args or environment
    raw_base_url = args.base_url or os.getenv("API_BASE_URL", DEFAULT_API_BASE)
    base_url = normalize_base_url(raw_base_url)
    service_token = args.service_token or os.getenv("SERVICE_TOKEN")
    poll_interval = args.interval or int(os.getenv("POLL_INTERVAL", DEFAULT_POLL_INTERVAL))
    poll_timeout = args.timeout or int(os.getenv("POLL_TIMEOUT", DEFAULT_POLL_TIMEOUT))

    log.info("Configuration: base_url=%s, token=%s, poll=%ds/%ds",
             base_url, mask_token(service_token), poll_interval, poll_timeout)

    try:
        # Load fixture
        fixture = load_fixture(args.fixture)

        # Create client
        client = get_api_client(base_url, service_token)

        # Submit briefing
        submit_result = submit_briefing(client, fixture)
        briefing_id = submit_result.get("briefing_id")

        if not briefing_id:
            log.error("No briefing_id in response: %s", submit_result)
            return 1

        result = {
            "briefing_id": briefing_id,
            "fixture_id": fixture.get("fixture_id"),
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
                elif final_status.get("status") == "failed":
                    result["error"] = final_status.get("error")
                    log.error("Report generation failed: %s", result["error"])
                    return 1

            except TimeoutError as e:
                log.error(str(e))
                result["error"] = "timeout"
                return 1

        # Output
        if args.output_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nBriefing ID: {briefing_id}")
            if result.get("report_url"):
                print(f"Report URL: {result['report_url']}")
            if result.get("pdf_url"):
                print(f"PDF URL: {result['pdf_url']}")

        return 0

    except FileNotFoundError as e:
        log.error(str(e))
        return 1
    except httpx.HTTPStatusError as e:
        log.error("HTTP error: %s %s - %s",
                  e.response.status_code,
                  e.response.reason_phrase,
                  e.response.text[:200])
        return 1
    except Exception as e:
        log.exception("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIS-1162 smoke test — end-to-end verification of ``display_section_title``
against the live backend API.

Rationale
---------
DevTools SSE capture in Chrome is unreliable; Chrome discards closed
streams before the payload tab settles. This script drives the chat
endpoints directly via ``httpx`` and asserts the ``display_section_title``
contract in two places:

  Assert 1 (Phase 1)     display_section_title == current_section_name
  Assert 2 (Phase 2 B)   display_section_title == "KI-Strategie & Roadmap"

Deterministic exit code so CI can consume it later.

Usage
-----
    BASE_URL=https://api.ki-sicherheit.jetzt \\
    python scripts/smoke_test_kis_1162.py

Optional env vars:
    BASE_URL     Target backend (required, no default).
    TIMEOUT      Per-request timeout in seconds (default: 30).
    VERBOSE      "1" to print each SSE state_update payload.

Auth
----
The /api/chat/* endpoints accept unauthenticated sessions (user_id stays
None). No ``STRATEGY_ADMIN_KEY`` is needed for this smoke test — despite
the original request template mentioning ADMIN_KEY, it is only required
for /api/strategy/admin/* routes which we do not touch here.

Scope
-----
This is NOT a replacement for the unit / integration tests in
``tests/test_kis_1162_display_section_title.py``. Those cover the
projection logic in isolation; this script proves the field reaches the
wire in a real Phase-2-Block-B session.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

try:
    import httpx
except ImportError:
    sys.exit("httpx not installed — `pip install httpx` and retry.")


BASE_URL = os.getenv("BASE_URL", "").rstrip("/")
TIMEOUT = float(os.getenv("TIMEOUT", "30"))
VERBOSE = os.getenv("VERBOSE") == "1"


def log(msg: str) -> None:
    print(msg, flush=True)


def vlog(msg: str) -> None:
    if VERBOSE:
        print(f"  [v] {msg}", flush=True)


# ---------------------------------------------------------------------------
# SSE parsing
# ---------------------------------------------------------------------------

def parse_sse_stream(response: httpx.Response) -> list[dict[str, Any]]:
    """Split an SSE byte stream into ``[{event, data}, …]``."""
    events: list[dict[str, Any]] = []
    event_name: str | None = None
    data_lines: list[str] = []

    for raw_line in response.iter_lines():
        line = raw_line.rstrip("\r")
        if not line:
            if event_name is not None:
                data_str = "\n".join(data_lines)
                try:
                    parsed: Any = json.loads(data_str) if data_str.strip() else {}
                except json.JSONDecodeError:
                    parsed = {"_raw": data_str}
                events.append({"event": event_name, "data": parsed})
            event_name = None
            data_lines = []
            continue
        if line.startswith("event:"):
            event_name = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())

    return events


def latest_state(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the last state_update payload in the stream, or None."""
    for ev in reversed(events):
        if ev.get("event") == "state_update":
            data = ev.get("data") or {}
            if isinstance(data, dict):
                return data
    return None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def chat_start(client: httpx.Client) -> tuple[str, dict[str, Any]]:
    r = client.post(
        f"{BASE_URL}/api/chat/start",
        json={"report_type": "r1", "lang": "de", "consent_report": True},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    payload = r.json()
    return payload["session_id"], payload["state"]


def chat_message(
    client: httpx.Client,
    session_id: str,
    message: str = "",
    qr_field: str | None = None,
    qr_value: str | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"session_id": session_id, "message": message}
    if qr_field:
        body["quick_reply_field"] = qr_field
        body["quick_reply_value"] = qr_value or ""
    with client.stream(
        "POST",
        f"{BASE_URL}/api/chat/message",
        json=body,
        timeout=TIMEOUT,
    ) as r:
        r.raise_for_status()
        events = parse_sse_stream(r)
    state = latest_state(events)
    if state is None:
        raise RuntimeError(
            f"No state_update in SSE stream "
            f"(qr={qr_field}={qr_value!r}, msg={message[:40]!r}). "
            f"Events: {[e.get('event') for e in events]}"
        )
    return state


def describe(label: str, state: dict[str, Any]) -> None:
    log(
        f"  → {label:<32} | phase={state.get('conversation_phase')!s:<12} "
        f"| block={state.get('current_block')!s:<4} "
        f"| display={state.get('display_section_title')!r}"
    )
    vlog(json.dumps(state, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

def assert_equal(label: str, got: Any, expected: Any) -> None:
    if got != expected:
        log(f"❌ {label}: expected {expected!r}, got {got!r}")
        sys.exit(2)
    log(f"✅ {label}: {got!r}")


def assert_present(label: str, got: Any) -> None:
    if got is None or got == "":
        log(f"❌ {label}: expected non-empty, got {got!r}")
        sys.exit(2)


# ---------------------------------------------------------------------------
# Main flow
# ---------------------------------------------------------------------------

def main() -> int:
    if not BASE_URL:
        log("❌ BASE_URL env var is required (e.g. https://api.ki-sicherheit.jetzt).")
        return 64  # EX_USAGE
    log(f"KIS-1162 smoke test — target {BASE_URL}")
    start_t = time.time()

    with httpx.Client() as client:
        # --- 0. Start session ---
        session_id, initial_state = chat_start(client)
        log(f"✓ Session started: {session_id}")
        describe("start", initial_state)

        # --- Assert 1: Phase 1 falls back to current_section_name ---
        assert_present("initial display_section_title present",
                       initial_state.get("display_section_title"))
        assert_equal(
            "Assert 1 (Phase 1): display_section_title == current_section_name",
            initial_state.get("display_section_title"),
            initial_state.get("current_section_name"),
        )

        # --- 1. Phase 1a QR sequence ---
        p1a_steps = [
            ("branche", "beratung"),
            ("unternehmensgroesse", "2–10"),
            ("country", "DE"),
            ("bundesland", "berlin"),
            ("investitionsbudget", "10000_50000"),
        ]
        state = initial_state
        for field, value in p1a_steps:
            state = chat_message(client, session_id, qr_field=field, qr_value=value)
            describe(f"qr {field}={value}", state)

        # --- 2. Phase 1b: one substantive answer should hit most fields ---
        phase_1b_prose = (
            "Wir sind eine Beratungsfirma für KMU mit Fokus auf "
            "Digitalstrategie. KI-Kompetenz hoch, Digitalisierungsgrad "
            "etwa 8 von 10. Ziele: Effizienz steigern, Prozesse "
            "automatisieren, Marktreichweite ausbauen."
        )
        state = chat_message(client, session_id, message=phase_1b_prose)
        describe("phase_1b prose", state)

        # Some Phase 1b sub-fields (digitalisierungsgrad / ki_kompetenz) may
        # still surface as QR prompts. Walk through up to 4 structured prompts;
        # after that the Phase 1b safeguard force-promotes to checkpoint.
        fallback_qr = {
            "digitalisierungsgrad": "7",
            "ki_kompetenz": "hoch",
            "ki_ziele": "effizienz,automatisierung,marktreichweite",
        }
        extra_prose = [
            "Effizienzsteigerung, Prozessautomatisierung, Reichweite.",
            "Strategische KI-Beratung für B2B, Angebots-Automatisierung.",
            "Kundenreichweite erhöhen, Reporting effizienter gestalten.",
            "Analysen beschleunigen, Vorschläge schneller erstellen.",
        ]
        prose_iter = iter(extra_prose)
        safety = 0
        while state.get("conversation_phase") not in ("checkpoint", "phase_2",
                                                       "summary"):
            safety += 1
            if safety > 8:
                log(f"❌ Did not reach checkpoint after {safety} turns. "
                    f"Last phase={state.get('conversation_phase')}.")
                return 3
            next_fields = state.get("next_fields") or []
            nf = next_fields[0] if next_fields else None
            if nf and nf in fallback_qr:
                state = chat_message(client, session_id,
                                     qr_field=nf, qr_value=fallback_qr[nf])
                describe(f"qr {nf}={fallback_qr[nf]}", state)
            else:
                msg = next(prose_iter, "Weitere Details sind oben bereits beschrieben.")
                state = chat_message(client, session_id, message=msg)
                describe(f"prose ({safety})", state)

        # --- 3. Checkpoint: pick Block B directly ---
        if state.get("conversation_phase") != "checkpoint":
            log(f"❌ Expected checkpoint phase before block selection, "
                f"got {state.get('conversation_phase')!r}.")
            return 4
        state = chat_message(client, session_id,
                             qr_field="__checkpoint__", qr_value="B")
        describe("checkpoint=B", state)

        # --- Assert 2: Phase 2 Block B, display_section_title == block_label ---
        assert_equal(
            "Assert 2a: conversation_phase",
            state.get("conversation_phase"), "phase_2",
        )
        assert_equal(
            "Assert 2b: current_block",
            state.get("current_block"), "B",
        )
        assert_equal(
            "Assert 2c: block_label",
            state.get("block_label"), "KI-Strategie & Roadmap",
        )
        assert_equal(
            "Assert 2d: display_section_title",
            state.get("display_section_title"), "KI-Strategie & Roadmap",
        )

        # Diagnostic: does current_section_name still lag? (documents Bug 5)
        csn = state.get("current_section_name")
        if csn != "KI-Strategie & Roadmap":
            log(
                f"ℹ️  current_section_name still lags: {csn!r} — exactly "
                f"the Bug 5 scenario. display_section_title overrides correctly."
            )

    dur = time.time() - start_t
    log(f"\n🎯 Bug 5 verified in {dur:.1f}s — display_section_title is the "
        f"single source of truth for the chat UI section header.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except httpx.HTTPStatusError as exc:
        log(f"❌ HTTP {exc.response.status_code} on "
            f"{exc.request.method} {exc.request.url}:\n{exc.response.text[:400]}")
        sys.exit(1)
    except httpx.RequestError as exc:
        log(f"❌ Network error: {exc}")
        sys.exit(1)
    except AssertionError as exc:
        log(f"❌ Assertion failed: {exc}")
        sys.exit(2)

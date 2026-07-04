# Template rebuild trigger: 2026-01-01 16:30 - Railway cache bust for Pages 2,3,4 redesign
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Briefings Worker Process (DB-Backed Queue)

Polls the database for briefings with status='accepted' and processes them
using the full analysis pipeline (LLM + PDF + Email).

Features:
- Atomic job claiming with SELECT ... FOR UPDATE SKIP LOCKED (race-safe)
- Graceful shutdown on SIGINT/SIGTERM
- Configurable poll interval and worker ID
- Automatic status updates (accepted -> processing -> done/failed)

Usage:
    python -m workers.briefings_worker

Environment Variables:
    WORKER_POLL_INTERVAL: Seconds between polls (default: 2)
    WORKER_ID: Unique worker identifier (default: auto-generated)
    LOG_LEVEL: Logging level (default: INFO)
"""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import SessionLocal, is_sqlite
from models import Briefing

# Configure logging
log_level = (os.getenv("LOG_LEVEL") or "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("briefings-worker")

# Worker configuration
POLL_INTERVAL = float(os.getenv("WORKER_POLL_INTERVAL", "2"))
WORKER_ID = os.getenv("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")

# Stale briefing recovery: briefings stuck in "processing" for longer than this are reset
# Default: 10 minutes (600 seconds).
# KIS-1247: Lange Reports (KMU: 11-15 Min) sind KEIN Stale-Fall mehr — der
# Worker sendet waehrend der Verarbeitung einen processing_at-Heartbeat
# (alle HEARTBEAT_INTERVAL_SECONDS). Stale heisst jetzt: 10 Min OHNE
# Heartbeat = Worker wirklich tot (Lauf 1121: lebender Worker wurde fuer
# tot erklaert, Briefing doppelt verarbeitet, Status-Race -> "failed").
STALE_BRIEFING_TIMEOUT_SECONDS = int(os.getenv("STALE_BRIEFING_TIMEOUT", "600"))
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "60"))
# How often to check for stale briefings (in poll cycles)
STALE_CHECK_INTERVAL_CYCLES = 15  # Every ~30 seconds at default poll interval

# Graceful shutdown flag
_shutdown_requested = False


def _handle_shutdown(signum, frame):
    """Signal handler for graceful shutdown."""
    global _shutdown_requested
    log.info("Shutdown signal received (sig=%s), finishing current job...", signum)
    _shutdown_requested = True


def recover_stale_briefings(db: Session) -> int:
    """
    Recover briefings stuck in 'processing' status for too long.

    This handles cases where a worker dies mid-processing (e.g., container restart,
    OOM kill, crash). Briefings older than STALE_BRIEFING_TIMEOUT_SECONDS are
    reset to 'accepted' so they can be re-processed.

    Args:
        db: SQLAlchemy session

    Returns:
        Number of briefings recovered
    """
    from datetime import timedelta

    cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=STALE_BRIEFING_TIMEOUT_SECONDS)

    try:
        if is_sqlite:
            # SQLite: Simple update
            stale_briefings = db.query(Briefing).filter(
                Briefing.status == "processing",
                Briefing.processing_at < cutoff_time
            ).all()

            count = 0
            for briefing in stale_briefings:
                log.warning(
                    "🔄 Recovering stale briefing %s (stuck since %s, worker=%s)",
                    briefing.id, briefing.processing_at, briefing.worker_id
                )
                briefing.status = "accepted"
                briefing.processing_at = None
                briefing.worker_id = None
                count += 1

            if count > 0:
                db.commit()
            return count

        # PostgreSQL: Use raw SQL for efficiency
        result = db.execute(
            text("""
                UPDATE briefings
                SET status = 'accepted',
                    processing_at = NULL,
                    worker_id = NULL
                WHERE status = 'processing'
                  AND processing_at < :cutoff
                RETURNING id, processing_at, worker_id
            """),
            {"cutoff": cutoff_time}
        ).fetchall()

        for row in result:
            log.warning(
                "🔄 Recovered stale briefing %s (stuck since %s, worker=%s)",
                row[0], row[1], row[2]
            )

        if result:
            db.commit()

        return len(result)

    except Exception as e:
        log.error("Error recovering stale briefings: %s", e)
        db.rollback()
        return 0


def claim_next_briefing(db: Session) -> Optional[Briefing]:
    """
    Atomically claim the next pending briefing using FOR UPDATE SKIP LOCKED.

    This ensures that multiple workers can safely compete for jobs without
    double-processing. PostgreSQL's SKIP LOCKED allows non-blocking claims.

    PLATIN+++ v5.4: Now accepts both 'accepted' AND 'queued' status for robustness.

    Args:
        db: SQLAlchemy session

    Returns:
        Briefing object if claimed, None if no jobs available
    """
    if is_sqlite:
        # SQLite fallback: simple SELECT (not race-safe, but works for dev/test)
        # PLATIN+++ v5.4: Accept both 'accepted' and 'queued'
        briefing = db.query(Briefing).filter(
            Briefing.status.in_(["accepted", "queued"])
        ).order_by(
            Briefing.created_at.asc()  # FIFO by creation time
        ).first()

        if briefing:
            briefing.status = "processing"
            briefing.processing_at = datetime.now(timezone.utc)
            briefing.worker_id = WORKER_ID
            db.commit()
            return briefing  # type: ignore[no-any-return]
        return None

    # PostgreSQL: Use FOR UPDATE SKIP LOCKED for race-safe claiming
    try:
        # Raw SQL for FOR UPDATE SKIP LOCKED (SQLAlchemy 2.x compatible)
        # PLATIN+++ v5.4: Accept both 'accepted' and 'queued'
        result = db.execute(
            text("""
                SELECT id FROM briefings
                WHERE status IN ('accepted', 'queued')
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)
        ).fetchone()

        if not result:
            return None

        briefing_id = result[0]
        briefing = db.get(Briefing, briefing_id)

        if briefing:
            briefing.status = "processing"
            briefing.processing_at = datetime.now(timezone.utc)
            briefing.worker_id = WORKER_ID
            db.commit()
            log.info("Claimed briefing %s for processing", briefing_id)
            return briefing  # type: ignore[no-any-return]

        return None

    except Exception as e:
        log.error("Error claiming briefing: %s", e)
        db.rollback()
        return None


def _send_admin_error_alert(briefing: Briefing, error_msg: str, run_id: str) -> None:
    """Send admin email alert when a briefing pipeline fails."""
    try:
        from gpt_analyze import _send_email_via_resend, _admin_recipients, _mask_email
    except ImportError:
        log.warning("[%s] Cannot import email helpers for admin alert", run_id)
        return

    if os.getenv("DISABLE_EMAILS", "").lower() in ("1", "true", "yes", "on"):
        return

    answers = getattr(briefing, "answers", {}) or {}
    company_size = answers.get("unternehmensgroesse", "unknown")
    user_email = ""
    if briefing.user_id and briefing.user:
        user_email = getattr(briefing.user, "email", "") or ""

    subject = f"Report-Fehler: Briefing #{briefing.id}"
    body = f"""
    <div style="font-family:sans-serif;max-width:600px;">
        <h2 style="color:#dc2626;">Report-Pipeline Fehler</h2>
        <table style="border-collapse:collapse;width:100%;">
            <tr><td style="padding:6px;font-weight:bold;">Briefing-ID:</td><td style="padding:6px;">{briefing.id}</td></tr>
            <tr><td style="padding:6px;font-weight:bold;">Segment:</td><td style="padding:6px;">{company_size}</td></tr>
            <tr><td style="padding:6px;font-weight:bold;">User-Email:</td><td style="padding:6px;">{user_email or 'N/A'}</td></tr>
            <tr><td style="padding:6px;font-weight:bold;">Run-ID:</td><td style="padding:6px;">{run_id}</td></tr>
            <tr><td style="padding:6px;font-weight:bold;">Zeitpunkt:</td><td style="padding:6px;">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
        </table>
        <div style="margin-top:16px;padding:12px;background:#fef2f2;border-radius:8px;border:1px solid #fecaca;">
            <strong>Fehler:</strong><br>
            <pre style="white-space:pre-wrap;font-size:12px;">{error_msg[:2000]}</pre>
        </div>
    </div>
    """

    for addr in _admin_recipients():
        ok, err = _send_email_via_resend(addr, subject, body)
        if ok:
            log.info("[%s] Admin error alert sent to %s", run_id, _mask_email(addr))
        else:
            log.warning("[%s] Admin error alert failed for %s: %s", run_id, _mask_email(addr), err)


def _start_processing_heartbeat(briefing_id: int) -> threading.Event:
    """KIS-1247: Haelt processing_at frisch, solange dieser Worker am Briefing
    arbeitet. Ohne Heartbeat erklaerte recover_stale_briefings einen lebenden
    Worker nach STALE_BRIEFING_TIMEOUT fuer tot und gab das Briefing erneut
    frei (Doppel-Verarbeitung + Status-Race, Lauf 1121)."""
    stop = threading.Event()

    def _beat() -> None:
        while not stop.wait(HEARTBEAT_INTERVAL_SECONDS):
            try:
                with SessionLocal() as hb_db:
                    hb_db.execute(
                        text(
                            "UPDATE briefings SET processing_at = :now "
                            "WHERE id = :bid AND status = 'processing'"
                        ),
                        {"now": datetime.now(timezone.utc), "bid": briefing_id},
                    )
                    hb_db.commit()
            except Exception as hb_err:  # pragma: no cover - defensiv
                log.warning("Heartbeat fuer Briefing %s fehlgeschlagen: %s", briefing_id, hb_err)

    threading.Thread(target=_beat, daemon=True, name=f"hb-briefing-{briefing_id}").start()
    return stop


def process_briefing(db: Session, briefing: Briefing) -> bool:
    """
    Process a single briefing through the full analysis pipeline.

    Args:
        db: SQLAlchemy session
        briefing: Briefing object to process

    Returns:
        True if successful, False if failed
    """
    run_id = f"{WORKER_ID}-{briefing.id}-{uuid.uuid4().hex[:4]}"
    log.info("[%s] Processing briefing %s...", run_id, briefing.id)

    _hb_stop = _start_processing_heartbeat(briefing.id)
    try:
        # Import here to avoid circular imports and ensure fresh module state
        from gpt_analyze import run_briefing_pipeline

        # Get user email if available (for notifications)
        user_email = None
        if briefing.user_id and briefing.user:
            user_email = getattr(briefing.user, "email", None)

        # Execute the full pipeline
        run_briefing_pipeline(db, briefing.id, email=user_email, run_id=run_id)

        # Update briefing status to done
        briefing.status = "done"
        briefing.done_at = datetime.now(timezone.utc)
        briefing.error = None
        db.commit()

        log.info("[%s] ✅ Briefing %s completed successfully", run_id, briefing.id)
        return True

    except Exception as e:
        log.error("[%s] ❌ Briefing %s failed: %s", run_id, briefing.id, e, exc_info=True)

        # Update briefing status to failed
        try:
            # KIS-1247: Race-Guard — hat ein anderer (oder frueherer) Lauf das
            # Briefing bereits fertiggestellt, darf "failed" das "done" nicht
            # ueberschreiben. Der Kunde haette sonst einen Report per Mail,
            # aber eine Fehlerseite im Browser.
            db.rollback()
            db.refresh(briefing)
            if briefing.status == "done":
                log.warning(
                    "[%s] Briefing %s ist bereits 'done' — Fehler dieses Laufs "
                    "wird NICHT als failed gespeichert (Doppel-Lauf-Race).",
                    run_id, briefing.id,
                )
                return False
            briefing.status = "failed"
            briefing.done_at = datetime.now(timezone.utc)
            briefing.error = str(e)[:8000]  # Truncate error message
            db.commit()
        except Exception as db_err:
            log.error("[%s] Failed to update briefing status: %s", run_id, db_err)
            db.rollback()

        # Send admin error notification (fire-and-forget)
        try:
            _send_admin_error_alert(briefing, str(e), run_id)
        except Exception as alert_err:
            log.warning("[%s] Admin error alert failed: %s", run_id, alert_err)

        return False

    finally:
        _hb_stop.set()


def run_worker_loop():
    """Main worker loop: poll DB, claim jobs, process, repeat."""
    log.info("=" * 60)
    log.info("Briefings Worker starting...")
    log.info("Worker ID: %s", WORKER_ID)
    log.info("Poll interval: %s seconds", POLL_INTERVAL)
    log.info("Stale briefing timeout: %s seconds", STALE_BRIEFING_TIMEOUT_SECONDS)
    log.info("Database: %s", "SQLite" if is_sqlite else "PostgreSQL")
    log.info("=" * 60)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _handle_shutdown)
    signal.signal(signal.SIGTERM, _handle_shutdown)

    jobs_processed = 0
    jobs_failed = 0
    jobs_recovered = 0
    poll_cycle = 0

    while not _shutdown_requested:
        db = SessionLocal()
        try:
            poll_cycle += 1

            # Periodically check for stale briefings (not every cycle to reduce DB load)
            if poll_cycle % STALE_CHECK_INTERVAL_CYCLES == 0:
                recovered = recover_stale_briefings(db)
                if recovered > 0:
                    jobs_recovered += recovered
                    log.info("🔄 Recovered %s stale briefing(s)", recovered)

            # Try to claim a job
            briefing = claim_next_briefing(db)

            if briefing:
                success = process_briefing(db, briefing)
                if success:
                    jobs_processed += 1
                else:
                    jobs_failed += 1
            else:
                # No jobs available, sleep before next poll
                time.sleep(POLL_INTERVAL)

        except Exception as e:
            log.error("Worker loop error: %s", e, exc_info=True)
            time.sleep(POLL_INTERVAL)

        finally:
            db.close()

    # Shutdown summary
    log.info("=" * 60)
    log.info("Worker shutdown complete")
    log.info("Jobs processed: %s", jobs_processed)
    log.info("Jobs failed: %s", jobs_failed)
    log.info("Jobs recovered: %s", jobs_recovered)
    log.info("=" * 60)


def main():
    """Entry point for the worker process."""
    try:
        run_worker_loop()
    except KeyboardInterrupt:
        log.info("Worker interrupted by user")
    except Exception as e:
        log.error("Worker crashed: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

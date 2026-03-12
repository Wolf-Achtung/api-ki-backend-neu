# -*- coding: utf-8 -*-
"""
Routes for Report 3: KI-Strategiebericht.

Endpoints:
- POST /api/strategy/questions/{briefing_id} — Save strategy questions
- GET  /api/strategy/questions/{briefing_id} — Get saved questions
- GET  /api/strategy/status/{briefing_id}    — Report status
- POST /api/strategy/generate/{briefing_id}  — Start report generation
- GET  /api/strategy/pdf/{briefing_id}       — PDF download
- GET  /api/strategy/html/{briefing_id}      — HTML preview
- POST /api/strategy/admin/unlock/{briefing_id} — Beta unlock
- POST /api/strategy/admin/reset-status/{briefing_id} — Reset stuck generation
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from routes._bootstrap import get_db
from models import Briefing, Analysis, StrategyQuestion, StrategyReport

log = logging.getLogger(__name__)

router = APIRouter(prefix="/strategy", tags=["strategy"])


# =============================================================================
# SCHEMAS
# =============================================================================

class StrategyQuestionsCreate(BaseModel):
    """Zusatzfragen für den KI-Strategiebericht (S1-S10)."""
    # Pflicht
    s1_budget: str = Field(..., description="Investitionsbudget 12 Monate")
    s2_zeitrahmen: str = Field(..., description="Gewünschter Umsetzungszeitraum")
    s3_prioritaeten: List[str] = Field(..., max_length=3, description="Top-3 Prioritäten")
    s4_engpass: str = Field(..., description="Wichtigster Engpass")
    s5_software: Optional[str] = Field(None, max_length=200, description="Bestehende Software")
    s6_foerderinteresse: str = Field(..., description="Interesse an Fördermitteln")
    s7_entscheidung: str = Field(..., description="Entscheidungshorizont")
    # Optional
    s8_erfahrung: Optional[str] = None
    s9_ansatz: Optional[str] = None
    s10_datenschutz: Optional[str] = None


class StrategyQuestionsResponse(BaseModel):
    briefing_id: int
    status: str
    message: str


# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

VALID_BUDGET = [
    "Noch unklar",
    "Unter 5.000€",
    "5.000–15.000€",
    "15.000–50.000€",
    "Über 50.000€",
]

VALID_ZEITRAHMEN = [
    "Sofort (1-3 Monate)",
    "Kurzfristig (3-6 Monate)",
    "Mittelfristig (6-12 Monate)",
    "Langfristig (12-18 Monate)",
]

VALID_PRIORITAETEN = [
    "Kosten senken",
    "Umsatz steigern",
    "Qualität verbessern",
    "Geschwindigkeit erhöhen",
    "Compliance sichern",
    "Neue Geschäftsfelder",
    "Fachkräftemangel kompensieren",
    "Kundenerlebnis verbessern",
]

VALID_ENGPASS = [
    "Zu wenig Know-how",
    "Kein Budget",
    "Fehlende Daten",
    "Widerstand im Team",
    "Regulatorische Unsicherheit",
    "Kein klarer Use Case",
    "Andere",
]

VALID_FOERDERINTERESSE = [
    "Ja, dringend",
    "Ja, wenn passend",
    "Nein, eigenes Budget",
    "Weiß nicht",
]

VALID_ENTSCHEIDUNG = [
    "Entscheide allein",
    "Brauche Vorlage für Geschäftsleitung",
    "Muss Gesellschafter überzeugen",
    "Muss Aufsichtsrat/Beirat informieren",
]

VALID_ERFAHRUNG = [
    "Noch keine",
    "Experimentiert",
    "Erste Tools im Einsatz",
    "Fortgeschritten",
]

VALID_ANSATZ = [
    "Cloud-SaaS",
    "On-Premise",
    "Hybrid",
    "Egal",
]

VALID_DATENSCHUTZ = [
    "Hoch",
    "Mittel",
    "Niedrig",
]


def _validate_questions(q: StrategyQuestionsCreate) -> Optional[str]:
    """Validate question values against allowed lists. Returns error message or None."""
    if q.s1_budget not in VALID_BUDGET:
        return f"Ungültiger Wert für s1_budget: {q.s1_budget}"
    if q.s2_zeitrahmen not in VALID_ZEITRAHMEN:
        return f"Ungültiger Wert für s2_zeitrahmen: {q.s2_zeitrahmen}"
    if not q.s3_prioritaeten or len(q.s3_prioritaeten) > 3:
        return "s3_prioritaeten muss 1-3 Einträge enthalten"
    for p in q.s3_prioritaeten:
        if p not in VALID_PRIORITAETEN:
            return f"Ungültiger Wert in s3_prioritaeten: {p}"
    if q.s4_engpass not in VALID_ENGPASS:
        return f"Ungültiger Wert für s4_engpass: {q.s4_engpass}"
    if q.s6_foerderinteresse not in VALID_FOERDERINTERESSE:
        return f"Ungültiger Wert für s6_foerderinteresse: {q.s6_foerderinteresse}"
    if q.s7_entscheidung not in VALID_ENTSCHEIDUNG:
        return f"Ungültiger Wert für s7_entscheidung: {q.s7_entscheidung}"
    # Optional fields
    if q.s8_erfahrung is not None and q.s8_erfahrung not in VALID_ERFAHRUNG:
        return f"Ungültiger Wert für s8_erfahrung: {q.s8_erfahrung}"
    if q.s9_ansatz is not None and q.s9_ansatz not in VALID_ANSATZ:
        return f"Ungültiger Wert für s9_ansatz: {q.s9_ansatz}"
    if q.s10_datenschutz is not None and q.s10_datenschutz not in VALID_DATENSCHUTZ:
        return f"Ungültiger Wert für s10_datenschutz: {q.s10_datenschutz}"
    return None


# =============================================================================
# ENDPOINTS: QUESTIONS
# =============================================================================

@router.post("/questions/{briefing_id}", response_model=StrategyQuestionsResponse)
async def save_strategy_questions(
    briefing_id: int,
    questions: StrategyQuestionsCreate,
    db: Session = Depends(get_db),
):
    """
    Speichert die Zusatzfragen für Report 3.
    Voraussetzung: briefing_id existiert und Report 1 ist abgeschlossen.
    """
    # 1. Prüfe ob Briefing existiert
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    # 2. Prüfe ob Report 1 abgeschlossen ist (briefing status = 'done')
    if briefing.status != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Report 1 muss zuerst abgeschlossen sein (aktueller Status: {briefing.status})"
        )

    # 3. Validiere Eingaben
    validation_error = _validate_questions(questions)
    if validation_error:
        raise HTTPException(status_code=422, detail=validation_error)

    # 4. Speichere/Update in strategy_questions Tabelle
    existing = db.query(StrategyQuestion).filter(
        StrategyQuestion.briefing_id == briefing_id
    ).first()

    if existing:
        # Update
        existing.s1_budget = questions.s1_budget
        existing.s2_zeitrahmen = questions.s2_zeitrahmen
        existing.s3_prioritaeten = questions.s3_prioritaeten
        existing.s4_engpass = questions.s4_engpass
        existing.s5_software = questions.s5_software
        existing.s6_foerderinteresse = questions.s6_foerderinteresse
        existing.s7_entscheidung = questions.s7_entscheidung
        existing.s8_erfahrung = questions.s8_erfahrung
        existing.s9_ansatz = questions.s9_ansatz
        existing.s10_datenschutz = questions.s10_datenschutz
        log.info("[Strategy] Updated questions for briefing_id=%d", briefing_id)
    else:
        # Insert
        sq = StrategyQuestion(
            briefing_id=briefing_id,
            s1_budget=questions.s1_budget,
            s2_zeitrahmen=questions.s2_zeitrahmen,
            s3_prioritaeten=questions.s3_prioritaeten,
            s4_engpass=questions.s4_engpass,
            s5_software=questions.s5_software,
            s6_foerderinteresse=questions.s6_foerderinteresse,
            s7_entscheidung=questions.s7_entscheidung,
            s8_erfahrung=questions.s8_erfahrung,
            s9_ansatz=questions.s9_ansatz,
            s10_datenschutz=questions.s10_datenschutz,
        )
        db.add(sq)
        log.info("[Strategy] Saved new questions for briefing_id=%d", briefing_id)

    # 5. Erstelle Eintrag in strategy_reports falls nicht vorhanden
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        sr = StrategyReport(
            briefing_id=briefing_id,
            status="pending",
        )
        db.add(sr)
        log.info("[Strategy] Created strategy_reports entry for briefing_id=%d", briefing_id)

    db.commit()

    return StrategyQuestionsResponse(
        briefing_id=briefing_id,
        status="saved",
        message="Zusatzfragen gespeichert",
    )


@router.get("/questions/{briefing_id}")
async def get_strategy_questions(
    briefing_id: int,
    db: Session = Depends(get_db),
):
    """Gibt die gespeicherten Zusatzfragen zurück."""
    sq = db.query(StrategyQuestion).filter(
        StrategyQuestion.briefing_id == briefing_id
    ).first()
    if not sq:
        raise HTTPException(status_code=404, detail="Keine Zusatzfragen für dieses Briefing gefunden")
    return sq.to_dict()


# =============================================================================
# ENDPOINTS: STATUS
# =============================================================================

@router.get("/status/{briefing_id}")
async def get_strategy_status(
    briefing_id: int,
    db: Session = Depends(get_db),
):
    """
    Status des Strategieberichts.
    Returns: status, pdf_available, email_sent, duration info.
    """
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Kein Strategiebericht für dieses Briefing gefunden")
    return sr.to_dict()


# =============================================================================
# ENDPOINTS: GENERATE (Task 7)
# =============================================================================

@router.post("/generate/{briefing_id}")
async def generate_strategy_report_endpoint(
    briefing_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Startet die Generierung des Strategieberichts.
    Läuft als Background-Task.

    Voraussetzungen:
    - Briefing existiert
    - Report 1 abgeschlossen
    - Zusatzfragen gespeichert
    - Payment OK (oder Beta-Flag)
    """
    # 1. Briefing existiert?
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    # 2. Report 1 abgeschlossen?
    if briefing.status != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Report 1 muss zuerst abgeschlossen sein (aktueller Status: {briefing.status})"
        )

    # 3. Zusatzfragen gespeichert?
    sq = db.query(StrategyQuestion).filter(
        StrategyQuestion.briefing_id == briefing_id
    ).first()
    if not sq:
        raise HTTPException(status_code=400, detail="Zusatzfragen müssen zuerst gespeichert werden")

    # 4. Strategy report entry exists?
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        sr = StrategyReport(briefing_id=briefing_id, status="pending")
        db.add(sr)
        db.commit()
        db.refresh(sr)

    # 5. Payment check (Beta or paid)
    if sr.payment_status not in ("beta", "paid", "free"):
        raise HTTPException(status_code=402, detail="Zahlung erforderlich")

    # 6. Already generating? Check if stale (stuck after container restart)
    if sr.status == "generating":
        stale_threshold = timedelta(minutes=10)
        now = datetime.now(timezone.utc)
        if sr.updated_at and (now - sr.updated_at) > stale_threshold:
            log.info(
                "[Strategy] Stale generation detected for briefing_id=%d (stuck since %s). Auto-reset to questions_saved.",
                briefing_id, sr.updated_at,
            )
            sr.status = "questions_saved"
            sr.updated_at = now
            db.commit()
            # Fall through to normal generation below
        else:
            return JSONResponse(
                content={"status": "already_generating", "briefing_id": briefing_id},
                status_code=200,
            )

    # 7. Already completed? Allow re-generation
    if sr.status == "completed":
        log.info("[Strategy] Re-generating report for briefing_id=%d", briefing_id)

    # 8. Update status and start background task
    sr.status = "generating"
    sr.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Load data needed for the pipeline
    analysis = db.query(Analysis).filter(
        Analysis.briefing_id == briefing_id
    ).first()

    briefing_data = briefing.answers or {}
    strategy_questions_data = sq.to_dict()
    report1_data = (analysis.meta if analysis else {}) or {}
    report2_data: Dict[str, Any] = {}  # Placeholder — will be populated from gamechanger data if available

    background_tasks.add_task(
        _run_strategy_pipeline,
        briefing_id=briefing_id,
        briefing_data=briefing_data,
        strategy_questions=strategy_questions_data,
        report1_data=report1_data,
        report2_data=report2_data,
    )

    log.info("[Strategy] Started generation for briefing_id=%d", briefing_id)

    return JSONResponse(
        content={"status": "generating", "briefing_id": briefing_id},
        status_code=202,
    )


async def _run_strategy_pipeline(
    briefing_id: int,
    briefing_data: Dict[str, Any],
    strategy_questions: Dict[str, Any],
    report1_data: Dict[str, Any],
    report2_data: Dict[str, Any],
):
    """Background task wrapper for the strategy pipeline."""
    from core.db import SessionLocal

    db = SessionLocal()
    try:
        from services.strategy_pipeline import generate_strategy_report
        await generate_strategy_report(
            briefing_id=briefing_id,
            briefing_data=briefing_data,
            strategy_questions=strategy_questions,
            report1_data=report1_data,
            report2_data=report2_data,
            db_session=db,
        )
    except Exception as exc:
        log.error("[Strategy] Pipeline failed for briefing_id=%d: %s", briefing_id, exc)
        # Update status to failed
        sr = db.query(StrategyReport).filter(
            StrategyReport.briefing_id == briefing_id
        ).first()
        if sr:
            sr.status = "failed"
            sr.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


# =============================================================================
# ENDPOINTS: PDF + HTML (Task 8)
# =============================================================================

@router.get("/pdf/{briefing_id}")
async def get_strategy_pdf(
    briefing_id: int,
    db: Session = Depends(get_db),
):
    """
    PDF-Download des Strategieberichts.
    Renders via Puppeteer PDF service (analog Report 1).
    """
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Kein Strategiebericht gefunden")
    if sr.status != "completed":
        raise HTTPException(status_code=400, detail=f"Bericht noch nicht fertig (Status: {sr.status})")
    if not sr.sections:
        raise HTTPException(status_code=500, detail="Keine Sections vorhanden")

    # Build HTML from template
    html_content = _render_strategy_html(sr, db)

    # Render PDF via Puppeteer service
    from services.pdf_client import render_pdf_from_html
    result = render_pdf_from_html(
        html=html_content,
        meta={"report_type": "strategy", "briefing_id": briefing_id},
    )

    if "error" in result:
        log.error("[Strategy] PDF rendering failed for briefing_id=%d: %s", briefing_id, result["error"])
        raise HTTPException(status_code=500, detail=f"PDF-Generierung fehlgeschlagen: {result['error']}")

    pdf_bytes = result.get("pdf_bytes")
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Keine PDF-Daten erhalten")

    # Update PDF tracking
    sr.pdf_available = True
    sr.pdf_generated_at = datetime.now(timezone.utc)
    sr.updated_at = datetime.now(timezone.utc)
    db.commit()

    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    firmenname = (briefing.answers or {}).get("unternehmen_name", "Unternehmen") if briefing else "Unternehmen"
    filename = f"KI-Strategiebericht-{firmenname}.pdf".replace(" ", "-")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/html/{briefing_id}", response_class=HTMLResponse)
async def get_strategy_html(
    briefing_id: int,
    db: Session = Depends(get_db),
):
    """HTML-Version des Strategieberichts (Debug/Validierung)."""
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        raise HTTPException(status_code=404, detail="Kein Strategiebericht gefunden")
    if sr.status != "completed":
        raise HTTPException(status_code=400, detail=f"Bericht noch nicht fertig (Status: {sr.status})")
    if not sr.sections:
        raise HTTPException(status_code=500, detail="Keine Sections vorhanden")

    html_content = _render_strategy_html(sr, db)
    return HTMLResponse(content=html_content, media_type="text/html; charset=utf-8")


def _render_strategy_html(sr: StrategyReport, db: Session) -> str:
    """Render strategy report HTML — delegates to shared renderer."""
    from services.strategy_renderer import render_strategy_html
    from utils.logo_embedder import embed_logos_in_html
    html = render_strategy_html(sr, db)
    # FIX-G: Embed logos as base64 (same pattern as report_renderer.py / gamechanger)
    _tpl_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    html = embed_logos_in_html(html, _tpl_dir)
    return html


# =============================================================================
# ENDPOINTS: ADMIN (Task 10)
# =============================================================================

@router.post("/admin/unlock/{briefing_id}")
async def admin_unlock_strategy(
    briefing_id: int,
    admin_key: str = Query(..., description="Admin API Key"),
    db: Session = Depends(get_db),
):
    """
    Beta-Freischaltung: Ermöglicht Generierung ohne Zahlung.
    Setzt payment_status='beta' in strategy_reports.
    Wird nur für die ersten Beta-Tester verwendet.
    """
    expected_key = os.getenv("STRATEGY_ADMIN_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=500, detail="STRATEGY_ADMIN_KEY nicht konfiguriert")
    if admin_key != expected_key:
        raise HTTPException(status_code=403, detail="Ungültiger Admin-Key")

    # Prüfe ob Briefing existiert
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing nicht gefunden")

    # Erstelle/Update strategy_reports
    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if sr:
        sr.payment_status = "beta"
        sr.updated_at = datetime.now(timezone.utc)
    else:
        sr = StrategyReport(
            briefing_id=briefing_id,
            status="pending",
            payment_status="beta",
        )
        db.add(sr)

    db.commit()
    log.info("[Strategy] Admin unlocked briefing_id=%d (beta)", briefing_id)

    return {"briefing_id": briefing_id, "payment_status": "beta", "message": "Beta freigeschaltet"}


@router.post("/admin/reset-status/{briefing_id}")
async def admin_reset_status(
    briefing_id: int,
    admin_key: str = Query(..., description="Admin API Key"),
    db: Session = Depends(get_db),
):
    """
    Reset stuck generation: Setzt status von 'generating' auf 'questions_saved'.
    Nur nötig nach Container-Restart während laufender Generierung.
    """
    expected_key = os.getenv("STRATEGY_ADMIN_KEY", "")
    if not expected_key:
        raise HTTPException(status_code=500, detail="STRATEGY_ADMIN_KEY nicht konfiguriert")
    if admin_key != expected_key:
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "detail": "Ungültiger Admin-Key"},
        )

    sr = db.query(StrategyReport).filter(
        StrategyReport.briefing_id == briefing_id
    ).first()
    if not sr:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "detail": f"Kein Strategy-Report für briefing_id {briefing_id}"},
        )

    if sr.status != "generating":
        return JSONResponse(
            status_code=400,
            content={
                "error": "not_generating",
                "detail": f"Status ist '{sr.status}', nicht 'generating'. Reset nicht nötig.",
            },
        )

    old_status = sr.status
    sr.status = "questions_saved"
    sr.updated_at = datetime.now(timezone.utc)
    db.commit()

    log.info(
        "[Strategy] Admin reset: briefing_id=%d, old_status=%s → questions_saved (by admin)",
        briefing_id, old_status,
    )

    return {
        "briefing_id": briefing_id,
        "old_status": old_status,
        "new_status": "questions_saved",
        "reset": True,
    }

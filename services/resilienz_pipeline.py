# -*- coding: utf-8 -*-
"""Resilienz V1: In-process-Report-Pipeline (KPA-Muster, kein Worker).

Ablauf: Briefing laden -> deterministisch scoren -> 2 LLM-Sektionen
(fail-open auf deterministische Texte) -> Jinja-HTML -> Analysis-Zeile ->
PDF -> Mail. Statusfuehrung direkt auf dem Briefing
(accepted -> processing -> done/failed).

Sprachregelung (Haftung): Der Report sichert nie "Sicherheit" oder
"Schutz" zu — Vokabular: Entscheidungsfaehigkeit, Vorbereitung,
Selbstauskunft. Tests/QA pruefen die verbotenen Muster.
"""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from services.resilienz_recommender import build_empfehlungen
from services.resilienz_score import calculate_resilienz, load_katalog

log = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATE_DIR = os.path.join(_BASE_DIR, "templates")

# Verbotene Zusicherungen (Haftung) — QA-Netz ueber dem fertigen HTML.
FORBIDDEN_ASSURANCES = (
    "garantiert sicher",
    "vollständig geschützt",
    "vollstaendig geschuetzt",
    "schützt Sie vor",
    "schuetzt Sie vor",
    "100 % Schutz",
    "100% Schutz",
    "Sicherheitsgarantie",
)

DISCLAIMER_DE = (
    "Dieser Report ist eine Selbstauskunft: Er bewertet Ihre Angaben, "
    "nicht Ihre Systeme. Er ist keine Sicherheitsprüfung, kein "
    "Penetrationstest und keine Rechtsberatung. Er sichert keine "
    "Schutzwirkung zu — er zeigt, wie vorbereitet Ihre Entscheidungswege "
    "sind. Die geschätzte Reaktionslücke ist eine Ableitung aus Ihren "
    "Antworten, keine Messung."
)

_AMPEL_FARBEN = {"rot": "#c0392b", "gelb": "#d4a017", "gruen": "#1e7d46"}
_AMPEL_LABELS = {"rot": "Rot", "gelb": "Gelb", "gruen": "Grün"}


# ---------------------------------------------------------------------------
# SVG-Bausteine (deterministisch, keine Chart-Library)
# ---------------------------------------------------------------------------

def build_radar_svg(block_means: Dict[str, float], katalog: Dict[str, Any]) -> str:
    """Spinnendiagramm der 6 Blockmittel (1..4) als inline-SVG."""
    cx, cy, r_max = 180.0, 160.0, 110.0
    blocks = katalog["blocks"]
    n = len(blocks)

    def point(i: int, value: float) -> str:
        angle = -math.pi / 2 + i * 2 * math.pi / n
        r = r_max * (value / 4.0)
        return f"{cx + r * math.cos(angle):.1f},{cy + r * math.sin(angle):.1f}"

    rings = []
    for ring_val in (1, 2, 3, 4):
        pts = " ".join(point(i, ring_val) for i in range(n))
        rings.append(
            f'<polygon points="{pts}" fill="none" stroke="#d8d8d8" stroke-width="1"/>'
        )
    axes, labels = [], []
    for i, block in enumerate(blocks):
        angle = -math.pi / 2 + i * 2 * math.pi / n
        x = cx + (r_max + 22) * math.cos(angle)
        y = cy + (r_max + 22) * math.sin(angle)
        axes.append(
            f'<line x1="{cx}" y1="{cy}" x2="{cx + r_max * math.cos(angle):.1f}" '
            f'y2="{cy + r_max * math.sin(angle):.1f}" stroke="#d8d8d8" stroke-width="1"/>'
        )
        labels.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="middle" '
            f'font-size="11" fill="#333">{block["id"]} · {block["titel"]}</text>'
        )
    data_pts = " ".join(point(i, block_means[b["id"]]) for i, b in enumerate(blocks))
    return (
        '<svg viewBox="0 0 360 320" role="img" aria-label="Blockprofil" '
        'xmlns="http://www.w3.org/2000/svg">'
        + "".join(rings) + "".join(axes)
        + f'<polygon points="{data_pts}" fill="rgba(30,90,160,0.25)" stroke="#1e5aa0" stroke-width="2"/>'
        + "".join(labels)
        + "</svg>"
    )


def build_zeitstrahl_svg(reaktionsluecke_label: str, benchmark_minuten: int) -> str:
    """Zeitstrahl: Angreifer-Benchmark vs. geschätzte Reaktionslücke."""
    return (
        '<svg viewBox="0 0 640 120" role="img" aria-label="Zeitvergleich" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<text x="0" y="18" font-size="13" fill="#333">Automatisierter Angriff (Benchmark)</text>'
        f'<rect x="0" y="26" width="60" height="18" rx="4" fill="#c0392b"/>'
        f'<text x="70" y="40" font-size="13" font-weight="bold" fill="#c0392b">~{benchmark_minuten} Minuten</text>'
        f'<text x="0" y="78" font-size="13" fill="#333">Ihre Organisation (geschätzt aus Ihren Angaben)</text>'
        f'<rect x="0" y="86" width="520" height="18" rx="4" fill="#5b6770"/>'
        f'<text x="530" y="100" font-size="13" font-weight="bold" fill="#333">{reaktionsluecke_label}</text>'
        "</svg>"
    )


# ---------------------------------------------------------------------------
# LLM-Sektionen (fail-open)
# ---------------------------------------------------------------------------

def _stufe_text(katalog: Dict[str, Any], qid: str, stufe: int) -> str:
    for block in katalog["blocks"]:
        for q in block["questions"]:
            if q["id"] == qid:
                return str(q["stufen"][stufe - 1])
    return ""


def _build_llm_vars(result: Dict[str, Any], answers: Dict[str, int], katalog: Dict[str, Any],
                    empfehlungen: List[Dict[str, Any]]) -> Dict[str, Any]:
    rl = result["reaktionsluecke"]
    treiber_texte = [
        f"{qid}: {_stufe_text(katalog, qid, answers[qid])}" for qid in rl["treiber"]
    ]
    schwach_texte = []
    for e in empfehlungen:
        block = next(b for b in katalog["blocks"] if b["id"] == e["block"])
        antworten = [
            f"{q['id']}: {_stufe_text(katalog, q['id'], answers[q['id']])}"
            for q in block["questions"]
        ]
        schwach_texte.append(f"Block {e['block']} ({e['titel']}): " + " | ".join(antworten))
    return {
        "score": result["score"],
        "ampel": _AMPEL_LABELS[result["ampel"]],
        "reaktionsluecke_label": rl["label"],
        "reaktionsluecke_aussage": rl["aussage"],
        "treiber_antworten": "\n".join(treiber_texte),
        "schwache_bloecke": "\n".join(schwach_texte),
        "schwaechster_block": result["schwaechster_block"],
        "benchmark_minuten": katalog["benchmark_minuten"],
    }


def _llm_section(section: str, vars_dict: Dict[str, Any], lang: str) -> Optional[str]:
    """Ein LLM-Absatz; None bei jedem Fehler (Aufrufer hat Fallback)."""
    try:
        from services.anthropic_client import call_anthropic, should_use_anthropic
        from services.prompt_loader import load_prompt
        if not should_use_anthropic(section):
            return None
        prompt = load_prompt(section, lang, vars_dict)
        text = call_anthropic(prompt, section=section, max_tokens=900)
        if text and text.strip():
            return str(text).strip()
    except Exception as exc:
        log.warning("[RESILIENZ] LLM-Sektion %s fail-open: %s", section, str(exc)[:200])
    return None


# ---------------------------------------------------------------------------
# Hauptpipeline
# ---------------------------------------------------------------------------

def render_resilienz_html(briefing: Any) -> Dict[str, Any]:
    """HTML + Metadaten fuer ein Resilienz-Briefing bauen (ohne DB-Write)."""
    lang = str(getattr(briefing, "lang", "de") or "de").lower()
    if not lang.startswith("de"):
        # Mehrsprachigkeit vorbereitet, aber V1 liefert bewusst nur DE —
        # kein stilles Sprach-Downgrade.
        raise ValueError(f"Resilienz-Report V1 unterstuetzt nur DE (lang={lang})")

    katalog = load_katalog("de")
    answers = {k: v for k, v in dict(briefing.answers or {}).items() if not k.startswith("_")}
    answers_int = {k: int(v) for k, v in answers.items()}
    result = calculate_resilienz(answers_int, "de")
    empfehlungen = build_empfehlungen(result["block_means"], "de")

    llm_vars = _build_llm_vars(result, answers_int, katalog, empfehlungen)
    kernaussage = _llm_section("resilienz_kernaussage", llm_vars, "de")
    befunde = _llm_section("resilienz_befunde", llm_vars, "de")

    from utils.report_display_id import get_report_display_id

    rl = result["reaktionsluecke"]
    blocks_ctx = []
    for block in katalog["blocks"]:
        bid = block["id"]
        blocks_ctx.append({
            "id": bid,
            "titel": block["titel"],
            "mean": result["block_means"][bid],
            "ampel": result["block_ampeln"][bid],
            "farbe": _AMPEL_FARBEN[result["block_ampeln"][bid]],
            "antworten": [
                {"id": q["id"], "text": q["text"],
                 "stufe": answers_int[q["id"]],
                 "stufe_text": q["stufen"][answers_int[q["id"]] - 1]}
                for q in block["questions"]
            ],
        })

    env = Environment(
        loader=FileSystemLoader(_TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("resilienz_report.html")
    html = template.render(
        display_id=get_report_display_id(briefing.id),
        datum=datetime.now(timezone.utc).strftime("%d.%m.%Y"),
        score=result["score"],
        ampel=result["ampel"],
        ampel_label=_AMPEL_LABELS[result["ampel"]],
        ampel_farbe=_AMPEL_FARBEN[result["ampel"]],
        gedeckelt=result["gedeckelt"],
        deckelregel_begruendung=katalog["deckelregel_begruendung"],
        ehrlichkeitsregel=katalog["ehrlichkeitsregel"],
        reaktionsluecke=rl,
        benchmark_minuten=katalog["benchmark_minuten"],
        zeitstrahl_svg=build_zeitstrahl_svg(rl["label"], katalog["benchmark_minuten"]),
        radar_svg=build_radar_svg(result["block_means"], katalog),
        blocks=blocks_ctx,
        empfehlungen=empfehlungen,
        kernaussage_html=kernaussage,
        befunde_html=befunde,
        disclaimer=DISCLAIMER_DE,
    )

    lowered = html.lower()
    for phrase in FORBIDDEN_ASSURANCES:
        if phrase.lower() in lowered:
            raise ValueError(f"Verbotene Zusicherung im Report: {phrase!r}")

    return {
        "html": html,
        "meta": {
            "report_type": "resilienz",
            "katalog_version": katalog["version"],
            "scores": {
                "score": result["score"],
                "ampel": result["ampel"],
                "gedeckelt": result["gedeckelt"],
                "block_means": result["block_means"],
                "reaktionsluecke": rl,
            },
            "llm_sections_used": {
                "kernaussage": kernaussage is not None,
                "befunde": befunde is not None,
            },
        },
    }


def generate_resilienz_report(briefing_id: int) -> None:
    """BackgroundTasks-Einstieg: kompletter Lauf inkl. Status, PDF, Mail."""
    from core.db import SessionLocal
    from models import Analysis, Briefing

    db = SessionLocal()
    try:
        briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
        if not briefing:
            log.error("[RESILIENZ] Briefing %s nicht gefunden", briefing_id)
            return
        briefing.status = "processing"
        briefing.processing_at = datetime.now(timezone.utc)
        db.commit()

        rendered = render_resilienz_html(briefing)

        analysis = Analysis(
            user_id=briefing.user_id,
            briefing_id=briefing.id,
            html=rendered["html"],
            meta=rendered["meta"],
        )
        db.add(analysis)
        briefing.status = "done"
        briefing.done_at = datetime.now(timezone.utc)
        db.commit()

        _send_resilienz_email(db, briefing, rendered["html"])
    except Exception as exc:
        log.error("[RESILIENZ] Generierung %s fehlgeschlagen: %s", briefing_id, exc, exc_info=True)
        try:
            briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
            if briefing:
                briefing.status = "failed"
                briefing.error = str(exc)[:500]
                db.commit()
        except Exception:  # pragma: no cover
            db.rollback()
    finally:
        db.close()


def render_resilienz_pdf(html: str, briefing_id: int) -> Dict[str, Any]:
    from services.pdf_client import build_footer_template, render_pdf_from_html
    return render_pdf_from_html(
        html,
        meta={"briefing_id": briefing_id, "report_type": "resilienz"},
        pdf_options={
            "printBackground": True,
            "displayHeaderFooter": True,
            "headerTemplate": "<div></div>",
            "footerTemplate": build_footer_template(str(briefing_id), lang="de"),
            "margin": {"top": "14mm", "right": "14mm", "bottom": "20mm", "left": "14mm"},
        },
    )


def _send_resilienz_email(db: Any, briefing: Any, html: str) -> None:
    """Report-Mail mit PDF-Anhang; Fehler blocken den Lauf nicht."""
    try:
        from gpt_analyze import _determine_user_email, _mask_email, _send_email_via_resend
        from utils.report_display_id import get_report_display_id

        user_email = _determine_user_email(db, briefing, None)
        if not user_email:
            log.info("[RESILIENZ] Keine Empfaenger-Mail fuer Briefing %s", briefing.id)
            return
        pdf_info = render_resilienz_pdf(html, briefing.id)
        pdf_bytes = pdf_info.get("pdf_bytes")
        display = get_report_display_id(briefing.id)
        attachments = None
        if pdf_bytes:
            attachments = [{
                "filename": f"KI-Resilienz-Check-{display}.pdf",
                "content": pdf_bytes,
                "mimetype": "application/pdf",
            }]
        body = (
            "<p>Guten Tag,</p>"
            "<p>Ihr KI-Resilienz-Check ist fertig. Das Ergebnis liegt als PDF bei.</p>"
            f"<p>Wichtig: Der Report ist eine Selbstauskunft — {DISCLAIMER_DE}</p>"
            "<p>Freundliche Grüße<br>ki-sicherheit.jetzt</p>"
        )
        ok, err = _send_email_via_resend(
            user_email, f"Ihr KI-Resilienz-Check ({display})", body, attachments=attachments,
        )
        log.info("[RESILIENZ] Mail an %s: ok=%s err=%s", _mask_email(user_email), ok, err)
    except Exception as exc:
        log.warning("[RESILIENZ] Mail-Versand uebersprungen: %s", str(exc)[:200])

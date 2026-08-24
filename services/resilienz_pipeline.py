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

# KIS-1260: Sparten-Labels (Medien-Vertikale) fuer den Betriebskontext
_SPARTE_LABELS = {
    "film_tv": "Film-/TV-Produktion",
    "post_vfx": "Postproduktion/VFX/Animation",
    "games": "Games/Interactive",
    "verlag": "Verlag/Publishing",
    "musik_audio": "Musik/Audio/Podcast",
    "agentur": "Agentur/Werbung/Design",
    "content_creation": "Content Creation/Social Media",
}


def load_r1_kontext(db: Any, user_id: Optional[int]) -> Optional[Dict[str, str]]:
    """KIS-1260: Branche/Sparte/Hauptleistung aus dem letzten fertigen
    r1-Briefing desselben Users — personalisiert die LLM-Texte, ohne dass
    der Check selbst Firmendaten erhebt. Kein r1 vorhanden -> None."""
    if not user_id:
        return None
    try:
        from models import Briefing
        from services.answers_normalizer import BRANCHEN_LABELS

        r1 = (
            db.query(Briefing)
            .filter(
                Briefing.user_id == user_id,
                Briefing.report_type == "r1",
                Briefing.status == "done",
            )
            .order_by(Briefing.id.desc())
            .first()
        )
        if not r1:
            return None
        answers = dict(r1.answers or {})
        branche = str(answers.get("branche") or "").strip().lower()
        kontext: Dict[str, str] = {}
        if branche:
            kontext["branche"] = BRANCHEN_LABELS.get(branche, branche)
        sparte = str(answers.get("medien_sparte") or "").strip().lower()
        if sparte:
            kontext["sparte"] = _SPARTE_LABELS.get(sparte, sparte)
        hauptleistung = str(answers.get("hauptleistung") or "").strip()
        if hauptleistung:
            kontext["hauptleistung"] = hauptleistung[:300]
        return kontext or None
    except Exception as exc:
        log.warning("[RESILIENZ] r1-Kontext nicht ladbar: %s", str(exc)[:200])
        return None


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
        f'<rect x="0" y="86" width="400" height="18" rx="4" fill="#5b6770"/>'
        # KIS-1259: Label stand bei x=530 und lief aus dem 640er-viewBox
        # ("mehr als 8 Stunde") — kuerzerer Balken, Label mit Platz daneben.
        f'<text x="410" y="100" font-size="13" font-weight="bold" fill="#333">{reaktionsluecke_label}</text>'
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


def _kontext_zeile(r1_kontext: Optional[Dict[str, str]]) -> str:
    """Betriebskontext fuer den Prompt — Branche, Sparte, Hauptleistung.

    KIS-1261: Die Hauptleistung ist ein Freitext aus dem r1-Fragebogen und
    kann in jeder Sprache dastehen. Fuer den Prompt ist das unkritisch (das
    Modell antwortet ohnehin deutsch), fuer den Report-Kopf nicht — dort
    steht nur die uebersetzte Branchenzeile (_kontext_kopf).
    """
    if not r1_kontext:
        return ""
    teile = []
    if _kontext_kopf(r1_kontext):
        teile.append(_kontext_kopf(r1_kontext))
    if r1_kontext.get("hauptleistung"):
        teile.append(r1_kontext["hauptleistung"][:180])
    return " — ".join(teile)


def _kontext_kopf(r1_kontext: Optional[Dict[str, str]]) -> str:
    """Kurze Branchenzeile fuer Seite 1 — immer deutsch, immer einzeilig."""
    if not r1_kontext or not r1_kontext.get("branche"):
        return ""
    kopf = r1_kontext["branche"]
    if r1_kontext.get("sparte"):
        kopf += f" ({r1_kontext['sparte']})"
    return kopf


_BEFUND_MIN_ZEICHEN = 40


def _fehlende_befund_bloecke(befunde_html: str, empfehlungen: List[Dict[str, Any]]) -> List[str]:
    """Welche schwachen Bloecke hat das Modell im Befundtext ausgelassen?

    KIS-1261: Der Lauf lieferte fuenf von sechs Befunden — ausgerechnet
    Block C (Entscheiden, hoechstes Gewicht, Treiber der Reaktionsluecke)
    fehlte. Ein Retry kostet 20 Sekunden und garantiert nichts; dieses Netz
    haengt die fehlenden Bloecke deterministisch an.
    """
    text = befunde_html or ""
    fehlend = []
    for e in empfehlungen:
        marker = f"Block {e['block']}"
        pos = text.find(marker)
        if pos < 0 or len(text) - pos < _BEFUND_MIN_ZEICHEN:
            fehlend.append(e["block"])
    return fehlend


def _deterministischer_befund(e: Dict[str, Any]) -> str:
    """Ein Befund aus den Angaben selbst — gleiche Form wie der Fallback."""
    return (
        f'<div class="befund"><h3>Block {e["block"]} — {e["titel"]}</h3>'
        f'<p>Die schwächste Angabe in diesem Bereich: „{e["schwaechste_antwort"]}“ — '
        f'auf die Frage „{e["schwaechste_frage"]}“. Genau hier verlängert sich '
        f'Ihre Reaktionszeit im Ernstfall.</p></div>'
    )


def _llm_section(section: str, vars_dict: Dict[str, Any], lang: str, max_tokens: int = 900) -> Optional[str]:
    """Ein LLM-Absatz; None bei jedem Fehler (Aufrufer hat Fallback).

    KIS-1259: bewusst OHNE should_use_anthropic — dessen ANTHROPIC_SECTIONS-
    Whitelist sortierte die neuen Sektionsnamen still aus (nur debug-Log),
    und der Report fiel unbemerkt auf die deterministischen Texte zurueck.
    Resilienz nutzt immer Anthropic; ohne Client greift der Fallback —
    jetzt mit sichtbarem Log in beiden Richtungen.
    """
    import time as _time
    try:
        from services.anthropic_client import call_anthropic, get_anthropic_client
        from services.prompt_loader import load_prompt
        if get_anthropic_client() is None:
            log.warning("[RESILIENZ] LLM-Sektion %s uebersprungen: kein Anthropic-Client", section)
            return None
        prompt = load_prompt(section, lang, vars_dict)
        _t0 = _time.time()
        text = call_anthropic(prompt, section=section, max_tokens=max_tokens)
        if text and text.strip():
            log.info("[RESILIENZ] LLM-Sektion %s ok (%.1fs, %d Zeichen)",
                     section, _time.time() - _t0, len(text))
            return str(text).strip()
        log.warning("[RESILIENZ] LLM-Sektion %s leer (%.1fs) — deterministischer Fallback",
                    section, _time.time() - _t0)
    except Exception as exc:
        log.warning("[RESILIENZ] LLM-Sektion %s fail-open: %s", section, str(exc)[:200])
    return None


# ---------------------------------------------------------------------------
# Hauptpipeline
# ---------------------------------------------------------------------------

def render_resilienz_html(briefing: Any, r1_kontext: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
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

    # KIS-1259: Deterministischer Befund-Fallback war 6x derselbe Satz.
    # Jetzt traegt jede Empfehlung ihre schwaechste Frage + Antwort — und
    # seit KIS-1261 speist das auch das Vollstaendigkeits-Netz unten.
    frage_map = {q["id"]: q for b in katalog["blocks"] for q in b["questions"]}
    for e in empfehlungen:
        block = next(b for b in katalog["blocks"] if b["id"] == e["block"])
        weakest_qid = min((q["id"] for q in block["questions"]), key=lambda qid: answers_int[qid])
        e["schwaechste_frage"] = frage_map[weakest_qid]["text"]
        e["schwaechste_antwort"] = frage_map[weakest_qid]["stufen"][answers_int[weakest_qid] - 1]

    llm_vars = _build_llm_vars(result, answers_int, katalog, empfehlungen)
    betriebskontext = _kontext_zeile(r1_kontext)
    llm_vars["betriebskontext"] = betriebskontext or "unbekannt"
    kernaussage = _llm_section("resilienz_kernaussage", llm_vars, "de")
    # KIS-1260: Befunde brauchen Luft — das adaptive Denken von Sonnet 5
    # zaehlt gegen max_tokens; 900 liess Block F leer (doppelte Truncation).
    befunde = _llm_section("resilienz_befunde", llm_vars, "de", max_tokens=2500)

    if befunde:
        fehlend = _fehlende_befund_bloecke(befunde, empfehlungen)
        if fehlend:
            log.warning("[RESILIENZ] Befunde ohne Block %s — deterministisch ergaenzt",
                        ", ".join(fehlend))
            nachtrag = [e for e in empfehlungen if e["block"] in fehlend]
            befunde += "".join(_deterministischer_befund(e) for e in nachtrag)

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
        # KIS-1261: Seite 1 zeigt nur die uebersetzte Branchenzeile. Der
        # r1-Freitext "hauptleistung" stand dort in Originalsprache (im
        # Testlauf englisch) und sprengte die Kopfzeile.
        betriebskontext=_kontext_kopf(r1_kontext),
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
            "betriebskontext": betriebskontext or None,
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

        r1_kontext = load_r1_kontext(db, briefing.user_id)
        rendered = render_resilienz_html(briefing, r1_kontext=r1_kontext)

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
    from datetime import datetime as _dt, timezone as _tz

    from services.pdf_client import build_footer_template, render_pdf_from_html
    from utils.report_display_id import get_report_display_id
    return render_pdf_from_html(
        html,
        meta={"briefing_id": briefing_id, "report_type": "resilienz"},
        pdf_options={
            "printBackground": True,
            "displayHeaderFooter": True,
            "headerTemplate": "<div></div>",
            # KIS-1259: Footer zeigte die rohe Briefing-ID (1142), der
            # Kopf die Display-ID (KIS-1259) — jetzt einheitlich.
            "footerTemplate": build_footer_template(get_report_display_id(briefing_id), _dt.now(_tz.utc).strftime("%d.%m.%Y"), lang="de"),
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
                "filename": f"Cyberangriffs-Check-{display}.pdf",
                "content": pdf_bytes,
                "mimetype": "application/pdf",
            }]
        body = (
            "<p>Guten Tag,</p>"
            "<p>Ihr Cyberangriffs-Check ist fertig. Das Ergebnis liegt als PDF bei.</p>"
            f"<p>Wichtig: Der Report ist eine Selbstauskunft — {DISCLAIMER_DE}</p>"
            "<p>Freundliche Grüße<br>ki-sicherheit.jetzt</p>"
        )
        ok, err = _send_email_via_resend(
            user_email, f"Ihr Cyberangriffs-Check ({display})", body, attachments=attachments,
        )
        log.info("[RESILIENZ] Mail an %s: ok=%s err=%s", _mask_email(user_email), ok, err)
    except Exception as exc:
        log.warning("[RESILIENZ] Mail-Versand uebersprungen: %s", str(exc)[:200])

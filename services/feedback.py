# -*- coding: utf-8 -*-
"""
services/feedback.py — Feedback-Service

Handles feedback submission: logging, optional DB persistence,
optional forwarding to external webhook (Make/n8n), and email notification.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

log = logging.getLogger("services.feedback")

# Default admin email for feedback notifications
FEEDBACK_NOTIFY_EMAIL_DEFAULT = "kontakt@ki-sicherheit.jetzt"


def _get_feedback_notify_email() -> str:
    """Returns FEEDBACK_NOTIFY_EMAIL or default (kontakt@ki-sicherheit.jetzt)."""
    return (os.getenv("FEEDBACK_NOTIFY_EMAIL") or "").strip() or FEEDBACK_NOTIFY_EMAIL_DEFAULT


# KIS-1318: Die Mail zeigte die Codes des Formulars („yes_interested",
# „quick_wins", „kmu") und übersah `tools_adopted` und `funding_applied` —
# die beiden Felder, die KIS-1281 (Stufe 4) als einzige Quelle für Neues von
# außen eingeführt hat. Labels wie im Formular (make-ki-frontend,
# feedback/feedback.html); wer dort eine Option ergänzt, ergänzt sie hier.
_LABELS: Dict[str, Dict[str, str]] = {
    "payment_willingness": {
        "yes_interested": "Ja, grundsätzlich interessant",
        "yes_if_deductible": "Ja, wenn steuerlich absetzbar oder förderfähig",
        "not_really": "Eher nicht",
        "need_info": "Braucht erst mehr Informationen",
    },
    "training_interest": {
        "urgent": "Ja, dringend",
        "interested": "Ja, grundsätzlich interessant",
        "need_info": "Braucht erst mehr Infos",
        "no": "Nein, kein Bedarf",
    },
    "contact_permission": {"yes": "Ja, gerne per E-Mail", "no": "Nein, danke"},
    "report_guardrails_used": {
        "yes": "Ja, berücksichtigt",
        "no": "Nein, ignoriert",
        "not_used": "Keine angegeben",
    },
    "ux_required_fields": {
        "ok": "Passend",
        "too_many": "Zu viele",
        "too_few": "Zu wenige",
        "unsure": "Kann ich nicht beurteilen",
    },
    "report_helpful_sections": {
        "quick_wins": "Quick Wins",
        "roadmap": "Roadmap",
        "compliance": "Risiko & Compliance",
        "funding": "Fördermöglichkeiten",
        "summary": "Zusammenfassung",
        "other": "Sonstiges",
    },
    "branch_feedback": {
        "beratung": "Beratung & Dienstleistungen",
        "it": "IT & Software",
        "medien": "Medien & Kreativwirtschaft",
        "handel": "Handel / E-Commerce",
        "industrie": "Industrie / Produktion",
        "sonstige": "Sonstige",
    },
    "company_size_feedback": {
        "solo": "Solo / Freiberuflich",
        "small_team": "Kleines Team (2–10)",
        "kmu": "KMU (11–100)",
        "larger": "Größer (100+)",
    },
}

_LEER = "—"


def _wert(payload: Dict[str, Any], key: str, *alt_keys: str) -> Any:
    val = payload.get(key)
    for ak in alt_keys:
        if val is None or val == "":
            val = payload.get(ak)
    return val


def _label(payload: Dict[str, Any], key: str, *alt_keys: str) -> str:
    """Wert mit Label aus `_LABELS`; Listen werden aufgezählt; leer → „—"."""
    val = _wert(payload, key, *alt_keys)
    if val is None or val == "" or val == []:
        return _LEER
    mapping = _LABELS.get(key, {})
    if isinstance(val, list):
        return ", ".join(mapping.get(str(v), str(v)) for v in val)
    return mapping.get(str(val), str(val))


def _skala(payload: Dict[str, Any], key: str, maximum: int, *alt_keys: str) -> tuple:
    """Liefert (Anzeige, Balken) für eine Bewertung, z. B. („6/10", „●●●●●●○○○○")."""
    val = _wert(payload, key, *alt_keys)
    try:
        n = int(str(val))
    except (TypeError, ValueError):
        return _LEER, ""
    n = max(0, min(maximum, n))
    return f"{n}/{maximum}", "●" * n + "○" * (maximum - n)


def _kis_nummer(briefing_id: Any) -> str:
    try:
        return f"KIS-{int(briefing_id) + 117}"
    except (ValueError, TypeError):
        return ""


def _zeit_de(timestamp: str) -> str:
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%d.%m.%Y, %H:%M Uhr UTC")
    except ValueError:
        return timestamp


def _freitexte(payload: Dict[str, Any]) -> list:
    felder = [
        ("Zum Report", "report_comment"),
        ("Zum Fragebogen", "ux_comment"),
        ("Abschluss", "final_comment"),
    ]
    out = []
    for titel, key in felder:
        val = _wert(payload, key)
        if val is not None and str(val).strip():
            out.append((titel, str(val).strip()))
    return out


def _bloecke(payload: Dict[str, Any]) -> list:
    """Die vier Blöcke der Mail als (Titel, [(Label, Wert, Balken)])."""
    g10, b10 = _skala(payload, "overall_helpfulness_score", 10, "gesamtbewertung")
    rel, brel = _skala(payload, "report_relevance_rating", 5)
    kla, bkla = _skala(payload, "ux_clarity_rating", 5)
    auf, bauf = _skala(payload, "ux_effort_rating", 5)
    ziel, bziel = _skala(payload, "report_goals_visible", 5)
    return [
        ("Bewertungen", [
            ("Hilfreich insgesamt", g10, b10),
            ("Report-Relevanz", rel, brel),
            ("Fragebogen: Klarheit", kla, bkla),
            ("Fragebogen: Aufwand", auf, bauf),
            ("Pflichtfelder", _label(payload, "ux_required_fields"), ""),
        ]),
        ("Inhalt des Reports", [
            ("Hilfreichste Kapitel", _label(payload, "report_helpful_sections"), ""),
            ("Ziele sichtbar", ziel, bziel),
            ("Leitplanken berücksichtigt", _label(payload, "report_guardrails_used"), ""),
            ("Werkzeuge übernommen", _label(payload, "tools_adopted"), ""),
            ("Förderung beantragt", _label(payload, "funding_applied"), ""),
            ("Branche", _label(payload, "branch_feedback"), ""),
            ("Unternehmensgröße", _label(payload, "company_size_feedback"), ""),
        ]),
        ("Geschäftssignale", [
            ("Zahlungsbereitschaft", _label(payload, "payment_willingness", "zahlungsbereitschaft"), ""),
            ("Schulungsinteresse", _label(payload, "training_interest", "schulungsinteresse"), ""),
            ("Kontakt erlaubt", _label(payload, "contact_permission", "kontakterlaubnis"), ""),
        ]),
    ]


def _kopfzeilen(payload: Dict[str, Any], timestamp: str) -> list:
    briefing_id = _wert(payload, "briefing_id")
    kis = _kis_nummer(briefing_id)
    zeilen = [
        ("E-Mail", _label(payload, "email")),
        ("Report", f"{kis} (Briefing {briefing_id})" if kis else _label(payload, "briefing_id")),
        ("Zeitpunkt", _zeit_de(timestamp)),
    ]
    for label, key in (("Testreferenz", "test_reference"), ("Report-Version", "report_version"),
                       ("Variante", "variant"), ("Sprache", "lang_ui")):
        val = _wert(payload, key)
        if val is not None and str(val).strip():
            zeilen.append((label, str(val)))
    return zeilen


def build_feedback_subject(payload: Dict[str, Any], feedback_type: str) -> str:
    email = str(_wert(payload, "email") or "").strip() or "unbekannt"
    if feedback_type == "waitlist_training":
        return f"[KI-Sicherheit] Schulungs-Warteliste: {email}"
    teile = ["[KI-Sicherheit] Feedback"]
    g10, _ = _skala(payload, "overall_helpfulness_score", 10, "gesamtbewertung")
    if g10 != _LEER:
        teile.append(g10)
    kis = _kis_nummer(_wert(payload, "briefing_id"))
    if kis:
        teile.append(kis)
    teile.append(email)
    return " · ".join(teile)


def _build_notification_body(payload: Dict[str, Any], feedback_type: str, timestamp: str) -> str:
    """Textfassung der Benachrichtigung (Fallback für Mailclients ohne HTML)."""
    if feedback_type == "waitlist_training":
        return (
            "Neue Anmeldung zur Schulungs-Warteliste\n\n"
            f"E-Mail:    {_label(payload, 'email')}\n"
            f"Zeitpunkt: {_zeit_de(timestamp)}\n\n"
            "Alle Einträge: GET /api/admin/feedback/list (Admin-Key per Header X-Admin-Key)"
        )
    breite = 28
    zeilen = ["Neues Feedback zum KI-Status-Report", ""]
    for label, wert in _kopfzeilen(payload, timestamp):
        zeilen.append(f"{label + ':':<{breite}}{wert}")
    for titel, eintraege in _bloecke(payload):
        zeilen += ["", titel.upper(), "-" * len(titel)]
        for label, wert, balken in eintraege:
            zeilen.append(f"{label + ':':<{breite}}{wert}" + (f"  {balken}" if balken else ""))
    zeilen += ["", "FREITEXT", "--------"]
    texte = _freitexte(payload)
    if texte:
        for titel, text in texte:
            zeilen.append(f"{titel}: {text}")
    else:
        zeilen.append("Keine Freitexte.")
    briefing_id = _wert(payload, "briefing_id")
    zeilen += ["", f"Report ansehen: GET /api/report/html/{briefing_id}",
               "Alle Einträge:  GET /api/admin/feedback/list (Admin-Key per Header X-Admin-Key)"]
    return "\n".join(zeilen)


def _esc(s: Any) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_notification_html(payload: Dict[str, Any], feedback_type: str, timestamp: str) -> str:
    """HTML-Fassung: Kopf mit Gesamtnote, vier Blöcke als Tabellen, Freitext
    als Zitate. Inline-Styles, keine externen Ressourcen — Outlook und Apple
    Mail zeigen das gleich."""
    if feedback_type == "waitlist_training":
        return (
            '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:14px;color:#1e293b;">'
            "<h2 style=\"margin:0 0 12px;font-size:18px;\">Neue Anmeldung zur Schulungs-Warteliste</h2>"
            f"<p><strong>E-Mail:</strong> {_esc(_label(payload, 'email'))}<br>"
            f"<strong>Zeitpunkt:</strong> {_esc(_zeit_de(timestamp))}</p></div>"
        )
    g10, b10 = _skala(payload, "overall_helpfulness_score", 10, "gesamtbewertung")
    kis = _kis_nummer(_wert(payload, "briefing_id"))
    kontakt = str(_wert(payload, "contact_permission", "kontakterlaubnis") or "") == "yes"
    kis_txt = (" · " + _esc(kis)) if kis else ""

    def _tabelle(eintraege: list) -> str:
        rows = []
        for label, wert, balken in eintraege:
            balken_html = (f'<span style="color:#1d4ed8;letter-spacing:1px;margin-left:8px;">{balken}</span>'
                           if balken else "")
            rows.append(
                '<tr><td style="padding:6px 12px 6px 0;color:#64748b;white-space:nowrap;vertical-align:top;">'
                f"{_esc(label)}</td><td style=\"padding:6px 0;\">{_esc(wert)}{balken_html}</td></tr>"
            )
        return '<table style="border-collapse:collapse;font-size:14px;">' + "".join(rows) + "</table>"

    teile = [
        '<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;font-size:14px;color:#1e293b;max-width:640px;">',
        '<div style="background:#0f2a4a;color:#fff;border-radius:10px;padding:16px 20px;margin-bottom:16px;">',
        f'<div style="font-size:12px;opacity:.8;">Neues Feedback{kis_txt}</div>',
        f'<div style="font-size:26px;font-weight:700;line-height:1.2;">{_esc(g10)} '
        f'<span style="font-size:14px;font-weight:400;opacity:.85;">hilfreich</span></div>',
        (f'<div style="font-size:16px;letter-spacing:2px;color:#93c5fd;">{b10}</div>' if b10 else ""),
        "</div>",
    ]
    if kontakt:
        teile.append('<div style="background:#dcfce7;border:1px solid #86efac;color:#166534;border-radius:8px;'
                     'padding:10px 14px;margin-bottom:16px;font-weight:600;">Kontakt erlaubt — Rückmeldung per E-Mail möglich.</div>')
    teile.append(_tabelle([(l, w, "") for l, w in _kopfzeilen(payload, timestamp)]))
    for titel, eintraege in _bloecke(payload):
        teile.append(f'<h3 style="font-size:15px;margin:20px 0 6px;padding-bottom:4px;border-bottom:1px solid #e2e8f0;">{_esc(titel)}</h3>')
        teile.append(_tabelle(eintraege))
    teile.append('<h3 style="font-size:15px;margin:20px 0 6px;padding-bottom:4px;border-bottom:1px solid #e2e8f0;">Freitext</h3>')
    texte = _freitexte(payload)
    if texte:
        for titel, text in texte:
            teile.append(f'<p style="margin:8px 0;"><strong>{_esc(titel)}:</strong></p>'
                         f'<blockquote style="margin:4px 0 12px;padding:8px 12px;border-left:3px solid #94a3b8;'
                         f'background:#f8fafc;white-space:pre-wrap;">{_esc(text)}</blockquote>')
    else:
        teile.append('<p style="color:#64748b;">Keine Freitexte.</p>')
    briefing_id = _wert(payload, "briefing_id")
    teile.append('<p style="margin-top:20px;font-size:12px;color:#64748b;">'
                 f"Report ansehen: <code>GET /api/report/html/{_esc(briefing_id)}</code> · "
                 "Alle Einträge: <code>GET /api/admin/feedback/list</code> (Admin-Key per Header X-Admin-Key)</p></div>")
    return "".join(teile)


async def send_feedback_notification_email(payload: Dict[str, Any]) -> bool:
    """
    Send feedback notification email to admin (kontakt@ki-sicherheit.jetzt).

    Uses the existing Mailer service (Resend/SMTP).
    Returns True if successful, False otherwise (never raises).
    """
    notify_email = _get_feedback_notify_email()
    # FIX-B1: Default type to "form_feedback" when empty/missing
    feedback_type = payload.get("type") or "form_feedback"
    timestamp = datetime.now(timezone.utc).isoformat()

    # KIS-1318: Betreff nennt Note und Report, der Text trägt Labels statt
    # Codes, dazu eine HTML-Fassung.
    subject = build_feedback_subject(payload, feedback_type)
    body_text = _build_notification_body(payload, feedback_type, timestamp)
    body_html = build_notification_html(payload, feedback_type, timestamp)

    try:
        from services.mailer import Mailer

        mailer = Mailer.from_settings()
        await mailer.send(
            to=notify_email,
            subject=subject,
            text=body_text,
            html=body_html,
        )
        log.info("✓ Feedback notification email sent to %s", notify_email)
        return True

    except Exception as exc:
        log.error(
            "✗ Failed to send feedback notification email to %s: %s - %s",
            notify_email,
            type(exc).__name__,
            str(exc)
        )
        return False


def log_feedback(payload: Dict[str, Any], source: str = "feedback_form_v1") -> None:
    """
    Log feedback payload in structured format.

    This ensures feedback is never lost - at minimum it's in the logs.
    """
    log.info(
        "📝 FEEDBACK RECEIVED [source=%s] payload=%s",
        source,
        json.dumps(payload, ensure_ascii=False, indent=None)
    )


def save_feedback_to_db(
    db,
    payload: Dict[str, Any],
    source: str = "feedback_form_v1"
) -> Optional[int]:
    """
    Save feedback to database.

    Returns the feedback ID if successful, None otherwise.
    """
    try:
        from models import Feedback

        feedback = Feedback(
            payload=payload,
            source=source
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        feedback_id: int = feedback.id
        log.info("✓ Feedback saved to DB: id=%d, source=%s", feedback_id, source)
        return feedback_id

    except ImportError:
        log.debug("Feedback model not available - skipping DB save")
        return None
    except Exception as exc:
        log.error("✗ Failed to save feedback to DB: %s - %s", type(exc).__name__, str(exc))
        try:
            db.rollback()
        except Exception:
            pass
        return None


async def process_feedback(
    payload: Dict[str, Any],
    db=None,
    source: str = "feedback_form_v1"
) -> Dict[str, Any]:
    """
    Process incoming feedback: log, save to DB, send email notification.

    This is the main entry point for the feedback service.
    Single notification path: email via Resend/SMTP to kontakt@ki-sicherheit.jetzt.
    Webhook forwarding was removed to prevent duplicate emails (external
    Make/n8n scenarios sent their own notifications).

    Returns a result dict with status and optional details.
    """
    result: Dict[str, Any] = {
        "logged": False,
        "saved_to_db": False,
        "email_sent": False,
        "feedback_id": None,
    }

    # 1. Always log (this ensures we never lose feedback)
    log_feedback(payload, source)
    result["logged"] = True

    # 2. Save to DB if available
    if db is not None:
        feedback_id = save_feedback_to_db(db, payload, source)
        if feedback_id:
            result["saved_to_db"] = True
            result["feedback_id"] = feedback_id

    # 3. Send email notification to admin (fire-and-forget, non-blocking)
    #    Single path for ALL feedback types — no webhook, no duplicate.
    asyncio.ensure_future(_safe_send_notification(payload))
    result["email_sent"] = True  # optimistic; errors are logged

    return result


async def _safe_send_notification(payload: Dict[str, Any]) -> None:
    """Fire-and-forget wrapper: send email, log errors, never raise."""
    try:
        await send_feedback_notification_email(payload)
    except Exception as exc:
        log.error("Background email notification failed: %s", exc)

# -*- coding: utf-8 -*-
"""routes/cyber_public.py — Cyberangriffs-Check ohne Login (KIS-1263).

Der eingeloggte Weg (routes/resilienz.py) bleibt unangetastet. Dieser
Router ist der oeffentliche Einstieg fuer ki-sicherheit.jetzt und
funktioniert zweistufig:

1. Kurz-Check: die fuenf Fragen der Min-Regel (B2, C1..C4). Sie bestimmen
   die Reaktionsluecke vollstaendig — das Ergebnis ist also keine
   geschoente Vorschau, sondern dieselbe Zahl wie im grossen Check.
   Kein Speichern, keine Mail, kein LLM.
2. Vollreport: alle 22 Antworten plus E-Mail. Der Report entsteht erst,
   wenn die Adresse per Bestaetigungslink freigegeben wurde — sonst
   koennte jeder fremde Adressen eintragen und PDFs zustellen lassen.

Schutz (oeffentlicher Endpunkt = fremde Kosten und fremde Postfaecher):
IP-Limit, Honigtopf-Feld, Mindest-Ausfuellzeit, Token mit Ablaufdatum.
Die Firmennamen-Invariante gilt unveraendert: erhoben werden 22 Stufen
und eine E-Mail, sonst nichts.
"""

from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from routes._bootstrap import get_db, rate_limiter
from services.resilienz_score import REAKTIONSLUECKE_FIELDS, all_question_ids, load_katalog

router = APIRouter(prefix="/cyber", tags=["cyber-public"])
log = logging.getLogger(__name__)

_TOKEN_TTL_TAGE = 7

# Mindestzeit fuers Ausfuellen. Ein Mensch braucht fuer 22 Fragen
# Minuten, ein Skript Millisekunden.
_MIN_MS_KURZ = 3_000
_MIN_MS_VOLL = 20_000


def _token_fuer(briefing_id: int) -> str:
    """Bestaetigungs-Token als HMAC ueber die Briefing-ID.

    Der Token wird nirgends gespeichert: Er laesst sich aus der ID und dem
    Server-Geheimnis jederzeit nachrechnen, ohne es aber nicht erraten.
    Das erspart eine Spalte, eine Migration und die Suche ueber alle
    offenen Vorgaenge — die Bestaetigung ist ein Primaerschluesselzugriff.
    """
    import hashlib
    import hmac

    secret = (
        os.getenv("CYBER_CONFIRM_SECRET")
        or os.getenv("JWT_SECRET")
        or os.getenv("SECRET_KEY")
        or ""
    )
    if not secret:
        raise RuntimeError("Kein Server-Geheimnis für den Bestätigungslink gesetzt")
    mac = hmac.new(secret.encode("utf-8"), f"cyber:{briefing_id}".encode("utf-8"),
                   hashlib.sha256)
    return mac.hexdigest()[:32]


def _limit(name: str, default_limit: int, default_window: int):
    return Depends(
        rate_limiter(
            f"cyber:{name}",
            int(os.getenv(f"CYBER_RATE_LIMIT_{name.upper()}", str(default_limit))),
            int(os.getenv(f"CYBER_RATE_WINDOW_{name.upper()}", str(default_window))),
        )
    )


def _frage_map(lang: str = "de") -> Dict[str, Dict[str, Any]]:
    return {q["id"]: q for b in load_katalog(lang)["blocks"] for q in b["questions"]}


def _pruefe_bot(hp: str, ms: int, min_ms: int) -> None:
    """Honigtopf und Ausfuellzeit — beides still, ohne Hinweis fuer Skripte."""
    if hp:
        raise HTTPException(status_code=422, detail="Eingabe konnte nicht verarbeitet werden")
    if ms < min_ms:
        raise HTTPException(status_code=422, detail="Eingabe konnte nicht verarbeitet werden")


def _stufen_pruefen(answers: Dict[str, int], erlaubt: set) -> Dict[str, int]:
    fehlend = sorted(erlaubt - set(answers))
    fremd = sorted(set(answers) - erlaubt)
    if fehlend:
        raise ValueError(f"Fehlende Antworten: {', '.join(fehlend)}")
    if fremd:
        raise ValueError(f"Unbekannte Felder: {', '.join(fremd)}")
    schlecht = sorted(k for k, s in answers.items() if not isinstance(s, int) or not 1 <= s <= 4)
    if schlecht:
        raise ValueError(f"Ungültige Stufe (erlaubt 1–4) bei: {', '.join(schlecht)}")
    return answers


# ---------------------------------------------------------------------------
# Stufe 1: Kurz-Check (fuenf Fragen, sofortiges Ergebnis)
# ---------------------------------------------------------------------------

class KurzcheckIn(BaseModel):
    answers: Dict[str, int]
    hp: str = ""
    ms: int = 0

    @field_validator("answers")
    @classmethod
    def _nur_treiberfragen(cls, v: Dict[str, int]) -> Dict[str, int]:
        return _stufen_pruefen(v, set(REAKTIONSLUECKE_FIELDS))


@router.get("/kurzfragen", dependencies=[_limit("lesen", 60, 60)])
async def kurzfragen() -> Dict[str, Any]:
    """Die fuenf Fragen, die die Reaktionsluecke bestimmen."""
    katalog = load_katalog("de")
    fragen = _frage_map("de")
    return {
        "benchmark_minuten": katalog["benchmark_minuten"],
        "ehrlichkeitsregel": katalog["ehrlichkeitsregel"],
        "questions": [
            {"id": qid, "text": fragen[qid]["text"], "stufen": fragen[qid]["stufen"]}
            for qid in REAKTIONSLUECKE_FIELDS
        ],
    }


@router.post("/kurzcheck", dependencies=[_limit("kurz", 20, 60)])
async def kurzcheck(payload: KurzcheckIn) -> Dict[str, Any]:
    """Reaktionsluecke aus den fuenf Treiberfragen — ohne Speichern."""
    _pruefe_bot(payload.hp, payload.ms, _MIN_MS_KURZ)

    katalog = load_katalog("de")
    min_stufe = min(payload.answers[f] for f in REAKTIONSLUECKE_FIELDS)
    band = next(b for b in katalog["reaktionsluecke_bands"] if b["min_stufe"] == min_stufe)
    treiber = sorted(f for f in REAKTIONSLUECKE_FIELDS if payload.answers[f] == min_stufe)
    fragen = _frage_map("de")
    return {
        "label": band["label"],
        "aussage": band["aussage"],
        "ampel": band["ampel"],
        "min_stufe": min_stufe,
        "benchmark_minuten": katalog["benchmark_minuten"],
        "ehrlichkeitsregel": katalog["ehrlichkeitsregel"],
        "treiber": [
            {"id": qid, "text": fragen[qid]["text"],
             "antwort": fragen[qid]["stufen"][payload.answers[qid] - 1]}
            for qid in treiber
        ],
    }


# ---------------------------------------------------------------------------
# Stufe 2: Vollreport anfordern (22 Antworten + E-Mail + Bestaetigung)
# ---------------------------------------------------------------------------

class AnforderungIn(BaseModel):
    answers: Dict[str, int]
    email: EmailStr
    einwilligung: bool = False
    hp: str = ""
    ms: int = 0

    @field_validator("answers")
    @classmethod
    def _vollstaendig(cls, v: Dict[str, int]) -> Dict[str, int]:
        return _stufen_pruefen(v, set(all_question_ids("de")))

    @field_validator("einwilligung")
    @classmethod
    def _muss_zustimmen(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Ohne Einwilligung können wir Ihnen den Report nicht senden")
        return v


@router.get("/fragen", dependencies=[_limit("lesen", 60, 60)])
async def alle_fragen() -> Dict[str, Any]:
    """Kompletter Katalog fuer den oeffentlichen Fragebogen — ohne Gewichte."""
    katalog = load_katalog("de")
    return {
        "version": katalog["version"],
        "benchmark_minuten": katalog["benchmark_minuten"],
        "blocks": [
            {
                "id": b["id"],
                "titel": b["titel"],
                "questions": [
                    {"id": q["id"], "text": q["text"], "stufen": q["stufen"]}
                    for q in b["questions"]
                ],
            }
            for b in katalog["blocks"]
        ],
    }


@router.post("/anfordern", status_code=202, dependencies=[_limit("anfordern", 5, 600)])
async def anfordern(
    payload: AnforderungIn,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Antworten annehmen und einen Bestaetigungslink schicken.

    Der Report entsteht bewusst noch nicht: Erst der Klick in der Mail
    beweist, dass die Adresse dem Absender gehoert.
    """
    _pruefe_bot(payload.hp, payload.ms, _MIN_MS_VOLL)

    from models import Briefing, User

    email = str(payload.email).strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Ein User-Datensatz oeffnet keinen Login: der Zugang haengt an
        # core.whitelist, nicht an dieser Tabelle.
        user = User(email=email)
        db.add(user)
        db.flush()

    briefing = Briefing(
        user_id=user.id,
        lang="de",
        report_type="resilienz",
        answers=dict(payload.answers),
        status="unconfirmed",
        source="cyber_public",
        request_ip=(request.client.host if request.client else None),
        request_ua=request.headers.get("user-agent"),
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)

    _sende_bestaetigungsmail(email, briefing.id)
    log.info("[CYBER] Anforderung angenommen: briefing=%s (unbestätigt)", briefing.id)
    return {"status": "bestaetigung_gesendet"}


def _bestaetigungs_url(briefing_id: int) -> str:
    from services.email_templates import _brand

    basis = os.getenv("API_PUBLIC_URL") or ""
    if not basis:
        basis = str(_brand().get("app_url") or "").rstrip("/")
    return f"{basis}/api/cyber/bestaetigen?b={briefing_id}&t={_token_fuer(briefing_id)}"


def _sende_bestaetigungsmail(email: str, briefing_id: int) -> None:
    try:
        from gpt_analyze import _mask_email, _send_email_via_resend

        url = _bestaetigungs_url(briefing_id)
        body = (
            "<p>Guten Tag,</p>"
            "<p>Sie haben den Cyberangriffs-Check ausgefüllt. Ein Klick, und wir "
            "erstellen Ihren Report:</p>"
            f'<p><a href="{url}" style="display:inline-block;background:#2B6CB0;'
            'color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;'
            'font-weight:600">Report anfordern →</a></p>'
            "<p>Der Report kommt danach als PDF an diese Adresse. Er dauert in der "
            "Regel unter zwei Minuten.</p>"
            "<p>Haben Sie den Check nicht ausgefüllt? Dann ignorieren Sie diese "
            "E-Mail — ohne Ihren Klick passiert nichts, und der Vorgang verfällt "
            f"nach {_TOKEN_TTL_TAGE} Tagen.</p>"
            "<p>Freundliche Grüße<br>ki-sicherheit.jetzt</p>"
        )
        ok, err = _send_email_via_resend(
            email, "Bitte bestätigen: Ihr Cyberangriffs-Check", body,
        )
        log.info("[CYBER] Bestätigungsmail an %s: ok=%s err=%s", _mask_email(email), ok, err)
    except Exception as exc:
        log.warning("[CYBER] Bestätigungsmail fehlgeschlagen (briefing=%s): %s",
                    briefing_id, str(exc)[:200])


def _seite(titel: str, text: str, status_code: int = 200) -> Response:
    html = (
        '<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{titel}</title><style>"
        "body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#0f172a;"
        "background:#f6f9ff;margin:0;padding:48px 16px;line-height:1.55}"
        ".c{max-width:520px;margin:0 auto;background:#fff;border:1px solid #e6edf3;"
        "border-radius:12px;padding:28px}h1{font-size:20px;margin:0 0 12px;color:#0F1D35}"
        "p{font-size:15px}</style></head><body><div class=\"c\">"
        f"<h1>{titel}</h1><p>{text}</p></div></body></html>"
    )
    return Response(content=html, media_type="text/html; charset=utf-8", status_code=status_code)


@router.get("/bestaetigen", dependencies=[_limit("bestaetigen", 20, 60)])
async def bestaetigen(
    b: int,
    t: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Response:
    """Bestaetigungslink: gibt die Adresse frei und startet die Generierung."""
    from models import Briefing

    if not secrets.compare_digest(t, _token_fuer(b)):
        return _seite(
            "Dieser Link stimmt nicht",
            "Bitte öffnen Sie den Link aus der E-Mail unverändert, "
            "oder füllen Sie den Check erneut aus.",
            status_code=403,
        )

    treffer: Optional[Any] = (
        db.query(Briefing)
        .filter(Briefing.id == b, Briefing.report_type == "resilienz")
        .first()
    )
    if not treffer:
        return _seite(
            "Diesen Vorgang gibt es nicht",
            "Füllen Sie den Check bitte erneut aus.",
            status_code=404,
        )
    if treffer.status != "unconfirmed":
        # Zweiter Klick auf denselben Link — kein Fehler, aber auch kein
        # zweiter Report: das waere ein kostenloser Wiederholungshebel.
        return _seite(
            "Dieser Link wurde schon benutzt",
            "Ihr Report ist bereits unterwegs oder liegt in Ihrem Postfach.",
        )

    alter = datetime.now(timezone.utc) - _als_utc(treffer.created_at)
    if alter > timedelta(days=_TOKEN_TTL_TAGE):
        treffer.status = "failed"
        treffer.error = "Bestätigungslink abgelaufen"
        db.commit()
        return _seite(
            "Dieser Link ist abgelaufen",
            f"Bestätigungslinks gelten {_TOKEN_TTL_TAGE} Tage. "
            "Füllen Sie den Check bitte erneut aus.",
            status_code=410,
        )

    treffer.status = "accepted"
    treffer.accepted_at = datetime.now(timezone.utc)
    db.commit()

    from services.resilienz_pipeline import generate_resilienz_report

    background.add_task(generate_resilienz_report, treffer.id)
    log.info("[CYBER] Bestätigt: briefing=%s — Generierung gestartet", treffer.id)
    return _seite(
        "Danke — Ihr Report wird erstellt",
        "Er kommt in der Regel innerhalb von zwei Minuten als PDF an Ihre "
        "E-Mail-Adresse. Sie können dieses Fenster schließen.",
    )


def _als_utc(wert: Any) -> datetime:
    if not wert:
        return datetime.now(timezone.utc)
    stand: datetime = wert
    return stand.replace(tzinfo=timezone.utc) if stand.tzinfo is None else stand

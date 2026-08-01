# -*- coding: utf-8 -*-
"""KIS-1249 / Platin+++ Stufe 1: Maschinelles QA-Gate über dem fertigen Report.

Prüft nach Abschluss aller Heiler/Enforcer genau die Befund-Klassen, die
bisher nur manuelle PDF-Reviews fanden (Läufe 1119–1238). Nicht blockierend:
Befunde werden als WARNING geloggt und unter sections['_PLATIN_QA_FINDINGS']
abgelegt (→ Meta/Admin-Sichtbarkeit). Blockierend bleibt allein der
bestehende Hard-Stop.

Befund-Klassen:
  name_leak          Kundenname im Report (Sicherheits-Constraint)
  collapsed_kpi      Kennzahlen als kollabierter Fließtext ("ROI8 %nach…")
  truncated_text     Sektion endet mitten im Satz/Wort ("… (max.")
  raw_boolean        ": True"/": False" sichtbar
  english_badge      englische Badge-/Enum-Reste (ESSENTIAL, limited, …)
  visible_snake_case snake_case-Token im sichtbaren Text
  dsgvo_cap          mehr als 2 "(DSGVO-Vorbehalt …)"-Einschübe
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

log = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")

_COLLAPSED_KPI_RE = re.compile(
    r"(?:ROI|Break-Even|Zeitersparnis)\d[\d.,]*\s*(?:%|Monate|Std)"
)
_RAW_BOOL_RE = re.compile(r":\s*(?:True|False)\b")
_ENGLISH_BADGE_RE = re.compile(
    r"\b(?:ESSENTIAL|RECOMMENDED|ANALYSIS|COLLABORATION|AUTOMATION|PRODUCTIVITY)\b"
    r"|(?:RISIKO\s+limited)\b|(?:Komplexität:\s*(?:low|medium|high))\b"
)
# snake_case im sichtbaren Text — Whitelist für legitime technische Begriffe
_SNAKE_RE = re.compile(r"\b[a-z]{3,}_[a-z_]{3,}\b")
_SNAKE_WHITELIST = frozenset({
    "gpt_analyze", "run_id", "api_key", "max_tokens", "top_p",
})
# KIS-1257: URLs vor dem snake_case-Scan strippen — Quellen-Links wie
# bafa.de/…/unternehmensberatung_node.html sind legitimer Inhalt,
# kein Feld-Leak (False Positive, Lauf KIS-1240 Strategie S. 35).
_URL_RE = re.compile(r"(?:https?://|www\.)\S+")
_TRUNCATED_TAIL_RE = re.compile(
    r"\((?:max|ca|inkl|zzgl|bzw|z\.\s?B)\.\s*$"
)
_DSGVO_RE = re.compile(r"\((?:DSGVO|Datenschutz)-Vorbehalt[^)<]{0,80}\)")

# Nur sichtbare Kunden-Sektionen scannen — interne Keys (_-Präfix,
# Konfiguration, Meta) erzeugen sonst Fehlalarme.
_SKIP_KEY_PREFIXES = ("_", "LOGO_", "FOOTER_", "THEME_", "BUILD_")


def _visible_text(html: str) -> str:
    return _TAG_RE.sub(" ", html)


def scan_sections(sections: Dict[str, Any], answers: Dict[str, Any] | None = None) -> List[Dict[str, str]]:
    """Scannt alle sichtbaren String-Sektionen und liefert Befunde."""
    findings: List[Dict[str, str]] = []
    answers = answers or {}

    _name = str(answers.get("unternehmen_name") or "").strip()
    _dsgvo_total = 0

    # KIS-1279 (EN-Lauf 1138): Im EN-Report sind ESSENTIAL/RECOMMENDED/limited
    # regulärer englischer Text, kein Badge-Leak — der english_badge-Check ist
    # ein DE-Detektor und liefe bei lang=en nur in False Positives (und damit
    # in unnötige Heal-LLM-Calls).
    _lang_en = str(answers.get("lang") or answers.get("LANG") or "de").lower().startswith("en")

    for key, value in sections.items():
        if not isinstance(value, str) or len(value) < 20:
            continue
        if any(key.startswith(p) for p in _SKIP_KEY_PREFIXES):
            continue
        text = _visible_text(value)

        if _name and len(_name) > 3 and _name in text:
            findings.append({"type": "name_leak", "section": key,
                             "detail": f"Kundenname '{_name[:20]}…' sichtbar"})

        for m in _COLLAPSED_KPI_RE.finditer(text):
            findings.append({"type": "collapsed_kpi", "section": key,
                             "detail": m.group(0)[:60]})

        if _RAW_BOOL_RE.search(text):
            findings.append({"type": "raw_boolean", "section": key,
                             "detail": _RAW_BOOL_RE.search(text).group(0)})

        if not _lang_en:
            for m in _ENGLISH_BADGE_RE.finditer(text):
                findings.append({"type": "english_badge", "section": key,
                                 "detail": m.group(0)})

        for m in _SNAKE_RE.finditer(_URL_RE.sub(" ", text)):
            if m.group(0) not in _SNAKE_WHITELIST:
                findings.append({"type": "visible_snake_case", "section": key,
                                 "detail": m.group(0)})
                break  # ein Beleg pro Sektion reicht

        if _TRUNCATED_TAIL_RE.search(text.strip()[-80:]):
            findings.append({"type": "truncated_text", "section": key,
                             "detail": text.strip()[-60:]})

        _dsgvo_total += len(_DSGVO_RE.findall(text))

    if _dsgvo_total > 2:
        findings.append({"type": "dsgvo_cap", "section": "*",
                         "detail": f"{_dsgvo_total} Vorkommen (Cap: 2)"})

    return findings


def run_platin_qa(sections: Dict[str, Any], answers: Dict[str, Any] | None = None,
                  run_id: str = "") -> List[Dict[str, str]]:
    """Führt den Scan aus, loggt Befunde und legt sie in den Sektionen ab."""
    try:
        findings = scan_sections(sections, answers)
    except Exception as exc:  # pragma: no cover - QA darf nie den Report killen
        log.warning("[%s] [PLATIN-QA] Scan übersprungen: %s", run_id, exc)
        return []
    for f in findings[:40]:
        log.warning("[%s] [PLATIN-QA][%s] %s: %s",
                    run_id, f["type"], f["section"], f["detail"])
    if not findings:
        log.info("[%s] [PLATIN-QA] ✅ 0 Befunde — Platin+++-Gate sauber", run_id)
    sections["_PLATIN_QA_FINDINGS"] = findings
    return findings


# =========================================================================
# KIS-1250 / Stufe 2: Seitenfüllgrad am gerenderten PDF
# =========================================================================

# Deckblatt (Seite 1) und die letzte Seite (Impressum) dürfen luftig sein;
# alle anderen Seiten mit weniger extrahiertem Text gelten als "dünn" —
# exakt die Befund-Klasse der manuellen Reviews (Lauf 1238: 11 Seiten
# unter ~45 % Füllgrad).
THIN_PAGE_MIN_CHARS = 350


def scan_pdf_pages(pdf_bytes: bytes, run_id: str = "", label: str = "") -> List[Dict[str, str]]:
    """Extrahiert Text je Seite und meldet dünne Seiten (nicht blockierend)."""
    findings: List[Dict[str, str]] = []
    try:
        import io as _io
        from pypdf import PdfReader
        reader = PdfReader(_io.BytesIO(pdf_bytes))
        total = len(reader.pages)
        for idx, page in enumerate(reader.pages, start=1):
            if idx == 1 or idx == total:
                continue
            try:
                chars = len((page.extract_text() or "").strip())
            except Exception:
                continue
            if chars < THIN_PAGE_MIN_CHARS:
                findings.append({
                    "type": "thin_page", "section": f"{label or 'pdf'}:S.{idx}",
                    "detail": f"nur {chars} Zeichen extrahiert (Schwelle {THIN_PAGE_MIN_CHARS})",
                })
        for f in findings[:20]:
            log.warning("[%s] [PLATIN-QA][thin_page] %s: %s", run_id, f["section"], f["detail"])
        if not findings:
            log.info("[%s] [PLATIN-QA] ✅ %s: keine dünnen Seiten (%d Seiten)", run_id, label or "pdf", total)
    except ImportError:
        log.info("[%s] [PLATIN-QA] pypdf nicht installiert — Seiten-Scan übersprungen", run_id)
    except Exception as exc:  # pragma: no cover - QA darf nie den Versand killen
        log.warning("[%s] [PLATIN-QA] Seiten-Scan übersprungen: %s", run_id, exc)
    return findings

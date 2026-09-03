#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIS-1265: News-Entwurf für ki-sicherheit.jetzt/aktuell — Standalone-Lauf.

Warum ein Skript und nicht der Endpunkt /api/content/research-news:
Der Endpunkt läuft im Web-Container und ruft sechs Tavily-Suchen plus
LLM-Aufrufe synchron innerhalb eines asynchronen Handlers auf. Das
blockiert die Ereignisschleife für die gesamte Laufzeit — Status-Abfragen,
Absenden und Login hängen solange. Dieses Skript läuft stattdessen als
GitHub-Actions-Job außerhalb von Railway; die Produktion wird nicht berührt.

Ablauf: Tavily-Recherche → LLM-Zusammenfassung → HTML-Schnipsel →
Datei (Artefakt) → Mail an ADMIN_NOTIFY_EMAIL.

Fehlende Schlüssel sind kein Fehler: Ohne TAVILY_API_KEY oder
OPENAI_API_KEY endet der Lauf mit Hinweis und Exit 0, damit der Cron
nicht wöchentlich rot ist, solange die Secrets fehlen.

Usage:
  python scripts/news_draft.py [--out news_draft.html] [--no-mail]
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# settings.py verlangt JWT_SECRET und DATABASE_URL beim Import — im
# CI-Job gibt es weder Login noch Datenbank. Platzhalter genügen; nichts
# davon wird für Recherche, LLM oder Mailversand benutzt.
os.environ.setdefault("JWT_SECRET", "news-draft-ci-placeholder")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


def _notice(msg: str) -> None:
    print(f"::notice::{msg}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="news_draft.html")
    ap.add_argument("--no-mail", action="store_true")
    args = ap.parse_args()

    if not os.getenv("TAVILY_API_KEY"):
        _notice("News-Entwurf übersprungen: TAVILY_API_KEY fehlt (Secret setzen).")
        return 0
    if not os.getenv("OPENAI_API_KEY"):
        _notice("News-Entwurf übersprungen: OPENAI_API_KEY fehlt (Secret setzen).")
        return 0

    from services.news_researcher import (
        generate_html_snippets,
        research_news,
        send_news_draft,
        summarize_news,
    )

    raw = research_news()
    print(f"Tavily: {len(raw)} Rohtreffer")
    if not raw:
        _notice("News-Entwurf: keine relevanten Treffer in den letzten 30 Tagen.")
        return 0

    items = summarize_news(raw)
    print(f"LLM: {len(items)} Meldungen nach Zusammenfassung")
    if not items:
        _notice("News-Entwurf: LLM-Zusammenfassung ergab keine Meldungen.")
        return 0

    html = generate_html_snippets(items)
    out = Path(args.out)
    out.write_text(html, encoding="utf-8")
    print(f"Entwurf geschrieben: {out} ({len(html)} Zeichen)")

    summary = Path(os.getenv("GITHUB_STEP_SUMMARY", "")) if os.getenv("GITHUB_STEP_SUMMARY") else None
    if summary:
        with summary.open("a", encoding="utf-8") as fh:
            fh.write(f"# 📰 News-Entwurf — {datetime.now():%d.%m.%Y}\n\n")
            fh.write(f"{len(items)} Meldung(en):\n\n")
            for it in items:
                fh.write(f"- **[{it.get('category', '?')}]** {it.get('title', '')}\n")
            fh.write("\nDer HTML-Entwurf liegt als Artefakt `news-draft` bei.\n")

    if args.no_mail:
        _notice("Mailversand per --no-mail übersprungen.")
        return 0
    if not os.getenv("ADMIN_NOTIFY_EMAIL"):
        _notice("Mail übersprungen: ADMIN_NOTIFY_EMAIL fehlt — Entwurf liegt als Artefakt bei.")
        return 0
    if not (os.getenv("RESEND_API_KEY") and os.getenv("RESEND_FROM")):
        _notice("Mail übersprungen: RESEND_API_KEY/RESEND_FROM fehlen — Entwurf liegt als Artefakt bei.")
        return 0

    asyncio.run(send_news_draft(html, items))
    _notice(f"News-Entwurf mit {len(items)} Meldung(en) per Mail versendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

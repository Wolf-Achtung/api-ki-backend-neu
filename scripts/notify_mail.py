#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""KIS-1265: Radar-Bericht per Mail — für CI-Jobs ohne Backend-Importe.

Die Radare öffnen Issues, aber ein Issue-Kommentar von github-actions
erreicht niemanden, der dem Issue nicht folgt. Wolf hatte deshalb seit
Juli wöchentliche Berichte in Issue #1107, ohne je eine Nachricht zu
bekommen. Dieses Skript schickt den Bericht zusätzlich per Mail (Resend,
REST direkt) — ohne settings.py, ohne Datenbank, nur `requests`.

Fehlende Secrets sind kein Fehler: Ohne RESEND_API_KEY, RESEND_FROM oder
Empfänger endet das Skript mit Hinweis und Exit 0.

Usage:
  python scripts/notify_mail.py --subject "…" --file radar_report.md
                                [--to mail@…] [--only-if-findings]
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path

RESEND_ENDPOINT = "https://api.resend.com/emails"


def markdown_to_html(md: str) -> str:
    """Kleiner Konverter für die Radar-Berichte: Überschriften, Tabellen,
    Listen, Fettdruck, Links. Kein Markdown-Paket nötig."""
    lines = md.splitlines()
    out: list[str] = []
    table: list[str] = []

    def flush_table() -> None:
        if not table:
            return
        rows = [r for r in table if not re.match(r"^\s*\|?\s*-{3,}", r)]
        out.append('<table style="border-collapse:collapse;font-size:13px">')
        for i, row in enumerate(rows):
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            out.append(
                "<tr>" + "".join(
                    f'<{tag} style="border:1px solid #e2e8f0;padding:4px 8px;text-align:left">'
                    f"{_inline(c)}</{tag}>" for c in cells
                ) + "</tr>"
            )
        out.append("</table>")
        table.clear()

    for line in lines:
        if line.strip().startswith("|"):
            table.append(line)
            continue
        flush_table()
        s = line.strip()
        if not s:
            continue
        if s.startswith("# "):
            out.append(f"<h2>{_inline(s[2:])}</h2>")
        elif s.startswith("## "):
            out.append(f"<h3>{_inline(s[3:])}</h3>")
        elif s.startswith("- "):
            out.append(f"<div>• {_inline(s[2:])}</div>")
        elif s.startswith("_") and s.endswith("_"):
            out.append(f'<p style="color:#64748b;font-size:12px">{_inline(s[1:-1])}</p>')
        else:
            out.append(f"<p>{_inline(s)}</p>")
    flush_table()
    return "\n".join(out)


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"(https?://[^\s<)]+)", r'<a href="\1">\1</a>', text)
    return text


def has_findings(md: str) -> bool:
    return bool(re.search(r"\*\*\d+ (?:Befund|Kandidat)", md))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--to", default=os.getenv("ADMIN_NOTIFY_EMAIL", ""))
    ap.add_argument("--only-if-findings", action="store_true")
    args = ap.parse_args()

    md = Path(args.file).read_text(encoding="utf-8")
    if args.only_if_findings and not has_findings(md):
        print("::notice::Keine Befunde — keine Mail.")
        return 0

    api_key = os.getenv("RESEND_API_KEY", "")
    sender = os.getenv("RESEND_FROM", "")
    if not (api_key and sender and args.to):
        print("::notice::Mail übersprungen: RESEND_API_KEY, RESEND_FROM oder Empfänger fehlt.")
        return 0

    import requests

    body_html = (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
        'color:#0f172a;max-width:760px;line-height:1.5">'
        + markdown_to_html(md)
        + "</div>"
    )
    resp = requests.post(
        RESEND_ENDPOINT,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"from": sender, "to": [args.to], "subject": args.subject,
              "html": body_html, "text": md},
        timeout=20,
    )
    if resp.status_code >= 300:
        print(f"::warning::Mailversand fehlgeschlagen: HTTP {resp.status_code} {resp.text[:200]}")
        return 0
    print(f"::notice::Bericht per Mail an {args.to} gesendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testlauf aus einem Profil starten (KIS-1308).

Schickt ein Profil im Format der Gold-Profile an
``POST /api/admin/testrun/profile``. Vorher prüft das Skript das Profil lokal
mit derselben Regel wie der Endpunkt, damit ein Tippfehler nicht erst in
Produktion auffällt.

Beispiel:

    export STRATEGY_ADMIN_KEY=…
    python scripts/testlauf_profil.py data/test_profiles_gold/medien_verlag_bayern_kmu_testlauf.json \
        --email wolf@hohl.rocks

``--check`` prüft nur, ohne zu senden. ``--base-url`` überschreibt die
Produktions-Adresse. Vor dem Start ``…/api/healthz`` prüfen — ein Deploy
mitten in der Generierung bricht sie ab.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://api-ki-backend-neu-production.up.railway.app"


def main() -> int:
    ap = argparse.ArgumentParser(description="Testlauf aus einem Profil starten")
    ap.add_argument("profil", help="Pfad zur Profil-JSON (answers + strategy_answers)")
    ap.add_argument("--email", default=None, help="Empfänger der Report-Mails (sonst Wegwerf-Adresse)")
    ap.add_argument("--base-url", default=os.getenv("KIS_BASE_URL", BASE_URL))
    ap.add_argument("--check", action="store_true", help="nur prüfen, nicht senden")
    ap.add_argument("--no-strategy", action="store_true", help="ohne Fragebogen 2 / Strategiebericht")
    args = ap.parse_args()

    profil = json.loads(Path(args.profil).read_text(encoding="utf-8"))
    answers = profil.get("answers") or {}
    strategy = None if args.no_strategy else profil.get("strategy_answers")

    sys.path.insert(0, str(ROOT))
    # Lokal ohne App-Settings (JWT_SECRET, DATABASE_URL) prüft profil_pruefen
    # nur Fragebogen 1; Fragebogen 2 prüft dann der Endpunkt selbst.
    from routes.admin_testrun import profil_pruefen

    fehler = profil_pruefen(answers, strategy)
    if fehler:
        print("Profil nicht einspielbar:")
        for f in fehler:
            print("  -", f)
        return 1
    print(f"Profil geprüft: {profil.get('profile_id', Path(args.profil).stem)} — "
          f"{len(answers)} Antworten, FB2: {'ja' if strategy else 'nein'}")
    if args.check:
        return 0

    key = os.getenv("STRATEGY_ADMIN_KEY", "")
    if not key:
        print("STRATEGY_ADMIN_KEY fehlt in der Umgebung.")
        return 2
    body = {
        "answers": answers,
        "strategy_answers": strategy,
        "email_override": args.email,
        "lang": profil.get("lang", "de"),
        "trigger_strategy": strategy is not None,
    }
    req = urllib.request.Request(
        f"{args.base_url.rstrip('/')}/api/admin/testrun/profile",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Admin-Key": key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            antwort = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"Fehler {exc.code}: {exc.read().decode('utf-8', 'replace')[:800]}")
        return 3
    print(json.dumps(antwort, ensure_ascii=False, indent=2))
    print(f"\nBriefing {antwort.get('new_briefing_id')} läuft — im PDF heißt es {antwort.get('report_display_id')}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

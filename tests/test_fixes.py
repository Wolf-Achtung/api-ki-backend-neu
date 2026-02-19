#!/usr/bin/env python3
"""
KI-Sicherheit.jetzt — Patch-Validation & Briefing-Trigger
===========================================================
Datum: 2026-02-19
Fixes: FIX-STRIP, FIX-STRIP-QW, FIX-NUM-DIAG

USAGE in Codespace Terminal:
  # 1. Patches validieren (kein DB nötig):
  python test_fixes.py --validate

  # 2. Briefing 710 erneut triggern:
  python test_fixes.py --rerun 710

  # 3. Beliebiges Briefing triggern:
  python test_fixes.py --rerun 42

  # 4. Logs nach dem Run prüfen:
  python test_fixes.py --check-logs

  # 5. Alles auf einmal (validate + rerun + check):
  python test_fixes.py --full 710
"""

import argparse
import os
import re
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# ANSI-Farben
# ---------------------------------------------------------------------------
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

def ok(msg):   print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg): print(f"  {RED}❌ {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}⚠️  {msg}{RESET}")
def info(msg): print(f"  {CYAN}ℹ️  {msg}{RESET}")

# ---------------------------------------------------------------------------
# 1. PATCH VALIDATION (kein DB, kein Server nötig)
# ---------------------------------------------------------------------------
def validate_patches():
    """Prüft ob die gepatchten Dateien korrekt sind."""
    print(f"\n{BOLD}{'='*60}")
    print(f"  PATCH VALIDATION")
    print(f"{'='*60}{RESET}\n")

    errors = 0

    # --- anthropic_client.py ---
    print(f"{BOLD}[1/3] anthropic_client.py{RESET}")

    ac_path = _find_file("services/anthropic_client.py")
    if not ac_path:
        fail("anthropic_client.py nicht gefunden!")
        errors += 1
    else:
        with open(ac_path, "r", encoding="utf-8") as f:
            ac_code = f.read()

        # Syntax-Check
        try:
            compile(ac_code, ac_path, "exec")
            ok("Syntax OK")
        except SyntaxError as e:
            fail(f"Syntax-Fehler: {e}")
            errors += 1

        # FIX-STRIP vorhanden?
        strip_count = ac_code.count(".strip()")
        if strip_count >= 5:
            ok(f".strip() gefunden: {strip_count}x (erwartet ≥5)")
        else:
            fail(f".strip() nur {strip_count}x gefunden (erwartet ≥5)")
            errors += 1

        # Kein ungeschütztes os.getenv für Modelle?
        # Suche os.getenv("ANTHROPIC_MODEL... ohne .strip()
        unsafe_envs = re.findall(
            r'os\.getenv\("ANTHROPIC_MODEL[^)]*\)(?!\.strip)',
            ac_code
        )
        if not unsafe_envs:
            ok("Alle ANTHROPIC_MODEL ENV-Reads haben .strip()")
        else:
            warn(f"{len(unsafe_envs)} ENV-Reads ohne .strip() gefunden:")
            for ue in unsafe_envs[:5]:
                print(f"      {ue[:80]}")

    # --- gpt_analyze.py ---
    print(f"\n{BOLD}[2/3] gpt_analyze.py{RESET}")

    ga_path = _find_file("gpt_analyze.py")
    if not ga_path:
        fail("gpt_analyze.py nicht gefunden!")
        errors += 1
    else:
        with open(ga_path, "r", encoding="utf-8") as f:
            ga_code = f.read()

        # Syntax-Check
        try:
            compile(ga_code, ga_path, "exec")
            ok("Syntax OK")
        except SyntaxError as e:
            fail(f"Syntax-Fehler: {e}")
            errors += 1

        # FIX-STRIP-QW vorhanden?
        if "FIX-STRIP-QW" in ga_code:
            ok("FIX-STRIP-QW (JSON-Prefix-Bereinigung) vorhanden")
        else:
            fail("FIX-STRIP-QW nicht gefunden — Quick Wins JSON-Fix fehlt!")
            errors += 1

        # Code-Fence-Stripping vorhanden?
        if "```(?:json|JSON)" in ga_code or "fence_match" in ga_code:
            ok("Code-Fence-Stripping vorhanden")
        else:
            fail("Code-Fence-Stripping nicht gefunden")
            errors += 1

        # FIX-NUM-DIAG vorhanden?
        if "FIX-NUM-DIAG" in ga_code:
            ok("FIX-NUM-DIAG (Numerical Diagnostik-Logging) vorhanden")
        else:
            fail("FIX-NUM-DIAG nicht gefunden")
            errors += 1

    # --- prompt_framework.md ---
    print(f"\n{BOLD}[3/3] prompt_framework.md{RESET}")

    pf_path = _find_file("prompts/de/prompt_framework.md")
    if not pf_path:
        warn("prompt_framework.md nicht unter prompts/de/ gefunden — manuell prüfen")
    else:
        with open(pf_path, "r", encoding="utf-8") as f:
            pf_content = f.read()

        # Leak-Check
        if "platzhalter" in pf_content.lower():
            fail("'Platzhalter' noch vorhanden — Leak-Sanitizer wird blocken!")
            errors += 1
        else:
            ok("Kein 'Platzhalter' mehr (Leak-Sanitizer wird nicht triggern)")

        # UTF-8 Check
        if "Ã" in pf_content or "â" in pf_content:
            fail("Kaputte UTF-8-Zeichen gefunden (Ã, â)")
            errors += 1
        else:
            ok("UTF-8-Encoding sauber")

    # --- Zusammenfassung ---
    print(f"\n{BOLD}{'='*60}")
    if errors == 0:
        print(f"  {GREEN}ALLE PATCHES VALIDIERT ✅  — Ready to deploy{RESET}")
    else:
        print(f"  {RED}{errors} FEHLER GEFUNDEN ❌  — Bitte korrigieren{RESET}")
    print(f"{'='*60}{RESET}\n")

    return errors == 0


def _find_file(relative_path: str) -> str | None:
    """Sucht eine Datei in typischen Projekt-Verzeichnissen."""
    candidates = [
        Path(relative_path),                          # Relativ zum CWD
        Path("/app") / relative_path,                 # Railway Container
        Path(".") / relative_path,                    # CWD
        Path("..") / relative_path,                   # Parent
        Path("/workspaces") / "**" / relative_path,   # Codespace
    ]

    # Erst direkte Pfade
    for p in candidates[:4]:
        if p.exists():
            return str(p)

    # Dann globale Suche im Workspace
    for base in [Path("."), Path("/workspaces"), Path("/app")]:
        if base.exists():
            matches = list(base.rglob(Path(relative_path).name))
            # Bevorzuge Pfade die den vollen relative_path enthalten
            for m in matches:
                if relative_path.replace("/", os.sep) in str(m):
                    return str(m)
            if matches:
                return str(matches[0])

    return None


# ---------------------------------------------------------------------------
# 2. BRIEFING RERUN TRIGGER
# ---------------------------------------------------------------------------
def rerun_briefing(briefing_id: int):
    """Triggert ein Briefing erneut über die DB."""
    print(f"\n{BOLD}{'='*60}")
    print(f"  BRIEFING {briefing_id} RERUN")
    print(f"{'='*60}{RESET}\n")

    # Versuche Import der App-Komponenten
    try:
        sys.path.insert(0, str(Path(".").resolve()))
        sys.path.insert(0, "/app")

        from database import get_db, SessionLocal
        from gpt_analyze import run_briefing_pipeline

        info(f"Starte Pipeline für Briefing {briefing_id}...")
        print()

        db = SessionLocal()
        try:
            start = time.time()
            run_briefing_pipeline(
                db=db,
                briefing_id=briefing_id,
                email=None,
                run_id=f"test-fix-{datetime.now().strftime('%H%M%S')}",
            )
            elapsed = time.time() - start
            ok(f"Pipeline erfolgreich beendet in {elapsed:.1f}s")
        except RuntimeError as e:
            elapsed = time.time() - start
            if "HARD STOP" in str(e):
                fail(f"HARD STOP nach {elapsed:.1f}s: {e}")
                print(f"\n  {YELLOW}→ Prüfe Logs mit: python test_fixes.py --check-logs{RESET}")
            else:
                fail(f"RuntimeError nach {elapsed:.1f}s: {e}")
        except Exception as e:
            fail(f"Fehler: {type(e).__name__}: {e}")
        finally:
            db.close()

    except ImportError as e:
        warn(f"Kann App-Module nicht importieren: {e}")
        print()
        info("Alternative: Briefing per API oder direkt in Railway retriggern:")
        print()
        _print_alternative_triggers(briefing_id)


def _print_alternative_triggers(briefing_id: int):
    """Zeigt alternative Wege zum Triggern."""
    api_base = os.getenv("API_BASE_URL", "https://ki-sicherheit-jetzt-production.up.railway.app")

    print(f"""  {BOLD}Option A — Per SQL (Railway DB Console):{RESET}
  UPDATE briefings
  SET status = 'pending', updated_at = NOW()
  WHERE id = {briefing_id};

  {BOLD}Option B — Per cURL (falls API-Endpoint existiert):{RESET}
  curl -X POST {api_base}/api/briefings/{briefing_id}/rerun \\
    -H "Authorization: Bearer $API_TOKEN"

  {BOLD}Option C — Per Railway CLI:{RESET}
  railway run python -c "
from database import SessionLocal
from gpt_analyze import run_briefing_pipeline
db = SessionLocal()
run_briefing_pipeline(db, {briefing_id}, run_id='test-fix')
db.close()
"

  {BOLD}Option D — Per Python in Codespace (mit DB-Zugang):{RESET}
  export DATABASE_URL='postgresql://...'  # Railway DB URL
  python -c "
import os; os.environ.setdefault('DATABASE_URL', os.environ['DATABASE_URL'])
from database import SessionLocal
from gpt_analyze import run_briefing_pipeline
db = SessionLocal()
run_briefing_pipeline(db, {briefing_id}, run_id='test-fix')
db.close()
"
""")


# ---------------------------------------------------------------------------
# 3. LOG CHECKER
# ---------------------------------------------------------------------------
def check_logs(log_source: str = None):
    """Prüft Railway-Logs auf erwartete Fix-Indikatoren."""
    print(f"\n{BOLD}{'='*60}")
    print(f"  LOG CHECK")
    print(f"{'='*60}{RESET}\n")

    log_text = ""

    if log_source and Path(log_source).exists():
        info(f"Lese lokale Logdatei: {log_source}")
        with open(log_source, "r", encoding="utf-8", errors="replace") as f:
            log_text = f.read()
    else:
        # Versuche Railway CLI
        info("Versuche Railway Logs zu lesen...")
        try:
            result = subprocess.run(
                ["railway", "logs", "--tail", "500"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                log_text = result.stdout
                ok(f"Railway Logs geladen ({len(log_text)} chars)")
            else:
                warn("Railway CLI nicht verfügbar")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            warn("Railway CLI nicht installiert oder Timeout")

    if not log_text:
        info("Kein Log-Input. Nutze eine der folgenden Optionen:")
        print(f"""
  {BOLD}Option A — Log-Datei angeben:{RESET}
  python test_fixes.py --check-logs --log-file railway_logs.txt

  {BOLD}Option B — Railway Logs exportieren:{RESET}
  railway logs --tail 1000 > railway_logs.txt
  python test_fixes.py --check-logs --log-file railway_logs.txt

  {BOLD}Option C — Railway Dashboard:{RESET}
  Logs manuell in Railway Dashboard prüfen.
  Suche nach den folgenden Patterns:
""")
        _print_expected_patterns()
        return

    _analyze_logs(log_text)


def _analyze_logs(log_text: str):
    """Analysiert Log-Text auf Fix-Indikatoren."""

    print(f"\n  {BOLD}--- Erwartete Verbesserungen ---{RESET}")

    # FIX-STRIP: Kein 404 mehr
    count_404 = log_text.count("404 Not Found")
    if count_404 == 0:
        ok("Kein '404 Not Found' — ENV-Newline-Fix wirkt")
    else:
        fail(f"Noch {count_404}x '404 Not Found' — ANTHROPIC_MODEL_* ENV prüfen!")
        # Zeige welche Sections betroffen sind
        for line in log_text.split("\n"):
            if "404 Not Found" in line:
                print(f"      {line.strip()[:120]}")

    # FIX-STRIP-QW: JSON-Prefix bereinigt
    if "FIX-STRIP-QW" in log_text:
        ok("FIX-STRIP-QW aktiv — JSON-Prefix wird bereinigt")
        for line in log_text.split("\n"):
            if "FIX-STRIP-QW" in line:
                print(f"      {line.strip()[:120]}")
    else:
        warn("Kein FIX-STRIP-QW Log — entweder kein JSON-Prefix nötig oder Fix nicht deployed")

    # Quick Wins Fallback
    qw_fallback = log_text.count("QW-FALLBACK-TRACKED")
    if qw_fallback == 0:
        ok("Kein Quick Wins Fallback — Hauptursache des HARD STOP behoben")
    else:
        fail(f"Quick Wins Fallback noch {qw_fallback}x — Quick Wins werden noch nicht als JSON erkannt")

    # HARD STOP
    hard_stops = log_text.count("HARD STOP")
    if hard_stops == 0:
        ok("Kein HARD STOP — Pipeline läuft durch")
    else:
        fail(f"Noch {hard_stops}x HARD STOP")
        for line in log_text.split("\n"):
            if "HARD STOP" in line:
                print(f"      {line.strip()[:120]}")

    # RELEASE-STRICT Blocking
    blocking = log_text.count("Blocking due to fallbacks")
    if blocking == 0:
        ok("Kein RELEASE-STRICT Blocking")
    else:
        fail(f"Noch {blocking}x RELEASE-STRICT Blocking")

    # FIX-NUM-DIAG: Diagnostik vorhanden?
    if "FIX-NUM-DIAG" in log_text:
        ok("FIX-NUM-DIAG aktiv — Numerische Issues werden geloggt:")
        for line in log_text.split("\n"):
            if "FIX-NUM-DIAG" in line:
                print(f"      {line.strip()[:140]}")
    else:
        warn("Kein FIX-NUM-DIAG Log — entweder kein DoD-Fail oder Fix nicht deployed")

    # Prompt Framework Leak
    pf_leak = log_text.count("prompt_framework still has leaks")
    if pf_leak == 0:
        ok("Kein Prompt-Framework Leak — 'Platzhalter'-Fix wirkt")
    else:
        fail(f"Prompt-Framework Leak noch {pf_leak}x — prompt_framework.md prüfen")

    # Opus-Calls erfolgreich?
    opus_ok = log_text.count("claude-opus-4-6' for section")
    opus_200 = len(re.findall(r"claude-opus-4-6.*200 OK", log_text))
    if opus_ok > 0:
        ok(f"Opus-4.6 Routing: {opus_ok} Sections, davon {opus_200} mit 200 OK")
    else:
        warn("Keine Opus-4.6 Calls gefunden")

    print(f"\n  {BOLD}--- Zusammenfassung ---{RESET}")
    critical_ok = (count_404 == 0 and qw_fallback == 0 and hard_stops == 0)
    if critical_ok:
        print(f"\n  {GREEN}{BOLD}🎉 ALLE KRITISCHEN FIXES WIRKEN — Pipeline sollte durchlaufen{RESET}\n")
    else:
        print(f"\n  {RED}{BOLD}⚠️  Noch Probleme vorhanden — siehe Details oben{RESET}\n")


def _print_expected_patterns():
    """Zeigt erwartete Log-Patterns."""
    print(f"""
  {GREEN}SOLLTE ERSCHEINEN (nach Fix):{RESET}
    [FIX-STRIP-QW] Removed 'json' prefix...
    [FIX-499-QW] JSON response detected...
    [FIX-510-QW] ✅ Premium JSON→HTML...
    [FIX-NUM-DIAG] Issue 1: type=..., section=...

  {RED}SOLLTE NICHT MEHR ERSCHEINEN:{RESET}
    HTTP/1.1 404 Not Found
    [QW-FALLBACK-TRACKED] Fallback count incremented
    [RELEASE-STRICT] Blocking due to fallbacks
    HARD STOP: Fallbacks used (strict mode)
    prompt_framework still has leaks
""")


# ---------------------------------------------------------------------------
# 4. ENV-VARIABLE CHECK
# ---------------------------------------------------------------------------
def check_env_vars():
    """Prüft ob Railway ENV-Variablen sauber sind."""
    print(f"\n{BOLD}{'='*60}")
    print(f"  ENV-VARIABLEN CHECK")
    print(f"{'='*60}{RESET}\n")

    model_vars = [
        "ANTHROPIC_MODEL",
        "ANTHROPIC_MODEL_OPUS",
        "ANTHROPIC_MODEL_EXECUTIVE_SUMMARY",
        "ANTHROPIC_MODEL_GAMECHANGER",
        "ANTHROPIC_MODEL_RECOMMENDATIONS",
        "ANTHROPIC_MODEL_RISKS",
        "ANTHROPIC_MODEL_BUSINESS_CASE",
        "ANTHROPIC_MODEL_STRATEGIE_GOVERNANCE",
        "ANTHROPIC_MODEL_FALLBACK",
        "ANTHROPIC_MODEL_DEFAULT",
    ]

    found = 0
    for var in model_vars:
        val = os.getenv(var)
        if val is not None:
            found += 1
            raw_repr = repr(val)
            stripped = val.strip()
            if val != stripped:
                fail(f"{var} = {raw_repr} ← TRAILING WHITESPACE/NEWLINE!")
                info(f"  Bereinigt wäre: '{stripped}'")
            elif not stripped:
                warn(f"{var} ist leer")
            else:
                ok(f"{var} = '{stripped}'")

    if found == 0:
        warn("Keine ANTHROPIC_MODEL_* ENV-Variablen gesetzt.")
        info("Normal in Codespace — in Railway sollten sie gesetzt sein.")
        info("Prüfe mit: railway variables")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="KI-Sicherheit.jetzt — Patch Validation & Briefing Trigger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python test_fixes.py --validate                   # Nur Patches prüfen
  python test_fixes.py --rerun 710                  # Briefing 710 nochmal laufen lassen
  python test_fixes.py --check-logs                 # Railway-Logs analysieren
  python test_fixes.py --check-logs --log-file x.log  # Lokale Logdatei analysieren
  python test_fixes.py --check-env                  # ENV-Variablen prüfen
  python test_fixes.py --full 710                   # Alles: validate → rerun → check
        """
    )
    parser.add_argument("--validate", action="store_true", help="Patches validieren")
    parser.add_argument("--rerun", type=int, metavar="BRIEFING_ID", help="Briefing erneut triggern")
    parser.add_argument("--check-logs", action="store_true", help="Logs auf Fix-Indikatoren prüfen")
    parser.add_argument("--log-file", type=str, help="Lokale Log-Datei statt Railway CLI")
    parser.add_argument("--check-env", action="store_true", help="ENV-Variablen prüfen")
    parser.add_argument("--full", type=int, metavar="BRIEFING_ID", help="Alles: validate + rerun + check")

    args = parser.parse_args()

    if not any([args.validate, args.rerun, args.check_logs, args.check_env, args.full]):
        parser.print_help()
        print(f"\n  {YELLOW}Tipp: Starte mit --validate um die Patches zu prüfen.{RESET}\n")
        return

    if args.full:
        # Alles
        valid = validate_patches()
        if valid:
            check_env_vars()
            rerun_briefing(args.full)
            print(f"\n  {CYAN}Warte 30s auf Log-Output...{RESET}")
            time.sleep(30)
            check_logs(args.log_file)
        else:
            fail("Patches nicht valide — Rerun abgebrochen.")
        return

    if args.validate:
        validate_patches()

    if args.check_env:
        check_env_vars()

    if args.rerun:
        rerun_briefing(args.rerun)

    if args.check_logs:
        check_logs(args.log_file)


if __name__ == "__main__":
    main()

# Security Inventory — api-ki-backend-neu

**Datum:** 2026-04-26
**Modus:** Schnell-Bestandsaufnahme (kein Fix durchgeführt)
**Stack:** FastAPI (Python 3.11), SQLAlchemy/Postgres, Uvicorn, OpenAI/Anthropic/Tavily/Perplexity-Integrationen
**Repo-Status:** Private, **aktiv** (letzter Push 2026-04-24, 134 Commits in History), **Production-deployed** (`https://api-ki-backend-neu-production.up.railway.app` — Railway, Procfile vorhanden, README dokumentiert Release R1)

## 🚦 Risiko-Ampel

**Gesamt:** 🔴 **ROT**

Begründung: Wolfs Production-`STRATEGY_ADMIN_KEY` (URL-encoded: `S5vI07d8c6jP7u%2B2bmZfD3yQ9z1454lX7F6nUw2h45XQbM1A45`) ist sowohl im aktuellen Tree (`scripts/testrun_team_berlin.sh:20`) als auch in der Git-History des privaten Repos hardcoded — er gewährt Vollzugriff auf produktive Admin-Endpunkte (`/api/admin/testrun/replay`, `/api/admin/strategy/...`).

## 🔍 Schnell-Scan Ergebnisse

| Layer | Ergebnis |
|---|---|
| Secrets HEAD | ❌ **1 CRITICAL** (Admin-Key in `scripts/testrun_team_berlin.sh:20`) + 3 False Positives (gitleaks) |
| Secrets History | ❌ **1 CRITICAL** (gleicher Admin-Key, eingeführt in commit `c17420f`, PR #931) |
| Dependency-CVEs | ⚠️ **4** (Pillow 11.3.0: 2 CVEs, Starlette 0.46.2: 2 CVEs) — keine als "Critical" eingestuft |
| .env im Tree | ✅ nein (`.env`/`.env.local` korrekt ignoriert) |
| .gitignore vorhanden | ✅ ja, enthält `.env` und `.env.local` |
| CORS-Allowlist | ✅ restriktiv (Whitelist von `ki-sicherheit.jetzt`-Domains; `*` nur als opt-in via `CORS_ALLOW_ANY=1` und dann ohne Credentials) |
| Hardcoded Secrets im Code | ❌ **1 gefunden** (siehe oben — Admin-Key); keine OpenAI/Anthropic/Stripe-Keys |

## 🚨 Stoppschilder (zutreffend)

- [x] **Wolfs Admin-Key `S5vI07d8c6jP7u+2bmZfD3yQ9z1454lX7F6nUw2h45XQbM1A45` in HEAD UND History.**
  Datei: `scripts/testrun_team_berlin.sh:20`
  Erstmals committed in `c17420f` (Merge PR #931 — `claude/remove-sonnet-qr-clicks-bo1Pm`)
  Verwendet gegen Production-URL `https://api-ki-backend-neu-production.up.railway.app`
  Schützt Admin-Endpunkte in `routes/admin_testrun.py` und `routes/strategy.py` (Validation gegen `STRATEGY_ADMIN_KEY` env-var) — Kompromittierung ermöglicht Daten-Replay, Forced Re-Generation und Strategy-Manipulation in Production.

- [ ] Live-API-Key (Anthropic/OpenAI/Stripe/Railway/AWS) — nicht gefunden
- [ ] Hardcoded Production-DB-Credentials — nicht gefunden
- [ ] JWT-Secret hardcoded — nicht gefunden (`settings.py` lädt aus `JWT_SECRET` env-var, validiert nicht-leer)
- [ ] CORS `*` UND User-Daten — nicht zutreffend (CORS ist restriktiv per Default)
- [ ] CVE Severity "Critical" — nicht zutreffend (gefundene CVEs sind High/Medium-Klasse)

## 🟡 Aufmerksamkeitspunkte (für späteren Voll-Audit)

- **Pillow 11.3.0** → CVE-2026-25990 (out-of-bounds write bei PSD-Decoding, fix: 12.1.1) und CVE-2026-40192 (decompression bomb bei FITS, fix: 12.2.0). Pillow wird laut `requirements.txt` für WebP-Logo-Optimierung verwendet — Angriffsoberfläche hängt davon ab, ob User-Uploads verarbeitet werden.
- **Starlette 0.46.2** (transitiv via FastAPI) → CVE-2025-54121 (DoS via large multipart spool, fix: 0.47.2) und CVE-2025-62727 (CPU-DoS via crafted Range-Header in `FileResponse`, fix: 0.49.1) — beide unauthenticated DoS, in einem öffentlich erreichbaren Prod-Service relevant.
- **Admin-Auth-Pattern via Query-String** (`?admin_key=...`): Admin-Keys werden als URL-Query-Parameter übergeben (`routes/admin_testrun.py`, `routes/strategy.py`) — landen damit potenziell in Server-Logs, Browser-History, Railway-Request-Logs, Referer-Headers. Header-basierte Übermittlung wäre sicherer.
- **`SMTP_HOST`, `SMTP_FROM`, Domain-Whitelist** in `.env.example` enthalten echte Produktionswerte (nicht Secrets, aber Recon-Material). Akzeptabel für ein Beispiel-File, aber erwähnenswert.
- **Sehr großes Repo / viel Audit-Material**: Tree enthält Dutzende `AUDIT_*.md`, `DIAGNOSE_*.md`, `FIX_*` und `*.bak`-Dateien — diese Dateien wurden nicht inhaltlich gescannt. Empfehlung: im Voll-Audit gezielt nach Production-Werten in den Markdown-Reports suchen.
- **Branch Protection** auf `main` ist nicht konfiguriert (alle 100+ Branches `protected: false`).

## 🟢 Bereits gut

- **JWT-Handling**: `settings.py` validiert via `field_validator`, dass `JWT_SECRET` nicht leer ist und schlägt sonst fehl — kein Default-Wert, kein Fallback.
- **CORS**: Whitelist-basiert, `allow_origins=["*"]` nur als opt-in (`CORS_ALLOW_ANY=1`) und dann zwingend mit `allow_credentials=False`.
- **Production-Server**: `uvicorn.run(..., reload=False)` — kein Debug/Reload-Mode hardcoded.
- **`.gitignore`**: deckt `.env`, `.env.local`, Backups, Logs, DB-Dateien sauber ab.

## 📋 Empfehlung für Voll-Audit

**Priorität:** **HOCH** (Sofortmaßnahme für Stoppschild empfohlen, dann Voll-Audit innerhalb 1 Woche)

Begründung: Repo ist live in Production und der geleakte Admin-Key gewährt privilegierten Zugriff. Auch wenn das Repo privat ist, ist der Key für jeden Mitarbeiter / jede AI-Session mit Repo-Zugriff sichtbar; eine Rotation und History-Bereinigung sind dringend. Die Dependency-CVEs (insbesondere Starlette-DoS) sind in einem öffentlich erreichbaren Service nicht zu vernachlässigen.

**Geschätzter Aufwand für Voll-Audit:** **2–4 h**
- ~30 min Admin-Key-Rotation in Railway + neuer Key in `STRATEGY_ADMIN_KEY` deployen
- ~30 min `scripts/testrun_team_berlin.sh` umbauen auf env-var-basiertes Lesen des Keys
- ~1 h History-Bereinigung (BFG/`git filter-repo` für den Key, force-push, Team-Koordination)
- ~30 min Dependency-Bumps (Pillow, Starlette via FastAPI-Pin) + Tests
- ~30 min Härtung (Branch Protection auf `main`, Push-Protection für Secrets aktivieren, Admin-Auth auf Header migrieren — optional)

---

*Inventory von Claude Code, 2026-04-26. Cleanup von `.inventory-temp/` erfolgt vor Commit.*

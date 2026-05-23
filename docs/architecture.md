# Architektur-Übersicht — api-ki-backend-neu

Onboarding- und Diagnose-Referenz für die Wolf-Achtung-KI-Sicherheit-Pipeline.
Beantwortet die Fragen, die bei jeder neuen Session / jedem neuen Sprint
zuerst geklärt werden müssen: welche ID wo, welcher Repo macht was, welche
ENV-Defaults gelten, wo querye ich was.

> Komplementär: `docs/ARCHITECTURE.md` (uppercase) beschreibt die
> PLATIN++-v5.3-Komponenten-Pipeline (Prompt-Loader, Guardrails, Healer,
> Validator). Dieses Doku-File fokussiert auf Infrastruktur, IDs und
> Deploy-Topologie.

---

## ID-System

| ID-Typ | Format | Wo? |
|---|---|---|
| **DB-ID** (`briefing_id`) | Integer Primary Key in `briefings.id` | Coach-URL, API-Endpunkte, Worker-Logs, DB-Queries, `analyses.briefing_id` FK |
| **Display-ID** | `KIS-NNNN` (z. B. `KIS-1196`) | Mail-Subject, PDF-Cover, R1-Header, KPA-Header, Strategy-Header, Admin-Mails |

### Umrechnung

```
Display-ID = "KIS-" + (DB-ID + REPORT_DISPLAY_OFFSET)
DB-ID      = int(Display-ID-Nummer) − REPORT_DISPLAY_OFFSET
```

`REPORT_DISPLAY_OFFSET` ist ENV-konfigurierbar (`utils/report_display_id.py:12`):

```python
offset = int(os.getenv("REPORT_DISPLAY_OFFSET", "0"))
```

- **Code-Default:** `0`
- **Production-Wert:** `117` (verifiziert via Real-Daten: Briefing 1078 → KIS-1195, Briefing 1079 → KIS-1196)

### Beispiele (verifiziert)

| DB-ID | Display-ID |
|---|---|
| 1078 | KIS-1195 |
| 1079 | KIS-1196 |

### Coach-URL-Schema (verifiziert)

```
https://make.ki-sicherheit.jetzt/coach/{briefing_id}
```

- Parameter `{briefing_id}` ist die **DB-ID**, nicht die Display-ID
- Quelle: `services/email_templates.py:23` (`render_coach_cta(briefing_id: int)`)
- Backend-Route-Prefix `/api/coach` (`routes/coach.py:21`) für API-Endpunkte (`/init`, `/message`)

---

## Repo-Struktur

### `api-ki-backend-neu` (dieser Repo)

- **Aufgabe:** HTML-Generation für R1 (KI-Readiness), KPA (Key-Pain-Areas), Strategy-Report
- **Sprache:** Python 3.11, FastAPI
- **Deploy:** Railway, Service `api-ki-backend-neu`
- **Worker:** `api-ki-backend-neu-worker` (R1-Generation asynchron via background-task)
- **Public Domain:** `api-ki-backend-neu-production.up.railway.app`
- **MCP-Scope:** wolf-achtung/api-ki-backend-neu

### `make-ki-pdfservice` (separater Repo)

- **Aufgabe:** HTML → PDF Rendering
- **Engine:** Puppeteer/Chromium *(Version: unverifiziert, Stand Erstbriefing — siehe TODO unten)*
- **Deploy:** Railway, Service `make-ki-pdfservice-production`
- **Public Domain:** `make-ki-pdfservice-production.up.railway.app`
- **Backend-Aufruf:** `POST {PDF_SERVICE_URL}/generate-pdf` mit JSON-Body `{html, meta, pdf_options}` (`services/pdf_client.py:265`)
- **MCP-Scope:** **NICHT zugreifbar** aus Sessions auf `api-ki-backend-neu`

---

## PDF-Service ENV-Defaults — *(unverifiziert)*

> **Status: UNVERIFIZIERT, Stand Erstbriefing 2026-05-22.**
> Die folgenden Werte stammen aus dem Wolf-Briefing für Sprint 1027.3 und
> wurden in dieser Session **nicht** gegen den `make-ki-pdfservice`-Repo-Code
> geprüft, da der Service-Repo außerhalb des MCP-Scope dieser
> Backend-Session lag. Erst nach Verifizierung gegen `package.json` /
> `index.js` / `.env.example` des Service-Repos als Fakt übernehmen.

| ENV-Variable | Vermuteter Default | Status |
|---|---|---|
| `PDF_SCALE` | `0.94` | unverifiziert |
| `PDF_PRINT_BACKGROUND` | `0` | unverifiziert |
| `PDF_MINIFY_HTML` | `1` | unverifiziert |
| `PDF_STRIP_PAGE_AT_RULES` | `1` | unverifiziert — **besonders prüfbedürftig**: falls zutreffend, würden `@page`-Regeln aus dem Template generell gestrippt; das berührt rückwirkend die KIS-1195-Analyse zu CSS-`@page`- vs. Backend-Margins. Page-Setup müsste dann zwingend Inline-CSS oder `pdf_options.margin`-Pfad sein. |
| `PDF_STRIP_SCRIPTS` | `1` | unverifiziert |

**Backend-Sicht (verifiziert):**
- `services/pdf_client.py:26` liest **nur** `PDF_SERVICE_URL`. Keine der oben gelisteten `PDF_*`-Variablen wird Backend-seitig gesetzt oder gelesen.
- Backend sendet via `pdf_options` (`routes/report.py:432-439`): `format=A4`, `printBackground=true`, `displayHeaderFooter=true`, `margin={top:12mm, right:12mm, bottom:20mm, left:12mm}`, plus `footerTemplate`.
- **NICHT** gesetzt vom Backend: `preferCSSPageSize`, `emulateMediaType`, `scale`, `viewport` — Service-Defaults greifen.

### TODO: Service-Repo-Verifikation

Wenn der `make-ki-pdfservice`-Repo aus einer Session zugreifbar ist (eigene MCP-Session auf `wolf-achtung/make-ki-pdfservice`):

1. `package.json` → Puppeteer-Version übernehmen
2. `index.js` / `server.js` → `page.pdf()`-Aufruf inspizieren: `preferCSSPageSize`, `emulateMediaType`, `scale`, `setViewport`
3. `.env.example` / `README.md` → ENV-Defaults extrahieren
4. Die fünf `PDF_*`-Werte in dieser Doku bestätigen oder korrigieren, `(unverifiziert)`-Markierung entfernen

---

## Tech-Stack-Anker

### LLM-Modelle

Production-Werte aus dem 1027.3-Briefing (Code-Defaults siehe Klammer):

| ENV-Variable | Production-Wert | Code-Default | Quelle |
|---|---|---|---|
| `OPENAI_MODEL` | `gpt-5.5-2026-04-23` | `gpt-4o` | `services/llm_client.py:269`, `services/strategy_pipeline.py:756` |
| `ANTHROPIC_MODEL_DEFAULT` | `claude-sonnet-4-6` | *(je Service)* | siehe `services/anthropic_client.py` |
| `ANTHROPIC_MODEL_OPUS` | `claude-opus-4-7` | `claude-opus-4-6` | `services/anthropic_client.py:84` |
| `ANTHROPIC_MODEL_COACH` *(optional)* | unset → fällt auf `ANTHROPIC_MODEL_OPUS` zurück | — | `services/coach_service.py:59-60` |
| → effektiver Coach-Model | `claude-opus-4-7` | `claude-opus-4-6` | abgeleitet |

### Datenbank

- **DBMS:** PostgreSQL
- **Railway-Service:** `Postgres-_HAO` (im KI-Sicherheit-Projekt)
- **Schema:** `public`
- **Connection:** `DATABASE_URL` (intern, Railway-VPC) bzw. `DATABASE_PUBLIC_URL` (TCP-Proxy für externe `psql`-Zugriffe)
- **Engine:** SQLAlchemy 2.x, psycopg (v3 bevorzugt, psycopg2 fallback) — `core/db.py`
- **Auto-Reconnect:** `pool_pre_ping=True`

### Wichtige Tabellen (Auszug)

| Tabelle | Zweck | Schreibpfad |
|---|---|---|
| `briefings` | Roh-Antworten R1-Fragebogen, JSONB `answers` | `routes/briefing.py` (Frontend POST) |
| `analyses` | Gerendertes R1-HTML + meta-JSONB | R1-Pipeline (worker), `models.py:103` |
| `strategy_questions` | Strategiefragebogen S1–S10, separate Tabelle | `routes/strategy.py:279`, `routes/chat.py:3219` |
| `strategy_reports` | Strategy-Report-Status + PDF-Bytes | `services/strategy_pipeline.py` |
| `reports` | PDF-Versand-Tracking | `models.py:145` |

### Zeitzone

- **Server-Zeitzone:** Europe/Berlin
- **Sommer (CEST):** UTC+2 (März–Oktober)
- **Winter (CET):** UTC+1 (Oktober–März)
- Backend-Code arbeitet intern in **UTC** (`datetime.now(timezone.utc)`), Display-Conversion erfolgt an Render-/Mail-Boundary

---

## Diagnose-Workflow für künftige Sprints

### Briefing-ID-Auflösung

```python
# Display-ID "KIS-1196" → DB-ID:
db_id = 1196 - 117  # = 1079

# DB-ID → Display-ID:
from utils.report_display_id import get_report_display_id
display = get_report_display_id(1079)  # = "KIS-1196"
```

### Worker-Logs

```bash
railway logs --service api-ki-backend-neu-worker
# Filter auf eine Briefing-ID:
railway logs --service api-ki-backend-neu-worker | grep -E "\[(Strategy|ADMIN-BRIEFING|KIS|run)[- ]*1079\b"
```

### DB-Access

```bash
# Production (TCP-Proxy):
psql "$DATABASE_PUBLIC_URL"

# Schema:
\d analyses
\d briefings
\d strategy_questions
```

### Migration-Apply-Workflow

**Wichtig: `migrations/*.sql` werden NICHT automatisch appliziert.**

`core/migrate.py:migrate_all` (aufgerufen beim FastAPI-Startup in `main.py:81-86`) führt **nur eine hardcoded DDL-Liste** in `core/migrate.py:DDL` aus. Es gibt **keinen** File-Iterator über `migrations/*.sql`, kein Alembic, keinen Versions-Tracker. Die SQL-Files im Verzeichnis sind Dokumentations-Artefakte und müssen **manuell** gegen die Production-DB ausgeführt werden — sonst existieren die neu definierten Spalten/Tabellen nicht, und Backend-Code-Pfade, die darauf zugreifen, werfen `UndefinedColumn`/`UndefinedTable`-Errors (im besten Fall in try/except gefangen und nur als Warning geloggt; im schlimmsten Fall ungefangen).

**Nach jedem Merge mit neuer `migrations/*.sql`-Datei: manueller Apply nötig.**

Beispiel-Befehle (Substituiere den File-Namen für andere Migrationen):

```bash
# Variante 1 — File-Apply von lokaler Repo-Kopie:
psql "$DATABASE_PUBLIC_URL" \
  -f migrations/2026-05-22_add_analyses_raw_sections_postgres.sql

# Variante 2 — Inline (von beliebigem Host mit psql + DATABASE_PUBLIC_URL):
psql "$DATABASE_PUBLIC_URL" -c "
ALTER TABLE analyses
  ADD COLUMN IF NOT EXISTS raw_sections JSONB DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_analyses_raw_sections_gin
  ON analyses USING GIN (raw_sections);
"

# Variante 3 — Via Railway-CLI mit Backend-internem DATABASE_URL:
railway run --service api-ki-backend-neu \
  psql "$DATABASE_URL" \
  -f migrations/2026-05-22_add_analyses_raw_sections_postgres.sql

# Verify (jede Variante):
psql "$DATABASE_PUBLIC_URL" -c "\d+ analyses" | grep raw_sections
# erwartet: raw_sections | jsonb | | |
```

**Konvention:** alle Migrations sind idempotent (`IF NOT EXISTS`-Klauseln), wiederholtes Anwenden ist gefahrlos. Bei zweistufiger Migration (Postgres + SQLite) gelten beide Files je nach Ziel-Engine — Production nutzt nur die `_postgres.sql`-Variante, lokale Dev-/Test-SQLite nutzt die `_sqlite.sql`-Variante.

**Backlog-Item für Sprint 1027.4:** `core/migrate.py:migrate_all` soll `migrations/*.sql` per glob iterieren statt die hardcoded DDL-Liste exklusiv zu fahren. Betrifft auch die Alt-Migration `2026-03-15_add_raw_sections_strategy.sql`, die ebenfalls nie im Auto-Runner war.

### Gerendertes R1-HTML (faktischer Render-Input)

```sql
SELECT id, briefing_id, created_at, LENGTH(html) AS html_len
FROM analyses
WHERE briefing_id = :db_id
ORDER BY created_at DESC
LIMIT 5;
```

Die `analyses.html`-Spalte ist der **exakte** HTML-String, der per `POST /generate-pdf` an den PDF-Service geht. Page-/Render-Bugs (KIS-1195-Klasse: Chromium clippt obwohl Backend korrekt liefert) sind nur durch Vergleich `analyses.html` ↔ erzeugtes PDF zu fassen.

### Pre-/Post-Healer-Section-Snapshots (ab Sprint 1027.3 / Item H)

Neue Spalte `analyses.raw_sections JSONB` mit Stage-Keys `pre_healer` und `post_healer`. Diagnose-Query:

```sql
SELECT raw_sections->'pre_healer'->>'exec_decision_html'
     = raw_sections->'post_healer'->>'exec_decision_html'
       AS healer_unchanged
FROM analyses WHERE id = :analysis_id;
```

Siehe Sprint-1027.3-Item-H für Schema-Details.

---

## Verifizierungs-Status

Stand: Sprint 1027.3-G (2026-05-22, Berlin)

| Inhalt | Status |
|---|---|
| ID-System (`REPORT_DISPLAY_OFFSET=117`, Display-Konvention) | ✅ verifiziert |
| Coach-URL-Schema + briefing_id-Typ | ✅ verifiziert (`services/email_templates.py:23`) |
| Beispiel-IDs 1078→KIS-1195, 1079→KIS-1196 | ✅ verifiziert |
| Repo-Struktur api-ki-backend-neu | ✅ verifiziert (lokaler Code) |
| Repo-Struktur make-ki-pdfservice | ⚠️ Code-Inspektion in dieser Session **nicht möglich** (MCP-Scope-Restriction) |
| Puppeteer/Chromium-Version | ❌ unverifiziert — TODO oben |
| PDF-Service ENV-Defaults (PDF_SCALE/PRINT_BACKGROUND/MINIFY/STRIP_*) | ❌ unverifiziert — TODO oben |
| Backend-PDF-Optionen (`pdf_options`) | ✅ verifiziert (`routes/report.py:432-439`, `services/pdf_client.py`) |
| LLM-Modell-Code-Defaults | ✅ verifiziert (Code-Pfade dokumentiert) |
| LLM-Modell-Production-Werte | ⚠️ aus Briefing übernommen, nicht gegen Railway-Env geprüft |
| DB-Tabellen-Schema | ✅ verifiziert (`models.py`) |

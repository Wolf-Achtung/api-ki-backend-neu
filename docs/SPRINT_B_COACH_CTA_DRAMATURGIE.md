# Sprint B — Coach-CTA-Dramaturgie + 4. Coach-Mail

**Status:** Coach-CTA aus R1/KPA/Strategy entfernt, dedizierte 4. Mail eingebaut, fire-and-forget gegen Pipeline-Erfolg

**Auslöser:** User klicken den Coach-CTA aktuell oft schon nach R1 — vor KPA und Strategy. Resultat: oberflächliche Coach-Gespräche ohne fundierten Diskussionsstand. Ziel: User liest alle drei Reports in Ruhe, der Coach öffnet sich gezielt nach Versand der Strategy-Mail.

---

## Sektion 1: Diagnose

`render_coach_cta(briefing_id, accent_color)` wird an drei Stellen in `services/email_templates.py` aufgerufen:

| Render-Funktion | Zeile vor Patch | Coach-CTA-Accent |
|---|---:|---|
| `render_report_ready_email` (R1) | 73 | `#2B6CB0` |
| `render_deep_dive_email` (KPA) | 162 | `#0D7377` |
| `render_strategy_email` (Strategy) | 223 | `#0F1D35` |

Alle drei Templates sind in der gleichen Datei — keine Cross-Module-Refactors nötig. Strategy-Pipeline-Trigger-Punkt: `services/strategy_pipeline.py:992` (direkt nach `[Strategy %d] email_sent=True committed`-Log und vor `_send_admin_briefing_email`).

`_send_email_via_resend` (`gpt_analyze.py:1666`) signature: `Tuple[bool, Optional[str]]` — kein Resend-ID-Return; ID wird separat im Resend-eigenen Log gelogged. Marker für Production-Korrelation muss daher per `briefing_id` + Timestamp arbeiten.

---

## Sektion 2: Patch — drei Komponenten

### 2.1 Coach-CTA aus Report-Mails entfernen

`services/email_templates.py` an drei Stellen: der `render_coach_cta(...)`-Call wird durch eine leere `coach_cta = ""`-Variable plus `[COACH-CTA-REMOVED]`-Marker-Log ersetzt. Die Variable bleibt in den f-String-Templates → keine HTML-Strukturänderung, nur weniger Output.

```python
# vorher
coach_cta = render_coach_cta(briefing_id, "#2B6CB0")

# nachher
coach_cta = ""
if recipient != "admin" and briefing_id:
    logger.info("[COACH-CTA-REMOVED] template=report_ready briefing_id=%d", briefing_id)
```

Marker emittiert nur für `recipient != "admin"` — Admin-Mails enthielten den CTA ohnehin nie, dort wäre der Marker irreführend.

### 2.2 Neue 4. Mail — `render_coach_reminder_email(briefing_id)`

Mail-Template direkt nach `render_strategy_email` im selben Modul. Subject **fix** wie im Briefing vereinbart: `"Sie haben Fragen zu Ihren Reports? Ihr persönlicher KI-Coach steht bereit"`. Body-Inhalt (deutsch, Sie-Form, warm):

1. Persönliche Anrede
2. Bestätigung "alle drei Reports erhalten" mit `<strong>`-Hervorhebung der Report-Namen
3. Aufforderung "in Ruhe durchzuarbeiten" + Hinweis dass Reports sich ergänzen
4. Einleitung zum Coach-CTA
5. Prominenter Coach-CTA-Button (`render_coach_cta(briefing_id, "#2B6CB0")`)
6. Liste der Coach-Kompetenzen (Umsetzungsfragen, Risikodiskussion, Tool-Auswahl, Förderstrategie)
7. Standard-Footer "Wolf Hohl — KI-Sicherheit.jetzt"

Body-Wortzahl bewusst unter dem Briefing-Cap von 200 Wörtern.

### 2.3 Pipeline-Trigger — `_send_coach_reminder_email(briefing_id, db_session)`

Neue Funktion in `services/strategy_pipeline.py` zwischen `_send_strategy_email` und `_send_admin_briefing_email`. Verhalten:

- Respektiert `DISABLE_EMAILS`-Env-Flag analog Standard-Mails
- Resend-Rate-Limit-Sleep 600ms vor Send (analog Standard-Mails)
- Eigener Resend-Call mit Subject + HTML, KEIN PDF-Attachment
- Marker-Logging an beiden Pfaden:
  - Success: `[COACH-REMINDER-MAIL] briefing_id=X email=u***@e.com status=sent`
  - Fail: `[COACH-REMINDER-MAIL-FAILED] briefing_id=X email=u***@e.com err=...`

Trigger-Punkt:

```python
# strategy_pipeline.py, run_strategy_pipeline
try:
    _send_strategy_email(briefing_id, pdf_bytes, db_session)
    sr.email_sent = True
    sr.email_sent_at = datetime.now(timezone.utc)
    db_session.commit()
    logger.info("[Strategy %d] email_sent=True committed", briefing_id)
except Exception as mail_exc:
    logger.error(...)

# NEU: Coach-Reminder nur bei email_sent=True
if getattr(sr, "email_sent", False):
    try:
        _send_coach_reminder_email(briefing_id, db_session)
    except Exception as cr_exc:
        logger.warning("[COACH-REMINDER-MAIL-FAILED] ...")
```

**Fire-and-forget vertraglich:** Wenn die 4. Mail fehlschlägt (Resend-Down, kein User-Email, Import-Failure), wird das nur als WARNING geloggt. Strategy-Mail wurde zugestellt → User hat seine Reports → Pipeline-Erfolg darf nicht zurückgerollt werden.

---

## Sektion 3: Edge-Case-Entscheidungen

Per Briefing-Pre-Commitments, keine Wolf-Pings nötig:

| Case | Entscheidung |
|---|---|
| Mehrere Briefings nacheinander | Pro Briefing eine Reminder-Mail, kein Dedupe |
| Admin-Test-Adresse | Bekommt 4. Mail wie normale User |
| Fehlerhafter Strategy-Lauf (`email_sent=False`) | Coach-Reminder NICHT ausgelöst |
| DB-Tracking | Kein neues Schema-Feld; Marker + Resend-ID im Log reichen |
| Mail-Subject | Briefing-Wortlaut exakt übernommen (47 Zeichen, kein Subject-Limit-Issue) |

---

## Sektion 4: Tests (`tests/test_coach_cta_dramaturgie.py`, 13 Tests)

| Test | Verifikation |
|---|---|
| `test_r1_user_mail_has_no_coach_cta` | R1 enthält weder "Coach-Gespr" noch `/coach/<id>` |
| `test_r1_user_mail_preserves_strategy_upsell` | Strategy-Upsell in R1 bleibt erhalten (nur Coach-CTA entfernt) |
| `test_kpa_user_mail_has_no_coach_cta` | analog KPA |
| `test_strategy_user_mail_has_no_coach_cta` | analog Strategy |
| `test_admin_mails_remain_clean` | Admin-Varianten unverändert clean |
| `test_renders_with_coach_cta` | Coach-Reminder enthält CTA mit korrekter URL |
| `test_acknowledges_all_three_reports` | Body bestätigt R1/KPA/Strategy-Versand |
| `test_invites_calm_reading_before_coach` | "in Ruhe" + Pacing-Hinweis vorhanden |
| `test_lists_coach_competencies` | ≥3 der 4 Briefing-Kompetenzen genannt |
| `test_body_under_200_words` | Briefing-Cap eingehalten |
| `test_reminder_fires_after_successful_strategy_mail` | Trigger feuert bei email_sent=True |
| `test_reminder_not_fired_when_strategy_mail_raised` | Bei Exception kein Reminder |
| `test_reminder_failure_logged_not_raised` | Send-Failure raised nichts |

Local full suite: **6400 passed, 10 skipped, 0 failed.**

---

## Sektion 5: Validierungsplan (Production-Smoke)

Wird zusammen mit C2-Smoke-Test im selben Test-Briefing-Lauf erledigt (Solo+Beratung+`ki_kompetenz=hoch`):

1. **Posteingang:** 4 Mails in dieser Reihenfolge:
   - R1 → KPA → Strategy → **Coach-Reminder** (neu)
2. **Inhalt:**
   - R1/KPA/Strategy zeigen KEINEN Coach-CTA-Button mehr
   - Coach-Reminder zeigt prominenten Coach-CTA mit Link `https://make.ki-sicherheit.jetzt/coach/<briefing_id>`
3. **Coach-Funktion:** Klick auf Coach-CTA in der 4. Mail führt zum Coach, Coach antwortet
4. **Logs:**
   - 3× `[COACH-CTA-REMOVED]` (template=report_ready / deep_dive / strategy)
   - 1× `[COACH-REMINDER-MAIL] briefing_id=... email=u***@... status=sent`
   - KEIN `[COACH-REMINDER-MAIL-FAILED]`

---

## Sektion 6: Geänderte Dateien

| Datei | Δ |
|---|---|
| `services/email_templates.py` | -6 / +69 LOC (3 CTA-Removals + neue Coach-Reminder-Template) |
| `services/strategy_pipeline.py` | +84 LOC (Trigger + neue `_send_coach_reminder_email`) |
| `tests/test_coach_cta_dramaturgie.py` | +180 (neu, 13 Tests) |
| `docs/SPRINT_B_COACH_CTA_DRAMATURGIE.md` | +130 (neu) |

**Out of Scope per Briefing:** Resend Scheduled-Send, DB-Tabelle `scheduled_coach_emails`, Cron-Reminder, Cancel/Update, Multi-Stage-Reminder, A/B-Subject-Tests, Unsubscribe-Logik.

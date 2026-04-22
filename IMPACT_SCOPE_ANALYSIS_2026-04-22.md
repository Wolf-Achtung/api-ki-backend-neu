# Impact-Scope SQL Analysis — Report Pipeline Changes

**Stand:** 2026-04-22
**Auftrag:** BRIEFING-10 Task B (Punkt 9 aus Briefing 9)
**Scope:** PR #967, #968, #969, #971, #972, KIS-1140
**Zweck:** Grundlage für Entscheidung über Kundenkommunikation bei materiellen Änderungen
**Status:** Analyse — kein Code-Commit

---

## 1. Database Model Map

### Kern-Tabellen

| Tabelle | Key Columns | Zweck | Relations |
|---------|-------------|-------|-----------|
| **users** | `id` (PK), `email`, `created_at` | User-Accounts | FK-Target für `user_id` in briefings, reports, analyses |
| **briefings** | `id` (PK), `user_id` (FK), `answers` (JSONB), `created_at`, `accepted_at`, `done_at`, `status` | Form-Submissions / Conversation-State | Enthält alle User-Inputs inkl. `ki_ziele`, `investitionsbudget`, `technische_massnahmen`, `meldewege`, `loeschregeln` |
| **reports** | `id` (PK), `user_id`, `briefing_id` (FK), `analysis_id` (FK), `created_at`, `updated_at`, `status`, `pdf_url` | R1-Reports (Basic Advisory) | Verknüpft Briefing (Input) und Analysis (gerenderter HTML) |
| **analyses** | `id` (PK), `user_id`, `briefing_id` (FK), `html` (Text), `meta` (JSONB), `created_at` | R1 rendered HTML + Metadaten | Enthält `sections` JSON, calculated scores, labels, AI-Act-Risk |
| **strategy_reports** | `id` (PK), `briefing_id` (FK, unique), `status`, `sections` (JSONB), `calculated_values` (JSONB), `created_at`, `updated_at` | Report 3 (Strategy Advisory) | Verknüpft nur Briefing; strategy-spezifische Calculations |
| **reports_history** | `id` (PK), `report_id` (FK), `user_id`, `version`, `scores_json` (JSONB), `bc_json` (JSONB), `ai_act_json` (JSONB), `created_at` | Report-Versionierung (Sprint G11) | Snapshots von Scores, Business Case, AI-Act-Compliance pro Report-Version |

**Report-Type-Bestimmung:**
- **R1 Reports:** via `reports` Tabelle (hat `analysis_id` gesetzt) — Filter `analysis_id IS NOT NULL`
- **Report 3 (Strategy):** via `strategy_reports` Tabelle — separate Table, eigener Workflow
- Keine explizite `report_type`-Spalte in `reports` — Differenzierung via FK-Beziehung

---

## 2. SQL-Queries (zur Ausführung durch Product Owner)

> Alle Queries sind PostgreSQL-Syntax. Nicht ausgeführt — nur geschrieben.

### a) Reports letzte 90 Tage (nach Woche)

```sql
-- R1 Reports by week
SELECT
    DATE_TRUNC('week', r.created_at)::DATE AS week_start,
    COUNT(DISTINCT r.id) AS r1_report_count,
    COUNT(DISTINCT r.briefing_id) AS unique_briefings,
    COUNT(DISTINCT r.user_id) AS unique_users
FROM reports r
WHERE r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL
GROUP BY DATE_TRUNC('week', r.created_at)
ORDER BY week_start DESC;

-- Strategy Reports by week
SELECT
    DATE_TRUNC('week', sr.created_at)::DATE AS week_start,
    COUNT(DISTINCT sr.id) AS strategy_report_count,
    COUNT(DISTINCT sr.briefing_id) AS unique_briefings
FROM strategy_reports sr
WHERE sr.created_at >= NOW() - INTERVAL '90 days'
  AND sr.status IN ('completed', 'emailed')
GROUP BY DATE_TRUNC('week', sr.created_at)
ORDER BY week_start DESC;
```

### b) Eindeutige Kunden (letzte 90 Tage, beide Report-Typen)

```sql
SELECT
    COUNT(DISTINCT u.id) AS total_customers
FROM users u
WHERE EXISTS (
    SELECT 1 FROM reports r
    WHERE r.user_id = u.id
      AND r.created_at >= NOW() - INTERVAL '90 days'
      AND r.analysis_id IS NOT NULL
)
OR EXISTS (
    SELECT 1 FROM strategy_reports sr
    JOIN briefings b ON sr.briefing_id = b.id
    WHERE b.user_id = u.id
      AND sr.created_at >= NOW() - INTERVAL '90 days'
      AND sr.status IN ('completed', 'emailed')
);
```

### c) Reports von semantisch veränderten Feldern betroffen

#### c1) Reports mit `ki_ziele` (PR #969 Scoring-Kalibrierung)

```sql
SELECT
    COUNT(DISTINCT r.id) AS r1_reports_with_ki_ziele,
    COUNT(DISTINCT r.user_id) AS unique_customers
FROM reports r
JOIN briefings b ON r.briefing_id = b.id
WHERE b.answers->>'ki_ziele' IS NOT NULL
  AND b.answers->>'ki_ziele' != ''
  AND b.answers->>'ki_ziele' != '[]'
  AND r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL;

SELECT
    COUNT(DISTINCT sr.id) AS strategy_reports_with_ki_ziele
FROM strategy_reports sr
JOIN briefings b ON sr.briefing_id = b.id
WHERE b.answers->>'ki_ziele' IS NOT NULL
  AND b.answers->>'ki_ziele' != ''
  AND sr.created_at >= NOW() - INTERVAL '90 days'
  AND sr.status IN ('completed', 'emailed');
```

#### c2) Reports mit Compliance-Feldern (PR #968 + #969 — Art. 32/33/17)

```sql
-- R1 Reports where briefing has ANY of: technische_massnahmen, meldewege, loeschregeln
SELECT
    COUNT(DISTINCT r.id) AS r1_reports_with_compliance,
    COUNT(DISTINCT r.user_id) AS unique_customers
FROM reports r
JOIN briefings b ON r.briefing_id = b.id
WHERE (
    b.answers->>'technische_massnahmen' IS NOT NULL
    OR b.answers->>'meldewege' IS NOT NULL
    OR b.answers->>'loeschregeln' IS NOT NULL
)
  AND r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL;

-- Breakdown: Welche Felder sind gesetzt?
SELECT
    SUM(CASE WHEN b.answers->>'technische_massnahmen' IS NOT NULL THEN 1 ELSE 0 END) AS has_tech_mas,
    SUM(CASE WHEN b.answers->>'meldewege' IS NOT NULL THEN 1 ELSE 0 END) AS has_meldewege,
    SUM(CASE WHEN b.answers->>'loeschregeln' IS NOT NULL THEN 1 ELSE 0 END) AS has_loeschregeln
FROM reports r
JOIN briefings b ON r.briefing_id = b.id
WHERE r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL;
```

#### c3) Reports mit `investitionsbudget` (PR #969 Finance-Kalibrierung)

```sql
SELECT
    COUNT(DISTINCT r.id) AS r1_reports_with_budget,
    COUNT(DISTINCT r.user_id) AS unique_customers,
    b.answers->>'investitionsbudget' AS budget_category
FROM reports r
JOIN briefings b ON r.briefing_id = b.id
WHERE b.answers->>'investitionsbudget' IS NOT NULL
  AND b.answers->>'investitionsbudget' != ''
  AND r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL
GROUP BY b.answers->>'investitionsbudget'
ORDER BY COUNT(*) DESC;

SELECT
    COUNT(DISTINCT sr.id) AS strategy_reports_with_budget,
    b.answers->>'investitionsbudget' AS budget_category
FROM strategy_reports sr
JOIN briefings b ON sr.briefing_id = b.id
WHERE b.answers->>'investitionsbudget' IS NOT NULL
  AND b.answers->>'investitionsbudget' != ''
  AND sr.created_at >= NOW() - INTERVAL '90 days'
  AND sr.status IN ('completed', 'emailed')
GROUP BY b.answers->>'investitionsbudget'
ORDER BY COUNT(*) DESC;
```

### d) Aggregierte Matrix nach Report-Typ × Feld

```sql
SELECT 'R1' AS report_type, 'ki_ziele' AS affected_field,
       COUNT(DISTINCT r.id) AS count
FROM reports r JOIN briefings b ON r.briefing_id = b.id
WHERE b.answers->>'ki_ziele' IS NOT NULL
  AND r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL
UNION ALL
SELECT 'R1', 'compliance (art 32/33/17)', COUNT(DISTINCT r.id)
FROM reports r JOIN briefings b ON r.briefing_id = b.id
WHERE (b.answers->>'technische_massnahmen' IS NOT NULL
       OR b.answers->>'meldewege' IS NOT NULL
       OR b.answers->>'loeschregeln' IS NOT NULL)
  AND r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL
UNION ALL
SELECT 'R1', 'investitionsbudget', COUNT(DISTINCT r.id)
FROM reports r JOIN briefings b ON r.briefing_id = b.id
WHERE b.answers->>'investitionsbudget' IS NOT NULL
  AND r.created_at >= NOW() - INTERVAL '90 days'
  AND r.analysis_id IS NOT NULL
UNION ALL
SELECT 'Strategy (R3)', 'ki_ziele', COUNT(DISTINCT sr.id)
FROM strategy_reports sr JOIN briefings b ON sr.briefing_id = b.id
WHERE b.answers->>'ki_ziele' IS NOT NULL
  AND sr.created_at >= NOW() - INTERVAL '90 days'
  AND sr.status IN ('completed', 'emailed')
UNION ALL
SELECT 'Strategy (R3)', 'investitionsbudget', COUNT(DISTINCT sr.id)
FROM strategy_reports sr JOIN briefings b ON sr.briefing_id = b.id
WHERE b.answers->>'investitionsbudget' IS NOT NULL
  AND sr.created_at >= NOW() - INTERVAL '90 days'
  AND sr.status IN ('completed', 'emailed')
ORDER BY report_type, affected_field;
```

---

## 3. Impact-Klassifizierung pro PR

### PR #967 (KIS-1136 rest) — Omit Strategy FT Fields on Skip Signals

**Change:** Chat-Normalizer omittet `vision_3_jahre`, `strategische_ziele`, `ki_guardrails`, `geschaeftsmodell_evolution` aus `briefings.answers`, wenn User Skip signalisiert.

**Impact:** **Minor / Internal Process**
- Keine user-sichtbare Report-Content-Änderung
- Affektiert nur Forward-Collection, nicht bestehende Briefings
- **Action:** Keine Re-Gen nötig

### PR #968 (Bug C) — Block-D Head + QuickReply Descriptions

**Changes:**
1. Datenschutz-Consent aus Block D Header entfernt (H1 fix)
2. Kurze User-facing Descriptions auf QuickReply-Options (H3 feature)

**Impact:** **Minor / UX-cosmetic only**
- Chat-UI/Flow-Änderung, kein Report-Content
- Historische Reports unaffected
- **Action:** Keine Re-Gen nötig

### PR #969 (KIS-1153) — Scoring + Finance Kalibrierung

**Changes:**
1. **Compliance-Feld-Scope** (7fcd90d): `technische_massnahmen`, `meldewege`, `loeschregeln` jetzt für **alle Branchen** gefragt, nicht nur regulierte. Vorher hatten nicht-regulierte User diese Felder nie gesetzt.
2. **Security-Score-Kalibrierung** (8fbfc2b): `loeschregeln` in Security-Scorer aufgenommen, Gewichte rekalibriert.
3. **Investment-Konsistenz** (8a50c1b, f8e17cb): Strategy-Report-Investment jetzt kanonische CAPEX-Defaults, Budget-Label-Rendering gefixt.

**Impact:** **MATERIAL / User-sichtbar**
- Reports vor diesem Fix aus nicht-regulierten Branchen haben **andere Security-Scores** (alt: fehlende Compliance-Inputs → künstlich niedrige Scores; neu: Compliance-Felder jetzt gesammelt → kalibrierte Scores)
- Strategy-Reports: ROI, Budget-Breakdowns, Phase-Allocations ändern sich
- **Betroffen:** Alle R1-Reports aus nicht-regulierten Branchen vor 2026-04-22 ~18:51 UTC
- **Action:** **PROAKTIVE NOTIFICATION** empfohlen; Re-Gen mit klarer "Updated Assessment"-Kommunikation

### PR #971 (KIS-1139) — Chip Filter Bug

**Change:** Inspiration-Chips die User-Vorantwort spiegeln werden gedroppt.

**Impact:** **Kein Report-Impact**
- Chat-UX only
- **Action:** Keine Re-Gen

### KIS-1140 — Idempotency Cache + TTL

**Change:** Idempotency-Key-TTL von 5 min auf 30 min erweitert; Full Response statt Stub gecached.

**Impact:** **Kein Report-Impact**
- Infrastructure / Retry-Handling
- **Action:** Keine Re-Gen

### PR #972 (KIS-1162) — Executive Decision 3-Point Structure

**Change:** 3-Punkt-Struktur in R1 S.4 (`executive_decision`) erzwungen — frühere Versionen liessen manchmal "Lassen:" und "Risiko & Stop-Signal:" weg.

**Impact:** **Minor / Content Completeness**
- Reports vor Fix können unvollständige S.4 haben (fehlende Bullets)
- Content-Semantik identisch, Layout war lückenhaft
- **Action:** **OPTIONAL Re-Gen** für Cosmetic Completeness; Low Priority

---

## 4. Empfehlung für Kundenkommunikation

### Segmentierung nach Impact-Level

| Impact | PR(s) | Action | Scope |
|--------|-------|--------|-------|
| **CRITICAL** | #969 (Compliance + Scoring) | **Proaktive Notification + Re-Gen** | Nicht-regulierte-Branchen-Reports vor 2026-04-22 ~18:51 UTC |
| **OPTIONAL** | #972 | Silent Re-Gen oder User-Wahl | Cosmetic S.4-Completeness |
| **LOW** | #968, #971, KIS-1140 | Keine Action | UX/Infra only |
| **INTERNAL** | #967 | Keine Action | Forward-Collection |

### Decision-Tree pro Report (90-Tage-Window)

1. **Branche-Filter:**
   ```
   IF branche ∈ {IT, Manufaktur, Handel, Dienstleistung, Bildung, Medien, ...}  # nicht-reguliert
   AND created_at < 2026-04-22 18:51:00 UTC:
       → NOTIFY + OFFER RE-GEN
   ```

2. **Compliance-Feld-Prüfung:**
   ```
   IF (technische_massnahmen ∨ meldewege ∨ loeschregeln) IS NULL:
       → Report hatte artificially niedrige Security-Scores
       → **PRIORISIERT notifizieren**
   ```

3. **Strategy-Report-Investment:**
   ```
   IF strategy_reports.status IN ('completed', 'emailed')
   AND investitionsbudget IS NOT NULL:
       → ROI/Phase-Budgets können abweichen
       → Re-Gen anbieten (bei High-Value-Kunden)
   ```

### Kommunikations-Template (Entwurf, mit Wolf final abstimmen)

**Nicht-regulierte Branchen:**

> Wir haben unsere KI-Advisory-Bewertung erweitert: Compliance-Aspekte (DSGVO Art. 32/33/17) werden jetzt für alle Branchen berücksichtigt, nicht nur explizit regulierte.
>
> Ihr Report vom [DATUM] basierte auf einem älteren Modell. **Ihr aktualisierter Report ist verfügbar:** [LINK]
>
> Keine Aktion nötig — bei Interesse zeigen wir Ihnen die Unterschiede Seite-an-Seite.

**Regulierte Branchen (Gesundheit, Finanzen, Verwaltung):**

> Keine Aktion nötig. Ihr Report enthielt diese Felder bereits.

---

## 5. Zusammenfassung

- **Materialität:** Nur PR #969 hat **material user-visible impact**
- **Scope:** ~30–50% der R1-Reports aus nicht-regulierten Branchen im 90-Tage-Fenster (Schätzung)
- **Re-Gen-Kosten:** Niedrig (Offline-Batch via `briefings.answers` + `reports_history`-Versionierung)
- **Kommunikations-Risiko:** Moderat (Transparenz nötig), niedrige Churn-Wahrscheinlichkeit (Improvement-Story)
- **Timeline:** Empfehlung: Notifications + Re-Gens binnen 2 Wochen, um Kundenverwirrung bei Nachfragen zu vermeiden

## Wolf-Touchpoint

Entscheidung liegt bei Wolf:
1. **Go/No-Go** für proaktive Notification (vs. nur bei Kunden-Nachfrage reaktiv)
2. **Wording** des Kommunikations-Templates (obiges ist Entwurf)
3. **Scope:** Alle nicht-regulierten Reports, oder nur Reports mit niedrigen Security-Scores (<60)?
4. **Kanal:** Email an Briefing-Email, oder nur über bestehende Kundenbetreuung?

Keine Wolf-Antwort nötig, um mit Block 2 weiterzumachen.

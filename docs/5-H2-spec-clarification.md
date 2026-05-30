# 5-H2 — Spec-Klarstellung (KIS-1200 NO-GO)

**Status (1027.5.1):** 5-H2 ist defensive API-Erweiterung — **kein
Code-Pfad ruft sie heute auf**. Empfehlung: Refactor-Kandidat 1027.6.

## Anlass

KIS-1200-Funnel wurde laut Sprint-1027.5.1-Briefing OHNE Tools-Vertiefung
gefahren. `briefing.answers` enthielt KEIN `s5_software`. R1 PDF S.15
Vendor-Audit zeigte 2 Tools (ChatGPT, Claude). Im Strategy-Report
(`strategy_reports.sections->'S4'`) wird Perplexity 6× im Fließtext
erwähnt, aber kein strukturiertes Audit-Objekt.

Die Handover-Spec für 5-H2 (aus Sprint 1027.5):
> "4 Tools inkl. Perplexity im Strategy-Vendor-Audit"
> "strategy_data->'vendor_audit'->'vendors' jsonb_array_length = 4"

ist nicht verifizierbar:

- `analyses`-Tabelle hat **keine** `strategy_data`-Spalte
  (Spalten: `id, user_id, briefing_id, html, meta, created_at, raw_sections`)
- Es gibt **kein** strukturiertes `vendor_audit`-JSON-Objekt
- `strategy_reports.sections->'S4'` ist HTML-String, kein JSONB-Array

Die Handover-Query wurde versehentlich auf ein nicht existierendes
DB-Schema geschrieben.

## Code-Pfad (was 5-H2 tatsächlich tut)

### Definition

| Datei | Symbol | Beschreibung |
|---|---|---|
| `services/vendor_audit_engine.py:918` | `_extract_vendors_from_briefing(briefing, strategy_answers=None)` | Akzeptiert optional `strategy_answers`-dict, merged es nicht-zerstörend in eine Briefing-Kopie (briefing-Werte gewinnen, nur leere Felder werden gefüllt) |
| `services/vendor_audit_engine.py:1244` | `generate_vendor_audit_report(..., strategy_answers=None)` | Reicht den Param an `_extract_vendors_from_briefing` weiter (Z. 1297) |

Mit `strategy_answers` werden zusätzlich diese source-Keys auditierbar:
- `s5_software`
- `S5_SOFTWARE`
- `bestehende_software`

(Sprint-1027.4-2D source_keys-Mapping)

### Production-Call-Site

**Nur eine** Stelle ruft `generate_vendor_audit_report` in der live-
Pipeline auf:

```python
# gpt_analyze.py:16058 — R1-Generation
vendor_audit_report = generate_vendor_audit_report(
    context=None,
    tools_data=sections.get("_tools_data"),
    risk_report_v2=sections.get("_risk_report"),
    risk_report_v3=sections.get("_risk_report_v3"),
    briefing=answers,
    llm_response=None,
    sections=sections,
)
```

`strategy_answers` wird **nicht** gesetzt → `_extract_vendors_from_briefing`
fällt auf reines `briefing`-Argument zurück. Der 5-H2-Fix hat hier
**keine Wirkung**.

`services/strategy_pipeline.py` ruft `generate_vendor_audit_report`
nicht auf — Strategy-Pipeline liest nur die *bereits berechneten*
VENDOR_AUDIT_RED/GREEN/STATUS-Counts aus `_r1_sections` (Z. 260-262)
und nutzt sie als Prompt-Variablen für Strategy-Section-Generation.

## Wo SOLLTE 5-H2 wirken, und tut es das?

| Section / Datenstruktur | Erwartete Änderung mit `strategy_answers` | Tatsächlich beobachtbar? |
|---|---|---|
| R1 `VENDOR_AUDIT_HTML` (Sections S.14/15) | Würde zusätzliche Vendor-Einträge zeigen — wenn aus strategy `s5_software` extrahierbar | **Nein** — `gpt_analyze.py:16058` passt strategy_answers nicht durch |
| Strategy `S4` HTML | Wird über LLM-Prompts generiert, nicht über vendor_audit_engine | **Nein** — kein Code-Pfad |
| Eigenes vendor_audit-JSON-Objekt | — | **Existiert nicht im DB-Schema** |

→ **5-H2-Fix ist heute defensiv-only.** Er hat keinen User-visible
Effekt, solange kein Caller `strategy_answers` setzt.

## Warum greift der Pfad nicht "by design"?

Pipeline-Reihenfolge bei normalem Funnel-Run:

1. R1-Generation (worker) → liest `briefing.answers`, generiert R1-PDF
   inkl. Vendor-Audit
2. R1-`report_ready`-Mail (mit PDF)
3. Strategy-Chat (user füllt s5_software ein)
4. Strategy-Pipeline → liest s5_software, generiert Strategy-PDF

Zwischen 1 und 3 ist die `strategy_answers`-Existenz unbekannt. Beim
R1-Re-Render (1027.4-3A-Pfad) wird `_send_admin_briefing_email` mit
`strategy_answers` aufgerufen, aber `_send_admin_briefing_email`
re-rendert das Briefing-PDF, nicht den R1-Report.

Das `/api/strategy/admin/r1-re-render`-Endpoint (routes/strategy.py:874)
liest R1 aus `analyses.meta['sections']` und rendert mit
`heal_report_html` + `b25_enforcer` + `render`, **ohne**
`generate_vendor_audit_report` neu aufzurufen. Vendor-Audit-HTML im
PDF stammt also weiterhin von der ursprünglichen R1-Generation.

## Validierungs-Query (statt der falschen Handover-Query)

Statt `strategy_data->'vendor_audit'->'vendors'` (existiert nicht):

```sql
-- Was R1-Vendor-Audit tatsächlich enthält
SELECT briefing_id,
       length(meta->'sections'->>'VENDOR_AUDIT_HTML') AS audit_html_len
FROM analyses
WHERE briefing_id = :briefing_id
ORDER BY id DESC
LIMIT 1;

-- Anzahl Vendor-Einträge im gerenderten Audit (HTML-Pattern-Zählung):
-- Audit-Tabelle erzeugt ein <tr class="vendor-row"> oder ähnlich pro Vendor.
SELECT briefing_id,
       (
         SELECT count(*) FROM regexp_matches(
           meta->'sections'->>'VENDOR_AUDIT_HTML',
           '<tr[^>]*class="[^"]*vendor[^"]*"',
           'g'
         )
       ) AS vendor_row_count
FROM analyses
WHERE briefing_id = :briefing_id;
```

(Exakter Selektor-Pattern siehe `services/vendor_audit_engine.py:vendor_audit_report_to_html`.)

## Wolf-Ping — Empfehlung

**Einordnung:** "wirkt nicht" + Refactor-Kandidat 1027.6.

Begründung:

- 5-H2-Defensive ist in-Code, aber ohne Caller. Keine Lasten, aber auch
  kein Wert für User.
- Echte Lösung für "Perplexity erscheint im R1-Vendor-Audit": R1
  muss zum Strategy-Chat-Abschluss-Zeitpunkt re-gerendert werden, mit
  `strategy_answers` durchgereicht an `generate_vendor_audit_report`.
- Aufwand für vollständigen Fix: 1027.6-Item-Größe (touches Chat-
  Abschluss-Hook, R1-Re-Render-Pfad, Renderer-Schnittstellen,
  Email-Versand-Zeitpunkt).

**Vorschlag:** 5-H2 als "API-Erweiterung erfolgt, kein Caller" im
Daily Report markieren; 1027.6 nimmt den Wire-up-Refactor auf (siehe
Backlog-Item "Vendor-Audit-Refactor: Briefing-State zu Strategy-Time
vollständig").

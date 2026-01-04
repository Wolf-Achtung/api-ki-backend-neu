# Fix-Plan: Priorisierte Maßnahmen

## Priorisierungs-Matrix

| Priorität | Problem | Impact | Aufwand | Risiko |
|-----------|---------|--------|---------|--------|
| P0 🔴 | #1 Digital Jetzt entfernen | Hoch (Falschaussage) | Niedrig | Niedrig |
| P0 🔴 | #2 Solo-Fördersumme begrenzen | Hoch (Falschaussage) | Mittel | Niedrig |
| P1 🟠 | #3 ROI-Berechnung transparent | Mittel (Vertrauensverlust) | Mittel | Niedrig |
| P1 🟠 | #4 Markttrends mit Quellen | Mittel (Vertrauensverlust) | Hoch | Niedrig |
| P2 🟡 | #5 Duplikate eliminieren | Niedrig (UX) | Mittel | Mittel |
| P2 🟡 | #6 Solo-Sprache korrigieren | Niedrig (UX) | Mittel | Niedrig |
| P3 🔵 | #7 Seitenzahl begrenzen | Niedrig (UX) | Hoch | Mittel |

---

## P0: Kritische Fixes (Sofort umsetzen)

### Fix #1: "Digital Jetzt" entfernen

**Root Cause:** `data/funding_programs.json:1-9`, `services/funding_parser.py:10-18`

**Lösung A: Programm entfernen (Empfohlen)**

```python
# data/funding_programs.json - LÖSCHEN:
# Zeile 1-10 (gesamter Eintrag für "Digital Jetzt")

# services/funding_parser.py - LÖSCHEN:
# Zeile 10-18 (FALLBACK_FUNDING_PROGRAMS Eintrag)
```

**Lösung B: Deadline-Validierung einbauen**

```python
# Neue Datei: services/funding_validator.py
from datetime import datetime

def validate_funding_programmes(programmes: list) -> list:
    """Filter out expired funding programmes."""
    today = datetime.now()
    valid = []
    for prog in programmes:
        deadline_str = prog.get("deadline", "")
        if not deadline_str:
            valid.append(prog)
            continue
        try:
            # Parse "31.03.2026" or "Q2 2025" formats
            deadline = parse_deadline(deadline_str)
            if deadline > today:
                valid.append(prog)
            else:
                log.warning(f"Filtered expired programme: {prog['name']}")
        except ValueError:
            valid.append(prog)  # Keep if unparseable
    return valid
```

**Test:**
```bash
grep -r "Digital Jetzt" data/ services/ prompts/
# Erwartetes Ergebnis: Keine Treffer
```

---

### Fix #2: Solo-Fördersumme realistisch begrenzen

**Root Cause:** `services/business_case_engine_v2.py:747-760`

**Lösung: Solo-Cap einführen**

```python
# services/business_case_engine_v2.py - Zeile 747 erweitern:

SOLO_FUNDING_CAP = 20000  # Realistisches Maximum für Solo
TEAM_FUNDING_CAP = 50000
KMU_FUNDING_CAP = 200000

def calculate_funding_with_size_cap(
    funding_data: Any,
    investment_total: float,
    company_size: str = "team"
) -> Tuple[float, List[str]]:
    """Calculate funding with size-appropriate caps."""

    # Bestehende Logik...
    total_funding = 0.0
    programme_names: List[str] = []

    # NEU: Cap basierend auf Unternehmensgröße
    funding_cap = {
        "solo": SOLO_FUNDING_CAP,
        "team": TEAM_FUNDING_CAP,
        "kmu": KMU_FUNDING_CAP,
    }.get(company_size.lower(), TEAM_FUNDING_CAP)

    for prog in programmes:
        # NEU: Solo-Filter verschärfen
        if company_size.lower() == "solo":
            fit_score = prog.get("fit_solo", 0.5)
            if fit_score < 0.7:  # Nur Programme mit hohem Solo-Fit
                continue

        funding_amount = _extract_funding_amount(prog)

        # NEU: Cap anwenden
        if total_funding + funding_amount > funding_cap:
            break

        total_funding += funding_amount
        programme_names.append(prog.get("name", ""))

    return min(total_funding, funding_cap), programme_names
```

**Test:**
```python
def test_solo_funding_cap():
    result, _ = calculate_funding_with_size_cap(
        funding_data=mock_programmes,
        investment_total=10000,
        company_size="solo"
    )
    assert result <= 20000, f"Solo funding {result} exceeds cap"
```

---

## P1: Wichtige Fixes (Diese Woche)

### Fix #3: ROI-Berechnung transparent machen

**Root Cause:** `services/roi_calculator.py:42-43`

**Lösung: Eingabe-basierte Berechnung statt Hardcoding**

```python
# services/roi_calculator.py - ERSETZEN Zeile 33-70:

def calc_roi(
    briefing: Dict[str, Any] | Any,
    quickwins: List[Dict[str, Any]] | None = None
) -> Dict[str, Any]:
    """
    Transparente ROI-Berechnung mit nachvollziehbaren Annahmen.

    ÄNDERUNG v2.0:
    - Statt 40h Fallback → Berechnung aus Quick Wins PFLICHT
    - Falls keine Quick Wins → konservative Schätzung mit Warnung
    """
    b = _briefing_to_dict(briefing)

    # Zeitersparnis: NUR aus Quick Wins ableiten
    hours = 0.0
    hours_source = "keine Angabe"

    if quickwins:
        for q in quickwins:
            try:
                h = float(q.get("time_saved_monthly_hours") or 0.0)
                hours += h
            except (ValueError, TypeError):
                pass
        if hours > 0:
            hours_source = f"Summe aus {len(quickwins)} Quick Wins"

    # NEU: Konservative Schätzung statt 40h Fallback
    if hours == 0:
        size = b.get("unternehmensgroesse", "").lower()
        if "solo" in size:
            hours = 8.0  # Solo: 2h/Woche = 8h/Monat (realistisch)
            hours_source = "Konservative Schätzung für Solo (8h/Monat)"
        else:
            hours = 16.0  # Team: 4h/Woche = 16h/Monat
            hours_source = "Konservative Schätzung für Team (16h/Monat)"

    rate = _estimate_hourly_rate(b)
    monthly = hours * rate
    invest = _parse_budget(b)
    be_months = (invest / monthly) if monthly > 0 else float('inf')

    # ROI mit Plausibilitäts-Check
    roi12_rate = ((monthly * 12) - invest) / max(invest, 1.0)
    roi12_pct = roi12_rate * 100.0

    # NEU: Warnung bei unrealistisch hohem ROI
    roi_warning = None
    if roi12_pct > 300:
        roi_warning = "ROI erscheint hoch - bitte Annahmen prüfen"
        roi12_pct = min(roi12_pct, 300)  # Cap bei 300%

    return {
        "hours": hours,
        "hours_source": hours_source,  # NEU: Transparenz
        "hourly_rate": rate,
        "monthly_value": monthly,
        "investment": invest,
        "break_even_months": be_months,
        "roi_12m": roi12_pct,
        "roi_warning": roi_warning,  # NEU: Warnung anzeigen
    }
```

**Test:**
```python
def test_roi_no_quickwins_solo():
    briefing = {"unternehmensgroesse": "solo", "investitionsbudget": "unter_2000"}
    result = calc_roi(briefing, quickwins=None)
    assert result["hours"] == 8.0, "Solo ohne QuickWins sollte 8h haben"
    assert result["roi_12m"] <= 300, "ROI sollte gedeckelt sein"
```

---

### Fix #4: Markttrends mit Quellen versehen

**Root Cause:** `services/branch_profile_engine.py:144-154`

**Lösung A: Quellen hinzufügen (Kurzfristig)**

```python
# services/branch_profile_engine.py - Zeile 144 erweitern:

"trends_de": [
    {
        "title": "AI-First Beratung",
        "description": "Beratungshäuser integrieren KI als Core-Service",
        "confidence": 0.7,  # Reduziert von 0.9
        "source": "McKinsey Global AI Survey 2024",  # NEU
        "source_url": "https://mckinsey.com/ai-survey",  # NEU
    },
    ...
],
```

**Lösung B: Research-API nutzen (Mittelfristig)**

```python
# services/market_trends_service.py (NEU)

from services.provider_perplexity import fetch_market_research

async def get_current_trends(branch: str, lang: str = "de") -> List[Dict]:
    """Fetch current trends from Perplexity with sources."""
    query = f"AI adoption trends in {branch} industry 2025"

    result = await fetch_market_research(query)

    trends = []
    for item in result.get("findings", []):
        trends.append({
            "title": item["headline"],
            "description": item["summary"],
            "confidence": item.get("confidence", 0.6),
            "source": item.get("source_name", "Marktanalyse"),
            "source_url": item.get("url"),
            "last_updated": datetime.now().isoformat(),
        })

    return trends
```

**HTML-Ausgabe mit Quellen:**
```html
<div class="trend-item">
    <strong>AI-First Beratung</strong>
    <p>Beratungshäuser integrieren KI als Core-Service</p>
    <small class="source">Quelle: McKinsey Global AI Survey 2024</small>
</div>
```

---

## P2: UX-Verbesserungen (Nächste Woche)

### Fix #5: Duplikate bei Handlungsempfehlungen eliminieren

**Root Cause:** `gpt_analyze.py:8045-8046`, `services/redundancy_detector.py:48-65`

**Lösung: Cross-Reference zwischen Sektionen**

```python
# services/redundancy_detector.py - Zeile 48 erweitern:

REDUNDANCY_SECTIONS: List[str] = [
    "exec_summary",
    "executive_summary",
    "top_3_massnahmen",  # NEU!
    "recommendations",
    ...
]

# Neue Funktion hinzufügen:
def deduplicate_recommendations(sections: Dict[str, str]) -> Dict[str, str]:
    """Remove duplicates between top_3 and full recommendations."""

    top3 = sections.get("TOP_3_MASSNAHMEN_HTML", "")
    reco = sections.get("RECOMMENDATIONS_HTML", "")

    if not top3 or not reco:
        return sections

    # Extrahiere Kernaussagen aus Top-3
    top3_phrases = extract_key_phrases(top3)

    # Entferne ähnliche Sätze aus vollständiger Liste
    cleaned_reco = remove_similar_content(reco, top3_phrases, threshold=0.85)

    # Füge Querverweis hinzu
    if cleaned_reco != reco:
        cleaned_reco = cleaned_reco.replace(
            "<h2>Handlungsempfehlungen",
            '<p class="cross-ref"><em>Die Top-3-Maßnahmen finden Sie auf Seite 2.</em></p>\n<h2>Weitere Handlungsempfehlungen'
        )

    sections["RECOMMENDATIONS_HTML"] = cleaned_reco
    return sections
```

**Integration in gpt_analyze.py:**
```python
# Nach Zeile 8635:
sections = deduplicate_recommendations(sections)
```

---

### Fix #6: Solo-Sprache korrigieren

**Root Cause:** LLM-Output ignoriert Persona-Constraints

**Lösung: Post-Processing Solo-Filter**

```python
# services/prompt_enhancer.py - Neue Funktion:

SOLO_FORBIDDEN_TERMS = [
    ("Auswertungs-Engine", "Analyse-Werkzeug"),
    ("Pipeline", "Arbeitsablauf"),
    ("Infrastruktur", "Grundlage"),
    ("skalierbare Prozesse", "wiederverwendbare Abläufe"),
    ("automatisierte Reporting-Infrastruktur", "automatische Berichtserstellung"),
    ("Data-Lake", "Datensammlung"),
    ("Microservices", "Module"),
    ("Enterprise", "Unternehmen"),
    ("Stakeholder", "Beteiligte"),
]

def apply_solo_language_filter(html: str, company_size: str) -> str:
    """Replace enterprise jargon with solo-appropriate terms."""
    if company_size.lower() != "solo":
        return html

    for enterprise_term, solo_term in SOLO_FORBIDDEN_TERMS:
        html = re.sub(
            rf'\b{enterprise_term}\b',
            solo_term,
            html,
            flags=re.IGNORECASE
        )

    return html
```

**Integration in gpt_analyze.py:**
```python
# Nach jeder Sektion:
section_html = apply_solo_language_filter(section_html, company_size)
```

---

## P3: Langfristige Optimierung

### Fix #7: Seitenzahl begrenzen

**Root Cause:** Keine Aggregat-Kontrolle über Gesamtlänge

**Lösung: Slim-Mode für Solo aktivieren**

```python
# gpt_analyze.py - Neue Konfiguration:

SECTION_PRIORITY = {
    "executive_summary": 1,     # Immer
    "top_3_massnahmen": 1,     # Immer
    "roadmap_90d": 1,          # Immer
    "business_case": 2,        # Wichtig
    "risks": 2,                # Wichtig
    "foerderpotenzial": 2,     # Wichtig
    "gamechanger": 3,          # Optional
    "wettbewerb_benchmark": 3, # Optional
    "branch_deep_dive": 4,     # Solo: Weglassen
    "vendor_audit": 4,         # Solo: Weglassen
    # ...
}

MAX_PAGES = {
    "solo": 15,
    "team": 25,
    "kmu": 40,
}

def filter_sections_for_size(sections: Dict, company_size: str) -> Dict:
    """Limit sections based on company size."""
    max_pages = MAX_PAGES.get(company_size, 25)
    current_pages = estimate_page_count(sections)

    if current_pages <= max_pages:
        return sections

    # Niedrigste Prioritäten zuerst entfernen
    priority_sorted = sorted(
        sections.keys(),
        key=lambda k: SECTION_PRIORITY.get(k, 3),
        reverse=True
    )

    for section_key in priority_sorted:
        if estimate_page_count(sections) <= max_pages:
            break
        if SECTION_PRIORITY.get(section_key, 3) >= 4:
            sections[section_key] = ""  # Sektion entfernen
            log.info(f"Removed section {section_key} for {company_size} slim mode")

    return sections
```

---

## Test-Plan

### Automatisierte Tests

```python
# tests/test_quality_fixes.py

class TestQualityFixes:

    def test_no_digital_jetzt(self):
        """Digital Jetzt should not appear anywhere."""
        funding = load_funding_programs()
        names = [p["name"] for p in funding]
        assert "Digital Jetzt" not in names

    def test_solo_funding_realistic(self):
        """Solo funding should not exceed 20k."""
        result = calculate_funding("solo", "beratung", "berlin")
        assert result.total <= 20000

    def test_roi_has_source(self):
        """ROI calculation should include source info."""
        result = calc_roi({"unternehmensgroesse": "solo"})
        assert "hours_source" in result
        assert result["hours_source"] != "keine Angabe"

    def test_trends_have_sources(self):
        """Market trends should include source references."""
        profile = get_branch_profile("beratung", "de")
        for trend in profile["trends"]:
            assert "source" in trend

    def test_no_duplicate_recommendations(self):
        """Top-3 and full recommendations should not overlap."""
        sections = generate_report(mock_briefing)
        top3 = extract_titles(sections["TOP_3_MASSNAHMEN_HTML"])
        reco = extract_titles(sections["RECOMMENDATIONS_HTML"])
        overlap = set(top3) & set(reco)
        assert len(overlap) == 0

    def test_solo_no_enterprise_jargon(self):
        """Solo reports should not contain enterprise terms."""
        report = generate_report({"unternehmensgroesse": "solo"})
        forbidden = ["Auswertungs-Engine", "Pipeline", "Infrastruktur"]
        for term in forbidden:
            assert term not in report["gamechanger"]

    def test_solo_max_pages(self):
        """Solo report should not exceed 15 pages."""
        pdf = generate_pdf({"unternehmensgroesse": "solo"})
        assert pdf.page_count <= 15
```

### Manuelle Tests

| Test | Schritte | Erwartetes Ergebnis |
|------|----------|---------------------|
| Förderung Solo | Report für Solo-Berater generieren | Fördersumme ≤ 20.000€ |
| Digital Jetzt | Suche in Report nach "Digital Jetzt" | Keine Treffer |
| ROI-Transparenz | Business-Case-Sektion prüfen | Quellenangabe für Zeitersparnis sichtbar |
| Markttrends | Trends-Sektion prüfen | Jeder Trend hat Quellenangabe |
| Keine Duplikate | S.2 und S.23 vergleichen | Verschiedene Empfehlungen |
| Solo-Sprache | Gamechanger-Sektion prüfen | Keine "Engine", "Pipeline", etc. |
| Seitenzahl Solo | PDF für Solo generieren | ≤ 15 Seiten |

---

## Implementierungs-Reihenfolge

### Sprint 1 (Sofort - 2 Tage)
- [ ] Fix #1: Digital Jetzt aus JSON/Code entfernen
- [ ] Fix #2: Solo-Funding-Cap implementieren
- [ ] Tests für #1 und #2

### Sprint 2 (Diese Woche - 3 Tage)
- [ ] Fix #3: ROI-Berechnung mit Transparenz
- [ ] Fix #4: Markttrends mit Quellen (Kurzfristig-Lösung)
- [ ] Tests für #3 und #4

### Sprint 3 (Nächste Woche - 4 Tage)
- [ ] Fix #5: Duplikat-Erkennung erweitern
- [ ] Fix #6: Solo-Sprachfilter
- [ ] Tests für #5 und #6

### Sprint 4 (Übernächste Woche - 5 Tage)
- [ ] Fix #7: Slim-Mode für Solo
- [ ] Gesamttest mit echten Briefings
- [ ] Deployment

---

## Risiko-Mitigation

| Risiko | Mitigation |
|--------|------------|
| Bestehende Reports brechen | Feature-Flag für neue Logik |
| LLM-Output weiterhin Enterprise-Sprache | Post-Processing als Fallback |
| Perplexity-API-Kosten steigen | Cache für Markttrends (24h TTL) |
| Slim-Mode entfernt wichtige Inhalte | Prioritäts-System + manuelle Überschreibung |

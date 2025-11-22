# Technical Implementation Guide: KI-Status-Report Quality Fixes

**Projekt:** KI-Sicherheit.jetzt Backend  
**Ziel:** Behebung von PDF-Generierungs- und Business-Logic-Problemen aus Report #88  
**Arbeitsweise:** Alle Fixes nacheinander durchführen  
**Erstellt:** 22.11.2025

---

## Repository Context

```
/backend
  /routes
    - briefings.py          # Briefing submission & save
    - auth.py              # Authentication
  /services
    - gpt_analyze.py       # Main analysis orchestration
    - business_calculator.py # Business case calculations
    - report_renderer.py   # HTML→PDF rendering
    - report_validator.py  # Quality checks
    - prompt_enhancer.py   # Context injection
  /templates
    - pdf_template.html    # Main PDF template
  /models
    - database.py          # SQLAlchemy models
```

**Tech Stack:** FastAPI + Python 3.11, PostgreSQL (Railway), WeasyPrint, OpenAI GPT-4, Resend

---

## Fix #1: Template Variables vollständig ersetzen

**Problem:** Im PDF stehen `{2160}`, `{6000}`, `{2.9}` statt der Werte selbst.

**Location:** `/backend/services/report_renderer.py`

**Implementation:**

```python
# In report_renderer.py nach replace_expression() einfügen:

def replace_business_variables(html: str, business_data: dict) -> str:
    """
    Replace ALL business case placeholders with actual values
    CRITICAL: Must handle ALL numeric variables
    """
    import re
    from decimal import Decimal
    
    # Define ALL possible business placeholders
    replacements = {
        "{monthly_savings}": f"{business_data.get('monthly_savings', 0):,.0f}",
        "{capex}": f"{business_data.get('capex', 0):,.0f}",
        "{opex}": f"{business_data.get('opex', 0):,.0f}",
        "{payback_months}": f"{business_data.get('payback_months', 0):.1f}",
        "{roi_12m}": f"{business_data.get('roi_12m', 0):.1f}",
        "{roi_percent}": f"{business_data.get('roi_12m', 0):.1f}",
        "{time_savings_hours}": f"{business_data.get('time_savings_hours', 0)}",
        "{hourly_rate}": f"{business_data.get('hourly_rate', 80)}",
    }
    
    # Replace all
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)
    
    # VALIDATION: Check for unreplaced placeholders
    remaining = re.findall(r'\{[a-z_]+\}', html)
    if remaining:
        logger.error(f"❌ Unreplaced template variables: {remaining}")
    
    return html

# In render_report() method - AFTER replace_expression():
html = replace_business_variables(html, context.get('business_case', {}))
```

**Test:**
```python
assert "{" not in final_html or "<script" in final_html  # Allow {braces} in JS only
```

---

## Fix #2: UTF-8 Encoding bei Briefing-Save

**Problem:** `"FragebÃ¶gen"`, `"MarktfÃ¼hrer"` werden falsch in PostgreSQL gespeichert.

**Location:** `/backend/routes/briefings.py`

**Dependencies:**
```bash
pip install ftfy
# Add to requirements.txt
```

**Implementation:**

```python
# In routes/briefings.py - VOR dem DB-Save

def clean_utf8_briefing(briefing_data: dict) -> dict:
    """
    Fix UTF-8 encoding corruption BEFORE saving to database
    
    Common issues:
    - Ã¶ → ö (FragebÃ¶gen → Fragebögen)
    - Ã¼ → ü (MarktfÃ¼hrer → Marktführer)
    """
    import ftfy
    
    def fix_string(s: str) -> str:
        if not isinstance(s, str):
            return s
        
        fixed = ftfy.fix_text(s)
        
        if fixed != s:
            logger.info(f"[UTF-8-FIX] '{s}' → '{fixed}'")
        
        return fixed
    
    def fix_recursive(obj):
        """Recursively fix all strings in nested dict/list"""
        if isinstance(obj, dict):
            return {k: fix_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [fix_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return fix_string(obj)
        return obj
    
    return fix_recursive(briefing_data)

# In submit_briefing() route - AFTER parsing JSON, BEFORE saving to DB:
logger.info("[ENCODING-FIX] Cleaning briefing data before save")
briefing_data = clean_utf8_briefing(briefing_json)

# Then save as usual
briefing = Briefing(
    user_id=user.id,
    briefing_data=briefing_data,  # Now cleaned
    ...
)
```

**Test:**
```python
corrupted = {"text": "FragebÃ¶gen"}
cleaned = clean_utf8_briefing(corrupted)
assert cleaned["text"] == "Fragebögen"
assert "Ã" not in json.dumps(cleaned)
```

---

## Fix #3: Size-Aware Business Case Kalkulation

**Problem:** Solo-Betrieb mit <100k Umsatz bekommt unrealistische "4.500 € monatliche Einsparung".

**Location:** `/backend/services/business_calculator.py`

**Implementation:**

```python
# In business_calculator.py - NEUE Funktion einfügen:

def get_size_constraints(
    unternehmensgroesse: str,
    jahresumsatz_range: str,
    investitionsbudget: str
) -> dict:
    """
    Define realistic constraints by company size
    """
    
    # Parse revenue range
    revenue_mapping = {
        "unter_100k": 50000,
        "100k_500k": 250000,
        "500k_2m": 1000000,
        "2m_10m": 5000000,
        "ueber_10m": 20000000
    }
    annual_revenue = revenue_mapping.get(jahresumsatz_range, 100000)
    monthly_revenue = annual_revenue / 12
    
    # Parse investment budget
    investment_mapping = {
        "unter_2000": 1000,
        "2000_10000": 5000,
        "10000_50000": 25000,
        "50000_250000": 125000,
        "ueber_250000": 500000
    }
    max_investment = investment_mapping.get(investitionsbudget, 10000)
    
    # Size-specific constraints
    constraints = {
        "solo": {
            "max_monthly_savings": min(monthly_revenue * 0.3, 2000),
            "max_capex": min(max_investment, 10000),
            "max_opex_monthly": 200,
            "hourly_rate": 80,
            "max_team_size": 2,
            "max_time_savings_hours": 20,
        },
        "klein": {
            "max_monthly_savings": min(monthly_revenue * 0.4, 10000),
            "max_capex": min(max_investment, 50000),
            "max_opex_monthly": 1000,
            "hourly_rate": 100,
            "max_team_size": 5,
            "max_time_savings_hours": 80,
        },
        "mittel": {
            "max_monthly_savings": min(monthly_revenue * 0.5, 50000),
            "max_capex": min(max_investment, 250000),
            "max_opex_monthly": 5000,
            "hourly_rate": 120,
            "max_team_size": 20,
            "max_time_savings_hours": 200,
        },
        "gross": {
            "max_monthly_savings": monthly_revenue * 0.6,
            "max_capex": max_investment,
            "max_opex_monthly": 20000,
            "hourly_rate": 150,
            "max_team_size": 100,
            "max_time_savings_hours": 500,
        }
    }
    
    size = unternehmensgroesse if unternehmensgroesse in constraints else "klein"
    return constraints[size]

# MODIFY calculate_business_case():

def calculate_business_case(
    briefing: dict,
    time_savings_hours: int = 36
) -> dict:
    """
    Calculate realistic business case based on company size
    """
    
    # Get size constraints
    constraints = get_size_constraints(
        unternehmensgroesse=briefing.get("unternehmensgroesse", "klein"),
        jahresumsatz_range=briefing.get("jahresumsatz", "100k_500k"),
        investitionsbudget=briefing.get("investitionsbudget", "2000_10000")
    )
    
    # Cap time savings to realistic maximum
    capped_hours = min(time_savings_hours, constraints["max_time_savings_hours"])
    
    # Calculate monthly savings
    monthly_savings = capped_hours * constraints["hourly_rate"]
    monthly_savings = min(monthly_savings, constraints["max_monthly_savings"])
    
    # Determine CAPEX based on investment budget
    capex = min(6000, constraints["max_capex"])
    
    # OPEX stays reasonable
    opex = min(120, constraints["max_opex_monthly"])
    
    # Calculate payback & ROI
    payback_months = capex / monthly_savings if monthly_savings > 0 else 999
    roi_12m = ((monthly_savings * 12 - opex * 12 - capex) / capex * 100) if capex > 0 else 0
    
    return {
        "monthly_savings": int(monthly_savings),
        "time_savings_hours": capped_hours,
        "capex": int(capex),
        "opex": int(opex),
        "payback_months": round(payback_months, 1),
        "roi_12m": round(roi_12m, 1),
        "hourly_rate": constraints["hourly_rate"],
        "constraints_applied": constraints,
    }

# ADD Validation:

def validate_business_case_plausibility(
    business_case: dict,
    briefing: dict
) -> list[str]:
    """
    Plausibility checks - return warnings if unrealistic
    """
    warnings = []
    
    revenue_map = {
        "unter_100k": 50000,
        "100k_500k": 250000,
        "500k_2m": 1000000,
        "2m_10m": 5000000,
        "ueber_10m": 20000000
    }
    annual_revenue = revenue_map.get(briefing.get("jahresumsatz"), 100000)
    monthly_revenue = annual_revenue / 12
    
    # Check 1: Savings vs Revenue
    if business_case["monthly_savings"] > monthly_revenue * 0.5:
        warnings.append(
            f"⚠️ Monatliche Einsparung ({business_case['monthly_savings']}€) "
            f"übersteigt 50% des Monatsumsatzes (~{monthly_revenue:.0f}€)"
        )
    
    # Check 2: CAPEX vs Investment Budget
    investment_max = {
        "unter_2000": 2000,
        "2000_10000": 10000,
        "10000_50000": 50000,
        "50000_250000": 250000,
        "ueber_250000": 500000
    }.get(briefing.get("investitionsbudget"), 10000)
    
    if business_case["capex"] > investment_max:
        warnings.append(
            f"⚠️ CAPEX ({business_case['capex']}€) übersteigt "
            f"Investment-Budget ({investment_max}€)"
        )
    
    # Check 3: ROI too good to be true
    if business_case["roi_12m"] > 500:
        warnings.append(
            f"⚠️ ROI von {business_case['roi_12m']:.0f}% unrealistisch hoch"
        )
    
    return warnings

# In gpt_analyze.py nach Business-Case-Berechnung:
warnings = validate_business_case_plausibility(business_case, briefing_data)
if warnings:
    logger.warning(f"[BUSINESS-CASE] Plausibility warnings:\n" + "\n".join(warnings))
```

**Test:**
```python
briefing_solo = {
    "unternehmensgroesse": "solo",
    "jahresumsatz": "unter_100k",
    "investitionsbudget": "2000_10000"
}
bc = calculate_business_case(briefing_solo, time_savings_hours=100)
assert bc["monthly_savings"] <= 2000
assert bc["capex"] <= 10000
```

---

## Fix #4: Size-Inappropriate Content Filter

**Problem:** Report enthält "Abteilung", "Team von 5 Entwicklern" bei Solo-Betrieb.

**Location:** `/backend/services/report_validator.py`

**Implementation:**

```python
# In report_validator.py - NEUE Funktionen:

SIZE_INAPPROPRIATE_TERMS = {
    "solo": {
        "Abteilung": "Bereich",
        "Abteilungen": "Bereiche",
        "die Geschäftsleitung": "Sie",
        "das Management": "Sie",
        "Ihr Team": "Sie",
        "Mitarbeiter": "Freelancer oder Partner",
        "HR-Abteilung": "HR-Prozesse",
        "IT-Abteilung": "IT-Setup",
    },
    "klein": {
        "der Konzern": "das Unternehmen",
        "Vorstand": "Geschäftsführung",
    }
}

def filter_size_inappropriate_content(
    content: str,
    unternehmensgroesse: str
) -> str:
    """
    Replace size-inappropriate terms with better alternatives
    """
    
    size = unternehmensgroesse if unternehmensgroesse in SIZE_INAPPROPRIATE_TERMS else "solo"
    replacements = SIZE_INAPPROPRIATE_TERMS.get(size, {})
    
    for inappropriate, replacement in replacements.items():
        if inappropriate in content:
            logger.info(f"[CONTENT-FILTER] Replacing '{inappropriate}' with '{replacement}' for {size}")
            content = content.replace(inappropriate, replacement)
    
    return content

# In validate_report() - ADD check:

def validate_report(sections: dict, briefing: dict) -> dict:
    """
    Validation with size-inappropriate content check
    """
    # ... existing validation ...
    
    size = briefing.get("unternehmensgroesse", "klein")
    
    for section_name, section_content in sections.items():
        if not isinstance(section_content, str):
            continue
        
        # Check for inappropriate terms
        inappropriate_terms = SIZE_INAPPROPRIATE_TERMS.get(size, {}).keys()
        found_terms = [term for term in inappropriate_terms if term in section_content]
        
        if found_terms:
            warnings.append({
                "type": "SIZE_INAPPROPRIATE_CONTENT",
                "section": section_name,
                "message": f"Unangemessen für '{size}': {', '.join(found_terms)}",
                "severity": "warning"
            })
    
    # ... rest of validation ...
```

**In gpt_analyze.py - Apply filter BEFORE rendering:**

```python
# After all sections generated, BEFORE HTML rendering:
logger.info(f"[CONTENT-FILTER] Filtering size-inappropriate content for {briefing_data.get('unternehmensgroesse')}")

for section_key, section_value in sections.items():
    if isinstance(section_value, str):
        sections[section_key] = filter_size_inappropriate_content(
            section_value,
            briefing_data.get("unternehmensgroesse", "klein")
        )
```

**Test:**
```python
content = "Die IT-Abteilung sollte ein Team von 5 Entwicklern aufbauen."
filtered = filter_size_inappropriate_content(content, "solo")
assert "Abteilung" not in filtered
```

---

## Fix #5: Roadmap-Dimensionierung nach Größe

**Problem:** 90-Tage Roadmap plant "50.000 € CAPEX" für Solo-Betrieb.

**Location:** `/backend/services/prompt_enhancer.py`

**Implementation:**

```python
# In prompt_enhancer.py - ADD:

ROADMAP_CONSTRAINTS = {
    "solo": {
        "max_budget_total": 10000,
        "max_budget_per_phase": 3000,
        "team_structure": "Sie + maximal 1-2 Freelancer",
        "phase_duration_weeks": 4,
        "example_team": "1 Backend-Dev (Freelance, 20h)",
        "realistic_capacity": "Sie arbeiten hauptsächlich selbst, Freelancer für Spezialaufgaben"
    },
    "klein": {
        "max_budget_total": 50000,
        "max_budget_per_phase": 15000,
        "team_structure": "Kernteam + externe Experten",
        "phase_duration_weeks": 4,
        "example_team": "2-3 Entwickler + 1 Projektleiter",
        "realistic_capacity": "Kleines internes Team + punktuelle Verstärkung"
    },
    "mittel": {
        "max_budget_total": 200000,
        "max_budget_per_phase": 60000,
        "team_structure": "Dediziertes Projektteam",
        "phase_duration_weeks": 6,
        "example_team": "5-8 Entwickler + PM + Architect",
        "realistic_capacity": "Vollständiges Projektteam mit verschiedenen Rollen"
    }
}

def enhance_roadmap_prompt(base_prompt: str, context: dict) -> str:
    """
    Inject size-specific constraints into roadmap prompt
    """
    
    size = context.get("unternehmensgroesse", "klein")
    constraints = ROADMAP_CONSTRAINTS.get(size, ROADMAP_CONSTRAINTS["klein"])
    
    # Get investment budget from briefing
    investment_budget = context.get("investitionsbudget", "2000_10000")
    investment_map = {
        "unter_2000": 2000,
        "2000_10000": 10000,
        "10000_50000": 50000,
        "50000_250000": 250000,
        "ueber_250000": 500000
    }
    max_realistic_budget = min(
        constraints["max_budget_total"],
        investment_map.get(investment_budget, 10000)
    )
    
    size_context = f"""
KRITISCHE VORGABEN - Unternehmensgröße: {size.upper()}

Budget-Grenzen (STRIKT EINHALTEN!):
- Gesamt-Budget für 90 Tage: MAX €{max_realistic_budget:,}
- Budget pro Phase: MAX €{constraints['max_budget_per_phase']:,}
- Angegebenes Investment-Budget: {investment_budget}

Team-Struktur (REALISTISCH!):
- {constraints['team_structure']}
- Beispiel: {constraints['example_team']}
- Kapazität: {constraints['realistic_capacity']}

VERBOTEN für {size}:
- KEINE "5 Entwickler + Projektleiter" bei Solo/Klein
- KEINE Budgets > €{max_realistic_budget:,}
- KEINE unrealistischen Teamgrößen

Die Roadmap MUSS mit dem realen Budget und der Unternehmensgröße umsetzbar sein!
"""
    
    return f"{size_context}\n\n{base_prompt}"

# In inject_context() - Apply to roadmap prompts:

if prompt_key in ["roadmap", "roadmap_12m", "pilot_plan"]:
    prompt = enhance_roadmap_prompt(prompt, context)
```

**Test:**
```python
context = {
    "unternehmensgroesse": "solo",
    "investitionsbudget": "2000_10000"
}
prompt = enhance_roadmap_prompt("Create a roadmap...", context)
assert "MAX €10" in prompt
assert "Solo" in prompt.upper()
```

---

## Fix #6: Score-Kontext & Relativierung

**Problem:** Score 91/100 wirkt übertrieben für Solo mit <100k Umsatz.

**Location:** `/backend/templates/pdf_template.html` und `/backend/services/gpt_analyze.py`

**Implementation in gpt_analyze.py:**

```python
# After score calculation - ADD:

BENCHMARK_SCORES = {
    "solo": {"avg": 65, "top10": 82},
    "klein": {"avg": 72, "top10": 88},
    "mittel": {"avg": 78, "top10": 92},
    "gross": {"avg": 82, "top10": 95}
}

def get_score_context(overall_score: int, size: str) -> dict:
    """Generate contextual score interpretation"""
    
    benchmark = BENCHMARK_SCORES.get(size, BENCHMARK_SCORES["klein"])
    
    if overall_score >= benchmark["top10"]:
        rating = "exzellent - Sie gehören zu den Top 10%"
    elif overall_score >= benchmark["avg"] + 10:
        rating = "überdurchschnittlich"
    elif overall_score >= benchmark["avg"]:
        rating = "gut - über dem Durchschnitt"
    elif overall_score >= benchmark["avg"] - 10:
        rating = "solide - im Durchschnitt"
    else:
        rating = "ausbaufähig - unter dem Durchschnitt"
    
    size_labels = {
        "solo": "Solo-Berater",
        "klein": "Kleinunternehmen",
        "mittel": "mittelständisches Unternehmen",
        "gross": "Großunternehmen"
    }
    
    return {
        "score_rating": rating,
        "size_label": size_labels.get(size, "Unternehmen"),
        "avg_score_for_size": benchmark["avg"],
        "top10_score_for_size": benchmark["top10"]
    }

# Add to context:
context["score_context"] = get_score_context(
    overall_score=scores["overall"],
    size=briefing_data.get("unternehmensgroesse", "klein")
)
```

**Implementation in pdf_template.html:**

```html
<!-- In Executive Summary section nach den Score-Badges: -->

<div class="score-context" style="
    background: #f0f9ff; 
    border-left: 4px solid #3b82f6; 
    padding: 1rem; 
    margin: 1rem 0;
">
    <strong>📊 Score-Einordnung:</strong>
    <p>
        Ihr Gesamt-Score von <strong>{{ overall_score }}/100</strong> ist 
        <em>für einen {{ score_context.size_label }} {{ score_context.score_rating }}</em>.
    </p>
    <p style="margin: 0.5rem 0; font-size: 0.9em; color: #64748b;">
        Zum Vergleich: Durchschnitt {{ score_context.size_label }}: {{ score_context.avg_score_for_size }}/100 | 
        Top 10% {{ score_context.size_label }}: {{ score_context.top10_score_for_size }}/100
    </p>
</div>
```

---

## Fix #7: Gamechanger realistischer formulieren

**Problem:** "100 Partner × €299 = €3.4 Mio ARR" für Solo-Start unrealistisch.

**Location:** `/backend/services/prompts/gamechanger.txt`

**Implementation:**

```
# In gamechanger.txt - Add size-specific constraints:

WICHTIGE KONTEXT-INFORMATION - Unternehmensgröße:
{{ unternehmensgroesse }}

REALISTISCHE GAMECHANGER-SKALIERUNG nach Größe:

{% if unternehmensgroesse == "solo" %}
Solo-Betrieb - Gamechanger in 12-18 Monaten alleine/mit 1-2 Freelancern erreichbar:
- Erste 5-10 Partner/Kunden in 12 Monaten (NICHT 100!)
- ARR-Ziel: €50k-150k im ersten Jahr (NICHT €3.4 Mio!)
- Team-Wachstum: Von 1 auf 2-3 Personen
- Investition: Max. €10-20k

Beispiel GUTER Solo-Gamechanger:
"White-Label für 10 Partner in 12 Monaten → €30k MRR (€360k ARR)"

Beispiel SCHLECHTER Solo-Gamechanger (unrealistisch!):
"100 Partner in 6 Monaten → €3.4 Mio ARR" ❌

{% elif unternehmensgroesse == "klein" %}
Klein-Unternehmen - Mit bestehendem Team + Budget umsetzbar:
- 20-50 neue Kunden/Partner in 12 Monaten
- ARR-Ziel: €250k-1M
- Team-Wachstum: +3-5 Personen
- Investition: €50-100k

{% else %}
Mittelstand/Konzern - Ambitionierte aber machbare Skalierung:
- 100+ neue Kunden in 12-18 Monaten
- ARR-Ziel: €1M-10M
- Dediziertes Produktteam
- Investition: €100k-500k
{% endif %}

VERMEIDE:
- Fantasy-Zahlen ohne VC-Funding
- "10× Wachstum in 3 Monaten" für Solo
- Benchmarks von Venture-Backed Startups
```

---

## Fix #8: Research-Daten Provenance

**Problem:** User sieht nicht woher Research-Daten kommen.

**Location:** `/backend/templates/pdf_template.html` und `/backend/services/gpt_analyze.py`

**Implementation in gpt_analyze.py:**

```python
# After research_pipeline.run() - ADD:
from datetime import datetime

research_sources = [
    {
        "provider": "Tavily",
        "query_type": "Tools & Funding",
        "date": datetime.now().strftime("%d.%m.%Y")
    },
    {
        "provider": "Perplexity",
        "query_type": "Markt & Wettbewerb",
        "date": datetime.now().strftime("%d.%m.%Y")
    }
]

context["research_sources"] = research_sources
context["report_date"] = datetime.now().strftime("%d.%m.%Y")
```

**Implementation in pdf_template.html:**

```html
<!-- In Research-basierte Sections (Wettbewerb, Tools): -->

{% if research_sources %}
<div class="research-provenance" style="
    font-size: 0.85em; 
    color: #64748b; 
    margin-top: 1rem;
    padding: 0.5rem;
    background: #f8fafc;
    border-radius: 4px;
">
    <strong>📊 Datenquellen:</strong>
    {% for source in research_sources %}
        {{ source.provider }} ({{ source.query_type }}, {{ source.date }}){% if not loop.last %} • {% endif %}
    {% endfor %}
    <br>
    <small style="opacity: 0.8;">
        Diese Informationen wurden am {{ report_date }} recherchiert und können sich ändern.
    </small>
</div>
{% endif %}
```

---

## Testing

### Unit Tests

```python
# tests/test_business_calculator.py

def test_solo_constraints():
    """Solo-Betrieb sollte realistische Grenzen haben"""
    briefing = {
        "unternehmensgroesse": "solo",
        "jahresumsatz": "unter_100k",
        "investitionsbudget": "2000_10000"
    }
    
    bc = calculate_business_case(briefing, time_savings_hours=100)
    
    assert bc["monthly_savings"] <= 2000
    assert bc["capex"] <= 10000
    assert bc["time_savings_hours"] <= 20

def test_utf8_cleaning():
    """UTF-8 corruption should be fixed"""
    corrupted = {
        "text": "FragebÃ¶gen",
        "nested": {"more": "MarktfÃ¼hrer"}
    }
    
    cleaned = clean_utf8_briefing(corrupted)
    
    assert cleaned["text"] == "Fragebögen"
    assert cleaned["nested"]["more"] == "Marktführer"
    assert "Ã" not in json.dumps(cleaned)

def test_template_variable_replacement():
    """All placeholders should be replaced"""
    html = "<p>Savings: {monthly_savings} €</p><p>CAPEX: {capex}</p>"
    business_data = {"monthly_savings": 2000, "capex": 6000}
    
    result = replace_business_variables(html, business_data)
    
    assert "{monthly_savings}" not in result
    assert "2" in result
```

### Integration Test

```python
# tests/test_report_generation.py

def test_solo_report_realistic():
    """End-to-end: Solo-Report should have realistic numbers"""
    briefing = load_test_briefing("solo_unter_100k.json")
    
    # Run full analysis
    analysis_id = trigger_analysis(briefing)
    report = wait_for_report(analysis_id)
    
    # Assertions
    assert report.business_case["monthly_savings"] <= 2000
    assert "Abteilung" not in report.pdf_text
    assert "{" not in report.pdf_text
    assert "Fragebögen" in report.pdf_text
```

---

## Deployment

```bash
# Install dependencies
pip install ftfy
echo "ftfy" >> requirements.txt

# Commit changes
git add .
git commit -m "fix: report quality improvements (UTF-8, business case, content filtering)"

# Deploy to Railway
railway up

# Monitor logs
railway logs --tail 100
```

---

## Success Criteria

Nach Implementierung aller Fixes sollten folgende Kriterien erfüllt sein:

- [ ] **Fix #1:** 0 Template-Variablen `{...}` im PDF sichtbar
- [ ] **Fix #2:** 0 UTF-8-Fehler (keine `Ã¶`, `Ã¼`, `Ã¤` mehr in DB/PDF)
- [ ] **Fix #3:** Business Cases realistisch für Unternehmensgröße
  - Solo: max. 2.000€/Monat Einsparung, max. 10.000€ CAPEX
  - Klein: max. 10.000€/Monat, max. 50.000€ CAPEX
- [ ] **Fix #4:** 0 "Abteilung" bei Solo-Reports
- [ ] **Fix #5:** Roadmap-Budgets ≤ Investment-Budget aus Briefing
- [ ] **Fix #6:** Scores haben Benchmark-Kontext ("für Solo exzellent")
- [ ] **Fix #7:** Gamechanger realistisch skaliert (Solo: 5-10 Partner, nicht 100)
- [ ] **Fix #8:** Research-Quellen dokumentiert (Tavily, Perplexity)

---

## Troubleshooting

### Problem: ftfy nicht installiert
```bash
railway run pip install ftfy
railway restart
```

### Problem: Template variables noch sichtbar
```python
# Check in report_renderer.py ob replace_business_variables() aufgerufen wird
# Check Logs für "Unreplaced template variables"
```

### Problem: UTF-8 noch falsch
```python
# Check ob clean_utf8_briefing() VOR db.add(briefing) aufgerufen wird
# Check Logs für "[UTF-8-FIX]" Einträge
```

### Problem: Business Case noch unrealistisch
```python
# Check ob get_size_constraints() korrekt implementiert
# Check Logs für "[BUSINESS-CASE] Plausibility warnings"
```

---

## Nächste Schritte nach Implementierung

1. **Test-Report generieren** mit Solo-Profil (<100k Umsatz)
2. **PDF prüfen auf:**
   - Keine `{placeholders}`
   - Korrekte Umlaute (Fragebögen, nicht FragebÃ¶gen)
   - Realistische Zahlen (max. 2.000€ Einsparung für Solo)
   - Keine "Abteilungen" bei Solo
3. **Logs monitoren** auf Warnings/Errors
4. **Feedback sammeln** von echten Usern

---

## Support & Kontakt

- **Railway Logs:** `railway logs --tail 100`
- **Database:** `railway connect` → PostgreSQL
- **PDF Debug:** Check `/tmp/report_debug_*.html` auf Railway

**Erstellt von:** Wolf Hohl  
**Datum:** 22.11.2025  
**Version:** 1.0

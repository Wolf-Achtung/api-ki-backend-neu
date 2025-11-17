# services/extra_sections.py
import os, json, html

def calc_business_case(answers: dict, env: dict):
    stundensatz = int(os.getenv("DEFAULT_STUNDENSATZ_EUR", env.get("DEFAULT_STUNDENSATZ_EUR", 60)))
    qw1 = int(os.getenv("DEFAULT_QW1_H", env.get("DEFAULT_QW1_H", 10)))
    qw2 = int(os.getenv("DEFAULT_QW2_H", env.get("DEFAULT_QW2_H", 8)))
    fallback = int(os.getenv("FALLBACK_QW_MONTHLY_H", env.get("FALLBACK_QW_MONTHLY_H", 18)))

    total_hours = answers.get("sum_quickwin_hours")
    if not isinstance(total_hours, (int, float)):
        total_hours = qw1 + qw2 + fallback

    einsparung_monat_eur = int(total_hours * stundensatz)

    band = (answers.get("investitionsbudget") or "").lower()
    if "unter_2000" in band:
        capex = 1500
    elif "2000_10000" in band:
        capex = 6000
    elif "10000" in band:
        capex = 12000
    else:
        capex = 4000

    groesse = answers.get("unternehmensgroesse", "solo")
    rev = answers.get("jahresumsatz", "unter_100k")
    opex = 180 if groesse == "solo" else 350
    if "unter_100k" in rev:
        opex = max(120, opex - 60)

    monatlicher_nutzen = einsparung_monat_eur - opex
    payback = round(capex / monatlicher_nutzen, 1) if monatlicher_nutzen > 0 else None
    roi_12m = einsparung_monat_eur * 12 - (capex + opex * 12)

    table = f"""
    <section class="card">
      <h2>Business‑Case (realistische Annahmen)</h2>
      <table class="table">
        <thead><tr><th>Parameter</th><th>Wert</th><th>Erläuterung</th></tr></thead>
        <tbody>
          <tr><td>Gesamteinsparung</td><td>{total_hours} h/Monat</td><td>Summe Quick‑Wins</td></tr>
          <tr><td>Stundensatz</td><td>{stundensatz} €</td><td>DEFAULT_STUNDENSATZ_EUR</td></tr>
          <tr><td>Monetärer Nutzen</td><td>{einsparung_monat_eur} €/Monat</td><td>Einsparung × Stundensatz</td></tr>
          <tr><td>Einführungskosten (CAPEX)</td><td>{capex} €</td><td>Mittel des Budgetbandes</td></tr>
          <tr><td>Laufende Kosten (OPEX)</td><td>{opex} €/Monat</td><td>Lizenzen & Betrieb</td></tr>
          <tr><td>Amortisation</td><td>{'—' if payback is None else f'{payback} Monate'}</td><td>CAPEX ÷ (Nutzen − OPEX)</td></tr>
          <tr><td>ROI nach 12 Monaten</td><td>{roi_12m} €</td><td>Nutzen×12 − (CAPEX + OPEX×12)</td></tr>
        </tbody>
      </table>
    </section>"""
    return {
        "CAPEX_REALISTISCH_EUR": capex,
        "OPEX_REALISTISCH_EUR": opex,
        "EINSPARUNG_MONAT_EUR": einsparung_monat_eur,
        "PAYBACK_MONTHS": payback,
        "ROI_12M": roi_12m,
        "BUSINESS_CASE_TABLE_HTML": table
    }

def build_benchmarks_section(scores: dict, path="data/benchmarks.json"):
    # (Lese JSON, rendere Tabelle + kleines Inline‑SVG; analog zu deinem Konzept)
    return "<section class='card'><h2>Benchmark‑Vergleich</h2>…</section>"

def build_starter_stacks(answers: dict, path="data/starter_stacks.json"):
    # (Lese global/all und rendere 4–8 Karten)
    return "<section class='card'><h2>Werkbank & Starter‑Stacks</h2>…</section>"

def build_responsible_ai_section(paths: dict):
    # (Lese knowledge/four_pillars.html + legal_pitfalls.html; robust mit Fallback)
    return "<section class='card'><h2>Verantwortungsvolle KI & Compliance</h2>…</section>"

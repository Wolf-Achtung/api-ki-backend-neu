# -*- coding: utf-8 -*-
from services.report_pipeline import render_report_html

briefing = {
    "unternehmen_name": "Beispiel GmbH",
    "branche": "Beratung",
    "bundesland": "Berlin",
    "jahresumsatz": "unter_100k",
    "unternehmensgroesse": "solo",
    "ki_knowhow": "fortgeschritten",
    "zeitbudget": "ueber_10",
    "ki_usecases": ["texterstellung","prozessautomatisierung","marketing"],
}
snippets = {
    "EXECUTIVE_SUMMARY_HTML": "<ul><li><strong>Reifegrad:</strong> 72/100 – Prozesse stark, Governance ausbaufähig.</li></ul><p class='small'>Dieser Report wurde teilweise mit KI‑Unterstützung erstellt.</p>",
    "QUICK_WINS_HTML_LEFT": "<div class='qwin'><h3>Report‑Automation</h3><ul><li>Nutzen: + Zeitersparnis</li></ul></div>",
    "QUICK_WINS_HTML_RIGHT": "<div class='qwin'><h3>RAG‑Wissensbasis</h3><ul><li>Nutzen: + Trefferquote</li></ul></div>",
    "PILOT_PLAN_HTML": "<ol><li>Test</li><li>Pilot</li><li>Rollout</li></ol>",
    "ROI_HTML": "<p>Payback ≈ 3 Monate.</p>",
    "COSTS_OVERVIEW_HTML": "<table class='table'><tr><th>CapEx</th><td>6.000 €</td></tr></table>",
    "RISKS_HTML": "<table class='table'><tr><th>Risiko</th><th>Mitigation</th></tr><tr><td>DSGVO</td><td>PII vermeiden</td></tr></table>",
    "GAMECHANGER_HTML": "<p>Transformative Wirkung durch standardisierte KI‑Beratung.</p>",
    "FOERDERPROGRAMME_HTML": "<ul><li><a href='#'>Digital Jetzt</a></li></ul>",
    "QUELLEN_HTML": "<ul><li><a href='#'>EU AI Act</a></li></ul>",
    "TOOLS_HTML": "<ul><li><a href='#'>Mistral AI</a> – EU‑Hosting.</li></ul>",
}
html = render_report_html(briefing, snippets)
with open("test_output.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Wrote test_output.html")

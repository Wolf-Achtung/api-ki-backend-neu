# services/research_pipeline.py – Build HTML tables for tools & funding
import os, html, datetime
from .research_clients import hybrid_search

DAYS = int(os.getenv("RESEARCH_DAYS","7"))

def _now_iso():
    return datetime.date.today().isoformat()

def run_research(answers: dict) -> dict:
    # Basic queries based on answers
    land = answers.get("BUNDESLAND_LABEL") or answers.get("bundesland") or ""
    branche = answers.get("BRANCHE_LABEL") or answers.get("branche") or ""
    # Tools
    tools_q = [
        f"{branche} KI Tools EU Datenschutz",
        "OpenAI GPT‑4o EU privacy",
        "Azure OpenAI EU region",
        "Mistral AI policies EU",
        "RAG open source FAISS LiteLLM"
    ]
    tool_rows = []
    for q in tools_q:
        for r in hybrid_search(q, 10):
            title = html.escape(r.get("title") or "Quelle")
            url = html.escape(r.get("url") or "#")
            desc = html.escape(r.get("description") or "")
            tool_rows.append(f"<tr><td><strong>{title}</strong></td><td>-</td><td>-</td><td>-</td><td><a href='{url}' target='_blank' rel='noopener'>Quelle</a></td></tr>")

    tools_table = "<table class='table'><thead><tr><th>Tool/Produkt</th><th>Kategorie</th><th>Preis</th><th>DSGVO/Host</th><th>Links</th></tr></thead><tbody>" + "".join(tool_rows[:20]) + "</tbody></table>"

    # Funding
    fund_q = [
        f"{land} Digitalisierung Förderung KMU",
        f"{land} Innovation Förderung KI",
        "BMWK Förderung Digital jetzt",
        "EU Förderung KI KMU"
    ]
    fund_rows = []
    for q in fund_q:
        for r in hybrid_search(q, 8):
            title = html.escape(r.get("title") or "Programm")
            url = html.escape(r.get("url") or "#")
            fund_rows.append(f"<tr><td>{title}</td><td>—</td><td>KMU</td><td>—</td><td>—</td><td><a href='{url}' target='_blank' rel='noopener'>Offizielle Infos</a></td></tr>")

    funding_table = "<table class='table'><thead><tr><th>Programm</th><th>Förderung</th><th>Zielgruppe</th><th>Deadline</th><th>Eligibility</th><th>Quelle</th></tr></thead><tbody>" + "".join(fund_rows[:12]) + "</tbody></table>"

    return {
        "TOOLS_TABLE_HTML": tools_table,
        "FUNDING_TABLE_HTML": funding_table,
        "last_updated": _now_iso()
    }

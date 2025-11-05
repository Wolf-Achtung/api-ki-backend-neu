# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Any, List, Tuple
import os, re, base64, hmac, hashlib

try:
    from .sanitize import ensure_utf8  # type: ignore
except Exception:  # pragma: no cover - fallback for standalone usage
    def ensure_utf8(x: str) -> str:
        return (x or "").encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

EM_DASH = "—"

def _table(headers: List[str], rows: List[Tuple[str, ...]]) -> str:
    parts: List[str] = []
    parts.append('<table class="table"><thead><tr>')
    for h in headers:
        parts.append(f"<th>{ensure_utf8(h)}</th>")
    parts.append("</tr></thead><tbody>")
    for r in rows:
        parts.append("<tr>")
        for c in r:
            parts.append(f"<td>{ensure_utf8(c)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)

def _p(s: str) -> str:
    return f"<p>{ensure_utf8(s)}</p>"

def _to_eur(v: float) -> str:
    s = f"{v:,.2f} €"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def _parse_budget_range(text: str) -> float:
    if not text:
        return 0.0
    t = str(text).strip()
    m = re.match(r"(\d+)[^\d]+(\d+)", t)
    if not m:
        m = re.match(r"(\d+)_?(\d+)?", t)
    if m:
        low = float(m.group(1)); high = float(m.group(2) or m.group(1))
        return (low + high) / 2.0
    try:
        return float(t)
    except Exception:
        return 0.0

def _branch_defaults(branche: str, size: str) -> Dict[str, Any]:
    b = (branche or "").lower()
    defaults = {
        "beratung": {
            "kpis": [
                ("Durchlaufzeit Angebot", "Zeit von Anfrage bis Angebot", "≤ 24 h"),
                ("Antwortzeit Kundenchat", "Median in Bürozeiten", "≤ 30 min"),
                ("Wiederverwendbare Vorlagen", "Anteil standardisierter Antworten", "≥ 60 %"),
                ("Automatisierungsgrad", "Anteil automatisierter Schritte", "≥ 40 %"),
            ],
            "tools": [
                ("Notion AI (Business)", "Notion", "ab ~20 €/User/Monat", "Wissensbasis & Doku (EU‑Optionen)"),
                ("Typeform (EU API)", "Typeform", "ab ~30–70 €/Monat", "Formulare/Fragebögen mit EU‑Endpunkt"),
                ("Make.com", "Make", "ab ~9–29 €/Monat", "No‑Code Automationen, Webhooks"),
                ("n8n (Self‑Hosted)", "n8n", "Open Source", "Automationsplattform, On‑Prem möglich"),
                ("Claude (Workplaces)", "Anthropic", "Pay‑per‑use", "LLM für Auswertung/Content, DE‑stark"),
            ],
        }
    }
    d = defaults.get(b, defaults["beratung"])
    kpis = list(d["kpis"])
    s = (size or "").lower()
    if s == "solo":
        kpis[0] = (kpis[0][0], kpis[0][1], "≤ 48 h")
        kpis[1] = (kpis[1][0], kpis[1][1], "≤ 60 min")
    elif s == "team_2_10":
        kpis[0] = (kpis[0][0], kpis[0][1], "≤ 36 h")
        kpis[1] = (kpis[1][0], kpis[1][1], "≤ 45 min")
    return {"kpis": kpis, "tools": d.get("tools", [])}

def _kpi_tables(branche: str, size: str) -> Dict[str, str]:
    d = _branch_defaults(branche, size)
    overview = _table(["KPI", "Definition", "Ziel"], d["kpis"]) if d.get("kpis") else ""
    return {"KPI_HTML": overview or f"<p>{ensure_utf8(EM_DASH)}</p>",
            "KPI_BRANCHE_HTML": overview or f"<p>{ensure_utf8(EM_DASH)}</p>"}

def _roi_and_costs(briefing: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, str]:
    invest_hint = _parse_budget_range(briefing.get("investitionsbudget"))
    invest = invest_hint if invest_hint > 0 else 6000.0
    yearly = float(metrics.get("jahresersparnis_eur", 0) or 0)
    monthly = float(metrics.get("monatsersparnis_eur", 0) or 0)
    rate = float(metrics.get("stundensatz_eur", 60) or 60)
    roi_pct = ((yearly - invest) / invest * 100.0) if invest > 0 else 0.0
    payback_months = (invest / monthly) if monthly > 0 else 0.0
    roi_rows = [
        ("Stundensatz (Benchmark)", f"{int(rate)} €"),
        ("Investition", _to_eur(invest)),
        ("Ersparnis (jährlich)", _to_eur(yearly)),
        ("Return on Investment (ROI)", f"{roi_pct:.0f} %" if invest > 0 else EM_DASH),
        ("Payback‑Periode", f"{payback_months:.1f} Monate" if monthly > 0 else EM_DASH),
    ]
    costs_rows = [
        ("Initiale Investition (CapEx)", _to_eur(invest)),
        ("Lizenzen/Hosting (OpEx)", _to_eur(max(180.0, rate * 3.0))),
        ("Schulung/Change", _to_eur(600.0)),
        ("Betrieb (Schätzung)", _to_eur(360.0)),
    ]
    return {"ROI_HTML": _table(["Kennzahl", "Wert"], roi_rows),
            "COSTS_OVERVIEW_HTML": _table(["Position", "Betrag"], costs_rows),
            "invest_value": invest}

def _sensitivity_table(invest: float, monthly_base: float, rate: float) -> str:
    if invest <= 0 or monthly_base <= 0:
        return "<p>—</p>"
    rows = []
    for f in (1.0, 0.8, 0.6):
        mon = monthly_base * f
        yr = mon * 12.0
        roi = ((yr - invest) / invest * 100.0) if invest > 0 else 0.0
        pb = (invest / mon) if mon > 0 else 0.0
        rows.append((f"{int(f * 100)} %", f"{_to_eur(yr)} / {_to_eur(mon)}", f"{roi:.0f} %", f"{pb:.1f} Monate"))
    return _table(["Adoption", "Ersparnis Jahr / Monat", "ROI", "Payback"], rows)

def _so_what(scores: Dict[str, int]) -> str:
    g = scores.get("governance", 0); s = scores.get("security", 0)
    v = scores.get("value", 0); e = scores.get("enablement", 0)
    items: List[str] = []
    if g < 50:
        items.append("<li><strong>Governance:</strong> Rollen & Leitlinien klären (1–2 Seiten), Freigabepfade definieren.</li>")
    if s < 50:
        items.append("<li><strong>Sicherheit:</strong> Datenschutz-Checkliste + Logging, Prompt‑Richtlinien, Human‑Oversight.</li>")
    if v < 50:
        items.append("<li><strong>Nutzen:</strong> 3 Quick Wins priorisieren, KPI‑Baseline setzen, 30‑Tage‑Review.</li>")
    if e < 50:
        items.append("<li><strong>Befähigung:</strong> Prompt‑Training (3 Sessions), Brown‑Bags, Champions benennen.</li>")
    if not items:
        items.append("<li>Reifegrad solide – Fokus auf Skalierung: wiederverwendbare Bausteine & Automatisierungsgrad erhöhen.</li>")
    return "<ul>" + "".join(items) + "</ul>"

def _read_text_candidates(path: str) -> str:
    candidates = [path, os.path.join("content", os.path.basename(path)), os.path.join("/mnt/data", os.path.basename(path))]
    for p in candidates:
        if p and os.path.exists(p):
            try:
                return open(p, "r", encoding="utf-8").read()
            except Exception:
                continue
    return ""

def _md_to_simple_html(md: str) -> str:
    if not md: return ""
    out: List[str] = []; in_ul = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line:
            if in_ul: out.append("</ul>"); in_ul = False
            continue
        if line.startswith(("### ", "## ")):
            if in_ul: out.append("</ul>"); in_ul = False
            tag = "h3" if line.startswith("### ") else "h2"
            out.append(f"<{tag}>{ensure_utf8(line.lstrip('# ').strip())}</{tag}>")
            continue
        if line.startswith(("* ", "- ")):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{ensure_utf8(line[2:].strip())}</li>")
            continue
        if in_ul: out.append("</ul>"); in_ul = False
        out.append(f"<p>{ensure_utf8(line)}</p>")
    if in_ul: out.append("</ul>")
    return "\n".join(out)

def _build_kreativ_special_html() -> str:
    path = os.getenv("KREATIV_TOOLS_PATH", "kreativ-tools.txt")
    raw = _read_text_candidates(path)
    if not raw:
        return _p("Hinweis: Die Datei 'kreativ-tools.txt' wurde nicht gefunden. Bitte hinterlegen (ENV KREATIV_TOOLS_PATH) – dann erscheint hier die stets aktuelle Abschätzung & Tool‑Übersicht.")
    html = _md_to_simple_html(raw)
    return html or _p("—")

GLOSSARY = {
    "KI": "Technologien, die aus Daten lernen und selbstständig Entscheidungen treffen oder Empfehlungen geben.",
    "LLM": "Large Language Model; Sprachmodell, das Texteingaben verarbeitet und Antworten generiert.",
    "DSGVO": "Datenschutz-Grundverordnung der EU; regelt den Umgang mit personenbezogenen Daten.",
    "DSFA": "Datenschutz-Folgenabschätzung (DPIA); Analyse der Risiken für Betroffene bei bestimmten Datenverarbeitungen.",
    "EU AI Act": "EU-Verordnung mit Anforderungen, Risikoklassen und Pflichten für KI-Systeme.",
    "Quick Win": "Maßnahme mit geringem Aufwand und schnellem, messbarem Nutzen.",
    "MVP": "Minimum Viable Product; erste funktionsfähige Version mit minimalem Funktionsumfang.",
    "RAG": "Retrieval-Augmented Generation; Abruf externer Wissensquellen zur besseren Antwortqualität.",
    "Fine‑Tuning": "Nachtrainieren eines Modells auf spezifische Daten zur Leistungsverbesserung.",
    "Guardrails": "Sicherheitsmechanismen/Regeln zur Begrenzung unerwünschter KI-Ausgaben.",
    "Halluzination": "Falsche, aber plausibel klingende KI-Antwort ohne Faktenbasis.",
    "Embedding": "Vektor-Repräsentation von Texten/Bildern; Grundlage für semantische Suche.",
    "Vektor-Datenbank": "Datenbank für Embeddings zur Ähnlichkeitssuche (z. B. FAISS, Milvus).",
    "ROI": "Return on Investment; Verhältnis von Gewinn zu eingesetztem Kapital.",
    "Payback": "Zeit, bis sich eine Investition amortisiert.",
    "Zero‑Shot": "Modell löst eine Aufgabe ohne Beispiele; Gegenteil: Few‑Shot.",
    "Prompt": "Anweisung/Eingabetext an ein Sprachmodell, der die Ausgabe steuert."
}

def _build_glossar_html(snippets: Dict[str, Any]) -> str:
    pieces: List[str] = []
    for _, v in (snippets or {}).items():
        if isinstance(v, bytes):
            try:
                v = v.decode("utf-8", errors="ignore")
            except Exception:
                v = ""
        if not isinstance(v, str):
            v = "" if v is None else str(v)
        try:
            clean = re.sub(r"<[^>]+>", " ", v)
        except Exception:
            clean = str(v)
        pieces.append(clean)
    text = " ".join(pieces).lower()
    used: List[Tuple[str, str]] = []
    for term, definition in GLOSSARY.items():
        if term.lower() in text:
            used.append((term, definition))
    base_terms = ["KI", "DSGVO", "DSFA", "EU AI Act", "Quick Win", "MVP", "ROI", "Payback", "LLM", "Prompt"]
    for t in base_terms:
        if (t, GLOSSARY[t]) not in used:
            used.append((t, GLOSSARY[t]))
    items = "".join([f"<li><strong>{ensure_utf8(t)}:</strong> {ensure_utf8(d)}</li>" for t, d in used])
    return f"<div class='card'><ul>{items}</ul></div>"

def _build_leistung_nachweis_html(owner: str, email: str, site: str) -> str:
    bullets = [
        ("KI‑Strategie & Audit", "TÜV‑zertifizierte Entwicklung und Vorbereitung auf Prüfungen"),
        ("EU AI Act & DSGVO", "Beratung entlang aktueller Vorschriften und Standards"),
        ("Dokumentation & Governance", "Aufbau förderfähiger KI‑Prozesse und Nachweise"),
        ("Minimiertes Haftungsrisiko", "Vertrauen bei Kunden, Partnern und Behörden"),
    ]
    lis = "".join([f"<li><strong>{ensure_utf8(a)}:</strong> {ensure_utf8(b)}</li>" for a, b in bullets])
    email_link = f"<a href='mailto:{ensure_utf8(email)}'>{ensure_utf8(email)}</a>" if email else "—"
    site_label = site.replace("https://","").replace("http://","") if site else "—"
    site_link = f"<a href='{ensure_utf8(site)}'>{ensure_utf8(site_label)}</a>" if site else "—"
    return ("<div class='card'>"
            "<p>Als TÜV‑zertifizierter KI‑Manager begleite ich Unternehmen bei der sicheren Einführung, Nutzung und Audit‑Vorbereitung von KI – mit klarer Strategie, dokumentierter Förderfähigkeit und DSGVO‑Konformität.</p>"
            f"<ul>{lis}</ul>"
            f"<p>Kontakt: {email_link} · {site_link}</p>"
            "</div>")

def _obfuscate_url(url: str) -> str:
    base = os.getenv("FEEDBACK_REDIRECT_BASE", "").rstrip("/")
    secret = os.getenv("FEEDBACK_SECRET", "")
    if base and secret and url:
        import base64, hmac, hashlib
        b64 = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
        sig = hmac.new(secret.encode("utf-8"), b64.encode("ascii"), hashlib.sha256).hexdigest()[:16]
        return f"{base}/fb?u={b64}&s={sig}"
    return url

def _build_feedback_box(feedback_url: str) -> str:
    url = _obfuscate_url(feedback_url)
    return f"<a href='{ensure_utf8(url)}'>Feedback geben (2–3 Min.)</a>"

def _default_tools_and_funding(briefing: Dict[str, Any], last_updated: str, report_date: str) -> Dict[str, str]:
    b = (briefing.get("bundesland") or "").lower()
    branche = briefing.get("branche") or "beratung"
    d = _branch_defaults(branche, briefing.get("unternehmensgroesse") or "")
    tools_rows = d.get("tools", [])
    tools_html = _table(["Tool/Produkt", "Anbieter", "Preis‑Hinweis", "Einsatz"], tools_rows)
    funding_rows = []
    if b == "be":
        funding_rows.extend([
            ("KOMPASS (Solo‑Selbständige)", "ESF+/BA", "bis 29.02.2028", "Qualifizierung/Coaching bis 4.500 €"),
            ("INQA‑Coaching (KMU)", "BMAS/ESF+", "laufend", "80 % Zuschuss bis 12 Tage"),
            ("Transfer BONUS", "IBB", "laufend", "bis 45.000 € (70 %)"),
            ("Pro FIT", "IBB", "laufend", "Zuschuss + Darlehen für F&E"),
        ])
    else:
        funding_rows.extend([
            ("INQA‑Coaching (KMU)", "BMAS/ESF+", "laufend", "80 % Zuschuss bis 12 Tage"),
            ("Förderdatenbank (Bund/Land)", "BMWK", "—", "Filter: Digitalisierung/KI"),
        ])
    funding_html = _table(["Programm", "Träger", "Deadline/Datum", "Kurzbeschreibung"], funding_rows)
    if last_updated or report_date:
        funding_html += f'<p class="small">Stand: {ensure_utf8(report_date)} • Research: {ensure_utf8(last_updated or report_date)}</p>'
    return {"TOOLS_HTML": tools_html, "FOERDERPROGRAMME_HTML": funding_html}

def _build_zim_alert_html() -> str:
    enabled = os.getenv("ZIM_ALERT_ENABLED", "1").strip() not in {"0", "false", "False", ""}
    if not enabled:
        return ""
    date = os.getenv("ZIM_ALERT_DATE", "03.11.2025")
    img1 = os.getenv("ZIM_ALERT_IMG1", "https://www.aif-projekt-gmbh.de/fileadmin/_processed_/d/e/csm_AdobeStock_555433125_Gorodenkoff_834x556px_d1e69d4f3e.jpg")
    img2 = os.getenv("ZIM_ALERT_IMG2", "https://www.zim.de/ZIM/Redaktion/DE/Bilder/webinare.jpg?__blob=normal&size=420w&v=1")
    link1 = os.getenv("ZIM_ALERT_LINK_1", "https://www.zim.de/ZIM/Redaktion/DE/Meldungen/2025/4/2025-11-03-foerderzentrale.html")
    link2 = os.getenv("ZIM_ALERT_LINK_2", "https://www.zim.de/ZIM/Redaktion/DE/Dossiers/foerderzentrale/digitale-antragstellung-im-zim-fzd.html")
    link3 = os.getenv("ZIM_ALERT_LINK_3", "https://www.gtai.de/en/invest/industries/digital-economy/half-billion-euro-program-for-german-smes-goes-digital-1942648")
    return ("<div class='spotlight'>"
            "<div class='zim-grid'>"
            f"<div><img src='{ensure_utf8(img1)}' alt='ZIM – digitale Antragstellung (Symbolbild)'></div>"
            f"<div><img src='{ensure_utf8(img2)}' alt='ZIM – Webinare & Infos'></div>"
            "</div>"
            "<div class='cta'>"
            f"<p><strong>Neu seit {ensure_utf8(date)}:</strong> ZIM‑Anträge können <em>vollständig elektronisch</em> über das Online‑Portal der <strong>Förderzentrale Deutschland</strong> eingereicht und <em>kollaborativ</em> bearbeitet werden.</p>"
            "<ul>"
            "<li>Einheitliches Online‑Formularsystem mit Hilfen & automatischer Prüfung.</li>"
            "<li>Weniger Verwaltungsaufwand, schnellere Prozesse – ideal für KMU/Kooperationsprojekte.</li>"
            "<li>Passgenau für Ihr Beratungs‑ & Innovationsumfeld (KI, F&E, Prototyping).</li>"
            "</ul>"
            f"<p class='small'>Quellen: <a href='{ensure_utf8(link1)}'>zim.de (Meldung)</a> · <a href='{ensure_utf8(link2)}'>zim.de (Dossier)</a> · <a href='{ensure_utf8(link3)}'>GTAI</a></p>"
            "</div>"
            "</div>")

def normalize_and_enrich_sections(briefing: Dict[str, Any] = None,
                                  snippets: Dict[str, str] = None,
                                  metrics: Dict[str, Any] = None,
                                  **kwargs) -> Dict[str, str]:
    snippets = snippets or kwargs.get("sections") or {}
    briefing = briefing or kwargs.get("answers") or {}
    metrics = metrics or kwargs.get("metrics") or {}
    out = dict(snippets or {})

    kpi = _kpi_tables(briefing.get("branche") or "beratung", briefing.get("unternehmensgroesse") or "")
    out.setdefault("KPI_HTML", kpi["KPI_HTML"])
    out.setdefault("KPI_BRANCHE_HTML", kpi["KPI_BRANCHE_HTML"])

    scores = kwargs.get("scores") or {}
    out.setdefault("REIFEGRAD_SOWHAT_HTML", _so_what(scores))

    if not out.get("ROI_HTML") or len(out.get("ROI_HTML", "").strip()) < 20:
        out.update(_roi_and_costs(briefing, metrics))

    invest = float(out.get("invest_value", 0) or 0)
    monthly = float(metrics.get("monatsersparnis_eur", 0) or 0)
    rate = float(metrics.get("stundensatz_eur", 60) or 60)
    out.setdefault("BUSINESS_SENSITIVITY_HTML", _sensitivity_table(invest, monthly, rate))

    last_updated = snippets.get("last_updated") or kwargs.get("last_updated") or briefing.get("research_last_updated") or ""
    report_date = briefing.get("report_date", "")
    if not out.get("TOOLS_HTML") or len(out.get("TOOLS_HTML", "").strip()) < 24:
        out.update(_default_tools_and_funding(briefing, last_updated, report_date))
    if not out.get("FOERDERPROGRAMME_HTML") or len(out.get("FOERDERPROGRAMME_HTML", "").strip()) < 20:
        b = (briefing.get("bundesland") or "").lower()
        funding_rows = []
        if b == "be":
            funding_rows.extend([
                ("KOMPASS (Solo‑Selbständige)", "ESF+/BA", "bis 29.02.2028", "Qualifizierung/Coaching bis 4.500 €"),
                ("INQA‑Coaching (KMU)", "BMAS/ESF+", "laufend", "80 % Zuschuss bis 12 Tage"),
                ("Transfer BONUS", "IBB", "laufend", "bis 45.000 € (70 %)"),
                ("Pro FIT", "IBB", "laufend", "Zuschuss + Darlehen für F&E"),
            ])
        else:
            funding_rows.extend([
                ("INQA‑Coaching (KMU)", "BMAS/ESF+", "laufend", "80 % Zuschuss bis 12 Tage"),
                ("Förderdatenbank (Bund/Land)", "BMWK", "—", "Filter: Digitalisierung/KI"),
            ])
        funding_html = _table(["Programm", "Träger", "Deadline/Datum", "Kurzbeschreibung"], funding_rows)
        if last_updated or report_date:
            funding_html += f'<p class="small">Stand: {ensure_utf8(report_date)} • Research: {ensure_utf8(last_updated or report_date)}</p>'
        out["FOERDERPROGRAMME_HTML"] = funding_html

    if not out.get("QUELLEN_HTML") or len(out.get("QUELLEN_HTML", "").strip()) < 16:
        out["QUELLEN_HTML"] = _table(
            ["Titel", "Host", "Datum", "Link"],
            [
                ("EU‑KI‑Verordnung (AI Act) – Überblick", "europa.eu", "—", "https://europa.eu"),
                ("INQA‑Coaching", "inqa.de", "—", "https://inqa.de"),
            ],
        )

    owner = os.getenv("OWNER_NAME", "Wolf Hohl")
    email = os.getenv("CONTACT_EMAIL", "kontakt@ki-sicherheit.jetzt")
    site = os.getenv("SITE_URL", "https://ki-sicherheit.jetzt")
    feedback_url = os.getenv("FEEDBACK_URL", "https://make.ki-sicherheit.jetzt/feedback/feedback.html")

    out["OWNER_NAME"] = owner
    out["CONTACT_EMAIL"] = email
    out["SITE_URL"] = site

    out.setdefault("KREATIV_SPECIAL_HTML", _build_kreativ_special_html())
    out.setdefault("LEISTUNG_NACHWEIS_HTML", _build_leistung_nachweis_html(owner, email, site))
    out.setdefault("GLOSSAR_HTML", _build_glossar_html(out))

    out.setdefault("ZIM_ALERT_HTML", _build_zim_alert_html())
    out.setdefault("LEAD_ZIM_ALERT", "ZIM: Antrag jetzt volldigital — nutzen Sie den Vorsprung für schnellere Förderprozesse.")

    out.setdefault("FEEDBACK_BOX_HTML", _build_feedback_box(feedback_url))

    return out

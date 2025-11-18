# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List, Tuple
from .base import EvalResult, pct
from . import compliance as compliance_mod
from . import innovation as innovation_mod
from . import efficiency as efficiency_mod

BRANCH_WEIGHTS = {
    # branche → (compliance, innovation, efficiency)
    "finanzen": (0.55, 0.20, 0.25),
    "gesundheit": (0.55, 0.20, 0.25),
    "verwaltung": (0.55, 0.20, 0.25),
    "it_software": (0.35, 0.35, 0.30),
    "industrie": (0.40, 0.25, 0.35),
    "beratung": (0.35, 0.30, 0.35),  # default für Beratung & Dienstleistungen
}

def _weights_for_branche(branche: str) -> Tuple[float,float,float]:
    b = (branche or "").lower().strip()
    for key, w in BRANCH_WEIGHTS.items():
        if key in b:
            return w
    return (0.40, 0.25, 0.35)  # Default

def _prioritize_actions(results: List[EvalResult]) -> List[str]:
    bucket_H: List[str] = []
    bucket_M: List[str] = []
    bucket_L: List[str] = []
    for r in results:
        for act in r.actions:
            tag = act.strip().split(']')[0].replace('[','').upper() if '[' in act else 'M'
            if tag.startswith('H'):
                bucket_H.append(act)
            elif tag.startswith('L'):
                bucket_L.append(act)
            else:
                bucket_M.append(act)
    # dedup, Reihenfolge beibehalten
    def dedup(lst: List[str]) -> List[str]:
        seen: set[str] = set()
        out: List[str] = []
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out
    return dedup(bucket_H) + dedup(bucket_M) + dedup(bucket_L)

def run_ensemble(answers: Dict) -> Dict[str, str]:
    """Führt die drei Evaluatoren aus, gewichtet sie und erzeugt HTML-Blöcke."""
    comp = compliance_mod.evaluate(answers)
    inno = innovation_mod.evaluate(answers)
    effi = efficiency_mod.evaluate(answers)
    w_comp, w_inno, w_effi = _weights_for_branche(answers.get('branche',''))

    overall = round((comp.score*w_comp + inno.score*w_inno + effi.score*w_effi) * 100)

    # Conflicts (einfacher Heuristik-Detector)
    conflicts: List[str] = []
    if inno.score >= 0.7 and comp.score < 0.6:
        conflicts.append("Hohe Innovationsambition bei schwacher Compliance – priorisiere DPA/Retention.")
    if effi.score >= 0.7 and comp.score < 0.6:
        conflicts.append("Hohe Effizienzhebel, aber Compliance-Basis unsicher – TOMs/DPIA zuerst.")
    if comp.score >= 0.8 and effi.score < 0.5:
        conflicts.append("Gute Compliance, aber geringe Umsetzungskraft – Quick‑Wins & SOPs forcieren.")

    # HTML: Summary
    summary_html = f"""
    <table class="table">
      <thead><tr><th>Dimension</th><th>Score</th><th>Gewicht</th></tr></thead>
      <tbody>
        <tr><td>Compliance</td><td>{round(comp.score*100)}/100</td><td>{int(w_comp*100)}%</td></tr>
        <tr><td>Innovation</td><td>{round(inno.score*100)}/100</td><td>{int(w_inno*100)}%</td></tr>
        <tr><td>Effizienz</td><td>{round(effi.score*100)}/100</td><td>{int(w_effi*100)}%</td></tr>
        <tr><th>Gesamt (gewichtet)</th><th>{overall}/100</th><th>—</th></tr>
      </tbody>
    </table>
    """

    # HTML: Actions
    actions_all = _prioritize_actions([comp, inno, effi])
    if not actions_all:
        actions_all = ["[M] Zwei Quick‑Wins identifizieren und bis Tag 60 umsetzen."]
    li = "".join(f"<li>{x}</li>" for x in actions_all[:10])
    actions_html = f"<ul>{li}</ul>"

    # HTML: Conflicts
    conflicts_html = ""
    if conflicts:
        cl = "".join(f"<li>{c}</li>" for c in conflicts)
        conflicts_html = f"<ul>{cl}</ul>"

    return {
        "summary_html": summary_html.strip(),
        "actions_html": actions_html.strip(),
        "conflicts_html": conflicts_html.strip()
    }

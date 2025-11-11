# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List
from .base import EvalResult, clamp01

def evaluate(answers: Dict) -> EvalResult:
    a = answers or {}
    breakdown = {}

    # Digitalisierungsgrad/Papierlosigkeit
    dig = 0.0
    try:
        # falls Prozent als String (z. B. "81-100")
        dg = a.get('prozesse_papierlos', '0')
        if isinstance(dg, str) and '-' in dg:
            lo, hi = dg.split('-', 1)
            dig = (float(lo.split('%')[0]) + float(hi.split('%')[0]))/200.0
        else:
            dig = min(1.0, float(a.get('digitalisierungsgrad', 0)) / 10.0)
    except Exception:
        dig = 0.5
    breakdown['digital'] = dig * 0.25

    # Zeitbudget (Enablement für Effizienzmaßnahmen)
    zb = a.get('zeitbudget')
    z = 1.0 if zb == 'ueber_10' else (0.7 if zb == '5_10' else 0.4 if zb else 0.3)
    breakdown['zeitbudget'] = z * 0.25

    # Automatisierungspotenzial (Heuristik)
    ap = a.get('automatisierungsgrad','mittel')
    ap_map = {'sehr_hoch': 1.0, 'hoch': 0.8, 'mittel': 0.6, 'niedrig': 0.3}
    auto = ap_map.get(ap, 0.6)
    breakdown['auto_potential'] = auto * 0.30

    # Trainings/Skills
    skills = 1.0 if a.get('ki_kompetenz') in ['hoch','mittel'] else 0.5 if a.get('ki_kompetenz') else 0.3
    breakdown['skills'] = skills * 0.20

    score = clamp01(sum(breakdown.values()))

    findings: List[str] = []
    if dig >= 0.6: findings.append("Guter Digitalisierungsgrad")
    if z >= 0.7: findings.append("Zeitbudget vorhanden")
    if auto >= 0.6: findings.append("Hohe Automationshebel erkennbar")
    if skills >= 0.5: findings.append("KI‑Kompetenz ausreichend")

    risks: List[str] = []
    if z < 0.7: risks.append("Geringes Zeitbudget für Umsetzung")
    if dig < 0.6: risks.append("Digitalisierungsgrad begrenzt → Vorarbeiten nötig")

    actions: List[str] = [
        "[H] 2–3 Quick‑Wins mit klaren SOPs umsetzen (30–60 Tage)",
        "[M] KPI‑Dashboard (Einsparungen/Qualität) einführen (30 Tage)",
        "[M] Automations‑Backlog mit ROI‑Schätzung pflegen (laufend)",
    ]

    return EvalResult(
        name="efficiency", score=score, findings=findings, risks=risks, actions=actions, breakdown=breakdown
    )

# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List
from .base import EvalResult, clamp01

def evaluate(answers: Dict) -> EvalResult:
    a = answers or {}
    breakdown = {}

    # Vision/Strategie
    has_vision = 1.0 if a.get('vision_3_jahre') else 0.6 if a.get('roadmap_vorhanden') else 0.3
    breakdown['vision'] = has_vision * 0.35

    # Innovation culture (aus Innovationsprozess)
    ip = a.get('innovationsprozess', '')
    culture = 1.0 if ip in ['alle','mitarbeitende'] else (0.6 if ip else 0.3)
    breakdown['culture'] = culture * 0.25

    # Use‑Case‑Neuheit/Vielfalt
    ucs = a.get('anwendungsfaelle', []) or []
    novelty = 1.0 if len(ucs) >= 3 else (0.7 if len(ucs) == 2 else (0.5 if len(ucs) == 1 else 0.2))
    breakdown['use_case_novelty'] = novelty * 0.25

    # Experimentierfreude (Pilot/PoC)
    pilot = a.get('pilot_bereich')
    exp = 1.0 if pilot else (0.6 if a.get('ki_projekte') else 0.3)
    breakdown['experimentation'] = exp * 0.15

    score = clamp01(sum(breakdown.values()))

    findings: List[str] = []
    if has_vision >= 0.6: findings.append("Vision/Roadmap vorhanden")
    if culture >= 0.6: findings.append("Innovationskultur aktiv")
    if novelty >= 0.7: findings.append("Mehrere Use Cases in Pipeline")
    if exp >= 0.6: findings.append("Pilot/PoC‑Bereitschaft ersichtlich")

    risks: List[str] = []
    if has_vision < 0.6: risks.append("Vision/Roadmap unklar")
    if culture < 0.6: risks.append("Geringe Partizipation in Innovationsprozessen")
    if novelty < 0.7: risks.append("Zu wenig differenzierte Use Cases")
    if exp < 0.6: risks.append("Keine Testkultur/PoC‑Routine")

    actions: List[str] = [
        "[M] Quartalsweiser Use‑Case‑Pitch (Top‑3 auswählen) (30 Tage)",
        "[M] Pilot‑Prozess standardisieren (Hypothesen, Erfolgskriterien) (30–60 Tage)",
    ]
    if has_vision < 0.6:
        actions.append("[H] Zielbild/Portfolio in 1‑seitiger Strategy‑Map festhalten (30 Tage)")

    return EvalResult(
        name="innovation", score=score, findings=findings, risks=risks, actions=actions, breakdown=breakdown
    )

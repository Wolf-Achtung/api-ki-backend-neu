# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, List
from .base import EvalResult, clamp01

def evaluate(answers: Dict) -> EvalResult:
    a = answers or {}
    score = 0.0
    breakdown = {}

    # DSGVO Awareness / DPO
    gdpr = 1.0 if (a.get('datenschutz') is True or a.get('datenschutzbeauftragter') == 'ja') else 0.0
    breakdown['gdpr_awareness'] = gdpr * 0.25

    # Technische Maßnahmen
    tm = a.get('technische_massnahmen')
    tech = 1.0 if tm == 'alle' else (0.6 if tm else 0.0)
    breakdown['technical_measures'] = tech * 0.25

    # DPIA / Folgenabschätzung
    dpia = 1.0 if a.get('folgenabschaetzung') == 'ja' else 0.0
    breakdown['dpia'] = dpia * 0.2

    # Lösch-/Retention-Policy
    retention = 1.0 if a.get('loeschregeln') == 'ja' else 0.0
    breakdown['retention'] = retention * 0.15

    # Hosting/Transfers (Heuristik)
    infra = a.get('it_infrastruktur', '')
    eu_hosting = 1.0 if 'eu' in (a.get('hosting_region','eu') or 'eu') else (0.8 if infra=='hybrid' else 0.6)
    breakdown['hosting'] = eu_hosting * 0.15

    score = sum(breakdown.values())
    score = clamp01(score)

    findings: List[str] = []
    if gdpr == 1.0: findings.append("DSGVO‑Awareness/DPO vorhanden")
    if tech > 0.0: findings.append("Technische Maßnahmen implementiert")
    if dpia == 1.0: findings.append("Risikoprüfung (DPIA) durchgeführt")
    if retention == 1.0: findings.append("Lösch-/Retention‑Policy vorhanden")
    if eu_hosting >= 0.8: findings.append("EU‑Hosting/Hybrid mit Schwerpunkt EU")

    risks: List[str] = []
    if gdpr == 0.0: risks.append("Fehlende DSGVO‑Awareness/DPO")
    if tech == 0.0: risks.append("Keine dokumentierten TOMs")
    if dpia == 0.0: risks.append("Keine DPIA (ggf. erforderlich)")
    if retention == 0.0: risks.append("Kein Löschkonzept/Retention‑Policy")
    if eu_hosting < 0.8: risks.append("Unklarer Datenstandort/Transfers")

    actions: List[str] = []
    if gdpr == 0.0: actions.append("[H] Datenschutzverantwortliche/n benennen (30 Tage)")
    if tech < 1.0: actions.append("[M] TOMs konsolidieren (Verschlüsselung, Protokollierung, RBAC) (60 Tage)")
    if dpia == 0.0: actions.append("[M] DPIA‑Screening durchführen (30 Tage)")
    if retention == 0.0: actions.append("[H] Retention‑Policy & Löschkonzept festlegen (60 Tage)")
    if eu_hosting < 0.8: actions.append("[M] EU‑Hosting/DPA‑Nachweise für kritische Tools (60 Tage)")

    return EvalResult(
        name="compliance",
        score=score,
        findings=findings,
        risks=risks,
        actions=actions,
        breakdown=breakdown
    )

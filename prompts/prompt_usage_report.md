
# Prompt-Nutzung (Abgleich mit gpt_analyze.py)

**Wird genutzt (prompt_map):**
- executive_summary.md
- quick_wins.md
- pilot_plan.md (als Roadmap 90 Tage)
- roadmap_12m.md
- costs_overview.md (ROI + Kosten)
- business_case.md
- data_readiness.md
- org_change.md
- risks.md
- gamechanger.md
- recommendations.md
- next_actions.md

**Nicht automatisch genutzt (optional/archivierbar):**
- ai_act_summary.md (AI-Act wird derzeit aus Datei/ENV generiert)
- business.md (Legacy)
- compliance.md (Legacy/überlappt mit risks.md)
- funding.md / foerderprogramme.md (Research-Tabellen ersetzen diese Inhalte)
- next_steps_30_tage.md (ersetzt durch next_actions.md)

**Vorschlag:**
- Entweder ai_act_summary.md in prompt_map integrieren (Schlüssel: "ai_act_summary"), oder in Ordner `_archive/` verschieben.
- Legacy-Prompts (business.md, compliance.md, next_steps_30_tage.md) verschieben oder löschen, um Redundanz zu vermeiden.

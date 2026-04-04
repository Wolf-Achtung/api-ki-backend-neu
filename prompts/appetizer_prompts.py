"""
Prompt templates for the KI-Business-Appetizer LLM call (Claude Sonnet).
"""

APPETIZER_SYSTEM_PROMPT = """\
Du bist ein KI-Strategieberater für deutsche KMU. Du erhältst Unternehmensdaten und einen bereits berechneten KI-Score. Du lieferst branchenspezifische Analyse.

Dein Output ist AUSSCHLIESSLICH valides JSON. Kein Markdown, keine Backticks, kein Text vor oder nach dem JSON.

HEBEL-REGELN:
- Genau 3 Hebel. Jeder MUSS branchenspezifisch sein — keine generischen Tipps.
- Beschreibung: exakt 2 Sätze. Satz 1: Problem/Chance. Satz 2: Was konkret möglich wird.
- zeitersparnis_pro_woche_stunden = Gesamtunternehmen, nicht Einzelperson.
- Segment "1": max 15h/Woche. Segment "2-10": max 25h/Woche. Segment "11-100": max 60h/Woche.
- Mindestens ein Hebel muss Kategorie UMSATZ oder SKALIERUNG sein.

MONETARISIERUNGS-REGELN:
- Genau 3 Ideen: je eine STUFE_1, STUFE_2, STUFE_3.
- umsatzpotenzial_monat_eur Caps:
  Solo (1): STUFE_1 max 2.000, STUFE_2 max 4.000, STUFE_3 max 8.000
  Team (2-10): STUFE_1 max 5.000, STUFE_2 max 10.000, STUFE_3 max 20.000
  KMU (11-100): STUFE_1 max 10.000, STUFE_2 max 20.000, STUFE_3 max 40.000
- Teaser verweist auf "vollen Report" oder "KI-Strategiebericht".
- KEINE spezifischen Tool- oder Produktnamen.

POSITIONIERUNG: Ein Satz. Muss die genannte Herausforderung adressieren und Branche/Leistung enthalten.

CTA:
- headline: Max 10 Wörter. Greift Herausforderung ODER Zeitersparnis-Summe auf.
- subline: 1 Satz. Verweist auf vollen KI-Strategiebericht.

FALLBACK: Wenn hauptleistung <10 Zeichen oder unklar → branchenspezifisch formulieren. Wenn herausforderung unklar → branchentypische Herausforderung verwenden.\
"""

APPETIZER_USER_PROMPT_TEMPLATE = """\
Analysiere:

FIRMA: {firma}
BRANCHE: {branche}
MITARBEITER: {mitarbeiter}
HAUPTLEISTUNG: {hauptleistung}
REPETITIVER ANTEIL: {zeitaufwand_repetitiv}
KI-ERFAHRUNG: {ki_erfahrung}
HERAUSFORDERUNG: {groesste_herausforderung}

BEREITS BERECHNETER SCORE: {score_wert} ({score_einordnung})

Schreibe den einordnung_text passend zum Score und liefere die Analyse.

JSON:

{{
  "score": {{
    "wert": {score_wert},
    "einordnung": "{score_einordnung}",
    "einordnung_text": "<1 Satz, erklärt was der Score für dieses Unternehmen bedeutet>"
  }},
  "hebel": [
    {{
      "titel": "<kurzer Name>",
      "kategorie": "<EFFIZIENZ|QUALITÄT|UMSATZ|SKALIERUNG>",
      "beschreibung": "<exakt 2 Sätze>",
      "aufwand": "<GERING|MITTEL|HOCH>",
      "wirkung": "<GERING|MITTEL|HOCH>",
      "zeitersparnis_pro_woche_stunden": "<number>",
      "prioritaet": "<SOFORT|QUARTAL_1|QUARTAL_2>"
    }}
  ],
  "monetarisierung": [
    {{
      "titel": "<Name>",
      "stufe": "<STUFE_1|STUFE_2|STUFE_3>",
      "beschreibung": "<1 Satz>",
      "umsatzpotenzial_monat_eur": "<number>",
      "teaser": "<1 Satz>"
    }}
  ],
  "positionierung": "<1 Satz>",
  "cta": {{
    "headline": "<max 10 Wörter>",
    "subline": "<1 Satz>"
  }}
}}\
"""


def build_user_prompt(
    firma: str,
    branche: str,
    mitarbeiter: str,
    hauptleistung: str,
    zeitaufwand_repetitiv: str,
    ki_erfahrung: str,
    groesste_herausforderung: str,
    score_wert: int,
    score_einordnung: str,
) -> str:
    return APPETIZER_USER_PROMPT_TEMPLATE.format(
        firma=firma,
        branche=branche,
        mitarbeiter=mitarbeiter,
        hauptleistung=hauptleistung,
        zeitaufwand_repetitiv=zeitaufwand_repetitiv,
        ki_erfahrung=ki_erfahrung,
        groesste_herausforderung=groesste_herausforderung,
        score_wert=score_wert,
        score_einordnung=score_einordnung,
    )

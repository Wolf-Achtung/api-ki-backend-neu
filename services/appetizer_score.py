"""
Deterministic score calculation for KI-Business-Appetizer.
The LLM is NEVER used for score calculation.
"""


def calculate_appetizer_score(
    ki_erfahrung: str,
    zeitaufwand_repetitiv: str,
    branche: str,
    mitarbeiter: str,
) -> dict:
    """Calculate KI-Readiness score from lookup tables. Returns dict with wert and einordnung."""

    ki_punkte = {
        "keine": 8,
        "erste_versuche": 18,
        "regelmaessig": 30,
    }

    repetitiv_punkte = {
        "unter_25": 10,
        "25_50": 20,
        "ueber_50": 30,
    }

    branchen_punkte = {
        "marketing": 18, "medien": 18, "it": 18, "beratung": 18,
        "finanzen": 15, "handel": 15, "bildung": 15, "logistik": 15,
        "gesundheit": 12, "verwaltung": 12, "industrie": 12,
        "bau": 9, "gastronomie": 9,
    }

    groesse_punkte = {
        "1": 10,
        "2-10": 16,
        "11-100": 20,
    }

    score = (
        ki_punkte.get(ki_erfahrung, 8)
        + repetitiv_punkte.get(zeitaufwand_repetitiv, 10)
        + branchen_punkte.get(branche, 12)
        + groesse_punkte.get(mitarbeiter, 10)
    )

    if score <= 50:
        einordnung = "STARTER"
    elif score <= 65:
        einordnung = "EXPLORER"
    elif score <= 80:
        einordnung = "READY"
    else:
        einordnung = "ADVANCED"

    return {"wert": score, "einordnung": einordnung}

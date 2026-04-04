"""
FastAPI route for KI-Potenzial-Check (Appetizer).
Registered via _build_router_config in main.py.
"""

import json
import logging
from enum import Enum
from typing import Optional

import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text

from core.db import SessionLocal
from prompts.appetizer_prompts import APPETIZER_SYSTEM_PROMPT, build_user_prompt
from services.appetizer_score import calculate_appetizer_score, enforce_zeitersparnis_caps

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class BrancheEnum(str, Enum):
    marketing = "marketing"
    beratung = "beratung"
    it = "it"
    finanzen = "finanzen"
    handel = "handel"
    bildung = "bildung"
    verwaltung = "verwaltung"
    gesundheit = "gesundheit"
    bau = "bau"
    medien = "medien"
    industrie = "industrie"
    logistik = "logistik"
    gastronomie = "gastronomie"


class MitarbeiterEnum(str, Enum):
    solo = "1"
    team = "2-10"
    kmu = "11-100"


class ZeitaufwandEnum(str, Enum):
    unter_25 = "unter_25"
    halb = "25_50"
    ueber_50 = "ueber_50"


class KiErfahrungEnum(str, Enum):
    keine = "keine"
    erste_versuche = "erste_versuche"
    regelmaessig = "regelmaessig"


class AppetizerRequest(BaseModel):
    firma: str = Field(default="Unternehmen", max_length=100)
    branche: BrancheEnum
    mitarbeiter: MitarbeiterEnum
    hauptleistung: str = Field(..., max_length=200)
    zeitaufwand_repetitiv: ZeitaufwandEnum
    ki_erfahrung: KiErfahrungEnum
    groesste_herausforderung: str = Field(..., max_length=200)
    email: Optional[str] = None
    newsletter_optin: bool = False

    @field_validator("hauptleistung", "groesste_herausforderung")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Feld darf nicht leer sein")
        return v.strip()

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Ungültige E-Mail-Adresse")
        return v


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def call_claude_sonnet(system_prompt: str, user_prompt: str) -> str:
    """Call Claude Sonnet and return the raw text response."""
    client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    block = message.content[0]
    assert hasattr(block, "text"), f"Unexpected content block type: {block.type}"
    result: str = block.text
    return result


def parse_and_validate_json(raw: str) -> dict:
    """Parse LLM output as JSON, stripping markdown fences if present."""
    text_content = raw.strip()
    if text_content.startswith("```"):
        text_content = text_content.split("\n", 1)[1] if "\n" in text_content else text_content[3:]
        if text_content.endswith("```"):
            text_content = text_content[:-3]
        text_content = text_content.strip()

    parsed: dict = json.loads(text_content)

    # Basic structural validation
    assert "score" in parsed, "Missing score"
    assert "hebel" in parsed and len(parsed["hebel"]) == 3, "Need exactly 3 hebel"
    assert "monetarisierung" in parsed and len(parsed["monetarisierung"]) == 3, "Need exactly 3 monetarisierung"
    assert "positionierung" in parsed, "Missing positionierung"
    assert "cta" in parsed, "Missing cta"

    return parsed


# ---------------------------------------------------------------------------
# Database helpers (sync SQLAlchemy, matching core.db pattern)
# ---------------------------------------------------------------------------

def save_appetizer_lead(request: AppetizerRequest, result: dict, score: dict):
    """Save lead with email to appetizer_leads table."""
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO appetizer_leads
                    (firma, branche, mitarbeiter, hauptleistung, zeitaufwand_repetitiv,
                     ki_erfahrung, groesste_herausforderung, email, newsletter_optin,
                     score_wert, score_einordnung, result_json)
                VALUES
                    (:firma, :branche, :mitarbeiter, :hauptleistung, :zeitaufwand_repetitiv,
                     :ki_erfahrung, :groesste_herausforderung, :email, :newsletter_optin,
                     :score_wert, :score_einordnung, :result_json)
            """),
            {
                "firma": request.firma,
                "branche": request.branche.value,
                "mitarbeiter": request.mitarbeiter.value,
                "hauptleistung": request.hauptleistung,
                "zeitaufwand_repetitiv": request.zeitaufwand_repetitiv.value,
                "ki_erfahrung": request.ki_erfahrung.value,
                "groesste_herausforderung": request.groesste_herausforderung,
                "email": request.email,
                "newsletter_optin": request.newsletter_optin,
                "score_wert": score["wert"],
                "score_einordnung": score["einordnung"],
                "result_json": json.dumps(result, ensure_ascii=False),
            },
        )
        db.commit()
        logger.info("Appetizer lead saved: branche=%s, score=%s, email=%s",
                     request.branche.value, score["wert"], request.email)
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save appetizer lead: %s", exc)
    finally:
        db.close()


def save_appetizer_analytics(branche: str, mitarbeiter: str, score: dict):
    """Save anonymous analytics to appetizer_analytics table."""
    db = SessionLocal()
    try:
        db.execute(
            text("""
                INSERT INTO appetizer_analytics (branche, mitarbeiter, score_wert, score_einordnung)
                VALUES (:branche, :mitarbeiter, :score_wert, :score_einordnung)
            """),
            {
                "branche": branche,
                "mitarbeiter": mitarbeiter,
                "score_wert": score["wert"],
                "score_einordnung": score["einordnung"],
            },
        )
        db.commit()
        logger.info("Appetizer analytics saved: branche=%s, mitarbeiter=%s, score=%s",
                     branche, mitarbeiter, score["wert"])
    except Exception as exc:
        db.rollback()
        logger.error("Failed to save appetizer analytics: %s", exc)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Endpoint (sync — FastAPI runs it in threadpool automatically)
# ---------------------------------------------------------------------------

@router.post("/generate")
def generate_appetizer(request: AppetizerRequest):
    # 1. Score berechnen (deterministic, no LLM)
    score = calculate_appetizer_score(
        ki_erfahrung=request.ki_erfahrung.value,
        zeitaufwand_repetitiv=request.zeitaufwand_repetitiv.value,
        branche=request.branche.value,
        mitarbeiter=request.mitarbeiter.value,
    )

    # 2. Build prompt and call LLM for content
    user_prompt = build_user_prompt(
        firma=request.firma,
        branche=request.branche.value,
        mitarbeiter=request.mitarbeiter.value,
        hauptleistung=request.hauptleistung,
        zeitaufwand_repetitiv=request.zeitaufwand_repetitiv.value,
        ki_erfahrung=request.ki_erfahrung.value,
        groesste_herausforderung=request.groesste_herausforderung,
        score_wert=score["wert"],
        score_einordnung=score["einordnung"],
    )

    try:
        raw_response = call_claude_sonnet(APPETIZER_SYSTEM_PROMPT, user_prompt)
        result = parse_and_validate_json(raw_response)
    except json.JSONDecodeError as e:
        logger.error("LLM returned invalid JSON: %s", e)
        raise HTTPException(status_code=500, detail="Analyse konnte nicht erstellt werden. Bitte versuchen Sie es erneut.")
    except (AssertionError, KeyError) as e:
        logger.error("LLM response validation failed: %s", e)
        raise HTTPException(status_code=500, detail="Analyse konnte nicht erstellt werden. Bitte versuchen Sie es erneut.")
    except anthropic.APIError as e:
        logger.error("Anthropic API error: %s", e)
        raise HTTPException(status_code=500, detail="Analyse konnte nicht erstellt werden. Bitte versuchen Sie es erneut.")

    # 3. Enforce backend-calculated score (override LLM values)
    result["score"]["wert"] = score["wert"]
    result["score"]["einordnung"] = score["einordnung"]

    # 4. Enforce Zeitersparnis-Caps (LLMs rechnen nie)
    result["hebel"] = enforce_zeitersparnis_caps(
        result["hebel"], request.mitarbeiter.value
    )

    # 5. Save lead if email provided
    if request.email:
        save_appetizer_lead(request, result, score)

    # 6. Always save anonymous analytics
    save_appetizer_analytics(request.branche.value, request.mitarbeiter.value, score)

    return {"status": "success", "result": result}

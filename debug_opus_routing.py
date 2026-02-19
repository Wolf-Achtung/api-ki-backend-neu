# ============================================================
# DEBUG ENDPOINT — Opus-Routing Verifikation
# ============================================================
# 
# Einfügen in deine FastAPI-App (z.B. main.py oder routes.py)
# Nach dem Test wieder ENTFERNEN!
#
# Aufruf: GET /debug/opus-routing
# ============================================================

import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/debug/opus-routing")
async def debug_opus_routing():
    """
    Temporärer Debug-Endpoint zur Verifikation des FIX-OPUS-ROUTING Deploys.
    Zeigt für alle relevanten Sections das aufgelöste Modell.
    NACH VALIDIERUNG ENTFERNEN!
    """
    
    # --- ENV-Werte auslesen ---
    env_info = {
        "OPUS_SECTIONS": os.environ.get("OPUS_SECTIONS", "NOT SET"),
        "ANTHROPIC_MODEL": os.environ.get("ANTHROPIC_MODEL", "NOT SET"),
        "ANTHROPIC_MODEL_OPUS": os.environ.get("ANTHROPIC_MODEL_OPUS", "NOT SET"),
        "LLM_PROVIDER_DEFAULT": os.environ.get("LLM_PROVIDER_DEFAULT", "NOT SET"),
    }
    
    # --- Opus-Sections aus ENV parsen ---
    opus_sections_raw = os.environ.get("OPUS_SECTIONS", "")
    opus_sections_list = [s.strip() for s in opus_sections_raw.split(",") if s.strip()]
    
    # --- Routing für jede Section testen ---
    results = {}
    
    # Versuch 1: Import der tatsächlichen Resolve-Funktion
    try:
        from services.anthropic_client import _resolve_anthropic_model
        
        test_sections = [
            # Premium (sollen Opus bekommen)
            "executive_summary",
            "gamechanger",
            "gamechanger_expand",
            "business_case",
            "strategie_governance",
            "strategie_governance_expand",
            "recommendations",
            "recommendations_expand",
            "risks",
            "risks_expand",
            "foerderpotenzial",
            "foerderpotenzial_expand",
            # Non-Premium (sollen Sonnet bekommen)
            "one_liner",
            "next_actions",
            "branch_deep_dive",
            "ki_skillplan",
        ]
        
        for section in test_sections:
            try:
                model = _resolve_anthropic_model(section)
                is_opus = section in opus_sections_list
                expected = os.environ.get("ANTHROPIC_MODEL_OPUS", "claude-opus-4-6") if is_opus else os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
                results[section] = {
                    "model": model,
                    "expected": expected,
                    "in_opus_list": is_opus,
                    "status": "✅ PASS" if model == expected else "❌ FAIL",
                }
            except Exception as e:
                results[section] = {"error": str(e)}
                
    except ImportError:
        # Versuch 2: Falls die Funktion anders heißt oder nicht importierbar
        try:
            from services.anthropic_client import _get_model_for_section
            for section in ["executive_summary", "gamechanger", "one_liner"]:
                try:
                    model = _get_model_for_section(section)
                    results[section] = {"model": model, "via": "_get_model_for_section"}
                except Exception as e:
                    results[section] = {"error": str(e)}
        except ImportError:
            results["_import_error"] = "Konnte weder _resolve_anthropic_model noch _get_model_for_section importieren"
    
    # --- Zusammenfassung ---
    opus_pass = sum(1 for v in results.values() if isinstance(v, dict) and v.get("status") == "✅ PASS" and v.get("in_opus_list"))
    opus_total = sum(1 for v in results.values() if isinstance(v, dict) and v.get("in_opus_list"))
    
    return {
        "fix": "FIX-OPUS-ROUTING",
        "briefing": "Post-Deploy Verification",
        "env": env_info,
        "opus_sections_parsed": opus_sections_list,
        "routing_results": results,
        "summary": {
            "opus_sections_correct": f"{opus_pass}/{opus_total}",
            "verdict": "✅ FIX VERIFIED" if opus_pass == opus_total and opus_total > 0 else "❌ FIX NOT WORKING",
        }
    }


# ============================================================
# EINBAU-ANLEITUNG:
# ============================================================
#
# Option A: Direkt in main.py (falls dort der FastAPI-App liegt)
#
#   from debug_opus_routing import router as debug_router
#   app.include_router(debug_router, tags=["debug"])
#
# Option B: Inline in main.py einfügen
#
#   Einfach den @app.get("/debug/opus-routing") Block
#   direkt in deine main.py kopieren (router → app ersetzen)
#
# Option C: Falls du eine routes/ Struktur hast
#
#   Diese Datei nach routes/debug_opus_routing.py kopieren
#   und in deinem Router-Setup einbinden.
#
# NACH DEM TEST:
#   git revert / Datei löschen / Endpoint entfernen
#   Kein Debug-Endpoint in Production lassen!
# ============================================================

# ============================================================================
# CODE-ÄNDERUNGEN FÜR gpt_analyze.py
# Context-System Integration - Version 2.1.0-Backend-Optimized
# ============================================================================

# ---------------------------------------------------------------------------
# ÄNDERUNG 1: Import hinzufügen (nach Zeile 13)
# ---------------------------------------------------------------------------
# VORHER (Zeile 13):
from services.prompt_loader import load_prompt

# NACHHER (füge nach Zeile 13 hinzu):
from services.prompt_loader import load_prompt
from services.prompt_enhancer import PromptEnhancer  # NEU!

# ---------------------------------------------------------------------------
# ÄNDERUNG 2: PromptEnhancer initialisieren (nach Zeile 158)
# ---------------------------------------------------------------------------
# VORHER (Zeile 158):
USE_PROMPT_SYSTEM = (os.getenv("USE_PROMPT_SYSTEM", "1") in ("1", "true", "TRUE", "yes", "YES"))

# NACHHER (füge nach Zeile 158 hinzu):
USE_PROMPT_SYSTEM = (os.getenv("USE_PROMPT_SYSTEM", "1") in ("1", "true", "TRUE", "yes", "YES"))

# Initialize PromptEnhancer (einmal beim App-Start) - NEU!
if USE_PROMPT_SYSTEM:
    try:
        _prompt_enhancer = PromptEnhancer(data_dir="data")
        log.info("✅ PromptEnhancer initialized with context system")
    except Exception as e:
        log.warning("⚠️ PromptEnhancer failed to initialize: %s", e)
        _prompt_enhancer = None
else:
    _prompt_enhancer = None
    log.info("ℹ️ PromptEnhancer disabled (USE_PROMPT_SYSTEM=0)")

# ---------------------------------------------------------------------------
# ÄNDERUNG 3: _generate_content_section() anpassen (Zeile 668-690)
# ---------------------------------------------------------------------------
# VORHER (Zeile 668-690):
def _generate_content_section(section_name: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    """🎯 UPDATED: Now uses prompt_loader system with variable interpolation!"""
    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} – LLM disabled]</em></p>"
    
    # Map section names to prompt files (without _de suffix for load_prompt)
    prompt_map = {
        # Core sections
        "executive_summary": "executive_summary",
        "quick_wins": "quick_wins",
        "roadmap": "pilot_plan",  # 90-day roadmap
        # ... etc ...
    }
    
    prompt_key = prompt_map.get(section_name)
    
    # Try to use prompt system if enabled and prompt exists
    if USE_PROMPT_SYSTEM and prompt_key:
        try:
            # Build variables for interpolation
            vars_dict = _build_prompt_vars(briefing, scores)
            
            # Load prompt with variable interpolation
            prompt_text = load_prompt(prompt_key, lang="de", vars_dict=vars_dict)
            
            # ... rest of the code ...

# NACHHER (ersetze Zeile 670-677):
def _generate_content_section(section_name: str, briefing: Dict[str, Any], scores: Dict[str, Any]) -> str:
    """🎯 UPDATED: Now uses PromptEnhancer with context system!"""
    if not ENABLE_LLM_CONTENT:
        return f"<p><em>[{section_name} – LLM disabled]</em></p>"
    
    # Map section names to prompt files
    prompt_map = {
        # Core sections
        "executive_summary": "executive_summary",
        "quick_wins": "quick_wins",
        "roadmap": "pilot_plan",  # 90-day roadmap
        "roadmap_12m": "roadmap_12m",
        "business_roi": "costs_overview",
        "business_costs": "costs_overview",
        "business_case": "business_case",
        "data_readiness": "data_readiness",
        "org_change": "org_change",
        "risks": "risks",
        "gamechanger": "gamechanger",
        "recommendations": "recommendations",
        "reifegrad_sowhat": "executive_summary",  # fallback to exec summary prompt
        # Previously unused prompts - now activated
        "ai_act_summary": "ai_act_summary",
        "strategie_governance": "strategie_governance",
        "wettbewerb_benchmark": "wettbewerb_benchmark",
        "technologie_prozesse": "technologie_prozesse",
        "unternehmensprofil_markt": "unternehmensprofil_markt",
        "tools_empfehlungen": "tools_empfehlungen",
        "foerderpotenzial": "foerderpotenzial",
        "transparency_box": "transparency_box",
        "ki_aktivitaeten_ziele": "ki_aktivitaeten_ziele",
    }
    
    prompt_key = prompt_map.get(section_name)
    
    # 🎯 NEW: Try to use PromptEnhancer with context system
    if USE_PROMPT_SYSTEM and prompt_key and _prompt_enhancer:
        try:
            # 1. Enhance prompt with context (branch + size specific info)
            enhanced_prompt = _prompt_enhancer.enhance_prompt(prompt_key, briefing)
            
            # 2. Build variables for final interpolation
            vars_dict = _build_prompt_vars(briefing, scores)
            
            # 3. Interpolate variables into enhanced prompt
            from services.prompt_loader import _interpolate
            prompt_text = _interpolate(enhanced_prompt, vars_dict)
            
            if not isinstance(prompt_text, str):
                log.warning("⚠️ Enhanced prompt %s returned non-string: %s, falling back", 
                           prompt_key, type(prompt_text))
                raise ValueError("Non-string prompt")
            
            log.debug("✅ Using enhanced prompt for %s (with context)", section_name)
            
            # 4. Call GPT with enhanced prompt
            _temp = float(os.getenv("GAMECHANGER_TEMPERATURE", "0.4")) if section_name == "gamechanger" else 0.2
            result = _call_openai(
                prompt=prompt_text,
                system_prompt="Du bist ein Senior‑KI‑Berater. Antworte nur mit validem HTML.",
                temperature=_temp,
                max_tokens=OPENAI_MAX_TOKENS
            ) or ""
            
            result = _clean_html(result)
            if _needs_repair(result):
                result = _repair_html(section_name, result)
            
            # Check if result is substantial enough
            if not result or len(result.strip()) < 50:
                log.warning("⚠️ GPT returned too little for %s (%d chars), using fallback", 
                           section_name, len(result))
                return _get_fallback_content(section_name, briefing, scores)
            
            return result
            
        except FileNotFoundError as e:
            log.warning("⚠️ Prompt file not found for %s: %s - using legacy", prompt_key, e)
        except Exception as e:
            log.error("❌ Error with enhanced prompt for %s: %s - using legacy", section_name, e)
    
    # Fallback to legacy system if enhancer not available
    log.debug("ℹ️ Using legacy prompt system for %s", section_name)
    # ... rest bleibt unverändert ...

# ---------------------------------------------------------------------------
# ZUSAMMENFASSUNG DER ÄNDERUNGEN
# ---------------------------------------------------------------------------

"""
ÄNDERUNGEN IN 3 SCHRITTEN:

1. Import hinzufügen (1 Zeile):
   from services.prompt_enhancer import PromptEnhancer

2. Initialisierung nach USE_PROMPT_SYSTEM (8 Zeilen):
   if USE_PROMPT_SYSTEM:
       try:
           _prompt_enhancer = PromptEnhancer(data_dir="data")
           log.info("✅ PromptEnhancer initialized")
       except Exception as e:
           log.warning("⚠️ PromptEnhancer failed: %s", e)
           _prompt_enhancer = None
   else:
       _prompt_enhancer = None

3. _generate_content_section() erweitern (Zeile 670-677 ersetzen):
   - Prüfung: if USE_PROMPT_SYSTEM and prompt_key and _prompt_enhancer:
   - Aufruf: enhanced_prompt = _prompt_enhancer.enhance_prompt(prompt_key, briefing)
   - Interpolation: prompt_text = _interpolate(enhanced_prompt, vars_dict)
   - Rest bleibt gleich

GESAMT: ~15 neue/geänderte Zeilen in gpt_analyze.py
"""

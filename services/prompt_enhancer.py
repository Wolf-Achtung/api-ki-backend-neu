# -*- coding: utf-8 -*-
"""
Prompt Enhancer - Injects context into existing prompts
Optimized for Wolf's ki-sicherheit.jetzt backend

This service works WITH Wolf's existing prompt_loader.py system.
It loads prompts via prompt_loader, injects context, and returns enhanced prompts.

Author: Wolf Hohl / Claude
Version: 2.2.0-Context-Whitelist-Fix
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from services.prompt_builder import PromptBuilder

log = logging.getLogger(__name__)


# Roadmap constraints by company size - Fix #5
ROADMAP_CONSTRAINTS = {
    "solo": {
        "max_budget_total": 10000,
        "max_budget_per_phase": 3000,
        "team_structure": "Sie + maximal 1-2 Freelancer",
        "phase_duration_weeks": 4,
        "example_team": "1 Backend-Dev (Freelance, 20h)",
        "realistic_capacity": "Sie arbeiten hauptsächlich selbst, Freelancer für Spezialaufgaben"
    },
    "klein": {
        "max_budget_total": 50000,
        "max_budget_per_phase": 15000,
        "team_structure": "Kernteam + externe Experten",
        "phase_duration_weeks": 4,
        "example_team": "2-3 Entwickler + 1 Projektleiter",
        "realistic_capacity": "Kleines internes Team + punktuelle Verstärkung"
    },
    "mittel": {
        "max_budget_total": 200000,
        "max_budget_per_phase": 60000,
        "team_structure": "Dediziertes Projektteam",
        "phase_duration_weeks": 6,
        "example_team": "5-8 Entwickler + PM + Architect",
        "realistic_capacity": "Vollständiges Projektteam mit verschiedenen Rollen"
    }
}


def enhance_roadmap_prompt(base_prompt: str, context: Dict[str, Any]) -> str:
    """
    Inject size-specific constraints into roadmap prompt.

    Args:
        base_prompt: Original prompt text
        context: Briefing data with unternehmensgroesse, investitionsbudget

    Returns:
        Enhanced prompt with size constraints
    """
    size = context.get("unternehmensgroesse", "klein").lower()
    constraints = ROADMAP_CONSTRAINTS.get(size, ROADMAP_CONSTRAINTS["klein"])

    # Get investment budget from briefing
    investment_budget = context.get("investitionsbudget", "2000_10000")
    investment_map = {
        "unter_2000": 2000,
        "2000_10000": 10000,
        "10000_50000": 50000,
        "50000_250000": 250000,
        "ueber_250000": 500000
    }
    budget_from_map = investment_map.get(investment_budget, 10000)
    max_realistic_budget = min(
        constraints["max_budget_total"],
        budget_from_map
    )

    size_context = f"""
KRITISCHE VORGABEN - Unternehmensgröße: {size.upper()}

Budget-Grenzen (STRIKT EINHALTEN!):
- Gesamt-Budget für 90 Tage: MAX €{max_realistic_budget:,}
- Budget pro Phase: MAX €{constraints['max_budget_per_phase']:,}
- Angegebenes Investment-Budget: {investment_budget}

Team-Struktur (REALISTISCH!):
- {constraints['team_structure']}
- Beispiel: {constraints['example_team']}
- Kapazität: {constraints['realistic_capacity']}

VERBOTEN für {size}:
- KEINE "5 Entwickler + Projektleiter" bei Solo/Klein
- KEINE Budgets > €{max_realistic_budget:,}
- KEINE unrealistischen Teamgrößen

Die Roadmap MUSS mit dem realen Budget und der Unternehmensgröße umsetzbar sein!

---

"""

    return size_context + base_prompt


class PromptEnhancer:
    """
    Enhances existing prompts with contextual information.
    Works with Wolf's existing prompt_loader.py system.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize PromptEnhancer.
        
        Args:
            data_dir: Path to context data directory
        """
        self.builder = PromptBuilder(data_dir=data_dir)
        log.info("✅ PromptEnhancer initialized (data_dir=%s)", data_dir)
    
    def build_context_block(self, briefing_data: Dict[str, Any]) -> str:
        """
        Build HTML-formatted context block for injection into prompts.
        
        Args:
            briefing_data: Complete briefing data with branche, unternehmensgroesse, etc.
            
        Returns:
            HTML string with context information
        """
        branche = briefing_data.get('branche', '')
        groesse = briefing_data.get('unternehmensgroesse', '')
        
        if not branche or not groesse:
            return "<!-- Context data incomplete -->"
        
        # Load contexts
        branch_ctx = self.builder.load_context('branch', branche)
        size_ctx = self.builder.load_context('size', groesse)
        
        log.info("✅ Context loaded: branch=%s, size=%s", branche, groesse)
        
        # Build compact HTML context block
        context_html = self._build_html_block(branch_ctx, size_ctx)
        
        return context_html
    
    def _build_html_block(self, branch_ctx: Dict[str, Any], size_ctx: Dict[str, Any]) -> str:
        """Build compact HTML context block"""
        
        # Helper to format list items
        def format_items(items: list, max_items: int = 4) -> str:
            if not items:
                return "<li>(Keine Angaben)</li>"
            return "\n    ".join([f"<li>{item}</li>" for item in items[:max_items]])
        
        # Branch section
        branch_html = f"""
<div class="context-block" style="background:#f3f4f6;padding:12px;border-left:3px solid #2563eb;margin:16px 0;font-size:11px;">
  <h4 style="margin:0 0 8px 0;font-size:12px;color:#1e40af;">📋 Branchen-Context: {branch_ctx.get('display_name', 'Unbekannt')}</h4>
  
  <p style="margin:6px 0;"><strong>Typische Workflows:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('typical_workflows', []))}
  </ul>
  
  <p style="margin:6px 0;"><strong>Häufigste Pain Points:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('common_pain_points', []))}
  </ul>
  
  <p style="margin:6px 0;"><strong>Typische Tools im Einsatz:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(branch_ctx.get('typical_tools', []))}
  </ul>"""
        
        # Size section
        chars = size_ctx.get('characteristics', {})
        budget = size_ctx.get('budget_realistic', {})
        
        size_html = f"""
  <hr style="margin:12px 0;border:none;border-top:1px solid #cbd5e1;">
  
  <h4 style="margin:8px 0 8px 0;font-size:12px;color:#1e40af;">🏢 Größen-Context: {size_ctx.get('display_name', 'Unbekannt')}</h4>
  
  <p style="margin:6px 0;"><strong>Charakteristika:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    <li>Mitarbeiter: {chars.get('mitarbeiter', 'unbekannt')}</li>
    <li>Budget CAPEX max: {budget.get('capex_max', 0):,}€</li>
    <li>Budget OPEX max: {budget.get('opex_monthly_max', 0)}€/Monat</li>
  </ul>
  
  <p style="margin:6px 0;"><strong>Fokus-Prioritäten:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;">
    {format_items(size_ctx.get('focus_priorities', []), max_items=3)}
  </ul>
  
  <p style="margin:6px 0;"><strong>❌ VERBOTEN für diese Größe:</strong></p>
  <ul style="margin:4px 0;padding-left:20px;color:#dc2626;">
    {format_items(size_ctx.get('forbidden_recommendations', []), max_items=5)}
  </ul>
</div>"""
        
        return branch_html + size_html
    
    def enhance_prompt(self, prompt_name: str, briefing_data: Dict[str, Any]) -> str:
        """
        Load a prompt and inject context.
        
        This method:
        1. Loads the base prompt from /prompts/de/ via prompt_loader
        2. Builds a context block from branch/size contexts
        3. Injects the context block into the prompt (ONLY for whitelisted prompts!)
        4. Returns the enhanced prompt
        
        Args:
            prompt_name: Name of the prompt (e.g., 'quick_wins')
            briefing_data: Complete briefing data
            
        Returns:
            Enhanced prompt with injected context (or plain prompt if not whitelisted)
        """
        # === WHITELIST: Only these prompts get context block ===
        # Context should only appear on Unternehmensprofil page, not everywhere!
        # This fixes the "10× context duplication" bug reported by Wolf
        PROMPTS_WITH_CONTEXT = {
            'unternehmensprofil_markt',  # Main profile page - needs context
            # Add more here if needed, but keep it minimal!
            # Most prompts DON'T need context - they have specific instructions
        }
        
        try:
            # Import prompt_loader dynamically to avoid circular imports
            from services.prompt_loader import load_prompt
            
            # Load base prompt (without variable interpolation yet)
            # We'll do variable interpolation in gpt_analyze.py as before
            base_prompt = load_prompt(prompt_name, lang="de", vars_dict=None)
            
            if not isinstance(base_prompt, str):
                log.warning("⚠️ Prompt '%s' returned non-string type: %s", prompt_name, type(base_prompt))
                return str(base_prompt)
            
            # === FIX: Check if this prompt should get context ===
            if prompt_name not in PROMPTS_WITH_CONTEXT:
                log.debug("⏭️  Skipping context for '%s' (not in whitelist)", prompt_name)

                # === Fix #5: Apply roadmap constraints for roadmap prompts ===
                ROADMAP_PROMPTS = {"roadmap", "roadmap_12m", "pilot_plan", "roadmap_90d"}
                if prompt_name in ROADMAP_PROMPTS:
                    log.info("🎯 Applying roadmap size constraints for '%s'", prompt_name)
                    base_prompt = enhance_roadmap_prompt(base_prompt, briefing_data)

                return base_prompt  # Return WITHOUT context (but with roadmap constraints if applicable)!
            
            # Build context block (only for whitelisted prompts)
            context_block = self.build_context_block(briefing_data)
            
            # Inject context block
            # Look for {CONTEXT_BLOCK} placeholder in the prompt
            if '{CONTEXT_BLOCK}' in base_prompt:
                enhanced = base_prompt.replace('{CONTEXT_BLOCK}', context_block)
                log.info("✅ Injected context block into prompt '%s'", prompt_name)
            else:
                # If no placeholder, prepend context at the beginning (after any HTML comments)
                # Find the first <section> or <div> tag
                import re
                match = re.search(r'(<(?:section|div)[^>]*>)', base_prompt, re.IGNORECASE)
                if match is not None:  # 🔧 FIXED: Changed from "if match:" to help mypy type narrowing
                    # Insert context right after opening tag
                    pos = match.end()
                    enhanced = base_prompt[:pos] + "\n" + context_block + "\n" + base_prompt[pos:]
                    log.debug("✅ Prepended context block to prompt '%s'", prompt_name)
                else:
                    # Fallback: just prepend
                    enhanced = context_block + "\n\n" + base_prompt
                    log.debug("⚠️ No suitable injection point found, prepended context to '%s'", prompt_name)
            
            return enhanced
            
        except FileNotFoundError as e:
            log.error("❌ Prompt file not found for '%s': %s", prompt_name, e)
            raise
        except Exception as e:
            log.error("❌ Failed to enhance prompt '%s': %s", prompt_name, e)
            raise
    
    def get_context_summary(self, briefing_data: Dict[str, Any]) -> str:
        """
        Get a plain text summary of the context (for debugging).
        
        Args:
            briefing_data: Briefing data
            
        Returns:
            Plain text summary
        """
        return self.builder.build_context_summary(briefing_data)


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    enhancer = PromptEnhancer(data_dir="data")
    
    # Test with Wolf's data
    test_briefing = {
        "branche": "beratung",
        "unternehmensgroesse": "solo",
        "hauptleistung": "Beratung von Unternehmen zur Integration von KI",
    }
    
    # Test context block generation
    context_block = enhancer.build_context_block(test_briefing)
    
    print("=" * 80)
    print("CONTEXT BLOCK (HTML):")
    print("=" * 80)
    print(context_block)
    print("=" * 80)
    
    # Test text summary
    summary = enhancer.get_context_summary(test_briefing)
    print("\nCONTEXT SUMMARY (TEXT):")
    print("=" * 80)
    print(summary)
    print("=" * 80)
    
    # Test whitelist
    print("\n" + "=" * 80)
    print("WHITELIST TEST:")
    print("=" * 80)
    
    test_prompts = [
        "unternehmensprofil_markt",  # Should get context
        "quick_wins",                 # Should NOT get context
        "executive_summary",          # Should NOT get context
    ]
    
    for prompt_name in test_prompts:
        try:
            enhanced = enhancer.enhance_prompt(prompt_name, test_briefing)
            has_context = "Branchen-Context:" in enhanced
            print(f"✅ {prompt_name}: Context={'YES ✓' if has_context else 'NO ✗'}")
        except Exception as e:
            print(f"❌ {prompt_name}: Error - {e}")

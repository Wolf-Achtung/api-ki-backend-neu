# -*- coding: utf-8 -*-
"""
Prompt Enhancer - Injects context into existing prompts
Optimized for Wolf's ki-sicherheit.jetzt backend

This service works WITH Wolf's existing prompt_loader.py system.
It loads prompts via prompt_loader, injects context, and returns enhanced prompts.

Author: Wolf Hohl / Claude
Version: 2.1.0-Backend-Optimized
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from services.prompt_builder import PromptBuilder

log = logging.getLogger(__name__)


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
        3. Injects the context block into the prompt
        4. Returns the enhanced prompt
        
        Args:
            prompt_name: Name of the prompt (e.g., 'quick_wins')
            briefing_data: Complete briefing data
            
        Returns:
            Enhanced prompt with injected context
        """
        try:
            # Import prompt_loader dynamically to avoid circular imports
            from services.prompt_loader import load_prompt
            
            # Load base prompt (without variable interpolation yet)
            # We'll do variable interpolation in gpt_analyze.py as before
            base_prompt = load_prompt(prompt_name, lang="de", vars_dict=None)
            
            if not isinstance(base_prompt, str):
                log.warning("⚠️ Prompt '%s' returned non-string type: %s", prompt_name, type(base_prompt))
                return str(base_prompt)
            
            # Build context block
            context_block = self.build_context_block(briefing_data)
            
            # Inject context block - three strategies in order of preference
            enhanced: str
            
            # Strategy 1: Replace {CONTEXT_BLOCK} placeholder if present
            if '{CONTEXT_BLOCK}' in base_prompt:
                enhanced = base_prompt.replace('{CONTEXT_BLOCK}', context_block)
                log.debug("✅ Injected context block into prompt '%s'", prompt_name)
                return enhanced
            
            # Strategy 2: Insert after first <section> or <div> tag
            import re
            match = re.search(r'(<(?:section|div)[^>]*>)', base_prompt, re.IGNORECASE)
            if match:
                pos = match.end()
                enhanced = base_prompt[:pos] + "\n" + context_block + "\n" + base_prompt[pos:]
                log.debug("✅ Prepended context block to prompt '%s'", prompt_name)
                return enhanced
            
            # Strategy 3: Fallback - just prepend to beginning
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

# -*- coding: utf-8 -*-
"""
Prompt Enhancer - Injects context into existing prompts
Optimized for ki-sicherheit.jetzt backend

This service works WITH the existing prompt_loader.py system.
It loads prompts via prompt_loader, injects context, and returns enhanced prompts.

Version: 2.3.2-Size-Mapping-TypedDict
"""
from __future__ import annotations

import logging
from typing import Any, Dict, TypedDict

from services.prompt_builder import PromptBuilder

log = logging.getLogger(__name__)


class RoadmapConstraints(TypedDict):
    """Typed structure for roadmap size constraints."""
    max_budget_total: int
    max_budget_per_phase: int
    team_structure: str
    phase_duration_weeks: int
    example_team: str
    realistic_capacity: str


# Roadmap constraints by company size
ROADMAP_CONSTRAINTS: Dict[str, RoadmapConstraints] = {
    "solo": {
        "max_budget_total": 10000,
        "max_budget_per_phase": 3000,
        "team_structure": "Sie + maximal 1–2 Freelancer",
        "phase_duration_weeks": 4,
        "example_team": "1 Backend-Dev (Freelance, 20h)",
        "realistic_capacity": "Sie arbeiten hauptsächlich selbst, Freelancer für Spezialaufgaben",
    },
    "team": {
        "max_budget_total": 50000,
        "max_budget_per_phase": 15000,
        "team_structure": "Kernteam + externe Experten",
        "phase_duration_weeks": 4,
        "example_team": "2–3 Entwickler + 1 Projektleiter:in",
        "realistic_capacity": "Kleines internes Team + punktuelle Verstärkung",
    },
    "kmu": {
        "max_budget_total": 200000,
        "max_budget_per_phase": 60000,
        "team_structure": "Dediziertes Projektteam",
        "phase_duration_weeks": 6,
        "example_team": "5–8 Entwickler:innen + PM + Architect",
        "realistic_capacity": "Vollständiges Projektteam mit verschiedenen Rollen",
    },
}


def _normalize_size(raw_size: str | None) -> str:
    """
    Normalize size value from briefing to internal ROADMAP_CONSTRAINTS key.

    Supports legacy values ("klein", "mittel", "small", "small_team") for
    backwards compatibility, mappt aber intern immer auf 'solo' | 'team' | 'kmu'.
    """
    if not raw_size:
        return "team"

    raw = raw_size.strip().lower()
    alias_map: Dict[str, str] = {
        "klein": "team",
        "small": "team",
        "small_team": "team",
        "mittel": "kmu",
        "medium": "kmu",
    }
    size = alias_map.get(raw, raw)
    if size not in ROADMAP_CONSTRAINTS:
        return "team"
    return size


def enhance_roadmap_prompt(base_prompt: str, context: Dict[str, Any]) -> str:
    """
    Inject size-specific constraints into roadmap prompt.

    Args:
        base_prompt: Original prompt text
        context: Briefing data with unternehmensgroesse, investitionsbudget

    Returns:
        Enhanced prompt with size constraints
    """
    size = _normalize_size(context.get("unternehmensgroesse"))  # maps to solo/team/kmu
    constraints = ROADMAP_CONSTRAINTS[size]

    # Get investment budget from briefing (aligned mit Formular-Optionen)
    investment_budget = context.get("investitionsbudget", "2000_10000")
    investment_map: Dict[str, int] = {
        "unter_2000": 2000,
        "2000_10000": 10000,
        "10000_50000": 50000,
        # Für „ueber_50000“ und „unklar“ nutzen wir die maximale sinnvolle Größe laut Size-Constraints
        "ueber_50000": constraints["max_budget_total"],
        "unklar": constraints["max_budget_total"],
    }
    budget_from_map: int = investment_map.get(
        investment_budget, constraints["max_budget_total"]
    )

    max_budget_total: int = constraints["max_budget_total"]
    max_realistic_budget = min(max_budget_total, budget_from_map)

    size_context = f"""
KRITISCHE VORGABEN – Unternehmensgröße: {size.upper()}

Budget-Grenzen (STRIKT EINHALTEN!):
- Gesamt-Budget für 90 Tage: MAX €{max_realistic_budget:,}
- Budget pro Phase: MAX €{constraints['max_budget_per_phase']:,}
- Angegebenes Investment-Budget (Kategorie): {investment_budget}

Team-Struktur (REALISTISCH!):
- {constraints['team_structure']}
- Beispiel: {constraints['example_team']}
- Kapazität: {constraints['realistic_capacity']}

VERBOTEN für {size}:
- KEINE Projektteams, die offensichtlich nicht zu dieser Unternehmensgröße passen
- KEINE Budgets > €{max_realistic_budget:,}
- KEINE unrealistischen Teamgrößen

Die Roadmap MUSS mit dem realen Budget und der Unternehmensgröße umsetzbar sein!

---

"""

    return size_context + base_prompt


class PromptEnhancer:
    """
    Enhances existing prompts with contextual information.
    Works with the existing prompt_loader.py system.
    """

    def __init__(self, data_dir: str = "data") -> None:
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
        branche = briefing_data.get("branche", "")
        groesse = briefing_data.get("unternehmensgroesse", "")

        if not branche or not groesse:
            return "<!-- Context data incomplete -->"

        # Load contexts
        branch_ctx = self.builder.load_context("branch", branche)
        size_ctx = self.builder.load_context("size", groesse)

        log.info("✅ Context loaded: branch=%s, size=%s", branche, groesse)

        # Build compact HTML context block
        context_html = self._build_html_block(branch_ctx, size_ctx)

        return context_html

    def _build_html_block(
        self, branch_ctx: Dict[str, Any], size_ctx: Dict[str, Any]
    ) -> str:
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
        chars = size_ctx.get("characteristics", {})
        budget = size_ctx.get("budget_realistic", {})

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
        # Only these prompts get context block
        PROMPTS_WITH_CONTEXT = {
            "unternehmensprofil_markt",  # Main profile page - needs context
            # Weitere Prompts bei Bedarf ergänzen
        }

        try:
            from services.prompt_loader import load_prompt

            base_prompt = load_prompt(prompt_name, lang="de", vars_dict=None)

            if not isinstance(base_prompt, str):
                log.warning(
                    "⚠️ Prompt '%s' returned non-string type: %s",
                    prompt_name,
                    type(base_prompt),
                )
                return str(base_prompt)

            # Kein Kontext für nicht gelistete Prompts
            if prompt_name not in PROMPTS_WITH_CONTEXT:
                log.debug(
                    "⏭️  Skipping context for '%s' (not in whitelist)", prompt_name
                )

                # Roadmap-Constraints anwenden, falls Roadmap-Prompt
                ROADMAP_PROMPTS = {"roadmap", "roadmap_12m", "pilot_plan", "roadmap_90d"}
                if prompt_name in ROADMAP_PROMPTS:
                    log.info("🎯 Applying roadmap size constraints for '%s'", prompt_name)
                    base_prompt = enhance_roadmap_prompt(base_prompt, briefing_data)

                return base_prompt

            # Kontextblock aufbauen
            context_block = self.build_context_block(briefing_data)

            # Kontext injizieren
            if "{CONTEXT_BLOCK}" in base_prompt:
                enhanced = base_prompt.replace("{CONTEXT_BLOCK}", context_block)
                log.info("✅ Injected context block into prompt '%s'", prompt_name)
            else:
                import re

                match = re.search(
                    r"(<(?:section|div)[^>]*>)", base_prompt, re.IGNORECASE
                )
                if match is not None:
                    pos = match.end()
                    enhanced = (
                        base_prompt[:pos]
                        + "\n"
                        + context_block
                        + "\n"
                        + base_prompt[pos:]
                    )
                    log.debug(
                        "✅ Prepended context block to prompt '%s'", prompt_name
                    )
                else:
                    enhanced = context_block + "\n\n" + base_prompt
                    log.debug(
                        "⚠️ No suitable injection point found, prepended context to '%s'",
                        prompt_name,
                    )

            return enhanced

        except FileNotFoundError as exc:
            log.error("❌ Prompt file not found for '%s': %s", prompt_name, exc)
            raise
        except Exception as exc:  # pragma: no cover - defensive
            log.error("❌ Failed to enhance prompt '%s': %s", prompt_name, exc)
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


if __name__ == "__main__":  # pragma: no cover - manual test harness
    logging.basicConfig(level=logging.DEBUG)

    enhancer = PromptEnhancer(data_dir="data")

    test_briefing: Dict[str, Any] = {
        "branche": "beratung",
        "unternehmensgroesse": "solo",
        "hauptleistung": "Beratung von Unternehmen zur Integration von KI",
    }

    context_block = enhancer.build_context_block(test_briefing)
    print("=" * 80)
    print("CONTEXT BLOCK (HTML):")
    print("=" * 80)
    print(context_block)
    print("=" * 80)

    summary = enhancer.get_context_summary(test_briefing)
    print("\nCONTEXT SUMMARY (TEXT):")
    print("=" * 80)
    print(summary)
    print("=" * 80)

    print("\n" + "=" * 80)
    print("WHITELIST TEST:")
    print("=" * 80)

    for prompt_name in ["unternehmensprofil_markt", "quick_wins", "executive_summary"]:
        try:
            enhanced = enhancer.enhance_prompt(prompt_name, test_briefing)
            has_context = "Branchen-Context:" in enhanced
            print(f"✅ {prompt_name}: Context={'YES ✓' if has_context else 'NO ✗'}")
        except Exception as exc:
            print(f"❌ {prompt_name}: Error - {exc}")

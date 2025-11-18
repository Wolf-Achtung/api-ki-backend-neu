# -*- coding: utf-8 -*-
"""
Prompt Builder Service - Loads and combines context data
Optimized for Wolf's ki-sicherheit.jetzt backend

Author: Wolf Hohl / Claude
Version: 2.1.0-Backend-Optimized
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)


class PromptBuilder:
    """
    Loads branch and size context files and combines them into prompts.
    Works with Wolf's existing backend structure.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize PromptBuilder.
        
        Args:
            data_dir: Path to data directory (relative or absolute)
        """
        # Support both relative and absolute paths
        self.data_dir = Path(data_dir).resolve()
        
        if not self.data_dir.exists():
            # Fallback: Try from /app/ root (Railway deployment)
            alt_path = Path("/app") / data_dir
            if alt_path.exists():
                self.data_dir = alt_path
                log.info(f"📁 Using data_dir: {self.data_dir}")
            else:
                log.warning(f"⚠️ data_dir not found: {self.data_dir}")
        else:
            log.info(f"📁 Using data_dir: {self.data_dir}")
        
        self.branch_dir = self.data_dir / "branch_contexts"
        self.size_dir = self.data_dir / "size_contexts"
        self.mappings_file = self.data_dir / "mappings.json"
        
        # Load mappings once at init
        self.mappings = self._load_mappings()
    
    def _load_mappings(self) -> Dict[str, str]:
        """Load branch/size key mappings from mappings.json"""
        if not self.mappings_file.exists():
            log.warning(f"⚠️ mappings.json not found at {self.mappings_file}")
            return {}
        
        try:
            with open(self.mappings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                mapping = data.get("mapping", {})
                return dict(mapping) if isinstance(mapping, dict) else {}
        except Exception as e:
            log.error(f"❌ Failed to load mappings.json: {e}")
            return {}
    
    def _normalize_key(self, key: str, context_type: str) -> str:
        """
        Normalize branch/size keys using mappings.
        
        Args:
            key: Original key (e.g., "bauwesen", "solo")
            context_type: "branch" or "size"
            
        Returns:
            Normalized key (e.g., "bau", "solo")
        """
        if not key:
            return ""
        
        # Check if there's a mapping
        mapped = self.mappings.get(key.lower())
        if mapped:
            log.debug(f"✅ Mapped '{key}' → '{mapped}'")
            return mapped
        
        # No mapping needed, return as-is
        return key.lower()
    
    def load_context(self, context_type: str, key: str) -> Dict[str, Any]:
        """
        Load a context file (branch or size).
        
        Args:
            context_type: "branch" or "size"
            key: Context key (e.g., "beratung", "solo")
            
        Returns:
            Dictionary with context data
        """
        if context_type not in ["branch", "size"]:
            raise ValueError(f"context_type must be 'branch' or 'size', got '{context_type}'")
        
        # Normalize the key using mappings
        normalized_key = self._normalize_key(key, context_type)
        
        # Determine directory
        context_dir = self.branch_dir if context_type == "branch" else self.size_dir
        
        # Try to load the file
        context_file = context_dir / f"{normalized_key}.json"
        
        if not context_file.exists():
            log.warning(f"⚠️ Context file not found: {context_file}")
            # Return minimal fallback
            return {
                "key": normalized_key,
                "display_name": normalized_key.capitalize(),
                "typical_workflows": [],
                "common_pain_points": [],
                "typical_tools": [],
            }
        
        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                log.debug(f"✅ Loaded context: {context_file.name}")
                # Ensure we return a dict, not Any
                return dict(data) if isinstance(data, dict) else {}
        except Exception as e:
            log.error(f"❌ Failed to load {context_file}: {e}")
            return {}
    
    def build_context_summary(self, briefing_data: Dict[str, Any]) -> str:
        """
        Build a text summary of branch + size context.
        
        Args:
            briefing_data: Briefing data with 'branche' and 'unternehmensgroesse'
            
        Returns:
            Text summary for prompt injection
        """
        branche = briefing_data.get('branche', '')
        groesse = briefing_data.get('unternehmensgroesse', '')
        
        if not branche or not groesse:
            return "<!-- No context data available -->"
        
        # Load contexts
        branch_ctx = self.load_context('branch', branche)
        size_ctx = self.load_context('size', groesse)
        
        # Build summary text
        summary_parts = []
        
        # Branch info
        if branch_ctx:
            summary_parts.append(f"**Branche:** {branch_ctx.get('display_name', branche)}")
            
            workflows = branch_ctx.get('typical_workflows', [])
            if workflows:
                summary_parts.append(f"\n**Typische Workflows:** {', '.join(workflows[:3])}")
            
            pain_points = branch_ctx.get('common_pain_points', [])
            if pain_points:
                summary_parts.append(f"\n**Häufigste Pain Points:** {', '.join(pain_points[:3])}")
        
        # Size info
        if size_ctx:
            summary_parts.append(f"\n\n**Unternehmensgröße:** {size_ctx.get('display_name', groesse)}")
            
            chars = size_ctx.get('characteristics', {})
            if chars:
                summary_parts.append(f"\n**Charakteristika:** {chars.get('mitarbeiter', 'N/A')} Mitarbeiter")
            
            budget = size_ctx.get('budget_realistic', {})
            if budget:
                summary_parts.append(
                    f"\n**Budget:** Max. {budget.get('capex_max', 0):,}€ CAPEX, "
                    f"{budget.get('opex_monthly_max', 0)}€/Monat OPEX"
                )
            
            forbidden = size_ctx.get('forbidden_recommendations', [])
            if forbidden:
                summary_parts.append(f"\n**❌ Verboten:** {', '.join(forbidden[:3])}")
        
        return '\n'.join(summary_parts)


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    builder = PromptBuilder(data_dir="data")
    
    # Test with Wolf's data
    test_briefing = {
        "branche": "beratung",
        "unternehmensgroesse": "solo",
    }
    
    summary = builder.build_context_summary(test_briefing)
    
    print("=" * 80)
    print("CONTEXT SUMMARY:")
    print("=" * 80)
    print(summary)
    print("=" * 80)

"""
Prompt Engine – nutzt PromptLoader & baut Eingaben aus Briefing + Benchmarks.

Hinweis: Diese Datei kapselt lediglich die Prompt-Vorbereitung (kein unmittelbarer
API-Call). So können OpenAI/Perplexity/Tavily-Adapter separat gepflegt werden.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from .prompt_loader import PromptLoader

@dataclass
class PromptContext:
    lang: str = "de"
    branche: Optional[str] = None
    size: Optional[str] = None
    state: Optional[str] = None
    company: Optional[str] = None
    main_service: Optional[str] = None
    answers: Dict[str, Any] = None

class PromptEngine:
    def __init__(self, prompt_dir: str | Path = "prompts", manifest: str | Path = "prompts/prompt_manifest.json"):
        self.loader = PromptLoader(prompt_dir, manifest)

    def build(self, ctx: PromptContext, keys: Optional[List[str]] = None) -> Dict[str, str]:
        bundle = self.loader.load_bundle(
            lang=ctx.lang, keys=keys, branche=ctx.branche, size=ctx.size
        )
        # Inject dynamic meta block for system prompt
        meta = {
            "branche": ctx.branche, "size": ctx.size, "state": ctx.state,
            "company": ctx.company, "main_service": ctx.main_service
        }
        bundle["__meta__"] = json.dumps(meta, ensure_ascii=False, indent=2)
        return bundle

# -*- coding: utf-8 -*-
"""
services.prompt_loader – v1.3
Manifest‑basierter Prompt‑Loader mit Branch‑Overrides und {{var}}/{{UPPER}}‑Interpolation.

Änderungen ggü. v1.2
--------------------
- Zentralisierte Interpolation via ``services.prompt_engine`` (vermeidet Doppel‑Logik).
- Kleiner LRU‑Cache für Templates (IO‑Reduktion).
- Strengeres Fehlerbild + klare Exceptions.
- Einheitliche Normalisierung von Branchenlabels.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import os, json, io, re
from functools import lru_cache

from .prompt_engine import render_template  # zentrale Interpolation

class PromptNotFound(FileNotFoundError):
    pass

def _read_text(path: str) -> str:
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()

def _find_root() -> str:
    return os.getenv("PROMPTS_ROOT", "prompts")

def _manifest_path(root: str) -> str:
    return os.getenv("PROMPT_MANIFEST", os.path.join(root, "prompt_manifest.json"))

@lru_cache(maxsize=1)
def _load_manifest(root: str) -> Dict[str, Any]:
    p = _manifest_path(root)
    if not os.path.exists(p):
        return {}
    with io.open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _normalize_branch_code(label: str) -> str:
    if not label: return ""
    label = label.strip().lower()
    mapping = {
        "marketing & werbung":"marketing", "marketing":"marketing",
        "beratung & dienstleistungen":"beratung", "beratung":"beratung",
        "it & software":"it", "software":"it", "it":"it",
        "finanzen & versicherungen":"finanzen", "finanzen":"finanzen",
        "handel & e-commerce":"handel", "e-commerce":"handel",
        "bildung":"bildung",
        "verwaltung":"verwaltung",
        "gesundheit & pflege":"gesundheit", "gesundheit":"gesundheit",
        "bauwesen & architektur":"bau", "bau":"bau",
        "medien & kreativwirtschaft":"medien", "medien":"medien",
        "industrie & produktion":"industrie", "industrie":"industrie",
        "transport & logistik":"logistik", "logistik":"logistik",
    }
    return mapping.get(label, re.sub(r"[^a-z0-9]+","_", label).strip("_"))

def load_prompt(section: str, lang: str="de", vars_dict: Optional[Dict[str, Any]] = None) -> str:
    root = _find_root()
    manifest = _load_manifest(root) or {}

    langs = manifest.get("languages", {})
    cfg = langs.get(lang, {})
    dir_ = cfg.get("dir", lang)
    sections = cfg.get("sections", {})
    aliases = cfg.get("aliases", {})
    ov = (manifest.get("overrides", {}) or {}).get("by_branch", {})

    # Alias-Auflösung
    key = aliases.get(section, section)
    file_rel = sections.get(key)
    if not file_rel:
        # Fallback: prompts/<lang>/<section>.txt
        file_rel = f"{lang}/{section}.txt"

    vars_dict = vars_dict or {}

    # Branch-Override prüfen
    branch_label = vars_dict.get("BRANCHE_LABEL") or vars_dict.get("branche") or ""
    branch_code = _normalize_branch_code(branch_label)
    if branch_code and key in ov:
        pattern = ov[key]  # z. B. overrides/recommendations/{branch}_de.txt ODER overrides/branche/{branch}/*
        candidate_rel = pattern.replace("{branch}", branch_code)
        ovr_path = os.path.join(root, dir_, candidate_rel)
        if os.path.exists(ovr_path):
            return render_template(_read_text(ovr_path), vars_dict, escape=True)

    # Default-Pfad über Manifest
    p = os.path.join(root, dir_, file_rel)
    if not os.path.exists(p):
        # finaler Fallback
        p = os.path.join(root, lang, f"{section}.txt")
        if not os.path.exists(p):
            raise PromptNotFound(f"Prompt not found for section='{section}', lang='{lang}' (tried {file_rel})")

    return render_template(_read_text(p), vars_dict, escape=True)

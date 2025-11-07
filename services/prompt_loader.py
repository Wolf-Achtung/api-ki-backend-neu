# -*- coding: utf-8 -*-
"""
services.prompt_loader – v1.2
Mehrsprachiger Prompt-Loader mit Manifest-Support, Branch-Overrides und {{var}}-Interpolation.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import os, json, io, re, html

class PromptNotFound(FileNotFoundError):
    pass

def _read_text(path: str) -> str:
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()

def _find_root() -> str:
    return os.getenv("PROMPTS_ROOT", "prompts")

def _manifest_path(root: str) -> str:
    return os.getenv("PROMPT_MANIFEST", os.path.join(root, "prompt_manifest.json"))

def _load_manifest(root: str) -> Dict[str, Any]:
    p = _manifest_path(root)
    if not os.path.exists(p):
        return {}
    with io.open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _normalize_branch_code(label: str) -> str:
    if not label: return ""
    label = label.lower()
    m = {
        "marketing & werbung":"marketing","beratung & dienstleistungen":"beratung","it & software":"it",
        "finanzen & versicherungen":"finanzen","handel & e-commerce":"handel","bildung":"bildung",
        "verwaltung":"verwaltung","gesundheit & pflege":"gesundheit","bauwesen & architektur":"bau",
        "medien & kreativwirtschaft":"medien","industrie & produktion":"industrie","transport & logistik":"logistik"
    }
    return m.get(label, re.sub(r"[^a-z0-9]+","_", label).strip("_"))

def _interpolate(template: str, vars_dict: Dict[str, Any]) -> str:
    def repl(m):
        key = m.group(1).strip()
        val = vars_dict.get(key, "")
        if isinstance(val, (dict, list)):
            try:
                val = json.dumps(val, ensure_ascii=False)
            except Exception:
                val = str(val)
        return html.escape(str(val))
    return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, template)

def load_prompt(section: str, lang: str="de", vars_dict: Optional[Dict[str, Any]]=None) -> str:
    root = _find_root()
    m = _load_manifest(root) or {}
    langs = (m.get("languages") or {})
    cfg = langs.get(lang) or {}
    dir_ = cfg.get("dir") or lang
    sections = cfg.get("sections") or {}
    aliases = cfg.get("aliases") or {}
    ov = (m.get("overrides") or {}).get("by_branch") or {}

    # resolve section by aliases
    key = section
    if key not in sections and key in aliases:
        key = aliases.get(key, key)

    file_rel = sections.get(key)
    if not file_rel:
        # fallback default path
        file_rel = f"{lang}/{section}.txt"

    # override by branch (if pattern present and vars_dict has BRANCHE_LABEL)
    branch_label = (vars_dict or {}).get("BRANCHE_LABEL") or (vars_dict or {}).get("branche") or ""
    branch_code = _normalize_branch_code(branch_label)
    if branch_code and key in ov:
        pattern = ov[key]  # e.g., overrides/recommendations/{branch}_de.txt
        rel = pattern.replace("{branch}", branch_code)
        ovr_path = os.path.join(root, dir_, rel)
        if os.path.exists(ovr_path):
            template = _read_text(ovr_path)
            return _interpolate(template, vars_dict or {})

    # default path via manifest
    p = os.path.join(root, dir_, file_rel)
    if not os.path.exists(p):
        # final fallback: prompts/<lang>/<section>.txt
        p = os.path.join(root, lang, f"{section}.txt")
        if not os.path.exists(p):
            raise PromptNotFound(f"Prompt not found for section='{section}', lang='{lang}' (tried {file_rel})")
    template = _read_text(p)
    return _interpolate(template, vars_dict or {})

"""
Prompt Loader – i18n‑fähig, manifest‑gesteuert, mit Branch/Größen‑Overrides.

- Lädt Prompts aus ./prompts/<lang>/
- Optionales Manifest (prompts/prompt_manifest.json) definiert Reihenfolge, Aliase & Typen.
- Unterstützt dynamische Overrides pro Branche und Unternehmensgröße: 
  ./prompts/<lang>/overrides/<branche>/<size>/<key>.md
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_LANG = "de"

@dataclass
class PromptSpec:
    key: str
    path: Path
    required: bool = True
    title: Optional[str] = None
    purpose: Optional[str] = None

class PromptLoader:
    def __init__(self, base_dir: str | Path = "prompts", manifest_path: str | Path = "prompts/prompt_manifest.json"):
        self.base_dir = Path(base_dir)
        self.manifest_path = Path(manifest_path)

    # ---------- public API ----------
    def load_bundle(
        self,
        lang: str = DEFAULT_LANG,
        keys: Optional[List[str]] = None,
        branche: Optional[str] = None,
        size: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Liefert ein Dict {key: content}. 
        Reihenfolge nach Manifest, wenn vorhanden; sonst alphabetisch.
        """
        lang_dir = self.base_dir / (lang or DEFAULT_LANG)
        manifest = self._read_manifest().get(lang or DEFAULT_LANG, {})

        bundle: Dict[str, str] = {}
        if keys is None:
            # gesamte Menge aus Manifest oder Dateisystem
            keys = list(manifest.keys()) if manifest else self._discover_keys(lang_dir)

        for key in keys:
            content = self._resolve_content(key, lang_dir, manifest, branche, size)
            if content is None:
                continue
            bundle[key] = content
        return bundle

    # ---------- intern ----------
    def _resolve_content(
        self, key: str, lang_dir: Path, manifest: Dict[str, dict], branche: Optional[str], size: Optional[str]
    ) -> Optional[str]:
        # 1) Override <branche>/<size>
        ov_path = lang_dir / "overrides"
        cand: List[Path] = []
        if branche and size:
            cand.append(ov_path / branche / size / f"{key}.md")
        if branche:
            cand.append(ov_path / branche / f"{key}.md")
        # 2) Manifest‑Pfad
        if key in manifest and manifest[key].get("path"):
            cand.append(lang_dir / manifest[key]["path"])
        # 3) Fallbacks
        cand.append(lang_dir / f"{key}.md")
        cand.append(lang_dir / f"{key}.txt")

        for p in cand:
            if p.exists():
                try:
                    return p.read_text(encoding="utf-8")
                except Exception:
                    return p.read_text(errors="ignore")
        return None

    def _discover_keys(self, lang_dir: Path) -> List[str]:
        keys = []
        if lang_dir.exists():
            for p in sorted(lang_dir.glob("*.md")):
                keys.append(p.stem)
            for p in sorted(lang_dir.glob("*.txt")):
                if p.stem not in keys:
                    keys.append(p.stem)
        return keys

    def _read_manifest(self) -> Dict[str, Dict[str, dict]]:
        if not self.manifest_path.exists():
            return {}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception:
            try:
                import json as _json
                return _json.loads(self.manifest_path.read_text(errors="ignore"))
            except Exception:
                return {}

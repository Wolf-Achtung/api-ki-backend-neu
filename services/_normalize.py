# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict

def _briefing_to_dict(briefing: Any) -> Dict[str, Any]:
    """Toleranter Normalizer: akzeptiert dict, pydantic/SQLAlchemy-Objekte, dataclasses.
    Gibt stets ein normales Dict zurück (lower-case Keys enthalten).
    """
    if briefing is None:
        return {}
    if isinstance(briefing, dict):
        return briefing
    # pydantic v2
    try:
        if hasattr(briefing, "model_dump"):
            return dict(briefing.model_dump())
    except Exception:
        pass
    # pydantic v1
    try:
        if hasattr(briefing, "dict"):
            return dict(briefing.dict())
    except Exception:
        pass
    # dataclass
    try:
        from dataclasses import asdict, is_dataclass
        if is_dataclass(briefing):
            return asdict(briefing)
    except Exception:
        pass
    # SQLAlchemy/ORM: __dict__ ohne private Felder
    try:
        data = {}
        for k in dir(briefing):
            if k.startswith("_"):
                continue
            try:
                v = getattr(briefing, k)
            except Exception:
                continue
            # uninteressante Callables/Methods filtern
            if callable(v):
                continue
            # einfache Typen übernehmen
            if isinstance(v, (str, int, float, bool, list, dict, tuple)) or v is None:
                data[k] = v
        if data:
            return data
    except Exception:
        pass
    # Fallback: leeres Dict
    return {}

# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class EvalResult:
    name: str
    score: float  # 0.0 .. 1.0
    findings: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    breakdown: Dict[str, float] = field(default_factory=dict)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def pct(x: float) -> str:
    return f"{round(x*100)}%"

# -*- coding: utf-8 -*-
"""KIS-B Konsistenz-Checker: alle Seiten-Budget-Tabellen müssen übereinstimmen.

Die Report-„Überproduktion" (mid-sentence-Trims, halb-leere Seiten) entstand,
weil vier unabhängige Budget-Tabellen auseinanderliefen. Dieser Guard verhindert
erneutes Drift: wer eine Tabelle ändert, muss alle ändern.
"""
from __future__ import annotations

from config.size_profiles import get_size_profile
from services.report_validator import ReportValidator
from services.solo_compact_engine import MAX_PAGES_BY_SIZE, SoloCompactConfig

# size_profiles nutzt Größen-Strings statt solo/team/kmu.
_SIZE_KEY = {"solo": "1", "team": "2-10", "kmu": "11-100"}


def test_max_pages_tables_agree():
    """MAX_PAGES_BY_SIZE, size_profiles und report_validator sind identisch."""
    for size in ("solo", "team", "kmu"):
        engine = MAX_PAGES_BY_SIZE[size]
        profile = get_size_profile(_SIZE_KEY[size])["max_pages"]
        validator = ReportValidator.MAX_REPORT_PAGES_BY_SIZE[size]
        assert engine == profile == validator, (
            f"Budget-Drift für '{size}': engine={engine}, "
            f"size_profile={profile}, validator={validator}"
        )


def test_solo_config_matches_table():
    """SoloCompactConfig.max_pages == MAX_PAGES_BY_SIZE['solo']."""
    assert SoloCompactConfig().max_pages == MAX_PAGES_BY_SIZE["solo"]


def test_page_budgets_are_monotonic():
    """solo <= kmu <= team (team ist der ausführlichste Report-Typ)."""
    assert MAX_PAGES_BY_SIZE["solo"] <= MAX_PAGES_BY_SIZE["kmu"] <= MAX_PAGES_BY_SIZE["team"]

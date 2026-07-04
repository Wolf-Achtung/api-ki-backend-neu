# -*- coding: utf-8 -*-
"""
FIX-KIS-1188-ITEM2: OPEX-bridge sentence must be appended to Strategy S5.

R1 + KPA report 120 €/Mo Software-Grundkosten; Strategy reports a higher
OPEX figure because it bundles Software + Tool-Lizenzen + anteilige
Betriebskosten. Without an explicit bridge, AI-literate customers read this
as an inconsistency.

services.strategy_renderer.inject_opex_bridge is the testable seam used by
render_strategy_html.
"""
from __future__ import annotations

import pytest

from services.strategy_renderer import inject_opex_bridge


S5_BODY = "<p>Hier die Investitionstabelle.</p>"


class TestOPEXBridge:

    def test_bridge_is_appended(self):
        out = inject_opex_bridge(S5_BODY, "300")
        assert out.startswith(S5_BODY)
        assert "OPEX-Methodik" in out

    def test_bridge_mentions_both_numbers(self):
        # KIS-1248: R1-OPEX kommt vom Aufrufer statt hartkodiert (Lauf 1238:
        # "120 €/Monat" stand neben kanonischen 600 €/Monat).
        out = inject_opex_bridge(S5_BODY, "300", r1_opex_monatlich="600")
        assert "300 €/Monat" in out  # Strategy figure
        assert "600 €/Monat" in out  # kanonischer R1-Wert
        assert "120" not in out
        assert "KI-Readiness Report" in out
        assert "KI-Status-Report" not in out

    def test_bridge_without_r1_value_stays_numberless(self):
        out = inject_opex_bridge(S5_BODY, "300")
        assert "reinen" in out and "Software-Grundkosten" in out
        assert "120" not in out

    def test_bridge_explains_strategy_scope(self):
        out = inject_opex_bridge(S5_BODY, "450")
        # Strategy includes Software + Tool-Lizenzen + Betriebskosten
        assert "Tool-Abos" in out or "Tool-Lizenzen" in out
        assert "Betriebskosten" in out

    def test_bridge_explains_both_are_correct(self):
        out = inject_opex_bridge(S5_BODY, "300")
        assert "methodisch korrekt" in out

    def test_bridge_uses_dedicated_modifier_class(self):
        """Dedicated CSS class so the OPEX bridge can be styled/scraped
        independently from the existing ROI methodology hint."""
        out = inject_opex_bridge(S5_BODY, "300")
        assert "methodik-hinweis--opex" in out

    def test_bridge_noop_when_opex_value_missing(self):
        """No bridge if the budget figure isn't available — we never
        inject a partial/empty number."""
        assert inject_opex_bridge(S5_BODY, "") == S5_BODY

    def test_bridge_noop_on_empty_s5(self):
        assert inject_opex_bridge("", "300") == ""

    @pytest.mark.parametrize("value", ["300", "450", "1.200"])
    def test_bridge_inlines_caller_value(self, value):
        out = inject_opex_bridge(S5_BODY, value)
        assert f"{value} €/Monat" in out

# -*- coding: utf-8 -*-
"""
Tests for Fix-Batch H - KPI Labels & Locale 100% German

Tests:
- All KPI labels are in ui_labels.json
- KPI visuals use ui() for labels
- German labels are used by default
"""

import os
import pytest
import json

# Set test environment before imports
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("OPENAI_API_KEY", "test-api-key")


class TestKPILabelsInUILabels:
    """Test that all required KPI labels exist in ui_labels.json."""

    def test_kpi_roi_exists(self):
        """Test that kpi_roi exists in ui_labels.json."""
        from pathlib import Path

        labels_path = Path(__file__).parent.parent / "i18n" / "ui_labels.json"
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = json.load(f)

        assert "kpi_roi" in labels
        assert labels["kpi_roi"]["de"] == "ROI"

    def test_kpi_payback_progress_exists(self):
        """Test that kpi_payback_progress exists in ui_labels.json."""
        from pathlib import Path

        labels_path = Path(__file__).parent.parent / "i18n" / "ui_labels.json"
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = json.load(f)

        assert "kpi_payback_progress" in labels
        assert labels["kpi_payback_progress"]["de"] == "Amortisationsfortschritt"

    def test_kpi_time_savings_hours_exists(self):
        """Test that kpi_time_savings_hours exists in ui_labels.json."""
        from pathlib import Path

        labels_path = Path(__file__).parent.parent / "i18n" / "ui_labels.json"
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = json.load(f)

        assert "kpi_time_savings_hours" in labels
        assert labels["kpi_time_savings_hours"]["de"] == "Zeitersparnis (Stunden)"

    def test_kpi_monthly_savings_exists(self):
        """Test that kpi_monthly_savings exists in ui_labels.json."""
        from pathlib import Path

        labels_path = Path(__file__).parent.parent / "i18n" / "ui_labels.json"
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = json.load(f)

        assert "kpi_monthly_savings" in labels
        assert labels["kpi_monthly_savings"]["de"] == "Monatliche Ersparnis (€)"

    def test_kpi_trend_labels_exist(self):
        """Test that trend labels exist in ui_labels.json."""
        from pathlib import Path

        labels_path = Path(__file__).parent.parent / "i18n" / "ui_labels.json"
        with open(labels_path, 'r', encoding='utf-8') as f:
            labels = json.load(f)

        assert "kpi_12month_trend" in labels
        assert labels["kpi_12month_trend"]["de"] == "12-Monats-Trend"

        assert "kpi_expected_trend" in labels
        assert labels["kpi_expected_trend"]["de"] == "Erwarteter Verlauf"

        assert "kpi_roi_comparison" in labels
        assert labels["kpi_roi_comparison"]["de"] == "ROI-Vergleich"


class TestKPIVisualsUseUI:
    """Test that KPI visuals use ui() for localization."""

    def test_kpi_visuals_has_ui_import(self):
        """Test that kpi_visuals.py imports get_label as ui."""
        from utils import kpi_visuals
        import inspect

        source = inspect.getsource(kpi_visuals)

        # Should have get_label import (aliased as ui)
        assert "from services.i18n import get_label as ui" in source

    def test_kpi_visuals_uses_ui_for_labels(self):
        """Test that kpi_visuals.py uses ui() for labels."""
        from utils import kpi_visuals
        import inspect

        source = inspect.getsource(kpi_visuals)

        # Should use ui() for KPI labels
        assert 'ui("kpi_roi_details"' in source
        assert 'ui("kpi_payback_months"' in source
        assert 'ui("kpi_time_savings_month"' in source

    def test_kpi_visuals_uses_ui_for_trend_labels(self):
        """Test that kpi_visuals.py uses ui() for trend labels."""
        from utils import kpi_visuals
        import inspect

        source = inspect.getsource(kpi_visuals)

        # Should use ui() for trend labels
        assert 'ui("kpi_12month_trend"' in source
        assert 'ui("kpi_expected_trend"' in source
        assert 'ui("kpi_roi_comparison"' in source


class TestGermanLabelsDefault:
    """Test that German labels are used by default."""

    def test_ui_returns_german_by_default(self):
        """Test that get_label() returns German label for de lang."""
        from services.i18n import get_label

        result = get_label("kpi_time_savings_month", "de")
        assert result == "Zeitersparnis/Monat"

    def test_ui_returns_english_for_en(self):
        """Test that get_label() returns English label for en lang."""
        from services.i18n import get_label

        result = get_label("kpi_time_savings_month", "en")
        assert result == "Time Savings/Month"

    def test_new_kpi_labels_german(self):
        """Test that new KPI labels return German."""
        from services.i18n import get_label

        assert get_label("kpi_roi", "de") == "ROI"
        assert get_label("kpi_payback_progress", "de") == "Amortisationsfortschritt"
        assert get_label("kpi_monthly_savings", "de") == "Monatliche Ersparnis (€)"


class TestBatchHIntegration:
    """Integration tests for Fix-Batch H."""

    def test_generate_kpi_visuals_de_labels(self):
        """Test that generate_kpi_visuals produces German labels."""
        # Only test if KPI visuals are enabled
        os.environ["ENABLE_KPI_VISUALS"] = "1"

        # Reload to pick up environment change
        import importlib
        import utils.kpi_visuals
        importlib.reload(utils.kpi_visuals)
        from utils.kpi_visuals import generate_kpi_visuals

        kpi = {
            "roi": 150.0,
            "payback_months": 6.0,
            "time_savings_hours": 40.0,
        }

        result = generate_kpi_visuals(kpi, lang="de")

        # Should produce HTML with German labels from ui_labels.json
        if result.get("bar_html"):
            html = result["bar_html"]
            # Check for German label presence (from ui_labels.json)
            assert "ROI" in html or "Amortisation" in html or "Zeitersparnis" in html

    def test_no_hardcoded_english_in_de_visuals(self):
        """Test that no hardcoded English appears in DE visuals."""
        os.environ["ENABLE_KPI_VISUALS"] = "1"
        from utils.kpi_visuals import generate_kpi_visuals

        kpi = {
            "roi": 150.0,
            "payback_months": 6.0,
            "time_savings_hours": 40.0,
        }

        result = generate_kpi_visuals(kpi, lang="de")

        # Should NOT have English labels when lang=de
        if result.get("html"):
            html = result["html"]
            # These should not appear in German output
            assert "Time Savings/Month" not in html
            assert "Payback Period" not in html

    def test_fix_batch_h_comment_exists(self):
        """Test that Fix-Batch H comment block exists."""
        from utils import kpi_visuals
        import inspect

        source = inspect.getsource(kpi_visuals)

        # Should have Fix-Batch H comments
        assert "Fix-Batch H" in source

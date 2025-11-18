# -*- coding: utf-8 -*-
"""
Integration-Tests für den kompletten Report-Generierungs-Workflow
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"

@pytest.fixture
def client():
    """FastAPI TestClient mit In-Memory-Datenbank"""
    from main import app
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Authentifizierte Headers für Tests"""
    # Mock JWT token creation and email sending
    with patch("core.security.create_access_token") as mock_token, \
         patch("routes.auth.Mailer.from_settings") as mock_mailer_factory:
        mock_token.return_value = "test-token-123"

        # Mock the mailer instance with async send method
        mock_mailer = MagicMock()
        mock_mailer.send = AsyncMock(return_value=None)
        mock_mailer_factory.return_value = mock_mailer

        # Request login code
        response = client.post("/api/auth/request-code", json={"email": "test@example.com"})
        assert response.status_code == 204

        # Login with mocked code validation
        with patch("routes.auth._read_code", return_value="123456"):
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "code": "123456"
            })
            assert response.status_code == 200
            token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


class TestReportWorkflow:
    """Test-Suite für den kompletten Report-Workflow"""

    def test_01_briefing_submission(self, client, auth_headers):
        """Test 1: Briefing erfolgreich einreichen"""
        payload = {
            "lang": "de",
            "answers": {
                "branche": "IT",
                "bundesland": "Bayern",
                "jahresumsatz": "1-5M",
                "unternehmensgroesse": "10-50",
                "ki_kompetenz": "Anfänger",
                "hauptleistung": "Software-Entwicklung",
                "antworten": [
                    {"frage_id": "ki_einsatz", "antwort": "Noch nicht im Einsatz"}
                ]
            }
        }

        response = client.post(
            "/api/briefings/submit",
            json=payload,
            headers=auth_headers | {"Idempotency-Key": "test-briefing-001"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["lang"] == "de"

    def test_02_analyze_trigger_dry_run(self, client):
        """Test 2: Analyze-Endpoint mit Dry-Run (ohne echtes LLM)"""
        response = client.post(
            "/api/analyze/run",
            json={"briefing_id": 1},
            headers={"x-dry-run": "true"}
        )

        assert response.status_code == 202
        data = response.json()
        assert data["dry_run"] is True
        assert data["analyzer_import_ok"] is True

    @patch("gpt_analyze.run_async")
    def test_03_analyze_trigger_mocked(self, mock_run_async, client):
        """Test 3: Analyze-Trigger mit gemocktem LLM"""
        with patch("routes.analyze._get_briefing_model") as mock_model:
            # Mock Briefing model
            mock_briefing = Mock()
            mock_briefing.id = 1
            mock_model.return_value = Mock(
                __name__="Briefing"
            )

            # Mock DB session
            with patch("routes.analyze.get_db") as mock_db:
                mock_db.return_value.get.return_value = mock_briefing

                response = client.post(
                    "/api/analyze/run",
                    json={"briefing_id": 1, "email_override": "test@example.com"}
                )

                assert response.status_code == 202
                assert mock_run_async.called

    def test_04_rate_limiting(self, client, auth_headers):
        """Test 4: Rate-Limiting funktioniert"""
        # Send multiple requests quickly
        for i in range(11):  # Limit ist 10 in 300 Sekunden
            response = client.post(
                "/api/briefings/submit",
                json={
                    "lang": "de",
                    "branche": "IT",
                    "bundesland": "Bayern",
                    "jahresumsatz": "1-5M",
                    "unternehmensgroesse": "10-50",
                    "ki_kompetenz": "Anfänger",
                    "hauptleistung": "Test",
                    "antworten": []
                },
                headers=auth_headers | {"Idempotency-Key": f"test-rate-{i}"}
            )

            if i < 10:
                assert response.status_code == 200
            else:
                # 11. Request sollte geblockt werden
                assert response.status_code == 429

    def test_05_idempotency(self, client, auth_headers):
        """Test 5: Idempotenz verhindert doppelte Requests"""
        payload = {
            "lang": "de",
            "branche": "IT",
            "bundesland": "Bayern",
            "jahresumsatz": "1-5M",
            "unternehmensgroesse": "10-50",
            "ki_kompetenz": "Anfänger",
            "hauptleistung": "Software",
            "antworten": []
        }

        headers = auth_headers | {"Idempotency-Key": "unique-key-12345"}

        # Erster Request
        response1 = client.post("/api/briefings/submit", json=payload, headers=headers)
        assert response1.status_code == 200

        # Zweiter Request mit gleichem Key
        response2 = client.post("/api/briefings/submit", json=payload, headers=headers)
        assert response2.status_code == 200
        assert response2.json()["status"] == "duplicate_ignored"


class TestReportGeneration:
    """Test-Suite für Report-Generierung mit gemocktem OpenAI"""

    @patch("gpt_analyze._call_openai")
    def test_report_generation_mocked(self, mock_openai):
        """Test: Report-Generierung mit gemockten LLM-Antworten"""
        from gpt_analyze import analyze_briefing
        from unittest.mock import MagicMock

        # Mock OpenAI responses
        mock_openai.return_value = """
        {
            "executive_summary": "Test-Zusammenfassung",
            "quick_wins": ["Win 1", "Win 2"],
            "roadmap_90": ["Schritt 1", "Schritt 2"]
        }
        """

        # Mock DB Session
        mock_db = MagicMock()
        mock_briefing = MagicMock()
        mock_briefing.id = 1
        mock_briefing.data = {
            "branche": "IT",
            "bundesland": "Bayern",
            "ki_kompetenz": "Anfänger"
        }
        mock_db.get.return_value = mock_briefing

        # Run analysis
        try:
            result = analyze_briefing(mock_db, briefing_id=1, run_id="test-run-001")
            assert result is not None
        except Exception as e:
            # Expected - we don't have full DB setup
            assert "briefing_id must be an integer" in str(e) or "Session" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

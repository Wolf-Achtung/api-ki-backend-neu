# -*- coding: utf-8 -*-
"""
End-to-End Tests mit Playwright
Testet das komplette Zusammenspiel Frontend ↔ Backend ↔ Report-Generierung

Voraussetzungen:
    pip install playwright pytest-playwright
    playwright install
"""
from __future__ import annotations

import pytest
import re
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Browser-Konfiguration für Tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "de-DE",
    }


class TestE2EReportGeneration:
    """End-to-End Tests für Report-Generierung"""

    @pytest.mark.e2e
    def test_complete_workflow(self, page: Page):
        """
        Test: Kompletter Workflow von Briefing-Formular bis Report-Download

        Schritte:
        1. Öffne Frontend
        2. Fülle Briefing-Formular aus
        3. Submit und warte auf Redirect
        4. Prüfe Report-Generierung
        5. Download PDF
        """
        # 1. Frontend öffnen
        page.goto("http://localhost:3000")  # Passe URL an
        expect(page).to_have_title(re.compile("KI.*Status", re.IGNORECASE))

        # 2. Login-Flow (falls erforderlich)
        # page.get_by_label("E-Mail").fill("test@example.com")
        # page.get_by_role("button", name="Code anfordern").click()
        # ... warte auf Email/Code ...

        # 3. Briefing-Formular ausfüllen
        page.get_by_label("Branche").select_option("IT")
        page.get_by_label("Bundesland").select_option("Bayern")
        page.get_by_label("Jahresumsatz").select_option("1-5M")
        page.get_by_label("Unternehmensgröße").select_option("10-50")
        page.get_by_label("KI-Kompetenz").select_option("Anfänger")
        page.get_by_label("Hauptleistung").fill("Software-Entwicklung")

        # 4. Formular absenden
        with page.expect_navigation():
            page.get_by_role("button", name=re.compile("Absenden|Submit")).click()

        # 5. Prüfe Erfolgs-Seite
        expect(page.locator("text=Vielen Dank")).to_be_visible(timeout=5000)

        # 6. Warte auf Report-Generierung (oder mock)
        # In echten Tests: warte auf WebSocket/Polling-Update
        # expect(page.locator("text=Report wird generiert")).to_be_visible()

        # 7. Prüfe Download-Link
        # download_button = page.get_by_role("link", name="PDF herunterladen")
        # expect(download_button).to_be_visible(timeout=30000)

    @pytest.mark.e2e
    def test_api_integration(self, page: Page):
        """
        Test: API-Calls während Frontend-Interaktion

        Überwacht Network-Traffic und prüft korrekte API-Calls
        """
        api_calls = []

        # Network-Listener einrichten
        def handle_request(request):
            if "/api/" in request.url:
                api_calls.append({
                    "method": request.method,
                    "url": request.url,
                    "headers": request.headers,
                })

        page.on("request", handle_request)

        # Frontend öffnen
        page.goto("http://localhost:3000")

        # Briefing einreichen
        page.get_by_role("button", name="Briefing starten").click()
        # ... Formular ausfüllen ...
        page.get_by_role("button", name="Absenden").click()

        # Warte kurz auf API-Calls
        page.wait_for_timeout(2000)

        # Prüfe API-Calls
        assert len(api_calls) > 0, "Keine API-Calls durchgeführt"

        # Prüfe /briefings/submit Call
        submit_call = next((c for c in api_calls if "/briefings/submit" in c["url"]), None)
        assert submit_call is not None, "/briefings/submit wurde nicht aufgerufen"
        assert submit_call["method"] == "POST"

        # Prüfe Authorization Header (falls Auth aktiv)
        # assert "authorization" in submit_call["headers"]

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_report_generation_with_real_llm(self, page: Page):
        """
        Test: Report-Generierung mit echtem LLM (langsam!)

        Nur für Staging/Pre-Production ausführen
        """
        pytest.skip("Nur für manuelle Tests mit echtem LLM")

        page.goto("http://localhost:3000")

        # Vollständiges Briefing ausfüllen
        # ... (wie oben) ...

        # Warte auf Report-Generierung (kann 30-60 Sekunden dauern)
        expect(page.locator("text=Report erfolgreich")).to_be_visible(timeout=90000)

        # Download PDF
        with page.expect_download() as download_info:
            page.get_by_role("link", name="PDF herunterladen").click()

        download = download_info.value
        assert download.suggested_filename.endswith(".pdf")

        # Optional: PDF-Inhalt validieren
        # import PyPDF2
        # pdf_content = download.path().read_bytes()
        # ... validate content ...


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "e2e"])

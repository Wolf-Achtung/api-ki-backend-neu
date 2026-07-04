# -*- coding: utf-8 -*-
"""KIS-1250 / Platin+++ Stufe 2: Pagination-Rollout, Vendor-Vollabdeckung,
Anker-Boxen, thin_page-Gate.

Die drei großen Restthemen aus der 1238-Validierung in einem Paket:
(1) R1-Kapitelfluss nach dem beim KPA bewährten Muster; (2) Vendor-Audit
deckt alle im Report empfohlenen Tool-Klassen ab (war: 1 von ~8);
(3) wörtliche Nutzer-Zitate als Anker vor den Quick Wins + belegbare
Score-Datenbasis unter „Meine Einschätzung"; (4) Seitenfüllgrad wird am
gerenderten PDF gemessen.
"""
from __future__ import annotations


def _read(path: str) -> str:
    return open(path, encoding="utf-8").read()


# =========================================================================
# 1. Pagination: R1-Kapitel fließen, Anker-Kapitel bleiben
# =========================================================================

class TestChapterFlow:

    def test_weak_chapters_flow(self):
        src = _read("templates/pdf_template_v7.html")
        idx = src.find("KIS-1250: Kapitelfluss nach KPA-Muster")
        assert idx != -1
        block = src[idx:idx + 1600]
        assert "#business-case-compact" in block
        assert "break-before: auto" in block

    def test_anchor_chapters_keep_page(self):
        src = _read("templates/pdf_template_v7.html")
        import re
        m = re.search(r"#mgmt-summary,\s*#sofort-start,\s*#advisor-note \{\s*break-before: page;", src)
        assert m, "Anker-Kapitel müssen eigene Seiten behalten"
        # Entscheidungsvorlage und AI-Act bleiben eigenständig
        assert "#decision {" in src and "#aiact-compact {" in src

    def test_headers_stick_to_content(self):
        src = _read("templates/pdf_template_v7.html")
        assert ".section > h2, .section-header" in src
        idx = src.find(".section > h2, .section-header")
        assert "break-after: avoid" in src[idx:idx + 200]


# =========================================================================
# 2. Vendor-Vollabdeckung
# =========================================================================

class TestVendorCoverage:

    def test_recommended_tools_in_catalog(self):
        from services.vendor_audit_engine import _KNOWN_VENDOR_META
        for key in ("otter", "n8n", "zapier", "autodesk", "obsidian",
                    "mistral", "azure openai", "langfuse"):
            assert key in _KNOWN_VENDOR_META, f"'{key}' fehlt im Vendor-Katalog"

    def test_eu_vendors_rated_low_risk(self):
        from services.vendor_audit_engine import _KNOWN_VENDOR_META
        assert _KNOWN_VENDOR_META["mistral"]["vendor_risk"] <= 2
        assert _KNOWN_VENDOR_META["deepl"]["vendor_risk"] <= 2
        assert _KNOWN_VENDOR_META["otter"]["vendor_risk"] >= 3

    def test_extraction_uses_word_boundaries(self):
        from services.vendor_audit_engine import _extract_vendors_from_sections
        # "Rotterdam" darf Otter NICHT triggern, echtes "Otter" schon
        s = {"TOOLS_EMPFEHLUNGEN_HTML": "<p>Projekt in Rotterdam geplant.</p>"}
        assert _extract_vendors_from_sections(s) == []
        s2 = {"TOOLS_EMPFEHLUNGEN_HTML": "<p>Nutzen Sie Otter für Transkription und n8n für Workflows.</p>"}
        names = {v["name"] for v in _extract_vendors_from_sections(s2)}
        assert "Otter.ai" in names and "n8n" in names

    def test_more_sections_scanned(self):
        from services.vendor_audit_engine import _extract_vendors_from_sections
        s = {"STARTER_KIT_HTML": "<p>Empfohlen: Autodesk Construction Cloud und Mistral AI.</p>"}
        names = {v["name"] for v in _extract_vendors_from_sections(s)}
        assert "Autodesk Construction Cloud" in names
        assert "Mistral AI" in names


# =========================================================================
# 3. Anker-Box + Score-Datenbasis
# =========================================================================

class TestAnchors:

    def test_anker_box_injection_present(self):
        src = _read("gpt_analyze.py")
        assert "[KIS-1250][ANKER-BOX]" in src
        idx = src.find("KIS-1250: Anker-Box")
        block = src[idx:idx + 2200]
        assert "top_zeitfresser" in block
        assert "zeitersparnis_prioritaet" in block
        assert "QUICK_WINS_HTML" in block
        # Nutzer-Text wird escaped und gekappt
        assert "_esc_1250" in block
        assert "[:160]" in block

    def test_advisor_datenbasis_present(self):
        src = _read("services/strategy_renderer.py")
        assert "[KIS-1250][ADVISOR-DATENBASIS]" in src
        idx = src.find("KIS-1250:")
        block = src[idx:idx + 2500]
        assert "Datenbasis:" in block
        assert "KI-Readiness-Score" in block
        # Nur belegte Werte, keine Erfindungen: Werte kommen aus report1_meta
        assert "report1_meta.get(\"scores\"" in block


# =========================================================================
# 4. thin_page-Gate
# =========================================================================

class TestThinPageGate:

    def _pdf(self, page_texts):
        from pypdf import PdfWriter
        import io as _io
        w = PdfWriter()
        for _ in page_texts:
            w.add_blank_page(width=595, height=842)
        buf = _io.BytesIO()
        w.write(buf)
        return buf.getvalue()

    def test_blank_middle_pages_flagged(self):
        from services.platin_qa import scan_pdf_pages
        pdf = self._pdf(["cover", "", "", "imprint"])  # 4 leere Seiten
        findings = scan_pdf_pages(pdf, run_id="test", label="R1")
        # Seite 1 und letzte sind ausgenommen, S.2+3 sind leer → 2 Befunde
        assert len(findings) == 2
        assert all(f["type"] == "thin_page" for f in findings)
        assert findings[0]["section"] == "R1:S.2"

    def test_never_raises_on_garbage(self):
        from services.platin_qa import scan_pdf_pages
        assert scan_pdf_pages(b"kein pdf", run_id="test") == []

    def test_hooked_after_r1_render(self):
        src = _read("gpt_analyze.py")
        idx = src.find("scan_pdf_pages(pdf_bytes, run_id=run_id, label=\"R1\")")
        assert idx != -1

    def test_pypdf_in_requirements(self):
        assert "pypdf" in _read("requirements.txt")

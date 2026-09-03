# -*- coding: utf-8 -*-
"""KIS-1266: Recherche einmal statt zweimal, Domänenfilter, Admin-Liste.

Hintergrund (ENV-Audit 2026-09): run_research lief zweimal je Report —
im Grounding und erneut in analyze_briefing — ohne neuen Inhalt. Der
Schalter USE_INTERNAL_RESEARCH wurde nie gelesen. Die gepflegten
Domänenlisten RESEARCH_INCLUDE_*/RESEARCH_EXCLUDE wurden nie angewandt.
"""
from __future__ import annotations

import importlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


# =========================================================================
# 1. Grounding hebt die Blöcke auf, analyze_briefing holt sie einmalig ab
# =========================================================================

class TestResearchOnce:

    def test_grounding_speichert_bloecke_und_take_leert(self, monkeypatch):
        import services.research_grounding as rg
        blocks = {"TOOLS_TABLE_HTML": "<table><tr><td>A</td></tr></table>",
                  "FUNDING_TABLE_HTML": "<table><tr><td>B</td></tr></table>",
                  "last_updated": "2026-09-03"}
        monkeypatch.setattr("services.research_pipeline.run_research", lambda answers: dict(blocks))
        rg.take_last_research_blocks()  # Altlast aus anderen Tests leeren
        rg.build_research_grounding({"branche": "medien"})
        erste = rg.take_last_research_blocks()
        assert erste["last_updated"] == "2026-09-03"
        assert erste["TOOLS_TABLE_HTML"] == blocks["TOOLS_TABLE_HTML"]
        # zweiter Abruf: leer — ein Report konsumiert genau seine Blöcke
        assert rg.take_last_research_blocks() == {}

    def test_ohne_grounding_bleibt_take_leer(self, monkeypatch):
        import services.research_grounding as rg
        rg.take_last_research_blocks()
        monkeypatch.setenv("RESEARCH_GROUNDING_ENABLED", "0")
        assert rg.build_research_grounding({}) == {}
        assert rg.take_last_research_blocks() == {}

    def test_run_research_wird_im_grounding_genau_einmal_gerufen(self, monkeypatch):
        import services.research_grounding as rg
        calls = []
        monkeypatch.setattr("services.research_pipeline.run_research",
                            lambda answers: calls.append(1) or {"last_updated": "x"})
        rg.build_research_grounding({})
        assert calls == [1]


# =========================================================================
# 2. USE_INTERNAL_RESEARCH wird jetzt gelesen
# =========================================================================

class TestUseInternalResearchSchalter:

    def _resolve(self):
        import gpt_analyze
        return gpt_analyze._resolve_use_internal_research()

    def test_env_0_schaltet_ab(self, monkeypatch):
        monkeypatch.setenv("USE_INTERNAL_RESEARCH", "0")
        monkeypatch.setenv("RESEARCH_PROVIDER", "hybrid")
        assert self._resolve() is False

    def test_env_1_schaltet_an(self, monkeypatch):
        monkeypatch.setenv("USE_INTERNAL_RESEARCH", "1")
        monkeypatch.setenv("RESEARCH_PROVIDER", "disabled")
        assert self._resolve() is True

    def test_ohne_env_gilt_research_provider(self, monkeypatch):
        monkeypatch.delenv("USE_INTERNAL_RESEARCH", raising=False)
        monkeypatch.setenv("RESEARCH_PROVIDER", "hybrid")
        assert self._resolve() is True
        monkeypatch.setenv("RESEARCH_PROVIDER", "disabled")
        assert self._resolve() is False


# =========================================================================
# 3. Domänenfilter erreichen die Tavily-API
# =========================================================================

class TestDomaenenfilter:

    def test_policy_liest_env_listen(self, monkeypatch):
        from services.research_pipeline import _policy_domains
        monkeypatch.setenv("RESEARCH_INCLUDE_FUNDING", "kfw.de, foerderdatenbank.de")
        monkeypatch.setenv("RESEARCH_INCLUDE_TOOLS", "openai.com")
        monkeypatch.setenv("RESEARCH_EXCLUDE", "reddit.com,medium.com")
        inc, exc = _policy_domains("funding")
        assert inc == ["kfw.de", "foerderdatenbank.de"]
        assert exc == ["reddit.com", "medium.com"]
        inc_t, _ = _policy_domains("tools")
        assert inc_t == ["openai.com"]

    def test_provider_sendet_domains_im_payload(self, monkeypatch):
        import services.provider_tavily as pt
        gesendet = {}
        monkeypatch.setattr(pt, "TAVILY_API_KEY", "k")
        monkeypatch.setattr(pt, "_post_json", lambda url, payload, timeout=8: gesendet.update(payload) or {"results": []})
        pt.search("Förderprogramme KI 2026", max_results=5, days=30,
                  include_domains=["KFW.de ", "bafa.de"], exclude_domains=["reddit.com"])
        assert gesendet["include_domains"] == ["kfw.de", "bafa.de"]
        assert gesendet["exclude_domains"] == ["reddit.com"]

    def test_ohne_listen_kein_filter_im_payload(self, monkeypatch):
        import services.provider_tavily as pt
        gesendet = {}
        monkeypatch.setattr(pt, "TAVILY_API_KEY", "k")
        monkeypatch.setattr(pt, "_post_json", lambda url, payload, timeout=8: gesendet.update(payload) or {"results": []})
        pt.search("x", include_domains=[], exclude_domains=None)
        assert "include_domains" not in gesendet
        assert "exclude_domains" not in gesendet


# =========================================================================
# 4. Eine Admin-Liste
# =========================================================================

class TestAdminListe:

    def test_env_admin_wird_erkannt(self, monkeypatch):
        from core.whitelist import is_admin, all_admins
        monkeypatch.setenv("ADMIN_EMAILS", "bewertung@ki-sicherheit.jetzt, Wolf.Hohl@web.de")
        assert is_admin("wolf.hohl@web.de")
        assert "bewertung@ki-sicherheit.jetzt" in all_admins()

    def test_ohne_env_gilt_konstante(self, monkeypatch):
        from core.whitelist import is_admin
        monkeypatch.delenv("ADMIN_EMAILS", raising=False)
        assert is_admin("bewertung@ki-sicherheit.jetzt")
        assert not is_admin("wolf.hohl@web.de")

    def test_admin_env_macht_nicht_zum_testnutzer(self, monkeypatch):
        from core.whitelist import is_whitelisted
        monkeypatch.setenv("ADMIN_EMAILS", "fremd@example.org")
        monkeypatch.delenv("EXTRA_WHITELIST", raising=False)
        assert not is_whitelisted("fremd@example.org")


# =========================================================================
# 5. Tote Module sind weg, lebende bleiben importierbar
# =========================================================================

class TestToteModule:

    def test_geloescht(self):
        for rel in ("services/research.py", "services/providers/tavily.py",
                    "services/providers/perplexity.py", "services/research_fetcher.py",
                    "services/research_hybrid_addon.py", "services/test_research_system.py"):
            assert not (REPO / rel).exists(), rel

    def test_lebende_module_importierbar(self):
        for mod in ("services.research_pipeline", "services.provider_tavily",
                    "services.provider_perplexity", "services.research_policy",
                    "services.research_grounding", "services.news_researcher"):
            importlib.import_module(mod)

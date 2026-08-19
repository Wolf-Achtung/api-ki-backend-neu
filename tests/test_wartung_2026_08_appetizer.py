# -*- coding: utf-8 -*-
"""Wartungs-Durchgang 2026-08: Appetizer-Textextraktion.

call_claude_sonnet las message.content[0].text. Bei Modellen mit adaptivem
Denken (claude-sonnet-5, Prod-Default via ANTHROPIC_MODEL) ist der erste
Block oft ein thinking-Block ohne .text — der assert brach dann jede
Appetizer-Anfrage mit 500 ab, obwohl die Antwort vollständig war.
Jetzt sammelt _extract_message_text alle Text-Blöcke ein.
"""

import routes.appetizer as appetizer


class _ThinkingBlock:
    type = "thinking"
    thinking = ""


class _TextBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class _Msg:
    def __init__(self, blocks):
        self.content = blocks
        self.stop_reason = "end_turn"


class _FakeMessages:
    def __init__(self, message):
        self._message = message

    def create(self, **kwargs):
        return self._message


class _FakeAnthropic:
    def __init__(self, message):
        self.messages = _FakeMessages(message)


def _patch_client(monkeypatch, message):
    monkeypatch.setattr(appetizer.anthropic, "Anthropic", lambda: _FakeAnthropic(message))


class TestAppetizerTextExtraction:

    def test_thinking_block_first_still_returns_text(self, monkeypatch):
        msg = _Msg([_ThinkingBlock(), _TextBlock('{"score": 1}')])
        _patch_client(monkeypatch, msg)
        assert appetizer.call_claude_sonnet("sys", "user") == '{"score": 1}'

    def test_plain_text_response_unchanged(self, monkeypatch):
        msg = _Msg([_TextBlock('{"score": 2}')])
        _patch_client(monkeypatch, msg)
        assert appetizer.call_claude_sonnet("sys", "user") == '{"score": 2}'

    def test_no_text_blocks_raises_assertion(self, monkeypatch):
        # Kein Text → AssertionError → Route antwortet ehrlich mit 500
        msg = _Msg([_ThinkingBlock()])
        _patch_client(monkeypatch, msg)
        try:
            appetizer.call_claude_sonnet("sys", "user")
        except AssertionError:
            pass
        else:
            raise AssertionError("expected AssertionError for empty response")


class TestFirmaRemoved:
    """Sicherheits-Invariante: Der Firmenname wird nirgendwo erhoben.

    Der Appetizer war der letzte Pfad mit einem firma-Feld. Es ist
    entfernt; die DB-Spalte bekommt einen festen Platzhalter.
    """

    VALID = {
        "branche": "medien",
        "mitarbeiter": "2-10",
        "hauptleistung": "Postproduktion und VFX",
        "zeitaufwand_repetitiv": "25_50",
        "ki_erfahrung": "erste_versuche",
        "groesste_herausforderung": "Zeitmangel",
    }

    def test_request_model_has_no_firma_field(self):
        assert "firma" not in appetizer.AppetizerRequest.model_fields

    def test_legacy_payload_with_firma_is_ignored(self):
        req = appetizer.AppetizerRequest(**{**self.VALID, "firma": "Geheime GmbH"})
        assert not hasattr(req, "firma")
        assert "Geheime GmbH" not in req.model_dump_json()

    def test_prompt_builder_has_no_firma(self):
        import inspect
        from prompts.appetizer_prompts import APPETIZER_USER_PROMPT_TEMPLATE, build_user_prompt
        assert "firma" not in inspect.signature(build_user_prompt).parameters
        assert "FIRMA" not in APPETIZER_USER_PROMPT_TEMPLATE

    def test_admin_email_has_no_firma_row(self):
        from services.email_templates import _render_appetizer_admin_email
        html = _render_appetizer_admin_email(
            {**self.VALID, "email": "x@y.de", "newsletter_optin": False},
            {"score": {"wert": 42, "einordnung": "Solide"}},
        )
        assert "Firma" not in html

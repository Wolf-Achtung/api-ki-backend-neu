"""Hotfix 1027.2.2-B: Tests für die conditional ABSCHLUSS-Block-Injektion
im STRATEGY_CONVERSATION_PROMPT, gegated über is_last_section.

KIS-1194 zeigte, dass der LLM nach Abschluss der ersten Strategy-Sektion
(s1_budget … s7_entscheidung) den Satz "Danke! Ihr individueller
KI-Strategiebericht wird jetzt erstellt…" hallucinierte, obwohl der
Fragebogen noch Sektion 1 (Erfahrung & Marktposition) zu durchlaufen
hatte. Trigger war der ABSCHLUSS-Block im System-Prompt, der schlicht
auf `missing_in_section == "alle erfasst"` ansprach — und das ist für
Sektion 0 nach Turn 7 wahr, obwohl der Fragebogen noch nicht fertig ist.

Fix: zwei separate Block-Konstanten und ein `is_last_section`-Flag, das
vom Aufrufer (routes/chat.py) explizit über ALLE Sections iterativ
berechnet wird — nicht über die lokale `missing_in_section`-Variable.
"""
from __future__ import annotations


class TestAbschlussBlockPlaceholder:
    def test_strategy_prompt_has_abschluss_block_placeholder(self) -> None:
        from services.chat_conversation import STRATEGY_CONVERSATION_PROMPT
        assert "{abschluss_block}" in STRATEGY_CONVERSATION_PROMPT, (
            "Placeholder {abschluss_block} fehlt im STRATEGY_CONVERSATION_PROMPT"
        )

    def test_strategy_prompt_no_longer_hardcodes_abschluss(self) -> None:
        from services.chat_conversation import STRATEGY_CONVERSATION_PROMPT
        sentinel = "Soll ich Ihren Strategiebericht jetzt erstellen?"
        assert sentinel not in STRATEGY_CONVERSATION_PROMPT, (
            f"Sentinel '{sentinel}' findet sich noch hardcoded im "
            "STRATEGY_CONVERSATION_PROMPT — Conditional-Gate umgangen."
        )


class TestAbschlussBlockContents:
    def test_last_section_block_contains_abschluss_wording(self) -> None:
        from services.chat_conversation import STRATEGY_ABSCHLUSS_BLOCK_LAST_SECTION
        assert "Soll ich Ihren Strategiebericht jetzt erstellen?" in STRATEGY_ABSCHLUSS_BLOCK_LAST_SECTION

    def test_interim_section_block_forbids_abschluss_wording(self) -> None:
        from services.chat_conversation import STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION
        body = STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION
        assert "VERBOTEN" in body
        assert "wird jetzt erstellt" in body
        assert "Strategiebericht wird jetzt erstellt" in body
        assert "Soll ich Ihren Strategiebericht jetzt erstellen?" in body

    def test_interim_section_block_offers_transition_template(self) -> None:
        from services.chat_conversation import STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION
        body = STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION
        assert "Übergangssatz" in body

    def test_both_blocks_carry_summary_confirmation_rule(self) -> None:
        from services.chat_conversation import (
            STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION,
            STRATEGY_ABSCHLUSS_BLOCK_LAST_SECTION,
        )
        for block_name, block in [
            ("LAST_SECTION", STRATEGY_ABSCHLUSS_BLOCK_LAST_SECTION),
            ("INTERIM_SECTION", STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION),
        ]:
            assert "ZUSAMMENFASSUNG BESTÄTIGT" in block, block_name
            assert "SOFORT zum nächsten Feld" in block, block_name


class TestAbschlussBlockSelection:
    """Funktionaler Test: format() mit dem richtigen Block je nach
    is_last_section-Flag — analog zur Logik in chat_conversation.py."""

    def _render(self, is_last_section: bool) -> str:
        from services.chat_conversation import (
            STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION,
            STRATEGY_ABSCHLUSS_BLOCK_LAST_SECTION,
            STRATEGY_CONVERSATION_PROMPT,
        )
        block = (
            STRATEGY_ABSCHLUSS_BLOCK_LAST_SECTION
            if is_last_section
            else STRATEGY_ABSCHLUSS_BLOCK_INTERIM_SECTION
        )
        return STRATEGY_CONVERSATION_PROMPT.format(
            section_name="Umsetzungsplanung",
            section_number=1,
            total_sections=2,
            collected_fields_summary="Branche: Beratung",
            missing_in_section="alle erfasst",
            next_fields_with_descriptions="s8_erfahrung — KI-Erfahrung",
            abschluss_block=block,
        )

    def test_interim_section_omits_kis_1194_phrase_as_instruction(self) -> None:
        """is_last_section=False: ABSCHLUSS-Cue darf NICHT als positive
        Anweisung im Prompt stehen."""
        prompt = self._render(is_last_section=False)
        assert "VERBOTEN" in prompt
        assert "Fragen Sie: \"Soll ich Ihren Strategiebericht" not in prompt, (
            "Interim-Section darf den ABSCHLUSS-Cue NICHT als Anweisung bekommen"
        )

    def test_last_section_keeps_kis_1194_phrase_as_instruction(self) -> None:
        """is_last_section=True: ABSCHLUSS-Frage IST die Anweisung."""
        prompt = self._render(is_last_section=True)
        assert "Fragen Sie: \"Soll ich Ihren Strategiebericht" in prompt, (
            "Letzte Sektion muss die ABSCHLUSS-Frage als Anweisung tragen"
        )


class TestGenerateResponseSignature:
    """Smoke-Test, dass generate_response den is_last_section-Parameter
    akzeptiert. Verifiziert die API-Brücke routes/chat.py <-> chat_conversation."""

    def test_generate_response_has_is_last_section_param(self) -> None:
        import inspect
        from services.chat_conversation import generate_response
        sig = inspect.signature(generate_response)
        assert "is_last_section" in sig.parameters, (
            "generate_response muss is_last_section akzeptieren — sonst kommt "
            "der Flag aus routes/chat.py nirgends an."
        )
        param = sig.parameters["is_last_section"]
        assert param.default is False, (
            "Default muss False sein — Interim-Block ist der sichere Default, "
            "damit nicht versehentlich ein neuer Aufrufer den ABSCHLUSS-Block "
            "ohne explizites Setzen bekommt."
        )


class TestRoutesChatIsLastSectionComputation:
    """Source-level Guard für die is_last_section-Berechnung in routes/chat.py.
    Wolf-Anweisung 1027.2.2: explizit über alle Sections iterieren, NICHT
    über die lokale missing_in_section-Variable — das war genau der
    KIS-1194-Bug-Trigger."""

    def _read_chat_routes(self) -> str:
        import os
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "routes",
            "chat.py",
        )
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_is_last_section_complete_var_present(self) -> None:
        src = self._read_chat_routes()
        assert "_is_last_section_complete" in src, (
            "routes/chat.py muss _is_last_section_complete berechnen und an "
            "generate_response durchreichen."
        )

    def test_global_completion_uses_iteration(self) -> None:
        """Die Berechnung MUSS über range(len(sections)) iterieren und für
        jede _si get_missing_fields aufrufen. Negativ-Test: missing_in_section
        darf NICHT als alleiniger Trigger genutzt werden."""
        src = self._read_chat_routes()
        # Iteration über alle Sections
        assert "for _si in range(len(sections))" in src, (
            "is_last_section muss über alle Sections iterieren, nicht über "
            "die lokale missing_in_section-Variable."
        )
        # Per-Section-Check via get_missing_fields
        assert "get_missing_fields(collected, _si, rt)" in src, (
            "Pro Section get_missing_fields aufrufen, damit required+optional "
            "Felder zusammen geprüft werden."
        )

    def test_passed_to_generate_response(self) -> None:
        src = self._read_chat_routes()
        assert "is_last_section=_is_last_section_complete" in src, (
            "Der berechnete Flag muss als is_last_section= an generate_response "
            "übergeben werden."
        )

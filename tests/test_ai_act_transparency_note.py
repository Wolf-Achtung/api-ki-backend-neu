# -*- coding: utf-8 -*-
"""
Guards the AI Act duty-matrix note for minimal/none risk.

Previously the note claimed the measures were "keine gesetzlichen Pflichten"
(no legal obligations) — misleading given the Art. 50 transparency obligations
that apply from 2 August 2026. The note must reference Art. 50 and that date.
"""
import pytest

from services.ai_act_module import _generate_duty_matrix_de, _generate_duty_matrix_en


@pytest.mark.parametrize("risk", ["none", "minimal"])
def test_de_note_mentions_art50_and_date(risk):
    html = _generate_duty_matrix_de(risk, branche="beratung", is_solo=True)
    assert "Art. 50" in html
    assert "2. August 2026" in html
    # The old absolute wording must be gone.
    assert "keine gesetzlichen Pflichten" not in html


@pytest.mark.parametrize("risk", ["none", "minimal"])
def test_en_note_mentions_art50_and_date(risk):
    html = _generate_duty_matrix_en(risk, branche="consulting", is_solo=True)
    assert "Art. 50" in html
    assert "2 August 2026" in html
    assert "not legal obligations" not in html


def test_high_risk_note_unchanged():
    html = _generate_duty_matrix_de("high-risk", branche="beratung", is_solo=True)
    assert "gesetzlich vorgeschrieben" in html

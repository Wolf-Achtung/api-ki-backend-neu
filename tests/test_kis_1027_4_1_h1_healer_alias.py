# -*- coding: utf-8 -*-
"""FIX-KIS-1027.4.1-H1: reduce_redundancy must not flag uppercase/lowercase
alias pairs as cross-section duplicates.

KIS-1198 zeigte post-Healer-Asymmetrie:
  GAMECHANGER_DECISION_HTML: 2333 -> 1899 chars (-19 %)
  gamechanger_decision:      2334 ->  772 chars (-67 %)

Ursache: FIX-C (reduce_redundancy) iteriert Insert-Order. Uppercase wird
zuerst gesehen, registriert alle Block-Fingerprints. Lowercase kommt
danach und ALLE seine Blöcke werden als "Cross-Section-Duplikat" des
uppercase-Alias geflaggt -> Lowercase wird auf Blöcke <160 chars
reduziert.

Fix: alias-aware Cross-Section-Dedup. Beide Aliase werden als dieselbe
logische Section behandelt.
"""
from __future__ import annotations

from services.report_healer import reduce_redundancy


def _make_dual_keyed_sections(html: str) -> dict:
    """Build a sections dict where the uppercase decision key is followed
    by its lowercase alias holding identical content (the post-2F state)."""
    return {
        "GAMECHANGER_DECISION_HTML": html,
        "gamechanger_decision": html,
        # an unrelated section in between to verify normal dedup still works
        "OTHER_SECTION": "<p>Ein völlig anderer Absatz mit ganz anderem Inhalt für die Plausibilität dieses Tests.</p>",
    }


# A realistic decision-section payload: 4 substantial <li> bullets >160 chars each
DECISION_HTML = (
    "<ul>"
    "<li><strong>Tun:</strong> Einen verbindlichen Standard-Arbeitsablauf einführen, "
    "bei dem jede Beratungsleistung den Ablauf Input-Analyse-Auswertung-Bericht "
    "in dieser Reihenfolge durchläuft und an jedem Schritt explizit dokumentiert wird.</li>"
    "<li><strong>Lassen:</strong> Ad-hoc-Recherchen ohne dokumentierte Quellen vermeiden, "
    "weil sie weder reproduzierbar sind noch in den TÜV-Audit-Pfad passen. Stattdessen "
    "kuratierte Recherche-Pipelines mit Quellen-Logging einsetzen.</li>"
    "<li><strong>Prüfen:</strong> Innerhalb von zwei Wochen ein Vier-Augen-Prinzip für "
    "alle ausgehenden Beratungsberichte etablieren — entweder durch interne Reviewer "
    "oder durch ein externes Peer-Netzwerk mit ähnlichem TÜV-Standard.</li>"
    "<li><strong>Stop:</strong> Keine neuen KI-Tools mehr einführen, bevor das bestehende "
    "Tool-Portfolio in der DSGVO-Tabelle dokumentiert und der Audit-Pfad geschlossen ist. "
    "Sonst entsteht Schatten-IT, die der Zertifizierung im Wege steht.</li>"
    "</ul>"
)


def test_alias_pair_not_cross_section_deduped():
    """Both keys must retain (near-)identical length after FIX-C."""
    sections = _make_dual_keyed_sections(DECISION_HTML)
    result, stats = reduce_redundancy(sections)

    upper_len = len(result["GAMECHANGER_DECISION_HTML"])
    lower_len = len(result["gamechanger_decision"])

    # Tolerance: minor whitespace/cleanup differences allowed,
    # but length must be within 5% of each other.
    assert upper_len > 0
    assert lower_len > 0
    diff_ratio = abs(upper_len - lower_len) / max(upper_len, lower_len)
    assert diff_ratio < 0.05, (
        f"Alias drift: upper={upper_len} lower={lower_len} diff={diff_ratio:.1%} "
        f"(expected <5%)"
    )


def test_alias_pair_keeps_most_content():
    """Alias pair must keep most of its content (no aggressive dedup)."""
    sections = _make_dual_keyed_sections(DECISION_HTML)
    result, _ = reduce_redundancy(sections)

    original_len = len(DECISION_HTML)
    upper_len = len(result["GAMECHANGER_DECISION_HTML"])
    lower_len = len(result["gamechanger_decision"])

    # Both should keep at least 90% of original content.
    assert upper_len / original_len >= 0.9, f"upper kept only {upper_len}/{original_len}"
    assert lower_len / original_len >= 0.9, f"lower kept only {lower_len}/{original_len}"


def test_cross_section_dedup_still_works_for_non_aliases():
    """Sanity: alias-awareness must not break normal cross-section dedup."""
    duplicate_para = (
        "<p>Dies ist ein langer, redundanter Absatz, der in zwei verschiedenen "
        "Sektionen exakt gleich auftaucht und durch FIX-C beim zweiten "
        "Vorkommen entfernt werden soll, weil er die Berichtsstruktur "
        "verunklart und keinen zusätzlichen Mehrwert bietet.</p>"
    )
    sections = {
        "SECTION_A_HTML": duplicate_para,
        # NOT an alias of SECTION_A_HTML — independent section
        "SECTION_B_HTML": duplicate_para + "<p>Plus ein zusätzlicher Absatz.</p>",
    }
    result, stats = reduce_redundancy(sections)
    # Section B should have lost the duplicate paragraph
    assert "verunklart" not in result["SECTION_B_HTML"], (
        "Non-alias cross-section duplicate should still be removed"
    )
    # Section A keeps it
    assert "verunklart" in result["SECTION_A_HTML"]

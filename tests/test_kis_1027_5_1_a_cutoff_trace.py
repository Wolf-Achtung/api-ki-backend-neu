# -*- coding: utf-8 -*-
"""FIX-KIS-1027.5.1-A: Decision-Cutoff-Trace-Instrumentierung.

KIS-1200 zeigte 675-char / 3-li post_healer-Inhalt in DB, gerendertes PDF
zeigt nur 1 mid-sentence-abgeschnittenen Bullet (~162 chars / 1 li). 3
CSS-basierte Iterationen (1027.2.3, 1027.4, 1027.5) haben den Bug nicht
behoben. Diese Tests verifizieren NUR die Instrumentierung — kein Fix.

Sieben Checkpoints im Pipeline-Fluss DB-Read -> render() -> pdf_client:
  0_db_read_admin_re_render  (routes/strategy.py admin-re-render)
  1_render_entry             (report_renderer.render Eintritt)
  2_pre_jinja                (vor env.get_template().render())
  3_post_jinja               (direkt nach Jinja-Render)
  4_pre_pagebreak_cleanup    (vor cleanup_pagebreaks)
  5_post_pagebreak_cleanup   (nach cleanup_pagebreaks)
  6_render_exit              (vor render-Return)
  7_pdf_client_http_send     (pdf_client HTTP-Boundary zu make-ki-pdfservice)

Logging-Marker: [DECISION-CUTOFF-TRACE] stage=X run_id=Y len=N li=M sha=Z mode=...
"""
from __future__ import annotations

import logging
import re

import pytest

from services.report_renderer import _trace_decision_cutoff


_DECISION_HTML_3_LI = (
    '<div class="exec-decision-box">'
    '  <p><strong>Ihre Entscheidung in 3 Punkten</strong></p>'
    '  <ul>'
    '    <li><strong>Tun:</strong> Standard-Workflow Input → KI-Entwurf → Review → Freigabe einführen.</li>'
    '    <li><strong>Lassen:</strong> Ad-hoc-Prompts ohne dokumentierte Quellen vermeiden.</li>'
    '    <li><strong>Risiko &amp; Stop-Signal:</strong> Nach 14 Tagen ohne messbaren Effekt stoppen.</li>'
    '  </ul>'
    '</div>'
)


_FULL_HTML_WITH_DECISION = f'''
<html><body>
<div class="section" id="other" data-category="strategy">
<p>Andere Section</p>
</div>
<div class="section" id="decision" data-category="strategy">
    <h2>Entscheidungsvorlage</h2>
    {_DECISION_HTML_3_LI}
</div>
<!-- ═══════ NACH DECISION ═══════ -->
<div class="section" id="footer-section" data-category="strategy">
<p>Footer-Section</p>
</div>
</body></html>
'''


def test_trace_logs_section_mode(caplog):
    """Mode='section' loggt direkt das uebergebene HTML-Fragment."""
    with caplog.at_level(logging.INFO, logger="services.report_renderer"):
        _trace_decision_cutoff("test_stage", "RUN-1", _DECISION_HTML_3_LI, mode="section")
    matches = [r for r in caplog.records if "[DECISION-CUTOFF-TRACE]" in r.getMessage()]
    assert len(matches) == 1, f"Erwartete 1 TRACE-Eintrag, gefunden {len(matches)}"
    msg = matches[0].getMessage()
    assert "stage=test_stage" in msg
    assert "run_id=RUN-1" in msg
    assert "li=3" in msg, f"3 <li> erwartet, message={msg!r}"
    assert "len=" in msg
    assert "sha=" in msg


def test_trace_logs_html_mode_extracts_decision_section(caplog):
    """Mode='html' extrahiert nur den #decision-Section-Block aus Full-HTML."""
    with caplog.at_level(logging.INFO, logger="services.report_renderer"):
        _trace_decision_cutoff("test_html", "RUN-2", _FULL_HTML_WITH_DECISION, mode="html")
    matches = [r for r in caplog.records if "[DECISION-CUTOFF-TRACE]" in r.getMessage()]
    assert len(matches) == 1
    msg = matches[0].getMessage()
    assert "li=3" in msg, f"3 <li> aus #decision erwartet, message={msg!r}"
    # Andere Sections (footer/other) duerfen die <li>-Zahl NICHT beeinflussen
    # (sie haben keine <li>); Length muss < Full-HTML-Length sein
    full_len = len(_FULL_HTML_WITH_DECISION)
    match = re.search(r'len=(\d+)', msg)
    assert match
    extracted_len = int(match.group(1))
    assert extracted_len < full_len, (
        f"Extracted len={extracted_len} sollte < full {full_len} sein"
    )


def test_trace_handles_empty_content(caplog):
    """Empty/None Content loggt NOT-FOUND statt zu crashen."""
    with caplog.at_level(logging.INFO, logger="services.report_renderer"):
        _trace_decision_cutoff("test_empty", "RUN-3", None, mode="section")
        _trace_decision_cutoff("test_empty_str", "RUN-3", "", mode="html")
    matches = [r for r in caplog.records if "[DECISION-CUTOFF-TRACE]" in r.getMessage()]
    assert len(matches) == 2
    assert all("NOT-FOUND" in m.getMessage() for m in matches)


def test_trace_handles_html_without_decision_section(caplog):
    """HTML ohne #decision-Section loggt NOT-FOUND, kein Crash."""
    html_no_decision = '<html><body><div class="section" id="other">Nichts</div></body></html>'
    with caplog.at_level(logging.INFO, logger="services.report_renderer"):
        _trace_decision_cutoff("test_no_dec", "RUN-4", html_no_decision, mode="html")
    matches = [r for r in caplog.records if "[DECISION-CUTOFF-TRACE]" in r.getMessage()]
    assert len(matches) == 1
    assert "NOT-FOUND" in matches[0].getMessage()


def test_trace_never_raises_on_internal_error(caplog):
    """Trace-Helper soll Render-Pipeline NIE brechen — auch bei kaputten Inputs."""
    class _Unencodable:
        def __str__(self):
            raise RuntimeError("intentional")

    # darf NICHT propagieren
    with caplog.at_level(logging.WARNING, logger="services.report_renderer"):
        _trace_decision_cutoff("test_robust", "RUN-5", _Unencodable(), mode="section")
    # Erwartung: entweder NOT-FOUND-Log ODER TRACE-ERROR-Warning, aber kein crash
    # (caplog captures both INFO und WARNING above)


def test_renderer_has_all_six_in_module_checkpoints():
    """Verifiziere, dass alle 6 Checkpoints (1..6) im report_renderer-Quellcode stehen."""
    import inspect
    from services import report_renderer
    src = inspect.getsource(report_renderer)
    for marker in (
        '"1_render_entry"',
        '"2_pre_jinja"',
        '"3_post_jinja"',
        '"4_pre_pagebreak_cleanup"',
        '"5_post_pagebreak_cleanup"',
        '"6_render_exit"',
    ):
        assert marker in src, f"Checkpoint {marker} fehlt im report_renderer"


def test_pdf_client_has_http_send_checkpoint():
    """Checkpoint 7 (pdf_client HTTP-Boundary) ist im pdf_client-Quellcode."""
    import inspect
    from services import pdf_client
    src = inspect.getsource(pdf_client)
    assert "7_pdf_client_http_send" in src, (
        "pdf_client Checkpoint 7 fehlt"
    )
    assert "DECISION-CUTOFF-TRACE" in src


def test_strategy_routes_has_db_read_checkpoint():
    """Checkpoint 0 (admin r1-re-render DB-Read) ist im routes/strategy.py."""
    import inspect
    from routes import strategy as strategy_routes
    src = inspect.getsource(strategy_routes)
    assert "0_db_read_admin_re_render" in src, (
        "routes/strategy.py Checkpoint 0 fehlt"
    )

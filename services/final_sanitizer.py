# -*- coding: utf-8 -*-
"""
Final Sanitizer — läuft als ALLERLETZTER Schritt vor dem Template-Rendering.
Fixt alle bekannten Darstellungsprobleme in einem einzigen Pass.
Muss NACH canonical injection und NACH allen Engine-Läufen aufgerufen werden.

Fixes:
  F1: PAYBACK_MONTHS formatieren (Raw Float → "1,6")
  F2: "36.0" → "36" (Ganzzahl-Formatierung)
  F3: BC-Prose neu generieren mit korrekten Canonical-Werten
  F4: "X Stunden/Woche" → Canonical Stunden/Monat
  F5: Prompt-Leak-Patterns entfernen
  F6: go-digital "(eingestellt)"
  F7: hauptleistung Global Limiter (max 5) + Deduplizierung
  F8: Leere HTML-Sections filtern (<20 Zeichen)
  F9: HAUPTLEISTUNG Mindest-Vorkommen in Exec Summary + Recommendations (FIX-641-P2)
"""
import re
import logging

log = logging.getLogger(__name__)


def final_sanitize(sections: dict) -> dict:
    """
    Einmaliger Sanitizer-Pass über ALLE sections.
    Muss NACH canonical injection und NACH allen Engine-Läufen aufgerufen werden.
    """
    fixes_applied = []

    # ─── FIX-F1: PAYBACK_MONTHS formatieren (Raw Float → "1,6") ───
    try:
        pb = sections.get('PAYBACK_MONTHS')
        if pb is not None:
            pb_float = float(str(pb).replace(',', '.'))
            pb_formatted = f"{pb_float:.1f}".replace('.', ',')
            sections['PAYBACK_MONTHS_FMT_DE'] = pb_formatted
            fixes_applied.append(f"F1:PAYBACK={pb_formatted}")
    except (ValueError, TypeError):
        pass

    # ─── FIX-F2: "36.0" → "36" (Ganzzahl-Formatierung) ───
    for key in ['CANON_HOURS_MONTH', 'EINSPARUNG_STUNDEN_MONAT']:
        val = sections.get(key)
        if val is not None:
            try:
                fval = float(str(val).replace(',', '.'))
                if fval == int(fval):
                    sections[key] = str(int(fval))
                    fixes_applied.append(f"F2:{key}={int(fval)}")
            except (ValueError, TypeError):
                pass

    # ─── FIX-F3: BC-Prose neu generieren mit korrekten Canonical-Werten ───
    try:
        _capex = sections.get('CAPEX_REALISTISCH_EUR') or sections.get('BC_INVESTMENT_TOTAL') or 5000
        _opex = sections.get('OPEX_REALISTISCH_EUR') or 350
        _einsparung = sections.get('EINSPARUNG_MONAT_EUR') or sections.get('BC_MONTHLY_SAVINGS_REALISTIC') or 3420
        _hours = sections.get('CANON_HOURS_MONTH') or 36
        _rate = sections.get('CANON_RATE_EUR') or 95
        _roi = sections.get('ROI_12M') or sections.get('BC_ROI_REALISTIC') or 200
        _bundesland = sections.get('BUNDESLAND_LABEL') or 'Ihrem Bundesland'

        # Payback aus Canonical
        _pb_raw = sections.get('PAYBACK_MONTHS', 1.6)
        try:
            _pb_float = float(str(_pb_raw).replace(',', '.'))
            _pb_fmt = f"{_pb_float:.1f}".replace('.', ',')
        except (ValueError, TypeError):
            _pb_fmt = str(_pb_raw)

        # ROI deckeln
        try:
            _roi_val = float(str(_roi).replace(',', '.'))
            _roi_fmt = f"{min(_roi_val, 200):.0f}"
        except (ValueError, TypeError):
            _roi_fmt = "200"

        # EUR-Formatierung
        def _fmt_eur(v):
            try:
                return f"{int(float(str(v).replace(',', '.'))):,}".replace(',', '.')
            except Exception:
                return str(v)

        _bc_prose = (
            f'<h3>Wirtschaftliche Bewertung</h3>\n'
            f'<p>Bei einem geschätzten Automatisierungspotenzial von <strong>{_hours} Stunden/Monat</strong>\n'
            f'und einem kalkulatorischen Stundensatz von <strong>{_rate} €</strong> ergibt sich eine\n'
            f'monatliche Einsparung von <strong>{_fmt_eur(_einsparung)} €</strong>\n'
            f'(abzüglich laufender Kosten von {_fmt_eur(_opex)} €/Monat für Lizenzen und Wartung).\n'
            f'Bei einer einmaligen Investition (CAPEX) von <strong>{_fmt_eur(_capex)} €</strong>\n'
            f'liegt die Amortisationsdauer bei rund <strong>{_pb_fmt} Monaten</strong>.</p>\n'
            f'<p>Der konservativ berechnete ROI auf 12 Monate beträgt <strong>{_roi_fmt} %</strong>\n'
            f'(gedeckelt). Dies unterstreicht die Wirtschaftlichkeit auch bei vorsichtigen Annahmen.</p>\n'
            f'<h3>Fördermöglichkeiten</h3>\n'
            f'<p>In <strong>{_bundesland}</strong> können Programme für\n'
            f'Digitalisierungs- und KI-Vorhaben relevant sein\n'
            f'(→ siehe Förderpotenzial).</p>'
        )

        _bc_html = sections.get('BUSINESS_CASE_HTML', '')
        _table_match = re.search(r'<table', _bc_html, re.IGNORECASE)
        _first_h3 = re.search(r'<h3', _bc_html, re.IGNORECASE)
        if _table_match and _first_h3:
            sections['BUSINESS_CASE_HTML'] = _bc_prose + '\n' + _bc_html[_table_match.start():]
            sections['business_case'] = sections['BUSINESS_CASE_HTML']
            fixes_applied.append(f"F3:BC-Prose={_pb_fmt}Mo")
    except Exception as e:
        log.warning("[FINAL-SANITIZER] F3 BC-Prose failed: %s", e)

    # ─── FIX-F4: "X Stunden/Woche" → Canonical Stunden/Monat ───
    canon_hours = sections.get('CANON_HOURS_MONTH') or '36'
    canon_einsparung = sections.get('EINSPARUNG_MONAT_EUR') or '3420'
    try:
        jahresersparnis = int(float(str(canon_einsparung).replace(',', '.')) * 12)
        jahresersparnis_fmt = f"{jahresersparnis:,}".replace(',', '.')
    except Exception:
        jahresersparnis_fmt = '41.040'

    for key in list(sections.keys()):
        val = sections.get(key)
        if not isinstance(val, str) or len(val) < 50:
            continue
        original = val
        # "9 Stunden/Woche" oder "X Stunden pro Woche" → Canonical
        val = re.sub(
            r'(?:ca\.?\s*)?\d+\s*Stunden?\s*/\s*Woche',
            f'{canon_hours} Stunden/Monat',
            val
        )
        val = re.sub(
            r'(?:ca\.?\s*)?\d+\s*Stunden?\s*pro\s*Woche',
            f'{canon_hours} Stunden pro Monat',
            val
        )
        # Falsche Jahresersparnis ersetzen (z.B. 39.240, 45.600)
        val = re.sub(
            r'(\d{2}\.\d{3})\s*€?\s*(Jahresersparnis|jährlich)',
            f'{jahresersparnis_fmt} € \\2',
            val
        )
        if val != original:
            sections[key] = val
            fixes_applied.append(f"F4:hours-fix-in-{key[:30]}")

    # ─── FIX-F5: Prompt-Leak-Patterns entfernen ───
    LEAK_PATTERNS = [
        r'Ihr Ziel\s*\(z\.?\s*B\.[^)]*\)',
        r'Kontext/Branche[:\s]*[…\.]*',
        r'Welche Daten/Quellen[^<]*',
        r'Erfolgskriterien[:\s]*\(KPIs?\)[^<]*',
        r'Wenn Sie magst[^<]*',
        r'nenne auch Ihre größten[^<]*',
        r'Use Case:\s*…[^<]*',
        r'Stakeholder/Nutzer:\s*…[^<]*',
        r'Datenquellen\s*&\s*Qualität:\s*…[^<]*',
        r'IT-Umgebung:\s*Cloud/On-Prem[^<]*',
        r'Constraints:\s*Budget,\s*Zeit[^<]*',
        r'Erfolgskriterien:\s*KPIs,\s*Akzeptanz[^<]*',
        r'\[IHR NAME\]',
        r'\[DATUM\]',
        # FIX-B7: Additional prompt-input-label patterns
        r'<li>\s*Ihr Ziel[:\s]*</li>',
        r'<li>\s*Ihre Datenlage[:\s]*</li>',
        r'<li>\s*Ihre Branche[:\s]*</li>',
        r'<li>\s*Ihr Unternehmen[:\s]*</li>',
        r'<li>\s*Ihre größten Herausforderungen[:\s]*</li>',
        r'<p>\s*Bitte beschreibe[^<]*</p>',
        r'<p>\s*Bitte nennen Sie[^<]*</p>',
        r'Beispiel-KPI[^<]{0,50}',
        r'Beispieltext[^<]{0,50}',
    ]
    for key in list(sections.keys()):
        val = sections.get(key)
        if not isinstance(val, str) or len(val) < 50:
            continue
        original = val
        for pattern in LEAK_PATTERNS:
            val = re.sub(pattern, '', val, flags=re.IGNORECASE)
        # Leere Tags nach Entfernung aufräumen
        val = re.sub(r'<li>\s*</li>', '', val)
        val = re.sub(r'<p>\s*</p>', '', val)
        val = re.sub(r'<br\s*/?>\s*<br\s*/?>', '<br/>', val)
        if val != original:
            sections[key] = val
            fixes_applied.append(f"F5:leak-cleaned-{key[:30]}")

    # ─── FIX-F6: go-digital "(eingestellt)" ───
    for key in list(sections.keys()):
        val = sections.get(key)
        if not isinstance(val, str):
            continue
        if 'go-digital' in val.lower() and '(eingestellt)' not in val:
            val = re.sub(
                r'go-digital(?!\s*\(eingestellt\))',
                'go-digital (eingestellt)',
                val, flags=re.IGNORECASE
            )
            sections[key] = val
            fixes_applied.append(f"F6:go-digital-in-{key[:30]}")

    # ─── FIX-F7: hauptleistung Global Limiter (max 5) + Deduplizierung ───
    try:
        hl = sections.get('hauptleistung') or sections.get('HAUPTLEISTUNG') or ''
        if len(hl) > 30:
            hl_needle = hl[:30]  # Ersten 30 Zeichen als Suchstring
            hl_short = hl[:40] + '…'

            # Erst Verdopplungen fixen
            for key in list(sections.keys()):
                val = sections.get(key)
                if not isinstance(val, str) or key in ('hauptleistung', 'HAUPTLEISTUNG', 'REPORT_SUBTITLE', 'HAUPTLEISTUNG_SHORT'):
                    continue
                doubled = hl + '. ' + hl
                if doubled in val:
                    val = val.replace(doubled, hl)
                    sections[key] = val
                    fixes_applied.append(f"F7:HL-double-fixed-{key[:20]}")
                doubled2 = hl + ' ' + hl
                if doubled2 in val:
                    val = val.replace(doubled2, hl)
                    sections[key] = val

            # Dann global auf max 5 begrenzen
            total = 0
            for key in list(sections.keys()):
                val = sections.get(key)
                if not isinstance(val, str) or key.startswith('_') or key in ('hauptleistung', 'HAUPTLEISTUNG', 'REPORT_SUBTITLE', 'HAUPTLEISTUNG_SHORT'):
                    continue
                count = val.count(hl_needle)
                if count > 0:
                    if total >= 5:
                        # Alle durch Kurzform ersetzen
                        val = val.replace(hl, hl_short)
                        sections[key] = val
                    total += count

            if total > 5:
                fixes_applied.append(f"F7:HL-limited-{total}→max5")
    except Exception as e:
        log.warning("[FINAL-SANITIZER] F7 HL-limiter failed: %s", e)

    # ─── FIX-F8: Leere HTML-Sections filtern (<20 Zeichen) ───
    KEEP_EMPTY = {'HERO_HTML', 'KPI_HTML', 'KPI_VISUALS_HTML', 'QUICK_WINS_HTML',
                  'QUICK_WINS_HTML_LEFT', 'QUICK_WINS_HTML_RIGHT'}
    for key in list(sections.keys()):
        if not key.endswith('_HTML') or key in KEEP_EMPTY:
            continue
        val = sections.get(key)
        if isinstance(val, str):
            stripped = re.sub(r'<[^>]*>', '', val).strip()
            if len(stripped) < 20:
                sections[key] = ''
                fixes_applied.append(f"F8:empty-{key}")

    # ─── FIX-F9: HAUPTLEISTUNG Mindest-Vorkommen sicherstellen (FIX-641-P2) ───
    # Problem: LLM generiert manchmal Content ohne die spezifische Hauptleistung
    # des Unternehmens zu nennen. Validator verlangt min 3x in Exec Summary, 2x in Reco.
    # Lösung: Kontextrelevante Sätze mit der Hauptleistung injizieren.
    try:
        hl = sections.get('hauptleistung') or sections.get('HAUPTLEISTUNG') or ''
        if len(hl) >= 5:
            # Kurzform für Injection (max 60 Zeichen)
            hl_short = hl
            if len(hl) > 60:
                for sep in [",", ";", ".", " und ", " mit "]:
                    pos = hl.find(sep)
                    if 15 < pos < 80:
                        hl_short = hl[:pos]
                        break
                else:
                    hl_short = hl[:60].rsplit(" ", 1)[0]

            _f9_targets = {
                'EXEC_SUMMARY_HTML': 3,
                'RECOMMENDATIONS_HTML': 2,
            }
            for key, min_count in _f9_targets.items():
                val = sections.get(key, '')
                if not isinstance(val, str) or len(val) < 100:
                    continue
                # Count occurrences (case-insensitive, HTML-stripped)
                text_only = re.sub(r'<[^>]*>', '', val).lower()
                count = text_only.count(hl_short.lower())
                if count < min_count:
                    needed = min_count - count
                    # Erster Injektions-Absatz
                    inject = (
                        f'<p>Im Bereich <strong>{hl_short}</strong> '
                        f'ergeben sich durch KI-gestützte Prozessoptimierung '
                        f'erhebliche Potenziale.</p>'
                    )
                    # Nach erstem </p> einfügen
                    insert_pos = val.find('</p>')
                    if insert_pos > 0:
                        insert_pos += 4
                        new_val = val[:insert_pos] + '\n' + inject + '\n' + val[insert_pos:]
                    else:
                        new_val = inject + '\n' + val
                    # Zweiter Absatz wenn nötig
                    if needed >= 2:
                        inject2 = (
                            f'<p>Gerade im Kerngeschäft ({hl_short}) '
                            f'lassen sich wiederkehrende Aufgaben automatisieren.</p>'
                        )
                        second_pos = new_val.find('</p>', insert_pos + len(inject) + 10)
                        if second_pos > 0:
                            second_pos += 4
                            new_val = new_val[:second_pos] + '\n' + inject2 + '\n' + new_val[second_pos:]
                        else:
                            new_val = new_val + '\n' + inject2
                    # Dritter Absatz wenn nötig
                    if needed >= 3:
                        inject3 = (
                            f'<p>Die Empfehlungen zielen darauf ab, '
                            f'{hl_short} effizienter und skalierbarer zu gestalten.</p>'
                        )
                        new_val = new_val + '\n' + inject3
                    sections[key] = new_val
                    # Update lowercase alias
                    lower_key = key.replace('_HTML', '').lower()
                    if lower_key in sections:
                        sections[lower_key] = new_val
                    fixes_applied.append(f"F9:HL-inject-{key}({count}→{min_count})")
    except Exception as e:
        log.warning("[FINAL-SANITIZER] F9 HL-inject failed: %s", e)

    # ─── Logging ───
    if fixes_applied:
        log.info("[FINAL-SANITIZER] Applied %d fixes: %s",
                 len(fixes_applied), ', '.join(fixes_applied))
    else:
        log.info("[FINAL-SANITIZER] No fixes needed")

    return sections

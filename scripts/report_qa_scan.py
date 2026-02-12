#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report QA Scan (HTML/PDF) — CI-friendly post-render scanner.

Scans rendered report artifacts (HTML and/or PDF) for common blockers
that may have survived the pipeline healing/validation steps.

Checks:
- Empty currency/percentage artifacts ('€.', 'bei %')
- Leakage phrases (prompt echoes, template phrases)
- Du-forms (informal address in formal reports)
- Placeholders (TODO, Lorem ipsum, unrendered {{...}})
- Truncation artifacts (ellipsis 'daue…', 'Le…', incomplete sentences)
- Un-localized English BC labels ('Payback Progress', 'Time Savings')
- Excessive n.v. values (indicates BC calculation failure)
- Segment-specific rules:
  - Solo: no Governance/Enterprise terms
  - Team: no Solo-specific terms, Team-adequate complexity
  - KMU: no Solo terms, KMU-adequate governance depth

Exit codes:
- 0: no violations (or warnings-only when --fail-on=error)
- 2: violations found (CI should fail)
- 1: runtime error

Usage:
  python scripts/report_qa_scan.py dist/report.html
  python scripts/report_qa_scan.py dist/report.pdf
  python scripts/report_qa_scan.py dist/ --json
  python scripts/report_qa_scan.py dist/ --segment solo --fail-on error
  python scripts/report_qa_scan.py artifacts/ --junit artifacts/qa_scan.xml

Optional outputs:
  --json        print machine-readable JSON report to stdout
  --junit PATH  write a small JUnit XML file (useful for CI artifacts)

Notes:
- PDF text extraction uses PyMuPDF (fitz) if available, otherwise pypdf/pdfminer.
- HTML text extraction uses BeautifulSoup if available, otherwise a simple tag-stripper.
- Complements (not replaces) the in-pipeline validators in services/.
"""

from __future__ import annotations

import argparse
import dataclasses
import html as html_lib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    severity: str  # 'error' | 'warning'
    # where: 'text' = extracted human text; 'raw' = raw file content (HTML only)
    where: str
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE

    def compile(self) -> "re.Pattern[str]":
        return re.compile(self.pattern, self.flags)


# Core blockers — focused on post-render artifacts
DEFAULT_RULES: List[Rule] = [
    # --- WP1 blocker patterns (empty business case values) ---
    Rule(
        id='CURRENCY_EURO_DOT',
        description='Leerer Euro-Wert: Punkt direkt nach € ohne Zahl (Template-Artefakt)',
        severity='error',
        where='text',
        # Match "€." but NOT "6.000 €." (valid sentence ending after a value).
        # Key: no digit within 3 chars before the €. Catches ": €." and standalone "€."
        pattern=r'(?<!\d)(?<!\d[ \xa0])€\s*\.',
    ),
    Rule(
        id='PERCENT_PLACEHOLDER_BEI',
        description='Leerer Prozent-Platzhalter: "bei %" ohne Zahl davor',
        severity='error',
        where='text',
        pattern=r'bei\s+%(?=\s|[)\].,;:!?]|$)',
    ),
    Rule(
        id='COLON_PERCENT_EMPTY',
        description='Leerer Prozent-Wert nach Doppelpunkt: ": %"',
        severity='error',
        where='text',
        pattern=r':\s+%(?=\s|[)\].,;:!?]|$)',
    ),
    # --- Prompt/template leak patterns ---
    Rule(
        id='LEAK_PLATZHALTER',
        description="Template-Leak: 'Platzhalter' im Fliesstext",
        severity='error',
        where='text',
        pattern=r'\bPlatzhalter\b',
    ),
    Rule(
        id='LEAK_BITTE_NENNE',
        description="Prompt-Leak: 'Bitte nenne/nennen kurz ...'",
        severity='error',
        where='text',
        pattern=r'\bbitte\s+nenn(?:e|en)\s+kurz\b',
    ),
    Rule(
        id='LEAK_ASSISTANT_DE',
        description="KI-Assistenz-Leak: 'wie kann ich dir/Ihnen helfen', 'als KI-Assistent'",
        severity='error',
        where='text',
        pattern=r'\b(?:wie\s+kann\s+ich\s+(?:dir|Ihnen|ihnen)\s+helfen|als\s+KI[- ]?Assistent|ich\s+bin\s+ein\s+KI)\b',
    ),
    Rule(
        id='LEAK_ASSISTANT_EN',
        description="AI assistant leak: 'how can I help', 'as an AI'",
        severity='error',
        where='text',
        pattern=r"\b(?:how\s+can\s+I\s+help|as\s+an\s+AI|I(?:'m| am)\s+an?\s+AI)\b",
    ),
    # --- RC3: Empty-input LLM fallback (confirmed blocker in Report #561) ---
    Rule(
        id='PLACEHOLDER_EMPTY_INPUT_FALLBACK',
        description='LLM-Fallback: Chatbot meldet fehlende Eingabe statt Report-Content',
        severity='error',
        where='text',
        pattern=r'\bIch\s+habe\s+keine\s+(?:Frage|Aufgabe|Information(?:en)?|Angaben)\b'
                r'|\bkeine\s+Frage\s+oder\s+Aufgabe\s+von\s+Ihnen\b'
                r'|\bwobei\s+kann\s+ich\s+(?:dir|Ihnen)\s+helfen\b',
    ),
    # --- RC3: Prompt-/Input-Checklist leak (confirmed in Report #561 PDF) ---
    Rule(
        id='LEAK_INPUT_CHECKLIST',
        description='Prompt-Leak: Input-Checklist-Begriff im Fliesstext (Datenlage/Tool-Uebersicht)',
        severity='warning',
        where='text',
        # "Datenlage" and "Tool-Übersicht" are pipeline input terms that shouldn't
        # appear verbatim in rendered reports. "Branche und Ziel" excluded (too broad).
        pattern=r'\b(?:Input-Checkliste|Datenlage|Tool-Übersicht)\b',
    ),
    # --- Du-form (informal address) ---
    Rule(
        id='DU_FORM_PRONOUNS',
        description="Du-Ansprache gefunden (du/dein/dich/dir) — Report soll Sie-Form verwenden",
        severity='warning',
        where='text',
        # Strict word-boundary: exclude "durch", "Produkt", "Industrie", "Verdunstung", etc.
        # Only match standalone du/dein/dich/dir NOT preceded/followed by letters
        # Use negative lookbehind/lookahead for German letters including umlauts
        pattern=r'(?<![A-Za-zÄÖÜäöüß])(?:du|dich|dir|dein(?:e[mnrs]?)?)(?![A-Za-zÄÖÜäöüß-])',
        flags=0,  # case-sensitive: only lowercase "du" etc.
    ),
    # --- Placeholder/TODO markers ---
    Rule(
        id='PLACEHOLDER_TODO',
        description='Platzhalter-Text: TODO/TBD/Lorem ipsum',
        severity='error',
        where='text',
        pattern=r'\b(?:TODO|TBD|Lorem\s+ipsum)\b',
    ),
    Rule(
        id='PLACEHOLDER_JINJA',
        description='Ungerenderter Template-Marker: {{ ... }} oder {% ... %}',
        severity='error',
        where='raw',
        pattern=r'(\{\{[^}]+\}\}|\{%\s*[^%]+%\})',
    ),
    # --- Truncation artifacts (survive content_quality_enforcer) ---
    Rule(
        id='TRUNCATION_ELLIPSIS',
        description='Trunkierungs-Artefakt: abgeschnittenes Wort mit Ellipse',
        severity='error',
        where='text',
        # Words ending with … or ... that indicate LLM/post-processing truncation
        # Exclude legitimate "..." at sentence end (3+ chars before dots)
        pattern=r'\b[A-Za-zÄÖÜäöüß]{1,4}[…]',
        flags=0,
    ),
    Rule(
        id='INCOMPLETE_SENTENCE_FRAGMENT',
        description='Unvollstaendiger Satz: Konjunktion/Artikel am Satzende ohne Fortsetzung',
        severity='warning',
        where='text',
        # A conjunction/article immediately followed by a period — indicates truncation
        pattern=r'\b(?:jedoch|darüber hinaus|allerdings|zudem|sowie|eines|einer|einem)\s*\.',
    ),
    # --- Un-localized English BC labels (should have been translated by healer) ---
    Rule(
        id='ENGLISH_BC_LABEL',
        description='Nicht lokalisiertes englisches Business-Case-Label',
        severity='error',
        where='text',
        pattern=r'\b(?:Payback\s+Progress|Time\s+Savings\s+(?:Hours|\(Hours\))|Monthly\s+Savings|Net\s+Present\s+Value)\b',
    ),
    # --- Excessive "n.v." indicating BC calculation failure ---
    Rule(
        id='NV_PLACEHOLDER_CLUSTER',
        description='Gehaeufte n.v.-Platzhalter (>3): Business-Case-Berechnung vermutlich fehlgeschlagen',
        severity='warning',
        where='text',
        # Matches 4th+ occurrence of "n. v." / "n.v." in text — the scan_content
        # loop handles first 3 as benign, 4th+ triggers this rule via post-scan check.
        # This pattern matches every single "n. v." / "n.v." occurrence;
        # the _check_nv_cluster post-scan step evaluates the count.
        pattern=r'n\.[\s\xa0]?v\.',
    ),
]

# Segment-specific rules
SEGMENT_RULES: Dict[str, List[Rule]] = {
    'solo': [
        Rule(
            id='SOLO_GOVERNANCE',
            description="SOLO: 'Governance' sollte als 'Spielregeln' erscheinen",
            severity='error',
            where='text',
            pattern=r'\bGovernance\b',
        ),
        Rule(
            id='SOLO_ENTERPRISE_TERMS',
            description='SOLO: Enterprise-Begriff (Stakeholder/Audit-Trail/Matrixorganisation)',
            severity='warning',
            where='text',
            pattern=r'\b(?:Stakeholder|Audit[-\s]?Trail|Matrixorganisation)\b',
        ),
    ],
    'team': [
        Rule(
            id='TEAM_SOLO_LANGUAGE',
            description='TEAM: Solo-spezifische Sprache erkannt (Einzelunternehmer/Freelancer/Solopreneur)',
            severity='warning',
            where='text',
            pattern=r'\b(?:Einzelunternehmer(?:in)?|Freelancer(?:in)?|Solopreneur(?:in)?|Solo-Selbstst[äa]ndige[rn]?|Ihre\s+Agilit[äa]t\s+als\s+Einzelperson)\b',
        ),
        Rule(
            id='TEAM_PAYBACK_PROGRESS_RAW',
            description='TEAM: Un-lokalisiertes "Payback Progress" Label (sollte deutsch sein)',
            severity='error',
            where='text',
            pattern=r'Payback\s+Progress\s*:?\s*\d+\s*%',
        ),
    ],
    'kmu': [
        Rule(
            id='KMU_SOLO_LANGUAGE',
            description='KMU: Solo-spezifische Sprache erkannt (Einzelunternehmer/Freelancer/Solopreneur)',
            severity='warning',
            where='text',
            pattern=r'\b(?:Einzelunternehmer(?:in)?|Freelancer(?:in)?|Solopreneur(?:in)?|Solo-Selbstst[äa]ndige[rn]?|Ihre\s+Agilit[äa]t\s+als\s+Einzelperson)\b',
        ),
        Rule(
            id='KMU_PAYBACK_PROGRESS_RAW',
            description='KMU: Un-lokalisiertes "Payback Progress" Label (sollte deutsch sein)',
            severity='error',
            where='text',
            pattern=r'Payback\s+Progress\s*:?\s*\d+\s*%',
        ),
        Rule(
            id='KMU_GOVERNANCE_DEPTH',
            description='KMU: "Spielregeln" statt "Governance" — KMU benoetigt Enterprise-Terminologie',
            severity='warning',
            where='text',
            # Inverse of Solo rule: KMU should use Governance, not Solo-simplified "Spielregeln"
            pattern=r'\bSpielregeln\b',
        ),
    ],
}


# ---------------------------------------------------------------------------
# Findings model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    file: str
    file_type: str  # 'html' | 'pdf' | 'txt'
    rule_id: str
    severity: str
    description: str
    match: str
    snippet: str
    position: int


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def _extract_text_from_html(raw: str) -> str:
    """Extract visible text from HTML, stripping tags/scripts/styles."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw, 'html.parser')
        # Remove script and style elements
        for tag in soup(['script', 'style']):
            tag.decompose()
        text = soup.get_text(' ')
    except Exception:
        # Fallback: crude tag stripping
        text = re.sub(r'<script\b[^>]*>.*?</script>', ' ', raw, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<style\b[^>]*>.*?</style>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
    text = html_lib.unescape(text)
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def _extract_text_from_pdf(path: Path) -> str:
    """Extract text from PDF using best available library."""
    # Try PyMuPDF first (fast + robust)
    try:
        import fitz
        doc = fitz.open(str(path))
        parts: List[str] = []
        for page in doc:
            parts.append(page.get_text('text'))
        doc.close()
        return '\n'.join(parts)
    except Exception:
        pass

    # Fallback: pypdf
    for mod in ('pypdf', 'PyPDF2'):
        try:
            pdf_mod = __import__(mod)
            reader = pdf_mod.PdfReader(str(path))
            parts = []
            for p in reader.pages:
                parts.append(p.extract_text() or '')
            return '\n'.join(parts)
        except Exception:
            continue

    # Fallback: pdfminer.six
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(path)) or ''
    except Exception as exc:
        raise RuntimeError(f'Could not extract text from PDF {path}: {exc}') from exc


def _read_file(path: Path) -> Tuple[str, str, str]:
    """Returns (file_type, raw_content, extracted_text)."""
    suffix = path.suffix.lower()
    if suffix in ('.html', '.htm'):
        raw = path.read_text(encoding='utf-8', errors='replace')
        return ('html', raw, _extract_text_from_html(raw))
    if suffix == '.pdf':
        extracted = _extract_text_from_pdf(path)
        return ('pdf', '', extracted)
    raw = path.read_text(encoding='utf-8', errors='replace')
    return ('txt', raw, raw)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def _snippet(text: str, start: int, end: int, radius: int = 60) -> str:
    """Extract a context snippet around a match."""
    a = max(0, start - radius)
    b = min(len(text), end + radius)
    sn = text[a:b].replace('\n', ' ').strip()
    return re.sub(r'\s{2,}', ' ', sn)


_NV_CLUSTER_THRESHOLD = 3  # 1-3 "n.v." is normal; 4+ indicates BC failure


def scan_content(
    *,
    file_path: Path,
    file_type: str,
    raw: str,
    text: str,
    rules: Sequence[Rule],
    max_findings_per_rule: int = 50,
) -> List[Finding]:
    """Scan content against all rules and return findings."""
    findings: List[Finding] = []
    for rule in rules:
        haystack = text if rule.where == 'text' else raw
        if not haystack:
            continue

        # NV_PLACEHOLDER_CLUSTER: only emit findings if count exceeds threshold
        if rule.id == 'NV_PLACEHOLDER_CLUSTER':
            rx = rule.compile()
            matches = list(rx.finditer(haystack))
            if len(matches) > _NV_CLUSTER_THRESHOLD:
                # Report a single aggregated finding
                first = matches[0]
                findings.append(
                    Finding(
                        file=str(file_path),
                        file_type=file_type,
                        rule_id=rule.id,
                        severity=rule.severity,
                        description=f'{rule.description} ({len(matches)}x gefunden)',
                        match=f'n.v. x{len(matches)}',
                        snippet=_snippet(haystack, first.start(), first.end()),
                        position=first.start(),
                    )
                )
            continue

        rx = rule.compile()
        count = 0
        for m in rx.finditer(haystack):
            s, e = m.span()
            findings.append(
                Finding(
                    file=str(file_path),
                    file_type=file_type,
                    rule_id=rule.id,
                    severity=rule.severity,
                    description=rule.description,
                    match=(m.group(0) or '')[:200],
                    snippet=_snippet(haystack, s, e),
                    position=s,
                )
            )
            count += 1
            if count >= max_findings_per_rule:
                break
    return findings


def iter_target_files(paths: Sequence[Path]) -> Iterable[Path]:
    """Yield scannable files from paths (files or directories)."""
    exts = {'.pdf', '.html', '.htm', '.txt'}
    for p in paths:
        if p.is_dir():
            for root, _, files in os.walk(p):
                for fn in sorted(files):
                    fp = Path(root) / fn
                    if fp.suffix.lower() in exts:
                        yield fp
        else:
            yield p


def build_rules(segment: Optional[str]) -> List[Rule]:
    """Build the rule set, optionally adding segment-specific rules."""
    rules = list(DEFAULT_RULES)
    if segment:
        rules.extend(SEGMENT_RULES.get(segment.strip().lower(), []))
    return rules


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_human(findings: List[Finding]) -> None:
    """Print human-readable findings to stdout."""
    if not findings:
        print('\u2705 QA-SCAN: Keine Verstoesse gefunden.')
        return

    total_errors = sum(1 for f in findings if f.severity == 'error')
    total_warnings = sum(1 for f in findings if f.severity == 'warning')
    print(f'\u274c QA-SCAN: Verstoesse gefunden \u2014 errors={total_errors}, warnings={total_warnings}')

    by_file: Dict[str, List[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    for file, items in sorted(by_file.items()):
        print(f'\n{file}')
        for it in sorted(items, key=lambda x: (x.severity != 'error', x.rule_id, x.position)):
            sev = 'ERROR' if it.severity == 'error' else 'WARN '
            print(f'  [{sev}] {it.rule_id}: {it.description}')
            print(f'         match: {it.match!r}')
            print(f'       snippet: {it.snippet!r}')


def write_junit(path: Path, findings: List[Finding]) -> None:
    """Write findings as JUnit XML for CI artifact upload."""
    import xml.etree.ElementTree as ET

    by_file: Dict[str, List[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    testsuite = ET.Element(
        'testsuite',
        attrib={
            'name': 'report_qa_scan',
            'tests': str(len(by_file) if by_file else 1),
            'failures': str(sum(1 for f in findings if f.severity == 'error')),
        },
    )

    if not by_file:
        tc = ET.SubElement(testsuite, 'testcase', attrib={'name': 'no_findings'})
        ET.SubElement(tc, 'system-out').text = 'No findings'
    else:
        for file, items in sorted(by_file.items()):
            tc = ET.SubElement(testsuite, 'testcase', attrib={'name': file})
            errors = [x for x in items if x.severity == 'error']
            if errors:
                msg_lines = [f'{e.rule_id}: {e.match} | {e.snippet}' for e in errors[:25]]
                failure = ET.SubElement(tc, 'failure', attrib={'message': f'{len(errors)} error(s) found'})
                failure.text = '\n'.join(msg_lines)
            warnings = [x for x in items if x.severity == 'warning']
            if warnings:
                out_lines = [f'[WARN] {w.rule_id}: {w.match} | {w.snippet}' for w in warnings[:50]]
                ET.SubElement(tc, 'system-out').text = '\n'.join(out_lines)

    tree = ET.ElementTree(testsuite)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(path), encoding='utf-8', xml_declaration=True)


def findings_to_json(findings: List[Finding]) -> Dict[str, object]:
    """Convert findings to JSON-serializable dict."""
    return {
        'schema': 'report_qa_scan.v1',
        'passed': sum(1 for f in findings if f.severity == 'error') == 0,
        'summary': {
            'total': len(findings),
            'errors': sum(1 for f in findings if f.severity == 'error'),
            'warnings': sum(1 for f in findings if f.severity == 'warning'),
        },
        'findings': [dataclasses.asdict(f) for f in findings],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description='CI-friendly QA scan for rendered report HTML/PDF artifacts.'
    )
    ap.add_argument('paths', nargs='+', help='File(s) or directory(ies) to scan')
    ap.add_argument('--segment', choices=['solo', 'team', 'kmu'], default=None,
                    help='Size segment (adds segment-specific checks)')
    ap.add_argument('--json', action='store_true', help='Print JSON report to stdout')
    ap.add_argument('--junit', default=None, help='Write JUnit XML to given path')
    ap.add_argument('--fail-on', choices=['error', 'warning'], default='error',
                    help='Exit code 2 on errors only (default) or also on warnings')
    ap.add_argument('--max-findings-per-rule', type=int, default=50,
                    help='Max findings per rule per file (default: 50)')
    args = ap.parse_args(argv)

    try:
        paths = [Path(p) for p in args.paths]
        rules = build_rules(args.segment)

        findings: List[Finding] = []
        scanned = 0
        for fp in iter_target_files(paths):
            if not fp.exists():
                continue
            file_type, raw, text = _read_file(fp)
            findings.extend(
                scan_content(
                    file_path=fp,
                    file_type=file_type,
                    raw=raw,
                    text=text,
                    rules=rules,
                    max_findings_per_rule=args.max_findings_per_rule,
                )
            )
            scanned += 1

        if scanned == 0:
            print('QA-SCAN: Keine scanbaren Dateien gefunden.', file=sys.stderr)
            return 1

        if args.json:
            print(json.dumps(findings_to_json(findings), ensure_ascii=False, indent=2))
        else:
            print_human(findings)

        if args.junit:
            write_junit(Path(args.junit), findings)

        if args.fail_on == 'warning':
            return 2 if findings else 0
        return 2 if any(f.severity == 'error' for f in findings) else 0

    except Exception as exc:
        print(f'QA-SCAN runtime error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

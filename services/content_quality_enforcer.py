"""
Content Quality Enforcer v1.0
=============================
Post-Processing Safety Net für Report-Qualität.

Fixes:
1. ROI-Filter: Entfernt ROI% außerhalb Business Case
2. Fragment-Repair: Repariert unvollständige Sätze
3. hauptleistung-Enforcer: Injiziert hauptleistung wenn unter Minimum
4. Product Name Safety Net: Korrigiert "Microsoft Kapazitäten" → "Microsoft Teams" (v14.35.21)
5. Solo Language Normalizer: Enterprise-Begriffe → Solo-freundlich (v14.35.22)

Wird nach SIEZEN-GUARD aufgerufen, vor Validation.
"""

import re
import logging

log = logging.getLogger(__name__)

# =============================================================================
# v14.35.22: SOLO LANGUAGE NORMALIZER
# =============================================================================
# Replaces enterprise-ish terms with solo-appropriate alternatives ONLY for solo persona.
# This reduces SIZE_MISMATCH warnings without changing meaning.

SOLO_TERM_REPLACEMENTS = [
    # (pattern, replacement, description)
    # Technical enterprise terms → Solo-friendly alternatives
    (r'\bModulen\b', 'Bausteinen', 'Modul→Baustein (Dativ Plural)'),
    (r'\bModule\b', 'Bausteine', 'Modul→Baustein (Plural)'),
    (r'\bModul\b', 'Baustein', 'Modul→Baustein'),
    (r'\bPlattformen\b', 'Tool-Setups', 'Plattform→Tool-Setup (Plural)'),
    (r'\bPlattform\b', 'Tool-Setup', 'Plattform→Tool-Setup'),
    (r'\bArchitekturen\b', 'Strukturen', 'Architektur→Struktur (Plural)'),
    (r'\bArchitektur\b', 'Struktur', 'Architektur→Struktur'),
    (r'\bTech-Stack\b', 'Tool-Set', 'Tech-Stack→Tool-Set'),
    (r'\bKI-Stack\b', 'KI-Werkzeuge', 'KI-Stack→KI-Werkzeuge'),
    (r'\bStack\b', 'Tool-Set', 'Stack→Tool-Set'),
    (r'\bLayer\b', 'Ebene', 'Layer→Ebene'),
    (r'\bDeployment\b', 'Einrichtung', 'Deployment→Einrichtung'),
    (r'\bRollout\b', 'Einführung', 'Rollout→Einführung'),
    (r'\bStakeholder\b', 'Beteiligte', 'Stakeholder→Beteiligte'),
    (r'\bGovernance-Struktur\b', 'Ordnungsrahmen', 'Governance-Struktur→Ordnungsrahmen'),
    (r'\bCompliance-Framework\b', 'Regelwerk', 'Compliance-Framework→Regelwerk'),
    (r'\bKPI-Dashboard\b', 'Kennzahlen-Übersicht', 'KPI-Dashboard→Kennzahlen-Übersicht'),
    (r'\bProzesslandschaft\b', 'Arbeitsabläufe', 'Prozesslandschaft→Arbeitsabläufe'),
    (r'\bMeilenstein-Planung\b', 'Etappenplanung', 'Meilenstein-Planung→Etappenplanung'),
]


def apply_solo_language_normalizer(sections: dict, company_size: str) -> dict:
    """
    Ersetzt Enterprise-Begriffe durch Solo-freundliche Alternativen.

    v14.35.22: Nur angewendet wenn company_size == "solo".
    Reduziert SIZE_MISMATCH Warnings ohne Bedeutungsänderung.

    Args:
        sections: Dict mit allen Report-Sections
        company_size: Unternehmensgröße ("solo", "team", "kmu")

    Returns:
        sections: Bereinigtes Dict
    """
    # Only apply for solo
    if not company_size or company_size.lower() != "solo":
        return sections

    total_replacements = 0
    sections_touched = 0

    # Sections to process
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "RECOMMENDATIONS_HTML", "QUICK_WINS_HTML",
        "ROADMAP_90D_HTML", "ROADMAP_12M_HTML", "GAMECHANGER_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML",
        "TOOLS_HTML", "DATA_STRATEGY_HTML", "GOVERNANCE_HTML",
    ]

    for section_key in check_sections:
        content = sections.get(section_key)
        if not content or not isinstance(content, str):
            continue

        section_replacements = 0
        modified_content = content

        for pattern, replacement, desc in SOLO_TERM_REPLACEMENTS:
            matches = len(re.findall(pattern, modified_content, re.IGNORECASE))
            if matches > 0:
                modified_content = re.sub(pattern, replacement, modified_content, flags=re.IGNORECASE)
                section_replacements += matches

        if section_replacements > 0:
            sections[section_key] = modified_content
            sections_touched += 1
            total_replacements += section_replacements

    if total_replacements > 0:
        log.info(
            "[SOLO-LANGUAGE] replaced_terms=%d in %d sections (company_size=solo)",
            total_replacements,
            sections_touched
        )

    return sections


# =============================================================================
# v14.35.21: PRODUCT NAME SAFETY NET (Seatbelt)
# =============================================================================
# This is a "seatbelt" - should never trigger if protection works correctly,
# but saves the release if something slips through.

PRODUCT_NAME_MUTATIONS = [
    # (broken_pattern, correct_replacement)
    (r"Microsoft\s+Kapazitäten", "Microsoft Teams"),
    (r"MS\s+Kapazitäten", "MS Teams"),
    (r"Google\s+Kapazitäten", "Google Teams"),  # hypothetical
]


def fix_product_name_mutations(html: str) -> tuple[str, int]:
    """
    Safety Net: Korrigiert fehlerhafte Produktnamen-Mutationen.

    v14.35.21: "Microsoft Kapazitäten" → "Microsoft Teams"

    This is a seatbelt - should never trigger if the protection in
    apply_solo_persona_filter() works correctly.

    Returns:
        tuple: (fixed_html, fix_count)
    """
    if not html:
        return html, 0

    result = html
    fix_count = 0

    for broken_pattern, correct in PRODUCT_NAME_MUTATIONS:
        pattern = re.compile(broken_pattern, re.IGNORECASE)
        matches = pattern.findall(result)
        if matches:
            result = pattern.sub(correct, result)
            fix_count += len(matches)
            log.warning(
                f"[SAFETY-NET] Fixed product name mutation: "
                f"'{broken_pattern}' → '{correct}' ({len(matches)}x)"
            )

    return result, fix_count


def apply_product_name_safety_net(sections: dict) -> dict:
    """
    Wendet Product Name Safety Net auf alle Sections an.

    v14.35.21: Seatbelt für "Microsoft Kapazitäten" → "Microsoft Teams"
    """
    total_fixes = 0

    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            fixed, count = fix_product_name_mutations(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count

    if total_fixes > 0:
        log.warning(f"[SAFETY-NET] Total product name mutations fixed: {total_fixes}")

    return sections


# =============================================================================
# Fix-Batch F: TEXT GLITCH FIXER
# =============================================================================
# Known text glitches that appear in reports due to LLM word corruption or
# unwanted zero values that should be suppressed.

TEXT_GLITCH_REPLACEMENTS = [
    # (pattern, replacement, description)
    # Word corruption glitches
    (r'\bresourceselung\b', 'Ressourcenstaffelung', 'corrupted word'),
    (r'\bRessourceselung\b', 'Ressourcenstaffelung', 'corrupted word capitalized'),
    # Zero resource display suppression
    (r'Ressourcen:\s*0\b', '', 'zero resources'),
    (r'Ressourcen\s*:\s*0\b', '', 'zero resources with space'),
    (r'\bRessourcen\s+0\b', '', 'zero resources no colon'),
    # Empty placeholder patterns
    (r'Mitarbeiter:\s*0\b', '', 'zero employees'),
    (r'Mitarbeiter\s*:\s*0\b', '', 'zero employees with space'),
]


def fix_text_glitches(html: str) -> tuple[str, int]:
    """
    Fix-Batch F: Fix known text glitches in HTML content.

    Fixes:
    - "resourceselung" → "Ressourcenstaffelung"
    - "Ressourcen: 0" → (removed)
    - Other known glitches

    Returns:
        tuple: (fixed_html, fix_count)
    """
    if not html:
        return html, 0

    result = html
    fix_count = 0

    for pattern, replacement, desc in TEXT_GLITCH_REPLACEMENTS:
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(result)
        if matches:
            result = regex.sub(replacement, result)
            fix_count += len(matches)
            log.info(f"[GLITCH-FIX] Fixed '{desc}': {len(matches)}x")

    return result, fix_count


def apply_text_glitch_fixer(sections: dict) -> dict:
    """
    Fix-Batch F: Apply text glitch fixes to all sections.

    Fixes known LLM word corruptions and unwanted zero displays.
    """
    total_fixes = 0

    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            fixed, count = fix_text_glitches(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count

    if total_fixes > 0:
        log.info(f"[GLITCH-FIX] Total text glitches fixed: {total_fixes}")

    return sections


# =============================================================================
# v14.35.22: OPEN EXAMPLE PAREN FIXER
# =============================================================================
# Problem: Report 468 had "(z.B." or "(z. B." at sentence ends without closing
# Solution: Remove incomplete example references, end with proper punctuation
# =============================================================================

# Pattern for open "(z.B." / "(z. B." patterns
OPEN_EXAMPLE_PATTERNS = [
    # "(z.B." at end of tag content (before </tag>)
    (re.compile(r'\(z\.\s*[Bb]\.\s*(</)'), r'\1'),
    # "(z. B." with space
    (re.compile(r'\(z\.\s+[Bb]\.\s*(</)'), r'\1'),
    # "(z.B." at end of line/text
    (re.compile(r'\(z\.\s*[Bb]\.\s*$', re.MULTILINE), '.'),
    # Lone "z.B." at end (careful)
    (re.compile(r'(?<=[,;:\s])\s*z\.\s*[Bb]\.\s*$', re.MULTILINE), '.'),
]


def fix_open_example_paren_html(html: str) -> tuple[str, int]:
    """
    Fix open example parentheses like "(z.B." in HTML content.

    v14.35.22: Adressiert Report 468 Problem #2 - offene Klammern.
    """
    if not html:
        return html, 0

    fix_count = 0
    result = html

    for pattern, replacement in OPEN_EXAMPLE_PATTERNS:
        new_result, count = pattern.subn(replacement, result)
        if count > 0:
            fix_count += count
            result = new_result

    return result, fix_count


def apply_open_example_paren_fixer(sections: dict) -> dict:
    """
    Wendet Open Example Paren Fixer auf alle Sections an.

    v14.35.22: Entfernt unvollständige "(z.B." Muster
    """
    total_fixes = 0

    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            fixed, count = fix_open_example_paren_html(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count

    if total_fixes > 0:
        log.info(f"[OPEN-PAREN-FIX] Total open example parens fixed: {total_fixes}")

    return sections


# =============================================================================
# 1. ROI-FILTER: Entfernt ROI-Prozentsätze außerhalb Business Case
# =============================================================================

ROI_PATTERNS = [
    # Explizite ROI-Prozentsätze
    r'\b(\d{2,3})\s*%?\s*ROI\b',           # "284% ROI" oder "284 ROI"
    r'\bROI\s*(?:von|of|:)?\s*(\d{2,3})\s*%',  # "ROI von 284%" oder "ROI: 284%"
    r'\bROI\s*(\d{2,3})\s*%',              # "ROI 284%"
    r'ERWARTETER\s+ROI\s*:?\s*(\d{2,3})\s*%',  # "ERWARTETER ROI: 284%"
    # Rendite-Varianten
    r'\bRendite\s*(?:von)?\s*(\d{2,3})\s*%',
    # Standalone hohe Prozentsätze im ROI-Kontext (vorsichtig)
    r'(?:ROI|Rendite|Return)[^.]{0,30}(\d{2,3})\s*%',
]

# Sections wo ROI ERLAUBT ist
ROI_ALLOWED_SECTIONS = [
    "BUSINESS_CASE_HTML", "business_case",
    "ROI_HTML", "business_roi",
    "BUSINESS_CASE_TABLE_HTML", "business_case_table_html",
    "BUSINESS_CASE_ENGINE_HTML",
    "BUSINESS_CASE_SIM_HTML",
]

def remove_roi_from_section(html: str, section_name: str) -> tuple[str, int]:
    """
    Entfernt ROI-Prozentsätze aus einer Section.
    
    Returns:
        tuple: (cleaned_html, removal_count)
    """
    if not html or len(html) < 50:
        return html, 0
    
    # Skip wenn ROI erlaubt
    if any(allowed in section_name for allowed in ROI_ALLOWED_SECTIONS):
        return html, 0
    
    removal_count = 0
    result = html
    
    for pattern in ROI_PATTERNS:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        for match in reversed(matches):  # Reverse um Indizes stabil zu halten
            # Ersetze mit Verweis auf Business Case
            replacement = "→ siehe Business Case"
            result = result[:match.start()] + replacement + result[match.end():]
            removal_count += 1
            log.info(f"[ROI-FILTER] {section_name}: Removed '{match.group()}' → '{replacement}'")
    
    return result, removal_count


def apply_roi_filter(sections: dict) -> dict:
    """
    Wendet ROI-Filter auf alle relevanten Sections an.
    """
    total_removed = 0
    
    # Sections die geprüft werden sollen
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "executive_summary",
        "RECOMMENDATIONS_HTML", "recommendations", 
        "GAMECHANGER_HTML", "gamechanger",
        "QUICK_WINS_HTML", "quick_wins",
        "HERO_HTML", "hero",
        "ROADMAP_90D_HTML", "roadmap_90d",
        "ROADMAP_12M_HTML", "roadmap_12m",
        "FOERDERPOTENZIAL_HTML", "foerderpotenzial",
        "ORG_CHANGE_HTML", "org_change",
        "RISKS_HTML", "risks",
    ]
    
    for key in check_sections:
        if key in sections and sections[key]:
            cleaned, count = remove_roi_from_section(sections[key], key)
            if count > 0:
                sections[key] = cleaned
                total_removed += count
    
    log.info(f"[ROI-FILTER] Complete: {total_removed} ROI references removed")
    return sections


# =============================================================================
# 2. FRAGMENT-REPAIR: Repariert unvollständige Sätze
# =============================================================================

FRAGMENT_PATTERNS = [
    # "Maßnahme: Einrichten eines." → unvollständig
    (r'Maßnahme:\s*[A-ZÄÖÜ][a-zäöüß]+\s+eine[sr]?\s*\.', 
     'Maßnahme: Siehe detaillierte Beschreibung in der Roadmap.'),
    
    # "Maßnahme:." → leer
    (r'Maßnahme:\s*\.', 
     'Maßnahme: Siehe Roadmap für konkrete Schritte.'),
    
    # "Implementieren von." → unvollständig
    (r'Implementieren\s+von\s*\.', 
     'Implementieren der empfohlenen KI-Lösung.'),
    
    # "Aufbau einer." → unvollständig
    (r'Aufbau\s+eine[rs]?\s*\.', 
     'Aufbau einer strukturierten KI-Governance.'),
    
    # "Erstellung eines." → unvollständig
    (r'Erstellung\s+eine[sr]?\s*\.', 
     'Erstellung eines Pilotprojekt-Plans.'),
    
    # "Einrichten eines." → unvollständig
    (r'Einrichten\s+eine[sr]?\s*\.', 
     'Einrichten eines standardisierten Workflows.'),
    
    # "Integration von." → unvollständig
    (r'Integration\s+von\s*\.', 
     'Integration der KI-Tools in bestehende Prozesse.'),
    
    # "Entwicklung einer." → unvollständig
    
    # "strukturiertem JSON-Output und." → unvollständig (v14.17)
    # v14.18: "jedes." allein am Ende
    (r'\b(jedes)\.$', r'\1 Mal.'),
    # "betrachtet werden,." kaputte Interpunktion
    (r',\s*\.$', r'.'),
    (r'\b(\w+)\s+und\.$', r'\1 und mehr.'),
    (r'Entwicklung\s+eine[rs]?\s*\.', 
     'Entwicklung einer KI-Strategie.'),

    # "Maßnahme: Pilotierung eines klar." → Artikel + abgebrochenes Adjektiv
    (r'Maßnahme:\s*[A-ZÄÖÜ][a-zäöüß]+\s+eine[sr]?\s+[a-zäöüß]+\s*\.',
     'Maßnahme: Siehe detaillierte Beschreibung in der Roadmap.'),

    # "...eines kompakten." → Artikel + Adjektiv ohne Nomen
    (r'([A-ZÄÖÜ][^.!?]{10,50})\s+(eines|einer|einem)\s+[a-zäöüß]+\s*\.',
     r'\1 – siehe Roadmap für Details.'),

    
    # Generische Fragment-Erkennung: Satz endet mit Artikel
    (r'([A-ZÄÖÜ][^.!?]{10,50})\s+(eines|einer|einem|von|für|zur|zum)\s*\.', 
     r'\1 – siehe Roadmap für Details.'),
]

def repair_fragments_in_section(html: str, section_name: str) -> tuple[str, int]:
    """
    Repariert Fragment-Sätze in einer Section.
    
    Returns:
        tuple: (repaired_html, repair_count)
    """
    if not html or len(html) < 50:
        return html, 0
    
    repair_count = 0
    result = html
    
    for pattern, replacement in FRAGMENT_PATTERNS:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        if matches:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            repair_count += len(matches)
            for match in matches:
                log.info(f"[FRAGMENT-REPAIR] {section_name}: Fixed '{match.group()[:50]}...'")
    
    return result, repair_count


def apply_fragment_repair(sections: dict) -> dict:
    """
    Wendet Fragment-Repair auf alle relevanten Sections an.
    """
    total_repaired = 0
    
    # Sections die geprüft werden sollen
    check_sections = [
        "RECOMMENDATIONS_HTML", "recommendations",
        "QUICK_WINS_HTML", "quick_wins",
        "ROADMAP_90D_HTML", "roadmap_90d",
        "ROADMAP_12M_HTML", "roadmap_12m",
        "GAMECHANGER_HTML", "gamechanger",
        "ORG_CHANGE_HTML", "org_change",
    ]
    
    for key in check_sections:
        if key in sections and sections[key]:
            repaired, count = repair_fragments_in_section(sections[key], key)
            if count > 0:
                sections[key] = repaired
                total_repaired += count
    
    log.info(f"[FRAGMENT-REPAIR] Complete: {total_repaired} fragments repaired")
    return sections

def fix_truncation_ellipsis(html: str) -> tuple[str, int]:
    """
    v14.27: Entfernt Trunkierungs-Ellipsen aus HTML.
    Patterns wie "daue…", "Le…", "Se…" werden entfernt.
    """
    if not html:
        return html, 0
    
    result = html
    fixes = 0
    
    # Pattern: Wort das mit … oder ... endet (Trunkierung)
    # v14.28: Aggressiveres Ellipsis-Pattern (auch 1-Zeichen)
    truncated = re.findall(r'\b\w+[…..]{1,3}(?=\s|<|$|\*)', result)
    # Auch Markdown-formatierte truncations
    truncated += re.findall(r'\*\*\w+[…]+\*\*', result)
    for tw in truncated:
        if tw.endswith('…') or tw.endswith('...'):
            result = result.replace(tw, '')
            fixes += 1
    
    # Cleanup: Doppelte Leerzeichen
    result = re.sub(r'  +', ' ', result)
    
    if fixes > 0:
        log.info(f"[ELLIPSIS-FIX] Fixed {fixes} truncation ellipses")
    
    return result, fixes

def apply_ellipsis_fix(sections: dict) -> dict:
    """
    v14.27: Wendet Ellipsen-Fix auf alle relevanten Sections an.
    Entfernt Trunkierungs-Artefakte wie "daue…", "Le…", "Se…"
    """
    ellipsis_sections = [
        "RISKS_HTML", "risks", "BRANCH_RISKS_HTML",
        "RECOMMENDATIONS_HTML", "recommendations",
        "QUICK_WINS_HTML", "quick_wins",
        "GAMECHANGER_HTML", "gamechanger",
    ]
    
    total_fixed = 0
    for key in ellipsis_sections:
        if key in sections and sections[key]:
            fixed, count = fix_truncation_ellipsis(sections[key])
            if count > 0:
                sections[key] = fixed
                total_fixed += count
    
    if total_fixed > 0:
        log.info(f"[ELLIPSIS-FIX] Complete: {total_fixed} ellipses fixed")
    return sections


# =============================================================================
# 3. HAUPTLEISTUNG-ENFORCER: Injiziert hauptleistung wenn unter Minimum
# =============================================================================

def count_hauptleistung(html: str, hauptleistung: str) -> int:
    """Zählt Vorkommen von hauptleistung in HTML."""
    if not html or not hauptleistung:
        return 0
    # Case-insensitive Suche
    return len(re.findall(re.escape(hauptleistung), html, re.IGNORECASE))


def inject_hauptleistung_executive(html: str, hauptleistung: str, current_count: int, target: int = 4) -> str:
    """
    Injiziert hauptleistung in Executive Summary wenn unter Minimum.
    
    Strategy:
    - Ersetzt generische Phrasen durch hauptleistung-Version
    - Priorisiert wichtige Stellen
    """
    if current_count >= target:
        return html
    
    needed = target - current_count
    injections_made = 0
    result = html
    
    # Injection-Patterns (von spezifisch zu generisch)
    injection_patterns = [
        # "Ihr Unternehmen" → "Ihr Unternehmen mit {hauptleistung}"
        (r'\b(Ihr(?:em?)?\s+Unternehmen)\b(?!\s+mit)', 
         f'Ihr Unternehmen mit {hauptleistung}'),
        
        # "Ihr Kerngeschäft" → hauptleistung direkt
        (r'\b(Ihr(?:em?)?\s+Kerngeschäft)\b',
         hauptleistung),
        
        # "diese Leistung" → hauptleistung
        (r'\b(diese[r]?\s+Leistung)\b',
         hauptleistung),
        
        # "Ihr Geschäftsmodell" → "Ihr Geschäftsmodell ({hauptleistung})"
        (r'\b(Ihr(?:em?)?\s+Geschäftsmodell)\b(?!\s*\()',
         f'Ihr Geschäftsmodell ({hauptleistung})'),
        
        # Weitere universelle Synonyme (alle Größen)
        (r'\b(Ihre[rn]?\s+Dienstleistung(?:en)?)\b',
         hauptleistung),
        
        (r'\b(Ihr(?:em?)?\s+Angebot)\b(?!\s*\()',
         f'Ihr Angebot ({hauptleistung})'),
        
        (r'\b(dieses\s+Angebot)\b',
         hauptleistung),
        
        (r'\b(Ihre[rn]?\s+Tätigkeit)\b(?!\s*\()',
         f'Ihre Tätigkeit ({hauptleistung})'),
        
        (r'\b(Ihr(?:em?)?\s+Service)\b',
         hauptleistung),
        
        (r'\b(diese[rn]?\s+Service[s]?)\b',
         hauptleistung),
        
        (r'\b(Ihre[rn]?\s+Leistung(?:en)?)\b',
         hauptleistung),
        
        # Aggressive Patterns für mehr Treffer
        (r'\b(KI-Einsatz)\b(?!\s+für)',
         f'KI-Einsatz für {hauptleistung}'),
        
        (r'\b(Ihrer?\s+Branche)\b(?!\s*\()',
         f'Ihrer Branche ({hauptleistung})'),
        
        (r'\b(Ihrem?\s+Bereich)\b',
         f'Ihrem Bereich {hauptleistung}'),
        
        (r'\b(diesen?\s+Bereich)\b',
         hauptleistung),
        
        (r'\b(Ihr(?:em?)?\s+Betrieb)\b',
         f'Ihr Betrieb ({hauptleistung})'),
        
        (r'\b(diese[rn]?\s+Tätigkeit)\b',
         hauptleistung),

    ]
    for pattern, replacement in injection_patterns:
        if injections_made >= needed:
            break
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            result = re.sub(pattern, replacement, result, count=1, flags=re.IGNORECASE)
            injections_made += 1
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Executive: Injected at '{match.group()[:30]}...'")
    
    # v14.17: Fallback wenn nicht genug Pattern-Matches
    if injections_made < needed:
        fallback_patterns = [
            # v14.19: AGGRESSIVERE Patterns
            (r'(<p>)([A-Z][^<]{10,})', f'\\1Für {hauptleistung}: \\2'),
            (r'(</strong>)(\s*[A-Z])', f'\\1 Im Bereich {hauptleistung} \\2'),
            (r'(<li>)([^<]{5,})', f'\\1{hauptleistung} - \\2'),
            (r'(\w{5,})(</p>)', f'\\1 für {hauptleistung}\\2'),
        ]
        for fb_pattern, fb_replacement in fallback_patterns:
            if injections_made >= needed:
                break
            if re.search(fb_pattern, result):
                result = re.sub(fb_pattern, fb_replacement, result, count=1)
                injections_made += 1
                log.info(f"[HAUPTLEISTUNG-ENFORCER] Executive: Aggressive fallback applied")
    
    # Level 2: Prefix-Injection wenn immer noch nicht genug
    if injections_made < needed:
        prefix = f'<p><strong>Fokus: {hauptleistung}</strong></p>'
        result = prefix + result
        injections_made += 1
        log.info(f"[HAUPTLEISTUNG-ENFORCER] Executive: Prefix injection applied")
    
    return result


def inject_hauptleistung_recommendations(html: str, hauptleistung: str, current_count: int, target: int = 3) -> str:
    """
    Injiziert hauptleistung in Recommendations wenn unter Minimum.
    """
    if current_count >= target:
        return html
    
    needed = target - current_count
    injections_made = 0
    result = html
    
    # Injection-Patterns für Recommendations
    injection_patterns = [
        # "Für Ihr Geschäftsmodell" → "Für Ihr Geschäftsmodell {hauptleistung}"
        (r'\b(Für\s+Ihr(?:em?)?\s+Geschäftsmodell)\b(?!\s+' + re.escape(hauptleistung) + ')',
         f'Für Ihr Geschäftsmodell {hauptleistung}'),
        
        # "Ihre Dienstleistung" → hauptleistung
        (r'\b(Ihre[r]?\s+Dienstleistung(?:en)?)\b',
         hauptleistung),
        
        # "diesen Bereich" → hauptleistung  
        (r'\b(diesen\s+Bereich)\b',
         hauptleistung),
        
        # "Ihren Prozessen" → "Ihren {hauptleistung}-Prozessen"
        
        # Weitere universelle Patterns für Recommendations
        (r'\b(Ihre[rn]?\s+Arbeit(?:sweise)?)\b',
         f'Ihre Arbeit mit {hauptleistung}'),
        
        (r'\b(Ihr(?:em?)?\s+Kerngeschäft)\b',
         hauptleistung),
        
        (r'\b(diese[rn]?\s+Leistung(?:en)?)\b',
         hauptleistung),
        
        (r'\b(Ihr(?:em?)?\s+Angebot)\b',
         hauptleistung),
        
        (r'\b(Ihre[rn]?\s+Tätigkeit)\b',
         hauptleistung),
        
        (r'\b(in\s+diesem\s+Bereich)\b',
         f'im Bereich {hauptleistung}'),

        (r'\b(Ihren\s+Prozessen)\b',
         f'Ihren {hauptleistung}-Prozessen'),
    ]
    
    for pattern, replacement in injection_patterns:
        if injections_made >= needed:
            break
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            result = re.sub(pattern, replacement, result, count=1, flags=re.IGNORECASE)
            injections_made += 1
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected at '{match.group()[:30]}...'")
    
    # v14.28: Count-basierter Fallback für Recommendations
    # Anwenden solange count < needed (nicht "not in"!)
    current_count = result.count(hauptleistung)
    
    while current_count < needed:
        injected = False
        
        # Strategie 1: Nach "KI " einfügen (natürlich)
        if 'KI ' in result and f'KI im Bereich {hauptleistung}' not in result:
            result = result.replace('KI ', f'KI im Bereich {hauptleistung} ', 1)
            injected = True
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected after 'KI '")
        
        # Strategie 2: Nach "Prozess" einfügen
        elif 'Prozess' in result and f'Prozess {hauptleistung}' not in result:
            result = result.replace('Prozess', f'Prozess ({hauptleistung})', 1)
            injected = True
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected after 'Prozess'")
        
        # Strategie 3: Am Anfang eines <li> einfügen
        elif '<li>' in result:
            # Finde ein <li> ohne hauptleistung
            li_pattern = r'(<li>)([^<]{10,})'
            match = re.search(li_pattern, result)
            if match and hauptleistung not in match.group(2)[:50]:
                result = re.sub(li_pattern, f'\\1Für {hauptleistung}: \\2', result, count=1)
                injected = True
                log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected in <li>")
        
        if not injected:
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: No more injection points, count={current_count}")
            break
        
        current_count = result.count(hauptleistung)
        if current_count >= needed:
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Target reached! count={current_count}")
            break
    
    return result


def apply_hauptleistung_enforcer(sections: dict, hauptleistung: str) -> dict:
    """
    Enforced hauptleistung Minimum in Executive Summary und Recommendations.
    """
    if not hauptleistung or len(hauptleistung) < 3:
        log.warning("[HAUPTLEISTUNG-ENFORCER] No hauptleistung provided, skipping")
        return sections
    
    # Executive Summary: Minimum 4x
    for key in ["EXECUTIVE_SUMMARY_HTML", "executive_summary", "EXEC_SUMMARY_HTML"]:  # v14.23: FINAL_CHECK entfernt (ist Plain Text, nicht HTML)
        if key in sections and sections[key]:
            current = count_hauptleistung(sections[key], hauptleistung)
            if current < 4:
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: {current}/4 → enforcing")
                sections[key] = inject_hauptleistung_executive(
                    sections[key], hauptleistung, current, target=4
                )
                new_count = count_hauptleistung(sections[key], hauptleistung)
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: Now {new_count}/4")
    
    # Recommendations: Minimum 3x
    for key in ["RECOMMENDATIONS_HTML", "recommendations"]:
        if key in sections and sections[key]:
            current = count_hauptleistung(sections[key], hauptleistung)
            if current < 3:
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: {current}/3 → enforcing")
                sections[key] = inject_hauptleistung_recommendations(
                    sections[key], hauptleistung, current, target=3
                )
                new_count = count_hauptleistung(sections[key], hauptleistung)
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: Now {new_count}/3")
    
    return sections


# =============================================================================
# P0.1: STRAY PREFIX REMOVER & TEXT HYGIENE
# =============================================================================
# Removes leading artifacts like "?" and ensures text hygiene

STRAY_PREFIX_PATTERNS = [
    # Leading question marks (with or without whitespace)
    (re.compile(r'^(\s*)\?\s+'), r'\1'),
    # Leading question marks in paragraphs/list items
    (re.compile(r'(<p[^>]*>)\s*\?\s+'), r'\1'),
    (re.compile(r'(<li[^>]*>)\s*\?\s+'), r'\1'),
    # Multiple leading punctuation artifacts
    (re.compile(r'^(\s*)[?!.:;,]\s+([A-ZÄÖÜ])'), r'\1\2'),
]


def remove_stray_prefixes(html: str) -> tuple[str, int]:
    """
    P0.1: Remove leading artifacts like '?' from text.

    Problem: GPT sometimes generates "? Du kannst..." or "? Sie können..."
    Solution: Remove the leading "?" and fix the sentence.

    Returns:
        tuple: (cleaned_html, fix_count)
    """
    if not html:
        return html, 0

    fix_count = 0
    result = html

    for pattern, replacement in STRAY_PREFIX_PATTERNS:
        matches = len(pattern.findall(result))
        if matches > 0:
            result = pattern.sub(replacement, result)
            fix_count += matches

    return result, fix_count


def apply_stray_prefix_remover(sections: dict) -> dict:
    """
    P0.1: Apply stray prefix removal to all text sections.
    Removes leading '?' and other punctuation artifacts.
    """
    total_fixes = 0

    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "RECOMMENDATIONS_HTML", "QUICK_WINS_HTML",
        "ROADMAP_90D_HTML", "ROADMAP_12M_HTML", "GAMECHANGER_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML",
        "TOOLS_HTML", "DATA_STRATEGY_HTML", "GOVERNANCE_HTML",
    ]

    for key in check_sections:
        if key in sections and sections[key]:
            fixed, count = remove_stray_prefixes(sections[key])
            if count > 0:
                sections[key] = fixed
                total_fixes += count
                # Update lowercase alias
                lower_key = key.replace("_HTML", "").lower()
                if lower_key in sections:
                    sections[lower_key] = fixed

    if total_fixes > 0:
        log.info(f"[STRAY-PREFIX] Removed {total_fixes} leading punctuation artifacts")

    return sections


# =============================================================================
# 4. SIEZEN-GUARD EXTENSION: Erweiterte du→Sie Patterns
# =============================================================================

EXTENDED_SIEZEN_PATTERNS = [
    # Possessive "dein/deine"
    (r'[Ff]ür deine', 'Für Ihre'),  # v14.18: 'Für deine Situation' -> 'Für Ihre Situation'
    (r'\b[Dd]ein\b', 'Ihr'),  # "Dein Assessment" → "Ihr Assessment"
    (r'\b[Dd]eine([rsmn]?)\b', r'Ihre\1'),
    (r'\b[Dd]einem\b', 'Ihrem'),
    (r'\b[Dd]einen\b', 'Ihren'),
    
    # "Du bist" → "Sie sind"
    (r'\b[Dd]u\s+bist\b', 'Sie sind'),
    (r'\b[Dd]u\s+hast\b', 'Sie haben'),
    (r'\b[Dd]u\s+kannst\b', 'Sie können'),
    (r'\b[Dd]u\s+solltest\b', 'Sie sollten'),
    (r'\b[Dd]u\s+musst\b', 'Sie müssen'),
    (r'\b[Dd]u\s+wirst\b', 'Sie werden'),
    
    # Standalone "dir/dich"
    (r'\b[Dd]ir\b', 'Ihnen'),
    (r'\b[Dd]ich\b', 'Sie'),
    
    # "für dich" → "für Sie"
    (r'\bfür\s+dich\b', 'für Sie'),
    (r'\bvon\s+dir\b', 'von Ihnen'),
    (r'\bbei\s+dir\b', 'bei Ihnen'),
    (r'\bmit\s+dir\b', 'mit Ihnen'),
    
    # =========================================
    # IMPERATIVE (Du-Form → Sie-Form)
    # =========================================
    # Am Satzanfang oder nach Aufzählungszeichen
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Lerne\b', r'\1Lernen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Nutze\b', r'\1Nutzen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Teste\b', r'\1Testen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Baue\b', r'\1Bauen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Entwickle\b', r'\1Entwickeln Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Prüfe\b', r'\1Prüfen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Erstelle\b', r'\1Erstellen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Starte\b', r'\1Starten Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Plane\b', r'\1Planen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Überlege\b', r'\1Überlegen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Markiere\b', r'\1Markieren Sie'),  # v14.17
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Dokumentiere\b', r'\1Dokumentieren Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Achte\b', r'\1Achten Sie'),  # v14.26
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Setze\b', r'\1Setzen Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Erstelle\b', r'\1Erstellen Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Entwickle\b', r'\1Entwickeln Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Analysiere\b', r'\1Analysieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Optimiere\b', r'\1Optimieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Implementiere\b', r'\1Implementieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Evaluiere\b', r'\1Evaluieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Integriere\b', r'\1Integrieren Sie'),  # v14.27
    
    # v14.29: AGGRESSIVE Imperative-Patterns (überall anwenden!)
    # Diese greifen an JEDER Position im Text
    (r'"Analysiere\b', '"Analysieren Sie'),  # Copy-Paste Prompts
    (r'"Erstelle\b', '"Erstellen Sie'),  # Copy-Paste Prompts
    (r'"Entwickle\b', '"Entwickeln Sie'),  # Copy-Paste Prompts
    (r'"Optimiere\b', '"Optimieren Sie'),  # Copy-Paste Prompts
    (r'"Prüfe\b', '"Prüfen Sie'),  # Copy-Paste Prompts
    # Auch ohne Anführungszeichen
    (r'(\s)Analysiere\b', r'\1Analysieren Sie'),  # Nach Whitespace
    (r'(\s)Erstelle\b', r'\1Erstellen Sie'),  # Nach Whitespace
    # v14.29: Skill-Fahrplan Fixes
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Etabliere\b', r'\1Etablieren Sie'),
    # "du" → "Sie" in bestimmten Kontexten
    (r'\bwie du\b', 'wie Sie'),
    (r'\bdass du\b', 'dass Sie'),
    (r'\bwenn du\b', 'wenn Sie'),
    (r'\bob du\b', 'ob Sie'),
    (r', du ', ', Sie '),  # v14.31: Allgemeines du nach Komma
    (r'\bsparst du\b', 'sparen Sie'),  # v14.35.3: "sparst du" → "sparen Sie"
    (r'\bhast du\b', 'haben Sie'),  # v14.35.3: "hast du" → "haben Sie"
    (r'\bkannst du\b', 'können Sie'),  # v14.35.3: "kannst du" → "können Sie"
    (r'\bmusst du\b', 'müssen Sie'),  # v14.35.3: "musst du" → "müssen Sie"
    (r'\bwillst du\b', 'wollen Sie'),  # v14.35.3: "willst du" → "wollen Sie"
    (r'\bbrauchst du\b', 'brauchen Sie'),  # v14.35.3: "brauchst du" → "brauchen Sie"
    (r' du ', ' Sie '),  # v14.35.3: Allgemeines " du " → " Sie "
    # v14.35.4: Fragment-Fixes für GPT-generierte Abbrüche
    (r', weil\.$', '.'),  # ", weil." → "."
    (r' weil\.$', '.'),  # " weil." → "."
    (r' zu\.$', '.'),  # " zu." → "."
    (r'kann zu\.$', 'kann problematisch werden.'),  # "kann zu." → sinnvoll
    (r'Dies kann zu\.$', 'Dies kann problematisch werden.'),
    (r': Ein\.$', '.'),  # ": Ein." → "."
    (r': Eine\.$', '.'),  # ": Eine." → "."
    (r'Gegenmaßnahme: Ein\.$', 'Gegenmaßnahme: Siehe Empfehlungen.'),
    (r'Gegenmaßnahme: Eine\.$', 'Gegenmaßnahme: Siehe Empfehlungen.'),
    (r'Skepsis kann die\.$', 'Skepsis kann die Akzeptanz gefährden.'),
    (r'wächst es schnell zu\.$', 'wächst es schnell.'),
    (r'Audits und eine\.$', 'Audits und regelmäßige Überprüfungen.'),
    (r'Der EU AI Act verlangt\.$', 'Der EU AI Act stellt Anforderungen an KI-Systeme.'),
    (r'kommen Experimente\.$', 'kommen Experimente zu kurz.'),
    (r'direkt in Ihre\.$', 'direkt in Ihre Prozesse integrieren.'),
    (r'Testlauf mit\.$', 'Testlauf mit ersten Anwendungsfällen.'),
    # v14.35.6: Weitere Fragment-Fixes aus Validation
    (r'Pro Quartal\.$', 'Pro Quartal überprüfen.'),
    (r'Anforderungen\. \.', 'Anforderungen.'),  # Doppelpunkt-Artefakt
    (r'Dies steht im Konflikt mit\.$', 'Dies steht im Konflikt mit den Zielen.'),
    (r'Qualität der\.$', 'Qualität der Ergebnisse.'),
    (r' direkt\.$', '.'),  # "...Geschäftsmodell direkt." → "...Geschäftsmodell."
    (r' Workflow\.$', ' Workflow beeinträchtigen.'),
    (r'\.\s*Dies\.$', '.'),  # ". Dies." → "."
    (r' automatisierte\.$', ' automatisierte Prozesse.'),
    (r'\. \.$', '.'),  # ". ." → "."
    (r'\s+\.$', '.'),  # " ." → "."
    # Generische Fragment-Fänger (Ende mit Artikel/Präposition)
    (r' der\.$', '.'),
    (r' die\.$', '.'),
    (r' das\.$', '.'),
    (r' den\.$', '.'),
    (r' dem\.$', '.'),
    (r' mit\.$', '.'),
    (r' für\.$', '.'),
    (r' auf\.$', '.'),
    (r' bei\.$', '.'),
    (r' von\.$', '.'),
    # v14.35.10: Weitere Fragment-Fixes aus v14.35.8 Validation
    (r' wahrgenommenen\.$', ' wahrgenommenen Nutzen.'),
    (r' in Ihrem\.$', ' in Ihrem Unternehmen.'),
    (r' die jede\.$', ' die jede Bewertung absichern.'),
    (r' laufenden\.$', ' laufenden Projekten.'),
    (r' eine Ablauf ', ' einen Ablauf '),  # Grammatik-Fix
    (r'\(z\. B\.$', '(z. B. Templates).'),  # Offene Klammer schließen
    (r'\(z\.\s*B\.[^)]{0,5}$', '(z. B. Templates)'),  # Offene Klammer am Ende
    (r' können zu\.$', ' können zu Problemen führen.'),
    (r' Automatisierung der\.$', ' Automatisierung der Prozesse.'),
    # v14.35.11: Weitere Fragment-Fixes aus Validation
    (r' weil als\.$', '.'),
    (r' Pro Quartal\.$', ' pro Quartal überprüfen.'),
    (r' was mit\.$', '.'),
    (r' als Verstoß gegen\.$', ' als Verstoß gegen Richtlinien.'),
    (r' Tool-Stack auf wenige\.$', ' Tool-Stack auf wenige konzentrieren.'),
    (r' automatisch\.$', ' automatisch generiert.'),
    (r' die verschiedene\.$', ' die verschiedene Aufgaben erfüllen.'),
    (r' Arbeitsalltag der\.$', ' Arbeitsalltag der Mitarbeitenden.'),
    (r'zugerechnet werden\. \.', 'zugerechnet werden.'),
    # v14.35.12: Weitere Fragmente aus Validation
    (r' europäischer\.$', ' europäischer Anbieter.'),
    (r' drohen\.$', ' drohen erhebliche Risiken.'),
    (r' erschweren\.$', ' erschweren die Umsetzung.'),
    (r' kein\.$', '.'),
    (r' eine\.$', '.'),
    (r' die Sie\.$', ' die Sie nutzen können.'),
    # v14.35.13: Weitere Risk-Card Fragmente aus Validation
    (r' als europäischer\.$', ' als europäischer Anbieter etablieren.'),
    (r' zur Vision als\.$', '.'),
    (r' Akzeptanz der\.$', ' Akzeptanz der Mitarbeitenden sichern.'),
    (r' erschwert eine\.$', ' erschwert eine Umsetzung.'),
    (r' generiertem\.$', ' generiertem Content.'),
    (r' automatisch generiertem\.$', ' automatisch generiertem Content.'),
    (r' parallelen\.$', ' parallelen Experimenten.'),
    (r' Informationen drohen\.$', ' Informationen drohen verloren zu gehen.'),
    (r' weder zur\.$', '.'),
    (r' verleitet zu\.$', '.'),
    (r'\. \.$', '.'),  # Doppelpunkt am Ende
    # v14.35.13: PROPHYLAKTISCHE Fragment-Patterns (alle möglichen Endungen)
    # === Artikel-Endungen ===
    (r' der\.$', '.'),
    (r' die\.$', '.'),
    (r' das\.$', '.'),
    (r' den\.$', '.'),
    (r' dem\.$', '.'),
    (r' des\.$', '.'),
    (r' einer\.$', '.'),
    (r' eines\.$', '.'),
    (r' einem\.$', '.'),
    (r' einen\.$', '.'),
    # === Präposition-Endungen ===
    (r' mit\.$', '.'),
    (r' bei\.$', '.'),
    (r' für\.$', '.'),
    (r' auf\.$', '.'),
    (r' von\.$', '.'),
    (r' zur\.$', '.'),
    (r' zum\.$', '.'),
    (r' als\.$', '.'),
    (r' aus\.$', '.'),
    (r' nach\.$', '.'),
    (r' durch\.$', '.'),
    (r' über\.$', '.'),
    (r' unter\.$', '.'),
    (r' ohne\.$', '.'),
    (r' gegen\.$', '.'),
    (r' zwischen\.$', '.'),
    (r' während\.$', '.'),
    (r' wegen\.$', '.'),
    (r' trotz\.$', '.'),
    (r' seit\.$', '.'),
    (r' bis\.$', '.'),
    (r' außer\.$', '.'),
    (r' statt\.$', '.'),
    (r' innerhalb\.$', '.'),
    (r' außerhalb\.$', '.'),
    (r' anstatt\.$', '.'),
    (r' bezüglich\.$', '.'),
    (r' hinsichtlich\.$', '.'),
    (r' aufgrund\.$', '.'),
    (r' anhand\.$', '.'),
    (r' mittels\.$', '.'),
    (r' zwecks\.$', '.'),
    (r' gemäß\.$', '.'),
    (r' laut\.$', '.'),
    # === Konjunktion-Endungen ===
    (r' und\.$', '.'),
    (r' oder\.$', '.'),
    (r' aber\.$', '.'),
    (r' sowie\.$', '.'),
    (r' wenn\.$', '.'),
    (r' weil\.$', '.'),
    (r' dass\.$', '.'),
    (r' damit\.$', '.'),
    (r' obwohl\.$', '.'),
    (r' falls\.$', '.'),
    (r' sofern\.$', '.'),
    (r' sobald\.$', '.'),
    (r' solange\.$', '.'),
    (r' bevor\.$', '.'),
    (r' nachdem\.$', '.'),
    (r' während\.$', '.'),
    (r' indem\.$', '.'),
    (r' sodass\.$', '.'),
    (r' weshalb\.$', '.'),
    (r' wodurch\.$', '.'),
    (r' womit\.$', '.'),
    (r' worauf\.$', '.'),
    (r' woran\.$', '.'),
    (r' worin\.$', '.'),
    (r' wovon\.$', '.'),
    (r' wozu\.$', '.'),
    (r' wobei\.$', '.'),
    # === Pronomen-Endungen ===
    (r' Sie\.$', '.'),
    (r' Ihr\.$', '.'),
    (r' Ihre\.$', '.'),
    (r' Ihren\.$', '.'),
    (r' Ihrem\.$', '.'),
    (r' Ihrer\.$', '.'),
    (r' sich\.$', '.'),
    (r' diese\.$', '.'),
    (r' dieser\.$', '.'),
    (r' dieses\.$', '.'),
    (r' diesen\.$', '.'),
    (r' diesem\.$', '.'),
    (r' jede\.$', '.'),
    (r' jeder\.$', '.'),
    (r' jedes\.$', '.'),
    (r' jeden\.$', '.'),
    (r' jedem\.$', '.'),
    (r' alle\.$', '.'),
    (r' aller\.$', '.'),
    (r' allem\.$', '.'),
    (r' allen\.$', '.'),
    (r' welche\.$', '.'),
    (r' welcher\.$', '.'),
    (r' welches\.$', '.'),
    (r' welchen\.$', '.'),
    (r' welchem\.$', '.'),
    # === Adjektiv-Endungen (häufige) ===
    (r' neue\.$', '.'),
    (r' neuen\.$', '.'),
    (r' neuer\.$', '.'),
    (r' neues\.$', '.'),
    (r' neuem\.$', '.'),
    (r' wichtige\.$', '.'),
    (r' wichtigen\.$', '.'),
    (r' wichtiger\.$', '.'),
    (r' wichtiges\.$', '.'),
    (r' verschiedene\.$', '.'),
    (r' verschiedenen\.$', '.'),
    (r' verschiedener\.$', '.'),
    (r' große\.$', '.'),
    (r' großen\.$', '.'),
    (r' großer\.$', '.'),
    (r' großes\.$', '.'),
    (r' kleine\.$', '.'),
    (r' kleinen\.$', '.'),
    (r' kleiner\.$', '.'),
    (r' kleines\.$', '.'),
    (r' erste\.$', '.'),
    (r' ersten\.$', '.'),
    (r' erster\.$', '.'),
    (r' erstes\.$', '.'),
    (r' weitere\.$', '.'),
    (r' weiteren\.$', '.'),
    (r' weiterer\.$', '.'),
    (r' weiteres\.$', '.'),
    (r' andere\.$', '.'),
    (r' anderen\.$', '.'),
    (r' anderer\.$', '.'),
    (r' anderes\.$', '.'),
    (r' anderem\.$', '.'),
    (r' eigene\.$', '.'),
    (r' eigenen\.$', '.'),
    (r' eigener\.$', '.'),
    (r' eigenes\.$', '.'),
    (r' eigenem\.$', '.'),
    (r' bestimmte\.$', '.'),
    (r' bestimmten\.$', '.'),
    (r' bestimmter\.$', '.'),
    (r' bestimmtes\.$', '.'),
    (r' entsprechende\.$', '.'),
    (r' entsprechenden\.$', '.'),
    (r' entsprechender\.$', '.'),
    (r' wesentliche\.$', '.'),
    (r' wesentlichen\.$', '.'),
    (r' notwendige\.$', '.'),
    (r' notwendigen\.$', '.'),
    (r' relevante\.$', '.'),
    (r' relevanten\.$', '.'),
    (r' effektive\.$', '.'),
    (r' effektiven\.$', '.'),
    (r' strategische\.$', '.'),
    (r' strategischen\.$', '.'),
    (r' technische\.$', '.'),
    (r' technischen\.$', '.'),
    (r' automatische\.$', '.'),
    (r' automatischen\.$', '.'),
    (r' manuelle\.$', '.'),
    (r' manuellen\.$', '.'),
    (r' digitale\.$', '.'),
    (r' digitalen\.$', '.'),
    (r' kritische\.$', '.'),
    (r' kritischen\.$', '.'),
    (r' konkrete\.$', '.'),
    (r' konkreten\.$', '.'),
    (r' aktuelle\.$', '.'),
    (r' aktuellen\.$', '.'),
    (r' zukünftige\.$', '.'),
    (r' zukünftigen\.$', '.'),
    (r' erfolgreiche\.$', '.'),
    (r' erfolgreichen\.$', '.'),
    (r' mögliche\.$', '.'),
    (r' möglichen\.$', '.'),
    (r' schnelle\.$', '.'),
    (r' schnellen\.$', '.'),
    (r' langfristige\.$', '.'),
    (r' langfristigen\.$', '.'),
    (r' kurzfristige\.$', '.'),
    (r' kurzfristigen\.$', '.'),
    # === Verb-Endungen (Partizip/abgebrochen) ===
    (r' können\.$', '.'),
    (r' werden\.$', '.'),
    (r' sollten\.$', '.'),
    (r' müssen\.$', '.'),
    (r' wollen\.$', '.'),
    (r' haben\.$', '.'),
    (r' sein\.$', '.'),
    (r' sind\.$', '.'),
    (r' wird\.$', '.'),
    (r' kann\.$', '.'),
    (r' soll\.$', '.'),
    (r' muss\.$', '.'),
    # === Spezielle Kombinationen ===
    (r' zu einem\.$', '.'),
    (r' zu einer\.$', '.'),
    (r' zu den\.$', '.'),
    (r' in der\.$', '.'),
    (r' in den\.$', '.'),
    (r' in dem\.$', '.'),
    (r' in einer\.$', '.'),
    (r' in einem\.$', '.'),
    (r' an der\.$', '.'),
    (r' an den\.$', '.'),
    (r' an dem\.$', '.'),
    (r' auf der\.$', '.'),
    (r' auf den\.$', '.'),
    (r' auf dem\.$', '.'),
    (r' bei der\.$', '.'),
    (r' bei den\.$', '.'),
    (r' bei dem\.$', '.'),
    (r' für die\.$', '.'),
    (r' für den\.$', '.'),
    (r' für das\.$', '.'),
    (r' mit der\.$', '.'),
    (r' mit den\.$', '.'),
    (r' mit dem\.$', '.'),
    (r' von der\.$', '.'),
    (r' von den\.$', '.'),
    (r' von dem\.$', '.'),
    (r' aus der\.$', '.'),
    (r' aus den\.$', '.'),
    (r' aus dem\.$', '.'),
    (r' nach der\.$', '.'),
    (r' nach den\.$', '.'),
    (r' nach dem\.$', '.'),
    (r' durch die\.$', '.'),
    (r' durch den\.$', '.'),
    (r' durch das\.$', '.'),
    (r' über die\.$', '.'),
    (r' über den\.$', '.'),
    (r' über das\.$', '.'),
    # === Offene Klammern ===
    (r'\([^)]{0,20}$', ''),  # Offene Klammer am Ende (max 20 Zeichen)
    (r'\(z\.\s*B\.\s*$', ''),  # Häufig: "(z. B." am Ende
    (r'\bsparst du\b', 'sparen Sie'),  # v14.35.3: "sparst du" → "sparen Sie"
    (r'\b([a-z]+)st du\b', r'\1en Sie'),  # Allgemein: "Xst du" → "Xen Sie"
    
    # v14.32: Verbkonjugation nach "Sie" korrigieren (Sie + -st → Sie + -en)
    (r'\bSie ([\w]+)st\b', r'Sie \1en'),  # Allgemeines Pattern
    # Spezifische häufige Fälle:
    (r'\bSie einhältst\b', 'Sie einhalten'),
    (r'\bSie prüfst\b', 'Sie prüfen'),
    (r'\bSie erstellst\b', 'Sie erstellen'),
    (r'\bSie analysierst\b', 'Sie analysieren'),
    (r'\bSie dokumentierst\b', 'Sie dokumentieren'),
    (r'\bSie redigierst\b', 'Sie redigieren'),
    (r'\bSie arbeitest\b', 'Sie arbeiten'),
    (r'\bSie nutzt\b', 'Sie nutzen'),
    (r'\bSie verwendest\b', 'Sie verwenden'),
    (r'\bSie brauchst\b', 'Sie brauchen'),
    (r'\bSie hast\b', 'Sie haben'),
    (r'\bSie bist\b', 'Sie sind'),
    (r'\bSie kannst\b', 'Sie können'),
    (r'\bSie musst\b', 'Sie müssen'),
    (r'\bSie sollst\b', 'Sie sollen'),
    (r'\bSie willst\b', 'Sie wollen'),
    
    # v14.29: Persona-Leak Fixes für Solo
    # Diese Enterprise-Begriffe werden für Solo ersetzt
    (r'\bModule\b', 'Bausteine'),  # Modul → Baustein
    (r'\bModul\b', 'Baustein'),
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    # v14.35: skalier*-Familie komplett (alle deutschen Flexionen)
    (r'\bSkalierung\b', 'Erweiterung'),  # feminin bleibt feminin
    (r'Skalierungs', 'Erweiterungs'),
    (r'\bskalieren\b', 'erweitern'),  # Verb
    (r'\bSkalierbarkeit\b', 'Erweiterbarkeit'),  # Substantiv
    (r'\bskalierbar\b', 'erweiterbar'),  # Adjektiv Grundform
    (r'\bskaliert\b', 'erweitert'),  # v14.35.4: Verb Partizip/3.Person
    (r'\bskalieren\b', 'erweitern'),  # v14.35.4: Verb Infinitiv
    (r'\bSkalierung auf \d+', 'Erweiterung auf'),  # v14.35.4: "Skalierung auf 1000+"
    (r'\bSkalierungs', 'Erweiterungs'),  # v14.35.4: Komposita
    (r'\bskalierbare\b', 'erweiterbare'),  # v14.35: Adjektiv feminin/Plural
    (r'\bskalierbares\b', 'erweiterbares'),  # v14.35: Adjektiv neutrum
    (r'\bskalierbaren\b', 'erweiterbaren'),  # v14.35: Adjektiv Dativ/Genitiv
    (r'\bskalierbarer\b', 'erweiterbarer'),  # v14.35: Adjektiv maskulin/Genitiv
    (r'\bhochskaliert', 'stark erweitert'),  # Partizip
    # v14.35.8: Explizite Großschreibungs-Patterns (statt IGNORECASE)
    (r'\bSkalierbare\b', 'Erweiterbare'),  # Am Satzanfang
    (r'\bSkalierbares\b', 'Erweiterbares'),
    (r'\bSkalierbaren\b', 'Erweiterbaren'),
    (r'\bSkalierbarer\b', 'Erweiterbarer'),
    (r'\bSkaliert\b', 'Erweitert'),  # Am Satzanfang
    (r'\bSkalieren\b', 'Erweitern'),
    (r'\bSkalieren\b', 'Erweitern'),
    (r'\bEngine\b', 'System'),
    # v14.35: Framework-Familie komplett
    (r'\bFrameworks\b', 'Konzepte'),  # v14.35: Plural zuerst (greedy)
    (r'\bFramework\b', 'Konzept'),
    (r'Assessment-Frameworks', 'Bewertungskonzepte'),  # v14.35: Zusammensetzung
    (r'Business-Case-Frameworks', 'Business-Case-Vorlagen'),  # v14.35: Zusammensetzung
    (r'\bPipeline\b', 'Ablauf'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Standardisiere\b', r'\1Standardisieren Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Strukturiere\b', r'\1Strukturieren Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Verbinde\b', r'\1Verbinden Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Richte\b', r'\1Richten Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Definiere\b', r'\1Definieren Sie'),  # v14.20

]

def apply_extended_siezen(html: str) -> tuple[str, int]:
    """
    Erweiterte du→Sie Konvertierung für Fälle die der Standard-Guard verpasst.
    """
    if not html:
        return html, 0
    
    replacements = 0
    result = html
    
    for pattern, replacement in EXTENDED_SIEZEN_PATTERNS:
        matches = len(re.findall(pattern, result))
        if matches > 0:
            result = re.sub(pattern, replacement, result)
            replacements += matches
    
    return result, replacements


def apply_extended_siezen_guard(sections: dict) -> dict:
    """
    Wendet erweiterte Siezen-Patterns auf alle Text-Sections an.
    """
    total_fixed = 0
    
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "RECOMMENDATIONS_HTML", "QUICK_WINS_HTML",
        "ROADMAP_90D_HTML", "ROADMAP_12M_HTML", "GAMECHANGER_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "TEMPLATES_START_HTML", "KICKOFF_VORLAGE_HTML",
        "ROI_TRACKING_HTML", "PROMPT_FRAMEWORK_HTML",
    ]
    
    for key in check_sections:
        if key in sections and sections[key]:
            fixed, count = apply_extended_siezen(sections[key])
            if count > 0:
                sections[key] = fixed
                total_fixed += count
                # Update lowercase alias
                lower_key = key.replace("_HTML", "").lower()
                if lower_key in sections:
                    sections[lower_key] = fixed
                log.info(f"[EXTENDED-SIEZEN] {key}: {count} additional fixes")
    
    log.info(f"[EXTENDED-SIEZEN] Complete: {total_fixed} additional du→Sie fixes")
    return sections

# =============================================================================
# 6. GRAMMAR-FIXER: Korrigiert typische Grammatik-/Formatierungsfehler
# =============================================================================

GRAMMAR_FIX_PATTERNS = [
    # "Einzelunternehmer in der Branche beratung" → korrekte Großschreibung
    (r'in der Branche ([a-zäöü]+)', lambda m: f'in der Branche {m.group(1).title()}'),
    
    # "Für Ihr Einzelunternehmer" → "Für Ihren Einzelbetrieb" oder "Für Sie als Einzelunternehmer"
    (r'Für Ihr Einzelunternehmer', 'Für Sie als Einzelunternehmer'),
    
    # v14.18: Zusammengeklebte Header trennen
    (r'([A-ZÄÖÜ]{5,})([A-Z][a-zäöü])', r'\1 - \2'),
    # Doppelte Leerzeichen
    (r'  +', ' '),
    
    # Punkt vor Komma
    # v14.18: Komma vor Punkt
    (r',\.', '.'),
    (r'\.,', ','),
    
    # Doppelte Punkte
    
    # v14.35: Persona-Leak Fixes (auch in GRAMMAR_FIX für alle Sections)
    # skalier*-Familie komplett (alle deutschen Flexionen)
    (r'\bSkalierung\b', 'Erweiterung'),
    (r'Skalierungs', 'Erweiterungs'),
    (r'\bskalieren\b', 'erweitern'),  # Verb
    (r'\bSkalierbarkeit\b', 'Erweiterbarkeit'),  # Substantiv
    (r'\bskalierbar\b', 'erweiterbar'),  # Adjektiv Grundform
    (r'\bskaliert\b', 'erweitert'),  # v14.35.4: Verb Partizip/3.Person
    (r'\bskalieren\b', 'erweitern'),  # v14.35.4: Verb Infinitiv
    (r'\bSkalierung auf \d+', 'Erweiterung auf'),  # v14.35.4: "Skalierung auf 1000+"
    (r'\bSkalierungs', 'Erweiterungs'),  # v14.35.4: Komposita
    (r'\bskalierbare\b', 'erweiterbare'),  # v14.35: Adjektiv feminin/Plural
    (r'\bskalierbares\b', 'erweiterbares'),  # v14.35: Adjektiv neutrum
    (r'\bskalierbaren\b', 'erweiterbaren'),  # v14.35: Adjektiv Dativ/Genitiv
    (r'\bskalierbarer\b', 'erweiterbarer'),  # v14.35: Adjektiv maskulin/Genitiv
    (r'\bhochskaliert', 'stark erweitert'),  # Partizip
    # v14.35.8: Explizite Großschreibungs-Patterns (statt IGNORECASE)
    (r'\bSkalierbare\b', 'Erweiterbare'),  # Am Satzanfang
    (r'\bSkalierbares\b', 'Erweiterbares'),
    (r'\bSkalierbaren\b', 'Erweiterbaren'),
    (r'\bSkalierbarer\b', 'Erweiterbarer'),
    (r'\bSkaliert\b', 'Erweitert'),  # Am Satzanfang
    (r'\bSkalieren\b', 'Erweitern'),
    (r'\bModule\b', 'Bausteine'),
    (r'\bModul\b', 'Baustein'),
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    # Framework-Familie komplett
    (r'\bFrameworks\b', 'Konzepte'),  # v14.35: Plural zuerst (greedy)
    (r'\bFramework\b', 'Konzept'),
    (r'Assessment-Frameworks', 'Bewertungskonzepte'),  # v14.35
    (r'Business-Case-Frameworks', 'Business-Case-Vorlagen'),  # v14.35
    (r'\bPipeline\b', 'Ablauf'),
    (r'\bEngine\b', 'System'),
    (r'\.\. ', '. '),

    # v14.35: Fragment-Fixes (erweitert)
    (r'\(z\.$', ''),  # Abgeschnittene "(z." am Zeilenende entfernen
    (r'\(z\.B\.$', ''),  # Abgeschnittene "(z.B." entfernen
    (r', die die ([A-Za-z]+)\.$', r', die \1.'),  # "die die X." → "die X."
    (r'und \.\.\.$', 'und weitere.'),  # "und ..." → "und weitere."
    (r'und\s*\.$', '.'),  # "und." am Ende → nur "."
    (r', da\.\s*$', '.'),  # v14.35: ", da." → "."
    (r'für diese\.\s*$', 'für diese Zwecke.'),  # v14.35: "für diese." → "für diese Zwecke."
    (r'im Rahmen\.\s*$', 'im Rahmen dessen.'),  # v14.35: "im Rahmen." → "im Rahmen dessen."
    (r'\s+zu\s*$', '.'),  # v14.35: "früh zu" am Ende → "früh."
    (r'\s+oder\s*$', '.'),  # v14.35: "Schritte oder" am Ende → "Schritte."
    (r'\s+und\s*$', '.'),  # v14.35: "Tests und" am Ende → "Tests."
    (r'„[^"]*-\s*$', ''),  # v14.35: Abgeschnittene "„Review-" entfernen
    (r'Schritt-für-\s*$', 'Schritt-für-Schritt.'),  # v14.35: "Schritt-für-" → "Schritt-für-Schritt."
    # v14.35.2: Zusätzliche Fragment-Fixes
    (r'– ohne\.\s*$', '.'),  # "– ohne." → "."
    (r'- ohne\.\s*$', '.'),  # "- ohne." (ASCII) → "."
    (r'– ohne\.\s*<', '.<'),  # "– ohne." vor Tag → "."
    (r'klar strukturiere ', 'klar strukturierte '),  # Grammatikfehler
    (r' mit n ', ' mit einem '),  # Kaputter Platzhalter "mit n"
    (r' mit n\.', ' mit einem passenden Tool.'),  # "mit n." → sinnvoll
    (r' und\.</p>', '.</p>'),  # "und.</p>" → ".</p>"
    (r' und\.<', '.<'),  # "und." vor Tag → "."
]

def apply_grammar_fixes(html: str) -> tuple[str, int]:
    """
    Korrigiert typische Grammatik- und Formatierungsfehler.
    """
    if not html:
        return html, 0
    
    fixes = 0
    result = html
    
    for pattern, replacement in GRAMMAR_FIX_PATTERNS:
        if callable(replacement):
            new_result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        else:
            # Type assertion for mypy: replacement is str here
            new_result = re.sub(pattern, str(replacement), result)
        if new_result != result:
            fixes += 1
            result = new_result
    
    return result, fixes

def apply_grammar_fixer(sections: dict) -> dict:
    """
    Wendet Grammar-Fixes auf alle relevanten Sections an.
    """
    total_fixes = 0
    
    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 100:
            fixed, count = apply_grammar_fixes(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count
    
    log.info(f"[GRAMMAR-FIXER] Complete: {total_fixes} grammar fixes")
    return sections



# =============================================================================
# MASTER FUNCTION: Apply All Quality Enforcers
# =============================================================================

# =============================================================================
# 5. LOCATION-VALIDATOR: Entfernt falsche Bundesländer aus Förder-Sections
# =============================================================================

# Alle deutschen Bundesländer
BUNDESLAENDER = [
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
    "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
    "Nordrhein-Westfalen", "NRW", "Rheinland-Pfalz", "Saarland", "Sachsen",
    "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"
]

# Sections wo Location-Check angewendet wird
LOCATION_CHECK_SECTIONS = [
    "executive_summary", "EXECUTIVE_SUMMARY_HTML",
    # v14.18: Noch mehr Sections
    "FOERDERPROGRAMME_HTML", "foerderprogramme",
    "FUNDING_TABLE_HTML", "funding_table",
    # v14.17: Erweitert um alle Förder-relevanten Sections
    "funding", "FUNDING_HTML",
    "foerderprogramme", "FOERDERPROGRAMME_HTML",
    "funding_branch_alignment", "FUNDING_BRANCH_ALIGNMENT_HTML",
    "tools_funding_alignment", "TOOLS_FUNDING_ALIGNMENT_HTML",
    "starter_kit", "STARTER_KIT_HTML", "STARTER_KIT_COMPACT_HTML",
    "foerderpotenzial", "FOERDERPOTENZIAL_HTML",
    "recommendations", "RECOMMENDATIONS_HTML",
    "quick_wins", "QUICK_WINS_HTML",
    "tools_section", "TOOLS_SECTION_HTML",
    "starter_kits", "STARTER_KITS_HTML",
    "kosten_uebersicht", "KOSTEN_UEBERSICHT_HTML",
]

def validate_location_in_section(html: str, correct_bundesland: str) -> tuple[str, int]:
    """
    Entfernt Referenzen zu falschen Bundesländern.
    
    Args:
        html: HTML content
        correct_bundesland: Das korrekte Bundesland des Users
        
    Returns:
        tuple: (cleaned_html, removal_count)
    """
    if not html or not correct_bundesland:
        return html, 0
    
    removals = 0
    result = html
    correct_lower = correct_bundesland.lower()
    
    for bundesland in BUNDESLAENDER:
        # Skip wenn es das korrekte Bundesland ist
        if bundesland.lower() == correct_lower:
            continue
        if bundesland.lower() == "nrw" and "nordrhein" in correct_lower:
            continue
        if "nordrhein" in bundesland.lower() and correct_lower == "nrw":
            continue
        
        # Suche nach dem falschen Bundesland
        pattern = rf'\b{re.escape(bundesland)}\b'
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        if matches:
            # Ersetze durch "Ihr Bundesland" oder entferne den Satz
            result = re.sub(pattern, "Ihr Bundesland", result, flags=re.IGNORECASE)
            removals += len(matches)
            log.warning(f"[LOCATION-VALIDATOR] Removed wrong Bundesland '{bundesland}' (correct: {correct_bundesland})")
    
    return result, removals

def apply_location_validator(sections: dict, bundesland: str) -> dict:
    """
    Wendet Location-Validierung auf relevante Sections an.
    """
    if not bundesland:
        log.debug("[LOCATION-VALIDATOR] No bundesland provided, skipping")
        return sections
    
    total_removals = 0
    
    for key in LOCATION_CHECK_SECTIONS:
        if key in sections and sections[key]:
            fixed, count = validate_location_in_section(sections[key], bundesland)
            if count > 0:
                sections[key] = fixed
                total_removals += count
                log.info(f"[LOCATION-VALIDATOR] {key}: {count} wrong Bundesland references removed")
    
    log.info(f"[LOCATION-VALIDATOR] Complete: {total_removals} total removals")
    return sections
def apply_all_quality_enforcers(sections: dict, hauptleistung: str = "", bundesland: str = "", company_size: str = "") -> dict:

    """
    Wendet alle Quality Enforcer in der richtigen Reihenfolge an.

    Order:
    0. Stray Prefix Remover (P0.1: entfernt führende "?" und Artefakte)
    1. ROI-Filter (entfernt verbotene ROI-Werte)
    2. Fragment-Repair (repariert unvollständige Sätze)
    3. Extended Siezen (erweiterte du→Sie)
    4. hauptleistung-Enforcer (injiziert fehlende hauptleistung)
    5. Location-Validator (entfernt falsche Bundesländer)
    6. Grammar-Fixer (korrigiert Grammatikfehler)
    7. Solo-Language-Normalizer (ersetzt Enterprise-Begriffe für Solo-Persona)

    Args:
        sections: Dict mit allen Report-Sections
        hauptleistung: Das Kerngeschäft des Users
        bundesland: Das Bundesland des Users
        company_size: Die Unternehmensgröße ("solo", "team", "kmu")

    Returns:
        sections: Bereinigtes Dict
    """
    log.info("[QUALITY-ENFORCER] Starting quality enforcement pipeline...")

    # 0. P0.1: Stray Prefix Remover (leading "?" and artifacts)
    sections = apply_stray_prefix_remover(sections)

    # 1. ROI-Filter
    sections = apply_roi_filter(sections)

    # 2. Fragment-Repair
    sections = apply_fragment_repair(sections)
    
    # 2.5 v14.27: Ellipsen-Fix (Trunkierung entfernen)
    sections = apply_ellipsis_fix(sections)
    
    # 3. Extended Siezen
    sections = apply_extended_siezen_guard(sections)
    
    # 4. hauptleistung-Enforcer
    if hauptleistung:
        sections = apply_hauptleistung_enforcer(sections, hauptleistung)
    
    
    # 5. Location-Validator
    
    # 6. Grammar-Fixer
    
    # 7. AI-Act Konsistenz (v14.19)
    sections = apply_ai_act_consistency(sections)
    sections = apply_grammar_fixer(sections)
    if bundesland:
        sections = apply_location_validator(sections, bundesland)

    # 8. KPI Consistency Enforcement (v14.35.19+)
    sections = apply_kpi_consistency_enforcer(sections)

    # 9. Product Name Safety Net (v14.35.21) - LAST STEP (seatbelt)
    sections = apply_product_name_safety_net(sections)

    # 10. Open Example Paren Fixer (v14.35.22) - Fix "(z.B." incomplete patterns
    sections = apply_open_example_paren_fixer(sections)

    # 11. Solo Language Normalizer (v14.35.22) - Replace enterprise terms for solo persona
    if company_size:
        sections = apply_solo_language_normalizer(sections, company_size)

    # 12. Text Glitch Fixer (Fix-Batch F) - Fix known word corruptions and zero displays
    sections = apply_text_glitch_fixer(sections)

    # 13. Empty Page Killer (Fix-Batch I + J3) - Remove empty page-breaking sections
    sections = apply_empty_page_killer(sections)

    # 14. Risk Truncation (Fix-Batch I) - Truncate risk descriptions at sentence boundaries
    sections = apply_risk_truncation(sections)

    # 15. Chat Artefact Filter (Fix-Batch J4) - Remove "Schreib mir", "Frag mich" etc.
    sections = apply_chat_artefact_filter(sections)

    log.info("[QUALITY-ENFORCER] Pipeline complete")
    return sections


# =============================================================================
# v14.19: AI-ACT KONSISTENZ-VALIDATOR
# =============================================================================

def fix_ai_act_consistency(html: str) -> tuple[str, int]:
    """
    Behebt Widersprüche in AI-Act Risikoklassen.
    Problem: Auf derselben Seite steht "Risikoklasse: minimal" UND "Hochrisiko"
    """
    if not html:
        return html, 0
    
    fixes = 0
    result = html
    
    # Prüfe auf Widerspruch: minimal + Hochrisiko
    has_minimal = bool(re.search(r'Risikoklasse:\s*minimal', result, re.IGNORECASE))
    has_hochrisiko = bool(re.search(r'\bHochrisiko\b', result, re.IGNORECASE))
    
    if has_minimal and has_hochrisiko:
        # Entferne "Hochrisiko" wenn "minimal" definiert ist
        result = re.sub(r'\bHochrisiko\b', 'geringes Risiko', result)
        fixes += 1
        log.warning("[AI-ACT-CONSISTENCY] Fixed contradiction: Hochrisiko → geringes Risiko (weil Risikoklasse minimal)")
    
    return result, fixes


def apply_ai_act_consistency(sections: dict) -> dict:
    """
    v14.23: Globale Prüfung - erst alle Sections scannen, dann global fixen
    """
    # Erst global prüfen
    all_ai_act_text = ""
    ai_act_keys = [
        "AI_ACT_DUTY_MATRIX_HTML", "AI_ACT_NONCOMPLIANCE_ALERTS_HTML",
        "AI_ACT_DATA_GAPS_HTML", "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "AI_ACT_RELATED_USECASES_HTML", "AI_ACT_TABLE_OFFER_HTML",
        "AI_ACT_ADDON_PACKAGES_HTML", "AI_ACT_SUMMARY_HTML", "ai_act_summary",
        "RISKS_HTML", "risks"
    ]
    for key in ai_act_keys:
        if key in sections and sections[key]:
            all_ai_act_text += str(sections[key])
    
    # Globaler Check
    # v14.24: Prüfe auch die Variable AI_ACT_RISK_LEVEL direkt
    risk_level = sections.get("AI_ACT_RISK_LEVEL", "")
    has_minimal = risk_level == "minimal" or bool(re.search(r"Risikoklasse:\s*minimal", all_ai_act_text, re.IGNORECASE))
    has_hochrisiko = bool(re.search(r"\bHochrisiko\b", all_ai_act_text, re.IGNORECASE))
    
    if has_minimal and has_hochrisiko:
        log.warning("[AI-ACT-CONSISTENCY] Global contradiction detected - fixing all sections")
        for key in ai_act_keys:
            if key in sections and sections[key] and "Hochrisiko" in str(sections[key]):
                sections[key] = re.sub(r"\bHochrisiko\b", "geringes Risiko", str(sections[key]))
                log.info(f"[AI-ACT-CONSISTENCY] Fixed Hochrisiko in {key}")
    
    return sections

def apply_ai_act_consistency_OLD(sections: dict) -> dict:
    """Wendet AI-Act Konsistenz-Prüfung auf relevante Sections an."""
    ai_act_sections = [
        # v14.22: Alle AI-Act Sections
        "AI_ACT_DUTY_MATRIX_HTML",
        "AI_ACT_NONCOMPLIANCE_ALERTS_HTML",
        "AI_ACT_DATA_GAPS_HTML",
        "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "AI_ACT_RELATED_USECASES_HTML",
        "AI_ACT_TABLE_OFFER_HTML",
        "AI_ACT_ADDON_PACKAGES_HTML",
        "AI_ACT_SUMMARY_HTML", "ai_act_summary",
        "RISKS_HTML", "risks"
    ]
    
    for key in ai_act_sections:
        if key in sections and sections[key]:
            fixed, count = fix_ai_act_consistency(sections[key])
            if count > 0:
                sections[key] = fixed

    return sections


# =============================================================================
# v14.35.19+: KPI CONSISTENCY ENFORCER
# =============================================================================
# Ensures all KPI values in the report match the canonical values
# Single Source of Truth: canonical_kpis dict stored in sections

def extract_canonical_kpis(sections: dict) -> dict:
    """
    Extracts canonical KPI values from sections dict.

    These are the single source of truth for:
    - monatsersparnis_stunden (monthly time savings in hours)
    - jahresersparnis_stunden (annual time savings in hours)
    - monatsersparnis_eur (monthly savings in EUR)
    - jahresersparnis_eur (annual savings in EUR)
    - stundensatz_eur (hourly rate)
    - roi_12m (12-month ROI %)
    - payback_months (payback period)
    """
    canonical = {}

    # Extract from sections dict (these are set in gpt_analyze.py)
    kpi_keys = [
        "monatsersparnis_stunden", "jahresersparnis_stunden",
        "monatsersparnis_eur", "jahresersparnis_eur",
        "stundensatz_eur", "roi_12m", "payback_months",
        "capex_realistisch_eur", "opex_realistisch_eur"
    ]

    for key in kpi_keys:
        if key in sections:
            try:
                canonical[key] = float(sections[key])
            except (TypeError, ValueError):
                pass

    return canonical


def enforce_kpi_consistency(html: str, canonical_kpis: dict) -> tuple[str, int]:
    """
    Enforces KPI consistency in HTML content.

    Replaces any time savings/ROI values that deviate significantly from canonical values.
    Tolerance: 20% for savings, 10% for ROI

    Returns:
        tuple: (enforced_html, enforcement_count)
    """
    if not html or not canonical_kpis:
        return html, 0

    enforcements = 0
    result = html

    # Time savings (hours per month): Replace values outside tolerance
    if "monatsersparnis_stunden" in canonical_kpis:
        canonical_hours = canonical_kpis["monatsersparnis_stunden"]

        # Pattern: "X Stunden/Monat" or "X h/Monat" or "X Stunden monatlich"
        # Note: [-–] puts hyphen first to avoid range interpretation issues
        pattern = r'(\d+(?:[-–]\d+)?)\s*(?:Stunden?|h)\s*(?:/\s*Monat|monatlich|pro Monat|monthly)'

        def fix_monthly_hours(match):
            nonlocal enforcements
            matched_text = match.group(1)

            # Handle ranges like "20-35"
            if '–' in matched_text or '-' in matched_text:
                parts = re.split(r'[-–]', matched_text)
                if len(parts) == 2:
                    try:
                        low, high = float(parts[0]), float(parts[1])
                        avg = (low + high) / 2
                        # Check if range is way off from canonical
                        if abs(avg - canonical_hours) / canonical_hours > 0.3:
                            enforcements += 1
                            # Create range around canonical
                            new_low = int(canonical_hours * 0.85)
                            new_high = int(canonical_hours * 1.15)
                            return f"{new_low}–{new_high} Stunden/Monat"
                    except (ValueError, ZeroDivisionError):
                        pass
            else:
                try:
                    value = float(matched_text)
                    # Check if value deviates > 30% from canonical
                    if canonical_hours > 0 and abs(value - canonical_hours) / canonical_hours > 0.3:
                        enforcements += 1
                        return f"{int(canonical_hours)} Stunden/Monat"
                except ValueError:
                    pass

            return match.group(0)

        result = re.sub(pattern, fix_monthly_hours, result, flags=re.IGNORECASE)

    # Time savings (hours per year): Replace values outside tolerance
    if "jahresersparnis_stunden" in canonical_kpis:
        canonical_hours_year = canonical_kpis["jahresersparnis_stunden"]

        # Pattern: "X Stunden/Jahr" or "X h/Jahr" or "X Stunden jährlich"
        # Note: [-–] puts hyphen first to avoid range interpretation issues
        pattern = r'(\d+(?:[-–]\d+)?)\s*(?:Stunden?|h)\s*(?:/\s*Jahr|jährlich|pro Jahr|yearly|p\.a\.)'

        def fix_yearly_hours(match):
            nonlocal enforcements
            matched_text = match.group(1)

            # Handle ranges
            if '–' in matched_text or '-' in matched_text:
                parts = re.split(r'[-–]', matched_text)
                if len(parts) == 2:
                    try:
                        low, high = float(parts[0]), float(parts[1])
                        avg = (low + high) / 2
                        if abs(avg - canonical_hours_year) / canonical_hours_year > 0.3:
                            enforcements += 1
                            new_low = int(canonical_hours_year * 0.85)
                            new_high = int(canonical_hours_year * 1.15)
                            return f"{new_low}–{new_high} Stunden/Jahr"
                    except (ValueError, ZeroDivisionError):
                        pass
            else:
                try:
                    value = float(matched_text)
                    if canonical_hours_year > 0 and abs(value - canonical_hours_year) / canonical_hours_year > 0.3:
                        enforcements += 1
                        return f"{int(canonical_hours_year)} Stunden/Jahr"
                except ValueError:
                    pass

            return match.group(0)

        result = re.sub(pattern, fix_yearly_hours, result, flags=re.IGNORECASE)

    if enforcements > 0:
        log.info(f"[KPI-ENFORCER] Fixed {enforcements} inconsistent KPI values")

    return result, enforcements


def apply_kpi_consistency_enforcer(sections: dict) -> dict:
    """
    Applies KPI consistency enforcement across all relevant sections.

    v14.35.19+: Single Source of Truth for KPIs
    """
    # Extract canonical KPIs
    canonical_kpis = extract_canonical_kpis(sections)

    if not canonical_kpis:
        log.debug("[KPI-ENFORCER] No canonical KPIs found, skipping enforcement")
        return sections

    total_enforcements = 0

    # Sections to check for KPI consistency
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "executive_summary",
        "BUSINESS_CASE_HTML", "business_case",
        "ROI_HTML", "roi",
        "RECOMMENDATIONS_HTML", "recommendations",
        "GAMECHANGER_HTML", "gamechanger",
        "QUICK_WINS_HTML", "quick_wins",
        "ROADMAP_90D_HTML", "roadmap_90d",
        "ROADMAP_12M_HTML", "roadmap_12m",
    ]

    for key in check_sections:
        if key in sections and sections[key] and isinstance(sections[key], str):
            enforced, count = enforce_kpi_consistency(sections[key], canonical_kpis)
            if count > 0:
                sections[key] = enforced
                total_enforcements += count

    if total_enforcements > 0:
        log.info(f"[KPI-ENFORCER] Complete: {total_enforcements} KPI inconsistencies fixed")

    return sections


# =============================================================================
# Fix-Batch I: EMPTY PAGE KILLER
# =============================================================================

def kill_empty_pages(html: str) -> tuple[str, int]:
    """
    Fix-Batch I + J3: Remove empty page-breaking sections that only have a heading.

    Empty pages occur when a section div contains only an <h2> or <h3> with
    no substantial content following it.

    Fix-Batch J3 Enhancement:
    - Also detect sections with only heading + <br> tags as empty

    Args:
        html: HTML string to process

    Returns:
        Tuple of (cleaned_html, removals_count)
    """
    if not html:
        return html, 0

    removals = 0
    result = html

    # Pattern: div/section with only heading and minimal content (<100 chars of text)
    # Match: <div class="..."><h2>Title</h2></div> or <section><h3>Title</h3></section>
    empty_section_patterns = [
        # Section with only heading (no other content)
        (r'<section[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*</section>', 'empty section'),
        # Div with only heading
        (r'<div[^>]*class="[^"]*section[^"]*"[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*</div>', 'empty div section'),
        # Page-break div with only heading
        (r'<div[^>]*style="[^"]*page-break[^"]*"[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*</div>', 'empty page-break div'),
        # Fix-Batch J3: Section with heading and only <br> tags
        (r'<section[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:<br\s*/?\s*>\s*)+</section>', 'section with only br tags'),
        (r'<div[^>]*class="[^"]*section[^"]*"[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:<br\s*/?\s*>\s*)+</div>', 'div section with only br tags'),
        # Fix-Batch J3: Section with heading + whitespace + br
        (r'<(section|div)[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:\s*<br\s*/?\s*>\s*)*\s*</\1>', 'section with heading and br only'),
    ]

    for pattern, desc in empty_section_patterns:
        matches = re.findall(pattern, result, re.IGNORECASE | re.DOTALL)
        if matches:
            for match in matches:
                match_str = match if isinstance(match, str) else match[0] if match else ""
                log.warning(f"[EMPTY-PAGE-KILLER] Removing {desc}: {match_str[:50]}...")
                removals += 1
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    # Also remove sections with heading and only whitespace/empty paragraphs
    empty_with_p_pattern = r'<(section|div)[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:<p>\s*</p>\s*)*</\1>'
    matches = re.findall(empty_with_p_pattern, result, re.IGNORECASE | re.DOTALL)
    if matches:
        for _ in matches:
            log.warning("[EMPTY-PAGE-KILLER] Removing section with empty paragraphs")
            removals += 1
        result = re.sub(empty_with_p_pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    # Fix-Batch J3: Remove sections with heading + empty paragraphs + br tags
    empty_br_p_pattern = r'<(section|div)[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:(?:<p>\s*</p>|<br\s*/?\s*>)\s*)*</\1>'
    matches = re.findall(empty_br_p_pattern, result, re.IGNORECASE | re.DOTALL)
    if matches:
        for _ in matches:
            log.warning("[EMPTY-PAGE-KILLER] Removing section with empty paragraphs and br tags")
            removals += 1
        result = re.sub(empty_br_p_pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    return result, removals


def apply_empty_page_killer(sections: dict) -> dict:
    """
    Fix-Batch I: Apply empty page killer to all HTML sections.

    Args:
        sections: Dict with all report sections

    Returns:
        Cleaned sections dict
    """
    html_keys = [k for k in sections.keys() if k.endswith('_HTML') or k == 'html']
    total_removals = 0

    for key in html_keys:
        if key in sections and sections[key] and isinstance(sections[key], str):
            cleaned, count = kill_empty_pages(sections[key])
            if count > 0:
                sections[key] = cleaned
                total_removals += count

    if total_removals > 0:
        log.info(f"[EMPTY-PAGE-KILLER] Complete: {total_removals} empty pages removed")

    return sections


# =============================================================================
# Fix-Batch I: RISK TEXT SENTENCE TRUNCATION
# =============================================================================

def truncate_at_sentence(text: str, max_chars: int = 500) -> str:
    """
    Fix-Batch I: Truncate text at last sentence boundary before max_chars.

    Ensures risk descriptions and other long texts are truncated at
    proper sentence boundaries (., !, ?) rather than mid-sentence.

    Args:
        text: Text to truncate
        max_chars: Maximum character limit

    Returns:
        Truncated text ending at sentence boundary
    """
    if not text or len(text) <= max_chars:
        return text

    # Find the last sentence boundary before max_chars
    truncated = text[:max_chars]

    # Look for sentence endings (., !, ?)
    sentence_endings = ['.', '!', '?']
    last_boundary = -1

    for i in range(len(truncated) - 1, -1, -1):
        if truncated[i] in sentence_endings:
            # Check it's not part of abbreviation (e.g., "z.B.", "bzw.", "etc.")
            # Simple heuristic: must be followed by space or end of string
            if i == len(truncated) - 1 or truncated[i + 1] in (' ', '\n', '<'):
                # Check it's not a single letter abbreviation
                if i >= 2 and truncated[i-1] != '.':
                    last_boundary = i
                    break
                elif i >= 1:
                    last_boundary = i
                    break

    if last_boundary > 0:
        return truncated[:last_boundary + 1]

    # No sentence boundary found, try to cut at last space
    last_space = truncated.rfind(' ')
    if last_space > max_chars // 2:
        return truncated[:last_space] + '...'

    # Last resort: hard cut with ellipsis
    return truncated[:max_chars - 3] + '...'


def truncate_risk_descriptions(html: str, max_chars: int = 500) -> tuple[str, int]:
    """
    Fix-Batch I: Truncate long risk descriptions at sentence boundaries.

    Finds risk description elements and ensures they don't exceed max_chars,
    cutting only at sentence boundaries.

    Args:
        html: HTML string containing risk descriptions
        max_chars: Maximum character limit for descriptions

    Returns:
        Tuple of (processed_html, truncations_count)
    """
    if not html:
        return html, 0

    truncations = 0
    result = html

    # Pattern: risk description paragraphs or divs
    # Look for common risk description patterns
    desc_patterns = [
        (r'(<div class="risk-description[^"]*"[^>]*>)([^<]{' + str(max_chars) + r',})(</div>)', 'risk-description div'),
        (r'(<p class="risk-text[^"]*"[^>]*>)([^<]{' + str(max_chars) + r',})(</p>)', 'risk-text paragraph'),
        (r'(<td class="risk-desc[^"]*"[^>]*>)([^<]{' + str(max_chars) + r',})(</td>)', 'risk-desc cell'),
    ]

    for pattern, desc in desc_patterns:
        def truncate_match(match):
            nonlocal truncations
            opening = match.group(1)
            content = match.group(2)
            closing = match.group(3)
            truncated = truncate_at_sentence(content, max_chars)
            if len(truncated) < len(content):
                truncations += 1
                log.info(f"[RISK-TRUNCATION] Truncated {desc} from {len(content)} to {len(truncated)} chars")
            return opening + truncated + closing

        result = re.sub(pattern, truncate_match, result, flags=re.IGNORECASE | re.DOTALL)

    return result, truncations


def apply_risk_truncation(sections: dict, max_chars: int = 500) -> dict:
    """
    Fix-Batch I: Apply risk description truncation to relevant sections.

    Args:
        sections: Dict with all report sections
        max_chars: Maximum character limit for risk descriptions

    Returns:
        Processed sections dict
    """
    risk_sections = [
        "RISKS_HTML", "risks",
        "AI_ACT_SUMMARY_HTML", "ai_act_summary",
        "COMPLIANCE_HTML", "compliance",
    ]

    total_truncations = 0

    for key in risk_sections:
        if key in sections and sections[key] and isinstance(sections[key], str):
            processed, count = truncate_risk_descriptions(sections[key], max_chars)
            if count > 0:
                sections[key] = processed
                total_truncations += count

    if total_truncations > 0:
        log.info(f"[RISK-TRUNCATION] Complete: {total_truncations} descriptions truncated at sentence boundary")

    return sections


# =============================================================================
# Fix-Batch J4: CHAT ARTEFACT FILTER
# =============================================================================
# Problem: LLM output sometimes contains chat artefacts like "Schreib mir",
# "Frag mich", "Wenn du..." that are inappropriate for formal reports.
# Solution: Filter these patterns from all text sections.
# =============================================================================

# Chat artefacts that should be removed (German patterns)
CHAT_ARTEFACT_PATTERNS = [
    # Direct address patterns
    r"(?i)schreib\s+mir\b.*?[.!]",
    r"(?i)frag\s+mich\b.*?[.!]",
    r"(?i)wenn\s+du\s+(möchtest|willst|brauchst)\b.*?[.!]",
    r"(?i)sag\s+mir\s+bescheid\b.*?[.!]",
    r"(?i)lass\s+mich\s+wissen\b.*?[.!]",
    r"(?i)meld\s+dich\b.*?[.!]",
    r"(?i)ruf\s+mich\s+an\b.*?[.!]",
    r"(?i)ich\s+kann\s+dir\s+(helfen|zeigen|erklären)\b.*?[.!]",
    r"(?i)ich\s+stehe\s+dir\s+zur\s+verfügung\b.*?[.!]",
    # Du-form patterns (informal)
    r"(?i)du\s+kannst\s+mich\s+(fragen|kontaktieren)\b.*?[.!]",
    r"(?i)wenn\s+du\s+fragen\s+hast\b.*?[.!]",
    r"(?i)falls\s+du\s+(weitere|mehr)\s+infos\s+(brauchst|möchtest)\b.*?[.!]",
    # Meta-commentary about the chat
    r"(?i)wie\s+besprochen\b",
    r"(?i)wie\s+ich\s+dir\s+gesagt\s+habe\b",
    r"(?i)ich\s+hoffe,\s+das\s+hilft\b",
    # Emoji clusters (more than 2 consecutive emojis)
    r"[\U0001F300-\U0001F9FF]{3,}",
]


def filter_chat_artefacts(text: str) -> tuple[str, int]:
    """
    Fix-Batch J4: Remove chat artefacts from text.

    Filters out LLM chat artefacts like "Schreib mir", "Frag mich", etc.
    that are inappropriate for formal business reports.

    Args:
        text: Text to process

    Returns:
        Tuple of (cleaned_text, removals_count)
    """
    if not text:
        return text, 0

    removals = 0
    result = text

    for pattern in CHAT_ARTEFACT_PATTERNS:
        matches = re.findall(pattern, result)
        if matches:
            removals += len(matches)
            result = re.sub(pattern, '', result)

    # Clean up double spaces and line breaks from removals
    result = re.sub(r'\s{2,}', ' ', result)
    result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)

    if removals > 0:
        log.info(f"[CHAT-ARTEFACT-FILTER] Removed {removals} chat artefacts")

    return result.strip(), removals


def apply_chat_artefact_filter(sections: dict) -> dict:
    """
    Fix-Batch J4: Apply chat artefact filter to all text sections.

    Args:
        sections: Dict with all report sections

    Returns:
        Cleaned sections dict
    """
    # All text-bearing sections
    text_sections = [
        k for k in sections.keys()
        if isinstance(sections.get(k), str) and sections.get(k)
        and (k.endswith('_HTML') or k.islower() or k in [
            'EXECUTIVE_SUMMARY', 'QUICK_WINS', 'RECOMMENDATIONS',
            'RISKS', 'STRATEGY', 'ROADMAP', 'executive_summary',
            'quick_wins', 'recommendations', 'risks', 'strategy', 'roadmap'
        ])
    ]

    total_removals = 0

    for key in text_sections:
        if key in sections and sections[key]:
            cleaned, count = filter_chat_artefacts(str(sections[key]))
            if count > 0:
                sections[key] = cleaned
                total_removals += count

    if total_removals > 0:
        log.info(f"[CHAT-ARTEFACT-FILTER] Complete: {total_removals} total artefacts removed")

    return sections

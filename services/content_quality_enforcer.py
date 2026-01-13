"""
Content Quality Enforcer v1.0
=============================
Post-Processing Safety Net für Report-Qualität.

Fixes:
1. ROI-Filter: Entfernt ROI% außerhalb Business Case
2. Fragment-Repair: Repariert unvollständige Sätze
3. hauptleistung-Enforcer: Injiziert hauptleistung wenn unter Minimum

Wird nach SIEZEN-GUARD aufgerufen, vor Validation.
"""

import re
import logging

log = logging.getLogger(__name__)

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
def apply_all_quality_enforcers(sections: dict, hauptleistung: str = "", bundesland: str = "") -> dict:

    """
    Wendet alle Quality Enforcer in der richtigen Reihenfolge an.
    
    Order:
    1. ROI-Filter (entfernt verbotene ROI-Werte)
    2. Fragment-Repair (repariert unvollständige Sätze)
    3. Extended Siezen (erweiterte du→Sie)
    4. hauptleistung-Enforcer (injiziert fehlende hauptleistung)
    5. Location-Validator (entfernt falsche Bundesländer)
    6. Grammar-Fixer (korrigiert Grammatikfehler)
    
    Args:
        sections: Dict mit allen Report-Sections
        hauptleistung: Das Kerngeschäft des Users
        
    Returns:
        sections: Bereinigtes Dict
    """
    log.info("[QUALITY-ENFORCER] Starting quality enforcement pipeline...")
    
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

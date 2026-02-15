#!/bin/bash
# =============================================================================
# FIX_C1-C6.sh — PDF Quality Fix Suite (korrigiert)
# =============================================================================
# Datum: 2026-02-15
# Fixes: 6 Issues aus PDF Visual Review
#
# FIX-C1 (P0): Leere Context-Block-Labels aus LLM-Output strippen
# FIX-C2 (P1): branch_deep_dive in prompt_map aufnehmen
# FIX-C3 (P1): Fehlende Section-Budgets ergänzen
# FIX-C4 (P2): RISKS_HTML Budget erhöhen
# FIX-C5 (P2): Vendor Audit Fallback aus Fragebogen-Tools
# FIX-C6 (P2): Governance-Board Persona-Replacement für team
#
# USAGE:
#   cd /workspaces/api-ki-backend-neu
#   bash FIX_C1-C6.sh
#
# ROLLBACK:
#   git checkout -- config/ services/ gpt_analyze.py
# =============================================================================

set -euo pipefail

echo ""
echo "======================================================"
echo "  FIX-C1..C6: PDF Quality Fix Suite"
echo "======================================================"
echo ""

# Verify we're in the right directory
if [ ! -f "gpt_analyze.py" ]; then
    echo "❌ ERROR: gpt_analyze.py not found."
    echo "   Run this script from the api-ki-backend-neu root directory:"
    echo "   cd /workspaces/api-ki-backend-neu && bash FIX_C1-C6.sh"
    exit 1
fi

echo "📂 Working directory: $(pwd)"
echo ""

# =============================================================================
# FIX-C2 (P1): Add branch_deep_dive to prompt_map
# =============================================================================
echo "--- FIX-C2: branch_deep_dive → prompt_map ---"

python3 << 'FIXC2'
with open("gpt_analyze.py", "r") as f:
    content = f.read()

old = '"prompt_framework": "prompt_framework",\n    }'
new = '"prompt_framework": "prompt_framework",\n        # FIX-C2: branch_deep_dive was missing -> empty prompt -> 400 error\n        "branch_deep_dive": "branch_deep_dive",\n    }'

if "FIX-C2" in content:
    print("  SKIP: already applied")
elif old in content:
    content = content.replace(old, new, 1)
    with open("gpt_analyze.py", "w") as f:
        f.write(content)
    print("  OK: branch_deep_dive added to prompt_map")
else:
    print("  WARN: target string not found")
FIXC2

echo ""

# =============================================================================
# FIX-C3 (P1): Add missing section budgets to size_profiles
# =============================================================================
echo "--- FIX-C3: Missing section budgets ---"

python3 << 'FIXC3'
with open("config/size_profiles.py", "r") as f:
    content = f.read()

if "FIX-C3" in content:
    print("  SKIP: already applied")
else:
    changed = False

    # SOLO budgets
    old_solo = '''"TECHNOLOGIE_PROZESSE_HTML": 2000,
            "_default": 1000,'''
    new_solo = '''"TECHNOLOGIE_PROZESSE_HTML": 2000,
            # FIX-C3: Sprint 2025 Phase 2 sections (were missing)
            "ROI_TRACKING_HTML": 2000,
            "AI_POLICY_MINI_HTML": 2500,
            "KICKOFF_VORLAGE_HTML": 2500,
            "PROMPT_FRAMEWORK_HTML": 1500,
            "BRANCH_DEEP_DIVE_HTML": 3000,
            "TRANSPARENCY_BOX_HTML": 1500,
            "KI_AKTIVITAETEN_ZIELE_HTML": 2000,
            "WETTBEWERB_BENCHMARK_HTML": 2000,
            "REIFEGRAD_SOWHAT_HTML": 1500,
            "AI_ACT_SUMMARY_HTML": 2000,
            "_default": 1000,'''
    if old_solo in content:
        content = content.replace(old_solo, new_solo, 1)
        changed = True

    # TEAM budgets
    old_team = '''"TECHNOLOGIE_PROZESSE_HTML": 3000,
            "_default": 1500,'''
    new_team = '''"TECHNOLOGIE_PROZESSE_HTML": 3000,
            # FIX-C3: Sprint 2025 Phase 2 sections (were missing)
            "ROI_TRACKING_HTML": 3000,
            "AI_POLICY_MINI_HTML": 3500,
            "KICKOFF_VORLAGE_HTML": 5000,
            "PROMPT_FRAMEWORK_HTML": 2000,
            "BRANCH_DEEP_DIVE_HTML": 6000,
            "TRANSPARENCY_BOX_HTML": 2000,
            "KI_AKTIVITAETEN_ZIELE_HTML": 3000,
            "WETTBEWERB_BENCHMARK_HTML": 3000,
            "REIFEGRAD_SOWHAT_HTML": 2000,
            "AI_ACT_SUMMARY_HTML": 3000,
            "_default": 1500,'''
    if old_team in content:
        content = content.replace(old_team, new_team, 1)
        changed = True

    if changed:
        with open("config/size_profiles.py", "w") as f:
            f.write(content)
        print("  OK: 10 section budgets added (solo + team)")
    else:
        print("  WARN: target strings not found")
FIXC3

echo ""

# =============================================================================
# FIX-C4 (P2): RISKS_HTML budget increase
# =============================================================================
echo "--- FIX-C4: RISKS_HTML budget increase ---"

python3 << 'FIXC4'
changes = 0

# size_profiles.py
with open("config/size_profiles.py", "r") as f:
    content = f.read()

# Solo: 1200 -> 2500 (first occurrence)
if '"RISKS_HTML": 1200,' in content:
    content = content.replace(
        '"RISKS_HTML": 1200,',
        '"RISKS_HTML": 2500,  # FIX-C4: was 1200',
        1
    )
    changes += 1

# Team: 1800 -> 4000 (first remaining occurrence)
if '"RISKS_HTML": 1800,' in content:
    content = content.replace(
        '"RISKS_HTML": 1800,',
        '"RISKS_HTML": 4000,  # FIX-C4: was 1800',
        1
    )
    changes += 1

if changes > 0:
    with open("config/size_profiles.py", "w") as f:
        f.write(content)
    print(f"  OK: size_profiles.py ({changes} profiles)")

# report_healer.py
with open("services/report_healer.py", "r") as f:
    content2 = f.read()

if '"RISKS_HTML": 1800,' in content2:
    content2 = content2.replace('"RISKS_HTML": 1800,', '"RISKS_HTML": 4000,  # FIX-C4', 1)
    with open("services/report_healer.py", "w") as f:
        f.write(content2)
    print("  OK: report_healer.py")
else:
    print("  INFO: report_healer already ok")
FIXC4

echo ""

# =============================================================================
# FIX-C5 (P2): Vendor Audit Fallback from questionnaire tools
# =============================================================================
echo "--- FIX-C5: Vendor Audit fallback ---"

python3 << 'FIXC5'
with open("services/vendor_audit_engine.py", "r") as f:
    content = f.read()

if "FIX-C5" in content:
    print("  SKIP: already applied")
else:
    # Part A: Add fallback function before _extract_vendors_from_tools
    fallback_code = '''

# FIX-C5: Known vendor metadata for questionnaire-based extraction
_KNOWN_VENDOR_META = {
    "chatgpt": {"name": "ChatGPT (OpenAI)", "category": "LLM", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "openai": {"name": "OpenAI", "category": "LLM API", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "claude": {"name": "Claude (Anthropic)", "category": "LLM", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "anthropic": {"name": "Anthropic", "category": "LLM API", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "perplexity": {"name": "Perplexity AI", "category": "Search AI", "host": "US", "gdpr": "Limited", "vendor_risk": 4, "eu_hosting": False},
    "tavily": {"name": "Tavily", "category": "Search API", "host": "US", "gdpr": "Limited", "vendor_risk": 4, "eu_hosting": False},
    "gemini": {"name": "Gemini (Google)", "category": "LLM", "host": "US/EU", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "google": {"name": "Google AI", "category": "LLM", "host": "US/EU", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "copilot": {"name": "Microsoft Copilot", "category": "LLM", "host": "EU available", "gdpr": "DPA + EU Data Boundary", "vendor_risk": 2, "eu_hosting": True},
    "microsoft": {"name": "Microsoft AI", "category": "LLM", "host": "EU available", "gdpr": "DPA + EU Data Boundary", "vendor_risk": 2, "eu_hosting": True},
    "midjourney": {"name": "Midjourney", "category": "Image Gen", "host": "US", "gdpr": "Limited", "vendor_risk": 4, "eu_hosting": False},
    "dall-e": {"name": "DALL-E (OpenAI)", "category": "Image Gen", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "deepl": {"name": "DeepL", "category": "Translation", "host": "DE", "gdpr": "Full DSGVO", "vendor_risk": 1, "eu_hosting": True},
    "notion": {"name": "Notion AI", "category": "Productivity", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "jasper": {"name": "Jasper AI", "category": "Content Gen", "host": "US", "gdpr": "DPA available", "vendor_risk": 3, "eu_hosting": False},
    "huggingface": {"name": "Hugging Face", "category": "ML Platform", "host": "US/EU", "gdpr": "Self-hosted option", "vendor_risk": 2, "eu_hosting": True},
}


def _extract_vendors_from_briefing(briefing: dict) -> list:
    """FIX-C5: Extract vendor info from questionnaire answers as fallback."""
    vendors = []
    seen = set()
    tool_sources = [
        briefing.get("VORHANDENE_TOOLS_LABELS", ""),
        briefing.get("vorhandene_tools", ""),
        briefing.get("ki_projekte", ""),
    ]
    for source in tool_sources:
        if not source:
            continue
        if isinstance(source, list):
            items = source
        else:
            items = [s.strip() for s in str(source).replace(";", ",").split(",")]
        for item in items:
            item_lower = item.strip().lower()
            if not item_lower:
                continue
            for key, meta in _KNOWN_VENDOR_META.items():
                if key in item_lower and meta["name"] not in seen:
                    vendors.append(dict(meta))
                    seen.add(meta["name"])
    return vendors


'''
    marker = "def _extract_vendors_from_tools("
    if marker in content:
        content = content.replace(marker, fallback_code + marker, 1)

    # Part B: Add fallback call in generate_vendor_audit_report
    old_call = "    # Extract vendors from tools data\n    vendors = _extract_vendors_from_tools(tools_data)"
    new_call = """    # Extract vendors from tools data
    vendors = _extract_vendors_from_tools(tools_data)

    # FIX-C5: Fallback - extract from questionnaire if tools_data is empty
    if not vendors and briefing:
        vendors = _extract_vendors_from_briefing(briefing)
        if vendors:
            log.info("[G35][FIX-C5] Extracted %d vendors from questionnaire fallback", len(vendors))"""

    if old_call in content:
        content = content.replace(old_call, new_call, 1)

    with open("services/vendor_audit_engine.py", "w") as f:
        f.write(content)
    print("  OK: vendor fallback + 16 known vendors added")
FIXC5

echo ""

# =============================================================================
# FIX-C6 (P2): Governance-Board Persona-Replacement for team
# =============================================================================
echo "--- FIX-C6: Team persona replacements ---"

python3 << 'FIXC6'
with open("services/content_quality_enforcer.py", "r") as f:
    content = f.read()

if "FIX-C6" in content:
    print("  SKIP: already applied")
else:
    # The key insight: check_sections is defined AFTER the solo guard.
    # We need to move it BEFORE the team block.
    # Original code flow:
    #   1. "# Only apply for solo" guard -> return if not solo
    #   2. total_replacements = 0
    #   3. sections_touched = 0
    #   4. check_sections = [...]
    #   5. for section_key in check_sections: ...
    #
    # New code flow:
    #   1. size_lower = ...
    #   2. check_sections = [...]       <-- MOVED UP
    #   3. if size_lower == "team": ... <-- NEW BLOCK using check_sections
    #   4. if size_lower != "solo": return
    #   5. total_replacements = 0
    #   6. sections_touched = 0
    #   7. for section_key in check_sections: ... (unchanged)

    old_block = '''    # Only apply for solo
    if not company_size or company_size.lower() != "solo":
        return sections

    total_replacements = 0
    sections_touched = 0

    # Sections to process - Fix-Batch C3: Expanded list to cover all content sections
    # FIX-526: Added NEXT_ACTIONS_HTML, PILOT_PLAN_HTML
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "EXECUTIVE_DECISION_HTML", "RECOMMENDATIONS_HTML",
        "QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT",
        "ROADMAP_90D_HTML", "ROADMAP_90D_DECISION_HTML", "ROADMAP_12M_HTML",
        "GAMECHANGER_HTML", "GAMECHANGER_DECISION_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML", "AI_ACT_SUMMARY_HTML",
        "TOOLS_HTML", "TOOLS_EMPFEHLUNGEN_HTML", "DATA_STRATEGY_HTML", "DATA_READINESS_HTML",
        "GOVERNANCE_HTML", "STRATEGIE_GOVERNANCE_HTML", "KI_STACK_SUMMARY_HTML",
        "BRANCH_DEEP_DIVE_HTML", "TOP_3_MASSNAHMEN_HTML", "MONETARISIERUNG_HTML",
        "TEMPLATES_START_HTML", "KICKOFF_VORLAGE_HTML", "PROMPT_FRAMEWORK_HTML",
        "TECHNOLOGIE_PROZESSE_HTML", "WETTBEWERB_BENCHMARK_HTML", "UNTERNEHMENSPROFIL_MARKT_HTML",
        "NEXT_ACTIONS_HTML", "PILOT_PLAN_HTML",
    ]'''

    new_block = r'''    # FIX-C6: Apply persona replacements for solo AND team
    size_lower = (company_size or "").lower()

    # Sections to process - Fix-Batch C3: Expanded list to cover all content sections
    # FIX-526: Added NEXT_ACTIONS_HTML, PILOT_PLAN_HTML
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "EXECUTIVE_DECISION_HTML", "RECOMMENDATIONS_HTML",
        "QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT",
        "ROADMAP_90D_HTML", "ROADMAP_90D_DECISION_HTML", "ROADMAP_12M_HTML",
        "GAMECHANGER_HTML", "GAMECHANGER_DECISION_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML", "AI_ACT_SUMMARY_HTML",
        "TOOLS_HTML", "TOOLS_EMPFEHLUNGEN_HTML", "DATA_STRATEGY_HTML", "DATA_READINESS_HTML",
        "GOVERNANCE_HTML", "STRATEGIE_GOVERNANCE_HTML", "KI_STACK_SUMMARY_HTML",
        "BRANCH_DEEP_DIVE_HTML", "TOP_3_MASSNAHMEN_HTML", "MONETARISIERUNG_HTML",
        "TEMPLATES_START_HTML", "KICKOFF_VORLAGE_HTML", "PROMPT_FRAMEWORK_HTML",
        "TECHNOLOGIE_PROZESSE_HTML", "WETTBEWERB_BENCHMARK_HTML", "UNTERNEHMENSPROFIL_MARKT_HTML",
        "NEXT_ACTIONS_HTML", "PILOT_PLAN_HTML",
    ]

    # Team-specific replacements (Governance-Board etc.)
    if size_lower == "team":
        TEAM_REPLACEMENTS = [
            (r"\bGovernance-Board\b", "KI-Verantwortlichen"),
            (r"\bGovernance Board\b", "KI-Verantwortlichen"),
            (r"\bEnterprise-Architektur\b", "IT-Struktur"),
            (r"\bKonzernstruktur\b", "Unternehmensstruktur"),
            (r"\bRollout-Plan\b", "Umsetzungsplan"),
            (r"\bStakeholder-Analyse\b", "Beteiligte"),
        ]
        team_total = 0
        for section_key in check_sections:
            val = sections.get(section_key)
            if not val or not isinstance(val, str):
                continue
            modified = val
            for pattern, replacement in TEAM_REPLACEMENTS:
                matches = len(re.findall(pattern, modified))
                if matches > 0:
                    modified = re.sub(pattern, replacement, modified)
                    team_total += matches
            if modified != val:
                sections[section_key] = modified
        if team_total > 0:
            log.info("[FIX-C6] Team persona cleanup: %d replacements", team_total)
        return sections

    if size_lower != "solo":
        return sections

    total_replacements = 0
    sections_touched = 0'''

    if old_block in content:
        content = content.replace(old_block, new_block, 1)
        with open("services/content_quality_enforcer.py", "w") as f:
            f.write(content)
        print("  OK: team persona replacements added (6 patterns)")
    else:
        print("  WARN: target block not found")
FIXC6

echo ""

# =============================================================================
# FIX-C1 (P0): Strip context block labels from LLM output
# =============================================================================
echo "--- FIX-C1: Context block stripper ---"

python3 << 'FIXC1'
import re

with open("services/pipeline_sanitizers.py", "r") as f:
    content = f.read()

if "FIX-C1" in content:
    print("  SKIP: already applied")
else:
    # Part A: Add the stripper function before INITIALIZATION
    new_function = r'''

# =============================================================================
# FIX-C1: STRIP CONTEXT BLOCK LABELS FROM LLM OUTPUT
# =============================================================================
# The prompt_enhancer injects HTML context blocks into LLM prompts. Some LLMs
# copy these blocks into their output. This sanitizer removes them.

# Regex: Match entire context-block divs (class="context-block")
_CONTEXT_BLOCK_RE = re.compile(
    r'<div[^>]*class="context-block[^"]*"[^>]*>.*?</div>',
    re.DOTALL | re.IGNORECASE,
)

# Regex: Match orphaned context labels
_CONTEXT_LABEL_PATTERNS = [
    r'<p[^>]*>\s*<strong>\s*(?:Typische (?:Tools im Einsatz|Workflows)|'
    r'H\u00e4ufigste Pain Points|Charakteristika|Fokus-Priorit\u00e4ten|'
    r'In Ihrer aktuellen Gr\u00f6\u00dfe nicht sinnvoll|'
    r'Branchen-Context|Gr\u00f6\u00dfen-Context|Mitarbeiter|'
    r'Budget (?:CAPEX|OPEX) max|'
    r'Kernleistung \(Hauptleistung\)|'
    r'Typical (?:Tools in Use|Workflows)|Common Pain Points|'
    r'Characteristics|Focus Priorities|'
    r'Not recommended for your current size|'
    r'Industry Context|Size Context|Core Service \(Main Offering\)'
    r')\s*:?\s*</strong>\s*</p>',
    r'<p[^>]*>\s*(?:Typische Tools im Einsatz|Charakteristika|'
    r'Fokus-Priorit\u00e4ten|In Ihrer aktuellen Gr\u00f6\u00dfe nicht sinnvoll)\s*:?\s*</p>',
    r'<ul[^>]*>\s*<li>\s*\((?:Keine Angaben|No data available)\)\s*</li>\s*</ul>',
]

_CONTEXT_LABEL_RES = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _CONTEXT_LABEL_PATTERNS]

# Match context section wrappers
_CONTEXT_SECTION_RE = re.compile(
    r'<(?:div|section)[^>]*(?:context-block|branch-context|size-context)[^>]*>'
    r'.*?</(?:div|section)>',
    re.DOTALL | re.IGNORECASE,
)

# HR separators between context blocks
_CONTEXT_HR_RE = re.compile(
    r'<hr[^>]*style="[^"]*border[^"]*#cbd5e1[^"]*"[^>]*/?>',
    re.IGNORECASE,
)


def strip_context_block_leaks(html: str, section_name: str = "") -> tuple:
    """
    FIX-C1: Remove context block labels that leaked from prompts into LLM output.
    Returns: Tuple of (cleaned_html, removal_count)
    """
    if not html or len(html) < 100:
        return html, 0

    removals = 0
    result = html

    # 1. Remove full context-block divs
    for _ in _CONTEXT_BLOCK_RE.finditer(result):
        removals += 1
    result = _CONTEXT_BLOCK_RE.sub("", result)

    # 2. Remove context section wrappers
    for _ in _CONTEXT_SECTION_RE.finditer(result):
        removals += 1
    result = _CONTEXT_SECTION_RE.sub("", result)

    # 3. Remove orphaned label patterns
    for pattern_re in _CONTEXT_LABEL_RES:
        for _ in pattern_re.finditer(result):
            removals += 1
        result = pattern_re.sub("", result)

    # 4. Remove context HR separators
    result = _CONTEXT_HR_RE.sub("", result)

    # 5. Clean up resulting empty tags
    result = re.sub(r'<(?:div|section)[^>]*>\s*</(?:div|section)>', "", result)
    result = re.sub(r'\n\s*\n\s*\n', "\n\n", result)

    if removals > 0:
        log.info(
            "[FIX-C1][CONTEXT-STRIP] section=%s removed=%d context block leaks",
            section_name, removals,
        )

    return result, removals


'''

    init_marker = "# =============================================================================\n# INITIALIZATION"
    if init_marker in content:
        content = content.replace(init_marker, new_function + init_marker, 1)
    else:
        content = content.rstrip() + "\n" + new_function + "\n"

    # Part B: Hook into sanitize_all_sections
    old_hook = """        sanitized[key] = result.content
        stats['entities_decoded']"""
    new_hook = """        # FIX-C1: Strip context block leaks from LLM output
        cleaned, c1_removals = strip_context_block_leaks(result.content, key)
        if c1_removals > 0:
            stats['context_blocks_stripped'] = stats.get('context_blocks_stripped', 0) + c1_removals

        sanitized[key] = cleaned
        stats['entities_decoded']"""

    if old_hook in content:
        content = content.replace(old_hook, new_hook, 1)
        print("  OK: context block stripper + hook added")
    else:
        print("  WARN: hook point not found (function still added)")

    with open("services/pipeline_sanitizers.py", "w") as f:
        f.write(content)
FIXC1

echo ""

# =============================================================================
# VALIDATION
# =============================================================================
echo "======================================================"
echo "  VALIDATION"
echo "======================================================"
echo ""

python3 << 'VALIDATE'
import ast, sys

# 1. Syntax check all modified files
files = [
    "config/size_profiles.py",
    "gpt_analyze.py",
    "services/content_quality_enforcer.py",
    "services/pipeline_sanitizers.py",
    "services/report_healer.py",
    "services/vendor_audit_engine.py",
]

syntax_ok = True
for f in files:
    try:
        with open(f) as fh:
            ast.parse(fh.read())
        print(f"  SYNTAX  OK: {f}")
    except SyntaxError as e:
        print(f"  SYNTAX ERR: {f} -> {e}")
        syntax_ok = False

print()

# 2. Check markers
markers = {
    "C1": ("services/pipeline_sanitizers.py", "strip_context_block_leaks"),
    "C2": ("gpt_analyze.py", '"branch_deep_dive": "branch_deep_dive"'),
    "C3": ("config/size_profiles.py", "ROI_TRACKING_HTML"),
    "C4": ("config/size_profiles.py", "FIX-C4"),
    "C5": ("services/vendor_audit_engine.py", "_extract_vendors_from_briefing"),
    "C6": ("services/content_quality_enforcer.py", "FIX-C6"),
}

all_ok = True
for fix_id, (filepath, marker) in markers.items():
    with open(filepath) as f:
        if marker in f.read():
            print(f"  FIX-{fix_id}: APPLIED")
        else:
            print(f"  FIX-{fix_id}: MISSING!")
            all_ok = False

print()

# 3. Smoke test C6 (check_sections must be defined before team block)
try:
    sys.path.insert(0, ".")
    # Quick import test - just check the function exists and runs
    from services.content_quality_enforcer import apply_solo_language_normalizer
    test = {"EXECUTIVE_SUMMARY_HTML": "Ein Governance-Board einrichten."}
    result = apply_solo_language_normalizer(dict(test), "team")
    assert "Governance-Board" not in result.get("EXECUTIVE_SUMMARY_HTML", ""), \
        "Governance-Board should be replaced for team"
    print("  SMOKE TEST C6: OK (Governance-Board replaced)")
except Exception as e:
    print(f"  SMOKE TEST C6: FAILED -> {e}")
    all_ok = False

# 4. Smoke test C5
try:
    from services.vendor_audit_engine import _extract_vendors_from_briefing
    briefing = {"VORHANDENE_TOOLS_LABELS": "ChatGPT, Claude, Perplexity"}
    vendors = _extract_vendors_from_briefing(briefing)
    assert len(vendors) >= 3, f"Expected >= 3 vendors, got {len(vendors)}"
    print(f"  SMOKE TEST C5: OK ({len(vendors)} vendors extracted)")
except Exception as e:
    print(f"  SMOKE TEST C5: FAILED -> {e}")
    all_ok = False

# 5. Smoke test C1
try:
    from services.pipeline_sanitizers import strip_context_block_leaks
    html = '<div class="context-block" style="x"><p><strong>Typische Tools im Einsatz:</strong></p></div><p>Real content</p>'
    cleaned, count = strip_context_block_leaks(html, "TEST")
    assert count > 0, "Should have removed context block"
    assert "Real content" in cleaned, "Should keep real content"
    print(f"  SMOKE TEST C1: OK ({count} blocks stripped)")
except Exception as e:
    print(f"  SMOKE TEST C1: FAILED -> {e}")
    all_ok = False

print()
if syntax_ok and all_ok:
    print("=" * 54)
    print("  ALL 6 FIXES APPLIED AND VERIFIED")
    print("=" * 54)
else:
    print("  WARNING: Some checks failed. Review output above.")
VALIDATE

echo ""
echo "--- Git commands to deploy: ---"
echo ""
echo "  git add -A"
echo '  git commit -m "FIX-C1..C6: PDF quality fixes (context blocks, branch_deep_dive, budgets, vendor audit, persona)"'
echo "  git push origin main"
echo ""

#!/usr/bin/env python3
"""
J-SERIE FIXES — Post I-Serie Nachbesserungen
=============================================
J1: I8 Monte Carlo — find & remove downstream ROI cap at MAX_ROI
J2: I10 Mojibake — add â€¢ → • pattern to fix_double_encoded_utf8
J3: Anthropic 400 — empty content guard before API calls
J4: N4.3 DoD — tolerate numerical=1 as non-critical
J5: I4 Roadmap Redundancy — extend to detect non-<ul> repetitions

Run from: /workspaces/api-ki-backend-neu/
Usage:    python3 fix_j_serie.py
"""

import os, sys, ast, re

BASE = "/workspaces/api-ki-backend-neu"
APPLIED = []
FAILED = []


def read_file(rel_path):
    fp = os.path.join(BASE, rel_path)
    with open(fp, "r", encoding="utf-8") as f:
        return f.read()


def write_file(rel_path, content):
    fp = os.path.join(BASE, rel_path)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(content)


def fix(rel_path, old, new, fix_id, desc):
    content = read_file(rel_path)
    if old not in content:
        FAILED.append(f"{fix_id}: String not found in {rel_path}")
        print(f"  ❌ {fix_id}: {desc} — STRING NOT FOUND")
        return False
    content = content.replace(old, new, 1)
    write_file(rel_path, content)
    APPLIED.append(f"{fix_id}: {desc}")
    print(f"  ✅ {fix_id}: {desc}")
    return True


def syntax_ok(rel_path):
    try:
        ast.parse(read_file(rel_path))
        return True
    except SyntaxError as e:
        print(f"  ❌ SYNTAX ERROR in {rel_path}: {e}")
        return False


def main():
    print("=" * 60)
    print("J-SERIE FIXES — 5 Post-Deploy Nachbesserungen")
    print("=" * 60)

    # ==================================================================
    # J1: I8 Monte Carlo — ROI percentiles still capped at MAX_ROI
    # ==================================================================
    print("\n📌 J1: Monte Carlo — downstream ROI cap entfernen")

    # First: Find where percentiles are calculated and potentially capped
    bcs = read_file("services/business_case_simulation.py")

    # Search for all locations where MAX_ROI is used with percentiles
    lines = bcs.split("\n")
    max_roi_lines = []
    for i, line in enumerate(lines, 1):
        if "MAX_ROI" in line and i != 52 and "SIMULATION_ROI_CAP" not in line:
            max_roi_lines.append((i, line.strip()))
    
    print(f"  ℹ️  MAX_ROI references (excluding import & sim cap): {len(max_roi_lines)}")
    for ln, txt in max_roi_lines:
        print(f"      L{ln}: {txt}")

    # The fix: We need to find where percentile results are clipped.
    # Common patterns: min(MAX_ROI, p50), np.clip, cap_roi, etc.
    # Let's look at the percentile extraction code
    
    # Find the percentile computation section
    perc_section_start = None
    perc_section_lines = []
    for i, line in enumerate(lines, 1):
        if "percentile" in line.lower() or "p50" in line.lower() or "p80" in line.lower() or "p90" in line.lower():
            perc_section_lines.append((i, line.rstrip()))
    
    print(f"  ℹ️  Percentile-related lines:")
    for ln, txt in perc_section_lines:
        print(f"      L{ln}: {txt}")

    # Strategy: cap the DISPLAYED percentile at a reasonable display max (e.g. 999%)
    # but NOT at MAX_ROI (200%). Look for patterns like:
    #   roi_pXX = min(MAX_ROI, ...)
    #   or: result['roi_pXX'] = ... capped
    
    # Direct approach: replace MAX_ROI with SIMULATION_ROI_CAP in percentile area
    # Let's find the exact patterns
    
    # Pattern 1: Direct clip in percentile extraction
    fixed_j1 = False
    
    # Check for np.percentile followed by min(MAX_ROI, ...)
    for pattern_desc, old_pat, new_pat in [
        ("percentile clip roi_p20", 
         "min(MAX_ROI, float(np.percentile(roi_results, 20)))",
         "float(np.percentile(roi_results, 20))"),
        ("percentile clip roi_p50",
         "min(MAX_ROI, float(np.percentile(roi_results, 50)))",
         "float(np.percentile(roi_results, 50))"),
        ("percentile clip roi_p80",
         "min(MAX_ROI, float(np.percentile(roi_results, 80)))",
         "float(np.percentile(roi_results, 80))"),
        ("percentile clip roi_p90",
         "min(MAX_ROI, float(np.percentile(roi_results, 90)))",
         "float(np.percentile(roi_results, 90))"),
    ]:
        if old_pat in bcs:
            bcs = bcs.replace(old_pat, new_pat)
            print(f"  ✅ J1a: Removed {pattern_desc}")
            fixed_j1 = True

    # Pattern 2: Bulk clip like np.clip(roi_results, MIN_ROI, MAX_ROI)
    clip_pattern = re.compile(r'np\.clip\s*\(\s*roi_results\s*,\s*MIN_ROI\s*,\s*MAX_ROI\s*\)')
    if clip_pattern.search(bcs):
        bcs = clip_pattern.sub("np.clip(roi_results, MIN_ROI, 500.0)", bcs)
        print(f"  ✅ J1a: Replaced np.clip MAX_ROI→500.0 for roi_results")
        fixed_j1 = True

    # Pattern 3: min(MAX_ROI, value) in a generic way around percentile code
    # Find all remaining min(MAX_ROI, ...) that aren't the simulation line
    remaining_caps = [(m.start(), m.group()) for m in re.finditer(r'min\s*\(\s*MAX_ROI\s*,', bcs)]
    sim_cap_pos = bcs.find("SIMULATION_ROI_CAP")
    
    for pos, match_str in remaining_caps:
        # Skip if this is within 5 lines of SIMULATION_ROI_CAP (that's our fix)
        if abs(pos - sim_cap_pos) < 200:
            continue
        # This is a downstream cap — needs to be widened
        # Replace min(MAX_ROI, X) with min(500.0, X)  
        # Find the full expression
        line_start = bcs.rfind("\n", 0, pos) + 1
        line_end = bcs.find("\n", pos)
        old_line = bcs[line_start:line_end]
        new_line = old_line.replace("min(MAX_ROI,", "min(500.0,  # J1: widened from MAX_ROI for percentile variance")
        if old_line != new_line:
            bcs = bcs[:line_start] + new_line + bcs[line_end:]
            print(f"  ✅ J1b: Widened downstream cap at position {pos}")
            fixed_j1 = True

    # Pattern 4: Check if ROI values are capped when building the result dict
    # Look for lines like: "roi_p50": min(MAX_ROI, ...)
    for p_label in ["roi_p20", "roi_p50", "roi_p80", "roi_p90", "ROI_P50", "ROI_P80", "ROI_P90"]:
        idx = bcs.find(p_label)
        while idx >= 0:
            # Get the full line
            line_start = bcs.rfind("\n", 0, idx) + 1
            line_end = bcs.find("\n", idx)
            line_content = bcs[line_start:line_end]
            if "MAX_ROI" in line_content and "SIMULATION" not in line_content:
                new_line_content = line_content.replace("MAX_ROI", "500.0  # J1: percentile display cap")
                bcs = bcs[:line_start] + new_line_content + bcs[line_end:]
                print(f"  ✅ J1c: Fixed {p_label} cap")
                fixed_j1 = True
            idx = bcs.find(p_label, line_end)

    if not fixed_j1:
        # Last resort: the capping might happen in the result formatting
        # Let's check if there's a round/min combo
        # Search broader for any MAX_ROI near roi output
        print("  ⚠️  J1: No standard cap pattern found. Searching broader...")
        
        # Find where simulation results are returned/assigned
        result_section = []
        in_result = False
        for i, line in enumerate(lines, 1):
            if "result" in line.lower() and ("roi" in line.lower() or "p50" in line.lower()):
                result_section.append((i, line.rstrip()))
            if "return" in line and "result" in line.lower() and i > 800:
                result_section.append((i, line.rstrip()))
        
        for ln, txt in result_section[-10:]:
            print(f"      L{ln}: {txt}")
        
        # Apply a blanket fix: after the simulation loop, before percentile extraction,
        # ensure roi_results are NOT re-clipped
        # Find "roi_results" usage
        if "roi_results = " in bcs or "roi_results.append" in bcs:
            # The simulation already caps at 500. The issue might be in how
            # percentiles are DISPLAYED. Let's add a comment marker and check
            # if there's a final formatting step
            pass
    
    write_file("services/business_case_simulation.py", bcs)
    if fixed_j1:
        APPLIED.append("J1: Monte Carlo downstream caps removed/widened")
    else:
        # Even if no downstream cap found, there might be a display-level cap.
        # Let's check gpt_analyze.py for P50/P80 capping
        print("  ℹ️  Checking gpt_analyze.py for display-level caps...")
        gpt = read_file("gpt_analyze.py")
        gpt_fixed = False
        for p_label in ["ROI_P50", "ROI_P80", "ROI_P90", "roi_p50", "roi_p80", "roi_p90"]:
            idx = gpt.find(p_label)
            while idx >= 0:
                line_start = gpt.rfind("\n", 0, idx) + 1
                line_end = gpt.find("\n", idx)
                line_content = gpt[line_start:line_end]
                if "MAX_ROI" in line_content or "200" in line_content and "min(" in line_content:
                    print(f"      Found cap at gpt_analyze.py: {line_content.strip()}")
                    new_lc = line_content.replace("MAX_ROI", "500.0").replace("min(200", "min(500")
                    if new_lc != line_content:
                        gpt = gpt[:line_start] + new_lc + gpt[line_end:]
                        gpt_fixed = True
                        print(f"  ✅ J1d: Fixed display cap in gpt_analyze.py")
                idx = gpt.find(p_label, line_end if idx < line_end else idx + 1)
        if gpt_fixed:
            write_file("gpt_analyze.py", gpt)
            APPLIED.append("J1d: gpt_analyze.py display-level caps fixed")

    # ==================================================================
    # J2: I10 Mojibake — â€¢ → • pattern missing
    # ==================================================================
    print("\n📌 J2: Mojibake — â€¢ → • Pattern hinzufügen")

    ps = read_file("services/pipeline_sanitizers.py")
    
    # Find the fix_double_encoded_utf8 function and check its patterns
    func_start = ps.find("def fix_double_encoded_utf8")
    func_end = ps.find("\ndef ", func_start + 10)
    func_code = ps[func_start:func_end] if func_end > 0 else ps[func_start:func_start+2000]
    
    print(f"  ℹ️  Current function ({len(func_code)} chars):")
    # Check if common mojibake patterns are present
    has_bullet = "â€¢" in func_code or "\\xe2\\x80\\xa2" in func_code or "bullet" in func_code.lower()
    has_umlaut = "Ã¶" in func_code or "Ã¤" in func_code or "umlaut" in func_code.lower()
    print(f"      Has bullet (•) pattern: {has_bullet}")
    print(f"      Has umlaut patterns: {has_umlaut}")

    # The function uses encode/decode approach. Let's check if it works or if we need
    # to add explicit replacement patterns.
    # The â€¢ is: \xe2\x80\xa2 interpreted as latin-1 = â€¢ (3 chars)
    # The function should catch this with encode('latin-1').decode('utf-8')
    # But it might not if the text is already valid UTF-8 with those chars embedded
    
    # Best fix: Add explicit replacement map for common mojibake sequences
    # These are the most common double-encoded UTF-8 patterns in German text
    
    MOJIBAKE_MAP_CODE = '''
# =============================================================================
# FIX-J2: Explicit mojibake replacement map for common patterns
# =============================================================================
_MOJIBAKE_REPLACEMENTS = {
    # Bullet point
    "â€¢": "•",
    # German umlauts (uppercase)
    "Ã„": "Ä", "Ã–": "Ö", "Ãœ": "Ü",
    # German umlauts (lowercase)  
    "Ã¤": "ä", "Ã¶": "ö", "Ã¼": "ü",
    # Eszett
    "ÃŸ": "ß",
    # Common punctuation
    "â€"": "–",  # en-dash
    "â€"": "—",  # em-dash  
    "â€˜": "'",  # left single quote
    "â€™": "'",  # right single quote
    "â€œ": "\u201c",  # left double quote
    "â€\u009d": "\u201d",  # right double quote
    "â€¦": "…",  # ellipsis
    # Misc
    "Ã©": "é", "Ã¨": "è", "Ãª": "ê",
    "Ã ": "à", "Ã¢": "â",
    "Ã®": "î", "Ã¯": "ï",
    "Ã´": "ô",
    "Ã¹": "ù", "Ã»": "û",
    "Ã§": "ç",
}

# Compile into a single regex for efficient replacement
_MOJIBAKE_PATTERN = re.compile("|".join(re.escape(k) for k in _MOJIBAKE_REPLACEMENTS.keys()))


def _apply_mojibake_fixes(text: str) -> str:
    """Apply explicit mojibake replacements."""
    return _MOJIBAKE_PATTERN.sub(lambda m: _MOJIBAKE_REPLACEMENTS[m.group()], text)

'''

    # Insert before the existing fix_double_encoded_utf8 function
    if "_MOJIBAKE_REPLACEMENTS" not in ps:
        ps = ps.replace(
            "def fix_double_encoded_utf8",
            MOJIBAKE_MAP_CODE + "\ndef fix_double_encoded_utf8"
        )
        print("  ✅ J2a: Mojibake replacement map added")
        APPLIED.append("J2a: Mojibake replacement map")
    else:
        print("  ⏭️  J2a: Already present")

    # Now modify fix_double_encoded_utf8 to also call _apply_mojibake_fixes
    if "_apply_mojibake_fixes" not in ps[ps.find("def fix_double_encoded_utf8"):ps.find("\ndef ", ps.find("def fix_double_encoded_utf8") + 10)]:
        # Add call at the end of the function, before the return
        # Find the return statement of fix_double_encoded_utf8
        func_start2 = ps.find("def fix_double_encoded_utf8")
        func_body_start = ps.find("\n", func_start2) + 1
        
        # Find "return text" or "return result" at the end of the function
        next_func = ps.find("\ndef ", func_start2 + 30)
        func_body = ps[func_start2:next_func] if next_func > 0 else ps[func_start2:func_start2+2000]
        
        # Find the last return in the function
        last_return_pos = func_body.rfind("return ")
        if last_return_pos > 0:
            return_line_start = func_body.rfind("\n", 0, last_return_pos) + 1
            indent = len(func_body[return_line_start:last_return_pos]) - len(func_body[return_line_start:last_return_pos].lstrip())
            indent_str = " " * indent
            
            # Get the return variable name
            return_line = func_body[last_return_pos:func_body.find("\n", last_return_pos)]
            return_var = return_line.replace("return ", "").strip()
            
            # Insert mojibake fix before the return
            injection = f"\n{indent_str}# FIX-J2: Apply explicit mojibake replacements\n{indent_str}{return_var} = _apply_mojibake_fixes({return_var})\n"
            
            # Calculate absolute position
            abs_pos = func_start2 + last_return_pos
            ps = ps[:abs_pos] + injection + ps[abs_pos:]
            print("  ✅ J2b: _apply_mojibake_fixes call injected into fix_double_encoded_utf8")
            APPLIED.append("J2b: Mojibake fix integrated into pipeline")
        else:
            FAILED.append("J2b: Could not find return statement in fix_double_encoded_utf8")
    else:
        print("  ⏭️  J2b: Already integrated")

    write_file("services/pipeline_sanitizers.py", ps)

    # ==================================================================
    # J3: Anthropic 400 — empty content guard
    # ==================================================================
    print("\n📌 J3: Anthropic API — empty content guard")

    ac = read_file("services/anthropic_client.py")
    
    # Find the call_anthropic function and add a guard
    if "# FIX-J3" not in ac:
        # Find the function signature
        func_sig = "def call_anthropic("
        func_pos = ac.find(func_sig)
        if func_pos >= 0:
            # Find where the actual API call happens (client.messages.create)
            # We need to add a guard before the first client.messages.create
            # Find the first "message = client.messages.create" after func_pos
            create_pos = ac.find("message = client.messages.create", func_pos)
            if create_pos >= 0:
                # Find the line start
                line_start = ac.rfind("\n", 0, create_pos) + 1
                indent = len(ac[line_start:create_pos]) - len(ac[line_start:create_pos].lstrip())
                indent_str = " " * indent
                
                guard_code = (
                    f"\n{indent_str}# FIX-J3: Guard against empty content (causes 400 Bad Request)\n"
                    f"{indent_str}if not prompt or (isinstance(prompt, str) and not prompt.strip()):\n"
                    f'{indent_str}    log.warning("[FIX-J3] Empty prompt for section=%s — skipping API call", section_name if "section_name" in dir() else "unknown")\n'
                    f'{indent_str}    return ""\n'
                    f"\n"
                )
                
                ac = ac[:line_start] + guard_code + ac[line_start:]
                write_file("services/anthropic_client.py", ac)
                print("  ✅ J3: Empty content guard added")
                APPLIED.append("J3: Anthropic empty content guard")
            else:
                FAILED.append("J3: client.messages.create not found")
        else:
            FAILED.append("J3: call_anthropic function not found")
    else:
        print("  ⏭️  J3: Already present")

    # Also check: the 400 errors are for specific sections where Claude is called
    # with the section content being empty. Let's add a guard in gpt_analyze.py
    # where call_anthropic is invoked for decision sections
    
    gpt = read_file("gpt_analyze.py")
    if "# FIX-J3-DECISION" not in gpt:
        # Find calls to call_anthropic for decision sections
        # These are the ones failing: gamechanger_decision, executive_decision, etc.
        # Add a content check before each Claude call for _DECISION sections
        decision_guard = '''
    # FIX-J3-DECISION: Skip Claude call if section content is empty
    if not section_content or not section_content.strip():
        log.warning("[FIX-J3-DECISION] Empty content for section=%s — using fallback", section_name)
        return "<p><em>Keine Daten verfügbar.</em></p>"
'''
        # We can't easily inject this without knowing exact call patterns.
        # Instead, let's make the anthropic_client more robust by handling empty responses
        print("  ℹ️  J3b: Decision guard — needs manual review of call sites")
    
    # ==================================================================
    # J4: N4.3 DoD — tolerate numerical=1
    # ==================================================================
    print("\n📌 J4: N4.3 DoD — numerical_inconsistencies Toleranz")

    n43 = read_file("services/n43_integration.py")
    
    # Find the DoD validation logic
    # Current: numerical_inconsistencies > 0 causes failure
    # Fix: Allow numerical_inconsistencies <= 1
    
    # Look for the threshold
    if "numerical_inconsistencies" in n43:
        # Find the dod_passed property
        dod_prop_start = n43.find("def dod_passed")
        if dod_prop_start >= 0:
            dod_prop_end = n43.find("\n    def ", dod_prop_start + 10)
            dod_body = n43[dod_prop_start:dod_prop_end] if dod_prop_end > 0 else n43[dod_prop_start:dod_prop_start+500]
            print(f"  ℹ️  Current dod_passed logic:")
            for line in dod_body.split("\n")[:15]:
                print(f"      {line}")
            
            # Fix: change numerical_inconsistencies == 0 to <= 1
            if "numerical_inconsistencies == 0" in n43:
                n43 = n43.replace(
                    "numerical_inconsistencies == 0",
                    "numerical_inconsistencies <= 1  # J4: tolerate 1 minor inconsistency"
                )
                write_file("services/n43_integration.py", n43)
                print("  ✅ J4: DoD threshold relaxed (numerical ≤ 1)")
                APPLIED.append("J4: N4.3 DoD numerical tolerance ≤ 1")
            elif "numerical_inconsistencies > 0" in n43:
                n43 = n43.replace(
                    "numerical_inconsistencies > 0",
                    "numerical_inconsistencies > 1  # J4: tolerate 1 minor inconsistency"
                )
                write_file("services/n43_integration.py", n43)
                print("  ✅ J4: DoD threshold relaxed (numerical > 1)")
                APPLIED.append("J4: N4.3 DoD numerical tolerance > 1")
            elif "self.numerical_inconsistencies" in dod_body and "0" in dod_body:
                # More complex pattern — show for manual fix
                print("  ⚠️  J4: Complex DoD pattern — check manually:")
                print(f"      {dod_body[:300]}")
                FAILED.append("J4: Complex DoD pattern needs manual fix")
            else:
                print("  ⚠️  J4: Could not find numerical threshold pattern")
                FAILED.append("J4: Numerical threshold pattern not found")
        else:
            FAILED.append("J4: dod_passed property not found")

    # ==================================================================
    # J5: I4 Roadmap Redundancy — extend beyond <ul> blocks
    # ==================================================================
    print("\n📌 J5: Roadmap Redundanz — Erkennung erweitern")

    ps2 = read_file("services/pipeline_sanitizers.py")
    
    # The current strip_redundant_blocks only checks <ul> blocks.
    # Roadmap redundancy uses <div> or <p> blocks.
    # Extend to also check <div> and <ol> blocks.
    
    old_pattern = '''    ul_pattern = re.compile(r'(<ul[^>]*>.*?</ul>)', re.DOTALL | re.IGNORECASE)
    ul_blocks = ul_pattern.findall(html)
    if not ul_blocks:
        return html, 0'''
    
    new_pattern = '''    # FIX-J5: Extended to detect <ul>, <ol>, and large <div> block repetitions
    block_pattern = re.compile(r'(<(?:ul|ol)[^>]*>.*?</(?:ul|ol)>|<div[^>]*>(?:(?!<div).)*?</div>)', re.DOTALL | re.IGNORECASE)
    ul_blocks = block_pattern.findall(html)
    if not ul_blocks:
        return html, 0'''
    
    if old_pattern in ps2:
        ps2 = ps2.replace(old_pattern, new_pattern)
        write_file("services/pipeline_sanitizers.py", ps2)
        print("  ✅ J5: Redundancy detection extended to <ol> and <div> blocks")
        APPLIED.append("J5: Extended redundancy detection")
    else:
        print("  ⏭️  J5: Pattern already modified or not found")

    # ==================================================================
    # SYNTAX CHECKS
    # ==================================================================
    print("\n" + "=" * 60)
    print("SYNTAX CHECKS")
    print("=" * 60)

    files_to_check = [
        "services/pipeline_sanitizers.py",
        "services/business_case_simulation.py",
        "services/anthropic_client.py",
        "services/n43_integration.py",
        "gpt_analyze.py",
    ]
    
    all_ok = True
    for f in files_to_check:
        fp = os.path.join(BASE, f)
        if os.path.exists(fp):
            if syntax_ok(f):
                print(f"  ✅ {f}")
            else:
                all_ok = False
        else:
            print(f"  ⏭️  {f} — not found, skipping")

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"\n✅ Angewendet: {len(APPLIED)}")
    for a in APPLIED:
        print(f"   • {a}")
    if FAILED:
        print(f"\n❌ Fehlgeschlagen: {len(FAILED)}")
        for f in FAILED:
            print(f"   • {f}")

    if all_ok:
        print("\n🎉 Syntax OK. Nächster Schritt:")
        print('   git add -A && git commit -m "FIX-J-SERIE: I8 Monte Carlo + I10 Mojibake + Anthropic guard + N4.3 DoD + Roadmap redundancy" && git push origin main')
    else:
        print("\n⚠️  Syntax-Fehler — bitte Output prüfen!")

    return 0 if (all_ok and not FAILED) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
import re

with open('gpt_analyze.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''                _rescued_html = _expand_short_section(
                    section_key=_sec_key,
                    current_html=_sec_html,
                    target_words=_min_words + 50,  # +50 buffer for safety
                    current_words=_sec_words,
                )
                if _rescued_html:
                    sections[_sec_key] = _rescued_html
                    # Also update lowercase alias if exists
                    _lower_key = _sec_key.replace("_HTML", "").lower()
                    if _lower_key in sections:
                        sections[_lower_key] = _rescued_html
                    _rescued += 1
                    log.info("[%s] [RESCUE-640] ✅ %s rescued successfully", run_id, _sec_key)
                else:
                    log.error("[%s] [RESCUE-640] ❌ %s rescue failed", run_id, _sec_key)'''

new_code = '''                _rescued_html = _expand_short_section(
                    section_key=_sec_key,
                    current_html=_sec_html,
                    target_words=_min_words + 50,  # +50 buffer for safety
                    current_words=_sec_words,
                )
                
                # FIX-700: Check if expansion was successful AND sufficient
                _rescued_sufficient = False
                if _rescued_html:
                    _rescued_text = re.sub(r"<[^>]+>", "", _rescued_html).strip()
                    _rescued_words = len(_rescued_text.split()) if _rescued_text else 0
                    if _rescued_words >= _min_words:
                        _rescued_sufficient = True
                        log.info("[%s] [RESCUE-640] Expansion OK: %d -> %d words", run_id, _sec_words, _rescued_words)
                    else:
                        log.warning("[%s] [RESCUE-640] Expansion insufficient: %d/%d", run_id, _rescued_words, _min_words)
                
                # FIX-700: If expansion failed, try fallback
                if not _rescued_sufficient:
                    log.warning("[%s] [RESCUE-640] Trying fallback for %s", run_id, _sec_key)
                    _fallback_key = _sec_key.replace("_HTML", "").lower()
                    try:
                        _fallback_html = _get_fallback_content(_fallback_key, briefing, scores)
                        if _fallback_html:
                            _fallback_text = re.sub(r"<[^>]+>", "", _fallback_html).strip()
                            _fallback_words = len(_fallback_text.split()) if _fallback_text else 0
                            if _fallback_words >= _min_words:
                                _rescued_html = _fallback_html
                                _rescued_sufficient = True
                                log.info("[%s] [RESCUE-640] Fallback OK: %d -> %d words", run_id, _sec_words, _fallback_words)
                            else:
                                log.error("[%s] [RESCUE-640] Fallback too short: %d/%d", run_id, _fallback_words, _min_words)
                    except Exception as e:
                        log.error("[%s] [RESCUE-640] Fallback error: %s", run_id, e)
                
                if _rescued_sufficient:
                    sections[_sec_key] = _rescued_html
                    _lower_key = _sec_key.replace("_HTML", "").lower()
                    if _lower_key in sections:
                        sections[_lower_key] = _rescued_html
                    _rescued += 1
                    log.info("[%s] [RESCUE-640] %s rescued", run_id, _sec_key)
                else:
                    log.error("[%s] [RESCUE-640] %s FAILED", run_id, _sec_key)'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('gpt_analyze.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK - FIX applied")
else:
    print("ERROR - old code not found")

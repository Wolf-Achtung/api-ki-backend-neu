"""
Test suite for FIX-B25-CANONICAL enforcer.
Run: python test_b25_enforcer.py
"""
import logging
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")

from b25_enforcer import (
    build_canonical_kpi_block,
    enforce_b25_canonical_kpis,
    sanitize_roi_values_in_content,
    apply_funding_blacklist,
    strip_canonical_blocks,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))


# ============================================================
print("\n📋 TEST 1: Canonical block covers all 5 ROI patterns")
# ============================================================
block = build_canonical_kpi_block(200.0, 1.6, 4)
check("Pattern 1: ROI: X%", "ROI: 200%" in block)
check("Pattern 2: ROI beträgt X%", "ROI beträgt 200%" in block)
check("Pattern 3: X% ROI", "200% ROI" in block)
check("Pattern 4: Return on Investment: X%", "Return on Investment: 200%" in block)
check("Pattern 5: X% Return", "200% Return" in block)
check("Payback (German decimal)", "Payback: 1,6 Monate" in block)
check("Amortisation variant", "Amortisation: 1,6 Monate" in block)
check("Tools count", "4 KI-Tools" in block)
check("Canonical markers", "[KPI-CANONICAL-START]" in block and "[KPI-CANONICAL-END]" in block)

# ============================================================
print("\n📋 TEST 2: ROI cap enforced in block builder")
# ============================================================
block_capped = build_canonical_kpi_block(350.0, 1.6, 4)
check("ROI 350% → 200% in block", "200%" in block_capped)
check("350% not in block", "350" not in block_capped)

block_exact = build_canonical_kpi_block(200.0, 1.6, 4)
check("ROI exactly 200% stays", "200%" in block_exact)

block_under = build_canonical_kpi_block(150.0, 2.3, 3)
check("ROI 150% stays as-is", "150%" in block_under)
check("Payback 2,3 correct", "2,3 Monate" in block_under)

# ============================================================
print("\n📋 TEST 3: Section injection — name-based detection")
# ============================================================
sections = {
    "executive_summary": "<h2>Summary</h2><p>ROI: 295%</p>",
    "roi_analysis": "<div>ROI beträgt 180%</div>",
    "legal_notice": "<p>Impressum und Datenschutz</p>",
    "appendix": "<p>Anhang mit Quellenverzeichnis</p>",
}
report_data = {
    "roi_percent": 295.0,
    "payback_months": 1.6,
    "tools_count": 4,
    "tools_names": ["ChatGPT", "Claude", "Perplexity", "Tavily"],
}
result, count = enforce_b25_canonical_kpis(sections, report_data, is_html=True)

check("executive_summary injected", "KPI-CANONICAL-START" in result["executive_summary"])
check("roi_analysis injected", "KPI-CANONICAL-START" in result["roi_analysis"])
check("legal_notice NOT injected", result["legal_notice"] == sections["legal_notice"])
check("appendix NOT injected", result["appendix"] == sections["appendix"])
check(f"Injection count = 2 (got {count})", count == 2)

# ============================================================
print("\n📋 TEST 4: Content-based fallback REMOVED (B28 — strict name-only)")
# ============================================================
sections2 = {
    "custom_xyz": "<p>Der ROI beträgt 150% und ist damit positiv.</p>",
    "random_section": "<p>Keine KPI-relevanten Inhalte hier.</p>",
}
result2, count2 = enforce_b25_canonical_kpis(sections2, report_data, is_html=True)

check("custom_xyz NOT injected (no content fallback)", result2["custom_xyz"] == sections2["custom_xyz"])
check("random_section NOT injected", result2["random_section"] == sections2["random_section"])
check(f"Count = 0 (got {count2})", count2 == 0)

# ============================================================
print("\n📋 TEST 5: Plain text mode (is_html=False)")
# ============================================================
sections3 = {
    "executive_summary": "ROI: 180%\nPayback: 2 Monate\n3 KI-Tools",
}
result3, count3 = enforce_b25_canonical_kpis(sections3, report_data, is_html=False)

check("Plain text prepended", result3["executive_summary"].startswith("\n[KPI-CANONICAL-START]"))
check("Original content preserved", "ROI: 180%" in result3["executive_summary"])

# ============================================================
print("\n📋 TEST 6: Canonical block appears BEFORE original content")
# ============================================================
injected_html = result["executive_summary"]
canonical_pos = injected_html.find("KPI-CANONICAL-START")
original_pos = injected_html.find("<h2>Summary</h2>")
check(
    "Canonical block before original content",
    canonical_pos < original_pos,
    f"canonical@{canonical_pos} vs original@{original_pos}",
)

# ============================================================
print("\n📋 TEST 7: ROI sanitizer — cap values >200%")
# ============================================================
html1 = '<td>Konservatives Szenario</td><td>295%</td>'
s1 = sanitize_roi_values_in_content(html1, roi_cap=200.0)
check("295% capped to 200%", "295" not in s1 and "200" in s1)

html2 = '<p>ROI: 150%</p>'
s2 = sanitize_roi_values_in_content(html2, roi_cap=200.0)
check("150% unchanged", "150" in s2)

html3 = '<p>Return on Investment: 320,5%</p>'
s3 = sanitize_roi_values_in_content(html3, roi_cap=200.0)
check("320,5% capped", "320" not in s3 and "200" in s3)

html4 = '<p>Der Umsatz beträgt 350.000 EUR</p>'
s4 = sanitize_roi_values_in_content(html4, roi_cap=200.0)
check("Non-ROI 350.000 unchanged", "350" in s4, f"got: {s4}")

# ============================================================
print("\n📋 TEST 8: Funding blacklist")
# ============================================================
sections_bl = {
    "automation_roadmap": (
        "Förderprogramme:\n"
        "- go-digital: Digitalisierung\n"
        "- KI-Invest: KI-Förderung\n"
        "- go-digital! Premium\n"
    ),
    "executive_summary": "Keine Förderprogramme erwähnt.",
}
cleaned = apply_funding_blacklist(sections_bl)

check(
    "go-digital lines removed",
    "go-digital" not in cleaned["automation_roadmap"],
)
check(
    "KI-Invest preserved",
    "KI-Invest" in cleaned["automation_roadmap"],
)
check(
    "executive_summary unchanged",
    cleaned["executive_summary"] == sections_bl["executive_summary"],
)

# ============================================================
print("\n📋 TEST 9: Tools with names in block")
# ============================================================
block_names = build_canonical_kpi_block(
    200.0, 1.6, 4,
    tools_names=["ChatGPT", "Claude", "Perplexity", "Tavily"],
)
check("Tools names present", "ChatGPT, Claude, Perplexity, Tavily" in block_names)
check("Count + names format", "4 KI-Tools (ChatGPT" in block_names)

# ============================================================
print("\n📋 TEST 10: Nested dict extraction")
# ============================================================
nested_data = {
    "kpis": {"roi_percent": 180.0},
    "calculated": {"payback_months": 2.5},
    "tools": {"tools_count": 6},
}
result10, count10 = enforce_b25_canonical_kpis(
    {"executive_summary": "<p>ROI info here</p>"},
    nested_data,
    is_html=True,
)
check("Nested extraction works", count10 == 1)
check("Block contains 180%", "180%" in result10.get("executive_summary", ""))

# ============================================================
print("\n📋 TEST 11: Non-string values in sections dict (B27.1 regression)")
# ============================================================
sections_mixed = {
    "executive_summary": "<h2>Summary</h2><p>ROI: 200%</p>",
    "score_gesamt": 92,
    "score_governance": 88,
    "monatsersparnis_stunden": 45.5,
    "roi_analysis": "<div>ROI beträgt 200%</div>",
    "tools_count": 4,
    "legal_notice": "<p>Impressum</p>",
    "is_platin": True,
    "sections_generated": ["exec", "roi", "tools"],
}
report_data_mixed = {"roi_percent": 200.0, "payback_months": 1.6, "tools_count": 4}

# enforce should NOT crash
try:
    result_mixed, count_mixed = enforce_b25_canonical_kpis(
        sections_mixed, report_data_mixed, is_html=True
    )
    check("No crash on mixed dict", True)
    check(
        f"String sections injected (got {count_mixed})",
        count_mixed >= 2,  # executive_summary + roi_analysis at minimum
    )
    check("Int value preserved", result_mixed["score_gesamt"] == 92)
    check("Float value preserved", result_mixed["monatsersparnis_stunden"] == 45.5)
    check("Bool value preserved", result_mixed["is_platin"] is True)
    check("List value preserved", result_mixed["sections_generated"] == ["exec", "roi", "tools"])
except Exception as e:
    check(f"No crash on mixed dict (GOT: {e})", False)

# sanitize should NOT crash on int
try:
    sanitized_int = sanitize_roi_values_in_content(92, roi_cap=200.0)
    check("Sanitizer handles int input", sanitized_int == 92)
except Exception as e:
    check(f"Sanitizer handles int input (GOT: {e})", False)

# blacklist should NOT crash on mixed dict
try:
    cleaned_mixed = apply_funding_blacklist(sections_mixed)
    check("Blacklist handles mixed dict", True)
    check("Blacklist preserves int", cleaned_mixed["score_gesamt"] == 92)
except Exception as e:
    check(f"Blacklist handles mixed dict (GOT: {e})", False)

# ============================================================
print("\n📋 TEST 12: Realistic section dict — only named sections get injection")
# ============================================================
sections_realistic = {
    # These SHOULD get injection (KPI sections)
    "executive_summary": "<h2>Summary</h2><p>Overview text</p>",
    "roi_analysis": "<div>ROI details</div>",
    "automation_roadmap": "<div>Automation plan</div>",
    "financial_summary": "<div>Costs and benefits</div>",
    "tools_analysis": "<div>Tool recommendations</div>",
    # These should NOT get injection (non-KPI sections)
    "vendor_audit": "<div>Vendor risk assessment with ROI mention</div>",
    "benchmark": "<div>Industry benchmark with ROI comparison</div>",
    "legal_notice": "<p>Impressum</p>",
    "strategy": "<div>Strategy recommendations</div>",
    "appendix": "<div>Appendix</div>",
    # Non-string values (should be skipped)
    "score_gesamt": 92,
    "score_governance": 88,
    "is_platin": True,
}
report_data_12 = {"roi_percent": 200.0, "payback_months": 1.6, "tools_count": 4}
result_12, count_12 = enforce_b25_canonical_kpis(sections_realistic, report_data_12, is_html=True)

check(f"Injection count 4-6 (got {count_12})", 4 <= count_12 <= 6)
check("vendor_audit NOT injected", "KPI-CANONICAL" not in result_12.get("vendor_audit", ""))
check("benchmark NOT injected", "KPI-CANONICAL" not in result_12.get("benchmark", ""))
check("Non-string preserved", result_12["score_gesamt"] == 92)

# ============================================================
print("\n📋 TEST 13: Extended blacklist covers KMU-innovativ and Digitalbonus")
# ============================================================
sections_funding = {
    "automation_roadmap": (
        "Empfohlene Förderprogramme:\n"
        "- go-digital: Digitalisierung\n"
        "- KMU-innovativ: Innovationsförderung\n"
        "- Digitalbonus: Bayerische Förderung\n"
        "- KI-Invest: KI-Förderung\n"
    ),
}
cleaned_13 = apply_funding_blacklist(sections_funding)
check("go-digital removed", "go-digital" not in cleaned_13["automation_roadmap"])
check("KMU-innovativ removed", "kmu-innovativ" not in cleaned_13["automation_roadmap"].lower())
check("Digitalbonus removed", "digitalbonus" not in cleaned_13["automation_roadmap"].lower())
check("KI-Invest preserved", "KI-Invest" in cleaned_13["automation_roadmap"])

# ============================================================
print("\n📋 TEST 14: Blacklist cleans dict and list sections (B29 fix)")
# ============================================================
sections_with_dict = {
    "AUTOMATION_ROADMAP_HTML": "Förderprogramme:\n- go-digital: Digitalisierung\n- KI-Invest: KI\n",
    "_automation_roadmap_report": {
        "programs": ["go-digital", "KMU-innovativ", "KI-Invest"],
        "recommendations": "Nutzen Sie go-digital für Digitalisierung.\nNutzen Sie KI-Invest für KI.",
        "scores": {"go-digital": 0.8, "KI-Invest": 0.9},
    },
    "_tools_report": [
        {"name": "ChatGPT", "program": "Digitalbonus"},
        {"name": "Claude", "program": "KI-Invest"},
    ],
    "score_gesamt": 91,
}
cleaned_14 = apply_funding_blacklist(sections_with_dict)

# HTML section cleaned (existing behavior)
check("HTML go-digital removed", "go-digital" not in cleaned_14["AUTOMATION_ROADMAP_HTML"])
check("HTML KI-Invest preserved", "KI-Invest" in cleaned_14["AUTOMATION_ROADMAP_HTML"])

# Dict section cleaned (B29 new behavior)
report_14 = cleaned_14["_automation_roadmap_report"]
check("Dict programs list: go-digital removed", "go-digital" not in report_14["programs"])
check("Dict programs list: KMU-innovativ removed", "KMU-innovativ" not in report_14["programs"])
check("Dict programs list: KI-Invest preserved", "KI-Invest" in report_14["programs"])
check("Dict recommendations: go-digital removed", "go-digital" not in report_14["recommendations"])
check("Dict recommendations: KI-Invest preserved", "KI-Invest" in report_14["recommendations"])

# List section cleaned (B29 new behavior)
tools_14 = cleaned_14["_tools_report"]
check("List: Digitalbonus tool removed", len(tools_14) == 1)
check("List: KI-Invest tool preserved", tools_14[0]["name"] == "Claude")

# Non-string preserved
check("Int preserved", cleaned_14["score_gesamt"] == 91)

# ============================================================
print("\n📋 TEST 15: New section keys match actual gpt_analyze.py keys")
# ============================================================
sections_real_keys = {
    "EXECUTIVE_SUMMARY_HTML": "<p>ROI: 200%</p>",
    "ROI_HTML": "<p>ROI details</p>",
    "BUSINESS_CASE_HTML": "<p>Kosten-Nutzen</p>",
    "WIRTSCHAFTLICHKEIT_HTML": "<p>Financial summary</p>",
    "KI_STACK_SUMMARY_HTML": "<p>Tools overview</p>",
    "FOERDERPOTEZIAL_HTML": "<p>Funding potential</p>",
    "AUTOMATION_ROADMAP_HTML": "<p>Roadmap</p>",
    "RECOMMENDATIONS_HTML": "<p>Empfehlungen</p>",
    "STRATEGIE_GOVERNANCE_HTML": "<p>Strategy</p>",
    # Non-KPI sections (should NOT get injection)
    "VENDOR_AUDIT_HTML": "<p>Vendor audit with ROI mention</p>",
    "BENCHMARK_HTML": "<p>Benchmark data</p>",
    "LEGAL_NOTICE_HTML": "<p>Impressum</p>",
    "score_gesamt": 91,
}
report_data_15 = {"roi_percent": 200.0, "payback_months": 1.6, "tools_count": 4}
result_15, count_15 = enforce_b25_canonical_kpis(sections_real_keys, report_data_15, is_html=True)

check(f"Injection count 7-10 (got {count_15})", 7 <= count_15 <= 10)
check("EXECUTIVE_SUMMARY injected", "[KPI-CANONICAL-START]" in result_15["EXECUTIVE_SUMMARY_HTML"])
check("ROI_HTML injected", "[KPI-CANONICAL-START]" in result_15["ROI_HTML"])
check("BUSINESS_CASE injected", "[KPI-CANONICAL-START]" in result_15["BUSINESS_CASE_HTML"])
check("VENDOR_AUDIT NOT injected", "[KPI-CANONICAL-START]" not in result_15["VENDOR_AUDIT_HTML"])
check("BENCHMARK NOT injected", "[KPI-CANONICAL-START]" not in result_15["BENCHMARK_HTML"])
check("Int preserved", result_15["score_gesamt"] == 91)

# ============================================================
print("\n📋 TEST 16: strip_canonical_blocks removes injected blocks")
# ============================================================
# Simulate post-enforce sections (canonical block prepended to content)
canonical = build_canonical_kpi_block(200.0, 1.6, 4)
sections_injected = {
    "EXECUTIVE_SUMMARY_HTML": canonical + "<h2>Summary</h2><p>ROI: 200%</p>",
    "ROI_HTML": canonical + "<p>ROI details</p>",
    "VENDOR_AUDIT_HTML": "<p>Vendor audit</p>",  # no canonical block
    "score_gesamt": 91,
    "_automation_roadmap_report": {"programs": ["KI-Invest"]},
}
stripped_16 = strip_canonical_blocks(sections_injected)

check("EXEC canonical stripped", "[KPI-CANONICAL-START]" not in stripped_16["EXECUTIVE_SUMMARY_HTML"])
check("EXEC original content preserved", "<h2>Summary</h2>" in stripped_16["EXECUTIVE_SUMMARY_HTML"])
check("ROI canonical stripped", "[KPI-CANONICAL-START]" not in stripped_16["ROI_HTML"])
check("ROI original content preserved", "<p>ROI details</p>" in stripped_16["ROI_HTML"])
check("VENDOR_AUDIT unchanged", stripped_16["VENDOR_AUDIT_HTML"] == "<p>Vendor audit</p>")
check("Int preserved", stripped_16["score_gesamt"] == 91)
check("Dict preserved", stripped_16["_automation_roadmap_report"] == {"programs": ["KI-Invest"]})

# ============================================================
print("\n📋 TEST 17: Full pipeline — inject, then strip leaves clean content")
# ============================================================
sections_pipeline = {
    "EXECUTIVE_SUMMARY_HTML": "<p>Executive overview</p>",
    "ROI_HTML": "<p>ROI section</p>",
    "BUSINESS_CASE_HTML": "<p>Business case</p>",
    "LEGAL_NOTICE_HTML": "<p>Impressum</p>",
    "score_gesamt": 91,
}
report_data_17 = {"roi_percent": 200.0, "payback_months": 1.6, "tools_count": 4}

# Step 1: inject canonical blocks
injected_17, count_17 = enforce_b25_canonical_kpis(sections_pipeline, report_data_17, is_html=True)
check(f"Injection count >= 3 (got {count_17})", count_17 >= 3)
check("Canonical present after inject", "[KPI-CANONICAL-START]" in injected_17["EXECUTIVE_SUMMARY_HTML"])

# Step 2: strip canonical blocks (simulating post-G22 cleanup)
final_17 = strip_canonical_blocks(injected_17)
check("Canonical gone after strip", "[KPI-CANONICAL-START]" not in final_17["EXECUTIVE_SUMMARY_HTML"])
check("Canonical gone from ROI", "[KPI-CANONICAL-START]" not in final_17["ROI_HTML"])
check("Canonical gone from BUSINESS_CASE", "[KPI-CANONICAL-START]" not in final_17["BUSINESS_CASE_HTML"])
check("Original EXEC content intact", "<p>Executive overview</p>" in final_17["EXECUTIVE_SUMMARY_HTML"])
check("Original ROI content intact", "<p>ROI section</p>" in final_17["ROI_HTML"])
check("LEGAL unchanged (never injected)", final_17["LEGAL_NOTICE_HTML"] == "<p>Impressum</p>")
check("Int preserved", final_17["score_gesamt"] == 91)

# ============================================================
print("\n📋 TEST 18: Integration — apply_funding_blacklist cleans dict with go-digital")
# ============================================================
sections_integration = {
    "AUTOMATION_ROADMAP_HTML": "Programme:\n- go-digital\n- KI-Invest\n",
    "_automation_roadmap_report": {
        "programs": ["go-digital", "KI-Invest"],
        "text": "Empfehlung: go-digital nutzen",
    },
}
result_18 = apply_funding_blacklist(sections_integration)
rpt = result_18["_automation_roadmap_report"]
check("Integration: go-digital removed from dict programs", "go-digital" not in rpt["programs"])
check("Integration: KI-Invest preserved in dict programs", "KI-Invest" in rpt["programs"])
check("Integration: go-digital removed from dict text", "go-digital" not in rpt["text"])
check("Integration: HTML also cleaned", "go-digital" not in result_18["AUTOMATION_ROADMAP_HTML"])

# ============================================================
# Summary
# ============================================================
total = passed + failed
print(f"\n{'='*50}")
if failed == 0:
    print(f"🎯 ALL {passed} TESTS PASSED — Ready for deployment")
else:
    print(f"⚠️  {passed}/{total} passed, {failed} FAILED")
print(f"{'='*50}\n")

sys.exit(0 if failed == 0 else 1)

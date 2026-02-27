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

check("executive_summary injected", "kpi-canonical" in result["executive_summary"])
check("roi_analysis injected", "kpi-canonical" in result["roi_analysis"])
check("legal_notice NOT injected", result["legal_notice"] == sections["legal_notice"])
check("appendix NOT injected", result["appendix"] == sections["appendix"])
check(f"Injection count = 2 (got {count})", count == 2)

# ============================================================
print("\n📋 TEST 4: Section injection — content-based detection")
# ============================================================
sections2 = {
    "custom_xyz": "<p>Der ROI beträgt 150% und ist damit positiv.</p>",
    "random_section": "<p>Keine KPI-relevanten Inhalte hier.</p>",
}
result2, count2 = enforce_b25_canonical_kpis(sections2, report_data, is_html=True)

check("custom_xyz injected (content detection)", "kpi-canonical" in result2["custom_xyz"])
check("random_section NOT injected", result2["random_section"] == sections2["random_section"])
check(f"Count = 1 (got {count2})", count2 == 1)

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
check("Block contains 180%", "180%" in result10["executive_summary"])

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

"""Smoke tests for b25_enforcer.py — B25 Canonical KPI Injection."""

from b25_enforcer import (
    build_canonical_kpi_block,
    enforce_b25_canonical_kpis,
    sanitize_roi_values_in_content,
    apply_funding_blacklist,
)

# Test 1: Block covers all 5 patterns
block = build_canonical_kpi_block(200.0, 1.6, 4)
assert "ROI: 200%" in block
assert "ROI beträgt 200%" in block
assert "200% ROI" in block
assert "Return on Investment: 200%" in block
assert "200% Return" in block
assert "Payback: 1,6 Monate" in block
assert "4 KI-Tools" in block
print("Test 1 PASSED: All 5 ROI patterns present")

# Test 2: Injection works on HTML content
sections = {
    "executive_summary": "<h2>Executive Summary</h2><p>Der Return on Investment beträgt 295% bei einer Amortisationsdauer von 1,6 Monaten.</p>",
    "legal_notice": "<p>Impressum und rechtliche Hinweise zu diesem Dokument.</p>",
}
report_data = {"roi_percent": 295.0, "payback_months": 1.6, "tools_count": 4}
result, count = enforce_b25_canonical_kpis(sections, report_data, is_html=True)
assert count == 1  # Only executive_summary gets injection
assert "kpi-canonical" in result["executive_summary"]
assert result["legal_notice"] == sections["legal_notice"]  # Unchanged
print(f"Test 2 PASSED: {count} section(s) injected")

# Test 3: ROI sanitizer caps 295%
html = '<td>Konservatives Szenario</td><td>295%</td>'
sanitized = sanitize_roi_values_in_content(html, roi_cap=200.0)
assert "295" not in sanitized
assert "200" in sanitized
print("Test 3 PASSED: ROI 295% -> 200%")

# Test 4: ROI cap applied in enforce
block2 = build_canonical_kpi_block(350.0, 1.6, 4)
assert "200%" in block2
assert "350" not in block2
print("Test 4 PASSED: ROI cap enforced in canonical block")

# Test 5: Content-based detection (section name doesn't match but content does)
sections2 = {
    "custom_section_xyz": "<p>Der ROI beträgt 150% und die Amortisation dauert 2 Monate. Weitere Details finden Sie im Anhang.</p>",
}
result2, count2 = enforce_b25_canonical_kpis(sections2, report_data, is_html=True)
assert count2 == 1  # Detected via content scan
print("Test 5 PASSED: Content-based KPI detection works")

# Test 6: apply_funding_blacklist removes blacklisted terms
sections3 = {
    "funding": "Zeile 1\ngo-digital Foerderung\nZeile 3\n",
    "other": "Kein Problem hier",
}
cleaned = apply_funding_blacklist(sections3)
assert "go-digital" not in cleaned["funding"]
assert "Zeile 1" in cleaned["funding"]
assert "Zeile 3" in cleaned["funding"]
assert cleaned["other"] == sections3["other"]
print("Test 6 PASSED: Funding blacklist removes go-digital lines")

# Test 7: Non-string content is passed through unchanged
sections4 = {
    "executive_summary": "<p>ROI: 100%</p>",
    "ROI_12M": 200.0,
    "PAYBACK_MONTHS": 1.6,
}
result4, count4 = enforce_b25_canonical_kpis(sections4, sections4, is_html=True)
assert result4["ROI_12M"] == 200.0  # Numeric value unchanged
print("Test 7 PASSED: Non-string values passed through unchanged")

print("\nALL TESTS PASSED — Ready for deployment")

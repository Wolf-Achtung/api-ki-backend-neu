#!/usr/bin/env python3
"""
I-SERIE PDF QUALITY FIXES — Direct Apply Script
=================================================
Applies all 10 fixes (I1-I10) to the KI-Sicherheit.jetzt codebase.
Run from: /workspaces/api-ki-backend-neu/
Usage:    python3 apply_i_serie.py
"""

import os
import sys
import ast

BASE = "/workspaces/api-ki-backend-neu"
FIXES_APPLIED = []
FIXES_FAILED = []


def apply_fix(filepath, old, new, fix_id, description):
    """Replace exact string in file. Reports success/failure."""
    full_path = os.path.join(BASE, filepath)
    if not os.path.exists(full_path):
        FIXES_FAILED.append(f"{fix_id}: File not found: {filepath}")
        return False

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    if old not in content:
        FIXES_FAILED.append(f"{fix_id}: Search string not found in {filepath}")
        return False

    count = content.count(old)
    if count > 1:
        print(f"  ⚠️  {fix_id}: Found {count} matches in {filepath} — replacing all")

    content = content.replace(old, new, 1)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    FIXES_APPLIED.append(f"{fix_id}: {description}")
    print(f"  ✅ {fix_id}: {description}")
    return True


def append_after(filepath, anchor, new_text, fix_id, description):
    """Insert new_text after anchor string in file."""
    full_path = os.path.join(BASE, filepath)
    if not os.path.exists(full_path):
        FIXES_FAILED.append(f"{fix_id}: File not found: {filepath}")
        return False

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    if anchor not in content:
        FIXES_FAILED.append(f"{fix_id}: Anchor not found in {filepath}")
        return False

    if new_text.strip().splitlines()[0].strip() in content:
        print(f"  ⏭️  {fix_id}: Already applied — skipping")
        FIXES_APPLIED.append(f"{fix_id}: {description} (already present)")
        return True

    content = content.replace(anchor, anchor + new_text, 1)

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    FIXES_APPLIED.append(f"{fix_id}: {description}")
    print(f"  ✅ {fix_id}: {description}")
    return True


def syntax_check(filepath):
    """Verify Python file has valid syntax."""
    full_path = os.path.join(BASE, filepath)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"  ❌ SYNTAX ERROR in {filepath}: {e}")
        return False


def main():
    print("=" * 60)
    print("I-SERIE PDF QUALITY FIXES — Applying 10 Fixes")
    print("=" * 60)

    if not os.path.isdir(BASE):
        print(f"❌ Directory not found: {BASE}")
        sys.exit(1)

    # ==================================================================
    # FIX I2: hauptleistung truncation — gpt_analyze.py
    # ==================================================================
    print("\n📌 FIX I2: hauptleistung truncation limit 120→250")
    apply_fix(
        "gpt_analyze.py",
        "    # Truncate hauptleistung - use smart truncation at word boundary\n"
        "    hl_truncated = _smart_truncate(hauptleistung, 120, '...') if hauptleistung else \"\"",
        "    # FIX-I2: Increased limit from 120 to 250 to prevent visible truncation\n"
        "    hl_truncated = _smart_truncate(hauptleistung, 250, '...') if hauptleistung else \"\"",
        "I2a", "gpt_analyze.py — truncation limit 120→250"
    )

    # ==================================================================
    # FIX I2+I3+I6: CSS fixes in pdf_template.html
    # ==================================================================
    print("\n📌 FIX I2/I3/I6: CSS fixes in pdf_template.html")

    # I2: Add text-overflow fix to td cells
    apply_fix(
        "templates/pdf_template.html",
        "            border-right: none;\n"
        "            word-wrap: break-word;\n"
        "            overflow-wrap: break-word;\n"
        "        }\n"
        "        /* Zebra Stripes",
        "            border-right: none;\n"
        "            word-wrap: break-word;\n"
        "            overflow-wrap: break-word;\n"
        "            /* FIX-I2: Prevent text truncation in ALL table cells */\n"
        "            text-overflow: unset !important;\n"
        "            white-space: normal !important;\n"
        "            max-width: none;\n"
        "        }\n"
        "\n"
        "        /* FIX-I3: Prevent page breaks inside content sections */\n"
        "        .section-body {\n"
        "            page-break-inside: avoid;\n"
        "        }\n"
        "        .quick-win, .quick-win-card, .quick-win-card-new {\n"
        "            page-break-inside: avoid;\n"
        "        }\n"
        "        .vendor-card, .funding-card, .foerder-card {\n"
        "            page-break-inside: avoid;\n"
        "        }\n"
        "        .benchmark-swot > div > div {\n"
        "            page-break-inside: avoid;\n"
        "        }\n"
        "        /* Zebra Stripes",
        "I2b+I3", "pdf_template.html — td text-overflow + page-break-inside"
    )

    # I2: hero-title__subtitle overflow fix
    apply_fix(
        "templates/pdf_template.html",
        "            font-style: italic;\n"
        "            color: var(--color-primary);\n"
        "            margin-bottom: 4px;\n"
        "        }\n"
        "\n"
        "        .hero-title__meta {",
        "            font-style: italic;\n"
        "            color: var(--color-primary);\n"
        "            margin-bottom: 4px;\n"
        "            /* FIX-I2: Prevent hauptleistung text truncation */\n"
        "            overflow-wrap: break-word;\n"
        "            word-wrap: break-word;\n"
        "            white-space: normal;\n"
        "            text-overflow: unset;\n"
        "        }\n"
        "\n"
        "        .hero-title__meta {",
        "I2c", "pdf_template.html — hero-title__subtitle overflow"
    )

    # I6: funding-matrix-v2 table
    apply_fix(
        "templates/pdf_template.html",
        "            width: 100%;\n"
        "            border-collapse: collapse;\n"
        "            font-size: 10pt;\n"
        "        }\n"
        "        .funding-matrix-v2 th {",
        "            width: 100%;\n"
        "            border-collapse: collapse;\n"
        "            font-size: 10pt;\n"
        "            /* FIX-I6: Fixed table layout for WeasyPrint */\n"
        "            table-layout: fixed;\n"
        "        }\n"
        "        .funding-matrix-v2 th {",
        "I6a", "pdf_template.html — funding table-layout: fixed"
    )

    # I6: funding th word-break
    apply_fix(
        "templates/pdf_template.html",
        "            font-weight: 600;\n"
        "            color: #475569;\n"
        "            border-bottom: 1px solid #e2e8f0;\n"
        "        }\n"
        "        .funding-matrix-v2 td {",
        "            font-weight: 600;\n"
        "            color: #475569;\n"
        "            border-bottom: 1px solid #e2e8f0;\n"
        "            /* FIX-I6: Word-break for narrow columns */\n"
        "            word-break: break-word;\n"
        "            overflow-wrap: break-word;\n"
        "        }\n"
        "        .funding-matrix-v2 td {",
        "I6b", "pdf_template.html — funding th word-break"
    )

    # I6: funding td word-break
    apply_fix(
        "templates/pdf_template.html",
        "            padding: 10pt 8pt;\n"
        "            border-bottom: 1px solid #f1f5f9;\n"
        "            vertical-align: top;\n"
        "        }\n"
        "        .funding-matrix-v2 tr:hover {",
        "            padding: 10pt 8pt;\n"
        "            border-bottom: 1px solid #f1f5f9;\n"
        "            vertical-align: top;\n"
        "            /* FIX-I6: Prevent text overflow in fixed-layout cells */\n"
        "            word-break: break-word;\n"
        "            overflow-wrap: break-word;\n"
        "            white-space: normal;\n"
        "        }\n"
        "        .funding-matrix-v2 tr:hover {",
        "I6c", "pdf_template.html — funding td word-break"
    )

    # ==================================================================
    # FIX I5: Vendor audit — flex→table in vendor_audit_engine.py
    # ==================================================================
    print("\n📌 FIX I5: Vendor audit layout flex→table")

    # Summary grid: grid→table
    apply_fix(
        "services/vendor_audit_engine.py",
        '            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">\n'
        '                <div style="padding:12px;background:{category_bg["green"]};border-radius:8px;border:1px solid {category_border["green"]};text-align:center;">',
        '            <div style="margin-bottom:12px;">\n'
        '                <table style="width:100%;border-collapse:separate;border-spacing:8px;table-layout:fixed;">\n'
        '                <tr>\n'
        '                <td style="padding:12px;background:{category_bg["green"]};border-radius:8px;border:1px solid {category_border["green"]};text-align:center;width:33%;">',
        "I5a", "vendor_audit — summary grid→table (green)"
    )

    apply_fix(
        "services/vendor_audit_engine.py",
        '                </div>\n'
        '                <div style="padding:12px;background:{category_bg["yellow"]};border-radius:8px;border:1px solid {category_border["yellow"]};text-align:center;">',
        '                </td>\n'
        '                <td style="padding:12px;background:{category_bg["yellow"]};border-radius:8px;border:1px solid {category_border["yellow"]};text-align:center;width:33%;">',
        "I5b", "vendor_audit — summary yellow div→td"
    )

    apply_fix(
        "services/vendor_audit_engine.py",
        '                </div>\n'
        '                <div style="padding:12px;background:{category_bg["red"]};border-radius:8px;border:1px solid {category_border["red"]};text-align:center;">',
        '                </td>\n'
        '                <td style="padding:12px;background:{category_bg["red"]};border-radius:8px;border:1px solid {category_border["red"]};text-align:center;width:33%;">',
        "I5c", "vendor_audit — summary red div→td"
    )

    # Close the red cell + table
    apply_fix(
        "services/vendor_audit_engine.py",
        '                    <div style="font-size:24px;font-weight:700;color:{category_colors["red"]};">{report.red_count}</div>\n'
        '                </div>\n'
        '            </div>',
        '                    <div style="font-size:24px;font-weight:700;color:{category_colors["red"]};">{report.red_count}</div>\n'
        '                </td>\n'
        '                </tr>\n'
        '                </table>\n'
        '            </div>',
        "I5d", "vendor_audit — close red td + table"
    )

    # EU compliance: flex→table
    apply_fix(
        "services/vendor_audit_engine.py",
        '            <div style="display:flex;gap:12px;margin-top:12px;">\n'
        '                <div style="flex:1;padding:8px;background:#fff;border-radius:6px;border:1px solid #e2e8f0;">',
        '            <table style="width:100%;border-collapse:separate;border-spacing:8px;table-layout:fixed;margin-top:12px;">\n'
        '            <tr>\n'
        '                <td style="padding:8px;background:#fff;border-radius:6px;border:1px solid #e2e8f0;width:50%;">',
        "I5e", "vendor_audit — EU compliance flex→table (left)"
    )

    apply_fix(
        "services/vendor_audit_engine.py",
        '                    <div style="font-size:14px;font-weight:600;color:#1e293b;">{report.eu_compliant_count} / {report.total_vendors}</div>\n'
        '                </div>\n'
        '                <div style="flex:1;padding:8px;background:#fff;border-radius:6px;border:1px solid #e2e8f0;">',
        '                    <div style="font-size:14px;font-weight:600;color:#1e293b;">{report.eu_compliant_count} / {report.total_vendors}</div>\n'
        '                </td>\n'
        '                <td style="padding:8px;background:#fff;border-radius:6px;border:1px solid #e2e8f0;width:50%;">',
        "I5f", "vendor_audit — EU compliance right cell"
    )

    apply_fix(
        "services/vendor_audit_engine.py",
        '                    <div style="font-size:14px;font-weight:600;color:#1e293b;">{report.compliance_score:.0f}%</div>\n'
        '                </div>\n'
        '            </div>',
        '                    <div style="font-size:14px;font-weight:600;color:#1e293b;">{report.compliance_score:.0f}%</div>\n'
        '                </td>\n'
        '            </tr>\n'
        '            </table>',
        "I5g", "vendor_audit — close compliance table"
    )

    # Vendor cards: flex→inline-block/float
    apply_fix(
        "services/vendor_audit_engine.py",
        '                <div class="vendor-card" style="padding:16px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;border-left:4px solid {cat_color};margin-bottom:12px;">\n'
        '                    <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">\n'
        '                        <div>',
        '                <div class="vendor-card" style="padding:16px;background:#fff;border-radius:8px;border:1px solid #e2e8f0;border-left:4px solid {cat_color};margin-bottom:12px;page-break-inside:avoid;">\n'
        '                    <div style="margin-bottom:8px;">\n'
        '                        <div style="display:inline-block;vertical-align:top;">',
        "I5h", "vendor_audit — card header flex→inline-block"
    )

    apply_fix(
        "services/vendor_audit_engine.py",
        '                        <div style="display:flex;gap:6px;align-items:center;">',
        '                        <div style="float:right;">',
        "I5i", "vendor_audit — card badges flex→float"
    )

    # Add clear:both after badges
    apply_fix(
        "services/vendor_audit_engine.py",
        '                            <span style="font-size:9px;padding:2px 8px;background:{cat_bg};color:{cat_color};border-radius:4px;border:1px solid {cat_border};font-weight:600;">{entry.overall_category.upper()}</span>\n'
        '                        </div>\n'
        '                    </div>',
        '                            <span style="font-size:9px;padding:2px 8px;background:{cat_bg};color:{cat_color};border-radius:4px;border:1px solid {cat_border};font-weight:600;">{entry.overall_category.upper()}</span>\n'
        '                        </div>\n'
        '                        <div style="clear:both;"></div>\n'
        '                    </div>',
        "I5j", "vendor_audit — add clear:both"
    )

    # Badge container: flex-wrap→inline-block margin
    apply_fix(
        "services/vendor_audit_engine.py",
        '                    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;">\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;">\U0001f4cd {entry.data_location}</span>\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:{"#dcfce7" if entry.has_dpa else "#fef2f2"};color:{"#166534" if entry.has_dpa else "#991b1b"};border-radius:3px;border:1px solid {"#86efac" if entry.has_dpa else "#fca5a5"};">\U0001f4c4 {labels["dpa_yes"] if entry.has_dpa else labels["dpa_no"]}</span>\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;">\U0001f512 {entry.security_posture.title()}</span>\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;">⚖️ {labels["ai_act"]}: {entry.ai_act_relevance}</span>',
        '                    <div style="margin-bottom:8px;word-break:break-word;overflow-wrap:break-word;">\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;display:inline-block;margin:2px;">\U0001f4cd {entry.data_location}</span>\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:{"#dcfce7" if entry.has_dpa else "#fef2f2"};color:{"#166534" if entry.has_dpa else "#991b1b"};border-radius:3px;border:1px solid {"#86efac" if entry.has_dpa else "#fca5a5"};display:inline-block;margin:2px;">\U0001f4c4 {labels["dpa_yes"] if entry.has_dpa else labels["dpa_no"]}</span>\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;display:inline-block;margin:2px;">\U0001f512 {entry.security_posture.title()}</span>\n'
        '                        <span style="font-size:8px;padding:2px 6px;background:#f8fafc;color:#64748b;border-radius:3px;border:1px solid #e2e8f0;display:inline-block;margin:2px;">⚖️ {labels["ai_act"]}: {entry.ai_act_relevance}</span>',
        "I5k", "vendor_audit — badge container flex→inline-block"
    )

    # ==================================================================
    # FIX I8: Monte Carlo cap — business_case_simulation.py
    # ==================================================================
    print("\n📌 FIX I8: Monte Carlo ROI cap 200→500 for simulation")
    apply_fix(
        "services/business_case_simulation.py",
        "        # Calculate ROI\n"
        "        roi = calculate_roi(annual_savings, effective_investment)\n"
        "        roi = max(MIN_ROI, min(MAX_ROI, roi))",
        "        # Calculate ROI\n"
        "        roi = calculate_roi(annual_savings, effective_investment)\n"
        "        # FIX-I8: Use higher cap (500%) for simulation to preserve percentile variance.\n"
        "        # The planning cap (200%) is only for displayed planning values, not for\n"
        "        # statistical analysis where variance must be visible.\n"
        "        SIMULATION_ROI_CAP = 500.0\n"
        "        roi = max(MIN_ROI, min(SIMULATION_ROI_CAP, roi))",
        "I8", "business_case_simulation.py — ROI cap 200→500"
    )

    # ==================================================================
    # FIX I9: SWOT grid→table — benchmark_engine.py
    # ==================================================================
    print("\n📌 FIX I9: SWOT CSS Grid→Table")
    apply_fix(
        "services/benchmark_engine.py",
        '    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">\n'
        '        <div style="padding: 16px; background: rgba(34, 197, 94, 0.08); border-radius: 8px; border-left: 4px solid #22c55e;">\n'
        '            <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #22c55e;">{labels["strengths"]}</h4>\n'
        '            <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                {render_items(report.strengths, "#22c55e", "rgba(34, 197, 94, 0.2)")}\n'
        '            </ul>\n'
        '        </div>\n'
        '        <div style="padding: 16px; background: rgba(239, 68, 68, 0.08); border-radius: 8px; border-left: 4px solid #ef4444;">\n'
        '            <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #ef4444;">{labels["weaknesses"]}</h4>\n'
        '            <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                {render_items(report.weaknesses, "#ef4444", "rgba(239, 68, 68, 0.2)")}\n'
        '            </ul>\n'
        '        </div>\n'
        '        <div style="padding: 16px; background: rgba(59, 130, 246, 0.08); border-radius: 8px; border-left: 4px solid #3b82f6;">\n'
        '            <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #3b82f6;">{labels["opportunities"]}</h4>\n'
        '            <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                {render_items(report.opportunities, "#3b82f6", "rgba(59, 130, 246, 0.2)")}\n'
        '            </ul>\n'
        '        </div>\n'
        '        <div style="padding: 16px; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border-left: 4px solid #f59e0b;">\n'
        '            <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #f59e0b;">{labels["threats"]}</h4>\n'
        '            <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                {render_items(report.threats, "#f59e0b", "rgba(245, 158, 11, 0.2)")}\n'
        '            </ul>\n'
        '        </div>\n'
        '    </div>',
        '    <table style="width: 100%; border-collapse: separate; border-spacing: 12px; table-layout: fixed;">\n'
        '        <tr>\n'
        '            <td style="padding: 16px; background: rgba(34, 197, 94, 0.08); border-radius: 8px; border-left: 4px solid #22c55e; vertical-align: top; width: 50%;">\n'
        '                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #22c55e;">{labels["strengths"]}</h4>\n'
        '                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                    {render_items(report.strengths, "#22c55e", "rgba(34, 197, 94, 0.2)")}\n'
        '                </ul>\n'
        '            </td>\n'
        '            <td style="padding: 16px; background: rgba(239, 68, 68, 0.08); border-radius: 8px; border-left: 4px solid #ef4444; vertical-align: top; width: 50%;">\n'
        '                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #ef4444;">{labels["weaknesses"]}</h4>\n'
        '                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                    {render_items(report.weaknesses, "#ef4444", "rgba(239, 68, 68, 0.2)")}\n'
        '                </ul>\n'
        '            </td>\n'
        '        </tr>\n'
        '        <tr>\n'
        '            <td style="padding: 16px; background: rgba(59, 130, 246, 0.08); border-radius: 8px; border-left: 4px solid #3b82f6; vertical-align: top; width: 50%;">\n'
        '                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #3b82f6;">{labels["opportunities"]}</h4>\n'
        '                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                    {render_items(report.opportunities, "#3b82f6", "rgba(59, 130, 246, 0.2)")}\n'
        '                </ul>\n'
        '            </td>\n'
        '            <td style="padding: 16px; background: rgba(245, 158, 11, 0.08); border-radius: 8px; border-left: 4px solid #f59e0b; vertical-align: top; width: 50%;">\n'
        '                <h4 style="margin: 0 0 12px 0; font-size: 12pt; font-weight: 600; color: #f59e0b;">{labels["threats"]}</h4>\n'
        '                <ul style="margin: 0; padding: 0 0 0 16px; font-size: 10pt; color: var(--color-text-normal, #1e293b);">\n'
        '                    {render_items(report.threats, "#f59e0b", "rgba(245, 158, 11, 0.2)")}\n'
        '                </ul>\n'
        '            </td>\n'
        '        </tr>\n'
        '    </table>',
        "I9", "benchmark_engine.py — SWOT grid→table"
    )

    # ==================================================================
    # FIX I1/I4/I7: New functions in pipeline_sanitizers.py
    # ==================================================================
    print("\n📌 FIX I1/I4/I7: pipeline_sanitizers.py — new functions + integration")

    # Add integration into sanitize_all_sections
    apply_fix(
        "services/pipeline_sanitizers.py",
        "        cleaned, c1_rem = strip_context_block_leaks(result.content, key)\n"
        "        if c1_rem > 0:\n"
        "            stats['context_blocks_stripped'] = stats.get('context_blocks_stripped', 0) + c1_rem\n"
        "        sanitized[key] = cleaned",
        "        cleaned, c1_rem = strip_context_block_leaks(result.content, key)\n"
        "        if c1_rem > 0:\n"
        "            stats['context_blocks_stripped'] = stats.get('context_blocks_stripped', 0) + c1_rem\n"
        "\n"
        "        # FIX-I1/I7: Strip variable name leaks and grammar fixes\n"
        "        cleaned, i1_rem = strip_variable_name_leaks(cleaned, key)\n"
        "        if i1_rem > 0:\n"
        "            stats['variable_leaks_stripped'] = stats.get('variable_leaks_stripped', 0) + i1_rem\n"
        "\n"
        "        # FIX-I4: Strip redundant content blocks\n"
        "        cleaned, i4_rem = strip_redundant_blocks(cleaned, key)\n"
        "        if i4_rem > 0:\n"
        "            stats['redundant_blocks_stripped'] = stats.get('redundant_blocks_stripped', 0) + i4_rem\n"
        "\n"
        "        sanitized[key] = cleaned",
        "I1/I4/I7a", "pipeline_sanitizers.py — integration into sanitize_all_sections"
    )

    # Add new functions before the FIX-C1 section
    NEW_FUNCTIONS = '''
# =============================================================================
# FIX-I1: STRIP VARIABLE NAME LEAKS FROM LLM OUTPUT
# =============================================================================
# LLM sometimes echoes variable names like "quick_wins" as <h4> headings.

_VARIABLE_NAME_LEAK_PATTERNS = [
    # <h4>quick_wins</h4> or <h4> quick_wins </h4>
    re.compile(r'<h4[^>]*>\\s*quick_wins\\s*</h4>', re.IGNORECASE),
    # <h3>quick_wins</h3>
    re.compile(r'<h3[^>]*>\\s*quick_wins\\s*</h3>', re.IGNORECASE),
    # <p>quick_wins</p> (standalone paragraph)
    re.compile(r'<p[^>]*>\\s*quick_wins\\s*</p>', re.IGNORECASE),
    # <strong>quick_wins</strong> (standalone)
    re.compile(r'<strong>\\s*quick_wins\\s*</strong>', re.IGNORECASE),
    # Other common variable name leaks
    re.compile(r'<h4[^>]*>\\s*(?:risks_html|RISKS_HTML|executive_summary|roadmap_12m)\\s*</h4>', re.IGNORECASE),
    re.compile(r'<h3[^>]*>\\s*(?:risks_html|RISKS_HTML|executive_summary|roadmap_12m)\\s*</h3>', re.IGNORECASE),
]

# FIX-I7: Grammar fix — LLM generates "Kleines Kapazität" instead of correct forms
_GRAMMAR_FIX_PATTERNS = [
    (re.compile(r'Kleines\\s+Kapazit[äa]t', re.IGNORECASE), 'Kleines Team'),
    (re.compile(r'Kleine\\s+Kapazit[äa]t', re.IGNORECASE), 'Kleine Kapazität'),
]


def strip_variable_name_leaks(html_content: str, section_name: str = "") -> tuple:
    """FIX-I1: Remove variable name leaks from LLM output.

    LLM sometimes generates the variable name (e.g., 'quick_wins') as a visible
    heading in the HTML output. This strips those leaks.

    Returns:
        Tuple of (cleaned_html, removal_count)
    """
    if not html_content or len(html_content) < 50:
        return html_content, 0

    result = html_content
    removals = 0

    for pattern in _VARIABLE_NAME_LEAK_PATTERNS:
        matches = pattern.findall(result)
        if matches:
            removals += len(matches)
            result = pattern.sub('', result)

    # FIX-I7: Apply grammar fixes
    for pattern, replacement in _GRAMMAR_FIX_PATTERNS:
        matches = pattern.findall(result)
        if matches:
            removals += len(matches)
            result = pattern.sub(replacement, result)

    # Clean up resulting empty lines
    if removals > 0:
        result = re.sub(r'\\n\\s*\\n\\s*\\n', '\\n\\n', result)
        log.info("[FIX-I1] Stripped %d variable name leaks from section=%s", removals, section_name)

    return result, removals


# =============================================================================
# FIX-I4: STRIP REDUNDANT CONTENT BLOCKS
# =============================================================================
# When strategic_context_block is echoed by LLM in multiple sections,
# detect and remove duplicate blocks.

def strip_redundant_blocks(html: str, section_name: str = "") -> tuple:
    """FIX-I4: Detect and remove duplicate content blocks in HTML.

    Identifies blocks of text (bullet lists, paragraphs) that appear 2+ times
    and removes all but the first occurrence.

    Returns:
        Tuple of (cleaned_html, removal_count)
    """
    if not html or len(html) < 500:
        return html, 0

    # Find repeated <ul>...</ul> blocks (common for context block echo)
    ul_pattern = re.compile(r'(<ul[^>]*>.*?</ul>)', re.DOTALL | re.IGNORECASE)
    ul_blocks = ul_pattern.findall(html)

    if not ul_blocks:
        return html, 0

    # Count occurrences of each block (normalized)
    from collections import Counter
    normalized_blocks = [re.sub(r'\\s+', ' ', b.strip()) for b in ul_blocks]
    block_counts = Counter(normalized_blocks)

    result = html
    removals = 0

    for block_norm, count in block_counts.items():
        if count <= 1:
            continue
        if len(block_norm) < 100:  # Skip tiny blocks
            continue

        # Find the original (non-normalized) block
        for original_block in ul_blocks:
            if re.sub(r'\\s+', ' ', original_block.strip()) == block_norm:
                # Remove all but first occurrence
                first_pos = result.find(original_block)
                if first_pos >= 0:
                    after_first = first_pos + len(original_block)
                    rest = result[after_first:]
                    removed_in_rest = rest.count(original_block)
                    if removed_in_rest > 0:
                        rest = rest.replace(original_block, '', removed_in_rest)
                        result = result[:after_first] + rest
                        removals += removed_in_rest
                break

    if removals > 0:
        log.info("[FIX-I4] Stripped %d redundant blocks from section=%s", removals, section_name)

    return result, removals


'''

    append_after(
        "services/pipeline_sanitizers.py",
        "# =============================================================================\n"
        "# FIX-C1: STRIP CONTEXT BLOCK LABELS FROM LLM OUTPUT\n"
        "# =============================================================================",
        "",  # dummy — we use a different approach
        "I1/I4/I7b", "pipeline_sanitizers.py — new functions"
    )

    # Actually insert the functions before FIX-C1
    full_path = os.path.join(BASE, "services/pipeline_sanitizers.py")
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    c1_marker = "# =============================================================================\n# FIX-C1: STRIP CONTEXT BLOCK LABELS FROM LLM OUTPUT\n# ============================================================================="

    if "strip_variable_name_leaks" not in content:
        if c1_marker in content:
            content = content.replace(c1_marker, NEW_FUNCTIONS + c1_marker)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("  ✅ I1/I4/I7b: pipeline_sanitizers.py — new functions added")
            FIXES_APPLIED.append("I1/I4/I7b: New functions strip_variable_name_leaks + strip_redundant_blocks")
        else:
            FIXES_FAILED.append("I1/I4/I7b: FIX-C1 marker not found in pipeline_sanitizers.py")
    else:
        print("  ⏭️  I1/I4/I7b: Functions already exist — skipping")

    # ==================================================================
    # FIX I10: UTF-8 repair in report_renderer.py
    # ==================================================================
    print("\n📌 FIX I10: Final UTF-8 double-encoding repair in report_renderer.py")
    apply_fix(
        "services/report_renderer.py",
        '    meta["report_id"] = ctx.get("report_id", "")\n'
        '    meta["report_date"] = ctx.get("report_date", "")\n'
        '\n'
        '    # =========================================================================\n'
        '    # FIX-514: Quick-Wins Non-Empty Gate',
        '    meta["report_id"] = ctx.get("report_id", "")\n'
        '    meta["report_date"] = ctx.get("report_date", "")\n'
        '\n'
        '    # =========================================================================\n'
        '    # FIX-I10: Final UTF-8 double-encoding repair on complete HTML\n'
        '    # Section pills and other template-level text can have mojibake (â€¢ → •)\n'
        '    # that wasn\'t caught by section-level sanitizers.\n'
        '    # =========================================================================\n'
        '    html_before_utf8 = html\n'
        '    html = fix_double_encoded_utf8(html)\n'
        '    if html != html_before_utf8:\n'
        '        log.info("[FIX-I10] Repaired UTF-8 double-encoding in final HTML for run=%s", run_id)\n'
        '\n'
        '    # =========================================================================\n'
        '    # FIX-514: Quick-Wins Non-Empty Gate',
        "I10", "report_renderer.py — final UTF-8 repair"
    )

    # ==================================================================
    # SYNTAX CHECKS
    # ==================================================================
    print("\n" + "=" * 60)
    print("SYNTAX CHECKS")
    print("=" * 60)

    py_files = [
        "gpt_analyze.py",
        "services/pipeline_sanitizers.py",
        "services/report_renderer.py",
        "services/vendor_audit_engine.py",
        "services/benchmark_engine.py",
        "services/business_case_simulation.py",
    ]

    all_ok = True
    for f in py_files:
        if syntax_check(f):
            print(f"  ✅ {f}")
        else:
            all_ok = False

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\n✅ Applied: {len(FIXES_APPLIED)}")
    for fix in FIXES_APPLIED:
        print(f"   • {fix}")

    if FIXES_FAILED:
        print(f"\n❌ Failed: {len(FIXES_FAILED)}")
        for fix in FIXES_FAILED:
            print(f"   • {fix}")

    if all_ok and not FIXES_FAILED:
        print("\n🎉 ALL FIXES APPLIED SUCCESSFULLY!")
        print("\nNext steps:")
        print("  git add -A")
        print('  git commit -m "FIX-I-SERIE: PDF quality I1-I10"')
        print("  git push origin main")
    elif FIXES_FAILED:
        print("\n⚠️  Some fixes failed — check output above")

    return 0 if (all_ok and not FIXES_FAILED) else 1


if __name__ == "__main__":
    sys.exit(main())

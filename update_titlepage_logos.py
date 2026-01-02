#!/usr/bin/env python3
"""Update titlepage: Better logo integration + TÜV as credential badge"""

import re

with open('templates/pdf_template.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the new PAGE 1 section we just created
page1_start = content.find('<!-- PAGE 1: EXECUTIVE ORIENTATION (MINIMAL)')
page2_start = content.find('<!-- PAGE 2: EXECUTIVE DECISION')

if page1_start == -1 or page2_start == -1:
    print("❌ Could not find PAGE 1")
    exit(1)

before_page1 = content[:page1_start]
after_page2 = content[page2_start:]

# NEW PAGE 1 with better logo integration
new_page1 = '''                <!-- PAGE 1: EXECUTIVE ORIENTATION (MINIMAL)        -->
                <!-- ============================================== -->
                <div class="exec-orientation" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; min-height: 100vh; padding: var(--space-xl) 0;">
                    
                    <!-- HERO SECTION: Fully centered, integrated -->
                    <div style="max-width: 800px; width: 100%;">
                        
                        <!-- Eyebrow + Report ID: Small, integrated -->
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-md);">
                            KI-Status-Report · {{ report_date }}
                            <span class="muted" style="margin: 0 8px;">·</span>
                            Report-ID: {{ report_id }}
                        </div>

                        <!-- Title & Company -->
                        <div style="margin-bottom: var(--space-xl);">
                            <h1 style="font-size: 32px; font-weight: 600; margin: 0 0 var(--space-sm) 0; color: var(--color-text-normal);">
                                KI-Readiness Report
                            </h1>
                            <p style="font-size: 16px; color: var(--color-text-muted); margin: 0;">
                                {{ ui("company_label_colon") }} <strong style="color: var(--color-text-normal);">{{ company_name or kundencode or ui("your_company") }}</strong>
                                <span class="muted"> · </span>
                                <span>{{ BRANCHE_LABEL }}</span>
                                <span class="muted"> · </span>
                                <span>{{ UNTERNEHMENSGROESSE_LABEL }}</span>
                            </p>
                        </div>

                        <!-- HERO SCORE: Very large, centered -->
                        <div style="margin-bottom: var(--space-xl);">
                            <div style="font-size: 72px; font-weight: 700; line-height: 1; color: var(--color-primary); margin-bottom: var(--space-xs);">
                                {{ score_gesamt }}
                                <span style="font-size: 36px; font-weight: 400; color: var(--color-text-muted);">/100</span>
                            </div>
                            <div style="font-size: 18px; font-weight: 500; color: var(--color-text-normal); margin-bottom: var(--space-xs);">
                                {{ score_rating }}
                            </div>
                            <div style="font-size: 14px; color: var(--color-text-muted);">
                                Reifegrad: {{ size_label }}
                                {% if top10_score_for_size and (top10_score_for_size|int > score_gesamt|int) %}
                                <span class="muted"> · </span>
                                <span>Potenzial: +{{ (top10_score_for_size|int) - (score_gesamt|int) }} Punkte</span>
                                {% endif %}
                            </div>
                        </div>

                        <!-- MAIN LOGO: Large, centered under score -->
                        <div style="margin-bottom: var(--space-xl);">
                            <img src="ki-sicherheit-logo.webp" alt="KI-Sicherheit.jetzt" style="height: 48px; max-width: 300px;">
                        </div>

                        <!-- 4 DIMENSION SCORES: Horizontal cards -->
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-md); margin-bottom: var(--space-xl);">
                            <div style="background: var(--color-bg-subtle); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-md); text-align: center;">
                                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-xs);">
                                    Governance
                                </div>
                                <div style="font-size: 28px; font-weight: 600; color: var(--color-text-normal);">
                                    {{ score_governance or 0 }}
                                    <span style="font-size: 14px; font-weight: 400; color: var(--color-text-muted);">/100</span>
                                </div>
                            </div>
                            <div style="background: var(--color-bg-subtle); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-md); text-align: center;">
                                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-xs);">
                                    Sicherheit
                                </div>
                                <div style="font-size: 28px; font-weight: 600; color: var(--color-text-normal);">
                                    {{ score_sicherheit or 0 }}
                                    <span style="font-size: 14px; font-weight: 400; color: var(--color-text-muted);">/100</span>
                                </div>
                            </div>
                            <div style="background: var(--color-bg-subtle); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-md); text-align: center;">
                                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-xs);">
                                    Wertschöpfung
                                </div>
                                <div style="font-size: 28px; font-weight: 600; color: var(--color-text-normal);">
                                    {{ score_wertschoepfung or score_nutzen or 0 }}
                                    <span style="font-size: 14px; font-weight: 400; color: var(--color-text-muted);">/100</span>
                                </div>
                            </div>
                            <div style="background: var(--color-bg-subtle); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-md); text-align: center;">
                                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-xs);">
                                    Befähigung
                                </div>
                                <div style="font-size: 28px; font-weight: 600; color: var(--color-text-normal);">
                                    {{ score_befaehigung or 0 }}
                                    <span style="font-size: 14px; font-weight: 400; color: var(--color-text-muted);">/100</span>
                                </div>
                            </div>
                        </div>

                        <!-- 3 KPI ROW: Large, prominent -->
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-lg); margin-bottom: var(--space-xl);">
                            <div style="text-align: center;">
                                <div style="font-size: 36px; font-weight: 600; color: var(--color-text-normal); margin-bottom: var(--space-xs);">
                                    {{ monatsersparnis_stunden or qw_hours_total }} <span style="font-size: 20px; font-weight: 400;">Std.</span>
                                </div>
                                <div style="font-size: 13px; font-weight: 500; color: var(--color-text-normal); margin-bottom: 4px;">
                                    Zeitersparnis/Monat
                                </div>
                                <div style="font-size: 11px; color: var(--color-text-muted);">
                                    bei Umsetzung der Empfehlungen
                                </div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 36px; font-weight: 600; color: var(--color-text-normal); margin-bottom: var(--space-xs);">
                                    {{ (ROI_12M or 0) | round(0) | int }}<span style="font-size: 20px; font-weight: 400;">%</span>
                                </div>
                                <div style="font-size: 13px; font-weight: 500; color: var(--color-text-normal); margin-bottom: 4px;">
                                    ROI (12 Monate)
                                </div>
                                <div style="font-size: 11px; color: var(--color-text-muted);">
                                    Payback: {{ PAYBACK_MONTHS or 'n/a' }} Monate
                                </div>
                            </div>
                            <div style="text-align: center;">
                                <div style="font-size: 36px; font-weight: 600; color: var(--color-text-normal); margin-bottom: var(--space-xs);">
                                    {{ AI_ACT_RISK_LEVEL or 'minimal' }}
                                </div>
                                <div style="font-size: 13px; font-weight: 500; color: var(--color-text-normal); margin-bottom: 4px;">
                                    AI Act Risiko
                                </div>
                                <div style="font-size: 11px; color: var(--color-text-muted);">
                                    DSGVO-konforme Empfehlung
                                </div>
                            </div>
                        </div>

                        <!-- AUTHOR CREDENTIALS: TÜV Badge -->
                        <div style="display: flex; align-items: center; justify-content: center; gap: var(--space-sm); padding: var(--space-md); background: var(--color-bg-subtle); border-radius: 8px; margin-bottom: var(--space-lg);">
                            <img src="tuev-logo-transparent.webp" alt="TÜV Austria" style="height: 24px; opacity: 0.7;">
                            <span style="font-size: 12px; color: var(--color-text-muted);">
                                Erstellt von: <strong style="color: var(--color-text-normal);">TÜV-zertifizierter KI-Manager</strong>
                            </span>
                        </div>

                        <!-- TRUST BADGES: Small, at bottom -->
                        <div style="display: flex; align-items: center; justify-content: center; gap: var(--space-md); font-size: 11px; color: var(--color-text-muted);">
                            <span style="display: flex; align-items: center; gap: 6px;">
                                <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--color-primary);"></span>
                                EU AI Act konform
                            </span>
                            <span style="display: flex; align-items: center; gap: 6px;">
                                <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--color-primary);"></span>
                                DSGVO-orientiert
                            </span>
                            <span style="display: flex; align-items: center; gap: 6px;">
                                <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--color-primary);"></span>
                                Keine Rechtsberatung
                            </span>
                        </div>

                    </div>
                </div>
                <!-- END PAGE 1 -->

                '''

# Combine
new_content = before_page1 + new_page1 + after_page2

with open('templates/pdf_template.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Logo integration updated!")
print("\nChanges:")
print("  • Report-ID integrated into eyebrow (top)")
print("  • KI-Sicherheit.jetzt logo: 48px height, centered under score")
print("  • TÜV badge as credential: 'Erstellt von TÜV-zertifizierter KI-Manager'")
print("  • TÜV logo small (24px) in badge box")
print("  • Everything nicely integrated in hero block")


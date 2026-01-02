#!/usr/bin/env python3
"""Redesign Page 2: Prominent Top-3 + Visual Hierarchy"""

with open('templates/pdf_template.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find PAGE 2
page2_start = content.find('<!-- PAGE 2: EXECUTIVE DECISION')
page3_start = content.find('<!-- PAGE 3: EXECUTIVE TOC')

if page2_start == -1 or page3_start == -1:
    print("❌ Could not find PAGE 2 or PAGE 3")
    exit(1)

before_page2 = content[:page2_start]
after_page3 = content[page3_start:]

# NEW PAGE 2 with better visual hierarchy
new_page2 = '''                <!-- PAGE 2: EXECUTIVE DECISION                     -->
                <!-- ============================================== -->
                <div class="exec-decision-page" style="padding: var(--space-xl) var(--space-lg);">
                    
                    <!-- Header -->
                    <div style="margin-bottom: var(--space-xl);">
                        <h2 style="font-size: 28px; font-weight: 600; margin: 0 0 var(--space-sm) 0;">
                            {{ ui("exec_decision_title", "Entscheidung & Fokus") }}
                        </h2>
                    </div>

                    <!-- Quick Summary Box -->
                    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-left: 4px solid var(--color-primary); padding: var(--space-lg); border-radius: 8px; margin-bottom: var(--space-xl);">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-lg);">
                            <div>
                                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-xs);">
                                    Ihr KI-Reifegrad
                                </div>
                                <div style="font-size: 24px; font-weight: 600; color: var(--color-text-normal);">
                                    {{ score_gesamt }}/100 - {{ score_rating }}
                                </div>
                            </div>
                            <div>
                                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-xs);">
                                    Erwarteter ROI
                                </div>
                                <div style="font-size: 24px; font-weight: 600; color: var(--color-text-normal);">
                                    {{ (ROI_12M or 0) | round(0) | int }}% nach 12 Monaten
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- FINAL CHECK with prominent actions -->
                    {% if FINAL_CHECK_INTRO or FINAL_CHECK_DECISIONS %}
                    <div style="background: var(--color-primary); color: white; padding: var(--space-lg); border-radius: 12px; margin-bottom: var(--space-xl);">
                        <h3 style="font-size: 20px; font-weight: 600; margin: 0 0 var(--space-md) 0; display: flex; align-items: center; gap: var(--space-sm);">
                            <span style="font-size: 24px;">🚀</span>
                            Final-Check
                        </h3>
                        {% if FINAL_CHECK_INTRO %}
                        <p style="margin: 0 0 var(--space-md) 0; opacity: 0.95;">{{ FINAL_CHECK_INTRO }}</p>
                        {% endif %}
                        {% if FINAL_CHECK_DECISIONS %}
                        <div style="display: flex; flex-direction: column; gap: var(--space-sm);">
                            {% for decision in FINAL_CHECK_DECISIONS %}
                            <div style="display: flex; align-items: start; gap: var(--space-sm); background: rgba(255,255,255,0.1); padding: var(--space-sm) var(--space-md); border-radius: 6px;">
                                <span style="font-weight: 600;">•</span>
                                <span>{{ decision }}</span>
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                    {% endif %}

                    <!-- TOP-3 MUSS-MAßNAHMEN with color coding -->
                    <div style="margin-bottom: var(--space-xl);">
                        <h3 style="font-size: 20px; font-weight: 600; margin: 0 0 var(--space-md) 0; display: flex; align-items: center; gap: var(--space-sm);">
                            <span style="font-size: 24px;">⚠️</span>
                            {{ ui("top3_title", "Top-3 MUSS-Maßnahmen") }}
                        </h3>
                        <div style="font-size: 13px; color: var(--color-text-muted); margin-bottom: var(--space-md);">
                            Diese Risiken wurden als hoch/kritisch eingestuft und erfordern sofortige Aufmerksamkeit.
                        </div>
                        <div class="top3-measures-enhanced">
                            {{ TOP_3_MASSNAHMEN_HTML | safe }}
                        </div>
                    </div>

                    <!-- Executive Decision Blocks -->
                    {% if EXECUTIVE_DECISION_HTML and EXECUTIVE_DECISION_HTML|trim and '<' in EXECUTIVE_DECISION_HTML %}
                    <div style="background: var(--color-bg-subtle); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg); margin-bottom: var(--space-lg);">
                        <h3 style="font-size: 16px; font-weight: 600; margin: 0 0 var(--space-md) 0;">
                            Strategische Empfehlungen
                        </h3>
                        {{ EXECUTIVE_DECISION_HTML|safe }}
                    </div>
                    {% endif %}

                    <!-- Continue Note -->
                    <div style="text-align: center; padding: var(--space-lg); background: var(--color-bg-subtle); border-radius: 8px;">
                        <p style="margin: 0; font-size: 13px; color: var(--color-text-muted);">
                            {{ ui("exec_continue", "Details und Begründungen folgen ab Seite 4 – je nach Informationsbedarf.") }}
                        </p>
                    </div>

                </div>
                <!-- END PAGE 2 -->

                '''

# Combine
new_content = before_page2 + new_page2 + after_page3

with open('templates/pdf_template.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Page 2 redesigned!")
print("\nChanges:")
print("  • Quick summary box with gradient background")
print("  • Final-Check in prominent blue box with 🚀")
print("  • Top-3 MUSS-Maßnahmen with ⚠️ icon")
print("  • Color-coded priority system")
print("  • Better spacing and visual hierarchy")
print("  • Continue note in subtle box")


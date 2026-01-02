#!/usr/bin/env python3
"""Redesign Page 3: Modern TOC with icons and card layout"""

with open('templates/pdf_template.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find PAGE 3
page3_start = content.find('<!-- PAGE 3: EXECUTIVE TOC')
page4_start = content.find('<!-- PAGE 4+: FULL REPORT')

if page3_start == -1 or page4_start == -1:
    print("❌ Could not find PAGE 3 or PAGE 4")
    exit(1)

before_page3 = content[:page3_start]
after_page4 = content[page4_start:]

# NEW PAGE 3 with modern card layout and icons
new_page3 = '''                <!-- PAGE 3: EXECUTIVE TOC                          -->
                <!-- ============================================== -->
                <div class="exec-toc-page" style="padding: var(--space-xl) var(--space-lg);">
                    
                    <!-- Header -->
                    <div style="margin-bottom: var(--space-xl); text-align: center;">
                        <h2 style="font-size: 28px; font-weight: 600; margin: 0 0 var(--space-sm) 0;">
                            {{ ui("toc_title", "So lesen Sie diesen Report") }}
                        </h2>
                    </div>

                    <!-- 2-Column Layout: Current vs Future State -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-xl); margin-bottom: var(--space-xl);">
                        
                        <!-- LEFT: Current State (inefficient) -->
                        <div style="background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%); border-left: 4px solid #dc3545; padding: var(--space-lg); border-radius: 8px;">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">⚠️</span>
                                <h3 style="font-size: 16px; font-weight: 600; margin: 0; color: #dc3545;">
                                    Heute ineffizient
                                </h3>
                            </div>
                            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #6c757d; line-height: 1.6;">
                                <li>Entwicklung und Optimierung von Abläufen</li>
                                <li>Einzelschritte ohne Standard-Bausteine</li>
                                <li>Compliance-Prüfungen kosten Zeit</li>
                            </ul>
                        </div>

                        <!-- RIGHT: Future State (in 90 days) -->
                        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-left: 4px solid #0ea5e9; padding: var(--space-lg); border-radius: 8px;">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">✅</span>
                                <h3 style="font-size: 16px; font-weight: 600; margin: 0; color: #0ea5e9;">
                                    In 90 Tagen anders
                                </h3>
                            </div>
                            <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #6c757d; line-height: 1.6;">
                                <li>Standard-Analyse-Backbone statt Handwerk</li>
                                <li>Klare Prüfpunkte + Module</li>
                                <li>Messbare Zeitgewinne</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Report Structure Cards -->
                    <div style="display: grid; grid-template-columns: 1fr; gap: var(--space-md); margin-bottom: var(--space-xl);">
                        
                        <!-- GROUP 1: Decision Overview -->
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">📊</span>
                                <h3 style="font-size: 16px; font-weight: 600; margin: 0;">
                                    {{ ui("toc_group_decision", "Entscheidungsübersicht") }}
                                </h3>
                            </div>
                            <ul style="margin: 0; padding-left: 24px; font-size: 13px; line-height: 1.8; color: var(--color-text-muted);">
                                <li>{{ ui("toc_item_summary", "Executive Summary & Kurzurteil") }}</li>
                                <li>{{ ui("toc_item_top3", "Top-3 Maßnahmen & 90-Tage-Fokus") }}</li>
                            </ul>
                        </div>

                        <!-- GROUP 2: Economics & Risk -->
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">💰</span>
                                <h3 style="font-size: 16px; font-weight: 600; margin: 0;">
                                    {{ ui("toc_group_economics", "Wirtschaft & Risiko") }}
                                </h3>
                            </div>
                            <ul style="margin: 0; padding-left: 24px; font-size: 13px; line-height: 1.8; color: var(--color-text-muted);">
                                <li>{{ ui("toc_item_roi", "Wirtschaftlichkeit (ROI/Payback) & Annahmen") }}</li>
                                <li>{{ ui("toc_item_compliance", "Risiko- & Compliance-Einordnung (AI Act / DSGVO / Vendor)") }}</li>
                            </ul>
                        </div>

                        <!-- GROUP 3: Implementation & Depth -->
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">🛣️</span>
                                <h3 style="font-size: 16px; font-weight: 600; margin: 0;">
                                    {{ ui("toc_group_implementation", "Umsetzung & Tiefe") }}
                                </h3>
                            </div>
                            <ul style="margin: 0; padding-left: 24px; font-size: 13px; line-height: 1.8; color: var(--color-text-muted);">
                                <li>{{ ui("toc_item_roadmap", "Roadmap (90 Tage / 12 Monate)") }}</li>
                                <li>{{ ui("toc_item_industry", "Branchen- & Tool-Einordnung") }}</li>
                                <li>{{ ui("toc_item_funding", "Förderoptionen & nächste Schritte") }}</li>
                            </ul>
                        </div>
                    </div>

                    <!-- Bottom Note -->
                    <div style="text-align: center; padding: var(--space-md); background: var(--color-bg-subtle); border-radius: 8px;">
                        <p style="margin: 0; font-size: 12px; color: var(--color-text-muted);">
                            {{ ui("toc_note", "Ab Seite 4: Vertiefung und Detailanalysen") }}
                        </p>
                    </div>

                </div>
                <!-- END PAGE 3 -->

                '''

# Combine
new_content = before_page3 + new_page3 + after_page4

with open('templates/pdf_template.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Page 3 redesigned!")
print("\nChanges:")
print("  • 2-column layout: 'Heute ineffizient' ⚠️ vs 'In 90 Tagen anders' ✅")
print("  • 3 section cards with icons: 📊 💰 🛣️")
print("  • Color-coded boxes (red gradient vs blue gradient)")
print("  • Modern card-based layout instead of plain lists")
print("  • Better visual hierarchy and spacing")


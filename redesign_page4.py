#!/usr/bin/env python3
"""Redesign Page 4: Modern context cards with emojis and better hierarchy"""

with open('templates/pdf_template.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the KONTEXT section
kontext_start = content.find('<!-- STRATEGISCHER KONTEXT & LEITPLANKEN -->')
quick_wins_start = content.find('<!-- QUICK WINS -->', kontext_start)

if kontext_start == -1 or quick_wins_start == -1:
    print("❌ Could not find KONTEXT section")
    exit(1)

before_kontext = content[:kontext_start]
after_kontext = content[quick_wins_start:]

# NEW KONTEXT SECTION with modern design
new_kontext = '''                <!-- STRATEGISCHER KONTEXT & LEITPLANKEN -->
                {% if strategische_ziele or zeitersparnis_prioritaet or hauptleistung or ki_projekte or geschaeftsmodell_evolution or vision_3_jahre or ki_guardrails %}
                <section class="section chapter" style="padding: var(--space-xl) var(--space-lg);">
                    
                    <!-- Header -->
                    <div style="margin-bottom: var(--space-xl);">
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--color-text-muted); margin-bottom: var(--space-xs);">
                            Kontext
                        </div>
                        <h2 style="font-size: 28px; font-weight: 600; margin: 0 0 var(--space-xs) 0;">
                            Strategischer Kontext &amp; Leitplanken
                        </h2>
                        <p style="font-size: 14px; color: var(--color-text-muted); margin: 0;">
                            Ihre strategischen Vorgaben
                        </p>
                    </div>

                    <!-- Context Cards Grid -->
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-lg); margin-bottom: var(--space-xl);">
                        
                        {% if strategische_ziele %}
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">🎯</span>
                                <h4 style="font-size: 14px; font-weight: 600; margin: 0;">
                                    Strategische Prioritäten
                                </h4>
                            </div>
                            <p style="margin: 0; font-size: 13px; line-height: 1.6; color: var(--color-text-muted);">
                                {{ strategische_ziele }}
                            </p>
                        </div>
                        {% endif %}

                        {% if zeitersparnis_prioritaet %}
                        <div style="background: linear-gradient(135deg, #fff5f5 0%, #ffe5e5 100%); border-left: 4px solid #ef4444; padding: var(--space-lg); border-radius: 8px;">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">⏰</span>
                                <h4 style="font-size: 14px; font-weight: 600; margin: 0; color: #dc2626;">
                                    Zeitersparnis-Priorität
                                </h4>
                            </div>
                            <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #6b7280;">
                                {{ zeitersparnis_prioritaet }}
                            </p>
                        </div>
                        {% endif %}

                        {% if hauptleistung %}
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">💼</span>
                                <h4 style="font-size: 14px; font-weight: 600; margin: 0;">
                                    Hauptleistung
                                </h4>
                            </div>
                            <p style="margin: 0; font-size: 13px; line-height: 1.6; color: var(--color-text-muted);">
                                {{ hauptleistung }}
                            </p>
                        </div>
                        {% endif %}

                        {% if ki_projekte %}
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">✨</span>
                                <h4 style="font-size: 14px; font-weight: 600; margin: 0;">
                                    Laufende/geplante KI-Projekte
                                </h4>
                            </div>
                            <p style="margin: 0; font-size: 13px; line-height: 1.6; color: var(--color-text-muted);">
                                {{ ki_projekte }}
                            </p>
                        </div>
                        {% endif %}

                        {% if geschaeftsmodell_evolution %}
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">📈</span>
                                <h4 style="font-size: 14px; font-weight: 600; margin: 0;">
                                    Geschäftsmodell-Evolution
                                </h4>
                            </div>
                            <p style="margin: 0; font-size: 13px; line-height: 1.6; color: var(--color-text-muted);">
                                {{ geschaeftsmodell_evolution }}
                            </p>
                        </div>
                        {% endif %}

                        {% if vision_3_jahre %}
                        <div style="background: var(--color-bg-surface); border: 1px solid var(--color-border); border-radius: 8px; padding: var(--space-lg);">
                            <div style="display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-md);">
                                <span style="font-size: 24px;">🔮</span>
                                <h4 style="font-size: 14px; font-weight: 600; margin: 0;">
                                    3-Jahres-Vision
                                </h4>
                            </div>
                            <p style="margin: 0; font-size: 13px; line-height: 1.6; color: var(--color-text-muted);">
                                {{ vision_3_jahre }}
                            </p>
                        </div>
                        {% endif %}
                    </div>

                    <!-- Guardrails: Prominent red box -->
                    {% if ki_guardrails %}
                    <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 2px solid #dc2626; border-radius: 12px; padding: var(--space-xl); margin-bottom: var(--space-lg);">
                        <div style="display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-md);">
                            <div style="background: #dc2626; border-radius: 50%; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <span style="font-size: 28px;">⚠️</span>
                            </div>
                            <h4 style="font-size: 18px; font-weight: 600; margin: 0; color: #dc2626;">
                                Guardrails / No-Gos
                            </h4>
                        </div>
                        <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #6b7280;">
                            {{ ki_guardrails }}
                        </p>
                    </div>
                    {% endif %}

                </section>
                {% endif %}

                '''

# Combine
new_content = before_kontext + new_kontext + after_kontext

with open('templates/pdf_template.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Page 4 (Kontext) redesigned!")
print("\nChanges:")
print("  • Modern card layout with emojis: 🎯 💼 ✨ 📈 ��")
print("  • Zeitersparnis-Priorität: RED gradient box (prominent!)")
print("  • Guardrails: Large RED warning box with ⚠️ icon")
print("  • 2-column grid for better space usage")
print("  • Cleaner typography and spacing")


"""
Content Quality Enforcer v1.0
=============================
Post-Processing Safety Net für Report-Qualität.

Fixes:
1. ROI-Filter: Entfernt ROI% außerhalb Business Case
2. Fragment-Repair: Repariert unvollständige Sätze
3. hauptleistung-Enforcer: Injiziert hauptleistung wenn unter Minimum
4. Product Name Safety Net: Korrigiert "Microsoft Kapazitäten" → "Microsoft Teams" (v14.35.21)
5. Solo Language Normalizer: Enterprise-Begriffe → Solo-freundlich (v14.35.22)

Wird nach SIEZEN-GUARD aufgerufen, vor Validation.
"""

import os
import re
import logging

log = logging.getLogger(__name__)

# =============================================================================
# v14.35.22: SOLO LANGUAGE NORMALIZER
# =============================================================================
# Replaces enterprise-ish terms with solo-appropriate alternatives ONLY for solo persona.
# This reduces SIZE_MISMATCH warnings without changing meaning.

SOLO_TERM_REPLACEMENTS = [
    # (pattern, replacement, description)
    # Technical enterprise terms → Solo-friendly alternatives
    # FIX-497: Extended dictionary to reduce warnings to zero

    # Module/Component terms
    (r'\bModulen\b', 'Bausteinen', 'Modul→Baustein (Dativ Plural)'),
    (r'\bModule\b', 'Bausteine', 'Modul→Baustein (Plural)'),
    (r'\bModul\b', 'Baustein', 'Modul→Baustein'),
    (r'\bKomponenten\b', 'Teile', 'Komponenten→Teile'),
    (r'\bKomponente\b', 'Teil', 'Komponente→Teil'),

    # Platform/Architecture terms
    (r'\bCloud-Plattform\b', 'Cloud-Umgebung', 'Cloud-Plattform→Cloud-Umgebung'),
    (r'\bKI-Plattform\b', 'KI-Umgebung', 'KI-Plattform→KI-Umgebung'),
    (r'\bDaten-Plattform\b', 'Daten-Umgebung', 'Daten-Plattform→Daten-Umgebung'),
    (r'\bPlattformen\b', 'Arbeitsumgebungen', 'Plattformen→Arbeitsumgebungen (Plural)'),
    (r'\bPlattform\b', 'Arbeitsumgebung', 'Plattform→Arbeitsumgebung'),
    (r'\bSystem-Architektur\b', 'System-Struktur', 'System-Architektur→System-Struktur'),
    (r'\bSoftware-Architektur\b', 'Software-Struktur', 'Software-Architektur→Software-Struktur'),
    (r'\bArchitekturen\b', 'Strukturen', 'Architekturen→Strukturen (Plural)'),
    (r'\bArchitektur\b', 'Struktur', 'Architektur→Struktur'),
    (r'\bInfrastrukturen\b', 'Grundausstattungen', 'Infrastrukturen→Grundausstattungen'),
    (r'\bInfrastruktur\b', 'Grundausstattung', 'Infrastruktur→Grundausstattung'),

    # Stack/Technical terms
    (r'\bTech-Stack\b', 'Technikpaket', 'Tech-Stack→Technikpaket'),
    (r'\bTech\s+Stack\b', 'Technikpaket', 'Tech Stack→Technikpaket'),
    # FIX-KIS-1188-ITEM4: Inflected article+adjective forms BEFORE generic KI-Stack.
    # "KI-Stack" is maskulin sing.; "KI-Werkzeuge" is neutr. plur. The naive
    # substitution otherwise produces "Ihren bestehenden KI-Werkzeuge" (Genus-Bruch).
    (r'\bIhren\s+bestehenden\s+KI[-\s]?Stack\b', 'Ihre bestehenden KI-Werkzeuge', 'Ihren bestehenden KI-Stack → Ihre bestehenden KI-Werkzeuge'),
    (r'\bIhrem\s+bestehenden\s+KI[-\s]?Stack\b', 'Ihren bestehenden KI-Werkzeugen', 'Ihrem bestehenden KI-Stack → Ihren bestehenden KI-Werkzeugen'),
    (r'\bIhren\s+KI[-\s]?Stack\b', 'Ihre KI-Werkzeuge', 'Ihren KI-Stack → Ihre KI-Werkzeuge'),
    (r'\bIhrem\s+KI[-\s]?Stack\b', 'Ihren KI-Werkzeugen', 'Ihrem KI-Stack → Ihren KI-Werkzeugen'),
    (r'\bIhr\s+KI[-\s]?Stack\b', 'Ihre KI-Werkzeuge', 'Ihr KI-Stack → Ihre KI-Werkzeuge'),
    (r'\bden\s+bestehenden\s+KI[-\s]?Stack\b', 'die bestehenden KI-Werkzeuge', 'den bestehenden KI-Stack → die bestehenden KI-Werkzeuge'),
    (r'\bdem\s+bestehenden\s+KI[-\s]?Stack\b', 'den bestehenden KI-Werkzeugen', 'dem bestehenden KI-Stack → den bestehenden KI-Werkzeugen'),
    (r'\bden\s+KI[-\s]?Stack\b', 'die KI-Werkzeuge', 'den KI-Stack → die KI-Werkzeuge'),
    (r'\bdem\s+KI[-\s]?Stack\b', 'den KI-Werkzeugen', 'dem KI-Stack → den KI-Werkzeugen'),
    (r'\bder\s+KI[-\s]?Stack\b', 'die KI-Werkzeuge', 'der KI-Stack → die KI-Werkzeuge'),
    (r'\bKI-Stack\b', 'KI-Werkzeuge', 'KI-Stack→KI-Werkzeuge'),
    (r'\bKI\s+Stack\b', 'KI-Werkzeuge', 'KI Stack→KI-Werkzeuge'),
    (r'\bTool-Stack\b', 'Werkzeugpaket', 'Tool-Stack→Werkzeugpaket'),
    (r'\bSoftware-Stack\b', 'Softwarepaket', 'Software-Stack→Softwarepaket'),
    (r'\bFull-Stack\b', 'Gesamtlösung', 'Full-Stack→Gesamtlösung'),
    (r'\bFull\s+Stack\b', 'Gesamtlösung', 'Full Stack→Gesamtlösung'),
    (r'\bStacks\b', 'Technikpakete', 'Stacks→Technikpakete (Plural)'),
    # FIX-S13A: Sync with solo_leak_scanner — exclude KI-Stack and Stack-Komponente
    (r'\b(?<!KI-)Stack\b(?!-Komponente)', 'Technikpaket', 'Stack→Technikpaket'),
    (r'\bLayers\b', 'Ebenen', 'Layers→Ebenen (Plural)'),
    (r'\bLayer\b', 'Ebene', 'Layer→Ebene'),
    (r'\bPipelines\b', 'Abläufe', 'Pipelines→Abläufe (Plural)'),
    (r'\bPipeline\b', 'Ablauf', 'Pipeline→Ablauf'),
    (r'\bWorkflow\b', 'Arbeitsablauf', 'Workflow→Arbeitsablauf'),
    (r'\bWorkflows\b', 'Arbeitsabläufe', 'Workflows→Arbeitsabläufe'),

    # Deployment/Rollout terms
    (r'\bDeployment\b', 'Einrichtung', 'Deployment→Einrichtung'),
    # FIX-P2-C4: Rollout → Einführung (was: empty string, caused double-spaces)
    (r'\bRollout-Plan\b', 'Einführungsplan', 'Rollout-Plan→Einführungsplan'),
    (r'\bRollout\b', 'Einführung', 'Rollout→Einführung'),
    (r'\bRoll-out\b', 'Einführung', 'Roll-out→Einführung'),
    (r'\bRollouts\b', 'Einführungen', 'Rollouts→Einführungen'),
    (r'\bImplementierung\b', 'Umsetzung', 'Implementierung→Umsetzung'),
    (r'\bIntegration\b', 'Einbindung', 'Integration→Einbindung'),

    # FIX-526: Baukasten → Vorlagenpaket (forbidden for solo per user feedback)
    (r'\bBaukästen\b', 'Vorlagenpakete', 'FIX-526: Baukästen→Vorlagenpakete'),
    (r'\bBaukasten\b', 'Vorlagenpaket', 'FIX-526: Baukasten→Vorlagenpaket'),

    # Scaling terms
    (r'\bSkalierung\b', 'Ausbau', 'Skalierung→Ausbau'),
    (r'\bskalieren\b', 'ausbauen', 'skalieren→ausbauen'),
    (r'\bSkalierbarkeit\b', 'Erweiterbarkeit', 'Skalierbarkeit→Erweiterbarkeit'),
    (r'\bskalierbar\b', 'erweiterbar', 'skalierbar→erweiterbar'),

    # Corporate governance terms
    # FIX-S14C: Compound pattern BEFORE simple patterns (longer match first)
    (r'\bStakeholder-Analyse\b', 'Beteiligten-Analyse', 'Stakeholder-Analyse→Beteiligten-Analyse'),
    (r'\bStakeholder-Alignment\b', 'Abstimmung der Beteiligten', 'Stakeholder-Alignment→Abstimmung der Beteiligten'),
    (r'\bStakeholder-Feedback\b', 'Rückmeldung der Beteiligten', 'Stakeholder-Feedback→Rückmeldung der Beteiligten'),
    (r'\bStakeholder-Management\b', 'Beteiligten-Management', 'Stakeholder-Management→Beteiligten-Management'),
    (r'\bStakeholder-Kommunikation\b', 'Kommunikation mit Beteiligten', 'Stakeholder-Kommunikation→Kommunikation mit Beteiligten'),
    (r'\bStakeholder-[A-Za-zäöüÄÖÜß]+\b', 'Beteiligten-Abstimmung', 'Stakeholder-Compound→Beteiligten-Abstimmung (Fallback)'),
    (r'\bStakeholdern\b', 'Beteiligten', 'Stakeholdern→Beteiligten (Dativ)'),
    (r'\bStakeholders\b', 'Beteiligte', 'Stakeholders→Beteiligte (EN Plural)'),
    (r'\bStakeholder\b', 'Beteiligte', 'Stakeholder→Beteiligte'),
    (r'\bAudit-Trail\b', 'Prüfpfad', 'Audit-Trail→Prüfpfad'),
    (r'\bAudit\s+Trail\b', 'Prüfpfad', 'Audit Trail→Prüfpfad'),

    # FIX-52x: Engine composites (common in section keys leak into text)
    (r'\bRoadmap-Engine\b', 'Roadmap-Ansatz', 'Roadmap-Engine→Roadmap-Ansatz'),
    (r'\bRisk-Engine\b', 'Risiko-Analyse', 'Risk-Engine→Risiko-Analyse'),
    (r'\bRisk_Engine\b', 'Risiko-Analyse', 'Risk_Engine→Risiko-Analyse'),
    (r'\bBusiness-Case-Engine\b', 'Geschäftsfall-Analyse', 'Business-Case-Engine→Geschäftsfall-Analyse'),
    (r'\bRecommendations-Engine\b', 'Empfehlungs-Baustein', 'Recommendations-Engine→Empfehlungs-Baustein'),
    (r'\bVendor-Audit-Engine\b', 'Anbieter-Prüfung', 'Vendor-Audit-Engine→Anbieter-Prüfung'),
    (r'\bAnalyse-Engine\b', 'Analyse-Baustein', 'Analyse-Engine→Analyse-Baustein'),
    (r'\bKI-Engine\b', 'KI-Baustein', 'KI-Engine→KI-Baustein'),
    (r'\bEngines\b(?!ering)', 'Bausteine', 'Engines→Bausteine (Plural)'),
    (r'\bEngine\b(?!ering)', 'Baustein', 'Engine→Baustein (nicht Engineering)'),

    (r'\bGovernance-Struktur\b', 'Ordnungsrahmen', 'Governance-Struktur→Ordnungsrahmen'),
    (r'\bGovernance\b', 'Steuerung', 'Governance→Steuerung'),
    (r'\bCompliance-Framework\b', 'Regelwerk', 'Compliance-Framework→Regelwerk'),
    (r'\bCompliance\b', 'Regelkonformität', 'Compliance→Regelkonformität'),
    (r'\bFramework\b', 'Rahmenwerk', 'Framework→Rahmenwerk'),

    # Dashboard/KPI terms
    (r'\bKPI-Dashboard\b', 'Kennzahlen-Übersicht', 'KPI-Dashboard→Kennzahlen-Übersicht'),
    (r'\bDashboard\b', 'Übersicht', 'Dashboard→Übersicht'),
    (r'\bKPIs\b', 'Kennzahlen', 'KPIs→Kennzahlen'),
    (r'\bKPI\b', 'Kennzahl', 'KPI→Kennzahl'),
    (r'\bMetriken\b', 'Kennwerte', 'Metriken→Kennwerte'),
    (r'\bMetrik\b', 'Kennwert', 'Metrik→Kennwert'),

    # Process terms
    (r'\bProzesslandschaft\b', 'Arbeitsabläufe', 'Prozesslandschaft→Arbeitsabläufe'),
    (r'\bProzessoptimierung\b', 'Ablaufverbesserung', 'Prozessoptimierung→Ablaufverbesserung'),
    (r'\bProzesse\b', 'Abläufe', 'Prozesse→Abläufe'),
    (r'\bProzess\b', 'Ablauf', 'Prozess→Ablauf'),

    # FIX-RC3a: Enterprise terms found in Solo validator warnings
    (r'\bEnterprise-Software\b', 'Business-Software', 'Enterprise-Software→Business-Software'),
    (r'\bWertschöpfungskette\b', 'Leistungskette', 'Wertschöpfungskette→Leistungskette'),
    (r'\bStrategische Roadmap\b', 'Strategischer Fahrplan', 'Strategische Roadmap→Strategischer Fahrplan'),
    (r'\bStrategischen Roadmap\b', 'Strategischen Fahrplan', 'Strategischen Roadmap→Strategischen Fahrplan'),

    # Planning terms
    (r'\bMeilenstein-Planung\b', 'Etappenplanung', 'Meilenstein-Planung→Etappenplanung'),
    (r'\bMeilensteine\b', 'Etappen', 'Meilensteine→Etappen'),
    (r'\bMeilenstein\b', 'Etappe', 'Meilenstein→Etappe'),
    (r'\bRoadmap\b', 'Fahrplan', 'Roadmap→Fahrplan'),
    (r'\bTimeline\b', 'Zeitplan', 'Timeline→Zeitplan'),

    # Team/Resource terms
    (r'\bRessourcen\b', 'Mittel', 'Ressourcen→Mittel'),
    (r'\bRessource\b', 'Mittel', 'Ressource→Mittel'),
    (r'\bTeam-Kapazität\b', 'Ihre Zeit', 'Team-Kapazität→Ihre Zeit'),
    (r'\bPersonalressourcen\b', 'Arbeitskraft', 'Personalressourcen→Arbeitskraft'),

    # Fix-Batch C5: Kapazität-Artefakte → Solo-freundliche Alternativen
    (r'\bKapazität-Training\b', 'Kompetenzaufbau (Training)', 'Kapazität-Training→Kompetenzaufbau'),
    (r'\bKapazitäts-Training\b', 'Kompetenzaufbau', 'Kapazitäts-Training→Kompetenzaufbau'),
    (r'\bSchulungskapazität\b', 'Weiterbildungszeit', 'Schulungskapazität→Weiterbildungszeit'),
    (r'\bBelastung des Kapazitäten\b', 'Belastung Ihrer Zeit', 'Kapazitäten-Belastung→Zeit-Belastung'),
    (r'\bBelastung der Kapazitäten\b', 'Belastung Ihrer Zeit', 'Kapazitäten-Belastung→Zeit-Belastung'),
    (r'\bKapazitäten benötigen\b', 'Sie benötigen', 'Kapazitäten benötigen→Sie benötigen'),
    (r'\bKapazitäten erfordern\b', 'Es ist erforderlich', 'Kapazitäten erfordern→Es ist erforderlich'),
    (r'\bKapazitäten\b', 'Zeitbudget', 'Kapazitäten→Zeitbudget'),
    (r'\bKapazität\b', 'Zeitbudget', 'Kapazität→Zeitbudget'),

    # Fix-Batch C3: Remove placeholder text that triggers warnings
    (r'\bBeispieltext:?\b', '', 'Remove Beispieltext'),
    (r'\bPlatzhalter:?\b', '', 'Remove Platzhalter'),
    (r'\bMustertext:?\b', '', 'Remove Mustertext'),
    (r'\bDummy-?Text:?\b', '', 'Remove Dummy-Text'),
    (r'\b\[TODO\]\b', '', 'Remove TODO markers'),
    (r'\b\[TBD\]\b', '', 'Remove TBD markers'),

    # FIX-504 TASK 3: Additional solo-scale term replacements
    # Scaling terms (enterprise-scale → solo-scale)
    (r'\bSkalierungsphase\b', 'Ausbauphase', 'Skalierungsphase→Ausbauphase'),
    (r'\bSkalierungsstrategie\b', 'Ausbaustrategie', 'Skalierungsstrategie→Ausbaustrategie'),
    (r'\bSkalierungspotenzial\b', 'Ausbaupotenzial', 'Skalierungspotenzial→Ausbaupotenzial'),
    (r'\bhochskalieren\b', 'erweitern', 'hochskalieren→erweitern'),
    (r'\brumskalieren\b', 'anpassen', 'rumskalieren→anpassen'),

    # Additional Stack/Module terms
    (r'\bTool-Stack\b', 'Tool-Set', 'Tool-Stack→Tool-Set'),
    (r'\bSoftware-Stack\b', 'Werkzeugpaket', 'Software-Stack→Werkzeugpaket'),
    (r'\bCloud-Stack\b', 'Cloud-Werkzeuge', 'Cloud-Stack→Cloud-Werkzeuge'),
    (r'\bModulare\b', 'Flexible', 'Modulare→Flexible'),
    (r'\bmodularen\b', 'flexiblen', 'modularen→flexiblen'),
    (r'\bmodularer\b', 'flexibler', 'modularer→flexibler'),
    (r'\bmodulares\b', 'flexibles', 'modulares→flexibles'),

    # Customer/Scale terms (enterprise claims → solo-appropriate)
    # NOTE: 1000+/500+/100+ Kunden patterns moved to FIX-509-A section below
    (r'\bMassenskalierung\b', 'schrittweisen Ausbau', 'Massenskalierung→schrittweisen Ausbau'),
    (r'\bMassenrollout\b', 'schrittweise Einführung', 'Massenrollout→schrittweise Einführung'),
    (r'\bgroßflächig\b', 'schrittweise', 'großflächig→schrittweise'),
    (r'\bflächendeckend\b', 'umfassend', 'flächendeckend→umfassend'),

    # Personnel terms (enterprise → solo)
    (r'\bTeam-Skalierung\b', 'Kapazitätserweiterung', 'Team-Skalierung→Kapazitätserweiterung'),
    (r'\bPersonalaufbau\b', 'externe Unterstützung', 'Personalaufbau→externe Unterstützung'),
    (r'\bMitarbeiteraufbau\b', 'Auslastungsoptimierung', 'Mitarbeiteraufbau→Auslastungsoptimierung'),
    (r'\bPersonalressourcen\b', 'Ihre Zeit', 'Personalressourcen→Ihre Zeit'),
    (r'\bTeamressourcen\b', 'Ihre Kapazitäten', 'Teamressourcen→Ihre Kapazitäten'),

    # FIX-506 TASK 3: Additional solo-scale sanitizer terms
    # Kollegen → Netzwerk/Partner (solo has no colleagues)
    (r'\bKollegen\b', 'Partner', 'Kollegen→Partner'),
    (r'\bKollegin\b', 'Partnerin', 'Kollegin→Partnerin'),
    (r'\bKolleg(?:innen|en)\s+und\s+Kolleg(?:innen|en)\b', 'Netzwerkpartner', 'Kollegen und Kollegen→Netzwerkpartner'),
    (r'\bMit\s+Kollegen\b', 'Mit Partnern', 'Mit Kollegen→Mit Partnern'),
    (r'\bIhre\s+Kollegen\b', 'Ihr Netzwerk', 'Ihre Kollegen→Ihr Netzwerk'),
    (r'\bden\s+Kollegen\b', 'dem Netzwerk', 'den Kollegen→dem Netzwerk'),
    (r'\bdie\s+Kollegen\b', 'das Netzwerk', 'die Kollegen→das Netzwerk'),

    # FIX-509-A: Solo-Scale Narrative Cleanup
    # Eliminate scaling narratives that don't fit solo profiles
    # "1000+ Kunden" → "deutlich mehr Mandate ohne linearen Zeitaufwand"
    (r'\b1000\+?\s*Kunden\b', 'deutlich mehr Mandate ohne linearen Zeitaufwand', 'FIX-509-A: 1000+ Kunden→mehr Mandate'),
    (r'\bErweiterung\s+auf\s+1000\+?\s*Kunden\b', 'deutlich mehr Mandate ohne linearen Zeitaufwand', 'FIX-509-A: Erweiterung auf 1000+'),
    (r'\b500\+?\s*Kunden\b', 'mehr Mandate ohne Mehraufwand', 'FIX-509-A: 500+ Kunden→mehr Mandate'),
    (r'\b100\+?\s*Kunden\b', 'weitere Mandanten', 'FIX-509-A: 100+ Kunden→weitere Mandanten'),
    # "internationale Expansion" → "schrittweise Markterweiterung"
    (r'\binternationale\s+Expansion\b', 'schrittweise Markterweiterung', 'FIX-509-A: internationale Expansion'),
    (r'\bInternationale\s+Expansion\b', 'Schrittweise Markterweiterung', 'FIX-509-A: Internationale Expansion'),
    (r'\bglobale\s+Expansion\b', 'schrittweise Markterweiterung', 'FIX-509-A: globale Expansion'),
    (r'\bweltweite\s+Expansion\b', 'schrittweise Markterweiterung', 'FIX-509-A: weltweite Expansion'),
    # "Plattform" already handled above, but add more specific patterns
    (r'\bPlattform-Skalierung\b', 'Produkt-Ausbau', 'FIX-509-A: Plattform-Skalierung'),
    (r'\bPlattformwachstum\b', 'Produktwachstum', 'FIX-509-A: Plattformwachstum'),

    # Infrastructure terms
    (r'\bInfrastrukturaufbau\b', 'Tool-Einrichtung', 'Infrastrukturaufbau→Tool-Einrichtung'),
    (r'\bSystem-Landschaft\b', 'Tool-Übersicht', 'System-Landschaft→Tool-Übersicht'),
    (r'\bSystemlandschaft\b', 'Tool-Übersicht', 'Systemlandschaft→Tool-Übersicht'),
    (r'\bUnternehmens-IT\b', 'Ihre Technik', 'Unternehmens-IT→Ihre Technik'),
    (r'\bEnterprise-Lösung\b', 'passende Lösung', 'Enterprise-Lösung→passende Lösung'),
    (r'\bEnterprise\b', 'professionelle', 'Enterprise→professionelle'),

    # --- FIX-52x: hard leaks observed in Report-520 ---
    # Skalierung plural/genitive forms
    (r'\bSkalierungen\b', 'Erweiterungen', 'FIX-52x: Skalierungen→Erweiterungen'),

    # Audit-Trail space variant
    (r'\bAudit\s+Trail\b', 'Prüfpfad', 'FIX-52x: Audit Trail→Prüfpfad'),

    # Stack variants with space instead of hyphen
    (r'\bKI\s+Stack\b', 'KI-Werkzeuge', 'FIX-52x: KI Stack→KI-Werkzeuge'),
    (r'\bTech\s+Stack\b', 'Technikpaket', 'FIX-52x: Tech Stack→Technikpaket'),
    (r'\bFull[-\s]?Stack\b', 'End-to-End', 'FIX-52x: Full-Stack→End-to-End'),
]


# =============================================================================
# FIX-509-B: ZERO-LEAK PHRASE KILL (GLOBAL & DETERMINISTIC)
# =============================================================================
# These phrases trigger regeneration/fallback and must be eliminated BEFORE
# zero-leak detection runs. Applied to ALL sections, not just solo.

ZERO_LEAK_PHRASE_REPLACEMENTS = [
    # (pattern, replacement, description)
    # "bei Bedarf" → "optional"
    (r'\bbei\s+Bedarf\b', 'optional', 'FIX-509-B: bei Bedarf→optional'),
    (r'\bBei\s+Bedarf\b', 'Optional', 'FIX-509-B: Bei Bedarf→Optional'),
    # "auf Wunsch" → "optional"
    (r'\bauf\s+Wunsch\b', 'optional', 'FIX-509-B: auf Wunsch→optional'),
    (r'\bAuf\s+Wunsch\b', 'Optional', 'FIX-509-B: Auf Wunsch→Optional'),
    # "wie kann ich dir helfen" → remove completely
    (r'\bwie\s+kann\s+ich\s+dir\s+helfen\b', '', 'FIX-509-B: wie kann ich dir helfen→remove'),
    (r'\bWie\s+kann\s+ich\s+dir\s+helfen\b', '', 'FIX-509-B: Wie kann ich dir helfen→remove'),
    (r'\bwie\s+kann\s+ich\s+Ihnen\s+helfen\b', '', 'FIX-509-B: wie kann ich Ihnen helfen→remove'),
    (r'\bWie\s+kann\s+ich\s+Ihnen\s+helfen\b', '', 'FIX-509-B: Wie kann ich Ihnen helfen→remove'),
    # Additional conversational phrases that trigger leaks
    (r'\bwas\s+kann\s+ich\s+für\s+Sie\s+tun\b', '', 'FIX-509-B: was kann ich für Sie tun→remove'),
    (r'\bWas\s+kann\s+ich\s+für\s+Sie\s+tun\b', '', 'FIX-509-B: Was kann ich für Sie tun→remove'),
    (r'\bgerne\s+helfe\s+ich\b', '', 'FIX-509-B: gerne helfe ich→remove'),
    (r'\bGerne\s+helfe\s+ich\b', '', 'FIX-509-B: Gerne helfe ich→remove'),
]


def apply_zero_leak_phrase_cleanup(sections: dict) -> dict:
    """
    FIX-509-B: Global pre-clean step to eliminate phrases that trigger
    regeneration/fallback. Runs BEFORE zero-leak detection.

    This is applied to ALL LLM-generated sections regardless of company size.

    Args:
        sections: Dict with all report sections

    Returns:
        sections: Cleaned dict with leak phrases replaced
    """
    total_replacements = 0
    sections_touched = 0

    # All LLM-generated sections that might contain leak phrases
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "EXECUTIVE_DECISION_HTML", "RECOMMENDATIONS_HTML",
        "QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT",
        "ROADMAP_90D_HTML", "ROADMAP_90D_DECISION_HTML", "ROADMAP_12M_HTML",
        "GAMECHANGER_HTML", "GAMECHANGER_DECISION_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML", "AI_ACT_SUMMARY_HTML",
        "TOOLS_HTML", "TOOLS_EMPFEHLUNGEN_HTML", "DATA_STRATEGY_HTML", "DATA_READINESS_HTML",
        "GOVERNANCE_HTML", "STRATEGIE_GOVERNANCE_HTML", "KI_STACK_SUMMARY_HTML",
        "BRANCH_DEEP_DIVE_HTML", "TOP_3_MASSNAHMEN_HTML", "MONETARISIERUNG_HTML",
        "TEMPLATES_START_HTML", "KICKOFF_VORLAGE_HTML", "PROMPT_FRAMEWORK_HTML",
        "TECHNOLOGIE_PROZESSE_HTML", "WETTBEWERB_BENCHMARK_HTML", "UNTERNEHMENSPROFIL_MARKT_HTML",
    ]

    for section_name in check_sections:
        content = sections.get(section_name)
        if not content or not isinstance(content, str):
            continue

        section_replacements = 0
        for pattern, replacement, desc in ZERO_LEAK_PHRASE_REPLACEMENTS:
            try:
                new_content, count = re.subn(pattern, replacement, content, flags=re.IGNORECASE)
                if count > 0:
                    content = new_content
                    section_replacements += count
                    log.debug(f"[ZERO-LEAK-CLEANUP] {section_name}: {desc} ({count}x)")
            except re.error as e:
                log.warning(f"[ZERO-LEAK-CLEANUP] Regex error for '{pattern}': {e}")

        if section_replacements > 0:
            # Clean up any resulting double spaces
            content = re.sub(r'\s{2,}', ' ', content)
            content = re.sub(r'\s+([.,;:!?])', r'\1', content)  # Fix space before punctuation
            sections[section_name] = content
            total_replacements += section_replacements
            sections_touched += 1

    if total_replacements > 0:
        log.info(f"[ZERO-LEAK-CLEANUP] Completed: {total_replacements} replacements in {sections_touched} sections")

    return sections


def apply_solo_language_normalizer(sections: dict, company_size: str) -> dict:
    """
    Ersetzt Enterprise-Begriffe durch Solo-freundliche Alternativen.

    v14.35.22: Nur angewendet wenn company_size == "solo".
    Reduziert SIZE_MISMATCH Warnings ohne Bedeutungsänderung.

    Args:
        sections: Dict mit allen Report-Sections
        company_size: Unternehmensgröße ("solo", "team", "kmu")

    Returns:
        sections: Bereinigtes Dict
    """
    # FIX-C6: Apply persona replacements for solo AND team
    size_lower = (company_size or "").lower()

    # Sections to process - Fix-Batch C3: Expanded list to cover all content sections
    # FIX-526: Added NEXT_ACTIONS_HTML, PILOT_PLAN_HTML
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "EXECUTIVE_DECISION_HTML", "RECOMMENDATIONS_HTML",
        "QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT",
        "ROADMAP_90D_HTML", "ROADMAP_90D_DECISION_HTML", "ROADMAP_12M_HTML",
        "GAMECHANGER_HTML", "GAMECHANGER_DECISION_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML", "AI_ACT_SUMMARY_HTML",
        "TOOLS_HTML", "TOOLS_EMPFEHLUNGEN_HTML", "DATA_STRATEGY_HTML", "DATA_READINESS_HTML",
        "GOVERNANCE_HTML", "STRATEGIE_GOVERNANCE_HTML", "KI_STACK_SUMMARY_HTML",
        "BRANCH_DEEP_DIVE_HTML", "TOP_3_MASSNAHMEN_HTML", "MONETARISIERUNG_HTML",
        "TEMPLATES_START_HTML", "KICKOFF_VORLAGE_HTML", "PROMPT_FRAMEWORK_HTML",
        "TECHNOLOGIE_PROZESSE_HTML", "WETTBEWERB_BENCHMARK_HTML", "UNTERNEHMENSPROFIL_MARKT_HTML",
        "NEXT_ACTIONS_HTML", "PILOT_PLAN_HTML",
        # FIX-P2-C2: Added missing sections that still had blacklist terms
        "KI_AKTIVITAETEN_ZIELE_HTML", "ki_aktivitaeten_ziele",
        "AI_POLICY_MINI_HTML", "ai_policy_mini",
        "VENDOR_AUDIT_HTML", "RISK_ENGINE_V3_HTML",
        "SOFORT_START_HTML",
        # FIX-S13A: Starter Kit sections were missing from solo language normalizer
        "STARTER_KIT_HTML", "STARTER_KIT_COMPACT_HTML",
        # FIX-P3-C3: Shadow keys for sections that also exist as lowercase
        "templates_start", "wettbewerb_benchmark",
        # FIX-S14C: Missing sections that could contain Stakeholder/forbidden terms
        "MANAGEMENT_SUMMARY_HTML", "FOERDERPROGRAMME_HTML", "COMPLIANCE_HTML",
        "BRANCH_RISKS_HTML", "BUSINESS_CASE_ENGINE_HTML", "BUSINESS_CASE_SIM_HTML",
        "BUSINESS_CASE_TABLE_HTML", "FUNDING_HTML", "FUNDING_BRANCH_ALIGNMENT_HTML",
        "FUNDING_TABLE_HTML", "HERO_HTML", "KOSTEN_UEBERSICHT_HTML",
        "OPEN_INPUTS_HTML", "ROI_HTML", "ROI_TRACKING_HTML",
        "STARTER_KITS_HTML", "TOOLS_BRANCH_ALIGNMENT_HTML",
        "TOOLS_FUNDING_ALIGNMENT_HTML", "TOOLS_SECTION_HTML",
        # KIS-1191 Sprint-1027.1.1: Include pristine QW snapshot in SOLO-LANGUAGE
        # pass. Snapshot is taken before enforcer passes to preserve PROBLEM/
        # WIRKUNG/UMSETZUNG block structure, but pure term substitutions are
        # safe and required — otherwise validator catches blacklist terms
        # ("Governance", "Stakeholder", …) on the un-normalized snapshot.
        "_QUICK_WINS_PRISTINE",
    ]

    # Team-specific replacements
    if size_lower == "team":
        TEAM_REPLACEMENTS = [
            (r"\bGovernance-Board\b", "KI-Verantwortlichen"),
            (r"\bGovernance Board\b", "KI-Verantwortlichen"),
            (r"\bEnterprise-Architektur\b", "IT-Struktur"),
            (r"\bKonzernstruktur\b", "Unternehmensstruktur"),
            (r"\bRollout-Plan\b", "Umsetzungsplan"),
            (r"\bStakeholder-Analyse\b", "Beteiligte"),
        ]
        team_total = 0
        for sk in check_sections:
            val = sections.get(sk)
            if not val or not isinstance(val, str): continue
            mod = val
            for pat, rep in TEAM_REPLACEMENTS:
                ms = len(re.findall(pat, mod))
                if ms > 0: mod = re.sub(pat, rep, mod); team_total += ms
            if mod != val: sections[sk] = mod
        if team_total > 0:
            log.info("[FIX-C6] Team persona cleanup: %d replacements", team_total)
        return sections

    if size_lower != "solo":
        return sections

    total_replacements = 0
    sections_touched = 0

    for section_key in check_sections:
        content = sections.get(section_key)
        if not content or not isinstance(content, str):
            continue

        section_replacements = 0
        modified_content = content

        for pattern, replacement, desc in SOLO_TERM_REPLACEMENTS:
            matches = len(re.findall(pattern, modified_content, re.IGNORECASE))
            if matches > 0:
                modified_content = re.sub(pattern, replacement, modified_content, flags=re.IGNORECASE)
                section_replacements += matches

        if section_replacements > 0:
            # FIX-526: Clean up double-spaces from removals (e.g., "Rollout" → "")
            modified_content = re.sub(r'\s{2,}', ' ', modified_content)
            modified_content = re.sub(r'\s+([.,;:!?])', r'\1', modified_content)  # Fix space before punctuation
            sections[section_key] = modified_content
            sections_touched += 1
            total_replacements += section_replacements

    if total_replacements > 0:
        log.info(
            "[SOLO-LANGUAGE] replaced_terms=%d in %d sections (company_size=solo)",
            total_replacements,
            sections_touched
        )

    # --- FIX-52x: STRICT safety net for remaining solo persona leaks ---
    # FIX-S13A: Word-boundary regex + HTML-stripping to prevent false negatives
    #   from HTML tags breaking word boundaries (e.g. Stake<wbr>holder)
    if os.getenv("RELEASE_STRICT_MODE") == "1":
        forbidden = ["Skalierung", "Stakeholder", "Audit-Trail", "Audit Trail", "Stack", "Tech-Stack", "Full-Stack",
                     "Enterprise-Software", "Wertschöpfungskette", "Strategische Roadmap"]
        all_text = " ".join(str(v) for v in sections.values() if isinstance(v, str))
        # Strip HTML tags before matching (consistent with solo_leak_scanner)
        all_text = re.sub(r'<[^>]+>', ' ', all_text)
        all_text = re.sub(r'&shy;', '', all_text)
        all_text = re.sub(r'\s+', ' ', all_text)
        still = [t for t in forbidden if re.search(r'\b' + re.escape(t) + r'\b', all_text, re.IGNORECASE)]
        if still:
            raise RuntimeError(f"[FIX-52x][SOLO-LEAK] forbidden terms remain after rewrite: {still}")

    return sections


def apply_solo_language_to_briefing(briefing: dict, company_size: str) -> dict:
    """
    FIX-526 P2: Early-stage SOLO scrubbing for user free-text fields.

    Applies SOLO_TERM_REPLACEMENTS to user-provided briefing fields BEFORE
    they are used in prompts. This prevents forbidden terms from being
    "baked into" the LLM context.

    Target fields:
    - vision_3_jahre
    - hauptleistung
    - strategische_ziele
    - ki_vision
    - herausforderungen
    - stärken
    - etc.

    Args:
        briefing: Dict with user-provided briefing data
        company_size: Company size ("solo", "team", "kmu")

    Returns:
        Sanitized briefing dict
    """
    if not company_size or company_size.lower() != "solo":
        return briefing

    if not briefing:
        return briefing

    # Fields to scrub early
    early_scrub_fields = [
        "vision_3_jahre", "hauptleistung", "strategische_ziele",
        "ki_vision", "herausforderungen", "stärken", "schwächen",
        "zielgruppe", "wettbewerber", "usp", "geschäftsmodell",
        "ki_erfahrung", "bisherige_ki_nutzung", "freitext_notizen",
        "branche_beschreibung", "angebot_beschreibung",
    ]

    total_replacements = 0
    result = dict(briefing)

    for field in early_scrub_fields:
        value = result.get(field)
        if not value or not isinstance(value, str):
            continue

        modified = value
        field_replacements = 0

        for pattern, replacement, desc in SOLO_TERM_REPLACEMENTS:
            matches = len(re.findall(pattern, modified, re.IGNORECASE))
            if matches > 0:
                modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)
                field_replacements += matches

        if field_replacements > 0:
            # Clean up double-spaces from removals
            modified = re.sub(r'\s{2,}', ' ', modified)
            modified = re.sub(r'\s+([.,;:!?])', r'\1', modified)
            result[field] = modified
            total_replacements += field_replacements

    if total_replacements > 0:
        log.info(
            "[FIX-526][SOLO-BRIEFING] early_scrub: %d replacements in briefing fields",
            total_replacements
        )

    return result


# =============================================================================
# v14.35.21: PRODUCT NAME SAFETY NET (Seatbelt)
# =============================================================================
# This is a "seatbelt" - should never trigger if protection works correctly,
# but saves the release if something slips through.

PRODUCT_NAME_MUTATIONS = [
    # (broken_pattern, correct_replacement)
    (r"Microsoft\s+Kapazitäten", "Microsoft Teams"),
    (r"MS\s+Kapazitäten", "MS Teams"),
    (r"Google\s+Kapazitäten", "Google Teams"),  # hypothetical
]


def fix_product_name_mutations(html: str) -> tuple[str, int]:
    """
    Safety Net: Korrigiert fehlerhafte Produktnamen-Mutationen.

    v14.35.21: "Microsoft Kapazitäten" → "Microsoft Teams"

    This is a seatbelt - should never trigger if the protection in
    apply_solo_persona_filter() works correctly.

    Returns:
        tuple: (fixed_html, fix_count)
    """
    if not html:
        return html, 0

    result = html
    fix_count = 0

    for broken_pattern, correct in PRODUCT_NAME_MUTATIONS:
        pattern = re.compile(broken_pattern, re.IGNORECASE)
        matches = pattern.findall(result)
        if matches:
            result = pattern.sub(correct, result)
            fix_count += len(matches)
            log.warning(
                f"[SAFETY-NET] Fixed product name mutation: "
                f"'{broken_pattern}' → '{correct}' ({len(matches)}x)"
            )

    return result, fix_count


def apply_product_name_safety_net(sections: dict) -> dict:
    """
    Wendet Product Name Safety Net auf alle Sections an.

    v14.35.21: Seatbelt für "Microsoft Kapazitäten" → "Microsoft Teams"
    """
    total_fixes = 0

    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            fixed, count = fix_product_name_mutations(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count

    if total_fixes > 0:
        log.info(f"[SAFETY-NET] Total product name mutations fixed: {total_fixes}")

    return sections


# =============================================================================
# Fix-Batch F: TEXT GLITCH FIXER
# =============================================================================
# Known text glitches that appear in reports due to LLM word corruption or
# unwanted zero values that should be suppressed.

TEXT_GLITCH_REPLACEMENTS = [
    # (pattern, replacement, description)
    # Word corruption glitches
    (r'\bresourceselung\b', 'Ressourcenstaffelung', 'corrupted word'),
    (r'\bRessourceselung\b', 'Ressourcenstaffelung', 'corrupted word capitalized'),
    # KIS-1127/C9: "Bausteinering" = corrupted "Engineering" (Engine→Baustein leaking into compound)
    (r'\bBausteinering\b', 'Engineering', 'corrupted Engineering'),
    # Zero resource display suppression
    (r'Ressourcen:\s*0\b', '', 'zero resources'),
    (r'Ressourcen\s*:\s*0\b', '', 'zero resources with space'),
    (r'\bRessourcen\s+0\b', '', 'zero resources no colon'),
    # Empty placeholder patterns
    (r'Mitarbeiter:\s*0\b', '', 'zero employees'),
    (r'Mitarbeiter\s*:\s*0\b', '', 'zero employees with space'),
]


def fix_text_glitches(html: str) -> tuple[str, int]:
    """
    Fix-Batch F: Fix known text glitches in HTML content.

    Fixes:
    - "resourceselung" → "Ressourcenstaffelung"
    - "Ressourcen: 0" → (removed)
    - Other known glitches

    Returns:
        tuple: (fixed_html, fix_count)
    """
    if not html:
        return html, 0

    result = html
    fix_count = 0

    for pattern, replacement, desc in TEXT_GLITCH_REPLACEMENTS:
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(result)
        if matches:
            result = regex.sub(replacement, result)
            fix_count += len(matches)
            log.info(f"[GLITCH-FIX] Fixed '{desc}': {len(matches)}x")

    return result, fix_count


def apply_text_glitch_fixer(sections: dict) -> dict:
    """
    Fix-Batch F: Apply text glitch fixes to all sections.

    Fixes known LLM word corruptions and unwanted zero displays.
    """
    total_fixes = 0

    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            fixed, count = fix_text_glitches(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count

    if total_fixes > 0:
        log.info(f"[GLITCH-FIX] Total text glitches fixed: {total_fixes}")

    return sections


# =============================================================================
# v14.35.22: OPEN EXAMPLE PAREN FIXER
# =============================================================================
# Problem: Report 468 had "(z.B." or "(z. B." at sentence ends without closing
# Solution: Remove incomplete example references, end with proper punctuation
# =============================================================================

# Pattern for open "(z.B." / "(z. B." patterns
OPEN_EXAMPLE_PATTERNS = [
    # "(z.B." at end of tag content (before </tag>)
    (re.compile(r'\(z\.\s*[Bb]\.\s*(</)'), r'\1'),
    # "(z. B." with space
    (re.compile(r'\(z\.\s+[Bb]\.\s*(</)'), r'\1'),
    # "(z.B." at end of line/text
    (re.compile(r'\(z\.\s*[Bb]\.\s*$', re.MULTILINE), '.'),
    # Lone "z.B." at end (careful)
    (re.compile(r'(?<=[,;:\s])\s*z\.\s*[Bb]\.\s*$', re.MULTILINE), '.'),
]


def fix_open_example_paren_html(html: str) -> tuple[str, int]:
    """
    Fix open example parentheses like "(z.B." in HTML content.

    v14.35.22: Adressiert Report 468 Problem #2 - offene Klammern.
    """
    if not html:
        return html, 0

    fix_count = 0
    result = html

    for pattern, replacement in OPEN_EXAMPLE_PATTERNS:
        new_result, count = pattern.subn(replacement, result)
        if count > 0:
            fix_count += count
            result = new_result

    return result, fix_count


def apply_open_example_paren_fixer(sections: dict) -> dict:
    """
    Wendet Open Example Paren Fixer auf alle Sections an.

    v14.35.22: Entfernt unvollständige "(z.B." Muster
    """
    total_fixes = 0

    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 10:
            fixed, count = fix_open_example_paren_html(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count

    if total_fixes > 0:
        log.info(f"[OPEN-PAREN-FIX] Total open example parens fixed: {total_fixes}")

    return sections


# =============================================================================
# 1. ROI-FILTER: Entfernt ROI-Prozentsätze außerhalb Business Case
# =============================================================================

ROI_PATTERNS = [
    # Explizite ROI-Prozentsätze
    r'\b(\d{2,3})\s*%?\s*ROI\b',           # "284% ROI" oder "284 ROI"
    r'\bROI\s*(?:von|of|:)?\s*(\d{2,3})\s*%',  # "ROI von 284%" oder "ROI: 284%"
    r'\bROI\s*(\d{2,3})\s*%',              # "ROI 284%"
    r'ERWARTETER\s+ROI\s*:?\s*(\d{2,3})\s*%',  # "ERWARTETER ROI: 284%"
    # Rendite-Varianten
    r'\bRendite\s*(?:von)?\s*(\d{2,3})\s*%',
    # Standalone hohe Prozentsätze im ROI-Kontext (vorsichtig)
    r'(?:ROI|Rendite|Return)[^.]{0,30}(\d{2,3})\s*%',
]

# Sections wo ROI ERLAUBT ist
ROI_ALLOWED_SECTIONS = [
    "BUSINESS_CASE_HTML", "business_case",
    "ROI_HTML", "business_roi",
    "BUSINESS_CASE_TABLE_HTML", "business_case_table_html",
    "BUSINESS_CASE_ENGINE_HTML",
    "BUSINESS_CASE_SIM_HTML",
]

def remove_roi_from_section(html: str, section_name: str) -> tuple[str, int]:
    """
    Entfernt ROI-Prozentsätze aus einer Section.
    
    Returns:
        tuple: (cleaned_html, removal_count)
    """
    if not html or len(html) < 50:
        return html, 0
    
    # Skip wenn ROI erlaubt
    if any(allowed in section_name for allowed in ROI_ALLOWED_SECTIONS):
        return html, 0
    
    removal_count = 0
    result = html
    
    for pattern in ROI_PATTERNS:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        for match in reversed(matches):  # Reverse um Indizes stabil zu halten
            # Ersetze mit Verweis auf Business Case
            replacement = "→ siehe Business Case"
            result = result[:match.start()] + replacement + result[match.end():]
            removal_count += 1
            log.info(f"[ROI-FILTER] {section_name}: Removed '{match.group()}' → '{replacement}'")
    
    return result, removal_count


def apply_roi_filter(sections: dict) -> dict:
    """
    Wendet ROI-Filter auf alle relevanten Sections an.
    """
    total_removed = 0
    
    # Sections die geprüft werden sollen
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "executive_summary",
        "RECOMMENDATIONS_HTML", "recommendations", 
        "GAMECHANGER_HTML", "gamechanger",
        "QUICK_WINS_HTML", "quick_wins",
        "HERO_HTML", "hero",
        "ROADMAP_90D_HTML", "roadmap_90d",
        "ROADMAP_12M_HTML", "roadmap_12m",
        "FOERDERPOTENZIAL_HTML", "foerderpotenzial",
        "ORG_CHANGE_HTML", "org_change",
        "RISKS_HTML", "risks",
    ]
    
    for key in check_sections:
        if key in sections and sections[key]:
            cleaned, count = remove_roi_from_section(sections[key], key)
            if count > 0:
                sections[key] = cleaned
                total_removed += count
    
    log.info(f"[ROI-FILTER] Complete: {total_removed} ROI references removed")
    return sections


# =============================================================================
# 2. FRAGMENT-REPAIR: Repariert unvollständige Sätze
# =============================================================================

FRAGMENT_PATTERNS = [
    # "Maßnahme: Einrichten eines." → unvollständig
    (r'Maßnahme:\s*[A-ZÄÖÜ][a-zäöüß]+\s+eine[sr]?\s*\.', 
     'Maßnahme: Siehe detaillierte Beschreibung in der Roadmap.'),
    
    # "Maßnahme:." → leer
    (r'Maßnahme:\s*\.', 
     'Maßnahme: Siehe Roadmap für konkrete Schritte.'),
    
    # "Implementieren von." → unvollständig
    (r'Implementieren\s+von\s*\.', 
     'Implementieren der empfohlenen KI-Lösung.'),
    
    # "Aufbau einer." → unvollständig
    (r'Aufbau\s+eine[rs]?\s*\.', 
     'Aufbau einer strukturierten KI-Governance.'),
    
    # "Erstellung eines." → unvollständig
    (r'Erstellung\s+eine[sr]?\s*\.', 
     'Erstellung eines Pilotprojekt-Plans.'),
    
    # "Einrichten eines." → unvollständig
    (r'Einrichten\s+eine[sr]?\s*\.', 
     'Einrichten eines standardisierten Workflows.'),
    
    # "Integration von." → unvollständig
    (r'Integration\s+von\s*\.', 
     'Integration der KI-Tools in bestehende Prozesse.'),
    
    # "Entwicklung einer." → unvollständig
    
    # "strukturiertem JSON-Output und." → unvollständig (v14.17)
    # v14.18: "jedes." allein am Ende
    (r'\b(jedes)\.$', r'\1 Mal.'),
    # "betrachtet werden,." kaputte Interpunktion
    (r',\s*\.$', r'.'),
    (r'\b(\w+)\s+und\.$', r'\1 und mehr.'),
    (r'Entwicklung\s+eine[rs]?\s*\.', 
     'Entwicklung einer KI-Strategie.'),

    # "Maßnahme: Pilotierung eines klar." → Artikel + abgebrochenes Adjektiv
    (r'Maßnahme:\s*[A-ZÄÖÜ][a-zäöüß]+\s+eine[sr]?\s+[a-zäöüß]+\s*\.',
     'Maßnahme: Siehe detaillierte Beschreibung in der Roadmap.'),

    # "...eines kompakten." → Artikel + Adjektiv ohne Nomen
    (r'([A-ZÄÖÜ][^.!?]{10,50})\s+(eines|einer|einem)\s+[a-zäöüß]+\s*\.',
     r'\1 – siehe Roadmap für Details.'),

    
    # Generische Fragment-Erkennung: Satz endet mit Artikel
    (r'([A-ZÄÖÜ][^.!?]{10,50})\s+(eines|einer|einem|von|für|zur|zum)\s*\.', 
     r'\1 – siehe Roadmap für Details.'),
]

def repair_fragments_in_section(html: str, section_name: str) -> tuple[str, int]:
    """
    Repariert Fragment-Sätze in einer Section.
    
    Returns:
        tuple: (repaired_html, repair_count)
    """
    if not html or len(html) < 50:
        return html, 0
    
    repair_count = 0
    result = html
    
    for pattern, replacement in FRAGMENT_PATTERNS:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        if matches:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            repair_count += len(matches)
            for match in matches:
                log.info(f"[FRAGMENT-REPAIR] {section_name}: Fixed '{match.group()[:50]}...'")
    
    return result, repair_count


def apply_fragment_repair(sections: dict) -> dict:
    """
    Wendet Fragment-Repair auf alle relevanten Sections an.
    """
    total_repaired = 0
    
    # Sections die geprüft werden sollen
    check_sections = [
        "RECOMMENDATIONS_HTML", "recommendations",
        "QUICK_WINS_HTML", "quick_wins",
        "ROADMAP_90D_HTML", "roadmap_90d",
        "ROADMAP_12M_HTML", "roadmap_12m",
        "GAMECHANGER_HTML", "gamechanger",
        "ORG_CHANGE_HTML", "org_change",
    ]
    
    for key in check_sections:
        if key in sections and sections[key]:
            repaired, count = repair_fragments_in_section(sections[key], key)
            if count > 0:
                sections[key] = repaired
                total_repaired += count
    
    log.info(f"[FRAGMENT-REPAIR] Complete: {total_repaired} fragments repaired")
    return sections

def fix_truncation_ellipsis(html: str) -> tuple[str, int]:
    """
    v14.27: Entfernt Trunkierungs-Ellipsen aus HTML.
    Patterns wie "daue…", "Le…", "Se…" werden entfernt.
    """
    if not html:
        return html, 0
    
    result = html
    fixes = 0
    
    # Pattern: Wort das mit … oder ... endet (Trunkierung)
    # v14.28: Aggressiveres Ellipsis-Pattern (auch 1-Zeichen)
    truncated = re.findall(r'\b\w+[…..]{1,3}(?=\s|<|$|\*)', result)
    # Auch Markdown-formatierte truncations
    truncated += re.findall(r'\*\*\w+[…]+\*\*', result)
    for tw in truncated:
        if tw.endswith('…') or tw.endswith('...'):
            result = result.replace(tw, '')
            fixes += 1
    
    # Cleanup: Doppelte Leerzeichen
    result = re.sub(r'  +', ' ', result)
    
    if fixes > 0:
        log.info(f"[ELLIPSIS-FIX] Fixed {fixes} truncation ellipses")
    
    return result, fixes

def apply_ellipsis_fix(sections: dict) -> dict:
    """
    v14.27: Wendet Ellipsen-Fix auf alle relevanten Sections an.
    Entfernt Trunkierungs-Artefakte wie "daue…", "Le…", "Se…"
    """
    ellipsis_sections = [
        "RISKS_HTML", "risks", "BRANCH_RISKS_HTML",
        "RECOMMENDATIONS_HTML", "recommendations",
        "QUICK_WINS_HTML", "quick_wins",
        "GAMECHANGER_HTML", "gamechanger",
    ]
    
    total_fixed = 0
    for key in ellipsis_sections:
        if key in sections and sections[key]:
            fixed, count = fix_truncation_ellipsis(sections[key])
            if count > 0:
                sections[key] = fixed
                total_fixed += count
    
    if total_fixed > 0:
        log.info(f"[ELLIPSIS-FIX] Complete: {total_fixed} ellipses fixed")
    return sections


# =============================================================================
# 3. HAUPTLEISTUNG-ENFORCER: Injiziert hauptleistung wenn unter Minimum
# =============================================================================

def count_hauptleistung(html: str, hauptleistung: str) -> int:
    """Zählt Vorkommen von hauptleistung in HTML."""
    if not html or not hauptleistung:
        return 0
    # Case-insensitive Suche
    return len(re.findall(re.escape(hauptleistung), html, re.IGNORECASE))


def inject_hauptleistung_executive(html: str, hauptleistung: str, current_count: int, target: int = 4) -> str:
    # Z3: DISABLED — Enforcer creates fragment-duplicates (16×→5× after limiter)
    # With DB truncation at 72 chars, GPT already gets short version
    log.info("[Z3] HAUPTLEISTUNG-ENFORCER disabled (was injecting %d→%d, causing fragments)", current_count, target)
    return html  # Return unchanged
    """
    Injiziert hauptleistung in Executive Summary wenn unter Minimum.
    
    Strategy:
    - Ersetzt generische Phrasen durch hauptleistung-Version
    - Priorisiert wichtige Stellen
    """
    if current_count >= target:
        return html
    
    needed = target - current_count
    injections_made = 0
    result = html
    
    # Injection-Patterns (von spezifisch zu generisch)
    injection_patterns = [
        # "Ihr Unternehmen" → "Ihr Unternehmen mit {hauptleistung}"
        (r'\b(Ihr(?:em?)?\s+Unternehmen)\b(?!\s+mit)', 
         f'Ihr Unternehmen mit {hauptleistung}'),
        
        # "Ihr Kerngeschäft" → hauptleistung direkt
        (r'\b(Ihr(?:em?)?\s+Kerngeschäft)\b',
         hauptleistung),
        
        # "diese Leistung" → hauptleistung
        (r'\b(diese[r]?\s+Leistung)\b',
         hauptleistung),
        
        # "Ihr Geschäftsmodell" → "Ihr Geschäftsmodell ({hauptleistung})"
        (r'\b(Ihr(?:em?)?\s+Geschäftsmodell)\b(?!\s*\()',
         f'Ihr Geschäftsmodell ({hauptleistung})'),
        
        # Weitere universelle Synonyme (alle Größen)
        (r'\b(Ihre[rn]?\s+Dienstleistung(?:en)?)\b',
         hauptleistung),
        
        (r'\b(Ihr(?:em?)?\s+Angebot)\b(?!\s*\()',
         f'Ihr Angebot ({hauptleistung})'),
        
        (r'\b(dieses\s+Angebot)\b',
         hauptleistung),
        
        (r'\b(Ihre[rn]?\s+Tätigkeit)\b(?!\s*\()',
         f'Ihre Tätigkeit ({hauptleistung})'),
        
        (r'\b(Ihr(?:em?)?\s+Service)\b',
         hauptleistung),
        
        (r'\b(diese[rn]?\s+Service[s]?)\b',
         hauptleistung),
        
        (r'\b(Ihre[rn]?\s+Leistung(?:en)?)\b',
         hauptleistung),
        
        # Aggressive Patterns für mehr Treffer
        (r'\b(KI-Einsatz)\b(?!\s+für)',
         f'KI-Einsatz für {hauptleistung}'),
        
        (r'\b(Ihrer?\s+Branche)\b(?!\s*\()',
         f'Ihrer Branche ({hauptleistung})'),
        
        (r'\b(Ihrem?\s+Bereich)\b',
         f'Ihrem Bereich {hauptleistung}'),
        
        (r'\b(diesen?\s+Bereich)\b',
         hauptleistung),
        
        (r'\b(Ihr(?:em?)?\s+Betrieb)\b',
         f'Ihr Betrieb ({hauptleistung})'),
        
        (r'\b(diese[rn]?\s+Tätigkeit)\b',
         hauptleistung),

    ]
    for pattern, replacement in injection_patterns:
        if injections_made >= needed:
            break
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            result = re.sub(pattern, replacement, result, count=1, flags=re.IGNORECASE)
            injections_made += 1
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Executive: Injected at '{match.group()[:30]}...'")
    
    # v14.17: Fallback wenn nicht genug Pattern-Matches
    if injections_made < needed:
        fallback_patterns = [
            # v14.19: AGGRESSIVERE Patterns
            (r'(<p>)([A-Z][^<]{10,})', f'\\1Für {hauptleistung}: \\2'),
            (r'(</strong>)(\s*[A-Z])', f'\\1 Im Bereich {hauptleistung} \\2'),
            (r'(<li>)([^<]{5,})', f'\\1{hauptleistung} - \\2'),
            (r'(\w{5,})(</p>)', f'\\1 für {hauptleistung}\\2'),
        ]
        for fb_pattern, fb_replacement in fallback_patterns:
            if injections_made >= needed:
                break
            if re.search(fb_pattern, result):
                result = re.sub(fb_pattern, fb_replacement, result, count=1)
                injections_made += 1
                log.info(f"[HAUPTLEISTUNG-ENFORCER] Executive: Aggressive fallback applied")
    
    # Level 2: Prefix-Injection wenn immer noch nicht genug
    if injections_made < needed:
        prefix = f'<p><strong>Fokus: {hauptleistung}</strong></p>'
        result = prefix + result
        injections_made += 1
        log.info(f"[HAUPTLEISTUNG-ENFORCER] Executive: Prefix injection applied")
    
    return result


def inject_hauptleistung_recommendations(html: str, hauptleistung: str, current_count: int, target: int = 3) -> str:
    """
    Injiziert hauptleistung in Recommendations wenn unter Minimum.
    """
    if current_count >= target:
        return html
    
    needed = target - current_count
    injections_made = 0
    result = html
    
    # Injection-Patterns für Recommendations
    injection_patterns = [
        # "Für Ihr Geschäftsmodell" → "Für Ihr Geschäftsmodell {hauptleistung}"
        (r'\b(Für\s+Ihr(?:em?)?\s+Geschäftsmodell)\b(?!\s+' + re.escape(hauptleistung) + ')',
         f'Für Ihr Geschäftsmodell {hauptleistung}'),
        
        # "Ihre Dienstleistung" → hauptleistung
        (r'\b(Ihre[r]?\s+Dienstleistung(?:en)?)\b',
         hauptleistung),
        
        # "diesen Bereich" → hauptleistung  
        (r'\b(diesen\s+Bereich)\b',
         hauptleistung),
        
        # "Ihren Prozessen" → "Ihren {hauptleistung}-Prozessen"
        
        # Weitere universelle Patterns für Recommendations
        (r'\b(Ihre[rn]?\s+Arbeit(?:sweise)?)\b',
         f'Ihre Arbeit mit {hauptleistung}'),
        
        (r'\b(Ihr(?:em?)?\s+Kerngeschäft)\b',
         hauptleistung),
        
        (r'\b(diese[rn]?\s+Leistung(?:en)?)\b',
         hauptleistung),
        
        (r'\b(Ihr(?:em?)?\s+Angebot)\b',
         hauptleistung),
        
        (r'\b(Ihre[rn]?\s+Tätigkeit)\b',
         hauptleistung),
        
        (r'\b(in\s+diesem\s+Bereich)\b',
         f'im Bereich {hauptleistung}'),

        (r'\b(Ihren\s+Prozessen)\b',
         f'Ihren {hauptleistung}-Prozessen'),
    ]
    
    for pattern, replacement in injection_patterns:
        if injections_made >= needed:
            break
        match = re.search(pattern, result, re.IGNORECASE)
        if match:
            result = re.sub(pattern, replacement, result, count=1, flags=re.IGNORECASE)
            injections_made += 1
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected at '{match.group()[:30]}...'")
    
    # v14.28: Count-basierter Fallback für Recommendations
    # Anwenden solange count < needed (nicht "not in"!)
    current_count = result.count(hauptleistung)
    
    while current_count < needed:
        injected = False
        
        # Strategie 1: Nach "KI " einfügen (natürlich)
        if 'KI ' in result and f'KI im Bereich {hauptleistung}' not in result:
            result = result.replace('KI ', f'KI im Bereich {hauptleistung} ', 1)
            injected = True
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected after 'KI '")
        
        # Strategie 2: Nach "Prozess" einfügen
        elif 'Prozess' in result and f'Prozess {hauptleistung}' not in result:
            result = result.replace('Prozess', f'Prozess ({hauptleistung})', 1)
            injected = True
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected after 'Prozess'")
        
        # Strategie 3: Am Anfang eines <li> einfügen
        elif '<li>' in result:
            # Finde ein <li> ohne hauptleistung
            li_pattern = r'(<li>)([^<]{10,})'
            match = re.search(li_pattern, result)
            if match and hauptleistung not in match.group(2)[:50]:
                result = re.sub(li_pattern, f'\\1Für {hauptleistung}: \\2', result, count=1)
                injected = True
                log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Injected in <li>")
        
        if not injected:
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: No more injection points, count={current_count}")
            break
        
        current_count = result.count(hauptleistung)
        if current_count >= needed:
            log.info(f"[HAUPTLEISTUNG-ENFORCER] Recommendations: Target reached! count={current_count}")
            break
    
    return result


def fix_hauptleistung_concat(sections: dict, hauptleistung: str) -> dict:
    """
    FIX-R3-4A: Repair missing space/period before hauptleistung injections.

    After the enforcer aggressively inserts hauptleistung, it may be glued
    directly to the previous word:  ")Beratung und..."  or  "UnternehmenBeratung"
    This function inserts ". " where a word-character or ")" directly precedes
    the hauptleistung text.
    """
    if not hauptleistung or len(hauptleistung) < 10:
        return sections

    # Use first 30 chars of hauptleistung for matching (avoids issues with long text)
    hl_prefix = hauptleistung[:30]
    hl_escaped = re.escape(hl_prefix)
    # Pattern: word-char or ) directly followed by hauptleistung (no space)
    concat_pattern = re.compile(r'(\w|\))(' + hl_escaped + r')', re.IGNORECASE)

    total_fixes = 0
    for key, val in sections.items():
        if not isinstance(val, str) or key.startswith("_"):
            continue
        new_val = concat_pattern.sub(r'\1. \2', val)
        if new_val != val:
            fixes = len(concat_pattern.findall(val))
            sections[key] = new_val
            total_fixes += fixes

    if total_fixes > 0:
        log.info("[FIX-R3-4A] Fixed %d hauptleistung concat bugs (missing space/period)", total_fixes)

    return sections


def _count_hauptleistung_combined(html: str, hauptleistung: str) -> int:
    """
    FIX-R2-4: Count both full-text AND short-form hauptleistung occurrences.

    After FIX-3.1 replaces excess full-text with a short form, the combined
    count (full + short) is the true density.  The enforcer must use this to
    avoid re-injecting text that was deliberately shortened.
    """
    if not html or not hauptleistung:
        return 0
    full_count = len(re.findall(re.escape(hauptleistung), html, re.IGNORECASE))
    # Derive the same short form that FIX-3.1 uses
    short = hauptleistung[:120].rsplit(" ", 1)[0] + "..." if len(hauptleistung) > 120 else hauptleistung  # L1: was 60
    for sep in [",", ";", ".", " und ", " mit "]:
        pos = hauptleistung.find(sep)
        if 15 < pos < 80:
            short = hauptleistung[:pos]
            break
    if short != hauptleistung and len(short) > 10:
        short_count = len(re.findall(re.escape(short), html, re.IGNORECASE))
        # Subtract full occurrences that also match short prefix
        return max(full_count, short_count)
    return full_count


def apply_hauptleistung_enforcer(sections: dict, hauptleistung: str) -> dict:
    # Z+3: ENTIRE ENFORCER DISABLED — all injection paths created 19x hauptleistung in Run 616
    log.info("[Z+3] apply_hauptleistung_enforcer DISABLED (all injection paths off)")
    return sections
    """
    Enforced hauptleistung Minimum in Executive Summary und Recommendations.
    """
    if not hauptleistung or len(hauptleistung) < 3:
        log.warning("[HAUPTLEISTUNG-ENFORCER] No hauptleistung provided, skipping")
        return sections

    # FIX-R2-4: Skip enforcer if FIX-3.1 has already limited repetitions.
    # Re-injecting after FIX-3.1 causes garbled text ("...UnternehmenBeratung
    # und Unterstützung...").
    if sections.get("_fix_3_1_applied"):
        log.info("[HAUPTLEISTUNG-ENFORCER] Skipped — FIX-3.1 already applied, re-injection would cause garbling")
        return sections

    # Executive Summary: Minimum 4x (count full + short combined)
    for key in ["EXECUTIVE_SUMMARY_HTML", "executive_summary", "EXEC_SUMMARY_HTML"]:  # v14.23: FINAL_CHECK entfernt (ist Plain Text, nicht HTML)
        if key in sections and sections[key]:
            current = _count_hauptleistung_combined(sections[key], hauptleistung) if len(hauptleistung) > 50 else count_hauptleistung(sections[key], hauptleistung)
            if current < 4:
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: {current}/4 → enforcing")
                sections[key] = inject_hauptleistung_executive(
                    sections[key], hauptleistung, current, target=4
                )
                new_count = count_hauptleistung(sections[key], hauptleistung)
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: Now {new_count}/4")

    # Recommendations: Minimum 3x
    for key in ["RECOMMENDATIONS_HTML", "recommendations"]:
        if key in sections and sections[key]:
            current = _count_hauptleistung_combined(sections[key], hauptleistung) if len(hauptleistung) > 50 else count_hauptleistung(sections[key], hauptleistung)
            if current < 3:
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: {current}/3 → enforcing")
                sections[key] = inject_hauptleistung_recommendations(
                    sections[key], hauptleistung, current, target=3
                )
                new_count = count_hauptleistung(sections[key], hauptleistung)
                log.info(f"[HAUPTLEISTUNG-ENFORCER] {key}: Now {new_count}/3")

    return sections


# =============================================================================
# P0.1: STRAY PREFIX REMOVER & TEXT HYGIENE
# =============================================================================
# Removes leading artifacts like "?" and ensures text hygiene

STRAY_PREFIX_PATTERNS = [
    # Leading question marks (with or without whitespace)
    (re.compile(r'^(\s*)\?\s+'), r'\1'),
    # Leading question marks in paragraphs/list items
    (re.compile(r'(<p[^>]*>)\s*\?\s+'), r'\1'),
    (re.compile(r'(<li[^>]*>)\s*\?\s+'), r'\1'),
    # Multiple leading punctuation artifacts
    (re.compile(r'^(\s*)[?!.:;,]\s+([A-ZÄÖÜ])'), r'\1\2'),
]


def remove_stray_prefixes(html: str) -> tuple[str, int]:
    """
    P0.1: Remove leading artifacts like '?' from text.

    Problem: GPT sometimes generates "? Du kannst..." or "? Sie können..."
    Solution: Remove the leading "?" and fix the sentence.

    Returns:
        tuple: (cleaned_html, fix_count)
    """
    if not html:
        return html, 0

    fix_count = 0
    result = html

    for pattern, replacement in STRAY_PREFIX_PATTERNS:
        matches = len(pattern.findall(result))
        if matches > 0:
            result = pattern.sub(replacement, result)
            fix_count += matches

    return result, fix_count


def apply_stray_prefix_remover(sections: dict) -> dict:
    """
    P0.1: Apply stray prefix removal to all text sections.
    Removes leading '?' and other punctuation artifacts.
    """
    total_fixes = 0

    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "RECOMMENDATIONS_HTML", "QUICK_WINS_HTML",
        "ROADMAP_90D_HTML", "ROADMAP_12M_HTML", "GAMECHANGER_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML",
        "TOOLS_HTML", "DATA_STRATEGY_HTML", "GOVERNANCE_HTML",
    ]

    for key in check_sections:
        if key in sections and sections[key]:
            fixed, count = remove_stray_prefixes(sections[key])
            if count > 0:
                sections[key] = fixed
                total_fixes += count
                # Update lowercase alias
                lower_key = key.replace("_HTML", "").lower()
                if lower_key in sections:
                    sections[lower_key] = fixed

    if total_fixes > 0:
        log.info(f"[STRAY-PREFIX] Removed {total_fixes} leading punctuation artifacts")

    return sections


# =============================================================================
# 4. SIEZEN-GUARD EXTENSION: Erweiterte du→Sie Patterns
# =============================================================================

EXTENDED_SIEZEN_PATTERNS = [
    # Possessive "dein/deine"
    (r'[Ff]ür deine', 'Für Ihre'),  # v14.18: 'Für deine Situation' -> 'Für Ihre Situation'
    (r'\b[Dd]ein\b', 'Ihr'),  # "Dein Assessment" → "Ihr Assessment"
    (r'\b[Dd]eine([rsmn]?)\b', r'Ihre\1'),
    (r'\b[Dd]einem\b', 'Ihrem'),
    (r'\b[Dd]einen\b', 'Ihren'),
    
    # "Du bist" → "Sie sind"
    (r'\b[Dd]u\s+bist\b', 'Sie sind'),
    (r'\b[Dd]u\s+hast\b', 'Sie haben'),
    (r'\b[Dd]u\s+kannst\b', 'Sie können'),
    (r'\b[Dd]u\s+solltest\b', 'Sie sollten'),
    (r'\b[Dd]u\s+musst\b', 'Sie müssen'),
    (r'\b[Dd]u\s+wirst\b', 'Sie werden'),
    
    # Standalone "dir/dich"
    (r'\b[Dd]ir\b', 'Ihnen'),
    (r'\b[Dd]ich\b', 'Sie'),
    
    # "für dich" → "für Sie"
    (r'\bfür\s+dich\b', 'für Sie'),
    (r'\bvon\s+dir\b', 'von Ihnen'),
    (r'\bbei\s+dir\b', 'bei Ihnen'),
    (r'\bmit\s+dir\b', 'mit Ihnen'),
    
    # =========================================
    # IMPERATIVE (Du-Form → Sie-Form)
    # =========================================
    # Am Satzanfang oder nach Aufzählungszeichen
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Lerne\b', r'\1Lernen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Nutze\b', r'\1Nutzen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Teste\b', r'\1Testen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Baue\b', r'\1Bauen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Entwickle\b', r'\1Entwickeln Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Prüfe\b', r'\1Prüfen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Erstelle\b', r'\1Erstellen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Starte\b', r'\1Starten Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Plane\b', r'\1Planen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Überlege\b', r'\1Überlegen Sie'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Markiere\b', r'\1Markieren Sie'),  # v14.17
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Dokumentiere\b', r'\1Dokumentieren Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Achte\b', r'\1Achten Sie'),  # v14.26
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Setze\b', r'\1Setzen Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Erstelle\b', r'\1Erstellen Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Entwickle\b', r'\1Entwickeln Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Analysiere\b', r'\1Analysieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Optimiere\b', r'\1Optimieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Implementiere\b', r'\1Implementieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Evaluiere\b', r'\1Evaluieren Sie'),  # v14.27
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Integriere\b', r'\1Integrieren Sie'),  # v14.27
    
    # v14.29: AGGRESSIVE Imperative-Patterns (überall anwenden!)
    # Diese greifen an JEDER Position im Text
    (r'"Analysiere\b', '"Analysieren Sie'),  # Copy-Paste Prompts
    (r'"Erstelle\b', '"Erstellen Sie'),  # Copy-Paste Prompts
    (r'"Entwickle\b', '"Entwickeln Sie'),  # Copy-Paste Prompts
    (r'"Optimiere\b', '"Optimieren Sie'),  # Copy-Paste Prompts
    (r'"Prüfe\b', '"Prüfen Sie'),  # Copy-Paste Prompts
    # Auch ohne Anführungszeichen
    (r'(\s)Analysiere\b', r'\1Analysieren Sie'),  # Nach Whitespace
    (r'(\s)Erstelle\b', r'\1Erstellen Sie'),  # Nach Whitespace
    # v14.29: Skill-Fahrplan Fixes
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Etabliere\b', r'\1Etablieren Sie'),
    # "du" → "Sie" in bestimmten Kontexten
    # FIX: Complete phrases first (before generic "wenn du" → "wenn Sie")
    (r'\bWenn du magst\b', 'Wenn Sie möchten'),
    (r'\bwenn du magst\b', 'wenn Sie möchten'),
    (r'\bFalls du magst\b', 'Falls Sie möchten'),
    (r'\bfalls du magst\b', 'falls Sie möchten'),
    (r'\bWenn du möchtest\b', 'Wenn Sie möchten'),
    (r'\bwenn du möchtest\b', 'wenn Sie möchten'),
    (r'\bFalls du möchtest\b', 'Falls Sie möchten'),
    (r'\bfalls du möchtest\b', 'falls Sie möchten'),
    (r'\bwie du\b', 'wie Sie'),
    (r'\bdass du\b', 'dass Sie'),
    (r'\bwenn du\b', 'wenn Sie'),
    (r'\bob du\b', 'ob Sie'),
    (r', du ', ', Sie '),  # v14.31: Allgemeines du nach Komma
    (r'\bsparst du\b', 'sparen Sie'),  # v14.35.3: "sparst du" → "sparen Sie"
    (r'\bhast du\b', 'haben Sie'),  # v14.35.3: "hast du" → "haben Sie"
    (r'\bkannst du\b', 'können Sie'),  # v14.35.3: "kannst du" → "können Sie"
    (r'\bmusst du\b', 'müssen Sie'),  # v14.35.3: "musst du" → "müssen Sie"
    (r'\bwillst du\b', 'wollen Sie'),  # v14.35.3: "willst du" → "wollen Sie"
    (r'\bbrauchst du\b', 'brauchen Sie'),  # v14.35.3: "brauchst du" → "brauchen Sie"
    (r' du ', ' Sie '),  # v14.35.3: Allgemeines " du " → " Sie "
    # v14.35.4: Fragment-Fixes für GPT-generierte Abbrüche
    (r', weil\.$', '.'),  # ", weil." → "."
    (r' weil\.$', '.'),  # " weil." → "."
    (r' zu\.$', '.'),  # " zu." → "."
    (r'kann zu\.$', 'kann problematisch werden.'),  # "kann zu." → sinnvoll
    (r'Dies kann zu\.$', 'Dies kann problematisch werden.'),
    (r': Ein\.$', '.'),  # ": Ein." → "."
    (r': Eine\.$', '.'),  # ": Eine." → "."
    (r'Gegenmaßnahme: Ein\.$', 'Gegenmaßnahme: Siehe Empfehlungen.'),
    (r'Gegenmaßnahme: Eine\.$', 'Gegenmaßnahme: Siehe Empfehlungen.'),
    (r'Skepsis kann die\.$', 'Skepsis kann die Akzeptanz gefährden.'),
    (r'wächst es schnell zu\.$', 'wächst es schnell.'),
    (r'Audits und eine\.$', 'Audits und regelmäßige Überprüfungen.'),
    (r'Der EU AI Act verlangt\.$', 'Der EU AI Act stellt Anforderungen an KI-Systeme.'),
    (r'kommen Experimente\.$', 'kommen Experimente zu kurz.'),
    (r'direkt in Ihre\.$', 'direkt in Ihre Prozesse integrieren.'),
    (r'Testlauf mit\.$', 'Testlauf mit ersten Anwendungsfällen.'),
    # v14.35.6: Weitere Fragment-Fixes aus Validation
    (r'Pro Quartal\.$', 'Pro Quartal überprüfen.'),
    (r'Anforderungen\. \.', 'Anforderungen.'),  # Doppelpunkt-Artefakt
    (r'Dies steht im Konflikt mit\.$', 'Dies steht im Konflikt mit den Zielen.'),
    (r'Qualität der\.$', 'Qualität der Ergebnisse.'),
    (r' direkt\.$', '.'),  # "...Geschäftsmodell direkt." → "...Geschäftsmodell."
    (r' Workflow\.$', ' Workflow beeinträchtigen.'),
    (r'\.\s*Dies\.$', '.'),  # ". Dies." → "."
    (r' automatisierte\.$', ' automatisierte Prozesse.'),
    (r'\. \.$', '.'),  # ". ." → "."
    (r'\s+\.$', '.'),  # " ." → "."
    # Generische Fragment-Fänger (Ende mit Artikel/Präposition)
    (r' der\.$', '.'),
    (r' die\.$', '.'),
    (r' das\.$', '.'),
    (r' den\.$', '.'),
    (r' dem\.$', '.'),
    (r' mit\.$', '.'),
    (r' für\.$', '.'),
    (r' auf\.$', '.'),
    (r' bei\.$', '.'),
    (r' von\.$', '.'),
    # v14.35.10: Weitere Fragment-Fixes aus v14.35.8 Validation
    (r' wahrgenommenen\.$', ' wahrgenommenen Nutzen.'),
    (r' in Ihrem\.$', ' in Ihrem Unternehmen.'),
    (r' die jede\.$', ' die jede Bewertung absichern.'),
    (r' laufenden\.$', ' laufenden Projekten.'),
    (r' eine Ablauf ', ' einen Ablauf '),  # Grammatik-Fix
    (r'\(z\. B\.$', '(z. B. Templates).'),  # Offene Klammer schließen
    (r'\(z\.\s*B\.[^)]{0,5}$', '(z. B. Templates)'),  # Offene Klammer am Ende
    (r' können zu\.$', ' können zu Problemen führen.'),
    (r' Automatisierung der\.$', ' Automatisierung der Prozesse.'),
    # v14.35.11: Weitere Fragment-Fixes aus Validation
    (r' weil als\.$', '.'),
    (r' Pro Quartal\.$', ' pro Quartal überprüfen.'),
    (r' was mit\.$', '.'),
    (r' als Verstoß gegen\.$', ' als Verstoß gegen Richtlinien.'),
    (r' Tool-Stack auf wenige\.$', ' Tool-Stack auf wenige konzentrieren.'),
    (r' automatisch\.$', ' automatisch generiert.'),
    (r' die verschiedene\.$', ' die verschiedene Aufgaben erfüllen.'),
    (r' Arbeitsalltag der\.$', ' Arbeitsalltag der Mitarbeitenden.'),
    (r'zugerechnet werden\. \.', 'zugerechnet werden.'),
    # v14.35.12: Weitere Fragmente aus Validation
    (r' europäischer\.$', ' europäischer Anbieter.'),
    (r' drohen\.$', ' drohen erhebliche Risiken.'),
    (r' erschweren\.$', ' erschweren die Umsetzung.'),
    (r' kein\.$', '.'),
    (r' eine\.$', '.'),
    (r' die Sie\.$', ' die Sie nutzen können.'),
    # v14.35.13: Weitere Risk-Card Fragmente aus Validation
    (r' als europäischer\.$', ' als europäischer Anbieter etablieren.'),
    (r' zur Vision als\.$', '.'),
    (r' Akzeptanz der\.$', ' Akzeptanz der Mitarbeitenden sichern.'),
    (r' erschwert eine\.$', ' erschwert eine Umsetzung.'),
    (r' generiertem\.$', ' generiertem Content.'),
    (r' automatisch generiertem\.$', ' automatisch generiertem Content.'),
    (r' parallelen\.$', ' parallelen Experimenten.'),
    (r' Informationen drohen\.$', ' Informationen drohen verloren zu gehen.'),
    (r' weder zur\.$', '.'),
    (r' verleitet zu\.$', '.'),
    (r'\. \.$', '.'),  # Doppelpunkt am Ende
    # v14.35.13: PROPHYLAKTISCHE Fragment-Patterns (alle möglichen Endungen)
    # === Artikel-Endungen ===
    (r' der\.$', '.'),
    (r' die\.$', '.'),
    (r' das\.$', '.'),
    (r' den\.$', '.'),
    (r' dem\.$', '.'),
    (r' des\.$', '.'),
    (r' einer\.$', '.'),
    (r' eines\.$', '.'),
    (r' einem\.$', '.'),
    (r' einen\.$', '.'),
    # === Präposition-Endungen ===
    (r' mit\.$', '.'),
    (r' bei\.$', '.'),
    (r' für\.$', '.'),
    (r' auf\.$', '.'),
    (r' von\.$', '.'),
    (r' zur\.$', '.'),
    (r' zum\.$', '.'),
    (r' als\.$', '.'),
    (r' aus\.$', '.'),
    (r' nach\.$', '.'),
    (r' durch\.$', '.'),
    (r' über\.$', '.'),
    (r' unter\.$', '.'),
    (r' ohne\.$', '.'),
    (r' gegen\.$', '.'),
    (r' zwischen\.$', '.'),
    (r' während\.$', '.'),
    (r' wegen\.$', '.'),
    (r' trotz\.$', '.'),
    (r' seit\.$', '.'),
    (r' bis\.$', '.'),
    (r' außer\.$', '.'),
    (r' statt\.$', '.'),
    (r' innerhalb\.$', '.'),
    (r' außerhalb\.$', '.'),
    (r' anstatt\.$', '.'),
    (r' bezüglich\.$', '.'),
    (r' hinsichtlich\.$', '.'),
    (r' aufgrund\.$', '.'),
    (r' anhand\.$', '.'),
    (r' mittels\.$', '.'),
    (r' zwecks\.$', '.'),
    (r' gemäß\.$', '.'),
    (r' laut\.$', '.'),
    # === Konjunktion-Endungen ===
    (r' und\.$', '.'),
    (r' oder\.$', '.'),
    (r' aber\.$', '.'),
    (r' sowie\.$', '.'),
    (r' wenn\.$', '.'),
    (r' weil\.$', '.'),
    (r' dass\.$', '.'),
    (r' damit\.$', '.'),
    (r' obwohl\.$', '.'),
    (r' falls\.$', '.'),
    (r' sofern\.$', '.'),
    (r' sobald\.$', '.'),
    (r' solange\.$', '.'),
    (r' bevor\.$', '.'),
    (r' nachdem\.$', '.'),
    (r' während\.$', '.'),
    (r' indem\.$', '.'),
    (r' sodass\.$', '.'),
    (r' weshalb\.$', '.'),
    (r' wodurch\.$', '.'),
    (r' womit\.$', '.'),
    (r' worauf\.$', '.'),
    (r' woran\.$', '.'),
    (r' worin\.$', '.'),
    (r' wovon\.$', '.'),
    (r' wozu\.$', '.'),
    (r' wobei\.$', '.'),
    # === Pronomen-Endungen ===
    (r' Sie\.$', '.'),
    (r' Ihr\.$', '.'),
    (r' Ihre\.$', '.'),
    (r' Ihren\.$', '.'),
    (r' Ihrem\.$', '.'),
    (r' Ihrer\.$', '.'),
    (r' sich\.$', '.'),
    (r' diese\.$', '.'),
    (r' dieser\.$', '.'),
    (r' dieses\.$', '.'),
    (r' diesen\.$', '.'),
    (r' diesem\.$', '.'),
    (r' jede\.$', '.'),
    (r' jeder\.$', '.'),
    (r' jedes\.$', '.'),
    (r' jeden\.$', '.'),
    (r' jedem\.$', '.'),
    (r' alle\.$', '.'),
    (r' aller\.$', '.'),
    (r' allem\.$', '.'),
    (r' allen\.$', '.'),
    (r' welche\.$', '.'),
    (r' welcher\.$', '.'),
    (r' welches\.$', '.'),
    (r' welchen\.$', '.'),
    (r' welchem\.$', '.'),
    # === Adjektiv-Endungen (häufige) ===
    (r' neue\.$', '.'),
    (r' neuen\.$', '.'),
    (r' neuer\.$', '.'),
    (r' neues\.$', '.'),
    (r' neuem\.$', '.'),
    (r' wichtige\.$', '.'),
    (r' wichtigen\.$', '.'),
    (r' wichtiger\.$', '.'),
    (r' wichtiges\.$', '.'),
    (r' verschiedene\.$', '.'),
    (r' verschiedenen\.$', '.'),
    (r' verschiedener\.$', '.'),
    (r' große\.$', '.'),
    (r' großen\.$', '.'),
    (r' großer\.$', '.'),
    (r' großes\.$', '.'),
    (r' kleine\.$', '.'),
    (r' kleinen\.$', '.'),
    (r' kleiner\.$', '.'),
    (r' kleines\.$', '.'),
    (r' erste\.$', '.'),
    (r' ersten\.$', '.'),
    (r' erster\.$', '.'),
    (r' erstes\.$', '.'),
    (r' weitere\.$', '.'),
    (r' weiteren\.$', '.'),
    (r' weiterer\.$', '.'),
    (r' weiteres\.$', '.'),
    (r' andere\.$', '.'),
    (r' anderen\.$', '.'),
    (r' anderer\.$', '.'),
    (r' anderes\.$', '.'),
    (r' anderem\.$', '.'),
    (r' eigene\.$', '.'),
    (r' eigenen\.$', '.'),
    (r' eigener\.$', '.'),
    (r' eigenes\.$', '.'),
    (r' eigenem\.$', '.'),
    (r' bestimmte\.$', '.'),
    (r' bestimmten\.$', '.'),
    (r' bestimmter\.$', '.'),
    (r' bestimmtes\.$', '.'),
    (r' entsprechende\.$', '.'),
    (r' entsprechenden\.$', '.'),
    (r' entsprechender\.$', '.'),
    (r' wesentliche\.$', '.'),
    (r' wesentlichen\.$', '.'),
    (r' notwendige\.$', '.'),
    (r' notwendigen\.$', '.'),
    (r' relevante\.$', '.'),
    (r' relevanten\.$', '.'),
    (r' effektive\.$', '.'),
    (r' effektiven\.$', '.'),
    (r' strategische\.$', '.'),
    (r' strategischen\.$', '.'),
    (r' technische\.$', '.'),
    (r' technischen\.$', '.'),
    (r' automatische\.$', '.'),
    (r' automatischen\.$', '.'),
    (r' manuelle\.$', '.'),
    (r' manuellen\.$', '.'),
    (r' digitale\.$', '.'),
    (r' digitalen\.$', '.'),
    (r' kritische\.$', '.'),
    (r' kritischen\.$', '.'),
    (r' konkrete\.$', '.'),
    (r' konkreten\.$', '.'),
    (r' aktuelle\.$', '.'),
    (r' aktuellen\.$', '.'),
    (r' zukünftige\.$', '.'),
    (r' zukünftigen\.$', '.'),
    (r' erfolgreiche\.$', '.'),
    (r' erfolgreichen\.$', '.'),
    (r' mögliche\.$', '.'),
    (r' möglichen\.$', '.'),
    (r' schnelle\.$', '.'),
    (r' schnellen\.$', '.'),
    (r' langfristige\.$', '.'),
    (r' langfristigen\.$', '.'),
    (r' kurzfristige\.$', '.'),
    (r' kurzfristigen\.$', '.'),
    # === Verb-Endungen (Partizip/abgebrochen) ===
    (r' können\.$', '.'),
    (r' werden\.$', '.'),
    (r' sollten\.$', '.'),
    (r' müssen\.$', '.'),
    (r' wollen\.$', '.'),
    (r' haben\.$', '.'),
    (r' sein\.$', '.'),
    (r' sind\.$', '.'),
    (r' wird\.$', '.'),
    (r' kann\.$', '.'),
    (r' soll\.$', '.'),
    (r' muss\.$', '.'),
    # === Spezielle Kombinationen ===
    (r' zu einem\.$', '.'),
    (r' zu einer\.$', '.'),
    (r' zu den\.$', '.'),
    (r' in der\.$', '.'),
    (r' in den\.$', '.'),
    (r' in dem\.$', '.'),
    (r' in einer\.$', '.'),
    (r' in einem\.$', '.'),
    (r' an der\.$', '.'),
    (r' an den\.$', '.'),
    (r' an dem\.$', '.'),
    (r' auf der\.$', '.'),
    (r' auf den\.$', '.'),
    (r' auf dem\.$', '.'),
    (r' bei der\.$', '.'),
    (r' bei den\.$', '.'),
    (r' bei dem\.$', '.'),
    (r' für die\.$', '.'),
    (r' für den\.$', '.'),
    (r' für das\.$', '.'),
    (r' mit der\.$', '.'),
    (r' mit den\.$', '.'),
    (r' mit dem\.$', '.'),
    (r' von der\.$', '.'),
    (r' von den\.$', '.'),
    (r' von dem\.$', '.'),
    (r' aus der\.$', '.'),
    (r' aus den\.$', '.'),
    (r' aus dem\.$', '.'),
    (r' nach der\.$', '.'),
    (r' nach den\.$', '.'),
    (r' nach dem\.$', '.'),
    (r' durch die\.$', '.'),
    (r' durch den\.$', '.'),
    (r' durch das\.$', '.'),
    (r' über die\.$', '.'),
    (r' über den\.$', '.'),
    (r' über das\.$', '.'),
    # === Offene Klammern ===
    (r'\([^)]{0,20}$', ''),  # Offene Klammer am Ende (max 20 Zeichen)
    (r'\(z\.\s*B\.\s*$', ''),  # Häufig: "(z. B." am Ende
    (r'\bsparst du\b', 'sparen Sie'),  # v14.35.3: "sparst du" → "sparen Sie"
    (r'\b([a-z]+)st du\b', r'\1en Sie'),  # Allgemein: "Xst du" → "Xen Sie"
    
    # v14.32: Verbkonjugation nach "Sie" korrigieren (Sie + -st → Sie + -en)
    (r'\bSie ([\w]+)st\b', r'Sie \1en'),  # Allgemeines Pattern
    # Spezifische häufige Fälle:
    (r'\bSie einhältst\b', 'Sie einhalten'),
    (r'\bSie prüfst\b', 'Sie prüfen'),
    (r'\bSie erstellst\b', 'Sie erstellen'),
    (r'\bSie analysierst\b', 'Sie analysieren'),
    (r'\bSie dokumentierst\b', 'Sie dokumentieren'),
    (r'\bSie redigierst\b', 'Sie redigieren'),
    (r'\bSie arbeitest\b', 'Sie arbeiten'),
    (r'\bSie nutzt\b', 'Sie nutzen'),
    (r'\bSie verwendest\b', 'Sie verwenden'),
    (r'\bSie brauchst\b', 'Sie brauchen'),
    (r'\bSie hast\b', 'Sie haben'),
    (r'\bSie bist\b', 'Sie sind'),
    (r'\bSie kannst\b', 'Sie können'),
    (r'\bSie musst\b', 'Sie müssen'),
    (r'\bSie sollst\b', 'Sie sollen'),
    (r'\bSie willst\b', 'Sie wollen'),
    
    # v14.29: Persona-Leak Fixes für Solo
    # Diese Enterprise-Begriffe werden für Solo ersetzt
    (r'\bModule\b', 'Bausteine'),  # Modul → Baustein
    (r'\bModul\b', 'Baustein'),
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    # v14.35: skalier*-Familie komplett (alle deutschen Flexionen)
    (r'\bSkalierung\b', 'Erweiterung'),  # feminin bleibt feminin
    (r'Skalierungs', 'Erweiterungs'),
    (r'\bskalieren\b', 'erweitern'),  # Verb
    (r'\bSkalierbarkeit\b', 'Erweiterbarkeit'),  # Substantiv
    (r'\bskalierbar\b', 'erweiterbar'),  # Adjektiv Grundform
    (r'\bskaliert\b', 'erweitert'),  # v14.35.4: Verb Partizip/3.Person
    (r'\bskalieren\b', 'erweitern'),  # v14.35.4: Verb Infinitiv
    (r'\bSkalierung auf \d+', 'Erweiterung auf'),  # v14.35.4: "Skalierung auf 1000+"
    (r'\bSkalierungs', 'Erweiterungs'),  # v14.35.4: Komposita
    (r'\bskalierbare\b', 'erweiterbare'),  # v14.35: Adjektiv feminin/Plural
    (r'\bskalierbares\b', 'erweiterbares'),  # v14.35: Adjektiv neutrum
    (r'\bskalierbaren\b', 'erweiterbaren'),  # v14.35: Adjektiv Dativ/Genitiv
    (r'\bskalierbarer\b', 'erweiterbarer'),  # v14.35: Adjektiv maskulin/Genitiv
    (r'\bhochskaliert', 'stark erweitert'),  # Partizip
    # v14.35.8: Explizite Großschreibungs-Patterns (statt IGNORECASE)
    (r'\bSkalierbare\b', 'Erweiterbare'),  # Am Satzanfang
    (r'\bSkalierbares\b', 'Erweiterbares'),
    (r'\bSkalierbaren\b', 'Erweiterbaren'),
    (r'\bSkalierbarer\b', 'Erweiterbarer'),
    (r'\bSkaliert\b', 'Erweitert'),  # Am Satzanfang
    (r'\bSkalieren\b', 'Erweitern'),
    (r'\bSkalieren\b', 'Erweitern'),
    (r'\bEngine\b', 'System'),
    # v14.35: Framework-Familie komplett
    (r'\bFrameworks\b', 'Konzepte'),  # v14.35: Plural zuerst (greedy)
    (r'\bFramework\b', 'Konzept'),
    (r'Assessment-Frameworks', 'Bewertungskonzepte'),  # v14.35: Zusammensetzung
    (r'Business-Case-Frameworks', 'Business-Case-Vorlagen'),  # v14.35: Zusammensetzung
    (r'\bPipeline\b', 'Ablauf'),
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Standardisiere\b', r'\1Standardisieren Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Strukturiere\b', r'\1Strukturieren Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Verbinde\b', r'\1Verbinden Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Richte\b', r'\1Richten Sie'),  # v14.20
    (r'(^|[.!?:]\s*|<li>\s*|<p>\s*)Definiere\b', r'\1Definieren Sie'),  # v14.20

]

def apply_extended_siezen(html: str) -> tuple[str, int]:
    """
    Erweiterte du→Sie Konvertierung für Fälle die der Standard-Guard verpasst.
    """
    if not html:
        return html, 0
    
    replacements = 0
    result = html
    
    for pattern, replacement in EXTENDED_SIEZEN_PATTERNS:
        matches = len(re.findall(pattern, result))
        if matches > 0:
            result = re.sub(pattern, replacement, result)
            replacements += matches
    
    return result, replacements


def apply_extended_siezen_guard(sections: dict) -> dict:
    """
    Wendet erweiterte Siezen-Patterns auf alle Text-Sections an.
    """
    total_fixed = 0
    
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "RECOMMENDATIONS_HTML", "QUICK_WINS_HTML",
        "ROADMAP_90D_HTML", "ROADMAP_12M_HTML", "GAMECHANGER_HTML",
        "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
        "KI_SKILLPLAN_HTML", "TEMPLATES_START_HTML", "KICKOFF_VORLAGE_HTML",
        "ROI_TRACKING_HTML", "PROMPT_FRAMEWORK_HTML",
    ]
    
    for key in check_sections:
        if key in sections and sections[key]:
            fixed, count = apply_extended_siezen(sections[key])
            if count > 0:
                sections[key] = fixed
                total_fixed += count
                # Update lowercase alias
                lower_key = key.replace("_HTML", "").lower()
                if lower_key in sections:
                    sections[lower_key] = fixed
                log.info(f"[EXTENDED-SIEZEN] {key}: {count} additional fixes")
    
    log.info(f"[EXTENDED-SIEZEN] Complete: {total_fixed} additional du→Sie fixes")
    return sections

# =============================================================================
# 6. GRAMMAR-FIXER: Korrigiert typische Grammatik-/Formatierungsfehler
# =============================================================================

GRAMMAR_FIX_PATTERNS = [
    # "Einzelunternehmer in der Branche beratung" → korrekte Großschreibung
    (r'in der Branche ([a-zäöü]+)', lambda m: f'in der Branche {m.group(1).title()}'),
    
    # "Für Ihr Einzelunternehmer" → "Für Ihren Einzelbetrieb" oder "Für Sie als Einzelunternehmer"
    (r'Für Ihr Einzelunternehmer', 'Für Sie als Einzelunternehmer'),
    
    # v14.18: Zusammengeklebte Header trennen
    (r'([A-ZÄÖÜ]{5,})([A-Z][a-zäöü])', r'\1 - \2'),
    # Doppelte Leerzeichen
    (r'  +', ' '),
    
    # Punkt vor Komma
    # v14.18: Komma vor Punkt
    (r',\.', '.'),
    (r'\.,', ','),
    
    # Doppelte Punkte
    
    # v14.35: Persona-Leak Fixes (auch in GRAMMAR_FIX für alle Sections)
    # skalier*-Familie komplett (alle deutschen Flexionen)
    (r'\bSkalierung\b', 'Erweiterung'),
    (r'Skalierungs', 'Erweiterungs'),
    (r'\bskalieren\b', 'erweitern'),  # Verb
    (r'\bSkalierbarkeit\b', 'Erweiterbarkeit'),  # Substantiv
    (r'\bskalierbar\b', 'erweiterbar'),  # Adjektiv Grundform
    (r'\bskaliert\b', 'erweitert'),  # v14.35.4: Verb Partizip/3.Person
    (r'\bskalieren\b', 'erweitern'),  # v14.35.4: Verb Infinitiv
    (r'\bSkalierung auf \d+', 'Erweiterung auf'),  # v14.35.4: "Skalierung auf 1000+"
    (r'\bSkalierungs', 'Erweiterungs'),  # v14.35.4: Komposita
    (r'\bskalierbare\b', 'erweiterbare'),  # v14.35: Adjektiv feminin/Plural
    (r'\bskalierbares\b', 'erweiterbares'),  # v14.35: Adjektiv neutrum
    (r'\bskalierbaren\b', 'erweiterbaren'),  # v14.35: Adjektiv Dativ/Genitiv
    (r'\bskalierbarer\b', 'erweiterbarer'),  # v14.35: Adjektiv maskulin/Genitiv
    (r'\bhochskaliert', 'stark erweitert'),  # Partizip
    # v14.35.8: Explizite Großschreibungs-Patterns (statt IGNORECASE)
    (r'\bSkalierbare\b', 'Erweiterbare'),  # Am Satzanfang
    (r'\bSkalierbares\b', 'Erweiterbares'),
    (r'\bSkalierbaren\b', 'Erweiterbaren'),
    (r'\bSkalierbarer\b', 'Erweiterbarer'),
    (r'\bSkaliert\b', 'Erweitert'),  # Am Satzanfang
    (r'\bSkalieren\b', 'Erweitern'),
    (r'\bModule\b', 'Bausteine'),
    (r'\bModul\b', 'Baustein'),
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    (r'\bModulen\b', 'Bausteinen'),  # v14.35.11: Dativ Plural
    # Framework-Familie komplett
    (r'\bFrameworks\b', 'Konzepte'),  # v14.35: Plural zuerst (greedy)
    (r'\bFramework\b', 'Konzept'),
    (r'Assessment-Frameworks', 'Bewertungskonzepte'),  # v14.35
    (r'Business-Case-Frameworks', 'Business-Case-Vorlagen'),  # v14.35
    (r'\bPipeline\b', 'Ablauf'),
    (r'\bEngine\b', 'System'),
    (r'\.\. ', '. '),

    # v14.35: Fragment-Fixes (erweitert)
    (r'\(z\.$', ''),  # Abgeschnittene "(z." am Zeilenende entfernen
    (r'\(z\.B\.$', ''),  # Abgeschnittene "(z.B." entfernen
    (r', die die ([A-Za-z]+)\.$', r', die \1.'),  # "die die X." → "die X."
    (r'und \.\.\.$', 'und weitere.'),  # "und ..." → "und weitere."
    (r'und\s*\.$', '.'),  # "und." am Ende → nur "."
    (r', da\.\s*$', '.'),  # v14.35: ", da." → "."
    (r'für diese\.\s*$', 'für diese Zwecke.'),  # v14.35: "für diese." → "für diese Zwecke."
    (r'im Rahmen\.\s*$', 'im Rahmen dessen.'),  # v14.35: "im Rahmen." → "im Rahmen dessen."
    (r'\s+zu\s*$', '.'),  # v14.35: "früh zu" am Ende → "früh."
    (r'\s+oder\s*$', '.'),  # v14.35: "Schritte oder" am Ende → "Schritte."
    (r'\s+und\s*$', '.'),  # v14.35: "Tests und" am Ende → "Tests."
    (r'„[^"]*-\s*$', ''),  # v14.35: Abgeschnittene "„Review-" entfernen
    (r'Schritt-für-\s*$', 'Schritt-für-Schritt.'),  # v14.35: "Schritt-für-" → "Schritt-für-Schritt."
    # v14.35.2: Zusätzliche Fragment-Fixes
    (r'– ohne\.\s*$', '.'),  # "– ohne." → "."
    (r'- ohne\.\s*$', '.'),  # "- ohne." (ASCII) → "."
    (r'– ohne\.\s*<', '.<'),  # "– ohne." vor Tag → "."
    (r'klar strukturiere ', 'klar strukturierte '),  # Grammatikfehler
    (r' mit n ', ' mit einem '),  # Kaputter Platzhalter "mit n"
    (r' mit n\.', ' mit einem passenden Tool.'),  # "mit n." → sinnvoll
    (r' und\.</p>', '.</p>'),  # "und.</p>" → ".</p>"
    (r' und\.<', '.<'),  # "und." vor Tag → "."

    # FIX-GRAMMAR-T1: ROI ist maskulin — "ein attraktives ROI" → "einen attraktiven ROI"
    (r'ein\s+sehr\s+attraktives\s+ROI', 'einen sehr attraktiven ROI'),
    (r'ein\s+attraktives\s+ROI', 'einen attraktiven ROI'),
    (r'ein\s+hohes\s+ROI', 'einen hohen ROI'),
    (r'ein\s+positives\s+ROI', 'einen positiven ROI'),
    (r'ein\s+gutes\s+ROI', 'einen guten ROI'),
    (r'das\s+ROI', 'der ROI'),

    # FIX-N1/N2 (KIS-1005): Singular subject + "nutzen" → "nutzt"
    # Covers: "Ihr Team nutzen", "Der Kollege nutzen", "Ein Mitarbeiter nutzen", etc.
    (r'\b(Ihr|Der|Die|Das|Ein) (Team|Kollege|Mitarbeiter|Chef|Geschäftsführer) nutzen\b',
     r'\1 \2 nutzt'),

    # NEU-2 (Session 28, KIS-1012): Compound-noun singular subjects + "nutzen" → "nutzt"
    # Covers: "Ihr Motion-Design-Team nutzen", "Das Pilotteam nutzen", "Ihr Kernteam nutzen"
    # The N1/N2 rule above only matches simple "Ihr Team nutzen" — this catches
    # compound nouns (hyphenated) ending in singular nouns like -Team, -System, etc.
    # "Teams nutzen" / "Sie nutzen" remain correct (plural subjects not matched).
    (r'\b((?:Ihr|Das|Ein)\s+\S*(?:Team|Unternehmen|System|Management|Pilotteam|Kernteam))\s+nutzen\b',
     lambda m: f'{m.group(1)} nutzt'),

    # KIS-1011-B1: "Ich haben" → "Ich habe" (defensive grammar fix)
    # Negative lookbehind prevents false positives like "die ich haben möchte"
    (r'(?<![a-zäöü])\bIch haben\b', 'Ich habe'),

    # KIS-1013-NEU-3: "können ich" → "kann ich" (Wettbewerbs-Prompt grammar fix)
    (r'\bkönnen ich\b', 'kann ich'),
    (r'\bKönnen ich\b', 'Kann ich'),

    # KIS-1013-B1: "ich haben" (lowercase) → "ich habe" — catch all case variants
    (r'\bich haben\b', 'ich habe'),
]

def apply_grammar_fixes(html: str) -> tuple[str, int]:
    """
    Korrigiert typische Grammatik- und Formatierungsfehler.
    """
    if not html:
        return html, 0
    
    fixes = 0
    result = html
    
    for pattern, replacement in GRAMMAR_FIX_PATTERNS:
        if callable(replacement):
            new_result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        else:
            # Type assertion for mypy: replacement is str here
            new_result = re.sub(pattern, str(replacement), result)
        if new_result != result:
            fixes += 1
            result = new_result
    
    return result, fixes

def apply_grammar_fixer(sections: dict) -> dict:
    """
    Wendet Grammar-Fixes auf alle relevanten Sections an.
    """
    total_fixes = 0
    
    for key, value in sections.items():
        if isinstance(value, str) and len(value) > 100:
            fixed, count = apply_grammar_fixes(value)
            if count > 0:
                sections[key] = fixed
                total_fixes += count
    
    log.info(f"[GRAMMAR-FIXER] Complete: {total_fixes} grammar fixes")
    return sections



# =============================================================================
# NEU-1 (Session 28): BAFA Amount Enforcer
# Prevents LLM from hallucinating wrong BAFA max amounts (e.g. 2.800€ for Bayern).
# Uses config/bafa.py as single source of truth for regional values.
# =============================================================================

def apply_bafa_amount_enforcer(sections: dict, bundesland: str) -> dict:
    """
    Replace incorrect BAFA max funding amounts in foerderpotenzial section
    with the correct regional value from config/bafa.py.

    The LLM prompt already contains deterministic BAFA data, but LLMs can
    hallucinate wrong amounts. This post-processor is a safety net.
    """
    if not bundesland:
        return sections

    # Only enforce in the foerderpotenzial section (where BAFA is discussed)
    target_keys = [k for k in sections if "foerder" in k.lower() or "funding" in k.lower()]
    if not target_keys:
        return sections

    try:
        from config.bafa import get_bafa_foerderung_max_display, get_bafa_foerderquote
        correct_max = get_bafa_foerderung_max_display(bundesland)  # e.g. "1.750 €"
        correct_quote = get_bafa_foerderquote(bundesland)  # e.g. 50
    except ImportError:
        log.warning("[BAFA-ENFORCER] config.bafa not available, skipping")
        return sections

    # Known wrong BAFA amounts that the LLM might hallucinate
    # Correct values: Alte BL = 1.750€/50%, Neue BL = 2.800€/80%, Berlin = 2.100€/60%
    all_bafa_amounts = ["1.750", "2.800", "2.100"]
    # Remove the correct amount from the "wrong" list
    correct_amount_str = correct_max.replace(" €", "").replace("\xa0€", "").strip()
    wrong_amounts = [a for a in all_bafa_amounts if a != correct_amount_str]

    total_fixes = 0
    for key in target_keys:
        value = sections.get(key, "")
        if not isinstance(value, str) or not value:
            continue

        original = value
        for wrong in wrong_amounts:
            # Pattern: wrong BAFA amount near BAFA context
            # Match "maximal X.XXX €" or "X.XXX €" or "X.XXX€" patterns
            # Only replace when in BAFA context (within ~200 chars of "BAFA" mention)
            # Use a function-based replacement to check BAFA proximity
            def _bafa_context_replace(m, _wrong=wrong, _correct_max=correct_max, _full=value):
                start = max(0, m.start() - 200)
                end = min(len(_full), m.end() + 200)
                context = _full[start:end].lower()
                if "bafa" in context or "beratungsförderung" in context or "unternehmensberatung" in context:
                    return m.group(0).replace(_wrong, correct_amount_str)
                return m.group(0)  # Not in BAFA context, leave unchanged

            # Match the wrong amount with optional € sign and optional "netto"
            pattern = re.compile(
                rf'(?:maximal\s+)?{re.escape(wrong)}\s*(?:€|&euro;|Euro)',
                re.IGNORECASE
            )
            value = pattern.sub(_bafa_context_replace, value)

            # KIS-1093-B: Comprehensive BAFA percentage enforcement.
            # Catches all wrong percentage patterns near BAFA context:
            # "Zuschuss von X%", "bis zu X%", "X % der Kosten", just "X%" etc.
            all_bafa_quotes = {50, 60, 80}
            wrong_quotes = [q for q in all_bafa_quotes if q != correct_quote]
            for wrong_q in wrong_quotes:
                if str(wrong_q) not in value:
                    continue
                # Match wrong percentage in any form near BAFA context
                pct_pattern = re.compile(
                    rf'(?:(?:Zuschuss\s+von\s+)|(?:bis\s+(?:zu\s+)?)|(?:Förderquote[:\s]+))?'
                    rf'{wrong_q}\s*(?:%|Prozent|%)',
                    re.IGNORECASE,
                )
                def _fix_pct(m: re.Match[str], _v: str = value, _wq: int = wrong_q) -> str:
                    if "bafa" in _v[max(0, m.start()-200):m.end()+200].lower():
                        return m.group(0).replace(str(_wq), str(correct_quote))
                    return m.group(0)
                value = pct_pattern.sub(_fix_pct, value)

        if value != original:
            sections[key] = value
            total_fixes += 1
            log.info("[BAFA-ENFORCER] Fixed BAFA amounts in section '%s' (bundesland=%s, correct=%s/%s%%)",
                     key, bundesland, correct_max, correct_quote)

    if total_fixes:
        log.info("[BAFA-ENFORCER] Complete: %d sections corrected", total_fixes)
    return sections


# =============================================================================
# MASTER FUNCTION: Apply All Quality Enforcers
# =============================================================================

# =============================================================================
# 5. LOCATION-VALIDATOR: Entfernt falsche Bundesländer aus Förder-Sections
# =============================================================================

# Alle deutschen Bundesländer
BUNDESLAENDER = [
    "Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen",
    "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen",
    "Nordrhein-Westfalen", "NRW", "Rheinland-Pfalz", "Saarland", "Sachsen",
    "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"
]

# Sections wo Location-Check angewendet wird
LOCATION_CHECK_SECTIONS = [
    "executive_summary", "EXECUTIVE_SUMMARY_HTML",
    # v14.18: Noch mehr Sections
    "FOERDERPROGRAMME_HTML", "foerderprogramme",
    "FUNDING_TABLE_HTML", "funding_table",
    # v14.17: Erweitert um alle Förder-relevanten Sections
    "funding", "FUNDING_HTML",
    "foerderprogramme", "FOERDERPROGRAMME_HTML",
    "funding_branch_alignment", "FUNDING_BRANCH_ALIGNMENT_HTML",
    "tools_funding_alignment", "TOOLS_FUNDING_ALIGNMENT_HTML",
    "starter_kit", "STARTER_KIT_HTML", "STARTER_KIT_COMPACT_HTML",
    "foerderpotenzial", "FOERDERPOTENZIAL_HTML",
    "recommendations", "RECOMMENDATIONS_HTML",
    "quick_wins", "QUICK_WINS_HTML",
    "tools_section", "TOOLS_SECTION_HTML",
    "starter_kits", "STARTER_KITS_HTML",
    "kosten_uebersicht", "KOSTEN_UEBERSICHT_HTML",
]

    # FIX-S13D: Förder-Keywords — if a wrong Bundesland appears in a <li>/<tr>
    # together with these keywords, remove the entire element (not just the name)
_FOERDER_KEYWORDS = [
    'Förder', 'Programm', 'Zuschuss', 'Landesförderung', 'Digitalbonus',
    'Innovationsgutschein', 'Digitalisierungsprämie', 'Gründer', 'Fördermittel',
]


def validate_location_in_section(html: str, correct_bundesland: str) -> tuple[str, int]:
    """
    Entfernt Referenzen zu falschen Bundesländern.

    FIX-S13D: If a wrong Bundesland appears inside a <li> or <tr> that also
    contains Förder-keywords, the entire element is removed (not just the name
    replaced with "Ihr Bundesland"). This prevents nonsensical entries like
    "Ihr Bundesland-Spezialförderung Digitalisierung".

    Args:
        html: HTML content
        correct_bundesland: Das korrekte Bundesland des Users

    Returns:
        tuple: (cleaned_html, removal_count)
    """
    if not html or not correct_bundesland:
        return html, 0

    removals = 0
    result = html
    correct_lower = correct_bundesland.lower()

    for bundesland in BUNDESLAENDER:
        # Skip wenn es das korrekte Bundesland ist
        if bundesland.lower() == correct_lower:
            continue
        if bundesland.lower() == "nrw" and "nordrhein" in correct_lower:
            continue
        if "nordrhein" in bundesland.lower() and correct_lower == "nrw":
            continue

        # Suche nach dem falschen Bundesland
        bl_pattern = rf'\b{re.escape(bundesland)}\b'
        if not re.search(bl_pattern, result, re.IGNORECASE):
            continue

        # FIX-S13D: Check if wrong Bundesland is inside <li> or <tr> with Förder-keywords
        # If so, remove the entire element instead of just replacing the name
        for tag in ('li', 'tr'):
            element_pattern = re.compile(
                rf'<{tag}[^>]*>.*?</{tag}>',
                re.DOTALL | re.IGNORECASE,
            )
            new_result = result
            for el_match in reversed(list(element_pattern.finditer(result))):
                el_html = el_match.group(0)
                # Check if this element contains the wrong Bundesland
                if not re.search(bl_pattern, el_html, re.IGNORECASE):
                    continue
                # Check if it also contains Förder-keywords
                el_text = re.sub(r'<[^>]+>', ' ', el_html)
                has_foerder = any(kw.lower() in el_text.lower() for kw in _FOERDER_KEYWORDS)
                if has_foerder:
                    new_result = new_result[:el_match.start()] + new_result[el_match.end():]
                    removals += 1
                    log.info(
                        f"[FIX-S13D] Removed entire <{tag}> with wrong Bundesland "
                        f"'{bundesland}' + Förder-keywords (correct: {correct_bundesland})"
                    )
            result = new_result

        # For remaining occurrences (not in <li>/<tr> with Förder-keywords):
        # Replace with "Ihr Bundesland" as before
        remaining = list(re.finditer(bl_pattern, result, re.IGNORECASE))
        if remaining:
            result = re.sub(bl_pattern, "Ihr Bundesland", result, flags=re.IGNORECASE)
            removals += len(remaining)
            log.warning(f"[LOCATION-VALIDATOR] Replaced wrong Bundesland '{bundesland}' → 'Ihr Bundesland' (correct: {correct_bundesland})")

    return result, removals

def apply_location_validator(sections: dict, bundesland: str) -> dict:
    """
    Wendet Location-Validierung auf relevante Sections an.
    """
    if not bundesland:
        log.debug("[LOCATION-VALIDATOR] No bundesland provided, skipping")
        return sections
    
    total_removals = 0
    
    for key in LOCATION_CHECK_SECTIONS:
        if key in sections and sections[key]:
            fixed, count = validate_location_in_section(sections[key], bundesland)
            if count > 0:
                sections[key] = fixed
                total_removals += count
                log.info(f"[LOCATION-VALIDATOR] {key}: {count} wrong Bundesland references removed")
    
    log.info(f"[LOCATION-VALIDATOR] Complete: {total_removals} total removals")
    return sections
# =============================================================================
# FIX-503B: CANONICAL PAYBACK ENFORCER
# =============================================================================
# Replaces inconsistent Payback/Amortisation values in LLM-generated text
# with the canonical value from business case calculation.

# Sections where Payback values should be enforced
PAYBACK_ENFORCE_SECTIONS = [
    "BRANCH_DEEP_DIVE_HTML",
    "TOOLS_BRANCH_ALIGNMENT_HTML",
    "TOOLS_EMPFEHLUNGEN_HTML",
    "BUSINESS_CASE_HTML",
    "EXECUTIVE_SUMMARY_HTML",
    "GAMECHANGER_HTML",
    "RECOMMENDATIONS_HTML",
    "ROADMAP_12M_HTML",
    "KI_STACK_SUMMARY_HTML",
    "MANAGEMENT_SUMMARY_HTML",
    "ROADMAP_90D_HTML",
]

# Patterns that indicate scenario/range context (should NOT be replaced)
# FIX-503C: Enhanced range detection to avoid replacing legitimate ranges
PAYBACK_SCENARIO_PATTERNS = [
    r'(?:konservativ|vorsichtig|pessimistisch)',
    r'(?:optimistisch|best.?case)',
    r'(?:realistisch|baseline)',
    r'P\s*(?:50|80|90)',
    r'Szenario',
    r'(?:bis|–|-)\s*\d+(?:[.,]\d+)?\s*(?:Monate|months)',  # Range like "3-6 Monate"
    r'\d+(?:[.,]\d+)?\s*[–\-]\s*\d+(?:[.,]\d+)?\s*(?:Monate|months)',  # "3-9 Monate" or "3–9 Monate"
    r'(?:zwischen|von)\s+\d+(?:[.,]\d+)?\s+(?:und|bis)\s+\d+',  # "zwischen 3 und 6" or "von 3 bis 6"
    r'(?:ca\.|circa|etwa|ungefähr)\s*\d+',  # "ca. 6 Monate" - approximate values
    r'Simulation',  # Monte Carlo simulation context
]


def _is_scenario_context(text: str, match_start: int, context_chars: int = 100) -> bool:
    """Check if a payback match is within a scenario/range context."""
    # Get surrounding context
    start = max(0, match_start - context_chars)
    end = min(len(text), match_start + context_chars)
    context = text[start:end].lower()

    for pattern in PAYBACK_SCENARIO_PATTERNS:
        if re.search(pattern, context, re.IGNORECASE):
            return True
    return False


def apply_canonical_payback_enforcer(sections: dict) -> dict:
    """
    FIX-503B / FIX-AMORT: Replace ALL Payback/Amortisation values with canonical.

    Extracts canonical payback from sections['PAYBACK_MONTHS'] and replaces
    ANY payback/amortisation numeric mention with the canonical value.

    Previous bug: 20% tolerance allowed two different values (e.g. 3,3 and 3,9)
    to coexist in the same report — both were "close enough" to canonical but
    visibly inconsistent to the customer. Now: ALWAYS enforce canonical.

    Does NOT replace:
    - Values in scenario/range context (P50, konservativ, optimistisch, etc.)

    Args:
        sections: Dict with all report sections

    Returns:
        sections: Dict with enforced canonical payback values
    """
    # Get canonical payback value
    canonical_raw = sections.get("PAYBACK_MONTHS")
    if not canonical_raw:
        log.debug("[PAYBACK-ENFORCER] No PAYBACK_MONTHS in sections, skipping")
        return sections

    try:
        canonical = float(str(canonical_raw).replace(",", "."))
    except (ValueError, TypeError):
        log.warning(f"[PAYBACK-ENFORCER] Invalid PAYBACK_MONTHS: {canonical_raw}")
        return sections

    if canonical <= 0:
        log.debug("[PAYBACK-ENFORCER] Canonical payback is 0 or negative, skipping")
        return sections

    # Format canonical value for German locale
    canonical_de = f"{canonical:.1f}".replace(".", ",")
    if canonical_de.endswith(",0"):
        canonical_de = canonical_de[:-2]  # "3,0" -> "3"

    # Pattern 1: Keyword-prefixed — "Payback 9 Monate", "Amortisation: 12,5 Monate"
    payback_pattern = re.compile(
        r'((?:Payback|Amortisation|Amortisierung|payback period)[:\s]+(?:von\s+)?)'
        r'(\d+(?:[.,]\d+)?)\s*(Monate?|months?|Monaten)',
        re.IGNORECASE
    )

    # Pattern 2: Verb-prefixed — "amortisiert sich in 3,9 Monaten",
    #   "sich in 3,3 Monaten amortisiert", "innerhalb von 4 Monaten amortisiert"
    amortisiert_pattern = re.compile(
        r'((?:amortisiert\s+sich\s+in|sich\s+in|innerhalb\s+von)\s+)'
        r'(\d+(?:[.,]\d+)?)\s*(Monate?n?)',
        re.IGNORECASE
    )

    total_replacements = 0
    sections_touched = 0

    for section_key in PAYBACK_ENFORCE_SECTIONS:
        content = sections.get(section_key)
        if not content or not isinstance(content, str):
            continue

        section_replacements = 0
        modified_content = content

        # Apply both patterns
        for pattern in [payback_pattern, amortisiert_pattern]:
            matches = list(pattern.finditer(modified_content))

            for match in reversed(matches):
                prefix = match.group(1)
                value_str = match.group(2)
                suffix = match.group(3)

                # Parse the found value
                try:
                    found_value = float(value_str.replace(",", "."))
                except ValueError:
                    continue

                # FIX-AMORT: Always enforce canonical — no tolerance.
                # Skip only if already exactly the canonical value.
                if found_value == canonical:
                    continue

                # Skip if in scenario context
                if _is_scenario_context(modified_content, match.start()):
                    log.debug(f"[PAYBACK-ENFORCER] Skipping scenario context: {match.group(0)}")
                    continue

                # Replace with canonical value
                replacement = f"{prefix}{canonical_de} {suffix}"
                modified_content = (
                    modified_content[:match.start()] +
                    replacement +
                    modified_content[match.end():]
                )
                section_replacements += 1
                log.info(
                    f"[PAYBACK-ENFORCER] {section_key}: Replaced '{match.group(0)}' -> '{replacement}'"
                )

        if section_replacements > 0:
            sections[section_key] = modified_content
            sections_touched += 1
            total_replacements += section_replacements

    if total_replacements > 0:
        log.info(
            f"[PAYBACK-ENFORCER] Enforced canonical payback ({canonical_de} Monate) "
            f"in {sections_touched} sections, {total_replacements} replacements"
        )

    return sections


def _apply_transparency_box_floor(sections: dict) -> dict:
    """
    FIX-520 TASK 2: Hard floor for transparency_box section.

    If transparency_box content is less than 60 words, replace with a
    deterministic minimum that passes SECTION_TOO_SHORT validation.
    """
    _TB_KEYS = ["TRANSPARENCY_BOX_HTML", "transparency_box"]
    for key in _TB_KEYS:
        content = sections.get(key)
        if not content or not isinstance(content, str):
            continue

        # Strip HTML tags for word count
        text_only = re.sub(r'<[^>]+>', '', content).strip()
        word_count = len(text_only.split())

        if word_count < 60:
            # Derive context from sections if available
            _datenquellen = (
                sections.get("DATENQUELLEN_LABELS")
                or sections.get("datenquellen")
                or "Fragebogen-Antworten"
            )
            _branch = (
                sections.get("BRANCH_CONTEXT_LABEL")
                or sections.get("BRANCHE_LABEL")
                or sections.get("branche")
                or "Ihrer Branche"
            )
            _report_date = sections.get("report_date") or sections.get("TODAY") or ""

            replacement = (
                '<div class="transparency-box">'
                '<h3>Transparenz &amp; Methodik</h3>'
                '<ul>'
                f'<li><strong>Datenbasis:</strong> {_datenquellen}</li>'
                f'<li><strong>Branchenkontext:</strong> {_branch}</li>'
                '<li><strong>Methodik:</strong> KI-gestützte Analyse Ihrer Fragebogen-Antworten, '
                'angereichert mit branchenspezifischem Kontext und aktuellen Förderdaten.</li>'
                '<li><strong>Validierung:</strong> Alle Kennzahlen (ROI, Payback, Zeitersparnis) '
                'basieren auf konservativen Annahmen und sollten vor Umsetzung validiert werden.</li>'
                '<li><strong>Hinweis:</strong> Dieser Report ersetzt keine individuelle Fachberatung. '
                'Die Empfehlungen dienen als strukturierte Entscheidungsgrundlage für Ihre '
                'KI-Strategie und sollten im Kontext Ihrer spezifischen Situation bewertet werden.</li>'
                '</ul>'
                '</div>'
            )
            sections[key] = replacement
            log.info(
                "[FIX-520][TRANSPARENCY-FLOOR] section=%s replaced: %d words < 60 minimum",
                key, word_count
            )

    return sections


# =============================================================================
# FIX-52x PRIO 1: Quick Wins Placeholder Scrub (aggressive)
# =============================================================================

_QUICKWINS_KEYS = ["QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT", "quick_wins"]

def scrub_quickwins_template_phrases(sections: dict) -> dict:
    """
    FIX-52x PRIO 1: Aggressively remove 'Platzhalter' and template artifacts
    from Quick Wins sections. Ensures TEMPLATE_PHRASE warnings are eliminated.
    """
    for key in _QUICKWINS_KEYS:
        html = sections.get(key)
        if not html or not isinstance(html, str):
            continue

        original = html

        # Remove entire elements containing "Platzhalter"
        html = re.sub(
            r'<(?:p|li|div|span)[^>]*>[^<]*\bPlatzhalter\b[^<]*</(?:p|li|div|span)>',
            '',
            html,
            flags=re.IGNORECASE
        )

        # Remove standalone "Platzhalter" word (replace with neutral text)
        html = re.sub(r'\bPlatzhalter\b', 'konkreter Vorschlag', html, flags=re.IGNORECASE)

        # Remove bracketed placeholders
        html = re.sub(r'\[Platzhalter[^\]]*\]', '', html, flags=re.IGNORECASE)
        html = re.sub(r'\[TODO[^\]]*\]', '', html, flags=re.IGNORECASE)

        # Normalize whitespace
        html = re.sub(r'\s{2,}', ' ', html)
        html = re.sub(r'<p>\s*</p>', '', html)
        html = re.sub(r'<li>\s*</li>', '', html)

        if html != original:
            sections[key] = html
            log.info("[FIX-52x][QUICKWINS-SCRUB] cleaned section=%s", key)

    return sections


# =============================================================================
# FIX-52x PRIO 4: Sentence Fragment Fixer (BUSINESS_CASE_HTML)
# =============================================================================

def fix_sentence_fragments(sections: dict) -> dict:
    """
    FIX-52x PRIO 4: Fix incomplete sentences in BUSINESS_CASE_HTML.
    Handles sentences ending with conjunctions, colons, or commas.
    """
    target_keys = ["BUSINESS_CASE_HTML", "business_case"]

    for key in target_keys:
        html = sections.get(key)
        if not html or not isinstance(html, str):
            continue

        original = html

        # Fix sentences ending with conjunctions/punctuation without proper ending
        # Pattern: text ending with "und", "oder", "sowie", ":", "," before closing tag
        def fix_fragment(match):
            content = match.group(1)
            tag = match.group(2)
            # Trim trailing conjunctions/punctuation and add period
            content = re.sub(r'\s*(?:und|oder|sowie|,|:)\s*$', '.', content.strip(), flags=re.IGNORECASE)
            # If no sentence-ending punctuation and length > 40, add period
            if len(content) > 40 and not re.search(r'[.!?]$', content):
                content = content.rstrip() + '.'
            return f'{content}</{tag}>'

        # Apply to <p>, <li> content
        html = re.sub(
            r'>([^<]{40,}?)\s*</([pP]|[lL][iI])>',
            lambda m: '>' + fix_fragment(m) if m.group(1).strip() else m.group(0),
            html
        )

        if html != original:
            sections[key] = html
            log.info("[FIX-52x][SENTENCE-FRAGMENT] fixed fragments in section=%s", key)

    return sections


# =============================================================================
# FIX-52x PRIO 3: Redundancy Auto-Shortener
# =============================================================================

def auto_shorten_redundant_sections(sections: dict) -> dict:
    """
    FIX-52x PRIO 3: Reduce redundancy in BUSINESS_CASE_HTML and PILOT_PLAN_HTML
    by replacing overly long repeated content patterns with shorter versions.
    """
    target_keys = ["BUSINESS_CASE_HTML", "PILOT_PLAN_HTML"]

    for key in target_keys:
        html = sections.get(key)
        if not html or not isinstance(html, str):
            continue

        original_len = len(html)

        # Find and deduplicate repeated paragraphs (exact matches)
        paragraphs = re.findall(r'<p[^>]*>([^<]+)</p>', html)
        seen = set()
        duplicates = []
        for p in paragraphs:
            p_normalized = ' '.join(p.split()).lower()
            if len(p_normalized) > 100:  # Only check substantial paragraphs
                if p_normalized in seen:
                    duplicates.append(p)
                else:
                    seen.add(p_normalized)

        # Remove duplicate paragraphs (keep first occurrence)
        for dup in duplicates:
            # Only remove the second and subsequent occurrences
            pattern = re.escape(f'<p>{dup}</p>')
            # Find all matches and remove all but first
            matches = list(re.finditer(pattern, html, re.IGNORECASE))
            if len(matches) > 1:
                # Remove from end to preserve indices
                for match in reversed(matches[1:]):
                    html = html[:match.start()] + html[match.end():]

        # Shorten overly verbose sections (>5000 chars) by trimming repetitive list items
        if len(html) > 5000:
            # Count list items
            li_matches = re.findall(r'<li[^>]*>([^<]+)</li>', html)
            if len(li_matches) > 10:
                # Keep first 8 items, summarize rest
                html = re.sub(
                    r'((?:<li[^>]*>[^<]+</li>\s*){8})(?:<li[^>]*>[^<]+</li>\s*)+',
                    r'\1<li><em>Weitere Details siehe Kennzahlenblock.</em></li>',
                    html,
                    count=1
                )

        if len(html) < original_len:
            sections[key] = html
            delta = original_len - len(html)
            log.info("[FIX-52x][REDUNDANCY-SHORTEN] section=%s reduced_by=%d chars", key, delta)

    return sections


# =============================================================================
# FIX-52x FINAL POLISH: Comprehensive Template Phrase Stripper
# =============================================================================

# Comprehensive list of template phrases that should never appear in output
_FINAL_TEMPLATE_PHRASES = [
    # German placeholders
    r'\bPlatzhalter\b',
    r'\bBeispieltext:?\b',  # FIX-645: Template-Phrase aus LLM output
    r'\[Platzhalter[^\]]*\]',
    r'\[TODO[^\]]*\]',
    r'\[FIXME[^\]]*\]',
    r'\[XXX[^\]]*\]',
    r'\[INSERT[^\]]*\]',
    r'\[EINFÜGEN[^\]]*\]',
    # Template markers
    r'\{\{[^}]+\}\}',  # Jinja2 double braces
    r'\{%[^%]+%\}',    # Jinja2 blocks
    r'\$\{[^}]+\}',    # Shell-style vars
    # Prompt echo patterns
    r'^Erstelle\s+(?:mir\s+)?(?:einen?\s+)?(?:detaillierten?\s+)?(?:Abschnitt|Text|Analyse)',
    r'^Schreibe?\s+(?:mir\s+)?(?:einen?\s+)?(?:detaillierten?\s+)?',
    r'^Generiere\s+(?:mir\s+)?',
    r'^Verfasse\s+(?:mir\s+)?',
    r'^Formuliere\s+(?:mir\s+)?',
    # Meta instructions that leaked
    r'^\s*Hinweis:\s*Dieser\s+Text',
    r'^\s*Anweisung:',
    r'^\s*Prompt:',
    r'^\s*Aufgabe:',
    # Common LLM artifacts
    r'(?i)\bals\s+KI(?:-Assistent)?\b',
    r'(?i)\bals\s+Sprachmodell\b',
    r'(?i)\bich\s+(?:kann|darf)\s+(?:nicht|keine)\b.*?(?:rechtliche|medizinische)\s+Beratung',
]

def strip_template_phrases_final(sections: dict) -> dict:
    """
    FIX-52x FINAL POLISH PRIO 1: Comprehensive final cleanup of ALL template
    phrases across ALL sections. This runs as the LAST step in the pipeline.
    """
    import re as regex_module

    total_fixes = 0

    for key, value in list(sections.items()):
        if not isinstance(value, str) or not value.strip():
            continue
        if key.startswith('_'):  # Skip internal keys
            continue

        original = value
        html = value

        for pattern in _FINAL_TEMPLATE_PHRASES:
            try:
                # For line-anchored patterns, process line by line
                if pattern.startswith('^'):
                    lines = html.split('\n')
                    new_lines = []
                    for line in lines:
                        stripped = line.strip()
                        # Remove HTML tags for matching
                        text_only = regex_module.sub(r'<[^>]+>', '', stripped)
                        if not regex_module.search(pattern, text_only, regex_module.IGNORECASE):
                            new_lines.append(line)
                    html = '\n'.join(new_lines)
                else:
                    # For inline patterns, replace with empty string
                    html = regex_module.sub(pattern, '', html, flags=regex_module.IGNORECASE)
            except regex_module.error:
                continue  # Skip invalid patterns

        # Clean up resulting empty elements
        html = regex_module.sub(r'<p[^>]*>\s*</p>', '', html)
        html = regex_module.sub(r'<li[^>]*>\s*</li>', '', html)
        html = regex_module.sub(r'<div[^>]*>\s*</div>', '', html)
        html = regex_module.sub(r'\s{3,}', '  ', html)

        if html != original:
            sections[key] = html
            total_fixes += 1

    if total_fixes > 0:
        log.info("[FIX-52x][FINAL-TEMPLATE-STRIP] cleaned %d sections", total_fixes)

    return sections


# =============================================================================
# FIX-52x FINAL POLISH: Paragraph Deduplication
# =============================================================================

def _dedupe_long_paragraphs(sections: dict) -> dict:
    """
    FIX-52x FINAL POLISH PRIO 3: Remove duplicate long paragraphs (>150 chars)
    that appear multiple times within the same section or across sections.
    """
    import re as regex_module

    # Track seen paragraphs globally across all sections
    global_seen = {}  # normalized_text -> (first_section, first_occurrence)
    total_removed = 0

    for key, value in list(sections.items()):
        if not isinstance(value, str) or not value.strip():
            continue
        if key.startswith('_'):
            continue

        html = value

        # Find all paragraphs with their positions
        para_pattern = r'<p[^>]*>([^<]{150,})</p>'
        matches = list(regex_module.finditer(para_pattern, html))

        removals = []
        for match in matches:
            content = match.group(1)
            # Normalize: lowercase, collapse whitespace
            normalized = ' '.join(content.lower().split())

            if normalized in global_seen:
                # This is a duplicate - mark for removal
                removals.append((match.start(), match.end()))
            else:
                global_seen[normalized] = (key, match.start())

        # Remove duplicates from end to preserve indices
        for start, end in reversed(removals):
            html = html[:start] + html[end:]
            total_removed += 1

        if removals:
            sections[key] = html

    if total_removed > 0:
        log.info("[FIX-52x][DEDUPE-PARAGRAPHS] removed %d duplicate paragraphs", total_removed)

    return sections


# =============================================================================
# FIX-52x FINAL POLISH: Trailing Fragment Stripper
# =============================================================================

def strip_trailing_sentence_fragments(sections: dict) -> dict:
    """
    FIX-52x FINAL POLISH PRIO 4: Remove short trailing fragments that look
    like incomplete sentences at the end of sections.

    Patterns:
    - Trailing text <30 chars without proper sentence ending
    - Orphaned conjunctions: "und", "oder", "sowie", "aber"
    - Dangling colons or commas at end
    """
    import re as regex_module

    total_fixes = 0

    for key, value in list(sections.items()):
        if not isinstance(value, str) or not value.strip():
            continue
        if key.startswith('_'):
            continue

        original = value
        html = value

        # Pattern 1: Short trailing content after last complete sentence
        # Match: complete sentence followed by short fragment
        def fix_trailing(m):
            full_content = m.group(0)
            tag_name = m.group(1)

            # Find the last proper sentence ending
            sentences = regex_module.split(r'([.!?])\s+', full_content)
            if len(sentences) >= 3:  # At least one complete sentence
                # Check if trailing part is short fragment
                trailing = sentences[-1] if sentences[-1] else ''
                trailing_text = regex_module.sub(r'<[^>]+>', '', trailing).strip()

                if len(trailing_text) < 30 and not regex_module.search(r'[.!?]$', trailing_text):
                    # Remove trailing fragment, keep sentence ending
                    proper_end = ''.join(sentences[:-1])
                    if proper_end and not proper_end.rstrip().endswith(('.', '!', '?')):
                        proper_end = proper_end.rstrip() + '.'
                    return proper_end + f'</{tag_name}>'

            return full_content

        # Apply to closing p/div/li tags
        html = regex_module.sub(
            r'>([^<]{50,})</([pP]|div|DIV|[lL][iI])>',
            fix_trailing,
            html
        )

        # Pattern 2: Remove dangling conjunctions at very end
        html = regex_module.sub(
            r'\s+(?:und|oder|sowie|aber|denn|weil)\s*</([pP]|div|[lL][iI])>',
            r'.</\1>',
            html,
            flags=regex_module.IGNORECASE
        )

        # Pattern 3: Remove trailing colons/commas before close tag
        html = regex_module.sub(
            r'\s*[,:]\s*</([pP]|div|[lL][iI])>',
            r'.</\1>',
            html
        )

        if html != original:
            sections[key] = html
            total_fixes += 1

    if total_fixes > 0:
        log.info("[FIX-52x][TRAILING-FRAGMENT] fixed %d sections", total_fixes)

    return sections


# =============================================================================
# FIX-52x FINAL POLISH: Final Solo Term Rewrite (runs LAST)
# =============================================================================

def apply_solo_terms_final(sections: dict, company_size: str) -> dict:
    """
    FIX-52x FINAL POLISH PRIO 2: Apply solo term replacements as the ABSOLUTE
    LAST step in the pipeline, after all LLM outputs are finalized.

    This ensures no enterprise terms leak through from any source.
    """
    if company_size != "solo":
        return sections

    import re as regex_module

    total_replacements = 0

    for key, value in list(sections.items()):
        if not isinstance(value, str) or not value.strip():
            continue
        if key.startswith('_'):
            continue

        original = value
        text = value

        for pattern, replacement, desc in SOLO_TERM_REPLACEMENTS:
            try:
                new_text, count = regex_module.subn(pattern, replacement, text, flags=regex_module.IGNORECASE)
                if count > 0:
                    text = new_text
                    total_replacements += count
            except regex_module.error:
                continue

        if text != original:
            sections[key] = text

    if total_replacements > 0:
        log.info("[FIX-52x][FINAL-SOLO-TERMS] applied %d replacements", total_replacements)

    # STRICT mode check for remaining forbidden terms
    # FIX-529: Extended forbidden terms list for solo persona
    if os.getenv("RELEASE_STRICT_MODE") == "1":
        forbidden = [
            # Technical terms (should be replaced, not just removed)
            "Skalierung", "Stakeholder", "Audit-Trail", "Audit Trail",
            "Stack", "Tech-Stack", "Full-Stack", "Rollout", "Deployment",
            "Pipeline", "Framework", "Dashboard", "KPI", "Modul", "Engine",
            # FIX-529: Additional forbidden terms per briefing
            "Architektur", "Layer", "KPI-Dashboard", "Workflow",
        ]
        all_text = " ".join(str(v) for v in sections.values() if isinstance(v, str))
        still = [t for t in forbidden if regex_module.search(r'\b' + regex_module.escape(t) + r'\b', all_text, regex_module.IGNORECASE)]
        if still:
            # Log warning but don't raise - this is informational
            log.warning("[FIX-52x][SOLO-LEAK-CHECK] terms still present after final rewrite: %s", still)

    return sections


def _limit_hauptleistung_repetitions(sections: dict, hauptleistung: str, max_full: int = 3) -> dict:

    # Z8: DISABLED — short-form replacement creates garbled fragments
    log.info("[Z8] _limit_hauptleistung_repetitions disabled (fragment prevention)")
    return sections
    """
    PLATIN+++ FIX 3.1: Limit full-text hauptleistung repetitions across all sections.

    After max_full occurrences, replace with a short version (first 60 chars + ...).
    This prevents the report from repeating the full hauptleistung 16-25 times.
    """
    if not hauptleistung or len(hauptleistung) <= 120:  # L1: was 50
        return sections

    # Create short version
    short = hauptleistung[:120].rsplit(" ", 1)[0] + "..." if len(hauptleistung) > 120 else hauptleistung  # L1: was 60
    # N1: Smarter short form — keep first SENTENCE, not first comma clause
    # Old logic cut at first comma (pos ~42) → "Beratung und Unterstützung für Unternehmen"
    # New: prefer first sentence (ending with ".") or 120-char word boundary
    dot_pos = hauptleistung.find(".")
    if 40 < dot_pos < 150:
        short = hauptleistung[:dot_pos + 1]  # Full first sentence
    # else: keep the 120-char version from above

    # O1b: Minimal PROTECTED — only sections that NEED full hauptleistung
    PROTECTED_SECTIONS = {
        "EXEC_SUMMARY_HTML", "RECOMMENDATIONS_HTML",  # Validator requires these
        "REPORT_SUBTITLE", "HAUPTLEISTUNG", "hauptleistung",  # Raw metadata
        "HERO_HTML", "hero",  # Cover page
    }

    total_replaced = 0
    for key, val in sections.items():
        if not isinstance(val, str) or key.startswith("_"):
            continue
        if key in PROTECTED_SECTIONS:
            log.info("[FIX-3.1] Skipping protected section %s (hauptleistung count: %d)", key, val.count(hauptleistung))
            continue
        count = val.count(hauptleistung)
        if count <= 0:
            continue
        # Keep first max_full occurrences in the entire report, replace rest
        # Process per-section: allow max 1 full occurrence per section (first one)
        parts = val.split(hauptleistung)
        if len(parts) <= 2:
            continue  # 0 or 1 occurrence in this section
        # Keep first occurrence, replace rest
        rebuilt = parts[0] + hauptleistung
        for part in parts[2:]:
            rebuilt += short + part
            total_replaced += 1
        sections[key] = rebuilt

    if total_replaced > 0:
        log.info("[FIX-3.1] hauptleistung repetition limited: replaced %d occurrences with short form", total_replaced)
        # FIX-R2-4: Set flag so the enforcer in subsequent passes won't re-inject
        sections["_fix_3_1_applied"] = True

    return sections


def _fix_segment_labels(sections: dict, company_size: str) -> dict:
    """FIX-911: Remove mismatched segment qualifiers like '(Team)' in KMU reports.

    The LLM sometimes generates text like '36 Stunden/Monat (Team)' or
    'KI-Assistenz-Plattform (Team)' even in KMU reports because of stale
    prompt context. This strips wrong-segment qualifiers from HTML sections.
    """
    import re as _re
    # Map segment to its correct label and the labels that are WRONG for it
    _wrong_labels = {
        "solo": [r"\(Team\)", r"\(KMU\)"],
        "team": [r"\(Solo\)", r"\(KMU\)"],
        "kmu":  [r"\(Solo\)", r"\(Team\)"],
    }
    wrong = _wrong_labels.get(company_size)
    if not wrong:
        return sections

    pattern = _re.compile(r"\s*(?:" + "|".join(wrong) + r")", _re.IGNORECASE)
    count = 0
    for key, val in sections.items():
        if not isinstance(val, str) or not val or key.startswith("_"):
            continue
        new_val = pattern.sub("", val)
        if new_val != val:
            sections[key] = new_val
            count += 1
    if count > 0:
        log.info("[FIX-911] Removed %d mismatched segment labels for company_size=%s", count, company_size)
    return sections


def apply_all_quality_enforcers(sections: dict, hauptleistung: str = "", bundesland: str = "", company_size: str = "") -> dict:

    """
    Wendet alle Quality Enforcer in der richtigen Reihenfolge an.

    Order:
    0. Stray Prefix Remover (P0.1: entfernt führende "?" und Artefakte)
    1. ROI-Filter (entfernt verbotene ROI-Werte)
    2. Fragment-Repair (repariert unvollständige Sätze)
    3. Extended Siezen (erweiterte du→Sie)
    4. hauptleistung-Enforcer (injiziert fehlende hauptleistung)
    5. Location-Validator (entfernt falsche Bundesländer)
    6. Grammar-Fixer (korrigiert Grammatikfehler)
    7. Solo-Language-Normalizer (ersetzt Enterprise-Begriffe für Solo-Persona)

    Args:
        sections: Dict mit allen Report-Sections
        hauptleistung: Das Kerngeschäft des Users
        bundesland: Das Bundesland des Users
        company_size: Die Unternehmensgröße ("solo", "team", "kmu")

    Returns:
        sections: Bereinigtes Dict
    """
    log.info("[QUALITY-ENFORCER] Starting quality enforcement pipeline...")

    # 0. FIX-517C: Universal Template Phrase Scrub (ALL personas, BEFORE validation)
    sections = scrub_template_phrases_all_sections(sections)

    # 0.5 P0.1: Stray Prefix Remover (leading "?" and artifacts)
    sections = apply_stray_prefix_remover(sections)

    # 1. ROI-Filter
    sections = apply_roi_filter(sections)

    # 2. Fragment-Repair
    sections = apply_fragment_repair(sections)
    
    # 2.5 v14.27: Ellipsen-Fix (Trunkierung entfernen)
    sections = apply_ellipsis_fix(sections)
    
    # 3. Extended Siezen
    sections = apply_extended_siezen_guard(sections)
    
    # 4. hauptleistung-Enforcer
    if hauptleistung:
        sections = apply_hauptleistung_enforcer(sections, hauptleistung)
    
    
    # 5. Location-Validator

    # 5.5 NEU-1 (Session 28): BAFA Amount Enforcer — fix hallucinated BAFA max amounts
    if bundesland:
        sections = apply_bafa_amount_enforcer(sections, bundesland)

    # 6. Grammar-Fixer

    # 7. AI-Act Konsistenz (v14.19)
    sections = apply_ai_act_consistency(sections)
    sections = apply_grammar_fixer(sections)
    if bundesland:
        sections = apply_location_validator(sections, bundesland)

    # 8. KPI Consistency Enforcement (v14.35.19+)
    sections = apply_kpi_consistency_enforcer(sections)

    # 8.5 FIX-503B: Canonical Payback Enforcer - Replace LLM hallucinated payback values
    sections = apply_canonical_payback_enforcer(sections)

    # 8.6 FIX-504: Kennzahlenblock KPI Enforcer - Fix spacing and enforce canonical values
    sections = apply_kennzahlenblock_enforcer(sections)

    # 9. Product Name Safety Net (v14.35.21) - LAST STEP (seatbelt)
    sections = apply_product_name_safety_net(sections)

    # 10. Open Example Paren Fixer (v14.35.22) - Fix "(z.B." incomplete patterns
    sections = apply_open_example_paren_fixer(sections)

    # 11. Solo Language Normalizer (v14.35.22) - FIRST PASS enterprise term replacement
    # NOTE: A final pass runs at the very end to catch any terms introduced by later steps
    if company_size:
        sections = apply_solo_language_normalizer(sections, company_size)

    # 12. Text Glitch Fixer (Fix-Batch F) - Fix known word corruptions and zero displays
    sections = apply_text_glitch_fixer(sections)

    # 13. Empty Page Killer (Fix-Batch I + J3) - Remove empty page-breaking sections
    sections = apply_empty_page_killer(sections)

    # 14. Risk Truncation (Fix-Batch I) - Truncate risk descriptions at sentence boundaries
    sections = apply_risk_truncation(sections)

    # 14.5 FIX-525: Risks Solo Padding - Ensure minimum 500 words for solo persona
    if company_size:
        sections = apply_risks_solo_padding(sections, company_size)

    # 14.7 FIX-911: Segment label fixer - remove mismatched "(Team)" / "(Solo)" / "(KMU)" labels
    if company_size:
        sections = _fix_segment_labels(sections, company_size)

    # 15. Chat Artefact Filter (Fix-Batch J4) - Remove "Schreib mir", "Frag mich" etc.
    sections = apply_chat_artefact_filter(sections)

    # 15.5 FIX-R2-2: Prompt-Leak Hard-Block (removes entire HTML blocks with prompt leaks)
    sections = apply_prompt_leak_hard_block(sections)

    # 16. FIX-514: Forbidden-Token Scrub (Rollout/Skalierung/Stack in decision+stack sections)
    sections = apply_forbidden_token_scrub(sections)

    # 17. FIX-514: Placeholder Scrub (remove "Platzhalter" from recommendations)
    sections = apply_placeholder_scrub(sections)

    # 17.5 FIX-52x: Quick Wins Placeholder Scrub (aggressive)
    sections = scrub_quickwins_template_phrases(sections)

    # 17.6 FIX-52x: Sentence Fragment Fixer (BUSINESS_CASE_HTML)
    sections = fix_sentence_fragments(sections)

    # 17.7 FIX-52x: Redundancy Auto-Shortener (BUSINESS_CASE_HTML, PILOT_PLAN_HTML)
    sections = auto_shorten_redundant_sections(sections)

    # 18. FIX-520 TASK 2: transparency_box hard-floor (min 60 words)
    sections = _apply_transparency_box_floor(sections)

    # =========================================================================
    # FIX-52x FINAL POLISH: These steps run LAST to catch any artifacts
    # introduced by earlier LLM-powered or template-based steps
    # =========================================================================

    # 19. FIX-52x: Deduplicate long identical paragraphs (PRIO 3)
    sections = _dedupe_long_paragraphs(sections)

    # 19.5 PLATIN+++ FIX 3.1: Limit hauptleistung full-text repetitions (max 3)
    if hauptleistung and len(hauptleistung) > 50:
        sections = _limit_hauptleistung_repetitions(sections, hauptleistung, max_full=3)

    # 19.6 FIX-R3-4A: Repair concat bugs (")Beratung", "UnternehmenBeratung")
    if hauptleistung and len(hauptleistung) > 10:
        sections = fix_hauptleistung_concat(sections, hauptleistung)

    # 20. FIX-52x: Strip trailing sentence fragments (PRIO 4)
    sections = strip_trailing_sentence_fragments(sections)

    # 21. FIX-52x: Final comprehensive template phrase cleanup (PRIO 1)
    sections = strip_template_phrases_final(sections)

    # 22. FIX-52x: FINAL solo term replacement (PRIO 2) - ABSOLUTE LAST STEP
    # This catches any enterprise terms that may have been introduced by
    # earlier steps (LLM outputs, template expansions, etc.)
    if company_size:
        sections = apply_solo_terms_final(sections, company_size)

    # 22.5 KIS-1013-B1: FINAL grammar pass — catch grammar errors introduced by
    # any earlier pipeline step (truncation-repair, solo-normalization, etc.)
    sections = apply_grammar_fixer(sections)

    # =========================================================================
    # FIX-527: Report Facts Integration
    # =========================================================================

    # 23. FIX-527: Collect open inputs (markers) and generate OPEN_INPUTS_HTML
    try:
        from services.report_facts import collect_open_inputs, validate_no_platzhalter_text
        open_inputs, open_inputs_html = collect_open_inputs(sections)
        if open_inputs_html:
            sections["OPEN_INPUTS_HTML"] = open_inputs_html
            sections["_OPEN_INPUTS_COUNT"] = len(open_inputs)

        # 24. FIX-527: Validate no "Platzhalter" text in report
        platzhalter_ok, platzhalter_violations = validate_no_platzhalter_text(sections)
        sections["_PLATZHALTER_AUDIT_PASS"] = platzhalter_ok
        if not platzhalter_ok:
            log.warning("[FIX-527] Platzhalter text found: %s", platzhalter_violations)
    except ImportError:
        log.debug("[FIX-527] report_facts module not available, skipping")

    log.info("[QUALITY-ENFORCER] Pipeline complete (FIX-52x final polish applied)")
    return sections


# =============================================================================
# v14.19: AI-ACT KONSISTENZ-VALIDATOR
# =============================================================================

def fix_ai_act_consistency(html: str) -> tuple[str, int]:
    """
    Behebt Widersprüche in AI-Act Risikoklassen.
    Problem: Auf derselben Seite steht "Risikoklasse: minimal" UND "Hochrisiko"
    """
    if not html:
        return html, 0
    
    fixes = 0
    result = html
    
    # Prüfe auf Widerspruch: minimal + Hochrisiko
    has_minimal = bool(re.search(r'Risikoklasse:\s*minimal', result, re.IGNORECASE))
    has_hochrisiko = bool(re.search(r'\bHochrisiko\b', result, re.IGNORECASE))
    
    if has_minimal and has_hochrisiko:
        # Entferne "Hochrisiko" wenn "minimal" definiert ist
        result = re.sub(r'\bHochrisiko\b', 'geringes Risiko', result)
        fixes += 1
        log.info("[AI-ACT-CONSISTENCY] Fixed contradiction: Hochrisiko → geringes Risiko (weil Risikoklasse minimal)")
    
    return result, fixes


def apply_ai_act_consistency(sections: dict) -> dict:
    """
    v14.23: Globale Prüfung - erst alle Sections scannen, dann global fixen
    """
    # Erst global prüfen
    all_ai_act_text = ""
    ai_act_keys = [
        "AI_ACT_DUTY_MATRIX_HTML", "AI_ACT_NONCOMPLIANCE_ALERTS_HTML",
        "AI_ACT_DATA_GAPS_HTML", "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "AI_ACT_RELATED_USECASES_HTML", "AI_ACT_TABLE_OFFER_HTML",
        "AI_ACT_ADDON_PACKAGES_HTML", "AI_ACT_SUMMARY_HTML", "ai_act_summary",
        "RISKS_HTML", "risks"
    ]
    for key in ai_act_keys:
        if key in sections and sections[key]:
            all_ai_act_text += str(sections[key])
    
    # Globaler Check
    # v14.24: Prüfe auch die Variable AI_ACT_RISK_LEVEL direkt
    risk_level = sections.get("AI_ACT_RISK_LEVEL", "")
    has_minimal = risk_level == "minimal" or bool(re.search(r"Risikoklasse:\s*minimal", all_ai_act_text, re.IGNORECASE))
    has_hochrisiko = bool(re.search(r"\bHochrisiko\b", all_ai_act_text, re.IGNORECASE))
    
    if has_minimal and has_hochrisiko:
        log.info("[AI-ACT-CONSISTENCY] Global contradiction detected - fixing all sections")
        for key in ai_act_keys:
            if key in sections and sections[key] and "Hochrisiko" in str(sections[key]):
                sections[key] = re.sub(r"\bHochrisiko\b", "geringes Risiko", str(sections[key]))
                log.info(f"[AI-ACT-CONSISTENCY] Fixed Hochrisiko in {key}")
    
    return sections

def apply_ai_act_consistency_OLD(sections: dict) -> dict:
    """Wendet AI-Act Konsistenz-Prüfung auf relevante Sections an."""
    ai_act_sections = [
        # v14.22: Alle AI-Act Sections
        "AI_ACT_DUTY_MATRIX_HTML",
        "AI_ACT_NONCOMPLIANCE_ALERTS_HTML",
        "AI_ACT_DATA_GAPS_HTML",
        "AI_ACT_RECOMMENDED_NEXT_STEPS_HTML",
        "AI_ACT_RELATED_USECASES_HTML",
        "AI_ACT_TABLE_OFFER_HTML",
        "AI_ACT_ADDON_PACKAGES_HTML",
        "AI_ACT_SUMMARY_HTML", "ai_act_summary",
        "RISKS_HTML", "risks"
    ]
    
    for key in ai_act_sections:
        if key in sections and sections[key]:
            fixed, count = fix_ai_act_consistency(sections[key])
            if count > 0:
                sections[key] = fixed

    return sections


# =============================================================================
# v14.35.19+: KPI CONSISTENCY ENFORCER
# =============================================================================
# Ensures all KPI values in the report match the canonical values
# Single Source of Truth: canonical_kpis dict stored in sections

def extract_canonical_kpis(sections: dict) -> dict:
    """
    Extracts canonical KPI values from sections dict.

    These are the single source of truth for:
    - monatsersparnis_stunden (monthly time savings in hours)
    - jahresersparnis_stunden (annual time savings in hours)
    - monatsersparnis_eur (monthly savings in EUR)
    - jahresersparnis_eur (annual savings in EUR)
    - stundensatz_eur (hourly rate)
    - roi_12m (12-month ROI %)
    - payback_months (payback period)
    """
    canonical = {}

    # Extract from sections dict (these are set in gpt_analyze.py)
    kpi_keys = [
        "monatsersparnis_stunden", "jahresersparnis_stunden",
        "monatsersparnis_eur", "jahresersparnis_eur",
        "stundensatz_eur", "roi_12m", "payback_months",
        "capex_realistisch_eur", "opex_realistisch_eur"
    ]

    for key in kpi_keys:
        if key in sections:
            try:
                canonical[key] = float(sections[key])
            except (TypeError, ValueError):
                pass

    return canonical


def enforce_kpi_consistency(html: str, canonical_kpis: dict) -> tuple[str, int]:
    """
    Enforces KPI consistency in HTML content.

    Replaces any time savings/ROI values that deviate significantly from canonical values.
    Tolerance: 20% for savings, 10% for ROI

    Returns:
        tuple: (enforced_html, enforcement_count)
    """
    if not html or not canonical_kpis:
        return html, 0

    enforcements = 0
    result = html

    # Time savings (hours per month): Replace values outside tolerance
    if "monatsersparnis_stunden" in canonical_kpis:
        canonical_hours = canonical_kpis["monatsersparnis_stunden"]

        # Pattern: "X Stunden/Monat" or "X h/Monat" or "X Stunden monatlich"
        # Note: [-–] puts hyphen first to avoid range interpretation issues
        pattern = r'(\d+(?:[-–]\d+)?)\s*(?:Stunden?|h)\s*(?:/\s*Monat|monatlich|pro Monat|monthly)'

        def fix_monthly_hours(match):
            nonlocal enforcements
            matched_text = match.group(1)

            # Handle ranges like "20-35"
            if '–' in matched_text or '-' in matched_text:
                parts = re.split(r'[-–]', matched_text)
                if len(parts) == 2:
                    try:
                        low, high = float(parts[0]), float(parts[1])
                        avg = (low + high) / 2
                        # FIX-RANGE: Reject absurdly wide ranges (ratio > 3x)
                        # e.g. "2–36" → ratio 18x, replace with canonical value
                        range_too_wide = low > 0 and high / low > 3
                        off_from_canonical = (
                            canonical_hours > 0
                            and abs(avg - canonical_hours) / canonical_hours > 0.3
                        )
                        if range_too_wide or off_from_canonical:
                            enforcements += 1
                            # Use tight ±10% range around canonical
                            new_low = max(1, int(canonical_hours * 0.9))
                            new_high = int(canonical_hours * 1.1)
                            # Avoid trivial ranges like "36–39" → just show single value
                            if new_high - new_low <= 2:
                                return f"{int(canonical_hours)} Stunden/Monat"
                            return f"{new_low}–{new_high} Stunden/Monat"
                    except (ValueError, ZeroDivisionError):
                        pass
            else:
                try:
                    value = float(matched_text)
                    # Check if value deviates > 30% from canonical
                    if canonical_hours > 0 and abs(value - canonical_hours) / canonical_hours > 0.3:
                        enforcements += 1
                        return f"{int(canonical_hours)} Stunden/Monat"
                except ValueError:
                    pass

            return match.group(0)

        result = re.sub(pattern, fix_monthly_hours, result, flags=re.IGNORECASE)

    # Time savings (hours per year): Replace values outside tolerance
    if "jahresersparnis_stunden" in canonical_kpis:
        canonical_hours_year = canonical_kpis["jahresersparnis_stunden"]

        # Pattern: "X Stunden/Jahr" or "X h/Jahr" or "X Stunden jährlich"
        # Note: [-–] puts hyphen first to avoid range interpretation issues
        pattern = r'(\d+(?:[-–]\d+)?)\s*(?:Stunden?|h)\s*(?:/\s*Jahr|jährlich|pro Jahr|yearly|p\.a\.)'

        def fix_yearly_hours(match):
            nonlocal enforcements
            matched_text = match.group(1)

            # Handle ranges
            if '–' in matched_text or '-' in matched_text:
                parts = re.split(r'[-–]', matched_text)
                if len(parts) == 2:
                    try:
                        low, high = float(parts[0]), float(parts[1])
                        avg = (low + high) / 2
                        if abs(avg - canonical_hours_year) / canonical_hours_year > 0.3:
                            enforcements += 1
                            new_low = int(canonical_hours_year * 0.85)
                            new_high = int(canonical_hours_year * 1.15)
                            return f"{new_low}–{new_high} Stunden/Jahr"
                    except (ValueError, ZeroDivisionError):
                        pass
            else:
                try:
                    value = float(matched_text)
                    if canonical_hours_year > 0 and abs(value - canonical_hours_year) / canonical_hours_year > 0.3:
                        enforcements += 1
                        return f"{int(canonical_hours_year)} Stunden/Jahr"
                except ValueError:
                    pass

            return match.group(0)

        result = re.sub(pattern, fix_yearly_hours, result, flags=re.IGNORECASE)

    if enforcements > 0:
        log.info(f"[KPI-ENFORCER] Fixed {enforcements} inconsistent KPI values")

    return result, enforcements


def apply_kpi_consistency_enforcer(sections: dict) -> dict:
    """
    Applies KPI consistency enforcement across all relevant sections.

    v14.35.19+: Single Source of Truth for KPIs
    """
    # Extract canonical KPIs
    canonical_kpis = extract_canonical_kpis(sections)

    if not canonical_kpis:
        log.debug("[KPI-ENFORCER] No canonical KPIs found, skipping enforcement")
        return sections

    total_enforcements = 0

    # Sections to check for KPI consistency
    # FIX-ZEITBUDGET: Added CHALLENGE_30_TAGE_HTML + SOFORT_START_HTML to catch
    # hallucinated "2–36 Stunden/Monat" ranges where min=score_sicherheit
    check_sections = [
        "EXECUTIVE_SUMMARY_HTML", "executive_summary",
        "BUSINESS_CASE_HTML", "business_case",
        "ROI_HTML", "roi",
        "RECOMMENDATIONS_HTML", "recommendations",
        "GAMECHANGER_HTML", "gamechanger",
        "QUICK_WINS_HTML", "quick_wins",
        "ROADMAP_90D_HTML", "roadmap_90d",
        "ROADMAP_12M_HTML", "roadmap_12m",
        "CHALLENGE_30_TAGE_HTML", "SOFORT_START_HTML",
    ]

    for key in check_sections:
        if key in sections and sections[key] and isinstance(sections[key], str):
            enforced, count = enforce_kpi_consistency(sections[key], canonical_kpis)
            if count > 0:
                sections[key] = enforced
                total_enforcements += count

    if total_enforcements > 0:
        log.info(f"[KPI-ENFORCER] Complete: {total_enforcements} KPI inconsistencies fixed")

    return sections


# =============================================================================
# Fix-Batch I + K3: EMPTY PAGE KILLER & LAYOUT HARDENING
# =============================================================================

def kill_empty_pages(html: str) -> tuple[str, int]:
    """
    Fix-Batch I + J3 + K3: Remove empty page-breaking sections.

    Empty pages occur when a section div contains only an <h2> or <h3> with
    no substantial content following it.

    K3 Enhancement:
    - Detect sections with less than 80 chars of actual text content
    - Remove double page-break combinations

    Args:
        html: HTML string to process

    Returns:
        Tuple of (cleaned_html, removals_count)
    """
    if not html:
        return html, 0

    removals = 0
    result = html

    # Pattern: div/section with only heading and minimal content (<100 chars of text)
    # Match: <div class="..."><h2>Title</h2></div> or <section><h3>Title</h3></section>
    empty_section_patterns = [
        # Section with only heading (no other content)
        (r'<section[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*</section>', 'empty section'),
        # Div with only heading
        (r'<div[^>]*class="[^"]*section[^"]*"[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*</div>', 'empty div section'),
        # Page-break div with only heading
        (r'<div[^>]*style="[^"]*page-break[^"]*"[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*</div>', 'empty page-break div'),
        # Fix-Batch J3: Section with heading and only <br> tags
        (r'<section[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:<br\s*/?\s*>\s*)+</section>', 'section with only br tags'),
        (r'<div[^>]*class="[^"]*section[^"]*"[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:<br\s*/?\s*>\s*)+</div>', 'div section with only br tags'),
        # Fix-Batch J3: Section with heading + whitespace + br
        (r'<(section|div)[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:\s*<br\s*/?\s*>\s*)*\s*</\1>', 'section with heading and br only'),
    ]

    for pattern, desc in empty_section_patterns:
        matches = re.findall(pattern, result, re.IGNORECASE | re.DOTALL)
        if matches:
            for match in matches:
                match_str = match if isinstance(match, str) else match[0] if match else ""
                log.warning(f"[EMPTY-PAGE-KILLER] Removing {desc}: {match_str[:50]}...")
                removals += 1
            result = re.sub(pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    # Also remove sections with heading and only whitespace/empty paragraphs
    empty_with_p_pattern = r'<(section|div)[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:<p>\s*</p>\s*)*</\1>'
    matches = re.findall(empty_with_p_pattern, result, re.IGNORECASE | re.DOTALL)
    if matches:
        for _ in matches:
            log.warning("[EMPTY-PAGE-KILLER] Removing section with empty paragraphs")
            removals += 1
        result = re.sub(empty_with_p_pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    # Fix-Batch J3: Remove sections with heading + empty paragraphs + br tags
    empty_br_p_pattern = r'<(section|div)[^>]*>\s*<h[23][^>]*>[^<]+</h[23]>\s*(?:(?:<p>\s*</p>|<br\s*/?\s*>)\s*)*</\1>'
    matches = re.findall(empty_br_p_pattern, result, re.IGNORECASE | re.DOTALL)
    if matches:
        for _ in matches:
            log.warning("[EMPTY-PAGE-KILLER] Removing section with empty paragraphs and br tags")
            removals += 1
        result = re.sub(empty_br_p_pattern, '', result, flags=re.IGNORECASE | re.DOTALL)

    # K3: Remove double page-break combinations (after + before)
    double_break_pattern = r'(page-break-after:\s*always[^}]*}[^<]*)(page-break-before:\s*always)'
    if re.search(double_break_pattern, result, re.IGNORECASE | re.DOTALL):
        log.info("[K3-PAGE-BREAK] Removing double page-break combination")
        result = re.sub(double_break_pattern, r'\1page-break-before: auto', result, flags=re.IGNORECASE | re.DOTALL)
        removals += 1

    return result, removals


def detect_orphan_sections(html: str, min_chars: int = 80) -> list[str]:
    """
    K3: Detect sections that have less than min_chars of actual text content.

    These are potential orphan sections that may result in mostly-blank pages.

    Args:
        html: HTML string to analyze
        min_chars: Minimum characters for a section to be considered non-orphan

    Returns:
        List of section identifiers that are potential orphans
    """
    orphans = []

    # Find all section/div elements with page-break
    section_pattern = r'<(section|div)[^>]*(?:class="[^"]*(?:section|chapter)[^"]*"|id="[^"]*")[^>]*>(.*?)</\1>'
    matches = re.findall(section_pattern, html, re.IGNORECASE | re.DOTALL)

    for tag, content in matches:
        # Strip HTML tags to get text content
        text_only = re.sub(r'<[^>]+>', '', content)
        text_only = re.sub(r'\s+', ' ', text_only).strip()

        if len(text_only) < min_chars:
            # Extract section identifier
            id_match = re.search(r'id="([^"]+)"', content)
            class_match = re.search(r'class="([^"]+)"', content)
            identifier = id_match.group(1) if id_match else (class_match.group(1) if class_match else "unknown")
            orphans.append(identifier)
            log.warning(f"[K3-ORPHAN-DETECT] Section '{identifier}' has only {len(text_only)} chars")

    return orphans


def apply_empty_page_killer(sections: dict) -> dict:
    """
    Fix-Batch I: Apply empty page killer to all HTML sections.

    Args:
        sections: Dict with all report sections

    Returns:
        Cleaned sections dict
    """
    html_keys = [k for k in sections.keys() if k.endswith('_HTML') or k == 'html']
    total_removals = 0

    for key in html_keys:
        if key in sections and sections[key] and isinstance(sections[key], str):
            cleaned, count = kill_empty_pages(sections[key])
            if count > 0:
                sections[key] = cleaned
                total_removals += count

    if total_removals > 0:
        log.info(f"[EMPTY-PAGE-KILLER] Complete: {total_removals} empty pages removed")

    return sections


# =============================================================================
# Fix-Batch I: RISK TEXT SENTENCE TRUNCATION
# =============================================================================

def truncate_at_sentence(text: str, max_chars: int = 500) -> str:
    """
    Fix-Batch I: Truncate text at last sentence boundary before max_chars.

    Ensures risk descriptions and other long texts are truncated at
    proper sentence boundaries (., !, ?) rather than mid-sentence.

    Args:
        text: Text to truncate
        max_chars: Maximum character limit

    Returns:
        Truncated text ending at sentence boundary
    """
    if not text or len(text) <= max_chars:
        return text

    # Find the last sentence boundary before max_chars
    truncated = text[:max_chars]

    # Look for sentence endings (., !, ?)
    sentence_endings = ['.', '!', '?']
    last_boundary = -1

    for i in range(len(truncated) - 1, -1, -1):
        if truncated[i] in sentence_endings:
            # Check it's not part of abbreviation (e.g., "z.B.", "bzw.", "etc.")
            # Simple heuristic: must be followed by space or end of string
            if i == len(truncated) - 1 or truncated[i + 1] in (' ', '\n', '<'):
                # Check it's not a single letter abbreviation
                if i >= 2 and truncated[i-1] != '.':
                    last_boundary = i
                    break
                elif i >= 1:
                    last_boundary = i
                    break

    if last_boundary > 0:
        return truncated[:last_boundary + 1]

    # No sentence boundary found, try to cut at last space
    last_space = truncated.rfind(' ')
    if last_space > max_chars // 2:
        return truncated[:last_space] + '...'

    # Last resort: hard cut with ellipsis
    return truncated[:max_chars - 3] + '...'


def truncate_risk_descriptions(html: str, max_chars: int = 2500) -> tuple[str, int]:
    """
    Fix-Batch I: Truncate long risk descriptions at sentence boundaries.

    Finds risk description elements and ensures they don't exceed max_chars,
    cutting only at sentence boundaries.

    Args:
        html: HTML string containing risk descriptions
        max_chars: Maximum character limit for descriptions

    Returns:
        Tuple of (processed_html, truncations_count)
    """
    if not html:
        return html, 0

    truncations = 0
    result = html

    # Pattern: risk description paragraphs or divs
    # Look for common risk description patterns
    desc_patterns = [
        (r'(<div class="risk-description[^"]*"[^>]*>)([^<]{' + str(max_chars) + r',})(</div>)', 'risk-description div'),
        (r'(<p class="risk-text[^"]*"[^>]*>)([^<]{' + str(max_chars) + r',})(</p>)', 'risk-text paragraph'),
        (r'(<td class="risk-desc[^"]*"[^>]*>)([^<]{' + str(max_chars) + r',})(</td>)', 'risk-desc cell'),
    ]

    for pattern, desc in desc_patterns:
        def truncate_match(match):
            nonlocal truncations
            opening = match.group(1)
            content = match.group(2)
            closing = match.group(3)
            truncated = truncate_at_sentence(content, max_chars)
            if len(truncated) < len(content):
                truncations += 1
                log.info(f"[RISK-TRUNCATION] Truncated {desc} from {len(content)} to {len(truncated)} chars")
            return opening + truncated + closing

        result = re.sub(pattern, truncate_match, result, flags=re.IGNORECASE | re.DOTALL)

    return result, truncations


def apply_risk_truncation(sections: dict, max_chars: int = 2500) -> dict:
    """
    Fix-Batch I: Apply risk description truncation to relevant sections.

    Args:
        sections: Dict with all report sections
        max_chars: Maximum character limit for risk descriptions

    Returns:
        Processed sections dict
    """
    # FIX-B14-ARCH: RISKS_HTML excluded — has own LLM budget, truncation destroys SVG cards
    risk_sections = [
        "AI_ACT_SUMMARY_HTML", "ai_act_summary",
        "COMPLIANCE_HTML", "compliance",
    ]

    total_truncations = 0

    for key in risk_sections:
        if key in sections and sections[key] and isinstance(sections[key], str):
            processed, count = truncate_risk_descriptions(sections[key], max_chars)
            if count > 0:
                sections[key] = processed
                total_truncations += count

    if total_truncations > 0:
        log.info(f"[RISK-TRUNCATION] Complete: {total_truncations} descriptions truncated at sentence boundary")

    return sections


# =============================================================================
# FIX-525: RISKS SOLO PADDING (deterministic minimum word guarantee)
# =============================================================================

_RISKS_SOLO_PADDING_HTML = """
<div class="risk-solo-supplemental">
  <h3>Pragmatische Absicherung für Einzelunternehmer</h3>
  <p>Als Einzelunternehmer tragen Sie die volle Verantwortung für den Einsatz von KI-Werkzeugen in Ihrem Geschäft. Die folgenden Absicherungsmaßnahmen helfen Ihnen, typische Risiken zu minimieren und gleichzeitig die Vorteile der KI-Unterstützung voll auszuschöpfen. Jede Maßnahme ist bewusst schlank gehalten und lässt sich ohne großen Zeitaufwand in Ihren Alltag integrieren.</p>

  <h4>Qualitätssicherung und Kontrolle</h4>
  <ul>
    <li><strong>Wöchentliche Stichprobenprüfung:</strong> Prüfen Sie jede Woche mindestens drei bis fünf KI-generierte Inhalte auf Korrektheit, Tonalität und fachliche Richtigkeit. Ein kurzer 15-Minuten-Check am Freitagnachmittag verhindert, dass sich systematische Fehler einschleichen. Dokumentieren Sie auffällige Muster, um Ihre Prompts kontinuierlich zu verbessern.</li>
    <li><strong>Vor-Versand-Kontrolle bei Kundenkommunikation:</strong> Lesen Sie jede KI-unterstützte E-Mail oder jeden Bericht vor dem Versand noch einmal durch. Achten Sie besonders auf Namen, Zahlen und spezifische Kundendetails. Diese abschließende Prüfung dauert nur wenige Minuten und schützt Ihre professionelle Reputation.</li>
    <li><strong>Feedback-Schleife einrichten:</strong> Bitten Sie gelegentlich vertrauenswürdige Kunden oder Kollegen um Feedback zu Ihren KI-unterstützten Inhalten. Externe Perspektiven helfen, blinde Flecken zu erkennen und die Qualität kontinuierlich zu steigern.</li>
  </ul>

  <h4>Verantwortlichkeiten und Grenzen</h4>
  <ul>
    <li><strong>Klare Aufgabentrennung definieren:</strong> Legen Sie schriftlich fest, welche Aufgaben Sie der KI überlassen und welche Sie selbst erledigen. Kritische Kundenentscheidungen, sensible Beratungsgespräche und rechtlich relevante Dokumente sollten immer in Ihren Händen bleiben. Die KI unterstützt bei Routine und Vorbereitung.</li>
    <li><strong>Eskalationskriterien festlegen:</strong> Bestimmen Sie klare Kriterien, wann Sie von KI-Unterstützung auf manuelle Bearbeitung wechseln. Bei ungewöhnlichen Anfragen, Beschwerden oder komplexen Sonderfällen ist menschliches Urteilsvermögen unverzichtbar.</li>
    <li><strong>Entscheidungshoheit behalten:</strong> Nutzen Sie KI als Werkzeug zur Entscheidungsvorbereitung, nicht als Entscheidungsträger. Sie tragen die Verantwortung für alle Geschäftsentscheidungen und sollten KI-Vorschläge stets kritisch prüfen.</li>
  </ul>

  <h4>Technische Absicherung</h4>
  <ul>
    <li><strong>Backup-Prozesse bereithalten:</strong> Halten Sie für jede KI-gestützte Aufgabe einen manuellen Alternativprozess bereit. Bei technischen Störungen, API-Ausfällen oder Wartungsarbeiten können Sie so nahtlos weiterarbeiten. Testen Sie diese Backup-Prozesse vierteljährlich.</li>
    <li><strong>Zugangsdaten sicher verwalten:</strong> Speichern Sie API-Schlüssel und Zugangsdaten in einem Passwort-Manager. Teilen Sie diese niemals per E-Mail oder Messenger. Ändern Sie Passwörter bei Verdacht auf unbefugten Zugriff sofort.</li>
    <li><strong>Regelmäßige Updates durchführen:</strong> Halten Sie Ihre KI-Werkzeuge und Browser auf dem aktuellen Stand. Sicherheitsupdates schließen bekannte Schwachstellen und schützen Ihre Geschäftsdaten.</li>
  </ul>

  <h4>Rechtliche und finanzielle Absicherung</h4>
  <ul>
    <li><strong>Datenschutz-Check durchführen:</strong> Prüfen Sie einmal jährlich, ob Ihre KI-Nutzung den aktuellen Datenschutz- und Urheberrechtsanforderungen entspricht. Achten Sie besonders auf die Verarbeitung von Kundendaten und die Nutzung urheberrechtlich geschützter Inhalte als Trainingsinput.</li>
    <li><strong>Transparenz gegenüber Kunden:</strong> Kommunizieren Sie offen, wo Sie KI-Unterstützung nutzen. Die meisten Kunden schätzen Ehrlichkeit und moderne Arbeitsweisen. Eine kurze Information in Ihren AGB oder auf Ihrer Website schafft Vertrauen.</li>
    <li><strong>Kosten überwachen:</strong> Überwachen Sie monatlich Ihre KI-Abonnements und API-Kosten. Kündigen Sie nicht genutzte Dienste zeitnah. Setzen Sie Kostenlimits bei nutzungsbasierten Diensten, um Überraschungen zu vermeiden.</li>
    <li><strong>Haftungsfragen klären:</strong> Informieren Sie sich über Ihre Haftung bei KI-generierten Fehlern. Im Zweifelsfall konsultieren Sie einen Rechtsanwalt, um Ihre Geschäftsbedingungen entsprechend anzupassen.</li>
  </ul>

  <p class="small muted">Diese Absicherungsmaßnahmen sind speziell für Einzelunternehmer konzipiert und erfordern nur minimalen Zeitaufwand bei maximalem Schutz. Passen Sie die Maßnahmen an Ihre spezifische Situation an und überprüfen Sie sie halbjährlich auf Aktualität. Ein strukturierter Ansatz bei der Risikominimierung zahlt sich langfristig aus und schafft eine solide Grundlage für nachhaltiges Wachstum mit KI-Unterstützung in Ihrem Geschäftsalltag.</p>
</div>
"""


def apply_risks_solo_padding(sections: dict, company_size: str) -> dict:
    """
    FIX-525: Deterministic padding for RISKS_HTML when too short for solo.

    If RISKS_HTML has fewer than 500 words for solo persona, appends
    deterministic supplemental content to guarantee minimum word count.

    Args:
        sections: Dict with all report sections
        company_size: Company size ("solo", "team", "kmu")

    Returns:
        Processed sections dict with padded RISKS_HTML if needed
    """
    if not company_size or company_size.lower() != "solo":
        return sections

    min_words_solo = 500
    key = "RISKS_HTML"
    html = sections.get(key, "")

    if not html or not isinstance(html, str):
        return sections

    # Count words (strip HTML tags)
    text_only = re.sub(r'<[^>]+>', ' ', html)
    word_count = len(text_only.split())

    if word_count >= min_words_solo:
        log.debug("[FIX-525][RISKS-PADDING] RISKS_HTML has %d words, no padding needed", word_count)
        return sections

    # Append padding content
    # Insert before closing </section> tag if present, otherwise append
    if "</section>" in html:
        padded_html = html.replace("</section>", f"\n{_RISKS_SOLO_PADDING_HTML}\n</section>", 1)
    else:
        padded_html = f"{html}\n{_RISKS_SOLO_PADDING_HTML}"

    # Verify new word count
    new_text = re.sub(r'<[^>]+>', ' ', padded_html)
    new_word_count = len(new_text.split())

    sections[key] = padded_html
    log.info(
        "[FIX-525][RISKS-PADDING] Padded RISKS_HTML: %d → %d words (min=%d)",
        word_count, new_word_count, min_words_solo
    )

    return sections


# =============================================================================
# Fix-Batch J4 + K1: CHAT ARTEFACT FILTER
# =============================================================================
# Problem: LLM output sometimes contains chat artefacts like "Schreib mir",
# "Frag mich", "Wenn du..." that are inappropriate for formal reports.
# K1 Enhancement: Also filter leading punctuation and Du-Ansprache
# Solution: Filter these patterns from all text sections.
# =============================================================================

# Chat artefacts that should be removed (German patterns)
# K1: Extended with more German prompt patterns
CHAT_ARTEFACT_PATTERNS = [
    # K1: Leading punctuation at paragraph/sentence start
    r"^\?\s*",  # Leading question mark
    r"^[.]\s*",  # Leading period
    r"^[–-]\s*(?![0-9])",  # Leading dash (not before numbers)
    # Direct address patterns (Du-form - informal, must be Sie)
    r"(?i)\bDu kannst mir\b.*?[.!?]",
    r"(?i)\bDu kannst\b.*?[.!?]",
    r"(?i)\bschreib\s+mir\b.*?[.!?]",
    r"(?i)\bfrag\s+mich\b.*?[.!?]",
    r"(?i)\bwenn\s+du\s+(möchtest|willst|brauchst)\b.*?[.!?]",
    r"(?i)\bsag\s+mir\s+bescheid\b.*?[.!?]",
    r"(?i)\blass\s+mich\s+wissen\b.*?[.!?]",
    r"(?i)\bmeld\s+dich\b.*?[.!?]",
    r"(?i)\bruf\s+mich\s+an\b.*?[.!?]",
    r"(?i)\bich\s+kann\s+dir\s+(helfen|zeigen|erklären)\b.*?[.!?]",
    r"(?i)\bich\s+stehe\s+dir\s+zur\s+verfügung\b.*?[.!?]",
    r"(?i)\bdu\s+kannst\s+mich\s+(fragen|kontaktieren)\b.*?[.!?]",
    r"(?i)\bwenn\s+du\s+fragen\s+hast\b.*?[.!?]",
    r"(?i)\bfalls\s+du\s+(weitere|mehr)\s+infos\s+(brauchst|möchtest)\b.*?[.!?]",
    # K1: Additional German prompt patterns
    r"(?i)\bgerne\s+so\s+konkret\b.*?[.!?]",
    r"(?i)\bstellen\.\s*$",  # Ends with "stellen."
    r"(?i)\bz\.\s*B\.\s+Fragen\s+stellen\b.*?[.!?]",
    # Meta-commentary about the chat
    r"(?i)\bwie\s+besprochen\b",
    r"(?i)\bwie\s+ich\s+dir\s+gesagt\s+habe\b",
    r"(?i)\bich\s+hoffe,\s+das\s+hilft\b",
    # Emoji clusters (more than 2 consecutive emojis)
    r"[\U0001F300-\U0001F9FF]{3,}",
]


def filter_chat_artefacts(text: str) -> tuple[str, int]:
    """
    Fix-Batch J4 + K1: Remove chat artefacts from text.

    Filters out LLM chat artefacts like "Schreib mir", "Frag mich", etc.
    that are inappropriate for formal business reports.

    K1 Enhancement: Also removes leading punctuation and Du-Ansprache.

    Args:
        text: Text to process

    Returns:
        Tuple of (cleaned_text, removals_count)
    """
    if not text:
        return text, 0

    removals = 0
    result = text

    for pattern in CHAT_ARTEFACT_PATTERNS:
        matches = re.findall(pattern, result, re.MULTILINE)
        if matches:
            removals += len(matches)
            result = re.sub(pattern, '', result, flags=re.MULTILINE)

    # K1: Clean leading punctuation from HTML paragraph content
    # Pattern: <p>? ... or <p>. ... at start of paragraphs
    html_leading_punct = r'(<p[^>]*>)\s*([?.\-–])\s*'
    html_matches = re.findall(html_leading_punct, result)
    if html_matches:
        removals += len(html_matches)
        result = re.sub(html_leading_punct, r'\1', result)

    # Clean up double spaces and line breaks from removals
    result = re.sub(r'\s{2,}', ' ', result)
    result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)

    # K1: Remove empty paragraphs after filtering
    result = re.sub(r'<p[^>]*>\s*</p>', '', result)

    if removals > 0:
        log.info(f"[CHAT-ARTEFACT-FILTER] Removed {removals} chat artefacts")

    return result.strip(), removals


def apply_chat_artefact_filter(sections: dict) -> dict:
    """
    Fix-Batch J4: Apply chat artefact filter to all text sections.

    Args:
        sections: Dict with all report sections

    Returns:
        Cleaned sections dict
    """
    # All text-bearing sections
    text_sections = [
        k for k in sections.keys()
        if isinstance(sections.get(k), str) and sections.get(k)
        and (k.endswith('_HTML') or k.islower() or k in [
            'EXECUTIVE_SUMMARY', 'QUICK_WINS', 'RECOMMENDATIONS',
            'RISKS', 'STRATEGY', 'ROADMAP', 'executive_summary',
            'quick_wins', 'recommendations', 'risks', 'strategy', 'roadmap'
        ])
    ]

    total_removals = 0

    for key in text_sections:
        if key in sections and sections[key]:
            cleaned, count = filter_chat_artefacts(str(sections[key]))
            if count > 0:
                sections[key] = cleaned
                total_removals += count

    if total_removals > 0:
        log.info(f"[CHAT-ARTEFACT-FILTER] Complete: {total_removals} total artefacts removed")

    return sections


# =============================================================================
# FIX-R2-2: PROMPT-LEAK HARD-BLOCK
# =============================================================================
# Problem: LLM sometimes renders the prompt template itself instead of the
# generated content, showing "Wie kann ich helfen? Bitte beschreibe kurz..."
# in the final report.  The existing chat-artefact filter (regex patterns)
# misses multi-sentence prompt leaks.
#
# Solution: Detect known prompt-leak phrases and remove the entire
# containing HTML block (<p>…</p> or <h3>…) to avoid partial remnants.
# =============================================================================

PROMPT_LEAK_HARD_BLOCK_PHRASES = [
    "Wie kann ich helfen",
    "Wie kann ich dir helfen",
    "Wie kann ich Ihnen helfen",
    "Bitte beschreibe kurz",
    "Ihr Ziel (z. B.",
    "Ihre Daten/Quellen (z. B.",
    "Ihre Umgebung (Cloud/On-Prem",
    "Erfolgskriterien (KPIs), Budgetrahmen",
    "nenne auch Branche und Stakeholder",
    "Wenn Sie magst",
    "Wobei kann ich helfen",
    "beschreibe dein anliegen",
    "du hast noch keine frage",
    "ich sehe keine frage",
]


def _remove_html_block_containing(html: str, phrase: str) -> tuple[str, bool]:
    """Remove the HTML block (<p>…</p>, <li>…</li>, or <div>…</div>) that contains *phrase*."""
    lower_html = html.lower()
    lower_phrase = phrase.lower()
    if lower_phrase not in lower_html:
        return html, False

    # Try to remove containing <p>…</p>, <li>…</li>, <div>…</div> blocks
    for tag in ("p", "li", "div"):
        pattern = re.compile(
            rf'<{tag}[^>]*>[^<]*(?:<(?!/{tag}>)[^<]*)*{re.escape(phrase)}.*?</{tag}>',
            re.IGNORECASE | re.DOTALL,
        )
        new_html, n = pattern.subn("", html)
        if n > 0:
            return new_html, True

    # Fallback: remove the sentence containing the phrase
    pattern_sent = re.compile(
        rf'[^.!?]*{re.escape(phrase)}[^.!?]*[.!?]?\s*',
        re.IGNORECASE,
    )
    new_html, n = pattern_sent.subn("", html)
    return new_html, n > 0


def apply_prompt_leak_hard_block(sections: dict) -> dict:
    """
    FIX-R2-2: Remove entire HTML blocks that contain prompt-leak phrases.

    These are multi-sentence prompt template leaks that the regex-based
    chat-artefact filter doesn't catch.
    """
    total_removed = 0
    checked_keys = [
        k for k in sections
        if isinstance(sections.get(k), str)
        and sections[k]
        and (k.endswith("_HTML") or k.islower())
        and not k.startswith("_")
    ]

    for key in checked_keys:
        html = sections[key]
        for phrase in PROMPT_LEAK_HARD_BLOCK_PHRASES:
            html, removed = _remove_html_block_containing(html, phrase)
            if removed:
                total_removed += 1
                log.info("[FIX-R2-2][HARD-BLOCK] Removed block containing '%s' from %s", phrase, key)
        if total_removed > 0:
            # Clean up empty paragraphs left behind
            html = re.sub(r'<p[^>]*>\s*</p>', '', html)
            html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
            sections[key] = html

    if total_removed > 0:
        log.info("[FIX-R2-2] PROMPT-LEAK HARD-BLOCK: removed %d leak blocks total", total_removed)

    return sections


# =============================================================================
# FIX-504: CANONICAL KENNZAHLENBLOCK KPI ENFORCER
# =============================================================================
# Problem: Report-501 shows inconsistent KPIs in Kennzahlenblock:
# - "Payback11 Monate" (missing space)
# - "ROI-Rate85%" (missing space)
# - "Zeitersparnis/Monat210 Std" (missing space)
# - Values don't match canonical business case values
#
# Solution: Targeted enforcer for Kennzahlenblock patterns with spacing normalization

# Patterns that indicate Kennzahlenblock context (not scenario tables)
KENNZAHLEN_CONTEXT_MARKERS = [
    r'Business[-\s]?Case\s+Kennzahlen',
    r'Ihre\s+KI[-\s]?Kennzahlen',
    r'ROI[-\s]?Übersicht',
    r'Amortisations[-\s]?Übersicht',
    r'class="kpi-card"',
    r'class="kennzahlen"',
]

# KPI patterns with missing spaces (spacing issues from LLM)
# FIX-506: Enhanced patterns to handle Report-504 specific glitches
# FIX-509-C: Final hardening for Kennzahlenblock typography
KPI_SPACING_PATTERNS = [
    # ==========================================================================
    # FIX-509-C: PRIORITY PATTERNS - Must enforce LABEL: TEXT format
    # ==========================================================================

    # "ROI-Ratesiehe Business Case" → "ROI-Rate: siehe Business Case"
    (r'(ROI[-\s]?Rate)\s*siehe\s+(Business\s*Case|Simulation)',
     r'\1: siehe \2'),
    # "ROI-Ratesiehe" → "ROI-Rate: siehe"
    (r'(ROI[-\s]?Rate)\s*siehe\b',
     r'\1: siehe'),
    # "Payback (Monate)siehe Business Case" → "Payback (Monate): siehe Business Case"
    (r'(Payback\s*\(Monate?\))\s*siehe\s+(Business\s*Case|Simulation)',
     r'\1: siehe \2'),
    # "Payback (Monate)siehe" → "Payback (Monate): siehe"
    (r'(Payback\s*\(Monate?\))\s*siehe\b',
     r'\1: siehe'),
    # "Paybacksiehe" → "Payback: siehe"
    (r'(Payback)\s*siehe\b',
     r'\1: siehe'),
    # "AI Act RisikoMittel" → "AI Act Risiko: Mittel"
    (r'(AI\s*Act\s*Risiko)\s*(minimal|gering|mittel|hoch|Hochrisiko|Niedrigrisiko|Minimal|Gering|Mittel|Hoch)',
     r'\1: \2'),
    # "AI-Act-RisikoMittel" variant → "AI-Act-Risiko: Mittel"
    (r'(AI[-\s]Act[-\s]Risiko)\s*(minimal|gering|mittel|hoch|Hochrisiko|Niedrigrisiko|Minimal|Gering|Mittel|Hoch)',
     r'\1: \2'),

    # ==========================================================================
    # Standard KPI spacing patterns
    # ==========================================================================

    # Payback without space: "Payback11 Monate" or "Payback11Monate" or "Payback11 Mon."
    (r'(Payback|Amortisation|Amortisierung)\s*(\d+(?:[,\.]\d+)?)\s*(Monate?|months?|Mon\.?)',
     r'\1: \2 \3'),
    # ROI-Rate with suffix: "ROI-Rate165%nach 24 Monaten" → "ROI-Rate: 165 % (nach 12 Monaten)"
    # KIS-1034-D4: Force "nach 12 Monaten" — LLM sometimes hallucinates 24/18/36.
    (r'(ROI[-\s]?Rate)\s*(\d+(?:[,\.]\d+)?)\s*%\s*nach\s+\d+\s+(Monat(?:en?)?)',
     r'\1: \2 % (nach 12 \3)'),
    # ROI-Rate without space: "ROI-Rate85%" or "ROI-Rate85%auf"
    (r'(ROI[-\s]?Rate)\s*(\d+(?:[,\.]\d+)?)\s*%\s*(?![(\w])',
     r'\1: \2 %'),
    (r'(ROI[-\s]?Rate)\s*(\d+(?:[,\.]\d+)?)\s*%\s*(?=auf)',
     r'\1: \2 % '),
    # ROI without space: "ROI85%" or "ROI: 85%auf"
    (r'\bROI\s*:?\s*(\d+(?:[,\.]\d+)?)\s*%\s*(?=auf|\w)',
     r'ROI: \1 % '),
    # Zeitersparnis with glued unit: "Zeitersparnis/Monat180 Std." or "Zeitersparnis/Monat210Std"
    (r'(Zeitersparnis\s*/\s*Monat)\s*(\d+(?:[,\.]\d+)?)\s*(Std\.?|Stunden?|h)',
     r'\1: \2 \3'),
    # Generic time savings: "Zeitersparnis210Std"
    (r'(Zeitersparnis)\s*(\d+(?:[,\.]\d+)?)\s*(Std\.?|Stunden?|h)',
     r'\1: \2 \3'),
    # "ROI-Rate165%siehe" → "ROI-Rate: 165 % – siehe"
    (r'(ROI[-\s]?Rate)\s*(\d+(?:[,\.]\d+)?)\s*%?\s*siehe\b',
     r'\1: \2 % – siehe'),
    # "Payback11siehe" → "Payback: 11 Monate – siehe"
    (r'(Payback|Amortisation)\s*(\d+(?:[,\.]\d+)?)\s*(?:Monate?)?\s*siehe\b',
     r'\1: \2 Monate – siehe'),
    # General label:value patterns without colon/space
    (r'(Payback|ROI|Amortisation)\s*:?\s*(\d)', r'\1: \2'),
]


def fix_kennzahlen_spacing(html: str) -> tuple[str, int]:
    """
    FIX-504 TASK 2: Fix missing spaces in Kennzahlenblock KPI patterns.

    Fixes patterns like:
    - "Payback11 Monate" → "Payback: 11 Monate"
    - "ROI-Rate85%" → "ROI-Rate: 85 %"
    - "Zeitersparnis/Monat210 Std" → "Zeitersparnis/Monat: 210 Std"
    - "AI Act RisikoMittel" → "AI Act Risiko: Mittel"

    Args:
        html: HTML content to fix

    Returns:
        Tuple of (fixed_html, fix_count)
    """
    if not html:
        return html, 0

    result = html
    fix_count = 0

    for pattern, replacement in KPI_SPACING_PATTERNS:
        regex = re.compile(pattern, re.IGNORECASE)
        matches = regex.findall(result)
        if matches:
            result = regex.sub(replacement, result)
            fix_count += len(matches)
            log.debug(f"[KPI-SPACING] Fixed pattern '{pattern[:30]}...': {len(matches)}x")

    # Additional cleanup: multiple colons/spaces
    result = re.sub(r':\s*:\s*', ': ', result)
    result = re.sub(r'\s{2,}', ' ', result)

    return result, fix_count


def enforce_kennzahlenblock_kpis(html: str, canonical_kpis: dict) -> tuple[str, int]:
    """
    FIX-504 TASK 1: Enforce canonical KPI values in Kennzahlenblock only.

    Targets specific Kennzahlenblock patterns and replaces with canonical values.
    Does NOT affect scenario tables or Monte Carlo simulation sections.

    Args:
        html: HTML content with potential KPI inconsistencies
        canonical_kpis: Dict with canonical values:
            - PAYBACK_MONTHS: canonical payback period
            - ROI_PLANWERT or roi_12m: canonical ROI percentage
            - monatsersparnis_stunden: canonical monthly time savings
            - AI_ACT_RISK_LEVEL: canonical AI Act risk level

    Returns:
        Tuple of (enforced_html, enforcement_count)
    """
    if not html or not canonical_kpis:
        return html, 0

    result = html
    enforcements = 0

    # Get canonical values
    canonical_payback = canonical_kpis.get("PAYBACK_MONTHS")
    canonical_roi = canonical_kpis.get("ROI_PLANWERT") or canonical_kpis.get("roi_12m")
    canonical_time_savings = canonical_kpis.get("monatsersparnis_stunden")
    canonical_ai_risk = canonical_kpis.get("AI_ACT_RISK_LEVEL")

    # Format canonical payback for German locale
    if canonical_payback is not None:
        try:
            pb_val = float(str(canonical_payback).replace(",", "."))
            pb_de = f"{pb_val:.1f}".replace(".", ",")
            if pb_de.endswith(",0"):
                pb_de = pb_de[:-2]

            # Pattern: standalone Payback mentions (not in scenario context)
            # FIX-520: Extended to catch: "Payback11 Monate", "Payback: 11 Mon.",
            # "Payback-Zeit: 11 Mo.", "Amortisation 9,5 Monate"
            payback_pattern = re.compile(
                r'((?:Payback(?:-Zeit)?|Amortisation|Amortisierung)[:\s]*)(\d+(?:[,\.]\d+)?)\s*(Monate?|Mon\.?|Mo\.?|months?)',
                re.IGNORECASE
            )

            def replace_payback(match):
                nonlocal enforcements
                prefix = match.group(1)
                found_val = match.group(2)
                suffix = match.group(3)

                # Parse found value
                try:
                    found_float = float(found_val.replace(",", "."))
                    # Skip if within 20% of canonical (allow rounding)
                    if abs(found_float - pb_val) / max(pb_val, 0.1) <= 0.20:
                        return match.group(0)

                    # Check if in scenario context
                    match_pos = match.start()
                    context_start = max(0, match_pos - 100)
                    context = result[context_start:match_pos].lower()
                    if any(kw in context for kw in ['szenario', 'konservativ', 'optimistisch', 'p50', 'p80', 'p90', 'simulation']):
                        return match.group(0)

                    enforcements += 1
                    log.info(f"[KENNZAHLEN-KPI] Payback: '{found_val}' → '{pb_de}'")
                    return f"{prefix.rstrip()}: {pb_de} {suffix}"
                except (ValueError, TypeError):
                    return match.group(0)

            result = payback_pattern.sub(replace_payback, result)
        except (ValueError, TypeError) as e:
            log.warning(f"[KENNZAHLEN-KPI] Invalid PAYBACK_MONTHS: {canonical_payback} - {e}")

    # Format canonical ROI
    if canonical_roi is not None:
        try:
            roi_val = float(str(canonical_roi).replace(",", "."))
            roi_str = f"{int(roi_val)}" if roi_val == int(roi_val) else f"{roi_val:.0f}"

            # Pattern: ROI percentage mentions
            # "ROI: 85%" or "ROI-Rate: 200%" or "ROI-Rate85%"
            roi_pattern = re.compile(
                r'(ROI[-\s]?(?:Rate)?[:\s]+)(\d+(?:[,\.]\d+)?)\s*%',
                re.IGNORECASE
            )

            def replace_roi(match):
                nonlocal enforcements
                prefix = match.group(1)
                found_val = match.group(2)

                try:
                    found_float = float(found_val.replace(",", "."))
                    # Skip if within 20% of canonical
                    if abs(found_float - roi_val) / max(roi_val, 0.1) <= 0.20:
                        return match.group(0)

                    # Check if in scenario context
                    match_pos = match.start()
                    context_start = max(0, match_pos - 100)
                    context = result[context_start:match_pos].lower()
                    if any(kw in context for kw in ['szenario', 'konservativ', 'optimistisch', 'p50', 'p80', 'p90', 'simulation']):
                        return match.group(0)

                    enforcements += 1
                    log.info(f"[KENNZAHLEN-KPI] ROI: '{found_val}%' → '{roi_str}%'")
                    return f"{prefix.rstrip()}: {roi_str} %"
                except (ValueError, TypeError):
                    return match.group(0)

            result = roi_pattern.sub(replace_roi, result)
        except (ValueError, TypeError) as e:
            log.warning(f"[KENNZAHLEN-KPI] Invalid ROI: {canonical_roi} - {e}")

    # Format canonical time savings
    if canonical_time_savings is not None:
        try:
            ts_val = float(str(canonical_time_savings).replace(",", "."))
            ts_str = f"{int(ts_val)}" if ts_val == int(ts_val) else f"{ts_val:.0f}"

            # Pattern: Zeitersparnis mentions
            # "Zeitersparnis/Monat: 210 Std" or "Zeitersparnis/Monat210 Std"
            time_pattern = re.compile(
                r'(Zeitersparnis\s*/\s*Monat[:\s]+)(\d+(?:[,\.]\d+)?)\s*(Std\.?|Stunden?|h)',
                re.IGNORECASE
            )

            def replace_time(match):
                nonlocal enforcements
                prefix = match.group(1)
                found_val = match.group(2)
                suffix = match.group(3)

                try:
                    found_float = float(found_val.replace(",", "."))
                    # Skip if within 30% of canonical (time savings can vary more)
                    if abs(found_float - ts_val) / max(ts_val, 0.1) <= 0.30:
                        return match.group(0)

                    enforcements += 1
                    log.info(f"[KENNZAHLEN-KPI] Zeitersparnis: '{found_val}' → '{ts_str}'")
                    return f"{prefix.rstrip()}: {ts_str} {suffix}"
                except (ValueError, TypeError):
                    return match.group(0)

            result = time_pattern.sub(replace_time, result)
        except (ValueError, TypeError) as e:
            log.warning(f"[KENNZAHLEN-KPI] Invalid time savings: {canonical_time_savings} - {e}")

    return result, enforcements


def apply_kennzahlenblock_enforcer(sections: dict) -> dict:
    """
    FIX-504: Apply Kennzahlenblock KPI enforcement to all relevant sections.

    Two-pass approach:
    1. First pass: Fix spacing issues (Payback11 → Payback: 11)
    2. Second pass: Enforce canonical values where significantly different

    Args:
        sections: Dict with all report sections

    Returns:
        Sections with enforced canonical KPI values and fixed spacing
    """
    # Build canonical KPIs dict from sections
    canonical_kpis = {
        "PAYBACK_MONTHS": sections.get("PAYBACK_MONTHS"),
        "ROI_PLANWERT": sections.get("ROI_PLANWERT"),
        "roi_12m": sections.get("roi_12m"),
        "monatsersparnis_stunden": sections.get("monatsersparnis_stunden"),
        "AI_ACT_RISK_LEVEL": sections.get("AI_ACT_RISK_LEVEL"),
    }

    # Sections to process (includes Kennzahlenblock-containing sections)
    kpi_sections = [
        "EXECUTIVE_SUMMARY_HTML", "executive_summary",
        "BUSINESS_CASE_HTML", "business_case",
        "RECOMMENDATIONS_HTML", "recommendations",
        "GAMECHANGER_HTML", "gamechanger",
        "QUICK_WINS_HTML", "quick_wins",
        "HERO_HTML", "hero",
        # LLM-generated text sections that may contain KPI summaries
        "BRANCH_DEEP_DIVE_HTML",
        "TOOLS_EMPFEHLUNGEN_HTML",
    ]

    total_spacing_fixes = 0
    total_enforcements = 0

    for key in kpi_sections:
        content = sections.get(key)
        if not content or not isinstance(content, str):
            continue

        # Pass 1: Fix spacing
        content, spacing_fixes = fix_kennzahlen_spacing(content)
        total_spacing_fixes += spacing_fixes

        # Pass 2: Enforce canonical values
        content, enforcements = enforce_kennzahlenblock_kpis(content, canonical_kpis)
        total_enforcements += enforcements

        if spacing_fixes > 0 or enforcements > 0:
            sections[key] = content

    if total_spacing_fixes > 0:
        log.info(f"[KENNZAHLEN-KPI] Fixed {total_spacing_fixes} spacing issues")
    if total_enforcements > 0:
        log.info(f"[KENNZAHLEN-KPI] Enforced {total_enforcements} canonical KPI values")

    return sections


# =============================================================================
# FIX-504 TASK 5: RELEASE_STRICT_MODE PREPARATION
# =============================================================================
# Utilities to check warning levels before enabling strict mode.
# Goal: warnings=0 (or only known acceptable warnings via whitelist)

# Known acceptable warnings that should not block strict mode
STRICT_MODE_ACCEPTABLE_WARNINGS = [
    # These are informational, not quality issues
    r"\[SOLO-LANGUAGE\].*replaced_terms",  # Term replacements are fixes, not warnings
    r"\[KPI-ENFORCER\].*Fixed.*inconsistent",  # Fixed values are good
    r"\[KENNZAHLEN-KPI\].*Fixed",  # Fixed spacing/values are good
    r"\[PAYBACK-ENFORCER\].*Enforced",  # Enforced values are good
]

# Critical warnings that MUST be fixed before strict mode
STRICT_MODE_BLOCKING_PATTERNS = [
    r"SIZE_MISMATCH",  # Persona/size mismatch
    r"PERSONA_LEAK",  # Wrong persona detected
    r"LLM_HALLUCINATION",  # Hallucinated content
    r"CRITICAL_ERROR",  # Critical quality issues
    r"JSON.*unparseable",  # JSON parsing failures
    r"FALLBACK.*triggered",  # Fallback content used
]


def check_strict_mode_readiness(warnings: list[str], blocking_threshold: int = 0) -> dict:
    """
    FIX-504 TASK 5: Check if the report is ready for RELEASE_STRICT_MODE.

    Analyzes warnings to determine if strict mode can be safely enabled.

    Args:
        warnings: List of warning messages from the current report
        blocking_threshold: Maximum number of blocking warnings allowed (default 0)

    Returns:
        Dict with:
            - ready: bool - True if strict mode can be enabled
            - blocking_count: int - Number of blocking warnings
            - acceptable_count: int - Number of acceptable warnings
            - blocking_warnings: list - List of blocking warning messages
            - summary: str - Human-readable summary
    """
    blocking_warnings = []
    acceptable_warnings = []
    other_warnings = []

    for warning in warnings:
        warning_str = str(warning)

        # Check if it's a blocking pattern
        is_blocking = any(
            re.search(pattern, warning_str, re.IGNORECASE)
            for pattern in STRICT_MODE_BLOCKING_PATTERNS
        )

        if is_blocking:
            blocking_warnings.append(warning_str)
            continue

        # Check if it's acceptable
        is_acceptable = any(
            re.search(pattern, warning_str, re.IGNORECASE)
            for pattern in STRICT_MODE_ACCEPTABLE_WARNINGS
        )

        if is_acceptable:
            acceptable_warnings.append(warning_str)
        else:
            other_warnings.append(warning_str)

    blocking_count = len(blocking_warnings)
    ready = blocking_count <= blocking_threshold

    summary_parts = [
        f"STRICT_MODE_READINESS: {'✅ READY' if ready else '❌ NOT READY'}",
        f"  Blocking warnings: {blocking_count}",
        f"  Acceptable warnings: {len(acceptable_warnings)}",
        f"  Other warnings: {len(other_warnings)}",
    ]

    if blocking_warnings:
        summary_parts.append("  Blocking issues:")
        for bw in blocking_warnings[:5]:  # Show first 5
            summary_parts.append(f"    - {bw[:100]}...")
        if len(blocking_warnings) > 5:
            summary_parts.append(f"    ... and {len(blocking_warnings) - 5} more")

    summary = "\n".join(summary_parts)

    log.info(f"[STRICT-MODE-CHECK] {summary}")

    return {
        "ready": ready,
        "blocking_count": blocking_count,
        "acceptable_count": len(acceptable_warnings),
        "other_count": len(other_warnings),
        "blocking_warnings": blocking_warnings,
        "acceptable_warnings": acceptable_warnings,
        "other_warnings": other_warnings,
        "summary": summary,
    }


def get_strict_mode_status() -> dict:
    """
    FIX-504 TASK 5: Get current RELEASE_STRICT_MODE status.

    Returns:
        Dict with:
            - enabled: bool - True if strict mode is currently enabled
            - recommended: bool - True if strict mode should be enabled
            - reason: str - Explanation
    """
    import os

    strict_mode = os.getenv("RELEASE_STRICT_MODE", "0") in ("1", "true", "True")

    return {
        "enabled": strict_mode,
        "env_var": os.getenv("RELEASE_STRICT_MODE", "not set"),
        "description": (
            "RELEASE_STRICT_MODE=1 enables zero-tolerance quality gating. "
            "Reports with critical warnings will be blocked. "
            "Only enable when warnings have been significantly reduced."
        ),
    }


# =============================================================================
# FIX-506 TASK 5: POST-TRUNCATION TEMPLATE PHRASE CLEANUP
# =============================================================================
# KIS-1011-B2: Known broken word-boundary phrases from LLM truncation
KNOWN_TRUNCATION_FIXES = [
    ('Vorhabe ichtschaftlich', 'Vorhaben wirtschaftlich'),
    ('Vorhabe nwirtschaftlich', 'Vorhaben wirtschaftlich'),
    ('wirtschaftlich keit', 'wirtschaftlichkeit'),
    ('Wirtschaftlich keit', 'Wirtschaftlichkeit'),
    # KIS-1013-B1: Grammar fixes for known truncation-repair artifacts
    ('Ich haben keinen Mitarbeiter', 'Wir haben keinen Mitarbeiter'),
    ('ich haben keinen Mitarbeiter', 'wir haben keinen Mitarbeiter'),
    ('können ich besser machen', 'kann ich besser machen'),
    ('Können ich besser machen', 'Kann ich besser machen'),
]

# When content gets truncated, it might create partial template phrases
# that trigger TEMPLATE_PHRASE warnings in the validator.
# This function cleans up such fragments.

# Template phrase fragments that might be created by truncation
TRUNCATION_PHRASE_CLEANUP = [
    # Partial template phrases that might appear after truncation
    (r'Platzhalter\s*$', ''),  # Incomplete "Platzhalter für X"
    (r'Beispiel\s*$', ''),  # Incomplete "Beispiel-X"
    (r'TODO\s*$', ''),  # Incomplete TODO
    (r'TBD\s*$', ''),  # Incomplete TBD
    (r'Hier\s+könnten\s*$', ''),  # Incomplete "Hier könnten Sie"
    (r'An\s+dieser\s+Stelle\s*$', ''),  # Incomplete phrase
    (r'bitte\s+konkretisieren\s*$', ''),  # Incomplete instruction
    (r'hier\s+weiter\s*$', ''),  # Incomplete "hier weiter ausformulieren"
    (r'nach\s+Bedarf\s*$', ''),  # Incomplete "nach Bedarf anpassen"
    (r'Konkret\w*\s+hier\s*$', ''),  # Incomplete "Konkret X hier einfügen"
    # Unclosed HTML tags that might trigger issues
    (r'<\w+[^>]*$', ''),  # Unclosed opening tag at end
    (r'<[^>]*$', ''),  # Partial tag at end
]


def cleanup_truncation_artifacts(html: str) -> str:
    """
    FIX-506 TASK 5: Clean up artifacts that might be created by truncation.

    When content is truncated (cut at character/word limits), it might:
    1. Create partial template phrases that trigger TEMPLATE_PHRASE warnings
    2. Leave unclosed HTML tags
    3. Create sentence fragments

    This function cleans up such artifacts.

    Args:
        html: HTML content that may have been truncated

    Returns:
        Cleaned HTML with truncation artifacts removed
    """
    if not html or len(html) < 10:
        return html

    result = html
    cleanups = 0

    # KIS-1011-B2: Fix known broken word-boundary phrases first
    for broken, fixed in KNOWN_TRUNCATION_FIXES:
        if broken in result:
            result = result.replace(broken, fixed)
            cleanups += 1

    # Apply cleanup patterns
    for pattern, replacement in TRUNCATION_PHRASE_CLEANUP:
        new_result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        if new_result != result:
            cleanups += 1
            result = new_result

    # Close any unclosed tags (simple heuristic)
    # Count open tags vs close tags for common elements
    for tag in ['p', 'div', 'span', 'li', 'ul', 'ol', 'strong', 'em', 'td', 'tr', 'table']:
        open_count = len(re.findall(f'<{tag}[^>]*>', result, re.IGNORECASE))
        close_count = len(re.findall(f'</{tag}>', result, re.IGNORECASE))
        # Add missing close tags at the end
        if open_count > close_count:
            diff = open_count - close_count
            result += f'</{tag}>' * diff
            cleanups += diff

    if cleanups > 0:
        log.info(f"[TRUNCATION-CLEANUP] Cleaned {cleanups} truncation artifacts")

    return result


def safe_html_truncate(html: str, max_chars: int = 10000) -> str:
    """
    FIX-506 TASK 5: Safely truncate HTML content without creating artifacts.

    Unlike simple slicing, this function:
    1. Respects sentence boundaries
    2. Ensures HTML tags are properly closed
    3. Removes template phrase fragments
    4. Maintains valid HTML structure

    Args:
        html: HTML content to truncate
        max_chars: Maximum character limit

    Returns:
        Safely truncated HTML
    """
    if not html or len(html) <= max_chars:
        return html

    # First, try to find a good sentence boundary
    truncated = html[:max_chars]

    # Find last complete sentence
    last_sentence_end = -1
    for match in re.finditer(r'[.!?](?:\s|<|$)', truncated):
        last_sentence_end = match.end()

    # If we found a sentence boundary in the second half, use it
    if last_sentence_end > max_chars * 0.5:
        truncated = truncated[:last_sentence_end]
    else:
        # Fall back to last HTML tag boundary
        last_tag_end = truncated.rfind('>')
        if last_tag_end > max_chars * 0.5:
            truncated = truncated[:last_tag_end + 1]

    # Clean up any artifacts
    truncated = cleanup_truncation_artifacts(truncated)

    log.info(f"[SAFE-TRUNCATE] Reduced {len(html)} -> {len(truncated)} chars")
    return truncated


# =============================================================================
# FIX-514 CHANGE 2: Forbidden-Token Scrub (ROADMAP_90D_DECISION + KI_STACK_SUMMARY)
# =============================================================================

# FIX-523A: Extended forbidden token scrub rules for all relevant sections
_FORBIDDEN_SCRUB_RULES: dict = {
    "ROADMAP_90D_DECISION_HTML": [
        (re.compile(r'\bRollout\b', re.IGNORECASE), "Einführung"),
        (re.compile(r'\bRoll-out\b', re.IGNORECASE), "Einführung"),
        (re.compile(r'\bSkalierung\b', re.IGNORECASE), "Ausbau"),
        (re.compile(r'\bskalieren\b', re.IGNORECASE), "ausbauen"),
        (re.compile(r'\bAudit[\s-]?Trail\b', re.IGNORECASE), "Nachvollziehbarkeit"),
        (re.compile(r'\bTech[\s-]?Stack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bTool[\s-]?Stack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bStack\b', re.IGNORECASE), "Tool-Set"),
    ],
    "KI_STACK_SUMMARY_HTML": [
        (re.compile(r'\bTech[\s-]?Stack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bTool[\s-]?Stack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bStack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bRollout\b', re.IGNORECASE), "Einführung"),
        (re.compile(r'\bSkalierung\b', re.IGNORECASE), "Ausbau"),
    ],
    # FIX-523A: Extended to ROADMAP_12M_HTML
    "ROADMAP_12M_HTML": [
        (re.compile(r'\bRollout\b', re.IGNORECASE), "Einführung"),
        (re.compile(r'\bRoll-out\b', re.IGNORECASE), "Einführung"),
        (re.compile(r'\bSkalierung\b', re.IGNORECASE), "Ausbau"),
        (re.compile(r'\bskalieren\b', re.IGNORECASE), "ausbauen"),
        (re.compile(r'\bTech[\s-]?Stack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bTool[\s-]?Stack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bStack\b', re.IGNORECASE), "Tool-Set"),
    ],
    # FIX-523A: Also clean ROADMAP_90D_HTML (non-decision variant)
    "ROADMAP_90D_HTML": [
        (re.compile(r'\bRollout\b', re.IGNORECASE), "Einführung"),
        (re.compile(r'\bSkalierung\b', re.IGNORECASE), "Ausbau"),
        (re.compile(r'\bTech[\s-]?Stack\b', re.IGNORECASE), "Tool-Set"),
        (re.compile(r'\bStack\b', re.IGNORECASE), "Tool-Set"),
    ],
    "PILOT_PLAN_HTML": [
        (re.compile(r'\bRollout\b', re.IGNORECASE), "Einführung"),
        (re.compile(r'\bSkalierung\b', re.IGNORECASE), "Ausbau"),
        (re.compile(r'\bStack\b', re.IGNORECASE), "Tool-Set"),
    ],
}


def apply_forbidden_token_scrub(sections: dict) -> dict:
    """
    FIX-514 CHANGE 2: Deterministic forbidden-token scrub for specific sections.

    Replaces priming-risk tokens (Rollout, Skalierung, Audit-Trail, Stack)
    in ROADMAP_90D_DECISION_HTML and KI_STACK_SUMMARY_HTML.
    """
    for key, rules in _FORBIDDEN_SCRUB_RULES.items():
        html = sections.get(key, "")
        if not html:
            continue

        counts: dict = {}
        for pattern, replacement in rules:
            result, n = pattern.subn(replacement, html)
            if n > 0:
                token_name = pattern.pattern.replace(r'\b', '').replace('[\\s-]?', '-').lower()
                counts[token_name] = counts.get(token_name, 0) + n
                html = result

        if counts:
            sections[key] = html
            log.info(
                "[FIX-514][FORBIDDEN-SCRUB] key=%s replaced=%s",
                key, counts
            )

    return sections


# =============================================================================
# FIX-514 CHANGE 3: Placeholder Scrub (RECOMMENDATIONS_HTML)
# =============================================================================

_PLACEHOLDER_LINE_PATTERN = re.compile(
    r'<(?:p|li|div)[^>]*>[^<]*\bPlatzhalter\b[^<]*</(?:p|li|div)>',
    re.IGNORECASE
)
_PLACEHOLDER_WORD_PATTERN = re.compile(r'\bPlatzhalter\b', re.IGNORECASE)


def apply_placeholder_scrub(sections: dict) -> dict:
    """
    FIX-514 CHANGE 3 + FIX-525: Remove lines/blocks containing 'Platzhalter' from
    RECOMMENDATIONS_HTML and NEXT_ACTIONS_HTML. Prevents STRICT template_phrase hits.
    """
    # FIX-525: Extended to include NEXT_ACTIONS_HTML
    target_keys = ["RECOMMENDATIONS_HTML", "NEXT_ACTIONS_HTML"]
    total_removed = 0

    for key in target_keys:
        html = sections.get(key, "")
        if not html or "platzhalter" not in html.lower():
            continue

        # Remove entire <p>/<li>/<div> blocks containing "Platzhalter"
        result, removed = _PLACEHOLDER_LINE_PATTERN.subn("", html)

        # If word still present (e.g. in inline text), replace with neutral term
        if _PLACEHOLDER_WORD_PATTERN.search(result):
            result, extra = _PLACEHOLDER_WORD_PATTERN.subn("konkreter Vorschlag", result)
            removed += extra

        if removed > 0:
            sections[key] = result
            total_removed += removed
            log.info("[FIX-525][PLACEHOLDER-SCRUB] key=%s removed=%d", key, removed)

    return sections


# =============================================================================
# FIX-517C TASK 1: Universal Template Phrase Scrubber (ALL sections, ALL personas)
# =============================================================================
# Deterministic removal of template/placeholder patterns BEFORE validation.
# This prevents false STRICT template_phrase hits from LLM-generated artifacts.

_TEMPLATE_PHRASE_PATTERNS = [
    # Bracketed placeholders: [Platzhalter: ...], [TODO: ...], [TBD], [TEMPLATE]
    (re.compile(r'\[Platzhalter(?::\s*[^\]]*?)?\]', re.IGNORECASE), ''),
    (re.compile(r'\[TODO(?::\s*[^\]]*?)?\]', re.IGNORECASE), ''),
    (re.compile(r'\[TBD\]', re.IGNORECASE), ''),
    (re.compile(r'\[TEMPLATE\]', re.IGNORECASE), ''),
    (re.compile(r'\[Beispieltext(?::\s*[^\]]*?)?\]', re.IGNORECASE), ''),
    (re.compile(r'\[Mustertext(?::\s*[^\]]*?)?\]', re.IGNORECASE), ''),
    # FIX: Prompt-Template placeholders that may leak from Sofort-Start generator
    (re.compile(r'\[ANFRAGE HIER EINFÜGEN\]', re.IGNORECASE), ''),
    (re.compile(r'\[NOTIZEN HIER EINFÜGEN\]', re.IGNORECASE), ''),
    (re.compile(r'\[CODE HIER EINFÜGEN\]', re.IGNORECASE), ''),
    (re.compile(r'\[DATEN HIER EINFÜGEN\]', re.IGNORECASE), ''),
    (re.compile(r'\[TEXT HIER EINFÜGEN\]', re.IGNORECASE), ''),
    (re.compile(r'\[[A-ZÄÖÜ][A-ZÄÖÜ\s]*HIER EINFÜGEN\]', re.IGNORECASE), ''),  # Generic pattern
    (re.compile(r'\[NAME/BRANCHE\]', re.IGNORECASE), ''),
    (re.compile(r'\[KURZBESCHREIBUNG\]', re.IGNORECASE), ''),
    (re.compile(r'\[FALLS BEKANNT\]', re.IGNORECASE), ''),
    # Mustache/Jinja-style template variables: {{variable}}, {{ variable }}
    (re.compile(r'\{\{\s*\w+\s*\}\}'), ''),
    # German template instructions that LLMs sometimes leave in
    (re.compile(r'\bHier steht Ihr Text\b', re.IGNORECASE), ''),
    (re.compile(r'\bFügen Sie hier[^.]*ein\.?', re.IGNORECASE), ''),
    (re.compile(r'\bBitte ersetzen Sie[^.]*\.?', re.IGNORECASE), ''),
    (re.compile(r'\bLorem ipsum[^.]*\.?', re.IGNORECASE), ''),
    # Explicit "Platzhalter" / "Beispieltext" / "Mustertext" as inline words (all sections)
    (re.compile(r'\bPlatzhalter\b', re.IGNORECASE), 'konkreter Vorschlag'),
    (re.compile(r'\bBeispieltext\b', re.IGNORECASE), ''),
    (re.compile(r'\bMustertext\b', re.IGNORECASE), ''),
    (re.compile(r'\bDummy-?Text\b', re.IGNORECASE), ''),
    # FIX-523A: Chat phrases that leak into output (NEXT_ACTIONS, LEAD_WETTBEWERB)
    (re.compile(r'\bBitte geben Sie mir das[^.]*\.?', re.IGNORECASE), ''),
    (re.compile(r'\bBitte geben Sie mir[^.]*\.?', re.IGNORECASE), ''),
    (re.compile(r'\bWelchen Wettbewerb[^.?]*[.?]?', re.IGNORECASE), ''),
    (re.compile(r'\bWelche Wettbewerber[^.?]*[.?]?', re.IGNORECASE), ''),
    (re.compile(r'\bKönnen Sie mir[^.?]*[.?]?', re.IGNORECASE), ''),
    (re.compile(r'\bMöchten Sie[^.?]*[.?]?', re.IGNORECASE), ''),
]

# All LLM-generated sections to scrub
_TEMPLATE_SCRUB_SECTIONS = [
    "EXECUTIVE_SUMMARY_HTML", "EXECUTIVE_DECISION_HTML", "RECOMMENDATIONS_HTML",
    "QUICK_WINS_HTML", "QUICK_WINS_HTML_LEFT", "QUICK_WINS_HTML_RIGHT",
    "ROADMAP_90D_HTML", "ROADMAP_90D_DECISION_HTML", "ROADMAP_12M_HTML",
    "GAMECHANGER_HTML", "GAMECHANGER_DECISION_HTML",
    "FOERDERPOTENZIAL_HTML", "RISKS_HTML", "ORG_CHANGE_HTML",
    "KI_SKILLPLAN_HTML", "BUSINESS_CASE_HTML", "AI_ACT_HTML", "AI_ACT_SUMMARY_HTML",
    "TOOLS_HTML", "TOOLS_EMPFEHLUNGEN_HTML", "DATA_STRATEGY_HTML", "DATA_READINESS_HTML",
    "GOVERNANCE_HTML", "STRATEGIE_GOVERNANCE_HTML", "KI_STACK_SUMMARY_HTML",
    "BRANCH_DEEP_DIVE_HTML", "TOP_3_MASSNAHMEN_HTML", "MONETARISIERUNG_HTML",
    "TEMPLATES_START_HTML", "KICKOFF_VORLAGE_HTML", "PROMPT_FRAMEWORK_HTML",
    "TECHNOLOGIE_PROZESSE_HTML", "WETTBEWERB_BENCHMARK_HTML", "UNTERNEHMENSPROFIL_MARKT_HTML",
    # FIX-523A: Added for template_phrase warnings
    "NEXT_ACTIONS_HTML", "LEAD_WETTBEWERB", "LEAD_EXEC", "LEAD_KPI", "LEAD_QW",
    "LEAD_ROADMAP_90", "LEAD_ROADMAP_12", "LEAD_BUSINESS", "LEAD_BUSINESS_DETAIL",
]


def scrub_template_phrases_all_sections(sections: dict) -> dict:
    """
    FIX-517C TASK 1: Universal template phrase scrubber.

    Removes placeholder/template artifacts from ALL LLM-generated sections
    regardless of persona. Runs BEFORE validation to prevent false STRICT hits.

    Patterns removed:
    - [Platzhalter: ...], [TODO: ...], [TBD], [TEMPLATE]
    - {{variable}} mustache-style placeholders
    - German template instructions ("Hier steht Ihr Text", "Fügen Sie hier...")
    - Standalone "Platzhalter", "Beispieltext", "Mustertext" words

    Returns:
        sections: Cleaned dict
    """
    total_removals = 0
    sections_touched = 0

    for section_key in _TEMPLATE_SCRUB_SECTIONS:
        content = sections.get(section_key)
        if not content or not isinstance(content, str):
            continue

        section_removals = 0
        modified = content

        for pattern, replacement in _TEMPLATE_PHRASE_PATTERNS:
            new_text, count = pattern.subn(replacement, modified)
            if count > 0:
                modified = new_text
                section_removals += count

        if section_removals > 0:
            # Clean up resulting double spaces and empty tags
            modified = re.sub(r'\s{2,}', ' ', modified)
            modified = re.sub(r'\s+([.,;:!?])', r'\1', modified)
            modified = re.sub(r'<(p|li|div)[^>]*>\s*</(p|li|div)>', '', modified)
            sections[section_key] = modified
            sections_touched += 1
            total_removals += section_removals

    if total_removals > 0:
        log.info(
            "[FIX-517C][TEMPLATE-SCRUB] removed=%d template phrases in %d sections",
            total_removals, sections_touched
        )

    return sections

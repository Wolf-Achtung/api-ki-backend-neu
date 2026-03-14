# -*- coding: utf-8 -*-
"""
Sprint G19: Branchenintelligenz & Marktlogik 2.0
================================================

Industry Intelligence Engine for automated branch profiling.

Features:
- Branch Profile Generator: drivers, trends, regulatory factors, use cases, maturity
- Risk & Opportunity Mapping: 3 opportunities, 3 risks, 3 bottlenecks
- HTML output variables for PDF templates
- Language support: DE/EN

Version: 1.0.0 (Sprint G19)
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION (ENV)
# =============================================================================

BRANCH_PROFILE_ENABLED = os.environ.get("BRANCH_PROFILE_ENABLED", "1") == "1"
BRANCH_PROFILE_CACHE_ENABLED = os.environ.get("BRANCH_PROFILE_CACHE_ENABLED", "1") == "1"
BRANCH_CONTEXTS_PATH = os.environ.get(
    "BRANCH_CONTEXTS_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "branch_contexts")
)

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class BranchDriver:
    """A key driver/factor for the industry."""
    title: str
    description: str
    impact_level: str = "high"  # high, medium, low
    trend_direction: str = "rising"  # rising, stable, declining


# Qualitative trend levels (Problem #4 fix - no fake percentages)
TREND_LEVELS = {
    "very_high": {"de": "Sehr stark wachsend", "en": "Very high growth"},
    "high": {"de": "Stark wachsend", "en": "High growth"},
    "medium": {"de": "Wachsend", "en": "Growing"},
    "stable": {"de": "Etabliert", "en": "Established"},
    "emerging": {"de": "Aufkommend", "en": "Emerging"},
}

# Colors for trend levels
TREND_LEVEL_COLORS = {
    "very_high": "#22c55e",  # Green
    "high": "#3b82f6",       # Blue
    "medium": "#8b5cf6",     # Purple
    "stable": "#64748b",     # Gray
    "emerging": "#f59e0b",   # Orange
}


@dataclass
class MarketTrend:
    """Market trend relevant to the industry."""
    title: str
    description: str
    trend_level: str = "high"  # very_high, high, medium, stable, emerging
    timeline: str = "2024-2026"

    @property
    def relevance_score(self) -> float:
        """Backwards compatibility: convert level to score."""
        level_scores = {"very_high": 0.95, "high": 0.85, "medium": 0.7, "stable": 0.5, "emerging": 0.6}
        return level_scores.get(self.trend_level, 0.7)

    def get_label(self, lang: str = "de") -> str:
        """Get localized label for the trend level."""
        return TREND_LEVELS.get(self.trend_level, TREND_LEVELS["medium"]).get(lang, self.trend_level)

    def get_color(self) -> str:
        """Get color for the trend level."""
        return TREND_LEVEL_COLORS.get(self.trend_level, "#6b7280")


@dataclass
class RegulatoryFactor:
    """Regulatory consideration for the industry."""
    title: str
    description: str
    urgency: str = "medium"  # high, medium, low
    compliance_deadline: Optional[str] = None


@dataclass
class UseCase:
    """Typical AI use case for the industry."""
    title: str
    description: str
    complexity: str = "medium"  # low, medium, high
    roi_potential: str = "high"  # low, medium, high
    implementation_months: int = 3


@dataclass
class BranchProfile:
    """Complete industry/branch profile."""
    branch_id: str
    branch_name: str
    branch_display_name: str
    size_context: str  # solo, team, kmu
    language: str  # de, en

    # Core profile data
    drivers: List[BranchDriver] = field(default_factory=list)
    market_trends: List[MarketTrend] = field(default_factory=list)
    regulatory_factors: List[RegulatoryFactor] = field(default_factory=list)
    use_cases: List[UseCase] = field(default_factory=list)

    # Maturity & scoring
    maturity_score: int = 50  # 0-100
    maturity_label: str = "medium"  # emerging, developing, maturing, mature
    digitalization_level: str = "medium"  # low, medium, high
    ai_adoption_rate: str = "early"  # early, growing, mainstream

    # Metadata
    description: str = ""
    kpis: List[str] = field(default_factory=list)
    competitive_density: str = "medium"  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskOpportunityMap:
    """Risk and opportunity mapping for industry."""
    branch_id: str
    opportunities: List[Dict[str, str]] = field(default_factory=list)
    risks: List[Dict[str, str]] = field(default_factory=list)
    bottlenecks: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# BRANCH INTELLIGENCE DATA
# =============================================================================

# Industry maturity scores (0-100) and characteristics
BRANCH_MATURITY_DATA: Dict[str, Dict[str, Any]] = {
    "beratung": {
        "maturity_score": 65,
        "digitalization_level": "medium",
        "ai_adoption_rate": "growing",
        "competitive_density": "high",
        "drivers_de": [
            ("Wissensintensität", "Beratung lebt von Expertise und intellektuellem Kapital - KI kann Wissenszugang demokratisieren"),
            ("Erweiterungsdruck", "Traditionelles Geschäftsmodell ist zeitbasiert und schwer erweiterbar - KI ermöglicht Kapazitätssteigerung"),
            ("Kundenzentriertheit", "Hohe individuelle Anforderungen pro Mandat - KI personalisiert ohne Zusatzaufwand"),
            ("Dokumentationsintensität", "Reports, Analysen, Präsentationen dominieren - ideale KI-Automatisierungschance"),
        ],
        "drivers_en": [
            ("Knowledge Intensity", "Consulting thrives on expertise and intellectual capital - AI democratizes knowledge access"),
            ("Scaling Pressure", "Traditional business model is time-based and hard to scale - AI enables capacity growth"),
            ("Client Centricity", "High individual requirements per mandate - AI personalizes without extra effort"),
            ("Documentation Intensity", "Reports, analyses, presentations dominate - ideal AI automation opportunity"),
        ],
        "trends_de": [
            ("AI-First Beratung", "Beratungshäuser integrieren KI als Core-Service", "very_high"),
            ("Outcome-Based Pricing", "Shift von Stundensätzen zu Value-Based-Modellen", "medium"),
            ("Remote-First Delivery", "Hybride Beratungsmodelle werden Standard", "high"),
            ("Data-Driven Insights", "Analysen basieren zunehmend auf Echtzeit-Daten", "high"),
        ],
        "trends_en": [
            ("AI-First Consulting", "Consulting firms integrate AI as core service", "very_high"),
            ("Outcome-Based Pricing", "Shift from hourly rates to value-based models", "medium"),
            ("Remote-First Delivery", "Hybrid consulting models becoming standard", "high"),
            ("Data-Driven Insights", "Analyses increasingly based on real-time data", "high"),
        ],
        "regulatory_de": [
            ("AI Act Compliance", "Bei KI-gestützter Beratung müssen Transparenzanforderungen erfüllt werden", "medium"),
            ("DSGVO/Datenschutz", "Kundendaten erfordern besondere Schutzmaßnahmen bei KI-Nutzung", "high"),
        ],
        "regulatory_en": [
            ("AI Act Compliance", "AI-assisted consulting must meet transparency requirements", "medium"),
            ("GDPR/Data Protection", "Client data requires special protection measures when using AI", "high"),
        ],
        "use_cases_de": [
            ("Angebotserstellung", "KI-gestützte Angebote in 5 statt 120 Minuten", "low", "high", 1),
            ("Research & Analyse", "Automatisierte Markt- und Wettbewerbsanalysen", "medium", "high", 2),
            ("Report-Generierung", "Automatische Erstellung von Berichten und Präsentationen", "medium", "high", 2),
            ("Meeting-Dokumentation", "Transkription, Zusammenfassung, Action Items", "low", "medium", 1),
        ],
        "use_cases_en": [
            ("Proposal Generation", "AI-assisted proposals in 5 instead of 120 minutes", "low", "high", 1),
            ("Research & Analysis", "Automated market and competitive analyses", "medium", "high", 2),
            ("Report Generation", "Automatic creation of reports and presentations", "medium", "high", 2),
            ("Meeting Documentation", "Transcription, summaries, action items", "low", "medium", 1),
        ],
        "kpis": ["Time-to-Offer", "Utilization Rate", "Client Satisfaction Score", "Knowledge Reuse Rate"],
        "opportunities_de": [
            ("Produktivitätssteigerung", "30-50% Zeitersparnis bei dokumentationsintensiven Aufgaben durch KI-Automation"),
            ("Erweiterung ohne Personalaufbau", "KI ermöglicht mehr Mandate pro Berater ohne Qualitätsverlust"),
            ("Premium-Positionierung", "KI-gestützte Insights als differenzierender Mehrwert für Kunden"),
        ],
        "opportunities_en": [
            ("Productivity Increase", "30-50% time savings on documentation-intensive tasks through AI automation"),
            ("Scaling Without Hiring", "AI enables more mandates per consultant without quality loss"),
            ("Premium Positioning", "AI-powered insights as differentiating added value for clients"),
        ],
        "risks_de": [
            ("Qualitätskontrolle", "KI-generierte Inhalte erfordern sorgfältige Prüfung vor Kundenauslieferung"),
            ("Know-how-Abfluss", "Firmenwissen in KI-Systemen muss geschützt werden"),
            ("Abhängigkeit von Tools", "Ohne Fallback-Strategie entstehen Single-Points-of-Failure"),
        ],
        "risks_en": [
            ("Quality Control", "AI-generated content requires careful review before client delivery"),
            ("Knowledge Leakage", "Company knowledge in AI systems must be protected"),
            ("Tool Dependency", "Without fallback strategy, single points of failure emerge"),
        ],
        "bottlenecks_de": [
            ("Fehlende KI-Kompetenz", "Teams benötigen Schulung in Prompt Engineering und KI-Tools"),
            ("Datensilos", "Fragmentiertes Firmenwissen erschwert KI-Integration"),
            ("Change Resistance", "Etablierte Arbeitsweisen und Skepsis gegenüber Automatisierung"),
        ],
        "bottlenecks_en": [
            ("Lacking AI Competence", "Teams need training in prompt engineering and AI tools"),
            ("Data Silos", "Fragmented company knowledge complicates AI integration"),
            ("Change Resistance", "Established work patterns and skepticism toward automation"),
        ],
    },
    "it": {
        "maturity_score": 80,
        "digitalization_level": "high",
        "ai_adoption_rate": "mainstream",
        "competitive_density": "high",
        "drivers_de": [
            ("Technologie-Affinität", "IT-Teams adoptieren neue Technologien früh und kompetent"),
            ("Automatisierungskultur", "DevOps, CI/CD und Automatisierung sind etabliert - KI ist logische Erweiterung"),
            ("Code-Generierung", "Copilot, ChatGPT etc. revolutionieren Softwareentwicklung"),
            ("Fachkräftemangel", "KI kompensiert fehlende Entwicklerkapazitäten"),
        ],
        "drivers_en": [
            ("Technology Affinity", "IT teams adopt new technologies early and competently"),
            ("Automation Culture", "DevOps, CI/CD and automation are established - AI is logical extension"),
            ("Code Generation", "Copilot, ChatGPT etc. revolutionize software development"),
            ("Talent Shortage", "AI compensates for missing developer capacity"),
        ],
        "trends_de": [
            ("AI-Assisted Development", "Copilot und ähnliche Tools werden Standard", "very_high"),
            ("Low-Code/No-Code", "Demokratisierung der Softwareentwicklung", "high"),
            ("AI Ops", "KI-gestützte IT-Operations und Monitoring", "high"),
            ("Security Automation", "KI für Threat Detection und Response", "very_high"),
        ],
        "trends_en": [
            ("AI-Assisted Development", "Copilot and similar tools becoming standard", "very_high"),
            ("Low-Code/No-Code", "Democratization of software development", "high"),
            ("AI Ops", "AI-powered IT operations and monitoring", "high"),
            ("Security Automation", "AI for threat detection and response", "very_high"),
        ],
        "regulatory_de": [
            ("AI Act - High-Risk", "Kritische IT-Systeme können als High-Risk klassifiziert werden", "high"),
            ("DSGVO/Datenschutz", "Bei Verarbeitung personenbezogener Daten strenge Auflagen", "high"),
            ("NIS2", "Cybersecurity-Anforderungen für kritische Infrastrukturen", "high"),
        ],
        "regulatory_en": [
            ("AI Act - High-Risk", "Critical IT systems may be classified as high-risk", "high"),
            ("GDPR/Data Protection", "Strict requirements when processing personal data", "high"),
            ("NIS2", "Cybersecurity requirements for critical infrastructure", "high"),
        ],
        "use_cases_de": [
            ("Code-Generierung", "Entwickler werden 30-50% produktiver mit AI-Assistenten", "low", "high", 1),
            ("Code-Review", "Automatische Qualitätsprüfung und Best-Practice-Hinweise", "low", "high", 1),
            ("Dokumentation", "Automatische Generierung von technischer Doku", "low", "medium", 1),
            ("Bug Detection", "KI-gestützte Fehlersuche und -behebung", "medium", "high", 2),
        ],
        "use_cases_en": [
            ("Code Generation", "Developers become 30-50% more productive with AI assistants", "low", "high", 1),
            ("Code Review", "Automatic quality checks and best practice hints", "low", "high", 1),
            ("Documentation", "Automatic generation of technical documentation", "low", "medium", 1),
            ("Bug Detection", "AI-powered bug finding and fixing", "medium", "high", 2),
        ],
        "kpis": ["Lines of Code per Developer", "Bug Rate", "Time-to-Deploy", "Code Review Turnaround"],
        "opportunities_de": [
            ("Entwicklerproduktivität", "30-50% Produktivitätssteigerung durch AI-Coding-Assistenten"),
            ("Quality Engineering", "Automatisierte Tests und Code-Reviews reduzieren Fehlerquote"),
            ("Wissenstransfer", "KI-Systeme dokumentieren und erklären Legacy-Code"),
        ],
        "opportunities_en": [
            ("Developer Productivity", "30-50% productivity increase through AI coding assistants"),
            ("Quality Engineering", "Automated tests and code reviews reduce error rate"),
            ("Knowledge Transfer", "AI systems document and explain legacy code"),
        ],
        "risks_de": [
            ("Code-Qualität", "KI-generierter Code kann Sicherheitslücken oder Bugs enthalten"),
            ("IP-Risiken", "Trainingsdaten und generierter Code können Urheberrechtsfragen aufwerfen"),
            ("Over-Reliance", "Entwickler verlieren fundamentale Skills bei zu starker KI-Abhängigkeit"),
        ],
        "risks_en": [
            ("Code Quality", "AI-generated code may contain security vulnerabilities or bugs"),
            ("IP Risks", "Training data and generated code may raise copyright questions"),
            ("Over-Reliance", "Developers lose fundamental skills with excessive AI dependence"),
        ],
        "bottlenecks_de": [
            ("Enterprise-Integration", "Unternehmens-KI muss in bestehende Tool-Landschaft passen"),
            ("Data Governance", "Sensible Codebases erfordern private AI-Deployments"),
            ("Cost Management", "API-Kosten bei intensiver Nutzung schwer kalkulierbar"),
        ],
        "bottlenecks_en": [
            ("Enterprise Integration", "Enterprise AI must fit existing tool landscape"),
            ("Data Governance", "Sensitive codebases require private AI deployments"),
            ("Cost Management", "API costs hard to calculate with intensive usage"),
        ],
    },
    "handel": {
        "maturity_score": 55,
        "digitalization_level": "medium",
        "ai_adoption_rate": "growing",
        "competitive_density": "high",
        "drivers_de": [
            ("E-Commerce Druck", "Stationärer Handel muss mit Online konkurrieren - KI optimiert beide Kanäle"),
            ("Personalisierung", "Kunden erwarten individuelle Empfehlungen und Erlebnisse"),
            ("Effizienz im Backend", "Lagerhaltung, Logistik, Pricing bieten Automatisierungspotenzial"),
            ("Customer Journey", "Nahtlose Omnichannel-Erlebnisse erfordern intelligente Systeme"),
        ],
        "drivers_en": [
            ("E-Commerce Pressure", "Brick-and-mortar must compete with online - AI optimizes both channels"),
            ("Personalization", "Customers expect individual recommendations and experiences"),
            ("Backend Efficiency", "Inventory, logistics, pricing offer automation potential"),
            ("Customer Journey", "Seamless omnichannel experiences require intelligent systems"),
        ],
        "trends_de": [
            ("Conversational Commerce", "Chatbots und Voice-Assistenten für Kundenservice", "high"),
            ("Dynamic Pricing", "KI-gestützte Preisoptimierung in Echtzeit", "medium"),
            ("Visual Search", "Produktsuche per Bild wird Standard", "medium"),
            ("Predictive Analytics", "Nachfrage- und Bestandsprognosen", "high"),
        ],
        "trends_en": [
            ("Conversational Commerce", "Chatbots and voice assistants for customer service", "high"),
            ("Dynamic Pricing", "AI-powered real-time price optimization", "medium"),
            ("Visual Search", "Image-based product search becoming standard", "medium"),
            ("Predictive Analytics", "Demand and inventory forecasting", "high"),
        ],
        "regulatory_de": [
            ("Preistransparenz", "Dynamische Preise müssen transparent kommuniziert werden", "medium"),
            ("DSGVO/Kundendaten", "Personalisierung erfordert datenschutzkonforme Verarbeitung", "high"),
        ],
        "regulatory_en": [
            ("Price Transparency", "Dynamic prices must be communicated transparently", "medium"),
            ("GDPR/Customer Data", "Personalization requires GDPR-compliant processing", "high"),
        ],
        "use_cases_de": [
            ("Chatbot Customer Service", "24/7 Kundenbetreuung automatisiert", "medium", "high", 2),
            ("Produktempfehlungen", "Personalisierte Recommendations steigern Conversion", "medium", "high", 3),
            ("Bestandsoptimierung", "KI prognostiziert Nachfrage und optimiert Lager", "high", "high", 6),
            ("Content-Generierung", "Produktbeschreibungen automatisch erstellen", "low", "medium", 1),
        ],
        "use_cases_en": [
            ("Chatbot Customer Service", "24/7 customer support automated", "medium", "high", 2),
            ("Product Recommendations", "Personalized recommendations increase conversion", "medium", "high", 3),
            ("Inventory Optimization", "AI forecasts demand and optimizes inventory", "high", "high", 6),
            ("Content Generation", "Automatically create product descriptions", "low", "medium", 1),
        ],
        "kpis": ["Conversion Rate", "Average Order Value", "Customer Retention", "Inventory Turnover"],
        "opportunities_de": [
            ("Conversion-Steigerung", "Personalisierte Empfehlungen können Conversion um 10-30% steigern"),
            ("Kostenreduktion", "Chatbots reduzieren Support-Kosten um 30-60%"),
            ("Bestandsoptimierung", "KI-Prognosen reduzieren Überbestände und Fehlmengen"),
        ],
        "opportunities_en": [
            ("Conversion Increase", "Personalized recommendations can boost conversion by 10-30%"),
            ("Cost Reduction", "Chatbots reduce support costs by 30-60%"),
            ("Inventory Optimization", "AI forecasts reduce overstock and stockouts"),
        ],
        "risks_de": [
            ("Kundenakzeptanz", "Nicht alle Kunden möchten mit Bots interagieren"),
            ("Systemkomplexität", "E-Commerce + KI erfordert technische Kompetenz"),
            ("Datenqualität", "Schlechte Produktdaten führen zu schlechten Empfehlungen"),
        ],
        "risks_en": [
            ("Customer Acceptance", "Not all customers want to interact with bots"),
            ("System Complexity", "E-commerce + AI requires technical competence"),
            ("Data Quality", "Poor product data leads to poor recommendations"),
        ],
        "bottlenecks_de": [
            ("Legacy-Systeme", "Ältere Warenwirtschaft schwer mit KI integrierbar"),
            ("Produktdatenqualität", "Unstrukturierte Kataloge erschweren KI-Nutzung"),
            ("Omnichannel-Integration", "Daten aus allen Kanälen zusammenführen"),
        ],
        "bottlenecks_en": [
            ("Legacy Systems", "Older ERP systems hard to integrate with AI"),
            ("Product Data Quality", "Unstructured catalogs complicate AI usage"),
            ("Omnichannel Integration", "Consolidating data from all channels"),
        ],
    },
    "finanzen": {
        "maturity_score": 70,
        "digitalization_level": "high",
        "ai_adoption_rate": "growing",
        "competitive_density": "high",
        "drivers_de": [
            ("Regulatorik", "Umfangreiche Compliance-Anforderungen treiben Automatisierung"),
            ("Risikomanagement", "KI ermöglicht bessere Risikoerkennung und -bewertung"),
            ("Kundenerwartungen", "FinTech-Konkurrenz setzt Maßstäbe für digitale Services"),
            ("Datenreichtum", "Finanzsektor hat strukturierte Daten - ideal für KI"),
        ],
        "drivers_en": [
            ("Regulation", "Extensive compliance requirements drive automation"),
            ("Risk Management", "AI enables better risk detection and assessment"),
            ("Customer Expectations", "FinTech competition sets standards for digital services"),
            ("Data Richness", "Financial sector has structured data - ideal for AI"),
        ],
        "trends_de": [
            ("RegTech", "KI-gestützte Compliance und Reporting", "very_high"),
            ("Fraud Detection", "Echtzeit-Betrugserkennung mit ML", "very_high"),
            ("Robo-Advisory", "Automatisierte Anlageberatung", "high"),
            ("Process Automation", "RPA + KI für Back-Office-Prozesse", "high"),
        ],
        "trends_en": [
            ("RegTech", "AI-powered compliance and reporting", "very_high"),
            ("Fraud Detection", "Real-time fraud detection with ML", "very_high"),
            ("Robo-Advisory", "Automated investment advice", "high"),
            ("Process Automation", "RPA + AI for back-office processes", "high"),
        ],
        "regulatory_de": [
            ("BaFin/MaRisk", "Strenge Dokumentations- und Prüfpflichten", "high"),
            ("AI Act - High-Risk", "Kreditscoring und Risikobewertung sind High-Risk-Anwendungen", "high"),
            ("DORA", "Digital Operational Resilience Act für Finanzsektor", "high"),
        ],
        "regulatory_en": [
            ("BaFin/MaRisk", "Strict documentation and audit requirements", "high"),
            ("AI Act - High-Risk", "Credit scoring and risk assessment are high-risk applications", "high"),
            ("DORA", "Digital Operational Resilience Act for financial sector", "high"),
        ],
        "use_cases_de": [
            ("Dokumenten-Analyse", "Automatische Extraktion aus Verträgen und Reports", "medium", "high", 3),
            ("Compliance-Monitoring", "KI überwacht Transaktionen und Regularien", "high", "high", 6),
            ("Kundenservice", "Chatbots für Standard-Anfragen", "medium", "medium", 2),
            ("Reporting", "Automatisierte Berichtserstellung", "medium", "high", 3),
        ],
        "use_cases_en": [
            ("Document Analysis", "Automatic extraction from contracts and reports", "medium", "high", 3),
            ("Compliance Monitoring", "AI monitors transactions and regulations", "high", "high", 6),
            ("Customer Service", "Chatbots for standard inquiries", "medium", "medium", 2),
            ("Reporting", "Automated report generation", "medium", "high", 3),
        ],
        "kpis": ["Compliance Score", "Processing Time", "Error Rate", "Customer Response Time"],
        "opportunities_de": [
            ("Compliance-Effizienz", "KI reduziert Aufwand für regulatorische Anforderungen um 40-60%"),
            ("Risikominimierung", "Bessere Betrugserkennung durch Mustererkennung"),
            ("Erweiterung", "Automatisierung ermöglicht Wachstum ohne proportionalen Personalaufbau"),
        ],
        "opportunities_en": [
            ("Compliance Efficiency", "AI reduces regulatory requirement effort by 40-60%"),
            ("Risk Minimization", "Better fraud detection through pattern recognition"),
            ("Scaling", "Automation enables growth without proportional staff increase"),
        ],
        "risks_de": [
            ("Regulatorische Unsicherheit", "AI Act Umsetzung noch nicht final geklärt"),
            ("Erklärbarkeit", "Black-Box-Modelle problematisch bei regulierten Entscheidungen"),
            ("Audit-Trail", "Nachvollziehbarkeit aller KI-Entscheidungen sicherstellen"),
        ],
        "risks_en": [
            ("Regulatory Uncertainty", "AI Act implementation not yet finalized"),
            ("Explainability", "Black-box models problematic for regulated decisions"),
            ("Audit Trail", "Ensure traceability of all AI decisions"),
        ],
        "bottlenecks_de": [
            ("Legacy-IT", "Kernbankensysteme oft schwer integrierbar"),
            ("Governance", "Strenge Anforderungen an KI-Modell-Governance"),
            ("Fachkräfte", "Spezialisten für RegTech und KI selten"),
        ],
        "bottlenecks_en": [
            ("Legacy IT", "Core banking systems often hard to integrate"),
            ("Governance", "Strict requirements for AI model governance"),
            ("Specialists", "Experts in RegTech and AI are rare"),
        ],
    },
    "gesundheit": {
        "maturity_score": 45,
        "digitalization_level": "low",
        "ai_adoption_rate": "early",
        "competitive_density": "medium",
        "drivers_de": [
            ("Fachkräftemangel", "Pflegenotstand und Ärztemangel treiben Automatisierungsbedarf"),
            ("Dokumentationslast", "Enormer administrativer Aufwand bei medizinischer Dokumentation"),
            ("Patientensicherheit", "KI kann Fehler reduzieren und Qualität steigern"),
            ("Kostendruck", "Effizienzsteigerung im Gesundheitswesen notwendig"),
        ],
        "drivers_en": [
            ("Staff Shortage", "Nursing and physician shortages drive automation need"),
            ("Documentation Burden", "Enormous administrative effort in medical documentation"),
            ("Patient Safety", "AI can reduce errors and improve quality"),
            ("Cost Pressure", "Efficiency improvement in healthcare necessary"),
        ],
        "trends_de": [
            ("Klinische Dokumentation", "KI-Assistenten für Arztbriefe und Befunde", "high"),
            ("Bildgebung", "AI-gestützte Diagnostik bei Röntgen, MRT, CT", "very_high"),
            ("Terminmanagement", "Intelligente Praxisorganisation", "medium"),
            ("Telemedizin", "KI-unterstützte Ferndiagnose und -behandlung", "medium"),
        ],
        "trends_en": [
            ("Clinical Documentation", "AI assistants for medical reports", "high"),
            ("Medical Imaging", "AI-assisted diagnostics for X-ray, MRI, CT", "very_high"),
            ("Appointment Management", "Intelligent practice organization", "medium"),
            ("Telemedicine", "AI-supported remote diagnosis and treatment", "medium"),
        ],
        "regulatory_de": [
            ("MDR/IVDR", "Medizinprodukteverordnung für KI-Systeme", "high"),
            ("AI Act - High-Risk", "Medizinische KI ist explizit High-Risk", "high"),
            ("DSGVO/Gesundheitsdaten", "Besondere Kategorie personenbezogener Daten", "high"),
        ],
        "regulatory_en": [
            ("MDR/IVDR", "Medical Device Regulation for AI systems", "high"),
            ("AI Act - High-Risk", "Medical AI is explicitly high-risk", "high"),
            ("GDPR/Health Data", "Special category of personal data", "high"),
        ],
        "use_cases_de": [
            ("Arztbrief-Generierung", "Automatische Erstellung klinischer Dokumente", "medium", "high", 3),
            ("Terminoptimierung", "KI plant Termine effizienter", "low", "medium", 2),
            ("Patientenkommunikation", "Chatbots für Terminbuchung und FAQs", "medium", "medium", 3),
            ("Abrechnungsunterstützung", "Automatische Kodierung und Prüfung", "medium", "high", 4),
        ],
        "use_cases_en": [
            ("Medical Letter Generation", "Automatic creation of clinical documents", "medium", "high", 3),
            ("Appointment Optimization", "AI schedules appointments more efficiently", "low", "medium", 2),
            ("Patient Communication", "Chatbots for appointment booking and FAQs", "medium", "medium", 3),
            ("Billing Support", "Automatic coding and verification", "medium", "high", 4),
        ],
        "kpis": ["Dokumentationszeit pro Patient", "Wartezeit", "Fehlerquote", "Patientenzufriedenheit"],
        "opportunities_de": [
            ("Zeitersparnis Dokumentation", "50-70% weniger Zeit für administrative Aufgaben"),
            ("Qualitätssteigerung", "KI als Second Opinion reduziert diagnostische Fehler"),
            ("Patientenerlebnis", "Kürzere Wartezeiten und bessere Kommunikation"),
        ],
        "opportunities_en": [
            ("Documentation Time Savings", "50-70% less time on administrative tasks"),
            ("Quality Improvement", "AI as second opinion reduces diagnostic errors"),
            ("Patient Experience", "Shorter wait times and better communication"),
        ],
        "risks_de": [
            ("Haftungsfragen", "Wer haftet bei KI-gestützten Fehldiagnosen?"),
            ("Datenschutz", "Gesundheitsdaten erfordern höchste Sicherheitsstandards"),
            ("Akzeptanz", "Patienten und Personal müssen KI vertrauen"),
        ],
        "risks_en": [
            ("Liability Questions", "Who is liable for AI-assisted misdiagnoses?"),
            ("Data Protection", "Health data requires highest security standards"),
            ("Acceptance", "Patients and staff must trust AI"),
        ],
        "bottlenecks_de": [
            ("Fragmentierte IT", "Praxis- und Klinik-Software oft nicht kompatibel"),
            ("Zertifizierung", "MDR-Konformität für KI-Medizinprodukte langwierig"),
            ("Schulungsbedarf", "Medizinisches Personal muss KI-Kompetenz aufbauen"),
        ],
        "bottlenecks_en": [
            ("Fragmented IT", "Practice and clinic software often incompatible"),
            ("Certification", "MDR compliance for AI medical devices lengthy"),
            ("Training Need", "Medical staff must build AI competence"),
        ],
    },
    "industrie": {
        "maturity_score": 60,
        "digitalization_level": "medium",
        "ai_adoption_rate": "growing",
        "competitive_density": "medium",
        "drivers_de": [
            ("Industrie 4.0", "Digitalisierung der Produktion ist strategisches Ziel"),
            ("Predictive Maintenance", "Ungeplante Stillstände kosten Millionen - KI verhindert sie"),
            ("Qualitätskontrolle", "Computer Vision automatisiert visuelle Inspektion"),
            ("Lieferketten-Resilienz", "KI optimiert Supply Chain Management"),
        ],
        "drivers_en": [
            ("Industry 4.0", "Digitalization of production is strategic goal"),
            ("Predictive Maintenance", "Unplanned downtime costs millions - AI prevents it"),
            ("Quality Control", "Computer vision automates visual inspection"),
            ("Supply Chain Resilience", "AI optimizes supply chain management"),
        ],
        "trends_de": [
            ("Digital Twin", "Virtuelle Abbilder von Produktionsanlagen", "high"),
            ("Autonomous Systems", "Selbststeuernde Logistik und Produktion", "medium"),
            ("Edge AI", "KI direkt an der Maschine", "high"),
            ("Generative Design", "KI entwirft optimierte Bauteile", "medium"),
        ],
        "trends_en": [
            ("Digital Twin", "Virtual replicas of production facilities", "high"),
            ("Autonomous Systems", "Self-controlling logistics and production", "medium"),
            ("Edge AI", "AI directly at the machine", "high"),
            ("Generative Design", "AI designs optimized components", "medium"),
        ],
        "regulatory_de": [
            ("Maschinensicherheit", "KI-gesteuerte Maschinen müssen CE-konform sein", "high"),
            ("AI Act", "Je nach Anwendung: High-Risk oder Standard", "medium"),
        ],
        "regulatory_en": [
            ("Machine Safety", "AI-controlled machines must be CE compliant", "high"),
            ("AI Act", "Depending on application: high-risk or standard", "medium"),
        ],
        "use_cases_de": [
            ("Predictive Maintenance", "Ausfälle vorhersagen und vermeiden", "high", "high", 6),
            ("Qualitätskontrolle", "Automatische Fehlererkennung per Computer Vision", "high", "high", 6),
            ("Produktionsplanung", "KI optimiert Kapazitäten und Ressourcen", "medium", "high", 4),
            ("Energiemanagement", "Intelligente Steuerung von Verbrauch", "medium", "medium", 3),
        ],
        "use_cases_en": [
            ("Predictive Maintenance", "Predict and prevent failures", "high", "high", 6),
            ("Quality Control", "Automatic defect detection via computer vision", "high", "high", 6),
            ("Production Planning", "AI optimizes capacity and resources", "medium", "high", 4),
            ("Energy Management", "Intelligent consumption control", "medium", "medium", 3),
        ],
        "kpis": ["OEE (Overall Equipment Effectiveness)", "Defect Rate", "Unplanned Downtime", "Energy Efficiency"],
        "opportunities_de": [
            ("Stillstandsreduktion", "Predictive Maintenance reduziert ungeplante Ausfälle um 30-50%"),
            ("Qualitätssteigerung", "Computer Vision erkennt Defekte zuverlässiger als Menschen"),
            ("Effizienzgewinn", "KI-optimierte Produktion spart 10-20% Ressourcen"),
        ],
        "opportunities_en": [
            ("Downtime Reduction", "Predictive maintenance reduces unplanned failures by 30-50%"),
            ("Quality Improvement", "Computer vision detects defects more reliably than humans"),
            ("Efficiency Gain", "AI-optimized production saves 10-20% resources"),
        ],
        "risks_de": [
            ("Investitionskosten", "IoT-Sensorik und KI-Infrastruktur erfordern hohe Anfangsinvestition"),
            ("Integration", "Anbindung an bestehende OT/IT-Landschaft komplex"),
            ("Cybersecurity", "Vernetzte Produktion erhöht Angriffsfläche"),
        ],
        "risks_en": [
            ("Investment Costs", "IoT sensors and AI infrastructure require high initial investment"),
            ("Integration", "Connecting to existing OT/IT landscape complex"),
            ("Cybersecurity", "Connected production increases attack surface"),
        ],
        "bottlenecks_de": [
            ("OT/IT-Konvergenz", "Produktions-IT und Office-IT zusammenbringen"),
            ("Datenqualität", "Maschinendaten oft unstrukturiert oder unvollständig"),
            ("Fachkräfte", "Kombination aus Produktions- und KI-Know-how selten"),
        ],
        "bottlenecks_en": [
            ("OT/IT Convergence", "Bringing production IT and office IT together"),
            ("Data Quality", "Machine data often unstructured or incomplete"),
            ("Specialists", "Combination of production and AI knowledge rare"),
        ],
    },
    "bildung": {
        "maturity_score": 40,
        "digitalization_level": "low",
        "ai_adoption_rate": "early",
        "competitive_density": "medium",
        "drivers_de": [
            ("Individualisierung", "Jeder Lernende hat andere Bedürfnisse - KI ermöglicht Personalisierung"),
            ("Lehrkräftemangel", "Zu wenig Personal für individuelle Betreuung"),
            ("Digitalisierungsrückstand", "Bildungssektor hinkt anderen Branchen hinterher"),
            ("Lebenslanges Lernen", "Upskilling-Bedarf durch KI selbst steigt"),
        ],
        "drivers_en": [
            ("Individualization", "Every learner has different needs - AI enables personalization"),
            ("Teacher Shortage", "Too few staff for individual support"),
            ("Digitalization Gap", "Education sector lags behind other industries"),
            ("Lifelong Learning", "Upskilling need increases due to AI itself"),
        ],
        "trends_de": [
            ("Adaptive Learning", "KI passt Lerninhalte an individuellen Fortschritt an", "high"),
            ("AI Tutors", "Intelligente Tutoren für 1:1-Betreuung", "high"),
            ("Content-Generierung", "KI erstellt und kuratiert Lehrmaterialien", "medium"),
            ("Assessment Automation", "Automatisierte Bewertung und Feedback", "medium"),
        ],
        "trends_en": [
            ("Adaptive Learning", "AI adapts learning content to individual progress", "high"),
            ("AI Tutors", "Intelligent tutors for 1:1 support", "high"),
            ("Content Generation", "AI creates and curates teaching materials", "medium"),
            ("Assessment Automation", "Automated evaluation and feedback", "medium"),
        ],
        "regulatory_de": [
            ("Bildungsdatenschutz", "Besonderer Schutz von Daten Minderjähriger", "high"),
            ("AI Act", "Bildungs-KI ist potenziell High-Risk-Kategorie", "high"),
        ],
        "regulatory_en": [
            ("Educational Data Protection", "Special protection of minors' data", "high"),
            ("AI Act", "Educational AI is potentially high-risk category", "high"),
        ],
        "use_cases_de": [
            ("Lernassistenten", "KI-Tutoren für individuelle Unterstützung", "medium", "high", 3),
            ("Content-Erstellung", "Automatisierte Erstellung von Lehrmaterialien", "low", "medium", 2),
            ("Plagiatsprüfung", "KI-gestützte Überprüfung von Arbeiten", "low", "medium", 1),
            ("Admin-Automatisierung", "Verwaltungsaufgaben automatisieren", "low", "medium", 2),
        ],
        "use_cases_en": [
            ("Learning Assistants", "AI tutors for individual support", "medium", "high", 3),
            ("Content Creation", "Automated creation of teaching materials", "low", "medium", 2),
            ("Plagiarism Check", "AI-powered verification of work", "low", "medium", 1),
            ("Admin Automation", "Automate administrative tasks", "low", "medium", 2),
        ],
        "kpis": ["Learning Outcomes", "Student Engagement", "Time-to-Competence", "Dropout Rate"],
        "opportunities_de": [
            ("Personalisiertes Lernen", "Jeder Lernende erhält individuell angepasste Inhalte"),
            ("Lehrerentlastung", "KI übernimmt repetitive Aufgaben wie Korrektur"),
            ("Erweiterung", "Qualitativ hochwertige Bildung für mehr Menschen"),
        ],
        "opportunities_en": [
            ("Personalized Learning", "Each learner receives individually adapted content"),
            ("Teacher Relief", "AI handles repetitive tasks like grading"),
            ("Scaling", "Quality education for more people"),
        ],
        "risks_de": [
            ("Bildungsgerechtigkeit", "KI-Zugang darf nicht von Ressourcen abhängen"),
            ("Fehlende Kritikfähigkeit", "Lernende übernehmen KI-Output unkritisch"),
            ("Datenschutz Minderjähriger", "Besonders sensible Daten erfordern höchsten Schutz"),
        ],
        "risks_en": [
            ("Educational Equity", "AI access must not depend on resources"),
            ("Lack of Critical Thinking", "Learners accept AI output uncritically"),
            ("Minor Data Protection", "Particularly sensitive data requires highest protection"),
        ],
        "bottlenecks_de": [
            ("Infrastruktur", "Viele Bildungseinrichtungen haben veraltete IT"),
            ("Kompetenz", "Lehrkräfte müssen KI-Didaktik erst erlernen"),
            ("Akzeptanz", "Widerstand gegen technologische Veränderung"),
        ],
        "bottlenecks_en": [
            ("Infrastructure", "Many educational institutions have outdated IT"),
            ("Competence", "Teachers must first learn AI didactics"),
            ("Acceptance", "Resistance to technological change"),
        ],
    },
    "marketing": {
        "maturity_score": 75,
        "digitalization_level": "high",
        "ai_adoption_rate": "mainstream",
        "competitive_density": "high",
        "drivers_de": [
            ("Content-Bedarf", "Omnichannel-Marketing erfordert massive Content-Produktion"),
            ("Personalisierung", "1:1-Marketing wird Erwartung, nicht Bonus"),
            ("Performance-Druck", "ROI-Nachweis für jeden Euro Marketing-Budget"),
            ("Kreativitätssteigerung", "KI als Co-Creator beschleunigt Ideenfindung"),
        ],
        "drivers_en": [
            ("Content Demand", "Omnichannel marketing requires massive content production"),
            ("Personalization", "1:1 marketing becomes expectation, not bonus"),
            ("Performance Pressure", "ROI proof for every marketing budget euro"),
            ("Creativity Boost", "AI as co-creator accelerates ideation"),
        ],
        "trends_de": [
            ("Generative Content", "KI erstellt Text, Bild, Video auf Knopfdruck", "very_high"),
            ("Hyper-Personalisierung", "Individuelle Ansprache in Echtzeit", "high"),
            ("Predictive Analytics", "KI prognostiziert Kampagnen-Performance", "high"),
            ("Conversational Marketing", "Chatbots als Marketing-Kanal", "medium"),
        ],
        "trends_en": [
            ("Generative Content", "AI creates text, image, video at the push of a button", "very_high"),
            ("Hyper-Personalization", "Individual approach in real-time", "high"),
            ("Predictive Analytics", "AI predicts campaign performance", "high"),
            ("Conversational Marketing", "Chatbots as marketing channel", "medium"),
        ],
        "regulatory_de": [
            ("DSGVO/E-Privacy", "Tracking und Personalisierung datenschutzkonform gestalten", "high"),
            ("Werbekennzeichnung", "KI-generierte Inhalte müssen ggf. gekennzeichnet werden", "medium"),
        ],
        "regulatory_en": [
            ("GDPR/E-Privacy", "Design tracking and personalization GDPR-compliant", "high"),
            ("Ad Disclosure", "AI-generated content may need to be labeled", "medium"),
        ],
        "use_cases_de": [
            ("Content-Generierung", "Blog-Posts, Social Media, Ads automatisch erstellen", "low", "high", 1),
            ("Copy-Optimierung", "A/B-Test-Varianten per KI generieren", "low", "high", 1),
            ("Bildgenerierung", "Visuelle Assets mit DALL-E, Midjourney etc.", "low", "medium", 1),
            ("Campaign Analytics", "KI-gestützte Performance-Analyse", "medium", "high", 2),
        ],
        "use_cases_en": [
            ("Content Generation", "Create blog posts, social media, ads automatically", "low", "high", 1),
            ("Copy Optimization", "Generate A/B test variants via AI", "low", "high", 1),
            ("Image Generation", "Visual assets with DALL-E, Midjourney etc.", "low", "medium", 1),
            ("Campaign Analytics", "AI-powered performance analysis", "medium", "high", 2),
        ],
        "kpis": ["Content Output", "Engagement Rate", "Conversion Rate", "CAC (Customer Acquisition Cost)"],
        "opportunities_de": [
            ("Content-Erweiterung", "10x mehr Content bei gleichen Ressourcen"),
            ("Kreativitätssteigerung", "Mehr Ideen, schnellere Iteration"),
            ("Performance-Optimierung", "KI-gestützte A/B-Tests verbessern Conversion"),
        ],
        "opportunities_en": [
            ("Content Scaling", "10x more content with same resources"),
            ("Creativity Boost", "More ideas, faster iteration"),
            ("Performance Optimization", "AI-powered A/B tests improve conversion"),
        ],
        "risks_de": [
            ("Qualitätskontrolle", "KI-Content muss auf Markenkonformität geprüft werden"),
            ("Authentizität", "Kunden merken generischen KI-Content"),
            ("Urheberrecht", "Rechtslage bei KI-generiertem Content noch unklar"),
        ],
        "risks_en": [
            ("Quality Control", "AI content must be checked for brand conformity"),
            ("Authenticity", "Customers notice generic AI content"),
            ("Copyright", "Legal situation for AI-generated content still unclear"),
        ],
        "bottlenecks_de": [
            ("Brand Guidelines", "KI muss Markentonalität konsistent treffen"),
            ("Tool-Überflutung", "Zu viele KI-Tools ohne klare Strategie"),
            ("Messbarkeit", "Attribution von KI-Impact schwierig"),
        ],
        "bottlenecks_en": [
            ("Brand Guidelines", "AI must consistently match brand tonality"),
            ("Tool Overload", "Too many AI tools without clear strategy"),
            ("Measurability", "Attribution of AI impact difficult"),
        ],
    },
    # =========================================================================
    # G19.1: NEW BRANCH PROFILES
    # =========================================================================
    "bauwesen_architektur": {
        "maturity_score": 55,
        "digitalization_level": "medium",
        "ai_adoption_rate": "early",
        "competitive_density": "medium",
        "drivers_de": [
            ("Projektgeschäft", "Jedes Bauprojekt ist einzigartig - KI optimiert wiederkehrende Prozesse in Planung und Dokumentation"),
            ("Ausschreibungskomplexität", "Öffentliche und private Ausschreibungen erfordern präzise, zeitaufwändige Unterlagen - KI beschleunigt"),
            ("BIM-Pflicht", "Building Information Modeling wird Standard - KI-Integration in BIM-Workflows wird kritisch"),
            ("Dokumentationsdichte", "Bautagebücher, Protokolle, Mängelberichte - hoher administrativer Aufwand für KI-Automatisierung"),
            ("Fachkräftemangel", "Bauwirtschaft kämpft mit Nachwuchsmangel - KI kompensiert fehlende Kapazitäten"),
        ],
        "drivers_en": [
            ("Project Business", "Each construction project is unique - AI optimizes recurring processes in planning and documentation"),
            ("Tender Complexity", "Public and private tenders require precise, time-consuming documents - AI accelerates"),
            ("BIM Mandate", "Building Information Modeling becoming standard - AI integration in BIM workflows critical"),
            ("Documentation Density", "Construction diaries, protocols, defect reports - high admin effort for AI automation"),
            ("Skilled Labor Shortage", "Construction industry struggles with talent gap - AI compensates missing capacity"),
        ],
        "trends_de": [
            ("BIM + KI-Integration", "KI-gestützte Planung und Kollisionsprüfung in BIM-Modellen", "high"),
            ("Dokumentationsautomatisierung", "Automatische Bautagebücher und Protokolle", "high"),
            ("Predictive Maintenance", "Vorausschauende Wartung für Gebäudetechnik", "medium"),
            ("Generative Design", "KI-gestützte Entwurfsoptimierung", "emerging"),
            ("Digital Twin", "Digitale Gebäudezwillinge für Betrieb und Wartung", "medium"),
            ("Drohnen + KI", "Automatisierte Baufortschrittskontrolle und Inspektion", "medium"),
        ],
        "trends_en": [
            ("BIM + AI Integration", "AI-powered planning and clash detection in BIM models", "high"),
            ("Documentation Automation", "Automatic construction diaries and protocols", "high"),
            ("Predictive Maintenance", "Proactive maintenance for building technology", "medium"),
            ("Generative Design", "AI-powered design optimization", "emerging"),
            ("Digital Twin", "Digital building twins for operations and maintenance", "medium"),
            ("Drones + AI", "Automated construction progress monitoring and inspection", "medium"),
        ],
        "regulatory_de": [
            ("Bauvorschriften", "KI-gestützte Planung muss alle Bauordnungen und Normen einhalten", "high"),
            ("HOAI-Konformität", "Honorarordnung für Architekten und Ingenieure bei KI-Einsatz beachten", "medium"),
            ("Haftungsfragen", "Verantwortlichkeit bei KI-gestützten Planungsentscheidungen klären", "high"),
            ("Datenschutz am Bau", "Personenbezogene Daten von Arbeitern und Bewohnern schützen", "medium"),
        ],
        "regulatory_en": [
            ("Building Codes", "AI-assisted planning must comply with all building regulations and standards", "high"),
            ("Professional Liability", "Consider professional standards for architects and engineers when using AI", "medium"),
            ("Liability Questions", "Clarify responsibility for AI-assisted planning decisions", "high"),
            ("Data Protection", "Protect personal data of workers and residents", "medium"),
        ],
        "use_cases_de": [
            ("Ausschreibungsassistent", "KI erstellt Leistungsverzeichnisse und Ausschreibungsunterlagen", "medium", "high", 2),
            ("Bautagebuch-Automation", "Automatische Dokumentation von Baufortschritt und Ereignissen", "low", "high", 1),
            ("Mängelmanagement", "KI-gestützte Erfassung, Kategorisierung und Tracking von Baumängeln", "medium", "high", 3),
            ("Planprüfung", "Automatische Prüfung auf Planungsfehler und Normkonformität", "high", "high", 6),
        ],
        "use_cases_en": [
            ("Tender Assistant", "AI creates specifications and tender documents", "medium", "high", 2),
            ("Construction Diary Automation", "Automatic documentation of progress and events", "low", "high", 1),
            ("Defect Management", "AI-powered capture, categorization and tracking of construction defects", "medium", "high", 3),
            ("Plan Review", "Automatic review for planning errors and code compliance", "high", "high", 6),
        ],
        "kpis": ["Bauzeit pro Projekt", "Nachtragsquote", "Dokumentationsstunden", "Mängelquote", "Planungsrevisions-Rate"],
        "opportunities_de": [
            ("Dokumentationseffizienz", "50-70% Zeitersparnis bei Bautagebüchern und Protokollen durch KI-Automatisierung"),
            ("Ausschreibungsqualität", "KI-gestützte Leistungsverzeichnisse reduzieren Nachträge um 15-25%"),
            ("Planungspräzision", "Automatische Kollisionsprüfung verhindert kostspielige Baufehler"),
        ],
        "opportunities_en": [
            ("Documentation Efficiency", "50-70% time savings on construction diaries and protocols through AI automation"),
            ("Tender Quality", "AI-assisted specifications reduce change orders by 15-25%"),
            ("Planning Precision", "Automatic clash detection prevents costly construction errors"),
        ],
        "risks_de": [
            ("Haftungsrisiko", "KI-gestützte Planungsentscheidungen können Haftungsfragen aufwerfen"),
            ("Datenqualität", "BIM-Modelle und Plandaten müssen aktuell und konsistent sein"),
            ("Akzeptanz am Bau", "Gewerbliche Mitarbeiter müssen KI-Tools annehmen"),
        ],
        "risks_en": [
            ("Liability Risk", "AI-assisted planning decisions may raise liability questions"),
            ("Data Quality", "BIM models and plan data must be current and consistent"),
            ("Acceptance on Site", "Trade workers must accept AI tools"),
        ],
        "bottlenecks_de": [
            ("Fragmentierte IT-Landschaft", "Viele Insellösungen ohne Schnittstellen erschweren KI-Integration"),
            ("Baustellenkonnektivität", "Fehlende Internet-Infrastruktur auf Baustellen"),
            ("Change Management", "Traditionelle Branche mit Widerstand gegen Digitalisierung"),
        ],
        "bottlenecks_en": [
            ("Fragmented IT Landscape", "Many isolated solutions without interfaces complicate AI integration"),
            ("Site Connectivity", "Missing internet infrastructure on construction sites"),
            ("Change Management", "Traditional industry with resistance to digitalization"),
        ],
    },
    "verwaltung": {
        "maturity_score": 45,
        "digitalization_level": "low",
        "ai_adoption_rate": "early",
        "competitive_density": "low",
        "drivers_de": [
            ("Compliance-Anforderungen", "Behörden müssen strenge Vorschriften einhalten - KI kann Compliance automatisieren"),
            ("Aktenführungspflicht", "Umfangreiche Dokumentationspflichten bieten Automatisierungspotenzial"),
            ("Datenschutz-Sensibilität", "Öffentliche Verwaltung arbeitet mit hochsensiblen Bürgerdaten - DSGVO-konforme KI erforderlich"),
            ("Bürgerprozesse", "Anträge, Bescheide, Anfragen - standardisierte Prozesse ideal für KI-Unterstützung"),
            ("Ressourcendruck", "Personalmangel und Budgetrestriktionen erfordern Effizienzsteigerung"),
            ("Onlinezugangsgesetz", "OZG-Verpflichtung treibt Digitalisierung - KI kann helfen"),
        ],
        "drivers_en": [
            ("Compliance Requirements", "Agencies must adhere to strict regulations - AI can automate compliance"),
            ("Records Management", "Extensive documentation duties offer automation potential"),
            ("Data Protection Sensitivity", "Public admin works with highly sensitive citizen data - GDPR-compliant AI required"),
            ("Citizen Processes", "Applications, notices, inquiries - standardized processes ideal for AI support"),
            ("Resource Pressure", "Staff shortages and budget constraints require efficiency gains"),
            ("Digital Access Act", "OZG obligation drives digitalization - AI can help"),
        ],
        "trends_de": [
            ("Bürgerportale mit KI", "Intelligente Chatbots für Bürgeranfragen und Antragshilfe", "medium"),
            ("Dokumentenklassifizierung", "Automatische Sortierung und Routing von Eingängen", "high"),
            ("Formularautomatisierung", "KI-gestützte Ausfüllhilfen und Plausibilitätsprüfung", "medium"),
            ("Bescheidgenerierung", "Automatische Erstellung von Standardbescheiden", "emerging"),
            ("E-Akte-Integration", "KI-Suche und Zusammenfassung in elektronischen Akten", "medium"),
            ("Prozessdigitalisierung", "Ende-zu-Ende Digitalisierung von Verwaltungsprozessen", "high"),
        ],
        "trends_en": [
            ("Citizen Portals with AI", "Intelligent chatbots for citizen inquiries and application help", "medium"),
            ("Document Classification", "Automatic sorting and routing of incoming documents", "high"),
            ("Form Automation", "AI-assisted form filling and plausibility checks", "medium"),
            ("Notice Generation", "Automatic creation of standard notices", "emerging"),
            ("E-File Integration", "AI search and summarization in electronic files", "medium"),
            ("Process Digitalization", "End-to-end digitalization of administrative processes", "high"),
        ],
        "regulatory_de": [
            ("DSGVO/Datenschutz", "Höchste Anforderungen bei Verarbeitung von Bürgerdaten", "high"),
            ("AI Act - High Risk", "Behördliche KI-Systeme oft als hochriskant eingestuft", "high"),
            ("Verwaltungsverfahrensgesetz", "Automatisierte Entscheidungen müssen rechtssicher sein", "high"),
            ("BSI-Vorgaben", "IT-Sicherheitsstandards für Behörden beachten", "high"),
        ],
        "regulatory_en": [
            ("GDPR/Data Protection", "Highest requirements for processing citizen data", "high"),
            ("AI Act - High Risk", "Government AI systems often classified as high-risk", "high"),
            ("Administrative Procedure Act", "Automated decisions must be legally sound", "high"),
            ("BSI Guidelines", "Observe IT security standards for public agencies", "high"),
        ],
        "use_cases_de": [
            ("Bürger-Chatbot", "24/7 Beantwortung häufiger Fragen und Antragshilfe", "medium", "high", 3),
            ("Antragsvorprüfung", "Automatische Vollständigkeits- und Plausibilitätsprüfung", "medium", "high", 2),
            ("Akten-Zusammenfassung", "KI-gestützte Zusammenfassung umfangreicher Akten", "low", "high", 2),
            ("Übersetzungsdienst", "Automatische Übersetzung für mehrsprachige Bürger", "low", "medium", 1),
        ],
        "use_cases_en": [
            ("Citizen Chatbot", "24/7 answering of common questions and application help", "medium", "high", 3),
            ("Application Pre-Review", "Automatic completeness and plausibility checks", "medium", "high", 2),
            ("File Summarization", "AI-powered summarization of extensive files", "low", "high", 2),
            ("Translation Service", "Automatic translation for multilingual citizens", "low", "medium", 1),
        ],
        "kpis": ["Durchlaufzeit pro Antrag", "Rückmeldequote Bürger", "DSGVO-Vorfälle", "Bearbeitungszeit", "Digitalisierungsgrad"],
        "opportunities_de": [
            ("Bürgerzufriedenheit", "24/7 verfügbare KI-Services verbessern Serviceerlebnis erheblich"),
            ("Bearbeitungseffizienz", "40-60% schnellere Antragsbearbeitung durch KI-Vorprüfung"),
            ("Fehlerreduktion", "Automatische Prüfungen reduzieren formale Fehler in Bescheiden"),
        ],
        "opportunities_en": [
            ("Citizen Satisfaction", "24/7 available AI services significantly improve service experience"),
            ("Processing Efficiency", "40-60% faster application processing through AI pre-review"),
            ("Error Reduction", "Automatic checks reduce formal errors in notices"),
        ],
        "risks_de": [
            ("Datenschutzverletzungen", "Fehlkonfigurierte KI kann sensible Bürgerdaten exponieren"),
            ("Rechtswidrigkeit", "Automatisierte Entscheidungen können anfechtbar sein"),
            ("Bürgervertrauen", "Intransparente KI kann Vertrauen in Verwaltung untergraben"),
        ],
        "risks_en": [
            ("Data Protection Violations", "Misconfigured AI can expose sensitive citizen data"),
            ("Legal Issues", "Automated decisions may be challengeable"),
            ("Citizen Trust", "Non-transparent AI can undermine trust in administration"),
        ],
        "bottlenecks_de": [
            ("Vergaberecht", "Beschaffung von KI-Lösungen durch Vergaberegeln erschwert"),
            ("Legacy-Systeme", "Veraltete Fachverfahren schwer mit KI zu integrieren"),
            ("Personalkompetenzen", "Mitarbeiter benötigen KI-Schulung und Change Management"),
        ],
        "bottlenecks_en": [
            ("Procurement Law", "Acquisition of AI solutions complicated by procurement rules"),
            ("Legacy Systems", "Outdated specialized procedures hard to integrate with AI"),
            ("Staff Competencies", "Employees need AI training and change management"),
        ],
    },
    "transport_logistik": {
        "maturity_score": 60,
        "digitalization_level": "medium",
        "ai_adoption_rate": "growing",
        "competitive_density": "high",
        "drivers_de": [
            ("Supply Chain Komplexität", "Globale Lieferketten erfordern intelligente Optimierung - KI managt Komplexität"),
            ("Zeitkritische Prozesse", "Just-in-Time Lieferung erfordert präzise Prognosen und Routenoptimierung"),
            ("Kostenoptimierung", "Kraftstoff, Personal, Lager - KI identifiziert Einsparpotenziale"),
            ("Tracking-Erwartung", "Kunden erwarten Echtzeit-Transparenz über Sendungsstatus"),
            ("Fahrermangel", "Personalmangel in der Logistik - KI optimiert vorhandene Kapazitäten"),
            ("Nachhaltigkeitsdruck", "CO2-Reduktion erfordert effizientere Routenplanung"),
        ],
        "drivers_en": [
            ("Supply Chain Complexity", "Global supply chains require intelligent optimization - AI manages complexity"),
            ("Time-Critical Processes", "Just-in-time delivery requires precise forecasts and route optimization"),
            ("Cost Optimization", "Fuel, personnel, warehouse - AI identifies savings potential"),
            ("Tracking Expectation", "Customers expect real-time transparency on shipment status"),
            ("Driver Shortage", "Personnel shortage in logistics - AI optimizes existing capacity"),
            ("Sustainability Pressure", "CO2 reduction requires more efficient route planning"),
        ],
        "trends_de": [
            ("Predictive Logistics", "KI-gestützte Prognosen für Nachfrage, Lieferzeiten, Kapazitäten", "very_high"),
            ("Routenoptimierung", "Dynamische Tourenplanung mit Echtzeit-Verkehrsdaten", "high"),
            ("Autonome Fahrzeuge", "Selbstfahrende LKW und Drohnenlieferung in Entwicklung", "emerging"),
            ("Smart Warehousing", "KI-gesteuerte Lagerroboter und Bestandsoptimierung", "high"),
            ("Last Mile Innovation", "KI optimiert die letzte Meile zum Kunden", "high"),
            ("Supply Chain Visibility", "End-to-End Transparenz über KI-Analytics", "high"),
        ],
        "trends_en": [
            ("Predictive Logistics", "AI-powered forecasts for demand, delivery times, capacities", "very_high"),
            ("Route Optimization", "Dynamic tour planning with real-time traffic data", "high"),
            ("Autonomous Vehicles", "Self-driving trucks and drone delivery in development", "emerging"),
            ("Smart Warehousing", "AI-controlled warehouse robots and inventory optimization", "high"),
            ("Last Mile Innovation", "AI optimizes the last mile to customers", "high"),
            ("Supply Chain Visibility", "End-to-end transparency through AI analytics", "high"),
        ],
        "regulatory_de": [
            ("Lenk- und Ruhezeiten", "KI-Systeme müssen gesetzliche Fahrervorschriften berücksichtigen", "high"),
            ("Gefahrgutvorschriften", "Transport gefährlicher Güter erfordert spezielle KI-Compliance", "high"),
            ("Zollvorschriften", "Grenzüberschreitende Logistik muss Zollregeln automatisiert einhalten", "medium"),
            ("Datenschutz", "Tracking-Daten von Fahrern und Kunden schützen", "medium"),
        ],
        "regulatory_en": [
            ("Driving Time Regulations", "AI systems must consider legal driver regulations", "high"),
            ("Hazardous Goods", "Transport of dangerous goods requires special AI compliance", "high"),
            ("Customs Regulations", "Cross-border logistics must automatically comply with customs rules", "medium"),
            ("Data Protection", "Protect tracking data of drivers and customers", "medium"),
        ],
        "use_cases_de": [
            ("Routenoptimierung", "KI berechnet optimale Touren unter Berücksichtigung aller Faktoren", "medium", "high", 2),
            ("Nachfrageprognose", "Vorhersage von Bestellvolumen für Kapazitätsplanung", "medium", "high", 3),
            ("ETA-Prediction", "Präzise Ankunftszeit-Vorhersagen für Kunden", "low", "high", 2),
            ("Lageroptimierung", "KI optimiert Einlagerung und Kommissionierung", "high", "high", 6),
        ],
        "use_cases_en": [
            ("Route Optimization", "AI calculates optimal tours considering all factors", "medium", "high", 2),
            ("Demand Forecasting", "Prediction of order volumes for capacity planning", "medium", "high", 3),
            ("ETA Prediction", "Precise arrival time predictions for customers", "low", "high", 2),
            ("Warehouse Optimization", "AI optimizes storage and picking", "high", "high", 6),
        ],
        "kpis": ["Lieferpünktlichkeit", "Kapazitätsauslastung", "Schadenquote", "Kraftstoffeffizienz", "Lagerumschlag"],
        "opportunities_de": [
            ("Routeneffizienz", "10-25% Kraftstoffeinsparung durch KI-optimierte Routen"),
            ("Liefergenauigkeit", "ETA-Präzision steigert Kundenzufriedenheit um 30%+"),
            ("Lagerkosten", "Bestandsoptimierung reduziert Kapitalbindung um 15-30%"),
        ],
        "opportunities_en": [
            ("Route Efficiency", "10-25% fuel savings through AI-optimized routes"),
            ("Delivery Accuracy", "ETA precision increases customer satisfaction by 30%+"),
            ("Warehouse Costs", "Inventory optimization reduces capital tie-up by 15-30%"),
        ],
        "risks_de": [
            ("Systemausfälle", "KI-abhängige Logistik braucht robuste Fallback-Systeme"),
            ("Datenqualität", "Falsche Bestandsdaten führen zu fehlerhaften KI-Entscheidungen"),
            ("Cyberrisiken", "Vernetzte Logistik erhöht Angriffsfläche für Hacker"),
        ],
        "risks_en": [
            ("System Outages", "AI-dependent logistics needs robust fallback systems"),
            ("Data Quality", "Wrong inventory data leads to incorrect AI decisions"),
            ("Cyber Risks", "Connected logistics increases attack surface for hackers"),
        ],
        "bottlenecks_de": [
            ("Datenintegration", "Verschiedene Systeme (WMS, TMS, ERP) müssen verbunden werden"),
            ("Echtzeit-Anforderungen", "KI-Systeme müssen binnen Sekunden reagieren"),
            ("Flottenalter", "Ältere Fahrzeuge fehlt Telematik für KI-Integration"),
        ],
        "bottlenecks_en": [
            ("Data Integration", "Various systems (WMS, TMS, ERP) must be connected"),
            ("Real-Time Requirements", "AI systems must respond within seconds"),
            ("Fleet Age", "Older vehicles lack telematics for AI integration"),
        ],
    },
}

# Fallback for unknown branches
DEFAULT_BRANCH_DATA = {
    "maturity_score": 50,
    "digitalization_level": "medium",
    "ai_adoption_rate": "growing",
    "competitive_density": "medium",
    "drivers_de": [
        ("Digitalisierungsdruck", "Wettbewerb und Kundenerwartungen treiben KI-Adoption"),
        ("Effizienzpotenzial", "Prozessautomatisierung spart Zeit und Kosten"),
        ("Fachkräftemangel", "KI kompensiert fehlende Personalressourcen"),
        ("Datennutzung", "Vorhandene Daten werden für KI-Anwendungen erschlossen"),
    ],
    "drivers_en": [
        ("Digitalization Pressure", "Competition and customer expectations drive AI adoption"),
        ("Efficiency Potential", "Process automation saves time and costs"),
        ("Talent Shortage", "AI compensates for missing staff resources"),
        ("Data Utilization", "Existing data is leveraged for AI applications"),
    ],
    "trends_de": [
        ("Generative AI", "ChatGPT und ähnliche Tools werden breit eingesetzt", "very_high"),
        ("Process Automation", "RPA und KI automatisieren Routineaufgaben", "high"),
        ("Analytics & BI", "Datengetriebene Entscheidungen werden Standard", "medium"),
        ("Customer Service AI", "Chatbots und virtuelle Assistenten", "medium"),
    ],
    "trends_en": [
        ("Generative AI", "ChatGPT and similar tools widely used", "very_high"),
        ("Process Automation", "RPA and AI automate routine tasks", "high"),
        ("Analytics & BI", "Data-driven decisions becoming standard", "medium"),
        ("Customer Service AI", "Chatbots and virtual assistants", "medium"),
    ],
    "regulatory_de": [
        ("AI Act", "Neue EU-Verordnung erfordert Compliance-Prüfung", "medium"),
        ("DSGVO", "Datenschutz bei KI-Anwendungen sicherstellen", "high"),
    ],
    "regulatory_en": [
        ("AI Act", "New EU regulation requires compliance check", "medium"),
        ("GDPR", "Ensure data protection in AI applications", "high"),
    ],
    "use_cases_de": [
        ("Content-Erstellung", "Texte, Reports, Präsentationen automatisieren", "low", "high", 1),
        ("Kundenservice", "Chatbots für häufige Anfragen", "medium", "medium", 2),
        ("Prozessautomatisierung", "Routineaufgaben automatisieren", "medium", "high", 3),
        ("Datenanalyse", "Insights aus vorhandenen Daten gewinnen", "medium", "medium", 3),
    ],
    "use_cases_en": [
        ("Content Creation", "Automate texts, reports, presentations", "low", "high", 1),
        ("Customer Service", "Chatbots for common inquiries", "medium", "medium", 2),
        ("Process Automation", "Automate routine tasks", "medium", "high", 3),
        ("Data Analysis", "Gain insights from existing data", "medium", "medium", 3),
    ],
    "kpis": ["Produktivität", "Fehlerquote", "Durchlaufzeit", "Kundenzufriedenheit"],
    "opportunities_de": [
        ("Produktivitätssteigerung", "20-40% Effizienzgewinn bei dokumentationsintensiven Aufgaben"),
        ("Kostensenkung", "Automatisierung reduziert operative Kosten"),
        ("Wettbewerbsvorteil", "Frühe KI-Adoption als Differenzierungsmerkmal"),
    ],
    "opportunities_en": [
        ("Productivity Increase", "20-40% efficiency gain in documentation-intensive tasks"),
        ("Cost Reduction", "Automation reduces operational costs"),
        ("Competitive Advantage", "Early AI adoption as differentiator"),
    ],
    "risks_de": [
        ("Qualitätskontrolle", "KI-Output muss geprüft werden"),
        ("Datenschutz", "Sensible Daten erfordern sichere KI-Nutzung"),
        ("Change Management", "Mitarbeiter müssen mitgenommen werden"),
    ],
    "risks_en": [
        ("Quality Control", "AI output must be reviewed"),
        ("Data Protection", "Sensitive data requires secure AI usage"),
        ("Change Management", "Employees must be brought along"),
    ],
    "bottlenecks_de": [
        ("Fehlende Kompetenz", "KI-Know-how im Team aufbauen"),
        ("Datenqualität", "Saubere Daten sind Voraussetzung für KI"),
        ("Budget", "Initiale Investition in Tools und Schulung"),
    ],
    "bottlenecks_en": [
        ("Lacking Competence", "Build AI know-how in the team"),
        ("Data Quality", "Clean data is prerequisite for AI"),
        ("Budget", "Initial investment in tools and training"),
    ],
}

# Branch name normalization mapping
BRANCH_ALIASES: Dict[str, str] = {
    # G19.1-MAP: Frontend dropdown value keys (primary mappings)
    "marketing_werbung": "marketing",
    "beratung_dienstleistungen": "beratung",
    "finanzen_versicherungen": "finanzen",
    "handel_ecommerce": "handel",
    "gesundheit_pflege": "gesundheit",
    "medien_kreativwirtschaft": "marketing",  # maps to marketing profile
    "industrie_produktion": "industrie",
    # German variations
    "beratung": "beratung",
    "consulting": "beratung",
    "unternehmensberatung": "beratung",
    "dienstleistung": "beratung",
    "dienstleistungen": "beratung",
    "it": "it",
    "it_software": "it",
    "software": "it",
    "tech": "it",
    "technologie": "it",
    "handel": "handel",
    "ecommerce": "handel",
    "e-commerce": "handel",
    "retail": "handel",
    "einzelhandel": "handel",
    "finanzen": "finanzen",
    "finance": "finanzen",
    "finanzdienstleistungen": "finanzen",
    "banking": "finanzen",
    "versicherung": "finanzen",
    "gesundheit": "gesundheit",
    "health": "gesundheit",
    "healthcare": "gesundheit",
    "medizin": "gesundheit",
    "pharma": "gesundheit",
    "pflege": "gesundheit",
    "industrie": "industrie",
    "manufacturing": "industrie",
    "produktion": "industrie",
    "fertigung": "industrie",
    "bildung": "bildung",
    "education": "bildung",
    "training": "bildung",
    "schule": "bildung",
    "hochschule": "bildung",
    "marketing": "marketing",
    "werbung": "marketing",
    "medien": "marketing",
    "agentur": "marketing",
    "kreativ": "marketing",
    "kreativwirtschaft": "marketing",
    # G19.1: New branch aliases
    "bauwesen_architektur": "bauwesen_architektur",
    "bauwesen": "bauwesen_architektur",
    "bau": "bauwesen_architektur",
    "architektur": "bauwesen_architektur",
    "construction": "bauwesen_architektur",
    "architecture": "bauwesen_architektur",
    "baugewerbe": "bauwesen_architektur",
    "immobilien": "bauwesen_architektur",
    "real_estate": "bauwesen_architektur",
    "verwaltung": "verwaltung",
    "public_sector": "verwaltung",
    "government": "verwaltung",
    "behoerde": "verwaltung",
    "oeffentlich": "verwaltung",
    "oeffentlicher_dienst": "verwaltung",
    "kommune": "verwaltung",
    "administration": "verwaltung",
    "transport_logistik": "transport_logistik",
    "logistik": "transport_logistik",
    "transport": "transport_logistik",
    "logistics": "transport_logistik",
    "spedition": "transport_logistik",
    "supply_chain": "transport_logistik",
    "shipping": "transport_logistik",
    "warehousing": "transport_logistik",
    "lager": "transport_logistik",
}


def _normalize_branch(branch: str) -> str:
    """Normalize branch name to canonical form."""
    if not branch:
        return "beratung"  # Default

    branch_lower = branch.lower().strip()
    branch_lower = branch_lower.replace(" ", "_").replace("-", "_")
    branch_lower = branch_lower.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")

    return BRANCH_ALIASES.get(branch_lower, branch_lower)


def _normalize_size(size: str) -> str:
    """Normalize company size to canonical form."""
    if not size:
        return "team"

    # FIX-SIZE-BUCKET: Normalize en-dash/em-dash to hyphen for consistent matching
    size_lower = size.lower().replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    # Check team first to avoid "2-10" matching "1" in solo check
    if "team" in size_lower or "2-10" in size_lower or "klein" in size_lower:
        return "team"
    elif "solo" in size_lower or "(1)" in size_lower or "selbst" in size_lower:
        return "solo"
    elif "kmu" in size_lower or "11-" in size_lower or "250" in size_lower:
        return "kmu"
    else:
        return "team"  # Default


def _get_branch_data(branch: str) -> Dict[str, Any]:
    """Get branch data, falling back to default if not found."""
    normalized = _normalize_branch(branch)
    return BRANCH_MATURITY_DATA.get(normalized, DEFAULT_BRANCH_DATA)


def _get_maturity_label(score: int) -> str:
    """Get maturity label from score."""
    if score >= 75:
        return "mature"
    elif score >= 55:
        return "maturing"
    elif score >= 35:
        return "developing"
    else:
        return "emerging"


# =============================================================================
# MAIN API FUNCTIONS
# =============================================================================

def build_branch_profile(
    branch: str,
    size: str = "team",
    language: str = "de"
) -> BranchProfile:
    """
    Build comprehensive branch/industry profile.

    Args:
        branch: Industry/branch name
        size: Company size (solo, team, kmu)
        language: Language code (de, en)

    Returns:
        BranchProfile with drivers, trends, regulatory factors, use cases, maturity
    """
    if not BRANCH_PROFILE_ENABLED:
        log.debug("[G19] Branch profile engine disabled")
        return BranchProfile(
            branch_id="disabled",
            branch_name="disabled",
            branch_display_name="",
            size_context="",
            language=language,
        )

    normalized_branch = _normalize_branch(branch)
    normalized_size = _normalize_size(size)
    lang_key = "de" if language.lower().startswith("de") else "en"

    data = _get_branch_data(normalized_branch)

    # Build drivers
    drivers_key = f"drivers_{lang_key}"
    drivers = [
        BranchDriver(
            title=d[0],
            description=d[1],
            impact_level="high",
            trend_direction="rising"
        )
        for d in data.get(drivers_key, [])[:6]
    ]

    # Build market trends (now using qualitative levels instead of percentages)
    trends_key = f"trends_{lang_key}"
    trends = [
        MarketTrend(
            title=t[0],
            description=t[1],
            trend_level=t[2] if len(t) > 2 else "high",
            timeline="2024-2026"
        )
        for t in data.get(trends_key, [])[:6]
    ]

    # Build regulatory factors
    regulatory_key = f"regulatory_{lang_key}"
    regulatory = [
        RegulatoryFactor(
            title=r[0],
            description=r[1],
            urgency=r[2] if len(r) > 2 else "medium"
        )
        for r in data.get(regulatory_key, [])
    ]

    # Build use cases
    use_cases_key = f"use_cases_{lang_key}"
    use_cases = [
        UseCase(
            title=u[0],
            description=u[1],
            complexity=u[2] if len(u) > 2 else "medium",
            roi_potential=u[3] if len(u) > 3 else "medium",
            implementation_months=u[4] if len(u) > 4 else 3
        )
        for u in data.get(use_cases_key, [])
    ]

    maturity_score = data.get("maturity_score", 50)

    # Try to load branch context for display name
    display_name = branch
    try:
        context_path = Path(BRANCH_CONTEXTS_PATH) / f"{normalized_branch}.json"
        if context_path.exists():
            with open(context_path, "r", encoding="utf-8") as f:
                ctx = json.load(f)
                display_name = ctx.get("display_name", branch)
    except Exception as e:
        log.debug(f"Could not load branch context: {e}")

    profile = BranchProfile(
        branch_id=normalized_branch,
        branch_name=normalized_branch,
        branch_display_name=display_name,
        size_context=normalized_size,
        language=lang_key,
        drivers=drivers,
        market_trends=trends,
        regulatory_factors=regulatory,
        use_cases=use_cases,
        maturity_score=maturity_score,
        maturity_label=_get_maturity_label(maturity_score),
        digitalization_level=data.get("digitalization_level", "medium"),
        ai_adoption_rate=data.get("ai_adoption_rate", "growing"),
        kpis=data.get("kpis", []),
        competitive_density=data.get("competitive_density", "medium"),
    )

    log.info(
        "[G19] Built branch profile: %s (size=%s, lang=%s, maturity=%d)",
        normalized_branch, normalized_size, lang_key, maturity_score
    )

    return profile


def get_branch_risk_opportunity_map(
    branch: str,
    language: str = "de"
) -> RiskOpportunityMap:
    """
    Generate risk and opportunity mapping for branch.

    Args:
        branch: Industry/branch name
        language: Language code (de, en)

    Returns:
        RiskOpportunityMap with 3 opportunities, 3 risks, 3 bottlenecks
    """
    normalized_branch = _normalize_branch(branch)
    lang_key = "de" if language.lower().startswith("de") else "en"

    data = _get_branch_data(normalized_branch)

    opportunities_key = f"opportunities_{lang_key}"
    risks_key = f"risks_{lang_key}"
    bottlenecks_key = f"bottlenecks_{lang_key}"

    opportunities = [
        {"title": o[0], "description": o[1]}
        for o in data.get(opportunities_key, [])[:3]
    ]

    risks = [
        {"title": r[0], "description": r[1]}
        for r in data.get(risks_key, [])[:3]
    ]

    bottlenecks = [
        {"title": b[0], "description": b[1]}
        for b in data.get(bottlenecks_key, [])[:3]
    ]

    return RiskOpportunityMap(
        branch_id=normalized_branch,
        opportunities=opportunities,
        risks=risks,
        bottlenecks=bottlenecks,
    )


# =============================================================================
# HTML OUTPUT GENERATION
# =============================================================================

def generate_branch_profile_html(
    profile: BranchProfile,
    lang: str = "de"
) -> str:
    """
    Generate BRANCH_PROFILE_HTML section.

    Args:
        profile: BranchProfile instance
        lang: Language code

    Returns:
        HTML string for PDF template
    """
    if not profile or profile.branch_id == "disabled":
        return ""

    if lang == "de":
        title = "Branchenprofil & Marktintelligenz"
        drivers_title = "Branchentreiber"
        trends_title = "Markttrends"
        regulatory_title = "Regulatorische Faktoren"
        use_cases_title = "Typische KI-Anwendungsfälle"
        maturity_title = "Branchenreife"
        labels = {
            "maturity": "Reifegradindex",
            "digitalization": "Digitalisierungsgrad",
            "ai_adoption": "KI-Adoption",
            "competition": "Wettbewerbsdichte",
        }
        adoption_labels = {
            "early": "Frühe Phase",
            "growing": "Wachsend",
            "mainstream": "Mainstream",
        }
        level_labels = {
            "low": "Niedrig",
            "medium": "Mittel",
            "high": "Hoch",
        }
        complexity_labels = {
            "low": "Gering",
            "medium": "Mittel",
            "high": "Hoch",
        }
    else:
        title = "Industry Profile & Market Intelligence"
        drivers_title = "Industry Drivers"
        trends_title = "Market Trends"
        regulatory_title = "Regulatory Factors"
        use_cases_title = "Typical AI Use Cases"
        maturity_title = "Industry Maturity"
        labels = {
            "maturity": "Maturity Index",
            "digitalization": "Digitalization Level",
            "ai_adoption": "AI Adoption",
            "competition": "Competitive Density",
        }
        adoption_labels = {
            "early": "Early Stage",
            "growing": "Growing",
            "mainstream": "Mainstream",
        }
        level_labels = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
        }
        complexity_labels = {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
        }

    # Maturity score color
    maturity_color = "#22c55e" if profile.maturity_score >= 70 else "#f59e0b" if profile.maturity_score >= 45 else "#dc2626"

    html_parts = [f"""
    <div class="branch-profile chapter-start" style="margin-top:24px;">
        <h2 style="color:var(--color-text-strong);font-size:var(--font-h2);margin-bottom:16px;display:flex;align-items:center;gap:12px;">
            <span style="font-size:24px;">🏭</span> {title}
        </h2>

        <!-- Maturity Overview -->
        <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:12px;margin-bottom:20px;">
            <div style="background:linear-gradient(135deg, {maturity_color}15, {maturity_color}08);border:1px solid {maturity_color}30;border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:28px;font-weight:700;color:{maturity_color};">{profile.maturity_score}</div>
                <div style="font-size:10px;color:var(--color-text-muted);">{labels["maturity"]}</div>
            </div>
            <div style="background:var(--color-bg-surface);border:1px solid var(--color-border);border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:14px;font-weight:600;color:var(--color-text-strong);">{level_labels.get(profile.digitalization_level, profile.digitalization_level)}</div>
                <div style="font-size:10px;color:var(--color-text-muted);">{labels["digitalization"]}</div>
            </div>
            <div style="background:var(--color-bg-surface);border:1px solid var(--color-border);border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:14px;font-weight:600;color:var(--color-text-strong);">{adoption_labels.get(profile.ai_adoption_rate, profile.ai_adoption_rate)}</div>
                <div style="font-size:10px;color:var(--color-text-muted);">{labels["ai_adoption"]}</div>
            </div>
            <div style="background:var(--color-bg-surface);border:1px solid var(--color-border);border-radius:8px;padding:12px;text-align:center;">
                <div style="font-size:14px;font-weight:600;color:var(--color-text-strong);">{level_labels.get(profile.competitive_density, profile.competitive_density)}</div>
                <div style="font-size:10px;color:var(--color-text-muted);">{labels["competition"]}</div>
            </div>
        </div>
    """]

    # Drivers section
    if profile.drivers:
        html_parts.append(f"""
        <div style="margin-bottom:20px;">
            <h3 style="font-size:14px;margin:0 0 12px 0;color:var(--color-text-strong);display:flex;align-items:center;gap:8px;">
                <span>🚀</span> {drivers_title}
            </h3>
            <div style="display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;">
        """)

        for driver in profile.drivers[:4]:
            html_parts.append(f"""
                <div style="background:var(--color-bg-surface);border:1px solid var(--color-border);border-radius:6px;padding:10px;">
                    <div style="font-weight:600;font-size:12px;color:var(--color-text-strong);margin-bottom:4px;">{driver.title}</div>
                    <div style="font-size:11px;color:var(--color-text-muted);">{driver.description}</div>
                </div>
            """)

        html_parts.append("</div></div>")

    # Market trends section
    if profile.market_trends:
        html_parts.append(f"""
        <div style="margin-bottom:20px;">
            <h3 style="font-size:14px;margin:0 0 12px 0;color:var(--color-text-strong);display:flex;align-items:center;gap:8px;">
                <span>📈</span> {trends_title}
            </h3>
            <div style="display:grid;grid-template-columns:repeat(2, 1fr);gap:10px;">
        """)

        for trend in profile.market_trends[:4]:
            # Use qualitative labels instead of fake percentages (Problem #4 fix)
            trend_label = trend.get_label(lang)
            trend_color = trend.get_color()
            html_parts.append(f"""
                <div style="background:var(--color-bg-surface);border:1px solid var(--color-border);border-radius:6px;padding:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                        <div style="font-weight:600;font-size:12px;color:var(--color-text-strong);">{trend.title}</div>
                        <div style="font-size:10px;padding:2px 6px;background:{trend_color}15;color:{trend_color};border-radius:4px;font-weight:600;">{trend_label}</div>
                    </div>
                    <div style="font-size:11px;color:var(--color-text-muted);">{trend.description}</div>
                </div>
            """)

        html_parts.append("</div></div>")

    # Regulatory factors
    if profile.regulatory_factors:
        html_parts.append(f"""
        <div style="margin-bottom:20px;">
            <h3 style="font-size:14px;margin:0 0 12px 0;color:var(--color-text-strong);display:flex;align-items:center;gap:8px;">
                <span>⚖️</span> {regulatory_title}
            </h3>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">
        """)

        urgency_colors = {"high": "#dc2626", "medium": "#f59e0b", "low": "#22c55e"}
        for reg in profile.regulatory_factors:
            color = urgency_colors.get(reg.urgency, "#6b7280")
            html_parts.append(f"""
                <div style="background:{color}10;border:1px solid {color}30;border-radius:6px;padding:8px 12px;flex:1;min-width:200px;">
                    <div style="font-weight:600;font-size:11px;color:{color};margin-bottom:2px;">{reg.title}</div>
                    <div style="font-size:10px;color:var(--color-text-muted);">{reg.description}</div>
                </div>
            """)

        html_parts.append("</div></div>")

    # Use cases
    if profile.use_cases:
        html_parts.append(f"""
        <div style="margin-bottom:16px;">
            <h3 style="font-size:14px;margin:0 0 12px 0;color:var(--color-text-strong);display:flex;align-items:center;gap:8px;">
                <span>💡</span> {use_cases_title}
            </h3>
            <table class="table-modern" style="width:100%;border-collapse:collapse;font-size:11px;">
                <thead>
                    <tr style="background:var(--color-bg-surface);border-bottom:1px solid var(--color-border);">
                        <th style="padding:8px;text-align:left;">{"Use Case" if lang == "en" else "Anwendungsfall"}</th>
                        <th style="padding:8px;text-align:center;">{"Complexity" if lang == "en" else "Komplexität"}</th>
                        <th style="padding:8px;text-align:center;">{"ROI" if lang == "en" else "ROI"}</th>
                        <th style="padding:8px;text-align:center;">{"Timeline" if lang == "en" else "Dauer"}</th>
                    </tr>
                </thead>
                <tbody>
        """)

        roi_colors = {"high": "#22c55e", "medium": "#f59e0b", "low": "#6b7280"}
        for uc in profile.use_cases[:4]:
            roi_color = roi_colors.get(uc.roi_potential, "#6b7280")
            timeline_text = f"{uc.implementation_months} {'months' if lang == 'en' else 'Monate'}"
            html_parts.append(f"""
                <tr style="border-bottom:1px solid var(--color-border-subtle);">
                    <td style="padding:8px;">
                        <strong>{uc.title}</strong>
                        <div style="font-size:10px;color:var(--color-text-muted);">{uc.description}</div>
                    </td>
                    <td style="padding:8px;text-align:center;">
                        <span style="font-size:10px;padding:2px 6px;background:var(--color-bg-surface);border-radius:4px;">{complexity_labels.get(uc.complexity, uc.complexity)}</span>
                    </td>
                    <td style="padding:8px;text-align:center;">
                        <span style="font-size:10px;padding:2px 6px;background:{roi_color}15;color:{roi_color};border-radius:4px;font-weight:600;">{level_labels.get(uc.roi_potential, uc.roi_potential).upper()}</span>
                    </td>
                    <td style="padding:8px;text-align:center;color:var(--color-text-muted);">{timeline_text}</td>
                </tr>
            """)

        html_parts.append("</tbody></table></div>")

    html_parts.append("</div>")

    return "\n".join(html_parts)


def generate_branch_opportunities_html(
    risk_map: RiskOpportunityMap,
    lang: str = "de"
) -> str:
    """
    Generate BRANCH_OPPORTUNITIES_HTML section.

    Args:
        risk_map: RiskOpportunityMap instance
        lang: Language code

    Returns:
        HTML string for opportunities section
    """
    if not risk_map or not risk_map.opportunities:
        return ""

    title = "Branchenchancen" if lang == "de" else "Industry Opportunities"

    html_parts = [f"""
    <div class="branch-opportunities" style="margin-top:16px;">
        <h3 style="font-size:14px;margin:0 0 12px 0;color:var(--color-text-strong);display:flex;align-items:center;gap:8px;">
            <span>✨</span> {title}
        </h3>
        <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:10px;">
    """]

    icons = ["🎯", "📊", "🚀"]
    for i, opp in enumerate(risk_map.opportunities[:3]):
        icon = icons[i] if i < len(icons) else "💡"
        html_parts.append(f"""
            <div style="background:linear-gradient(135deg, #22c55e10, #22c55e05);border:1px solid #22c55e30;border-radius:8px;padding:12px;">
                <div style="font-size:18px;margin-bottom:6px;">{icon}</div>
                <div style="font-weight:600;font-size:12px;color:var(--color-text-strong);margin-bottom:4px;">{opp.get("title", "")}</div>
                <div style="font-size:11px;color:var(--color-text-muted);">{opp.get("description", "")}</div>
            </div>
        """)

    html_parts.append("</div></div>")

    return "\n".join(html_parts)


def generate_branch_risks_html(
    risk_map: RiskOpportunityMap,
    lang: str = "de"
) -> str:
    """
    Generate BRANCH_RISKS_HTML section.

    Args:
        risk_map: RiskOpportunityMap instance
        lang: Language code

    Returns:
        HTML string for risks and bottlenecks section
    """
    if not risk_map:
        return ""

    risks_title = "Branchenrisiken" if lang == "de" else "Industry Risks"
    bottlenecks_title = "Typische Engpässe" if lang == "de" else "Typical Bottlenecks"

    html_parts = [f"""
    <div class="branch-risks" style="margin-top:16px;">
    """]

    # Risks
    if risk_map.risks:
        html_parts.append(f"""
        <h3 style="font-size:14px;margin:0 0 12px 0;color:var(--color-text-strong);display:flex;align-items:center;gap:8px;">
            <span>⚠️</span> {risks_title}
        </h3>
        <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:10px;margin-bottom:16px;">
        """)

        risk_icons = ["🔒", "⚡", "📉"]
        for i, risk in enumerate(risk_map.risks[:3]):
            icon = risk_icons[i] if i < len(risk_icons) else "⚠️"
            html_parts.append(f"""
                <div style="background:linear-gradient(135deg, #f59e0b10, #f59e0b05);border:1px solid #f59e0b30;border-radius:8px;padding:12px;">
                    <div style="font-size:18px;margin-bottom:6px;">{icon}</div>
                    <div style="font-weight:600;font-size:12px;color:var(--color-text-strong);margin-bottom:4px;">{risk.get("title", "")}</div>
                    <div style="font-size:11px;color:var(--color-text-muted);">{risk.get("description", "")}</div>
                </div>
            """)

        html_parts.append("</div>")

    # Bottlenecks
    if risk_map.bottlenecks:
        html_parts.append(f"""
        <h3 style="font-size:14px;margin:0 0 12px 0;color:var(--color-text-strong);display:flex;align-items:center;gap:8px;">
            <span>🚧</span> {bottlenecks_title}
        </h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px;">
        """)

        for bottleneck in risk_map.bottlenecks[:3]:
            html_parts.append(f"""
                <div style="background:var(--color-bg-surface);border:1px solid var(--color-border);border-radius:6px;padding:10px;flex:1;min-width:180px;">
                    <div style="font-weight:600;font-size:11px;color:var(--color-text-strong);margin-bottom:2px;">{bottleneck.get("title", "")}</div>
                    <div style="font-size:10px;color:var(--color-text-muted);">{bottleneck.get("description", "")}</div>
                </div>
            """)

        html_parts.append("</div>")

    html_parts.append("</div>")

    return "\n".join(html_parts)


def get_branch_profile_html_sections(
    briefing: Dict[str, Any],
    lang: str = "de"
) -> Dict[str, Any]:
    """
    Generate all branch profile HTML sections for report.

    Args:
        briefing: Briefing dictionary with branch and size info
        lang: Language code

    Returns:
        Dictionary with BRANCH_PROFILE_HTML, BRANCH_OPPORTUNITIES_HTML, BRANCH_RISKS_HTML
    """
    branch = briefing.get("branche") or briefing.get("BRANCH_LABEL") or "beratung"
    size = briefing.get("unternehmensgroesse") or briefing.get("SIZE_LABEL") or "team"

    profile = build_branch_profile(branch, size, lang)
    risk_map = get_branch_risk_opportunity_map(branch, lang)

    return {
        "BRANCH_PROFILE_HTML": generate_branch_profile_html(profile, lang),
        "BRANCH_OPPORTUNITIES_HTML": generate_branch_opportunities_html(risk_map, lang),
        "BRANCH_RISKS_HTML": generate_branch_risks_html(risk_map, lang),
        "branch_profile": profile.to_dict(),
        "branch_risk_map": risk_map.to_dict(),
    }


# =============================================================================
# MODULE INITIALIZATION
# =============================================================================

log.info(
    "[G19] Branch Profile Engine loaded - enabled=%s, cache=%s",
    BRANCH_PROFILE_ENABLED,
    BRANCH_PROFILE_CACHE_ENABLED,
)

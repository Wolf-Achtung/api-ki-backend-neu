"""
Knowledge Fusion Engine - Research Aggregator 2.0 (N4.0)

PLATIN+++ v5.0 - Autonomous Engine Layer

This module resolves redundancy, overlap, and inconsistency in research
insights from multiple sources.

Features:
- Semantic clustering of insights
- Competitor deduplication
- Key signal extraction (5-Signal Model)
- Market thesis generation (Executive-Level)
- McKinsey-style citation formatting

Output:
- Consolidated market theses
- Competition patterns
- Branch-specific key signals
- Citable insights
"""

import logging
import hashlib
import re
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypedDict,
)

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class InsightCategory(Enum):
    """Categories of market insights."""
    MARKET_TREND = "market_trend"
    COMPETITOR = "competitor"
    TECHNOLOGY = "technology"
    REGULATION = "regulation"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    BENCHMARK = "benchmark"
    BEST_PRACTICE = "best_practice"


class SignalType(Enum):
    """5-Signal Model for key market signals."""
    GROWTH_SIGNAL = "growth_signal"  # Market growth indicators
    DISRUPTION_SIGNAL = "disruption_signal"  # Technology/business model disruption
    CONSOLIDATION_SIGNAL = "consolidation_signal"  # M&A, market consolidation
    REGULATION_SIGNAL = "regulation_signal"  # Regulatory changes
    TALENT_SIGNAL = "talent_signal"  # Workforce/skills shifts


class ClusterQuality(Enum):
    """Quality assessment of insight clusters."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ThesisConfidence(Enum):
    """Confidence level for market theses."""
    HIGH = "high"  # >80% support
    MEDIUM = "medium"  # 50-80% support
    LOW = "low"  # <50% support
    SPECULATIVE = "speculative"  # Limited data


# Signal keywords for detection
SIGNAL_KEYWORDS: Dict[SignalType, List[str]] = {
    SignalType.GROWTH_SIGNAL: [
        "wachstum", "growth", "expansion", "steigend", "zunahme",
        "marktanteil", "umsatzsteigerung", "skalierung", "nachfrage",
    ],
    SignalType.DISRUPTION_SIGNAL: [
        "disruption", "innovation", "transformation", "durchbruch",
        "paradigmenwechsel", "revolution", "neue technologie", "ki", "ai",
    ],
    SignalType.CONSOLIDATION_SIGNAL: [
        "übernahme", "fusion", "m&a", "konsolidierung", "zusammenschluss",
        "akquisition", "merger", "partnerschaft",
    ],
    SignalType.REGULATION_SIGNAL: [
        "regulierung", "gesetz", "compliance", "vorschrift", "eu",
        "dsgvo", "ki-verordnung", "audit", "zertifizierung",
    ],
    SignalType.TALENT_SIGNAL: [
        "fachkräfte", "skills", "qualifikation", "talent", "ausbildung",
        "weiterbildung", "recruiting", "personalentwicklung",
    ],
}

# McKinsey-style citation templates
CITATION_TEMPLATES = {
    "market_size": "Der {market}-Markt wird auf {value} geschätzt (Stand: {date}).",
    "growth_rate": "Die jährliche Wachstumsrate beträgt {value}% (CAGR {period}).",
    "competitor": "{company} hält einen Marktanteil von {value}% im {segment}-Segment.",
    "trend": "Laut {source} wird {trend} als führender Trend identifiziert.",
    "benchmark": "Best-in-Class-Unternehmen erreichen {metric} von {value}.",
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class RawInsight(TypedDict, total=False):
    """Raw insight from research sources."""
    id: str
    content: str
    source: str
    source_type: str
    timestamp: str
    category: str
    confidence: float
    metadata: Dict[str, Any]


class ClusteredInsight(TypedDict):
    """Clustered and processed insight."""
    cluster_id: str
    representative: str
    members: List[str]
    category: str
    signals: List[str]
    confidence: float
    sources: List[str]


class MarketThesis(TypedDict):
    """Executive-level market thesis."""
    thesis_id: str
    statement: str
    supporting_evidence: List[str]
    confidence: str
    category: str
    implications: List[str]
    sources: List[str]


class CompetitorProfile(TypedDict):
    """Deduplicated competitor profile."""
    name: str
    normalized_name: str
    mentions: int
    market_position: str
    strengths: List[str]
    weaknesses: List[str]
    signals: List[str]


class KeySignal(TypedDict):
    """Key market signal."""
    signal_type: str
    description: str
    evidence: List[str]
    impact_score: float
    urgency: str
    sources: List[str]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class InsightCluster:
    """Cluster of related insights."""
    cluster_id: str
    category: InsightCategory
    members: List[RawInsight] = field(default_factory=list)
    centroid_text: str = ""
    quality: ClusterQuality = ClusterQuality.MEDIUM
    signals: Set[SignalType] = field(default_factory=set)

    def add_member(self, insight: RawInsight) -> None:
        """Add an insight to the cluster."""
        self.members.append(insight)
        self._update_centroid()

    def _update_centroid(self) -> None:
        """Update centroid text (longest/most detailed member)."""
        if self.members:
            self.centroid_text = max(
                (m.get("content", "") for m in self.members),
                key=len,
            )


@dataclass
class FusionResult:
    """Result of knowledge fusion process."""
    fusion_id: str
    timestamp: datetime
    clusters: List[InsightCluster] = field(default_factory=list)
    theses: List[MarketThesis] = field(default_factory=list)
    competitors: List[CompetitorProfile] = field(default_factory=list)
    signals: List[KeySignal] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# SEMANTIC CLUSTERING
# =============================================================================

class SemanticClusterer:
    """
    Clusters insights based on semantic similarity.

    Uses TF-IDF-like scoring and keyword overlap for clustering.
    """

    SIMILARITY_THRESHOLD = 0.35  # Minimum similarity for same cluster

    def __init__(self) -> None:
        self._stopwords = {
            "der", "die", "das", "und", "in", "von", "zu", "mit", "für",
            "auf", "ist", "sind", "wird", "werden", "hat", "haben", "ein",
            "eine", "einer", "eines", "als", "auch", "an", "bei", "nach",
            "sich", "dem", "den", "des", "im", "aus", "oder", "wie",
            "the", "and", "of", "to", "in", "a", "is", "for", "on", "with",
        }

    def cluster_insights(
        self,
        insights: List[RawInsight],
        min_cluster_size: int = 2,
    ) -> List[InsightCluster]:
        """
        Cluster insights based on semantic similarity.

        Args:
            insights: List of raw insights to cluster
            min_cluster_size: Minimum members for valid cluster

        Returns:
            List of InsightClusters
        """
        if not insights:
            return []

        # Calculate pairwise similarities
        n = len(insights)
        similarities: Dict[Tuple[int, int], float] = {}

        for i in range(n):
            for j in range(i + 1, n):
                sim = self._calculate_similarity(
                    insights[i].get("content", ""),
                    insights[j].get("content", ""),
                )
                if sim >= self.SIMILARITY_THRESHOLD:
                    similarities[(i, j)] = sim

        # Agglomerative clustering
        clusters = self._agglomerative_cluster(insights, similarities)

        # Filter by minimum size
        valid_clusters = [c for c in clusters if len(c.members) >= min_cluster_size]

        # Add unclustered insights as singleton clusters (if significant)
        clustered_ids = {
            m.get("id") for c in valid_clusters for m in c.members
        }
        for insight in insights:
            if insight.get("id") not in clustered_ids:
                if len(insight.get("content", "")) > 100:  # Only significant insights
                    cluster = InsightCluster(
                        cluster_id=f"single_{insight.get('id', 'unknown')}",
                        category=self._categorize_insight(insight),
                        members=[insight],
                        centroid_text=insight.get("content", ""),
                        quality=ClusterQuality.LOW,
                    )
                    valid_clusters.append(cluster)

        log.info(
            "[N4.0-KnowledgeFusion] Clustered %d insights into %d clusters",
            len(insights),
            len(valid_clusters),
        )

        return valid_clusters

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate Jaccard similarity with TF weighting."""
        words_a = self._tokenize(text_a)
        words_b = self._tokenize(text_b)

        if not words_a or not words_b:
            return 0.0

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        base_similarity = intersection / union if union > 0 else 0.0

        # Boost for shared important words (non-stopwords of length > 5)
        important_shared = sum(
            1 for w in (words_a & words_b) if len(w) > 5
        )
        boost = min(important_shared * 0.05, 0.2)

        return min(base_similarity + boost, 1.0)

    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize and clean text."""
        words = re.findall(r"\b\w+\b", text.lower())
        return {w for w in words if w not in self._stopwords and len(w) > 2}

    def _agglomerative_cluster(
        self,
        insights: List[RawInsight],
        similarities: Dict[Tuple[int, int], float],
    ) -> List[InsightCluster]:
        """Perform agglomerative clustering."""
        n = len(insights)

        # Initialize each insight as its own cluster
        cluster_assignments = list(range(n))
        cluster_members: Dict[int, List[int]] = {i: [i] for i in range(n)}

        # Sort similarities descending
        sorted_pairs = sorted(
            similarities.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Merge clusters
        for (i, j), sim in sorted_pairs:
            ci = cluster_assignments[i]
            cj = cluster_assignments[j]

            if ci != cj:
                # Merge smaller into larger
                if len(cluster_members[ci]) < len(cluster_members[cj]):
                    ci, cj = cj, ci

                # Update assignments
                for idx in cluster_members[cj]:
                    cluster_assignments[idx] = ci
                cluster_members[ci].extend(cluster_members[cj])
                del cluster_members[cj]

        # Build InsightClusters
        result: List[InsightCluster] = []
        for cluster_id, member_indices in cluster_members.items():
            members = [insights[i] for i in member_indices]
            category = self._categorize_insight(members[0] if members else {})

            cluster = InsightCluster(
                cluster_id=f"cluster_{cluster_id}",
                category=category,
                members=members,
            )
            cluster._update_centroid()
            cluster.quality = self._assess_quality(cluster)
            cluster.signals = self._detect_signals(cluster)

            result.append(cluster)

        return result

    def _categorize_insight(self, insight: RawInsight) -> InsightCategory:
        """Categorize an insight based on content."""
        content = insight.get("content", "").lower()

        if any(w in content for w in ["wettbewerb", "konkurrent", "competitor"]):
            return InsightCategory.COMPETITOR
        elif any(w in content for w in ["technologie", "ki", "ai", "digital"]):
            return InsightCategory.TECHNOLOGY
        elif any(w in content for w in ["regulierung", "compliance", "gesetz"]):
            return InsightCategory.REGULATION
        elif any(w in content for w in ["chance", "opportunity", "potenzial"]):
            return InsightCategory.OPPORTUNITY
        elif any(w in content for w in ["risiko", "risk", "gefahr"]):
            return InsightCategory.RISK
        elif any(w in content for w in ["benchmark", "best practice"]):
            return InsightCategory.BENCHMARK
        elif any(w in content for w in ["markt", "trend", "entwicklung"]):
            return InsightCategory.MARKET_TREND
        else:
            return InsightCategory.MARKET_TREND

    def _assess_quality(self, cluster: InsightCluster) -> ClusterQuality:
        """Assess quality of a cluster."""
        # Based on number of members and source diversity
        n_members = len(cluster.members)
        sources = {m.get("source", "") for m in cluster.members}
        n_sources = len(sources)

        if n_members >= 3 and n_sources >= 2:
            return ClusterQuality.HIGH
        elif n_members >= 2:
            return ClusterQuality.MEDIUM
        else:
            return ClusterQuality.LOW

    def _detect_signals(self, cluster: InsightCluster) -> Set[SignalType]:
        """Detect signals present in cluster."""
        signals: Set[SignalType] = set()
        content = " ".join(m.get("content", "") for m in cluster.members).lower()

        for signal_type, keywords in SIGNAL_KEYWORDS.items():
            if any(kw in content for kw in keywords):
                signals.add(signal_type)

        return signals


# =============================================================================
# COMPETITOR DEDUPLICATION
# =============================================================================

class CompetitorDeduplicator:
    """
    Deduplicates and consolidates competitor information.

    Handles:
    - Name normalization
    - Profile merging
    - Strength/weakness aggregation
    """

    # Common company name variations
    NAME_VARIATIONS: Dict[str, List[str]] = {
        "microsoft": ["ms", "msft", "microsoft corp", "microsoft corporation"],
        "google": ["alphabet", "google llc", "google inc"],
        "amazon": ["aws", "amazon web services", "amazon.com"],
        "salesforce": ["sfdc", "salesforce.com"],
        "sap": ["sap se", "sap ag"],
        "oracle": ["oracle corp", "oracle corporation"],
    }

    def __init__(self) -> None:
        # Build reverse lookup
        self._name_lookup: Dict[str, str] = {}
        for canonical, variants in self.NAME_VARIATIONS.items():
            for variant in variants:
                self._name_lookup[variant.lower()] = canonical
            self._name_lookup[canonical] = canonical

    def deduplicate_competitors(
        self,
        insights: List[RawInsight],
    ) -> List[CompetitorProfile]:
        """
        Extract and deduplicate competitors from insights.

        Returns list of consolidated competitor profiles.
        """
        # Extract competitor mentions
        mentions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for insight in insights:
            content = insight.get("content", "")
            competitors = self._extract_competitors(content)

            for comp_name in competitors:
                normalized = self._normalize_name(comp_name)
                mentions[normalized].append({
                    "original_name": comp_name,
                    "content": content,
                    "source": insight.get("source", ""),
                })

        # Build profiles
        profiles: List[CompetitorProfile] = []

        for normalized_name, mention_list in mentions.items():
            if len(mention_list) >= 1:  # At least one mention
                profile = self._build_profile(normalized_name, mention_list)
                profiles.append(profile)

        # Sort by mentions
        profiles.sort(key=lambda p: p["mentions"], reverse=True)

        log.info(
            "[N4.0-KnowledgeFusion] Deduplicated %d competitor profiles",
            len(profiles),
        )

        return profiles

    def _extract_competitors(self, content: str) -> List[str]:
        """Extract competitor names from content."""
        # Simple extraction using capitalized words
        competitors: List[str] = []

        # Known company pattern
        company_pattern = re.compile(
            r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)"
            r"(?:\s+(?:GmbH|AG|Inc|Corp|Ltd|SE))?\b"
        )

        matches = company_pattern.findall(content)
        for match in matches:
            # Filter out common non-company words
            if match.lower() not in {
                "der", "die", "das", "und", "oder", "aber", "wenn",
                "the", "and", "but", "for", "with",
            }:
                # Check if it's a known company
                if self._is_likely_company(match):
                    competitors.append(match)

        return competitors

    def _is_likely_company(self, name: str) -> bool:
        """Check if name is likely a company."""
        name_lower = name.lower()

        # Check known companies
        if name_lower in self._name_lookup:
            return True

        # Check for company indicators
        company_indicators = ["gmbh", "ag", "inc", "corp", "ltd", "se", "plc"]
        if any(ind in name_lower for ind in company_indicators):
            return True

        # Check if it's a well-known tech company
        tech_companies = [
            "microsoft", "google", "amazon", "apple", "meta", "facebook",
            "salesforce", "sap", "oracle", "ibm", "cisco", "dell",
            "workday", "servicenow", "adobe", "atlassian",
        ]
        if name_lower in tech_companies:
            return True

        return False

    def _normalize_name(self, name: str) -> str:
        """Normalize company name."""
        name_lower = name.lower().strip()

        # Check direct lookup
        if name_lower in self._name_lookup:
            return self._name_lookup[name_lower]

        # Remove common suffixes
        for suffix in [" gmbh", " ag", " inc", " corp", " ltd", " se"]:
            if name_lower.endswith(suffix):
                name_lower = name_lower[:-len(suffix)]

        return name_lower.title()

    def _build_profile(
        self,
        normalized_name: str,
        mentions: List[Dict[str, Any]],
    ) -> CompetitorProfile:
        """Build competitor profile from mentions."""
        # Aggregate content
        all_content = " ".join(m["content"] for m in mentions).lower()
        sources = list({m["source"] for m in mentions})

        # Extract strengths
        strengths = self._extract_attributes(
            all_content,
            ["stärke", "vorteil", "führend", "stark", "strength", "advantage"],
        )

        # Extract weaknesses
        weaknesses = self._extract_attributes(
            all_content,
            ["schwäche", "nachteil", "schwach", "weakness", "disadvantage"],
        )

        # Detect signals
        signals = []
        for signal_type, keywords in SIGNAL_KEYWORDS.items():
            if any(kw in all_content for kw in keywords):
                signals.append(signal_type.value)

        # Determine market position
        if any(w in all_content for w in ["marktführer", "leader", "führend"]):
            market_position = "leader"
        elif any(w in all_content for w in ["challenger", "herausforderer"]):
            market_position = "challenger"
        elif any(w in all_content for w in ["nische", "spezialist", "niche"]):
            market_position = "niche"
        else:
            market_position = "competitor"

        return {
            "name": normalized_name.title(),
            "normalized_name": normalized_name.lower(),
            "mentions": len(mentions),
            "market_position": market_position,
            "strengths": strengths[:5],  # Top 5
            "weaknesses": weaknesses[:5],
            "signals": signals[:3],
        }

    def _extract_attributes(
        self,
        content: str,
        keywords: List[str],
    ) -> List[str]:
        """Extract attributes near keywords."""
        attributes: List[str] = []

        for keyword in keywords:
            # Find sentences containing keyword
            sentences = re.split(r"[.!?]", content)
            for sentence in sentences:
                if keyword in sentence.lower():
                    # Clean and add
                    cleaned = sentence.strip()
                    if len(cleaned) > 20 and len(cleaned) < 200:
                        attributes.append(cleaned)

        return attributes


# =============================================================================
# KEY SIGNAL EXTRACTOR
# =============================================================================

class KeySignalExtractor:
    """
    Extracts key market signals using 5-Signal Model.

    Signals:
    1. Growth Signal - Market expansion indicators
    2. Disruption Signal - Technology/model disruption
    3. Consolidation Signal - M&A activity
    4. Regulation Signal - Regulatory changes
    5. Talent Signal - Workforce shifts
    """

    def extract_signals(
        self,
        clusters: List[InsightCluster],
    ) -> List[KeySignal]:
        """
        Extract key signals from clustered insights.

        Returns list of KeySignals ordered by impact.
        """
        signals: List[KeySignal] = []

        for signal_type in SignalType:
            signal = self._extract_signal_type(clusters, signal_type)
            if signal:
                signals.append(signal)

        # Sort by impact score
        signals.sort(key=lambda s: s["impact_score"], reverse=True)

        log.info(
            "[N4.0-KnowledgeFusion] Extracted %d key signals",
            len(signals),
        )

        return signals

    def _extract_signal_type(
        self,
        clusters: List[InsightCluster],
        signal_type: SignalType,
    ) -> Optional[KeySignal]:
        """Extract a specific signal type."""
        relevant_clusters = [
            c for c in clusters if signal_type in c.signals
        ]

        if not relevant_clusters:
            return None

        # Aggregate evidence
        evidence: List[str] = []
        sources: Set[str] = set()

        for cluster in relevant_clusters:
            for member in cluster.members:
                if len(evidence) < 5:
                    evidence.append(member.get("content", "")[:200])
                sources.add(member.get("source", ""))

        # Calculate impact score
        impact_score = min(len(relevant_clusters) / 3, 1.0)

        # Determine urgency
        keywords = SIGNAL_KEYWORDS[signal_type]
        urgent_keywords = ["sofort", "dringend", "akut", "immediate", "urgent"]
        content = " ".join(e.lower() for e in evidence)
        has_urgent = any(kw in content for kw in urgent_keywords)

        urgency = "high" if has_urgent else ("medium" if impact_score > 0.5 else "low")

        # Generate description
        description = self._generate_signal_description(signal_type, evidence)

        return {
            "signal_type": signal_type.value,
            "description": description,
            "evidence": evidence,
            "impact_score": round(impact_score, 2),
            "urgency": urgency,
            "sources": list(sources)[:5],
        }

    def _generate_signal_description(
        self,
        signal_type: SignalType,
        evidence: List[str],
    ) -> str:
        """Generate signal description."""
        descriptions = {
            SignalType.GROWTH_SIGNAL: (
                "Marktwachstumsindikatoren zeigen positive Entwicklung. "
                "Expansion und steigende Nachfrage werden beobachtet."
            ),
            SignalType.DISRUPTION_SIGNAL: (
                "Technologische Disruption und Innovationsdynamik erkennbar. "
                "KI und Digitalisierung treiben Transformation."
            ),
            SignalType.CONSOLIDATION_SIGNAL: (
                "Konsolidierungstrends im Markt beobachtbar. "
                "M&A-Aktivitäten und strategische Partnerschaften nehmen zu."
            ),
            SignalType.REGULATION_SIGNAL: (
                "Regulatorische Veränderungen erfordern Anpassung. "
                "Compliance-Anforderungen steigen."
            ),
            SignalType.TALENT_SIGNAL: (
                "Fachkräftesituation verändert sich. "
                "Neue Skills und Qualifikationen werden nachgefragt."
            ),
        }

        return descriptions.get(signal_type, "Signal erkannt.")


# =============================================================================
# MARKET THESIS BUILDER
# =============================================================================

class MarketThesisBuilder:
    """
    Builds executive-level market theses.

    Generates McKinsey-style insights with:
    - Clear thesis statements
    - Supporting evidence
    - Strategic implications
    """

    def build_theses(
        self,
        clusters: List[InsightCluster],
        signals: List[KeySignal],
        competitors: List[CompetitorProfile],
    ) -> List[MarketThesis]:
        """
        Build market theses from analyzed data.

        Returns list of MarketTheses.
        """
        theses: List[MarketThesis] = []

        # Thesis from high-quality clusters
        for cluster in clusters:
            if cluster.quality == ClusterQuality.HIGH:
                thesis = self._build_cluster_thesis(cluster)
                if thesis:
                    theses.append(thesis)

        # Thesis from strong signals
        for signal in signals:
            if signal["impact_score"] >= 0.5:
                thesis = self._build_signal_thesis(signal)
                if thesis:
                    theses.append(thesis)

        # Thesis from competitor landscape
        if len(competitors) >= 3:
            thesis = self._build_competitive_thesis(competitors)
            if thesis:
                theses.append(thesis)

        # Deduplicate similar theses
        theses = self._deduplicate_theses(theses)

        log.info(
            "[N4.0-KnowledgeFusion] Built %d market theses",
            len(theses),
        )

        return theses

    def _build_cluster_thesis(
        self,
        cluster: InsightCluster,
    ) -> Optional[MarketThesis]:
        """Build thesis from insight cluster."""
        if not cluster.members:
            return None

        # Generate thesis statement
        category_statements = {
            InsightCategory.MARKET_TREND: (
                "Der Markt zeigt einen deutlichen Trend zu {focus}, "
                "der strategische Implikationen für die Positionierung hat."
            ),
            InsightCategory.TECHNOLOGY: (
                "Technologische Entwicklungen im Bereich {focus} "
                "verändern die Wettbewerbsdynamik fundamental."
            ),
            InsightCategory.COMPETITOR: (
                "Die Wettbewerbslandschaft verschiebt sich: "
                "{focus} gewinnt an strategischer Bedeutung."
            ),
            InsightCategory.OPPORTUNITY: (
                "Signifikante Marktchancen entstehen durch {focus}, "
                "die proaktives Handeln erfordern."
            ),
            InsightCategory.RISK: (
                "Aufkommende Risiken im Bereich {focus} "
                "erfordern strategische Absicherung."
            ),
            InsightCategory.REGULATION: (
                "Regulatorische Entwicklungen zu {focus} "
                "erfordern Compliance-Anpassungen."
            ),
            InsightCategory.BENCHMARK: (
                "Best-Practice-Analysen zeigen: {focus} "
                "differenziert Marktführer von Nachzüglern."
            ),
            InsightCategory.BEST_PRACTICE: (
                "Führende Unternehmen setzen auf {focus} "
                "als Differenzierungsmerkmal."
            ),
        }

        # Extract focus from centroid
        focus = self._extract_focus(cluster.centroid_text)

        template = category_statements.get(
            cluster.category,
            "Marktanalyse zeigt: {focus} ist strategisch relevant."
        )
        statement = template.format(focus=focus)

        # Supporting evidence
        evidence = [
            m.get("content", "")[:150] + "..."
            for m in cluster.members[:3]
        ]

        # Implications
        implications = self._generate_implications(cluster.category)

        # Sources
        sources = list({m.get("source", "") for m in cluster.members})

        # Confidence
        confidence = (
            ThesisConfidence.HIGH.value
            if cluster.quality == ClusterQuality.HIGH
            else ThesisConfidence.MEDIUM.value
        )

        return {
            "thesis_id": f"thesis_{cluster.cluster_id}",
            "statement": statement,
            "supporting_evidence": evidence,
            "confidence": confidence,
            "category": cluster.category.value,
            "implications": implications,
            "sources": sources[:5],
        }

    def _build_signal_thesis(self, signal: KeySignal) -> Optional[MarketThesis]:
        """Build thesis from key signal."""
        signal_statements = {
            SignalType.GROWTH_SIGNAL.value: (
                "Der Markt befindet sich in einer Wachstumsphase mit "
                "signifikanten Expansionsmöglichkeiten."
            ),
            SignalType.DISRUPTION_SIGNAL.value: (
                "Disruptive Technologien transformieren die Branche grundlegend – "
                "First-Mover-Vorteile sind entscheidend."
            ),
            SignalType.CONSOLIDATION_SIGNAL.value: (
                "Marktkonsolidierung schreitet voran – "
                "strategische Positionierung wird kritisch."
            ),
            SignalType.REGULATION_SIGNAL.value: (
                "Regulatorische Veränderungen schaffen neue Rahmenbedingungen – "
                "Compliance wird zum Wettbewerbsfaktor."
            ),
            SignalType.TALENT_SIGNAL.value: (
                "Der Wettbewerb um Talente intensiviert sich – "
                "Personalstrategie wird zum Differenziator."
            ),
        }

        statement = signal_statements.get(
            signal["signal_type"],
            f"Marktsignal: {signal['description']}"
        )

        implications = [
            "Strategische Neuausrichtung prüfen",
            "Investitionsplanung anpassen",
            "Monitoring-Prozess etablieren",
        ]

        return {
            "thesis_id": f"thesis_signal_{signal['signal_type']}",
            "statement": statement,
            "supporting_evidence": signal["evidence"][:3],
            "confidence": (
                ThesisConfidence.HIGH.value
                if signal["impact_score"] > 0.7
                else ThesisConfidence.MEDIUM.value
            ),
            "category": signal["signal_type"],
            "implications": implications,
            "sources": signal["sources"],
        }

    def _build_competitive_thesis(
        self,
        competitors: List[CompetitorProfile],
    ) -> Optional[MarketThesis]:
        """Build thesis from competitive landscape."""
        leaders = [c for c in competitors if c["market_position"] == "leader"]
        challengers = [c for c in competitors if c["market_position"] == "challenger"]

        if leaders:
            leader_names = ", ".join(c["name"] for c in leaders[:3])
            statement = (
                f"Die Wettbewerbslandschaft wird von {leader_names} dominiert. "
                "Differenzierung erfordert klare Positionierung in Nischensegmenten "
                "oder technologische Innovation."
            )
        else:
            statement = (
                "Der Markt ist fragmentiert ohne klare Marktführer – "
                "Konsolidierungspotenzial und Opportunitäten für aggressive Expansion."
            )

        evidence = [
            f"{c['name']}: {c['market_position']} mit {c['mentions']} Erwähnungen"
            for c in competitors[:5]
        ]

        return {
            "thesis_id": "thesis_competitive_landscape",
            "statement": statement,
            "supporting_evidence": evidence,
            "confidence": ThesisConfidence.MEDIUM.value,
            "category": "competitive",
            "implications": [
                "Wettbewerbspositionierung schärfen",
                "Differenzierungsmerkmale entwickeln",
                "Partnerschaftspotenziale evaluieren",
            ],
            "sources": [],
        }

    def _extract_focus(self, text: str) -> str:
        """Extract main focus from text."""
        # Find most frequent significant terms
        words = re.findall(r"\b[A-Za-zÄÖÜäöüß]{4,}\b", text)
        word_counts: Dict[str, int] = defaultdict(int)

        stopwords = {
            "dass", "wird", "werden", "sind", "haben", "kann", "können",
            "durch", "auch", "oder", "sowie", "dieser", "diese", "dieses",
        }

        for word in words:
            if word.lower() not in stopwords:
                word_counts[word.lower()] += 1

        if word_counts:
            top_word = max(word_counts.items(), key=lambda x: x[1])[0]
            return str(top_word).title()

        return "diesen Bereich"

    def _generate_implications(
        self,
        category: InsightCategory,
    ) -> List[str]:
        """Generate strategic implications for category."""
        implications_map = {
            InsightCategory.MARKET_TREND: [
                "Strategische Roadmap anpassen",
                "Ressourcenallokation überprüfen",
                "Marktbeobachtung intensivieren",
            ],
            InsightCategory.TECHNOLOGY: [
                "Technologie-Roadmap aktualisieren",
                "Build-vs-Buy-Entscheidung treffen",
                "Pilotprojekt initiieren",
            ],
            InsightCategory.COMPETITOR: [
                "Wettbewerbsstrategie schärfen",
                "Differenzierungspotenziale identifizieren",
                "Preispositionierung prüfen",
            ],
            InsightCategory.OPPORTUNITY: [
                "Business Case entwickeln",
                "Schnelle Pilotierung evaluieren",
                "Investitionsrahmen definieren",
            ],
            InsightCategory.RISK: [
                "Risikomitigationsplan erstellen",
                "Monitoring etablieren",
                "Contingency-Planung durchführen",
            ],
            InsightCategory.REGULATION: [
                "Compliance-Assessment durchführen",
                "Prozessanpassungen planen",
                "Schulungsmaßnahmen initiieren",
            ],
            InsightCategory.BENCHMARK: [
                "Gap-Analyse durchführen",
                "Best Practices adaptieren",
                "KPIs anpassen",
            ],
            InsightCategory.BEST_PRACTICE: [
                "Lessons Learned dokumentieren",
                "Transferpotenziale identifizieren",
                "Implementierungsplan entwickeln",
            ],
        }

        return implications_map.get(category, [
            "Strategische Bewertung durchführen",
            "Handlungsoptionen entwickeln",
        ])

    def _deduplicate_theses(
        self,
        theses: List[MarketThesis],
    ) -> List[MarketThesis]:
        """Remove duplicate or very similar theses."""
        if len(theses) <= 1:
            return theses

        unique: List[MarketThesis] = []
        seen_statements: Set[str] = set()

        for thesis in theses:
            # Simple deduplication based on statement similarity
            statement_key = thesis["statement"][:50].lower()
            if statement_key not in seen_statements:
                unique.append(thesis)
                seen_statements.add(statement_key)

        return unique


# =============================================================================
# KNOWLEDGE FUSION ENGINE
# =============================================================================

class KnowledgeFusionEngine:
    """
    Main engine for knowledge fusion and research aggregation.

    Combines:
    - Semantic clustering
    - Competitor deduplication
    - Signal extraction
    - Thesis generation
    """

    def __init__(self) -> None:
        self._clusterer = SemanticClusterer()
        self._deduplicator = CompetitorDeduplicator()
        self._signal_extractor = KeySignalExtractor()
        self._thesis_builder = MarketThesisBuilder()
        self._lock = threading.RLock()

        log.info("[N4.0-KnowledgeFusion] KnowledgeFusionEngine initialized")

    def fuse_insights(
        self,
        raw_insights: List[RawInsight],
    ) -> FusionResult:
        """
        Perform complete knowledge fusion on raw insights.

        Returns FusionResult with all processed data.
        """
        fusion_id = hashlib.sha256(
            datetime.now().isoformat().encode()
        ).hexdigest()[:12]

        log.info(
            "[N4.0-KnowledgeFusion] Starting fusion of %d insights",
            len(raw_insights),
        )

        # Cluster insights
        clusters = self._clusterer.cluster_insights(raw_insights)

        # Extract competitors
        competitors = self._deduplicator.deduplicate_competitors(raw_insights)

        # Extract key signals
        signals = self._signal_extractor.extract_signals(clusters)

        # Build market theses
        theses = self._thesis_builder.build_theses(clusters, signals, competitors)

        # Compile statistics
        statistics = {
            "input_insights": len(raw_insights),
            "clusters_created": len(clusters),
            "competitors_identified": len(competitors),
            "signals_extracted": len(signals),
            "theses_generated": len(theses),
            "high_quality_clusters": sum(
                1 for c in clusters if c.quality == ClusterQuality.HIGH
            ),
        }

        result = FusionResult(
            fusion_id=fusion_id,
            timestamp=datetime.now(),
            clusters=clusters,
            theses=theses,
            competitors=competitors,
            signals=signals,
            statistics=statistics,
        )

        log.info(
            "[N4.0-KnowledgeFusion] Fusion complete: %d clusters, %d theses, %d signals",
            len(clusters),
            len(theses),
            len(signals),
        )

        return result

    def cluster_insights(
        self,
        insights: List[RawInsight],
    ) -> List[ClusteredInsight]:
        """
        Cluster insights and return formatted results.

        Convenience method for direct cluster access.
        """
        clusters = self._clusterer.cluster_insights(insights)

        return [
            {
                "cluster_id": c.cluster_id,
                "representative": c.centroid_text[:200],
                "members": [m.get("content", "")[:100] for m in c.members],
                "category": c.category.value,
                "signals": [s.value for s in c.signals],
                "confidence": 0.8 if c.quality == ClusterQuality.HIGH else 0.5,
                "sources": list({m.get("source", "") for m in c.members}),
            }
            for c in clusters
        ]

    def deduplicate_competitors(
        self,
        insights: List[RawInsight],
    ) -> List[CompetitorProfile]:
        """Deduplicate competitors from insights."""
        return self._deduplicator.deduplicate_competitors(insights)

    def extract_key_signals(
        self,
        insights: List[RawInsight],
    ) -> List[KeySignal]:
        """Extract key signals from insights."""
        clusters = self._clusterer.cluster_insights(insights)
        return self._signal_extractor.extract_signals(clusters)

    def build_market_thesis(
        self,
        insights: List[RawInsight],
    ) -> List[MarketThesis]:
        """Build market theses from insights."""
        clusters = self._clusterer.cluster_insights(insights)
        signals = self._signal_extractor.extract_signals(clusters)
        competitors = self._deduplicator.deduplicate_competitors(insights)
        return self._thesis_builder.build_theses(clusters, signals, competitors)


# =============================================================================
# SINGLETON & HELPER FUNCTIONS
# =============================================================================

_fusion_instance: Optional[KnowledgeFusionEngine] = None
_fusion_lock = threading.Lock()


def get_knowledge_fusion_engine() -> KnowledgeFusionEngine:
    """Get or create singleton knowledge fusion engine."""
    global _fusion_instance

    if _fusion_instance is None:
        with _fusion_lock:
            if _fusion_instance is None:
                _fusion_instance = KnowledgeFusionEngine()

    return _fusion_instance


def fuse_research_insights(
    raw_insights: List[RawInsight],
) -> Dict[str, Any]:
    """
    Fuse research insights and return structured results.

    Convenience function for external use.
    """
    engine = get_knowledge_fusion_engine()
    result = engine.fuse_insights(raw_insights)

    return {
        "fusion_id": result.fusion_id,
        "timestamp": result.timestamp.isoformat(),
        "theses": result.theses,
        "competitors": result.competitors,
        "signals": result.signals,
        "statistics": result.statistics,
    }


def cluster_insights(
    insights: List[RawInsight],
) -> List[ClusteredInsight]:
    """
    Cluster insights semantically.

    Convenience function for external use.
    """
    engine = get_knowledge_fusion_engine()
    return engine.cluster_insights(insights)


def extract_key_signals(
    insights: List[RawInsight],
) -> List[KeySignal]:
    """
    Extract key market signals.

    Convenience function for external use.
    """
    engine = get_knowledge_fusion_engine()
    return engine.extract_key_signals(insights)


def build_market_thesis(
    insights: List[RawInsight],
) -> List[MarketThesis]:
    """
    Build executive-level market theses.

    Convenience function for external use.
    """
    engine = get_knowledge_fusion_engine()
    return engine.build_market_thesis(insights)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "InsightCategory",
    "SignalType",
    "ClusterQuality",
    "ThesisConfidence",
    # Classes
    "KnowledgeFusionEngine",
    "SemanticClusterer",
    "CompetitorDeduplicator",
    "KeySignalExtractor",
    "MarketThesisBuilder",
    # Data classes
    "InsightCluster",
    "FusionResult",
    # Type definitions
    "RawInsight",
    "ClusteredInsight",
    "MarketThesis",
    "CompetitorProfile",
    "KeySignal",
    # Functions
    "get_knowledge_fusion_engine",
    "fuse_research_insights",
    "cluster_insights",
    "extract_key_signals",
    "build_market_thesis",
    # Constants
    "SIGNAL_KEYWORDS",
    "CITATION_TEMPLATES",
]

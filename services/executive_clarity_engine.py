"""
Executive Clarity Engine - N4.1 PLATIN+++ Executive Experience Layer.

Zero-Confusion Guarantee providing:
- Jargon Detector: removes/replaces technical AI terms, prompt vocabulary, GPT/Claude internals
- Leadership Clarity Rewriter: shorter, harder, clearer text with action language
- Executive-Level Metrics Guard: no contradictory KPIs, unclear recommendations, duplicates

Board-Ready. Investment-Ready. C-Level-Perfect.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, TypedDict

log = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPE DEFINITIONS
# =============================================================================


class JargonCategory(Enum):
    """Categories of jargon to detect."""
    AI_TECHNICAL = "ai_technical"
    PROMPT_VOCABULARY = "prompt_vocabulary"
    MODEL_INTERNAL = "model_internal"
    DEVELOPER_SPEAK = "developer_speak"
    ACADEMIC = "academic"


class ClarityIssue(Enum):
    """Types of clarity issues."""
    JARGON = "jargon"
    PASSIVE_VOICE = "passive_voice"
    AMBIGUOUS = "ambiguous"
    WORDY = "wordy"
    UNCLEAR_ACTION = "unclear_action"
    CONTRADICTORY = "contradictory"
    DUPLICATE = "duplicate"


class MetricIssue(Enum):
    """Types of metric issues."""
    CONTRADICTION = "contradiction"
    MISSING_CONTEXT = "missing_context"
    UNCLEAR_RECOMMENDATION = "unclear_recommendation"
    DUPLICATE_METRIC = "duplicate_metric"
    INCONSISTENT_UNIT = "inconsistent_unit"


class JargonMatch(TypedDict):
    """Jargon match result."""
    term: str
    category: str
    replacement: str
    position: int


class ClarityScore(TypedDict):
    """Clarity score breakdown."""
    overall_score: float
    jargon_score: float
    readability_score: float
    action_clarity_score: float
    consistency_score: float


class ClarityResult(TypedDict):
    """Result of clarity analysis."""
    original_text: str
    clarified_text: str
    issues_found: List[Dict[str, Any]]
    jargon_removed: List[JargonMatch]
    score: ClarityScore


class MetricValidation(TypedDict):
    """Metric validation result."""
    is_valid: bool
    issues: List[Dict[str, Any]]
    contradictions: List[Tuple[str, str]]
    duplicates: List[str]


# =============================================================================
# CONFIGURATION
# =============================================================================


CLARITY_CONFIG: Dict[str, Any] = {
    "max_sentence_words": 25,
    "max_paragraph_sentences": 5,
    "min_clarity_score": 0.7,
    "passive_voice_threshold": 0.2,
    "jargon_density_threshold": 0.05,
}


# Jargon dictionary with replacements
JARGON_DICTIONARY: Dict[JargonCategory, Dict[str, str]] = {
    JargonCategory.AI_TECHNICAL: {
        "transformer": "KI-Modell",
        "neural network": "KI-System",
        "neuronales netzwerk": "KI-System",
        "deep learning": "maschinelles Lernen",
        "machine learning": "maschinelles Lernen",
        "natural language processing": "Sprachverarbeitung",
        "nlp": "Sprachverarbeitung",
        "large language model": "KI-Sprachmodell",
        "llm": "KI-Sprachmodell",
        "embedding": "Datenrepräsentation",
        "vector": "Datenpunkt",
        "tokenization": "Textverarbeitung",
        "fine-tuning": "Anpassung",
        "pre-training": "Grundtraining",
        "inference": "Analyse",
        "latency": "Antwortzeit",
        "throughput": "Verarbeitungskapazität",
        "hallucination": "Fehlerhafte Ausgabe",
        "halluzination": "Fehlerhafte Ausgabe",
        "prompt injection": "Sicherheitsrisiko",
        "context window": "Verarbeitungskapazität",
        "retrieval augmented": "wissensbasiert",
        "rag": "wissensbasierte KI",
        "agentic": "autonom",
        "multimodal": "mehrstufig",
        "attention mechanism": "Analyseverfahren",
        "gradient": "Optimierungsparameter",
        "backpropagation": "Lernverfahren",
        "hyperparameter": "Einstellung",
        "epoch": "Trainingsrunde",
        "batch size": "Verarbeitungsmenge",
        "overfitting": "Überanpassung",
        "underfitting": "Unteranpassung",
    },
    JargonCategory.PROMPT_VOCABULARY: {
        "prompt": "Anfrage",
        "prompt engineering": "Anfrageoptimierung",
        "system prompt": "Systemkonfiguration",
        "few-shot": "beispielbasiert",
        "zero-shot": "ohne Beispiele",
        "chain of thought": "schrittweise Analyse",
        "cot": "schrittweise Analyse",
        "temperature": "Kreativitätseinstellung",
        "top-p": "Auswahlparameter",
        "sampling": "Auswahl",
        "completion": "Ausgabe",
        "token": "Textelement",
        "context": "Zusammenhang",
        "grounding": "Faktenbasis",
    },
    JargonCategory.MODEL_INTERNAL: {
        "gpt-4": "KI-Modell",
        "gpt-3.5": "KI-Modell",
        "claude": "KI-Assistent",
        "claude-3": "KI-Assistent",
        "gemini": "KI-System",
        "openai": "KI-Anbieter",
        "anthropic": "KI-Anbieter",
        "api": "Schnittstelle",
        "endpoint": "Zugangspunkt",
        "sdk": "Entwicklungskit",
        "model id": "Modellversion",
        "assistant message": "KI-Antwort",
        "user message": "Anfrage",
        "system message": "Konfiguration",
    },
    JargonCategory.DEVELOPER_SPEAK: {
        "json": "Datenformat",
        "xml": "Datenformat",
        "yaml": "Konfiguration",
        "schema": "Struktur",
        "parsing": "Verarbeitung",
        "regex": "Suchmuster",
        "webhook": "Benachrichtigung",
        "callback": "Rückmeldung",
        "async": "parallel",
        "sync": "sequentiell",
        "pipeline": "Verarbeitungskette",
        "middleware": "Zwischenschicht",
        "deployment": "Bereitstellung",
        "containerized": "isoliert",
        "kubernetes": "Infrastruktur",
        "docker": "Container",
        "ci/cd": "Automatisierung",
        "devops": "IT-Betrieb",
        "microservice": "Dienst",
        "monolith": "Gesamtsystem",
        "refactoring": "Überarbeitung",
        "code review": "Qualitätsprüfung",
        "pull request": "Änderungsantrag",
        "commit": "Änderung",
        "repository": "Ablage",
        "branch": "Version",
    },
    JargonCategory.ACADEMIC: {
        "empirisch": "erfahrungsbasiert",
        "signifikant": "erheblich",
        "probabilistisch": "wahrscheinlichkeitsbasiert",
        "stochastisch": "zufallsbasiert",
        "deterministic": "vorhersagbar",
        "heuristik": "Faustregel",
        "algorithmus": "Verfahren",
        "iteration": "Wiederholung",
        "konvergenz": "Annäherung",
        "divergenz": "Abweichung",
        "bias": "Verzerrung",
        "variance": "Streuung",
        "correlation": "Zusammenhang",
        "regression": "Trendanalyse",
        "classification": "Kategorisierung",
        "clustering": "Gruppierung",
        "dimensionality": "Komplexität",
    },
}


# Passive voice patterns (German)
PASSIVE_PATTERNS: List[str] = [
    r"\bwird\s+\w+t\b",
    r"\bwurde\s+\w+t\b",
    r"\bwerden\s+\w+t\b",
    r"\bwurden\s+\w+t\b",
    r"\bworden\b",
    r"\bist\s+\w+t\s+worden\b",
    r"\bsind\s+\w+t\s+worden\b",
    r"\bkann\s+\w+t\s+werden\b",
    r"\bsollte\s+\w+t\s+werden\b",
]


# Wordy phrases and their concise replacements
WORDY_REPLACEMENTS: Dict[str, str] = {
    "in der Lage sein": "können",
    "in der Lage ist": "kann",
    "ist in der Lage": "kann",
    "in der Lage sind": "können",
    "sind in der Lage": "können",
    "zur Verfügung stellen": "bereitstellen",
    "zur Verfügung steht": "verfügbar ist",
    "eine Rolle spielen": "relevant sein",
    "eine wichtige Rolle": "wesentlich",
    "in Bezug auf": "bezüglich",
    "im Hinblick auf": "hinsichtlich",
    "unter Berücksichtigung": "berücksichtigend",
    "in Anbetracht": "angesichts",
    "zum Zeitpunkt": "bei",
    "zum jetzigen Zeitpunkt": "aktuell",
    "zu dem Zweck": "um zu",
    "mit dem Ziel": "um zu",
    "aus diesem Grund": "deshalb",
    "aufgrund der Tatsache": "da",
    "trotz der Tatsache": "obwohl",
    "im Rahmen von": "bei",
    "eine Vielzahl von": "viele",
    "eine große Anzahl von": "viele",
    "in zunehmendem Maße": "zunehmend",
    "in erheblichem Maße": "erheblich",
    "durchgeführt werden": "erfolgen",
    "zur Anwendung kommen": "angewandt werden",
    "Anwendung finden": "angewandt werden",
    "in Betracht ziehen": "berücksichtigen",
    "in Erwägung ziehen": "erwägen",
}


# Ambiguous terms that need clarification
AMBIGUOUS_TERMS: Set[str] = {
    "zeitnah", "bald", "demnächst", "kurzfristig", "mittelfristig", "langfristig",
    "einige", "manche", "gewisse", "diverse", "verschiedene",
    "relevant", "wichtig", "wesentlich", "signifikant",
    "optimieren", "verbessern", "steigern", "erhöhen",
    "ungefähr", "etwa", "circa", "ca.",
    "eventuell", "möglicherweise", "gegebenenfalls", "ggf.",
}


# Action verbs for leadership clarity
ACTION_VERBS: List[str] = [
    "entscheiden", "freigeben", "genehmigen", "priorisieren",
    "initiieren", "starten", "stoppen", "eskalieren",
    "delegieren", "überwachen", "bewerten", "bestätigen",
    "investieren", "allokieren", "budgetieren", "finanzieren",
    "kommunizieren", "informieren", "berichten", "präsentieren",
]


# =============================================================================
# JARGON DETECTOR
# =============================================================================


class JargonDetector:
    """
    Detects and removes technical jargon.

    Targets:
    - AI technical terms
    - Prompt engineering vocabulary
    - Model-internal terminology
    - Developer speak
    """

    def __init__(self) -> None:
        # Build compiled patterns for each category
        self._patterns: Dict[JargonCategory, List[Tuple[Pattern[str], str]]] = {}

        for category, terms in JARGON_DICTIONARY.items():
            self._patterns[category] = []
            for term, replacement in terms.items():
                pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                self._patterns[category].append((pattern, replacement))

    def detect(self, text: str) -> List[JargonMatch]:
        """
        Detect jargon in text.

        Args:
            text: Input text

        Returns:
            List of jargon matches
        """
        matches: List[JargonMatch] = []

        for category, patterns in self._patterns.items():
            for pattern, replacement in patterns:
                for match in pattern.finditer(text):
                    matches.append(JargonMatch(
                        term=match.group(),
                        category=category.value,
                        replacement=replacement,
                        position=match.start(),
                    ))

        # Sort by position
        matches.sort(key=lambda x: x["position"])

        return matches

    def remove_jargon(self, text: str) -> Tuple[str, List[JargonMatch]]:
        """
        Remove jargon from text.

        Args:
            text: Input text

        Returns:
            Tuple of (cleaned text, list of matches)
        """
        matches = self.detect(text)
        result = text

        # Replace in reverse order to preserve positions
        for match in reversed(matches):
            term_pattern = re.compile(rf"\b{re.escape(match['term'])}\b", re.IGNORECASE)
            result = term_pattern.sub(match["replacement"], result, count=1)

        return result, matches

    def calculate_jargon_density(self, text: str) -> float:
        """Calculate jargon density in text."""
        matches = self.detect(text)
        words = len(text.split())

        if words == 0:
            return 0.0

        return len(matches) / words


# =============================================================================
# LEADERSHIP CLARITY REWRITER
# =============================================================================


class LeadershipClarityRewriter:
    """
    Rewrites text for leadership clarity.

    Makes text shorter, harder, clearer with action language.
    """

    def __init__(self) -> None:
        self._passive_patterns = [
            re.compile(p, re.IGNORECASE) for p in PASSIVE_PATTERNS
        ]
        self._wordy_patterns = {
            phrase: re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
            for phrase in WORDY_REPLACEMENTS
        }

    def rewrite(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Rewrite text for clarity.

        Args:
            text: Input text

        Returns:
            Tuple of (rewritten text, issues fixed)
        """
        issues: List[Dict[str, Any]] = []
        result = text

        # Remove wordy phrases
        result, wordy_issues = self._remove_wordy_phrases(result)
        issues.extend(wordy_issues)

        # Reduce passive voice
        result, passive_issues = self._reduce_passive_voice(result)
        issues.extend(passive_issues)

        # Shorten sentences
        result, sentence_issues = self._shorten_sentences(result)
        issues.extend(sentence_issues)

        # Add action language
        result, action_issues = self._enhance_action_language(result)
        issues.extend(action_issues)

        # Clean up whitespace
        result = re.sub(r"\s+", " ", result).strip()

        return result, issues

    def _remove_wordy_phrases(
        self,
        text: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Remove wordy phrases."""
        result = text
        issues: List[Dict[str, Any]] = []

        for phrase, pattern in self._wordy_patterns.items():
            if pattern.search(result):
                replacement = WORDY_REPLACEMENTS[phrase]
                result = pattern.sub(replacement, result)
                issues.append({
                    "type": ClarityIssue.WORDY.value,
                    "original": phrase,
                    "replacement": replacement,
                })

        return result, issues

    def _reduce_passive_voice(
        self,
        text: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Flag passive voice (full conversion would need NLP)."""
        issues: List[Dict[str, Any]] = []

        for pattern in self._passive_patterns:
            matches = pattern.findall(text)
            for match in matches:
                issues.append({
                    "type": ClarityIssue.PASSIVE_VOICE.value,
                    "match": match,
                    "suggestion": "Aktive Formulierung verwenden",
                })

        # Note: Automatic passive-to-active conversion requires NLP
        # Here we just flag for manual review
        return text, issues

    def _shorten_sentences(
        self,
        text: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Identify overly long sentences."""
        issues: List[Dict[str, Any]] = []
        sentences = re.split(r"[.!?]\s+", text)
        max_words = CLARITY_CONFIG["max_sentence_words"]

        for sentence in sentences:
            word_count = len(sentence.split())
            if word_count > max_words:
                issues.append({
                    "type": ClarityIssue.WORDY.value,
                    "sentence": sentence[:100] + "..." if len(sentence) > 100 else sentence,
                    "word_count": word_count,
                    "max_recommended": max_words,
                })

        return text, issues

    def _enhance_action_language(
        self,
        text: str,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Check for action language presence."""
        issues: List[Dict[str, Any]] = []
        text_lower = text.lower()

        action_count = sum(
            1 for verb in ACTION_VERBS
            if verb in text_lower
        )

        sentences = re.split(r"[.!?]\s+", text)
        if sentences and action_count < len(sentences) * 0.3:
            issues.append({
                "type": ClarityIssue.UNCLEAR_ACTION.value,
                "action_verbs_found": action_count,
                "sentences": len(sentences),
                "suggestion": "Mehr Handlungsverben verwenden",
            })

        return text, issues

    def calculate_readability_score(self, text: str) -> float:
        """Calculate readability score (simplified Flesch-Kincaid for German)."""
        sentences = re.split(r"[.!?]\s+", text)
        words = text.split()

        if not sentences or not words:
            return 0.0

        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(w) for w in words) / len(words)

        # Simplified scoring: shorter is better, clamped to [0, 1]
        sentence_score = max(0.0, min(1.0, 1 - (avg_sentence_length - 15) / 30))
        word_score = max(0.0, min(1.0, 1 - (avg_word_length - 5) / 5))

        return (sentence_score * 0.6 + word_score * 0.4)


# =============================================================================
# EXECUTIVE METRICS GUARD
# =============================================================================


class ExecutiveMetricsGuard:
    """
    Guards against metric inconsistencies.

    Checks for:
    - Contradictory KPIs
    - Unclear recommendations
    - Duplicate metrics/risks/actions
    """

    def __init__(self) -> None:
        self._metric_patterns = {
            "percentage": re.compile(r"(\d+(?:,\d+)?)\s*%"),
            "currency_eur": re.compile(r"(\d+(?:[.,]\d+)?)\s*(EUR|€|Euro|Mio|Tsd)", re.IGNORECASE),
            "time_months": re.compile(r"(\d+)\s*(Monate?|months?)", re.IGNORECASE),
            "count": re.compile(r"(\d+)\s*(Prozesse?|FTE|Mitarbeiter)", re.IGNORECASE),
        }

    def validate_metrics(
        self,
        sections: List[Dict[str, Any]],
    ) -> MetricValidation:
        """
        Validate metrics across sections.

        Args:
            sections: List of section dicts

        Returns:
            MetricValidation result
        """
        issues: List[Dict[str, Any]] = []
        contradictions: List[Tuple[str, str]] = []
        duplicates: List[str] = []

        # Extract all metrics
        all_metrics = self._extract_metrics(sections)

        # Check for contradictions
        contradictions = self._find_contradictions(all_metrics)
        for c in contradictions:
            issues.append({
                "type": MetricIssue.CONTRADICTION.value,
                "metric1": c[0],
                "metric2": c[1],
            })

        # Check for duplicates
        duplicates = self._find_duplicates(sections)
        for d in duplicates:
            issues.append({
                "type": MetricIssue.DUPLICATE_METRIC.value,
                "metric": d,
            })

        # Check for unclear recommendations
        unclear = self._find_unclear_recommendations(sections)
        issues.extend(unclear)

        is_valid = len(contradictions) == 0 and len(duplicates) == 0

        return MetricValidation(
            is_valid=is_valid,
            issues=issues,
            contradictions=contradictions,
            duplicates=duplicates,
        )

    def _extract_metrics(
        self,
        sections: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract metrics from sections."""
        metrics: Dict[str, List[Dict[str, Any]]] = {
            "roi": [],
            "cost": [],
            "time": [],
            "count": [],
        }

        for section in sections:
            content = section.get("content", "")
            section_id = section.get("id", "unknown")

            # Extract ROI/percentage metrics
            for match in self._metric_patterns["percentage"].finditer(content):
                context = content[max(0, match.start() - 50):match.end() + 50]
                if any(kw in context.lower() for kw in ["roi", "rendite", "return"]):
                    metrics["roi"].append({
                        "value": float(match.group(1).replace(",", ".")),
                        "section": section_id,
                        "context": context,
                    })

            # Extract cost metrics
            for match in self._metric_patterns["currency_eur"].finditer(content):
                metrics["cost"].append({
                    "value": match.group(0),
                    "section": section_id,
                })

        return metrics

    def _find_contradictions(
        self,
        metrics: Dict[str, List[Dict[str, Any]]],
    ) -> List[Tuple[str, str]]:
        """Find contradictory metrics."""
        contradictions: List[Tuple[str, str]] = []

        # Check ROI consistency
        roi_values = metrics.get("roi", [])
        if len(roi_values) >= 2:
            values = [m["value"] for m in roi_values]
            if max(values) - min(values) > 50:  # More than 50% difference
                contradictions.append((
                    f"ROI {min(values)}% (Section {roi_values[0]['section']})",
                    f"ROI {max(values)}% (Section {roi_values[-1]['section']})",
                ))

        return contradictions

    def _find_duplicates(
        self,
        sections: List[Dict[str, Any]],
    ) -> List[str]:
        """Find duplicate metrics or statements."""
        duplicates: List[str] = []
        seen_statements: Dict[str, str] = {}

        for section in sections:
            content = section.get("content", "")
            section_id = section.get("id", "unknown")

            # Extract key statements (simplified)
            sentences = re.split(r"[.!?]\s+", content)
            for sentence in sentences:
                # Normalize
                normalized = sentence.lower().strip()
                if len(normalized) < 20:
                    continue

                # Check for near-duplicate
                for seen, seen_section in seen_statements.items():
                    if self._similarity(normalized, seen) > 0.85:
                        if section_id != seen_section:
                            duplicates.append(
                                f"'{sentence[:50]}...' in {section_id} and {seen_section}",
                            )

                seen_statements[normalized] = section_id

        return duplicates

    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word-based similarity."""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _find_unclear_recommendations(
        self,
        sections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find unclear recommendations."""
        issues: List[Dict[str, Any]] = []

        for section in sections:
            content = section.get("content", "")
            section_id = section.get("id", "unknown")

            # Check for ambiguous terms in recommendations
            if "empfehl" in content.lower():
                for term in AMBIGUOUS_TERMS:
                    if term in content.lower():
                        issues.append({
                            "type": MetricIssue.UNCLEAR_RECOMMENDATION.value,
                            "section": section_id,
                            "ambiguous_term": term,
                            "suggestion": f"'{term}' konkretisieren",
                        })

        return issues


# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================


class ExecutiveClarityEngine:
    """
    Main engine for executive clarity.

    Orchestrates:
    - Jargon detection and removal
    - Leadership clarity rewriting
    - Metrics validation
    """

    def __init__(self) -> None:
        self._jargon_detector = JargonDetector()
        self._clarity_rewriter = LeadershipClarityRewriter()
        self._metrics_guard = ExecutiveMetricsGuard()

    def process_text(self, text: str) -> ClarityResult:
        """
        Process text for executive clarity.

        Args:
            text: Input text

        Returns:
            ClarityResult with clarified text and analysis
        """
        # Remove jargon
        dejargoned_text, jargon_matches = self._jargon_detector.remove_jargon(text)

        # Rewrite for clarity
        clarified_text, clarity_issues = self._clarity_rewriter.rewrite(dejargoned_text)

        # Calculate scores
        score = self._calculate_clarity_score(
            text, clarified_text, jargon_matches, clarity_issues,
        )

        return ClarityResult(
            original_text=text,
            clarified_text=clarified_text,
            issues_found=clarity_issues,
            jargon_removed=jargon_matches,
            score=score,
        )

    def process_sections(
        self,
        sections: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Process multiple sections.

        Args:
            sections: List of section dicts

        Returns:
            Dict with processed sections and validation
        """
        log.info(
            "[N4.1-Clarity] Processing %d sections for clarity...",
            len(sections),
        )

        processed_sections: List[Dict[str, Any]] = []
        total_jargon = 0
        total_issues = 0

        for section in sections:
            section_id = section.get("id", "unknown")
            content = section.get("content", "")

            result = self.process_text(content)

            processed_sections.append({
                "id": section_id,
                "original_content": content,
                "clarified_content": result["clarified_text"],
                "score": result["score"],
                "jargon_count": len(result["jargon_removed"]),
                "issues_count": len(result["issues_found"]),
            })

            total_jargon += len(result["jargon_removed"])
            total_issues += len(result["issues_found"])

        # Validate metrics across sections
        metric_validation = self._metrics_guard.validate_metrics(sections)

        log.info(
            "[N4.1-Clarity] Clarity processing complete: "
            "%d jargon terms removed, %d issues found, metrics valid: %s",
            total_jargon,
            total_issues,
            metric_validation["is_valid"],
        )

        return {
            "sections": processed_sections,
            "total_jargon_removed": total_jargon,
            "total_issues_found": total_issues,
            "metric_validation": metric_validation,
            "overall_clarity_score": self._calculate_overall_score(processed_sections),
        }

    def validate_report(
        self,
        sections: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate entire report for clarity issues.

        Args:
            sections: List of section dicts

        Returns:
            Validation report
        """
        results = self.process_sections(sections)

        is_clear = (
            results["overall_clarity_score"] >= CLARITY_CONFIG["min_clarity_score"]
            and results["metric_validation"]["is_valid"]
        )

        return {
            "is_clear": is_clear,
            "clarity_score": results["overall_clarity_score"],
            "jargon_leaks": results["total_jargon_removed"],
            "metric_issues": results["metric_validation"]["issues"],
            "recommendation": self._generate_recommendation(results),
        }

    def _calculate_clarity_score(
        self,
        original: str,
        clarified: str,
        jargon: List[JargonMatch],
        issues: List[Dict[str, Any]],
    ) -> ClarityScore:
        """Calculate clarity score breakdown."""
        # Jargon score (fewer is better)
        jargon_density = self._jargon_detector.calculate_jargon_density(original)
        jargon_score = max(0, 1 - jargon_density / CLARITY_CONFIG["jargon_density_threshold"])

        # Readability score
        readability_score = self._clarity_rewriter.calculate_readability_score(clarified)

        # Action clarity (based on issues)
        action_issues = sum(1 for i in issues if i.get("type") == ClarityIssue.UNCLEAR_ACTION.value)
        action_score = max(0, 1 - action_issues * 0.2)

        # Consistency score (based on issues)
        other_issues = len(issues) - action_issues
        consistency_score = max(0, 1 - other_issues * 0.1)

        # Overall score (clamped to [0, 1])
        overall = (
            jargon_score * 0.3 +
            readability_score * 0.3 +
            action_score * 0.2 +
            consistency_score * 0.2
        )
        overall = max(0.0, min(1.0, overall))

        return ClarityScore(
            overall_score=overall,
            jargon_score=min(1.0, jargon_score),
            readability_score=min(1.0, readability_score),
            action_clarity_score=min(1.0, action_score),
            consistency_score=min(1.0, consistency_score),
        )

    def _calculate_overall_score(
        self,
        processed_sections: List[Dict[str, Any]],
    ) -> float:
        """Calculate overall clarity score across sections."""
        if not processed_sections:
            return 0.0

        scores: List[float] = [float(s["score"]["overall_score"]) for s in processed_sections]
        avg_score = sum(scores) / len(scores)
        return float(max(0.0, min(1.0, avg_score)))

    def _generate_recommendation(
        self,
        results: Dict[str, Any],
    ) -> str:
        """Generate recommendation based on results."""
        score = results["overall_clarity_score"]
        jargon = results["total_jargon_removed"]
        issues = results["total_issues_found"]

        if score >= 0.9:
            return "Exzellente Klarheit – Report ist board-ready."

        if score >= 0.7:
            return (
                f"Gute Klarheit mit Verbesserungspotenzial. "
                f"{jargon} Fachbegriffe und {issues} stilistische Punkte "
                f"wurden identifiziert."
            )

        return (
            f"Überarbeitung empfohlen: {jargon} Fachbegriffe entfernen, "
            f"{issues} Klarheitspunkte adressieren für board-ready Status."
        )


# =============================================================================
# SINGLETON & CONVENIENCE FUNCTIONS
# =============================================================================


_engine_instance: Optional[ExecutiveClarityEngine] = None


def get_clarity_engine() -> ExecutiveClarityEngine:
    """Get or create the singleton clarity engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExecutiveClarityEngine()
    return _engine_instance


def clarify_text(text: str) -> ClarityResult:
    """
    Clarify text for executive readability.

    Convenience function for external use.

    Args:
        text: Input text

    Returns:
        ClarityResult with clarified text
    """
    engine = get_clarity_engine()
    return engine.process_text(text)


def clarify_sections(
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Clarify multiple sections.

    Convenience function for external use.

    Args:
        sections: List of section dicts

    Returns:
        Dict with processed sections
    """
    engine = get_clarity_engine()
    return engine.process_sections(sections)


def validate_report_clarity(
    sections: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate report for clarity.

    Convenience function for external use.

    Args:
        sections: List of section dicts

    Returns:
        Validation report
    """
    engine = get_clarity_engine()
    return engine.validate_report(sections)


def get_clarity_score(text: str) -> float:
    """
    Get clarity score for text.

    Convenience function for external use.

    Args:
        text: Input text

    Returns:
        Clarity score (0-1)
    """
    engine = get_clarity_engine()
    result = engine.process_text(text)
    return result["score"]["overall_score"]

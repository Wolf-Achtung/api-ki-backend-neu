# -*- coding: utf-8 -*-
"""
Funding Service - EU/Country-based Funding Module

Provides a unified interface for funding recommendations across different
countries and the EU. Supports DE (full), AT, EU-core, and placeholder
countries for future expansion.

Version: 1.0.0
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

log = logging.getLogger(__name__)

# Base directory for funding data
FUNDING_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "funding"


@dataclass
class FundingProgramme:
    """Represents a single funding programme."""
    id: str
    title: str
    region: str
    region_label: str
    funding_type: str
    funding_rate: str
    max_amount: float
    max_amount_display: str
    focus: str
    suitable_for: List[str]
    notes: str
    relevance_ki: str
    priority: int
    url: str = ""
    country_code: str = ""


@dataclass
class FundingResult:
    """Result of funding recommendation lookup."""
    has_programmes: bool
    country_code: str
    country_name: str
    programmes: List[FundingProgramme]
    programmes_html: str
    potential_html: str
    lang: str = "de"
    debug_info: Dict[str, Any] = field(default_factory=dict)
    is_fallback: bool = False
    fallback_reason: str = ""


class FundingService:
    """
    Central funding service for multi-country/EU funding recommendations.

    Usage:
        service = FundingService()
        result = service.get_funding_recommendations("DE", answers, lang="de")
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the funding service."""
        self.data_dir = data_dir or FUNDING_DATA_DIR
        self.config = self._load_config()
        self._cache: Dict[str, Any] = {}
        log.info("✅ FundingService initialized (data_dir=%s)", self.data_dir)

    def _load_config(self) -> Dict[str, Any]:
        """Load the funding configuration."""
        config_path = self.data_dir / "config.json"
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config: Dict[str, Any] = json.load(f)
                log.debug("✅ Loaded funding config from %s", config_path)
                return config
        except FileNotFoundError:
            log.warning("⚠️ Funding config not found at %s, using defaults", config_path)
            return {
                "default_country": "DE",
                "fallback_country": "EU",
                "supported_countries": {}
            }
        except Exception as e:
            log.error("❌ Error loading funding config: %s", e)
            return {"default_country": "DE", "fallback_country": "EU", "supported_countries": {}}

    def _load_country_programmes(self, country_code: str) -> List[Dict[str, Any]]:
        """Load funding programmes for a specific country."""
        # Check cache first
        cache_key = f"programmes_{country_code}"
        if cache_key in self._cache:
            return cast(List[Dict[str, Any]], self._cache[cache_key])

        country_config = self.config.get("supported_countries", {}).get(country_code, {})
        if not country_config.get("active", False):
            log.debug("⚠️ Country %s is not active", country_code)
            return []

        funding_file = country_config.get("funding_file", f"funding_{country_code.lower()}.json")
        file_path = self.data_dir / funding_file

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                programmes: List[Dict[str, Any]] = data.get("programmes", [])
                self._cache[cache_key] = programmes
                log.debug("✅ Loaded %d programmes for %s", len(programmes), country_code)
                return programmes
        except FileNotFoundError:
            log.warning("⚠️ Funding file not found: %s", file_path)
            return []
        except Exception as e:
            log.error("❌ Error loading funding file %s: %s", file_path, e)
            return []

    def _normalize_size(self, size_value: str) -> str:
        """Normalize company size to standard values (solo/team/kmu)."""
        if not size_value:
            return "team"

        size_lower = size_value.lower().strip()
        size_mapping: Dict[str, List[str]] = self.config.get("size_mapping", {})

        for normalized, variants in size_mapping.items():
            if size_lower in [v.lower() for v in variants]:
                return str(normalized)

        # Fallback logic
        if any(x in size_lower for x in ["solo", "freiberuf", "selbst", "1"]):
            return "solo"
        elif any(x in size_lower for x in ["kmu", "sme", "mittel", "11"]):
            return "kmu"
        else:
            return "team"

    def _get_localized_text(self, obj: Any, lang: str, fallback: str = "") -> str:
        """Extract localized text from an object (dict with de/en keys or string)."""
        if isinstance(obj, dict):
            result = obj.get(lang, obj.get("de", obj.get("en", fallback)))
            return str(result) if result is not None else fallback
        elif isinstance(obj, str):
            return obj
        return fallback

    def _filter_programmes(
        self,
        programmes: List[Dict[str, Any]],
        answers: Dict[str, Any],
        country_code: str,
        lang: str
    ) -> List[FundingProgramme]:
        """Filter and convert programmes based on company profile."""
        size_group = self._normalize_size(answers.get("unternehmensgroesse", ""))
        region = answers.get("bundesland", "").upper()
        branch = str(answers.get("branche", "") or "").strip().lower()

        filtered: List[FundingProgramme] = []

        for prog in programmes:
            # Size filter
            suitable_for = prog.get("suitable_for", [])
            if size_group not in suitable_for:
                continue

            # Optional branch filter (Phase 1 Medien): Programme mit
            # "branchen"-Liste erscheinen nur für passende Branchen.
            # Programme ohne das Feld bleiben für alle sichtbar (fail-open);
            # ebenso, wenn das Briefing keine Branche enthält.
            prog_branchen = prog.get("branchen")
            if prog_branchen and branch and branch not in [
                str(b).lower() for b in prog_branchen
            ]:
                continue

            # Convert to FundingProgramme with localized texts
            fp = FundingProgramme(
                id=prog.get("id", ""),
                title=self._get_localized_text(prog.get("title", ""), lang),
                region=prog.get("region", country_code),
                region_label=self._get_localized_text(prog.get("region_label", ""), lang),
                funding_type=prog.get("funding_type", "grant"),
                funding_rate=prog.get("funding_rate", ""),
                max_amount=prog.get("max_amount", 0),
                max_amount_display=self._get_localized_text(prog.get("max_amount_display", ""), lang),
                focus=self._get_localized_text(prog.get("focus", ""), lang),
                suitable_for=suitable_for,
                notes=self._get_localized_text(prog.get("notes", ""), lang),
                relevance_ki=prog.get("relevance_ki", "medium"),
                priority=prog.get("priority", 99),
                url=prog.get("url", ""),
                country_code=country_code
            )
            filtered.append(fp)

        # Sort by priority (lower = higher priority)
        filtered.sort(key=lambda x: x.priority)

        # Regional boost for DE
        if country_code == "DE" and region:
            for fp in filtered:
                if fp.region == region:
                    fp.priority = 0  # Boost regional programmes
            filtered.sort(key=lambda x: x.priority)

        return filtered

    def _build_programmes_html(
        self,
        programmes: List[FundingProgramme],
        lang: str,
        country_code: str,
        max_programmes: int = 8
    ) -> str:
        """Build HTML table for funding programmes."""
        if not programmes:
            if lang == "en":
                return "<p class='muted small'>No specific funding programs available for your profile at this time.</p>"
            return "<p class='muted small'>Keine spezifischen Förderprogramme für Ihr Profil verfügbar.</p>"

        # Limit to top programmes
        top_programmes = programmes[:max_programmes]

        # Headers based on language
        if lang == "en":
            headers = {
                "programme": "Programme",
                "region": "Region",
                "rate": "Funding Rate",
                "max": "Max. Amount",
                "relevance": "AI Relevance"
            }
            relevance_labels = {"high": "High", "medium": "Medium", "low": "Low"}
            note_prefix = "Note"
        else:
            headers = {
                "programme": "Programm",
                "region": "Region",
                "rate": "Förderquote",
                "max": "Max. Volumen",
                "relevance": "KI-Relevanz"
            }
            relevance_labels = {"high": "Sehr hoch", "medium": "Mittel", "low": "Gering"}
            note_prefix = "Hinweis"

        html_parts = []
        html_parts.append('<div class="funding-matrix">')
        html_parts.append('  <table class="funding-table table-modern">')
        html_parts.append('    <thead>')
        html_parts.append('      <tr>')
        html_parts.append(f'        <th>{headers["programme"]}</th>')
        html_parts.append(f'        <th>{headers["region"]}</th>')
        html_parts.append(f'        <th>{headers["rate"]}</th>')
        html_parts.append(f'        <th>{headers["max"]}</th>')
        html_parts.append(f'        <th>{headers["relevance"]}</th>')
        html_parts.append('      </tr>')
        html_parts.append('    </thead>')
        html_parts.append('    <tbody>')

        for prog in top_programmes:
            relevance_class = prog.relevance_ki.lower()
            relevance_label = relevance_labels.get(relevance_class, prog.relevance_ki)

            html_parts.append('      <tr>')
            html_parts.append(f'        <td><strong>{prog.title}</strong><br>')
            html_parts.append(f'          <span class="small muted">{prog.focus}</span>')
            html_parts.append('        </td>')
            html_parts.append(f'        <td>{prog.region_label}</td>')
            html_parts.append(f'        <td>{prog.funding_rate}</td>')
            html_parts.append(f'        <td>{prog.max_amount_display}</td>')
            html_parts.append(f'        <td><span class="relevance-badge relevance-{relevance_class}">{relevance_label}</span></td>')
            html_parts.append('      </tr>')

        html_parts.append('    </tbody>')
        html_parts.append('  </table>')

        # Add note about country/region
        if lang == "en":
            if country_code == "EU":
                note_text = f"These EU-wide programs are available to SMEs across the European Union. Country-specific programs may also be available."
            else:
                country_name = self.config.get("supported_countries", {}).get(country_code, {}).get("name_en", country_code)
                note_text = f"These programs are specifically selected for your company profile in {country_name}. Additional regional programs may be available."
        else:
            if country_code == "EU":
                note_text = f"Diese EU-weiten Programme stehen KMU in der gesamten Europäischen Union zur Verfügung. Länderspezifische Programme können zusätzlich verfügbar sein."
            else:
                country_name = self.config.get("supported_countries", {}).get(country_code, {}).get("name_de", country_code)
                note_text = f"Diese Programme sind speziell für Ihr Unternehmensprofil in {country_name} vorausgewählt. Weitere regionale Programme können verfügbar sein."

        html_parts.append(f'  <p class="small muted" style="margin-top: 6pt;">')
        from services.extra_sections import _current_quarter_label
        html_parts.append(f'    <strong>{note_prefix}:</strong> {note_text} Stand: {_current_quarter_label()}.')
        html_parts.append('  </p>')
        html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _build_potential_html(
        self,
        programmes: List[FundingProgramme],
        answers: Dict[str, Any],
        lang: str,
        country_code: str,
        is_fallback: bool = False
    ) -> str:
        """Build funding potential assessment HTML."""
        if not programmes:
            if lang == "en":
                return "<p>No funding programs currently match your profile. Consider reaching out to local business support organizations for guidance.</p>"
            return "<p>Derzeit entsprechen keine Förderprogramme Ihrem Profil. Wenden Sie sich an lokale Wirtschaftsförderungen für weitere Beratung.</p>"

        # Get business case values if available
        capex = answers.get("CAPEX_REALISTISCH_EUR", 0)

        # Count high-relevance programmes
        high_relevance_count = sum(1 for p in programmes if p.relevance_ki == "high")

        if lang == "en":
            if is_fallback:
                intro = f"""
<p>While country-specific programs for your location are still being added,
several EU-wide funding opportunities may be relevant for your AI project.
These programs are accessible to SMEs across Europe.</p>
"""
            else:
                country_name = self.config.get("supported_countries", {}).get(country_code, {}).get("name_en", country_code)
                intro = f"""
<p>Based on your company profile, there are <strong>{len(programmes)} funding programs</strong>
in {country_name} that may be suitable for your AI initiative.
Of these, <strong>{high_relevance_count} programs</strong> have high AI relevance.</p>
"""

            benefits = """
<h4>How Funding Can Improve Your Business Case</h4>
<ul>
  <li><strong>Reduced initial investment:</strong> Grants typically cover 30-50% of eligible costs</li>
  <li><strong>Faster payback:</strong> Lower upfront costs mean quicker return on investment</li>
  <li><strong>Lower risk:</strong> External funding reduces financial exposure</li>
  <li><strong>Additional resources:</strong> Savings can fund training or enhanced solutions</li>
</ul>
"""

            next_steps = """
<h4>Next Steps for Funding</h4>
<ol>
  <li>Review the programs above and identify 1-2 that match your project</li>
  <li>Check eligibility requirements and application deadlines</li>
  <li>Prepare a project description with goals, timeline, and budget</li>
  <li>Consider consulting a funding advisor for complex applications</li>
</ol>
"""
        else:
            country_name = self.config.get("supported_countries", {}).get(country_code, {}).get("name_de", country_code)
            intro = f"""
<p>Basierend auf Ihrem Unternehmensprofil stehen <strong>{len(programmes)} Förderprogramme</strong>
in {country_name} zur Verfügung, die für Ihr KI-Vorhaben relevant sein könnten.
Davon haben <strong>{high_relevance_count} Programme</strong> eine hohe KI-Relevanz.</p>
"""

            benefits = """
<h4>Wie Fördermittel Ihren Business Case verbessern können</h4>
<ul>
  <li><strong>Reduzierte Anfangsinvestition:</strong> Zuschüsse decken typischerweise 30-50% der förderfähigen Kosten</li>
  <li><strong>Schnellere Amortisation:</strong> Geringere Anfangskosten bedeuten schnelleren ROI</li>
  <li><strong>Geringeres Risiko:</strong> Externe Förderung reduziert die finanzielle Belastung</li>
  <li><strong>Zusätzliche Ressourcen:</strong> Einsparungen können für Schulungen oder erweiterte Lösungen genutzt werden</li>
</ul>
"""

            next_steps = """
<h4>Nächste Schritte für die Förderprüfung</h4>
<ol>
  <li>Programme oben prüfen und 1-2 passende identifizieren</li>
  <li>Fördervoraussetzungen und Antragsfristen prüfen</li>
  <li>Projektbeschreibung mit Zielen, Zeitplan und Budget erstellen</li>
  <li>Bei komplexen Anträgen ggf. Förderberatung hinzuziehen</li>
</ol>
"""

        return f"""
<section class="section funding-potential">
{intro}
{benefits}
{next_steps}
</section>
""".strip()

    def derive_country_from_answers(self, answers: Dict[str, Any], lang: str) -> str:
        """
        Determine the country code from answers and language.

        Priority:
        1. Explicit country field
        2. Bundesland → DE
        3. Lang-based fallback (de → DE, en → EU)
        """
        # Check explicit country field
        country_raw = answers.get("country", "")
        country = str(country_raw).upper() if country_raw else ""
        if country and country in self.config.get("supported_countries", {}):
            return country

        # Check for German Bundesland → implies DE
        bundesland = answers.get("bundesland", "")
        if bundesland:
            return "DE"

        # Language-based fallback
        if lang == "de":
            default_country = self.config.get("default_country", "DE")
            return str(default_country) if default_country else "DE"
        else:
            # For non-German reports, use EU as fallback
            fallback_country = self.config.get("fallback_country", "EU")
            return str(fallback_country) if fallback_country else "EU"

    def get_funding_recommendations(
        self,
        country_code: str,
        answers: Dict[str, Any],
        lang: str = "de"
    ) -> FundingResult:
        """
        Get funding recommendations for a country/profile.

        Args:
            country_code: ISO country code (DE, AT, EU, etc.)
            answers: Briefing answers including unternehmensgroesse, bundesland, etc.
            lang: Language for output (de/en)

        Returns:
            FundingResult with programmes and HTML content
        """
        log.info("🔍 Getting funding recommendations for country=%s, lang=%s", country_code, lang)

        # Normalize country code
        country_code = country_code.upper() if country_code else "EU"

        # Check if country is supported
        country_config = self.config.get("supported_countries", {}).get(country_code, {})
        is_fallback = False
        fallback_reason = ""

        if not country_config.get("active", False):
            # Fall back to EU
            original_country = country_code
            country_code = self.config.get("fallback_country", "EU")
            country_config = self.config.get("supported_countries", {}).get(country_code, {})
            is_fallback = True
            fallback_reason = f"Country {original_country} not yet supported, using EU programs"
            log.info("⚠️ %s", fallback_reason)

        # Load programmes
        programmes_raw = self._load_country_programmes(country_code)

        # For DE, also include EU programmes
        if country_code == "DE" and not is_fallback:
            eu_programmes = self._load_country_programmes("EU")
            programmes_raw.extend(eu_programmes)

        # Filter by profile
        programmes = self._filter_programmes(programmes_raw, answers, country_code, lang)

        # Get country name
        country_name = self._get_localized_text(
            country_config.get(f"name_{lang}", country_config.get("name_en", country_code)),
            lang,
            country_code
        )

        # Build HTML outputs
        programmes_html = self._build_programmes_html(programmes, lang, country_code)
        potential_html = self._build_potential_html(programmes, answers, lang, country_code, is_fallback)

        result = FundingResult(
            has_programmes=len(programmes) > 0,
            country_code=country_code,
            country_name=country_name,
            programmes=programmes,
            programmes_html=programmes_html,
            potential_html=potential_html,
            lang=lang,
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            debug_info={
                "raw_programme_count": len(programmes_raw),
                "filtered_programme_count": len(programmes),
                "size_group": self._normalize_size(answers.get("unternehmensgroesse", "")),
            }
        )

        log.info(
            "✅ Funding result: country=%s, programmes=%d, has_programmes=%s",
            country_code, len(programmes), result.has_programmes
        )

        return result


# Module-level convenience function
_service_instance: Optional[FundingService] = None


def get_funding_service() -> FundingService:
    """Get or create the funding service singleton."""
    global _service_instance
    if _service_instance is None:
        _service_instance = FundingService()
    return _service_instance


def get_funding_recommendations(
    country_code: str,
    answers: Dict[str, Any],
    lang: str = "de"
) -> FundingResult:
    """
    Convenience function to get funding recommendations.

    This is the main API for the funding module.

    Args:
        country_code: ISO country code (DE, AT, EU, etc.)
        answers: Briefing answers
        lang: Language for output

    Returns:
        FundingResult with all funding data
    """
    service = get_funding_service()
    return service.get_funding_recommendations(country_code, answers, lang)


def derive_country_from_answers(answers: Dict[str, Any], lang: str) -> str:
    """
    Convenience function to derive country from answers.

    Args:
        answers: Briefing answers
        lang: Language of the report

    Returns:
        Country code (DE, AT, EU, etc.)
    """
    service = get_funding_service()
    return service.derive_country_from_answers(answers, lang)


# Test harness
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Test DE profile
    print("=" * 60)
    print("TEST: DE Solo Profile (Berlin)")
    print("=" * 60)

    de_answers = {
        "unternehmensgroesse": "solo",
        "bundesland": "BE",
        "branche": "beratung",
    }

    result = get_funding_recommendations("DE", de_answers, lang="de")
    print(f"Country: {result.country_name}")
    print(f"Programmes: {len(result.programmes)}")
    print(f"Has programmes: {result.has_programmes}")
    print()

    # Test EN profile (EU fallback)
    print("=" * 60)
    print("TEST: EN Profile (France → EU fallback)")
    print("=" * 60)

    en_answers = {
        "unternehmensgroesse": "kmu",
        "country": "FR",
    }

    result = get_funding_recommendations("FR", en_answers, lang="en")
    print(f"Country: {result.country_name}")
    print(f"Is fallback: {result.is_fallback}")
    print(f"Fallback reason: {result.fallback_reason}")
    print(f"Programmes: {len(result.programmes)}")

# services/anthropic_client.py

from __future__ import annotations

import logging
import json
import os
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # Wir loggen das später sauber weg

log = logging.getLogger(__name__)

# Import PLATIN_STOP_SEQUENCES for Anthropic-specific stop sequence handling
# OpenAI no longer supports stop parameter for new models, but Anthropic still does
_PLATIN_STOP_SEQUENCES: List[str] = []
_get_platin_config: Callable[[str], Any] = lambda x: None

try:
    from services.prompt_enhancer import PLATIN_STOP_SEQUENCES as _imported_seqs
    from services.prompt_enhancer import get_platin_config as _imported_config
    _PLATIN_STOP_SEQUENCES = _imported_seqs
    _get_platin_config = _imported_config
except ImportError:  # pragma: no cover
    pass  # Use defaults defined above

# --- ENV Defaults ----------------------------------------------------------

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929").strip()  # K1: updated, FIX-STRIP
DEFAULT_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "5000"))  # J11: raised from 3000
DEFAULT_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2"))

# Effort routing — applied as output_config={"effort": ...} on the messages.create call.
# Supported models: Opus 4.6, Opus 4.7, Sonnet 4.6. Haiku 4.5 left untouched per audit.
ANTHROPIC_EFFORT_DEFAULT = "high"
_EFFORT_MODEL_MARKERS = ("opus-4-6", "opus-4-7", "sonnet-4-6")

# KIS-1230-HOTFIX: Modelle, die `temperature` mit 400 ablehnen
# ("temperature is deprecated for this model"), aber NICHT über die
# Effort-Marker laufen. Die Claude-5-Familie (claude-sonnet-5, ...) gehört
# dazu — der KIS-1230-Lauf verlor dadurch ALLE Sonnet-Sektionen an die
# Fallback-Kette (Decision-Boxen wurden Boilerplate). Für diese Modelle wird
# temperature weggelassen; effort senden wir bewusst nicht (Support unklar).
_NO_TEMPERATURE_MODEL_MARKERS = _EFFORT_MODEL_MARKERS + (
    "sonnet-5", "opus-5", "haiku-5", "fable-5", "mythos-5",
    # KIS-1231: opus-4-8 lehnt temperature ebenfalls ab (KMU-Lauf 1114:
    # jede Opus-Sektion lief über den reaktiven 400-Retry — ein verlorener
    # API-Roundtrip pro Sektion). Proaktiv weglassen.
    "opus-4-8",
)


def get_anthropic_effort() -> str:
    """Read ANTHROPIC_EFFORT from env (low|medium|high|xhigh|max), default 'high'."""
    return (os.getenv("ANTHROPIC_EFFORT", ANTHROPIC_EFFORT_DEFAULT).strip().lower()
            or ANTHROPIC_EFFORT_DEFAULT)


def _model_supports_effort(model: str) -> bool:
    m = (model or "").lower()
    return any(marker in m for marker in _EFFORT_MODEL_MARKERS)


def _model_rejects_temperature(model: str) -> bool:
    m = (model or "").lower()
    return any(marker in m for marker in _NO_TEMPERATURE_MODEL_MARKERS)


def build_anthropic_create_kwargs(
    *,
    model: str,
    max_tokens: int,
    temperature: float,
    system: str,
    messages: List[Any],
    stop_sequences: Optional[List[str]] = None,
) -> dict:
    """Assemble kwargs for client.messages.create(), including conditional
    output_config={"effort": ...} for models that support it.

    Effort-capable models (Opus 4.6/4.7, Sonnet 4.6) reject ``temperature``
    with 400 ("temperature is deprecated for this model") — for those we
    omit the parameter and let the provider use its default.
    """
    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if stop_sequences:
        kwargs["stop_sequences"] = stop_sequences
    if _model_supports_effort(model):
        kwargs["output_config"] = {"effort": get_anthropic_effort()}
    elif not _model_rejects_temperature(model):
        kwargs["temperature"] = temperature
    # KIS-1230-HOTFIX: Claude-5-Familie bekommt weder temperature (400)
    # noch output_config (Support unklar) — Provider-Defaults.
    return kwargs


# --- KIS-1231: Truncation-Retry ---------------------------------------------
# Der KMU-Lauf 1114 zeigte: claude-sonnet-5 schreibt deutlich länger als die
# per ENV kalibrierten Budgets (OPENAI_MAX_TOKENS_*). 7+ Sektionen endeten mit
# stop_reason=max_tokens; quick_wins lieferte dadurch abgeschnittenes JSON und
# FIX-499-QW brach im STRICT-Modus den GESAMTEN Report ab. Statt jedes Budget
# einzeln nachzuziehen: bei max_tokens einmal mit erhöhtem Budget neu
# generieren. Kostet für die betroffene Sektion einen zweiten Call — die
# Alternative (PLATIN-Fallback + 2-Pass-Expand) kostet mehr und liefert
# schlechteren Text.

def _truncation_retry_enabled() -> bool:
    return os.getenv("ANTHROPIC_TRUNCATION_RETRY", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def _truncation_retry_max_tokens(current: int) -> int:
    """Erhöhtes Budget für den Retry: current × Faktor (Default 2.0),
    gedeckelt (Default 16000). Liefert current zurück, wenn keine Erhöhung
    möglich ist (dann lohnt kein Retry)."""
    try:
        factor = float(os.getenv("ANTHROPIC_TRUNCATION_RETRY_FACTOR", "2.0"))
    except ValueError:
        factor = 2.0
    try:
        cap = int(os.getenv("ANTHROPIC_TRUNCATION_RETRY_CAP", "16000"))
    except ValueError:
        cap = 16000
    return max(current, min(cap, int(current * factor)))


def _extract_message_text(message: Any) -> str:
    """Sammelt alle Text-Blöcke einer Anthropic-Message ein."""
    parts = []
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", "") or "")
    return "".join(parts).strip()


# --- Prompt-Caching-Diagnose (reines Logging) --------------------------------
# Nach JEDEM Anthropic-Call wird response.usage protokolliert. Auswertung:
#   cache_read_input_tokens > 0        → Cache greift
#   cache_creation_input_tokens > 0    → dieser Call hat den Cache geschrieben
#   beide durchgängig 0                → Prefix unter dem Modell-Minimum ODER
#                                        kein cache_control gesetzt ODER der
#                                        Prefix ändert sich zwischen den Calls
# Diese Funktion darf niemals werfen — sie hängt in Erfolgs- wie Retry-Pfaden.

# --- KIS-1270: cache-korrekte Kostenschaetzung + DB-Persistenz --------------
# Basispreise USD pro 1M Token (input, output) — Annahme Stand 2026-08,
# ueberschreibbar per ANTHROPIC_PRICES_JSON='{"opus": [5, 25], ...}'.
# Multiplikatoren auf den Input-Basispreis: regulaer 1,00x / 5m-Cache-Write
# 1,25x / Cache-Read 0,10x. Bewusst IMMER mit allen drei Input-Feldern
# gerechnet (creative-radar-Lektion: input_tokens allein untertreibt, sobald
# Caching greift, weil das Feld nur die Token NACH dem Breakpoint enthaelt).
_DEFAULT_PRICES: Dict[str, Any] = {"opus": (5.0, 25.0), "sonnet": (3.0, 15.0), "haiku": (1.0, 5.0)}


def _price_for_model(model: str) -> "tuple[float, float]":
    prices: Dict[str, Any] = dict(_DEFAULT_PRICES)
    try:
        _override = os.getenv("ANTHROPIC_PRICES_JSON", "")
        if _override:
            for k, v in json.loads(_override).items():
                prices[str(k).lower()] = (float(v[0]), float(v[1]))
    except Exception:
        pass
    m = (model or "").lower()
    for key, pair in prices.items():
        if key in m:
            return (float(pair[0]), float(pair[1]))
    _s = prices["sonnet"]
    return (float(_s[0]), float(_s[1]))


def estimate_anthropic_cost_usd(model: str, input_tokens: int,
                                cache_creation: int, cache_read: int,
                                output_tokens: int) -> float:
    """total_input = input + 1,25*write + 0,10*read (jeweils x Basispreis)."""
    base_in, base_out = _price_for_model(model)
    input_cost = (input_tokens * 1.0 + cache_creation * 1.25 + cache_read * 0.10) * base_in / 1_000_000
    output_cost = output_tokens * base_out / 1_000_000
    return float(round(input_cost + output_cost, 6))


def _persist_anthropic_usage(call_site: str, model: str, input_tokens: int,
                             cache_creation: int, cache_read: int,
                             output_tokens: int) -> None:
    """Fail-open: Persistenz darf nie einen LLM-Call brechen (laeuft in
    Worker-Threads; eigene Session pro Aufruf)."""
    if os.getenv("ANTHROPIC_USAGE_DB", "1").strip().lower() in ("0", "false", "no", "off"):
        return
    try:
        from core.db import SessionLocal
        from models import AnthropicUsage
        db = SessionLocal()
        try:
            db.add(AnthropicUsage(
                call_site=call_site[:120], model=(model or "?")[:80],
                input_tokens=input_tokens,
                cache_creation_input_tokens=cache_creation,
                cache_read_input_tokens=cache_read,
                output_tokens=output_tokens,
                cost_usd=estimate_anthropic_cost_usd(
                    model, input_tokens, cache_creation, cache_read, output_tokens),
            ))
            db.commit()
        finally:
            db.close()
    except Exception as _p_exc:  # pragma: no cover — nie den Call gefaehrden
        log.debug("[CACHE-USAGE] DB-Persistenz uebersprungen (%s): %s", call_site, _p_exc)


def log_anthropic_usage(message: Any, *, call_site: str, model: str = "") -> None:
    """Protokolliert die Cache-/Token-Felder aus ``message.usage``."""
    try:
        usage = getattr(message, "usage", None)

        def _u(name: str) -> int:
            if usage is None:
                return 0
            value = getattr(usage, name, None)
            if value is None and isinstance(usage, dict):
                value = usage.get(name)
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                return 0

        _input = _u("input_tokens")
        _created = _u("cache_creation_input_tokens")
        _read = _u("cache_read_input_tokens")
        log.info(
            "[CACHE-USAGE] call_site=%s model=%s input_tokens=%d "
            "cache_creation_input_tokens=%d cache_read_input_tokens=%d "
            "prompt_tokens_total=%d output_tokens=%d",
            call_site, model or "?", _input, _created, _read,
            _input + _created + _read, _u("output_tokens"),
        )
        _persist_anthropic_usage(call_site, model, _input, _created, _read,
                                 _u("output_tokens"))
    except Exception as _usage_exc:  # pragma: no cover — Logging darf nie brechen
        log.debug("[CACHE-USAGE] Logging fehlgeschlagen (%s): %s", call_site, _usage_exc)


# --- RUN-622 P2: Opus Routing ------------------------------------------------
OPUS_MODEL = os.getenv("ANTHROPIC_MODEL_OPUS", "claude-opus-4-6").strip()  # FIX-629 + FIX-STRIP
_OPUS_SECTIONS_RAW = os.getenv("OPUS_SECTIONS", "")
OPUS_SECTIONS_SET: set = {
    s.strip().lower()
    for s in _OPUS_SECTIONS_RAW.split(",")
    if s.strip()
}
if OPUS_SECTIONS_SET:
    log.info(
        "🏆 [FIX-OPUS-ROUTING] Opus routing ACTIVE for %d sections: %s | model=%s",
        len(OPUS_SECTIONS_SET), sorted(OPUS_SECTIONS_SET), OPUS_MODEL,
    )
else:
    log.info("ℹ️ [FIX-OPUS-ROUTING] Opus routing disabled (OPUS_SECTIONS not set)")

# z.B. USE_ANTHROPIC_FOR_EXEC_SUMMARY, USE_ANTHROPIC_FOR_RISKS, ...
SECTION_FLAG_PREFIX = "USE_ANTHROPIC_FOR_"


# --- Hilfsfunktionen -------------------------------------------------------


def _normalize_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    value = value.strip().lower()
    return value in ("1", "true", "yes", "on")


_SECTION_ENV_ALIASES = {
    # FIX-629: KRITISCHER BUG BEHOBEN - executive_summary → EXEC_SUMMARY war FALSCH!
    # Wolf setzt ANTHROPIC_MODEL_EXECUTIVE_SUMMARY in Railway.
    # Alter Code suchte ANTHROPIC_MODEL_EXEC_SUMMARY → nie gefunden → Sonnet Fallback.
    # Alle Einträge müssen dem Railway-Variablennamen entsprechen (UPPERCASE nach _).
    "executive_summary":        "EXECUTIVE_SUMMARY",
    "gamechanger":              "GAMECHANGER",
    "recommendations":          "RECOMMENDATIONS",
    "risks":                    "RISKS",
    "business_case":            "BUSINESS_CASE",
    "foerderpotenzial":         "FOERDERPOTENZIAL",
    "strategie_governance":     "STRATEGIE_GOVERNANCE",
    "technologie_prozesse":     "TECHNOLOGIE_PROZESSE",
    "quick_wins":               "QUICK_WINS",
    "roadmap_12m":              "ROADMAP_12M",
    "org_change":               "ORG_CHANGE",
    "unternehmensprofil_markt": "UNTERNEHMENSPROFIL_MARKT",
}


def section_to_env_suffix(section: Optional[str]) -> Optional[str]:
    if not section:
        return None
    section = section.strip()
    if not section:
        return None

    if section in _SECTION_ENV_ALIASES:
        return _SECTION_ENV_ALIASES[section]

    # Standard: snake-case -> UPPER mit Unterstrichen
    return section.upper().replace("-", "_")


def _is_openai_model(model_name: str) -> bool:
    """
    Prüft, ob ein Modellname nach einem OpenAI-Modell aussieht.
    """
    if not model_name:
        return False
    model_lower = model_name.lower()
    return (
        model_lower.startswith("gpt-")
        or model_lower.startswith("o1-")
        or model_lower.startswith("o3-")
        or "gpt-4" in model_lower
        or "gpt-3" in model_lower
    )


def _is_claude_model(model_name: str) -> bool:
    """
    Prüft, ob ein Modellname nach einem Claude-Modell aussieht.
    """
    if not model_name:
        return False
    model_lower = model_name.lower()
    return model_lower.startswith("claude-")


def _resolve_anthropic_model(section: Optional[str], requested_model: Optional[str]) -> str:
    """
    Ermittelt das tatsächlich zu verwendende Anthropic-Modell für einen Abschnitt.

    Mappt OpenAI-Modellnamen automatisch auf Claude-Modelle, um Fehler zu vermeiden.

    FIX-OPUS-ROUTING: Neue Priorität (2026-02-19):
    0. OPUS_SECTIONS → HÖCHSTE Priorität, überschreibt ALLES
    1. Sektion-spezifischer ENV-Override: ANTHROPIC_MODEL_<SECTION>
    2. Globale ENV: ANTHROPIC_MODEL_DEFAULT → ANTHROPIC_MODEL
    3. Falls requested_model ein Claude-Modell ist, verwende es
    4. Fallback: DEFAULT_MODEL

    Args:
        section: Der Abschnitts-Identifier (z.B. "executive_summary")
        requested_model: Das ursprünglich angeforderte Modell (kann OpenAI-Modell sein)

    Returns:
        Ein valider Claude-Modellname
    """
    section_lower = (section or "").strip().lower()

    # =========================================================================
    # FIX-OPUS-ROUTING: Step 0 — OPUS hat IMMER Vorrang
    # Wenn eine Section in OPUS_SECTIONS steht, bekommt sie Opus.
    # Kein ENV-Override kann das überschreiben.
    # =========================================================================
    if section_lower and section_lower in OPUS_SECTIONS_SET:
        log.info(
            "🏆 [FIX-OPUS-ROUTING] OPUS section '%s' → model='%s' "
            "(OPUS_SECTIONS=%d, overrides ALL ENV)",
            section, OPUS_MODEL, len(OPUS_SECTIONS_SET),
        )
        return OPUS_MODEL

    # 1. Sektion-spezifischer Override (nur für Non-Opus-Sections)
    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        env_name = f"ANTHROPIC_MODEL_{suffix}"
        section_model = os.getenv(env_name)
        if section_model:
            section_model = section_model.strip()  # FIX-STRIP
            log.info(
                "🎯 [RESOLVE] section='%s' → model='%s' (source='%s')",
                section, section_model, env_name,
            )
            return section_model

    # 2. Globale ENV-Variablen
    global_model = (
        os.getenv("ANTHROPIC_MODEL_DEFAULT") or os.getenv("ANTHROPIC_MODEL") or ""
    ).strip()
    if global_model:
        log.info(
            "🎯 [RESOLVE] section='%s' → model='%s' (source='ENV_GLOBAL')",
            section, global_model,
        )
        return global_model

    # 3. Requested model prüfen
    if requested_model:
        if _is_openai_model(requested_model):
            fallback = DEFAULT_MODEL
            log.info(
                "🔄 [RESOLVE] section='%s' → OpenAI model '%s' mapped to '%s'",
                section, requested_model, fallback,
            )
            return fallback
        elif _is_claude_model(requested_model):
            log.info(
                "✅ [RESOLVE] section='%s' → model='%s' (source='requested')",
                section, requested_model,
            )
            return requested_model

    # 4. Harter Fallback
    log.info(
        "🔄 [RESOLVE] section='%s' → model='%s' (source='FALLBACK')",
        section, DEFAULT_MODEL,
    )
    return DEFAULT_MODEL


# v7.1.6: Premium sections that should be verified in logs
_PREMIUM_SECTIONS = {"advisor_note", "business_case", "executive_summary", "one_liner"}


def log_premium_routing(section: str, resolved_model: str) -> None:
    """Log routing for premium sections to verify Opus assignment."""
    if (section or "").strip().lower() in _PREMIUM_SECTIONS:
        is_opus = "opus" in resolved_model.lower()
        log.info(
            "[FIX-OPUS-ROUTING] Premium section '%s' → model='%s' (is_opus=%s, "
            "in_OPUS_SECTIONS=%s)",
            section, resolved_model, is_opus,
            (section or "").strip().lower() in OPUS_SECTIONS_SET,
        )


@lru_cache(maxsize=1)
def get_anthropic_client() -> Optional["anthropic.Anthropic"]:
    """
    Liefert eine gecachte Anthropic-Client-Instanz oder None, wenn
    kein API-Key oder kein anthropic-Paket vorhanden ist.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("⚠️ ANTHROPIC_API_KEY not set – Anthropic-Client deaktiviert.")
        return None

    if anthropic is None:
        log.error(
            "❌ anthropic-Paket nicht installiert. "
            "Bitte `pip install anthropic` im Backend-Environment ausführen."
        )
        return None

    _timeout = float(os.getenv("ANTHROPIC_TIMEOUT", "180"))  # seconds
    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=_timeout,
    )
    log.info("✅ Anthropic-Client initialisiert (timeout=%ss).", _timeout)
    return client


def _get_model_for_section(section: Optional[str]) -> str:
    """
    Ermittelt das Anthropic-Modell für einen Abschnitt:
    0. OPUS_SECTIONS → Opus (FIX-OPUS-ROUTING)
    1. ANTHROPIC_MODEL_<SECTION>
    2. ANTHROPIC_MODEL
    3. DEFAULT_MODEL
    """
    # FIX-OPUS-ROUTING: Opus-Check auch hier
    section_lower = (section or "").strip().lower()
    if section_lower and section_lower in OPUS_SECTIONS_SET:
        return OPUS_MODEL

    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        env_name = f"ANTHROPIC_MODEL_{suffix}"
        section_model = os.getenv(env_name)
        if section_model:
            return section_model.strip()  # FIX-STRIP

    return os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL).strip()  # FIX-STRIP


def _get_temperature_for_section(section: Optional[str]) -> float:
    """
    Optional: Temperatur pro Abschnitt überschreibbar:
    ANTHROPIC_TEMP_<SECTION>, sonst ANTHROPIC_TEMPERATURE oder Default.
    """
    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        env_name = f"ANTHROPIC_TEMP_{suffix}"
        section_temp = os.getenv(env_name)
        if section_temp:
            try:
                return float(section_temp)
            except ValueError:
                log.warning(
                    "⚠️ Ungültige Temperatur in %s=%r – verwende Default.",
                    env_name,
                    section_temp,
                )

    global_temp = os.getenv("ANTHROPIC_TEMPERATURE")
    if global_temp:
        try:
            return float(global_temp)
        except ValueError:
            log.warning(
                "⚠️ Ungültige ANTHROPIC_TEMPERATURE=%r – verwende Default.",
                global_temp,
            )

    return DEFAULT_TEMPERATURE


def _get_max_tokens_for_section(section: Optional[str]) -> int:
    """
    Optional: Max Tokens pro Abschnitt:
    ANTHROPIC_MAX_TOKENS_<SECTION>, sonst ANTHROPIC_MAX_TOKENS oder Default.
    """
    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        env_name = f"ANTHROPIC_MAX_TOKENS_{suffix}"
        section_max = os.getenv(env_name)
        if section_max:
            try:
                return int(section_max)
            except ValueError:
                log.warning(
                    "⚠️ Ungültige MaxTokens in %s=%r – verwende Default.",
                    env_name,
                    section_max,
                )

    global_max = os.getenv("ANTHROPIC_MAX_TOKENS")
    if global_max:
        try:
            return int(global_max)
        except ValueError:
            log.warning(
                "⚠️ Ungültige ANTHROPIC_MAX_TOKENS=%r – verwende Default.",
                global_max,
            )

    return DEFAULT_MAX_TOKENS


def should_use_anthropic(section: Optional[str] = None) -> bool:
    """
    Entscheidet, ob für einen Abschnitt Anthropic genutzt werden soll.

    Reihenfolge:
    1. Wenn kein API-Key oder kein Client -> False
    2. ANTHROPIC_SECTIONS Whitelist (wenn gesetzt)
    3. Section-Flag: USE_ANTHROPIC_FOR_<SECTION> (wenn gesetzt)
    4. LLM_PROVIDER_DEFAULT == 'anthropic' -> True
    5. sonst False
    """
    client = get_anthropic_client()
    if client is None:
        return False

    # FIX-625-1: If section is in OPUS_SECTIONS, always route to Anthropic
    # (OPUS_SECTIONS defines premium sections that MUST use Claude Opus)
    if section:
        section_lower = section.strip().lower()
        if section_lower in OPUS_SECTIONS_SET:
            log.info(
                "🎯 [FIX-625] Opus section '%s' → forcing Anthropic path",
                section,
            )
            return True

    # Optionale Whitelist
    whitelist_env = os.getenv("ANTHROPIC_SECTIONS")
    if whitelist_env:
        allowed_sections = [s.strip().lower() for s in whitelist_env.split(",") if s.strip()]
        if allowed_sections:
            section_normalized = section.strip().lower() if section else ""
            if section_normalized not in allowed_sections:
                log.debug(
                    "🚫 Abschnitt '%s' nicht in ANTHROPIC_SECTIONS Whitelist – nutze Anthropic NICHT",
                    section
                )
                return False

    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        flag_name = f"{SECTION_FLAG_PREFIX}{suffix}"
        flag_val = os.getenv(flag_name)
        if flag_val is not None:
            # expliziter Override
            use_it = _normalize_bool(flag_val)
            log.debug(
                "🎯 Anthropic-Routing für Abschnitt %s (%s=%r) -> %s",
                section,
                flag_name,
                flag_val,
                use_it,
            )
            return use_it

    # globaler Default
    default_provider = os.getenv("LLM_PROVIDER_DEFAULT", "openai").strip().lower()
    if default_provider == "anthropic":
        log.info(
            "✅ [FIX-OPUS-ROUTING] LLM_PROVIDER_DEFAULT=anthropic → Anthropic für section='%s'",
            section,
        )
        return True

    log.info(
        "ℹ️ [FIX-OPUS-ROUTING] section='%s' → NOT using Anthropic "
        "(LLM_PROVIDER_DEFAULT='%s')",
        section, default_provider,
    )
    return False


# --- Öffentliche LLM-Funktion ----------------------------------------------


# --- KIS-1234-P2: Prompt-Caching, Structured Output, Extended Thinking ------

def _prompt_caching_enabled() -> bool:
    return os.getenv("ANTHROPIC_PROMPT_CACHING", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def _build_user_content(prompt: str, context_prefix: Optional[str]) -> List[Any]:
    """User-Content-Blöcke: optionaler gemeinsamer Kontext-Prefix (mit
    cache_control) vor dem sektionsspezifischen Prompt.

    Der Prefix ist je Report-Lauf für ALLE Sektionen identisch — der
    Anthropic-Prompt-Cache (5-Min-TTL) trifft damit ab dem zweiten
    Sektions-Call und spart den Großteil der Input-Kosten des Laufs.
    """
    if context_prefix and _prompt_caching_enabled():
        return [
            {
                "type": "text",
                "text": context_prefix,
                "cache_control": {"type": "ephemeral"},
            },
            {"type": "text", "text": prompt},
        ]
    if context_prefix:
        return [{"type": "text", "text": f"{context_prefix}\n\n{prompt}"}]
    return [{"type": "text", "text": prompt}]


# KIS-1288: Modelle, deren Thinking-Einschaltform {"type": "adaptive"} ist.
# Das alte Format {"type": "enabled", "budget_tokens": N} lehnen sie mit 400
# ab (Sonnet 5 / Opus 5 / 4.7 / 4.8) bzw. es ist deprecated (4.6). Die Menge
# ist identisch mit den Modellen, die temperature ablehnen — bewusst geteilt.
_ADAPTIVE_THINKING_MODEL_MARKERS = _NO_TEMPERATURE_MODEL_MARKERS


def _maybe_add_thinking(kwargs: dict, section: Optional[str], max_tok: int) -> dict:
    """Extended Thinking für ausgewählte Sektionen (Default: aus).

    ANTHROPIC_THINKING_BUDGET=<tokens> + ANTHROPIC_THINKING_SECTIONS=a,b,c
    aktivieren thinking für die genannten Sektionen.

    KIS-1288: Das Format hängt vom Modell ab. 4.6+/Claude-5-Modelle bekommen
    {"type": "adaptive"} — budget_tokens gibt dort 400. Ältere Modelle
    behalten das budget_tokens-Format (dort Pflicht). In beiden Fällen wird
    max_tokens auf Budget+2000 angehoben (alt: API-Anforderung
    max_tokens > budget_tokens; adaptiv: Kopffreiheit, weil Denk-Tokens
    gegen max_tokens zählen) und temperature entfällt (mit thinking
    unvereinbar). output_config (effort) bleibt bei adaptive erhalten —
    effort steuert dort die Denktiefe.
    """
    try:
        _budget = int(os.getenv("ANTHROPIC_THINKING_BUDGET", "0"))
    except ValueError:
        _budget = 0
    if _budget <= 0 or not section:
        return kwargs
    _sections = {
        s.strip().lower()
        for s in os.getenv("ANTHROPIC_THINKING_SECTIONS", "").split(",")
        if s.strip()
    }
    if section.strip().lower() not in _sections:
        return kwargs
    _model = str(kwargs.get("model") or "").lower()
    _adaptive = any(marker in _model for marker in _ADAPTIVE_THINKING_MODEL_MARKERS)
    if _adaptive:
        kwargs["thinking"] = {"type": "adaptive"}
    else:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": _budget}
        kwargs.pop("output_config", None)
    kwargs.pop("temperature", None)
    kwargs["max_tokens"] = max(max_tok, _budget + 2000)
    log.info(
        "🧠 [KIS-1234-P2/KIS-1288] Extended Thinking für section=%s (format=%s, budget=%d)",
        section, "adaptive" if _adaptive else "budget_tokens", _budget,
    )
    return kwargs


def call_anthropic_structured(
    prompt: str,
    *,
    section: str,
    schema: dict,
    tool_name: str = "emit_result",
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    context_prefix: Optional[str] = None,
) -> Optional[dict]:
    """Erzwingt strukturierten JSON-Output über Tool-Use (KIS-1234-P2).

    Eliminiert die FIX-499-Fehlerklasse (unparseables/truncated JSON aus
    Freitext) architektonisch: Die API validiert gegen das Schema, wir
    lesen den tool_use-Input als fertiges Dict.
    """
    client = get_anthropic_client()
    if client is None or not prompt or not prompt.strip():
        return None
    model_name = _resolve_anthropic_model(section, None)
    max_tok = max_tokens if max_tokens is not None else _get_max_tokens_for_section(section)
    kwargs = build_anthropic_create_kwargs(
        model=model_name,
        max_tokens=max_tok,
        temperature=_get_temperature_for_section(section),
        system=system_prompt or "Du bist ein hilfreicher, präziser KI-Berater.",
        messages=[{"role": "user", "content": _build_user_content(prompt, context_prefix)}],
    )
    kwargs["tools"] = [{
        "name": tool_name,
        "description": "Gibt das Ergebnis strikt im geforderten Schema zurück.",
        "input_schema": schema,
    }]
    kwargs["tool_choice"] = {"type": "tool", "name": tool_name}
    try:
        message = client.messages.create(**kwargs)
        log_anthropic_usage(message, call_site=f"structured:{section}", model=model_name)
    except anthropic.BadRequestError as exc:
        if "temperature" in str(exc) and "deprecated" in str(exc):
            kwargs.pop("temperature", None)
            try:
                message = client.messages.create(**kwargs)
                log_anthropic_usage(
                    message, call_site=f"structured:{section}:retry-no-temp",
                    model=model_name,
                )
            except Exception as retry_exc:
                log.warning("⚠️ [STRUCTURED] Retry gescheitert (%s): %s", section, str(retry_exc)[:200])
                return None
        else:
            log.warning("⚠️ [STRUCTURED] BadRequest (%s): %s", section, str(exc)[:200])
            return None
    except Exception as exc:
        log.warning("⚠️ [STRUCTURED] API-Fehler (%s): %s", section, str(exc)[:200])
        return None

    # KIS-1288: Gleiches Netz wie call_anthropic (KIS-1231). Endet der Call
    # am Token-Limit, ist der tool_use-Input oft unvollständig oder fehlt —
    # einmaliger Retry mit erhöhtem Budget statt abgeschnittener Struktur.
    if getattr(message, "stop_reason", None) == "max_tokens":
        retry_max = _truncation_retry_max_tokens(max_tok)
        if _truncation_retry_enabled() and retry_max > max_tok:
            log.warning(
                "⚠️ [STRUCTURED/KIS-1288] section=%s hit max_tokens (%d) — Retry mit Budget %d",
                section, max_tok, retry_max,
            )
            retry_kwargs = dict(kwargs)
            retry_kwargs["max_tokens"] = retry_max
            try:
                retry_message = client.messages.create(**retry_kwargs)
                log_anthropic_usage(
                    retry_message,
                    call_site=f"structured:{section}:truncation-retry",
                    model=model_name,
                )
                if getattr(retry_message, "stop_reason", None) != "max_tokens":
                    message = retry_message
                else:
                    log.warning(
                        "⚠️ [STRUCTURED/KIS-1288] Retry section=%s erneut am Limit (%d) — "
                        "verwende Erst-Antwort",
                        section, retry_max,
                    )
            except Exception as retry_exc:
                log.warning(
                    "⚠️ [STRUCTURED/KIS-1288] Retry section=%s gescheitert: %s — "
                    "verwende Erst-Antwort",
                    section, str(retry_exc)[:200],
                )

    _input = _extract_structured_tool_input(message, tool_name)
    if _input is not None:
        log.info("✅ [STRUCTURED] section=%s via tool_use (stop=%s)",
                 section, getattr(message, "stop_reason", "?"))
        return _input
    log.warning("⚠️ [STRUCTURED] Kein tool_use-Block in Antwort (%s)", section)
    return None


def _extract_structured_tool_input(message: Any, tool_name: str) -> Optional[dict]:
    """Liest den input des passenden tool_use-Blocks aus einer Message."""
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", "") == tool_name:
            _input = getattr(block, "input", None)
            if isinstance(_input, dict):
                return _input
    return None


def call_anthropic(
    prompt: str,
    *,
    section: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
    context_prefix: Optional[str] = None,
) -> Optional[str]:
    """
    Spricht die Anthropic Messages API an und gibt den Text-Content zurück.

    Signature ist bewusst ähnlich wie _call_openai(...) in gpt_analyze.py,
    damit wir sie leicht austauschen / einbinden können.
    """
    client = get_anthropic_client()
    if client is None:
        log.error(
            "❌ call_anthropic() aufgerufen, aber kein gültiger Anthropic-Client verfügbar."
        )
        return None

    # Modell-Mapping durchführen
    model_name = _resolve_anthropic_model(section, model)
    log_premium_routing(section or "", model_name)
    temp = temperature if temperature is not None else _get_temperature_for_section(section)
    max_tok = max_tokens if max_tokens is not None else _get_max_tokens_for_section(section)
    sys = system_prompt or "Du bist ein hilfreicher, präziser KI-Berater."

    # Stop-Sequences für PLATIN-kritische Sections (Anthropic still supports this)
    # OpenAI no longer supports stop parameter for new models (gpt-4o-mini, gpt-4.1, etc.)
    stop_seqs: Optional[List[str]] = None
    if section and _get_platin_config(section) and _PLATIN_STOP_SEQUENCES:
        stop_seqs = _PLATIN_STOP_SEQUENCES
        log.debug("🛑 Added stop sequences for Anthropic section=%s", section)

    # =========================================================================
    # FIX-J7: 3-Layer Empty Content Guard (prevents 400 Bad Request)
    # Layer 1: Empty prompt → return fallback
    # Layer 2: Whitespace-only prompt → return fallback
    # Layer 3: BadRequestError catch → return fallback instead of crash
    # =========================================================================
    if not prompt or not prompt.strip():
        log.warning(
            "[FIX-J7] Empty/whitespace prompt for section=%s — skipping API call",
            section or "unknown"
        )
        return ""

    # Build messages list — KIS-1234-P2: optionaler gemeinsamer
    # Kontext-Prefix mit cache_control (Prompt-Caching über den Lauf).
    messages: List[Any] = [
        {
            "role": "user",
            "content": _build_user_content(prompt, context_prefix),
        }
    ]

    # Versuch 1: Mit aufgelöstem Modell
    _first_kwargs = build_anthropic_create_kwargs(
        model=model_name,
        max_tokens=max_tok,
        temperature=temp,
        system=sys,
        messages=messages,
        stop_sequences=stop_seqs,
    )
    _first_kwargs = _maybe_add_thinking(_first_kwargs, section, max_tok)
    try:
        message = client.messages.create(**_first_kwargs)
        log_anthropic_usage(
            message, call_site=f"call_anthropic:{section or 'unknown'}", model=model_name,
        )
    except anthropic.BadRequestError as exc:
        # KIS-1230-HOTFIX: Reaktives Sicherheitsnetz — lehnt ein (neues)
        # Modell einen Sampling-Parameter ab ("`temperature` is deprecated"),
        # einmal OHNE den Parameter wiederholen statt leer zurückzugeben.
        # Genau dieser Pfad hat im KIS-1230-Lauf alle claude-sonnet-5-
        # Sektionen (u.a. die Decision-Boxen) in die Fallback-Kette geschickt.
        _msg = str(exc)
        if "temperature" in _msg and "deprecated" in _msg:
            log.warning(
                "⚠️ Anthropic lehnt temperature für Modell '%s' ab (Abschnitt '%s') "
                "— Retry ohne temperature",
                model_name, section,
            )
            try:
                _retry_kwargs = build_anthropic_create_kwargs(
                    model=model_name,
                    max_tokens=max_tok,
                    temperature=temp,
                    system=sys,
                    messages=messages,
                    stop_sequences=stop_seqs,
                )
                _retry_kwargs.pop("temperature", None)
                message = client.messages.create(**_retry_kwargs)
                log_anthropic_usage(
                    message,
                    call_site=f"call_anthropic:{section or 'unknown'}:retry-no-temp",
                    model=model_name,
                )
            except Exception as retry_exc:
                log.warning(
                    "⚠️ Retry ohne temperature gescheitert für Abschnitt '%s': %s — returning empty",
                    section, str(retry_exc)[:200]
                )
                return ""
        else:
            # FIX-J7 Layer 3: Catch 400 errors (empty content, invalid params)
            log.warning(
                "⚠️ Anthropic BadRequestError für Abschnitt '%s': %s — returning empty",
                section, str(exc)[:200]
            )
            return ""

    except anthropic.NotFoundError as exc:
        # Modell nicht gefunden -> Fallback-Versuch
        fallback_model = os.getenv("ANTHROPIC_MODEL_FALLBACK", "claude-sonnet-4-5-20250929").strip()  # K1 + FIX-STRIP
        log.warning(
            "⚠️ Anthropic NotFoundError für Modell '%s' (Abschnitt '%s'): %s. "
            "Versuche Fallback-Modell '%s'...",
            model_name,
            section,
            str(exc),
            fallback_model
        )

        # Retry mit Fallback
        try:
            message = client.messages.create(**build_anthropic_create_kwargs(
                model=fallback_model,
                max_tokens=max_tok,
                temperature=temp,
                system=sys,
                messages=messages,
                stop_sequences=stop_seqs,
            ))
            log_anthropic_usage(
                message,
                call_site=f"call_anthropic:{section or 'unknown'}:model-fallback",
                model=fallback_model,
            )
            log.info(
                "✅ Fallback auf Modell '%s' erfolgreich (Abschnitt '%s')",
                fallback_model,
                section
            )
        except Exception as retry_exc:
            log.error(
                "❌ Auch Fallback-Modell '%s' gescheitert (Abschnitt '%s'): %s",
                fallback_model,
                section,
                str(retry_exc)
            )
            return None
    except Exception as exc:  # pragma: no cover
        log.exception("❌ Fehler beim Aufruf der Anthropic API (Abschnitt '%s'): %s", section, exc)
        return None

    # Response auslesen mit PLATIN+ Diagnostik
    try:
        text = _extract_message_text(message)

        # PLATIN+ Diagnostik: Einheitliches Log-Format (wie OpenAI) für Railway
        stop_reason = getattr(message, "stop_reason", "unknown")
        usage = getattr(message, "usage", None)
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        section_label = section or "unknown"

        if stop_reason == "max_tokens":
            log.warning(
                "⚠️ LLM section=%s finished with reason=max_tokens (hit token limit %d) – risk of truncation",
                section_label,
                max_tok,
            )
            # KIS-1231: Einmaliger Retry mit erhöhtem Budget statt
            # abgeschnittenen Text weiterzureichen (truncated JSON in
            # quick_wins brach im STRICT-Modus den ganzen Report ab).
            retry_max = _truncation_retry_max_tokens(max_tok)
            if _truncation_retry_enabled() and retry_max > max_tok:
                try:
                    _trunc_kwargs = build_anthropic_create_kwargs(
                        model=model_name,
                        max_tokens=retry_max,
                        temperature=temp,
                        system=sys,
                        messages=messages,
                        stop_sequences=stop_seqs,
                    )
                    try:
                        retry_message = client.messages.create(**_trunc_kwargs)
                    except anthropic.BadRequestError as _trunc_exc:
                        # gleiches reaktives Netz wie beim Erst-Call
                        if "temperature" in str(_trunc_exc) and "deprecated" in str(_trunc_exc):
                            _trunc_kwargs.pop("temperature", None)
                            retry_message = client.messages.create(**_trunc_kwargs)
                        else:
                            raise
                    log_anthropic_usage(
                        retry_message,
                        call_site=f"call_anthropic:{section_label}:truncation-retry",
                        model=model_name,
                    )
                    retry_text = _extract_message_text(retry_message)
                    retry_stop = getattr(retry_message, "stop_reason", "unknown")
                    retry_usage = getattr(retry_message, "usage", None)
                    retry_tokens = getattr(retry_usage, "output_tokens", 0) if retry_usage else 0
                    if retry_text and (retry_stop != "max_tokens" or len(retry_text) > len(text)):
                        log.info(
                            "✅ [KIS-1231] Truncation-Retry section=%s erfolgreich: "
                            "reason=%s tokens=%d (Budget %d→%d)",
                            section_label, retry_stop, retry_tokens, max_tok, retry_max,
                        )
                        return retry_text
                    log.warning(
                        "⚠️ [KIS-1231] Truncation-Retry section=%s brachte keine Verbesserung "
                        "(reason=%s, len %d vs. %d) — behalte Erst-Antwort",
                        section_label, retry_stop, len(retry_text or ""), len(text),
                    )
                except Exception as trunc_retry_exc:
                    log.warning(
                        "⚠️ [KIS-1231] Truncation-Retry section=%s gescheitert: %s — "
                        "behalte (möglicherweise abgeschnittene) Erst-Antwort",
                        section_label, str(trunc_retry_exc)[:200],
                    )
        else:
            log.info(
                "✅ LLM section=%s finished with reason=%s (tokens=%d, max=%d)",
                section_label,
                stop_reason,
                output_tokens,
                max_tok,
            )

        return text or None
    except Exception as exc:  # pragma: no cover
        log.exception(
            "❌ Konnte Anthropic-Antwort nicht auslesen (Abschnitt %s): %s",
            section,
            exc,
        )
        return None

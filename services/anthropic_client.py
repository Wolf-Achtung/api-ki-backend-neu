# services/anthropic_client.py

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Callable, List, Optional

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


def call_anthropic(
    prompt: str,
    *,
    section: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None,
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

    # Build messages list
    messages: List[Any] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                }
            ],
        }
    ]

    # Versuch 1: Mit aufgelöstem Modell
    try:
        message = client.messages.create(**build_anthropic_create_kwargs(
            model=model_name,
            max_tokens=max_tok,
            temperature=temp,
            system=sys,
            messages=messages,
            stop_sequences=stop_seqs,
        ))
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
        parts = []
        for block in getattr(message, "content", []) or []:
            if getattr(block, "type", None) == "text":
                parts.append(getattr(block, "text", "") or "")
        text = "".join(parts).strip()

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

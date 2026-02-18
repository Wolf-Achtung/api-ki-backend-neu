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

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")  # K1: updated
DEFAULT_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "5000"))  # J11: raised from 3000
DEFAULT_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2"))

# --- RUN-622 P2: Opus Routing ------------------------------------------------
OPUS_MODEL = os.getenv("ANTHROPIC_MODEL_OPUS", "claude-opus-4-5-20250929")
_OPUS_SECTIONS_RAW = os.getenv("OPUS_SECTIONS", "")
OPUS_SECTIONS_SET: set = {
    s.strip().lower()
    for s in _OPUS_SECTIONS_RAW.split(",")
    if s.strip()
}
if OPUS_SECTIONS_SET:
    log.info(
        "🎯 [RUN-622] Opus routing enabled for %d sections: %s",
        len(OPUS_SECTIONS_SET), sorted(OPUS_SECTIONS_SET),
    )
else:
    log.info("ℹ️ [RUN-622] Opus routing disabled (OPUS_SECTIONS not set)")

# z.B. USE_ANTHROPIC_FOR_EXEC_SUMMARY, USE_ANTHROPIC_FOR_RISKS, ...
SECTION_FLAG_PREFIX = "USE_ANTHROPIC_FOR_"


# --- Hilfsfunktionen -------------------------------------------------------


def _normalize_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    value = value.strip().lower()
    return value in ("1", "true", "yes", "on")


_SECTION_ENV_ALIASES = {
    # Abschnitts-Key -> ENV-Suffix
    # executive_summary => EXEC_SUMMARY (analog zu OPENAI_MODEL_EXEC_SUMMARY)
    "executive_summary": "EXEC_SUMMARY",
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
    
    Reihenfolge:
    1. Sektion-spezifischer ENV-Override: ANTHROPIC_MODEL_<SECTION_IN_UPPERCASE>
    2. Globale ENV-Variable: ANTHROPIC_MODEL_DEFAULT -> ANTHROPIC_MODEL
    3. Falls requested_model ein Claude-Modell ist, verwende es
    4. Fallback: "claude-3-5-sonnet-latest"
    
    Args:
        section: Der Abschnitts-Identifier (z.B. "executive_summary")
        requested_model: Das ursprünglich angeforderte Modell (kann OpenAI-Modell sein)
    
    Returns:
        Ein valider Claude-Modellname
    """
    # 1. Sektion-spezifischer Override
    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        env_name = f"ANTHROPIC_MODEL_{suffix}"
        section_model = os.getenv(env_name)
        if section_model:
            log.info(
                "🎯 anthropic_client: Using model '%s' for section '%s' (requested='%s', source='%s')",
                section_model,
                section,
                requested_model or "None",
                env_name
            )
            return section_model
    
    # 1b. RUN-622 P2: Opus Routing via OPUS_SECTIONS ENV
    section_lower = (section or "").strip().lower()
    if section_lower in OPUS_SECTIONS_SET:
        log.info(
            "🎯 anthropic_client: Opus routing → '%s' for section '%s' (source='OPUS_SECTIONS')",
            OPUS_MODEL, section,
        )
        return OPUS_MODEL
    
    # 2. Globale ENV-Variablen
    global_model = os.getenv("ANTHROPIC_MODEL_DEFAULT") or os.getenv("ANTHROPIC_MODEL")
    if global_model:
        log.info(
            "🎯 anthropic_client: Using model '%s' for section '%s' (requested='%s', source='ENV')",
            global_model,
            section,
            requested_model or "None"
        )
        return global_model
    
    # 3. Requested model prüfen
    if requested_model:
        if _is_openai_model(requested_model):
            # OpenAI-Modell erkannt -> Ignorieren und Fallback verwenden
            fallback = "claude-3-5-sonnet-latest"
            log.info(
                "🔄 anthropic_client: Mapping OpenAI model '%s' to Claude model '%s' for section '%s'",
                requested_model,
                fallback,
                section
            )
            return fallback
        elif _is_claude_model(requested_model):
            # Valides Claude-Modell
            log.info(
                "✅ anthropic_client: Using model '%s' for section '%s' (requested='%s')",
                requested_model,
                section,
                requested_model
            )
            return requested_model
    
    # 4. Harter Fallback
    fallback = "claude-3-5-sonnet-latest"
    log.info(
        "🔄 anthropic_client: Using fallback model '%s' for section '%s' (requested='%s')",
        fallback,
        section,
        requested_model or "None"
    )
    return fallback


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

    client = anthropic.Anthropic(api_key=api_key)
    log.info("✅ Anthropic-Client initialisiert.")
    return client


def _get_model_for_section(section: Optional[str]) -> str:
    """
    Ermittelt das Anthropic-Modell für einen Abschnitt:
    1. ANTHROPIC_MODEL_<SECTION>
    2. ANTHROPIC_MODEL
    3. DEFAULT_MODEL
    """
    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        env_name = f"ANTHROPIC_MODEL_{suffix}"
        section_model = os.getenv(env_name)
        if section_model:
            return section_model

    return os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)


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
        log.debug(
            "✅ LLM_PROVIDER_DEFAULT=anthropic – verwende Anthropic für Abschnitt %s",
            section,
        )
        return True

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
        if stop_seqs:
            message = client.messages.create(
                model=model_name,
                max_tokens=max_tok,
                temperature=temp,
                system=sys,
                messages=messages,
                stop_sequences=stop_seqs,
            )
        else:
            message = client.messages.create(
                model=model_name,
                max_tokens=max_tok,
                temperature=temp,
                system=sys,
                messages=messages,
            )
    except anthropic.BadRequestError as exc:
        # FIX-J7 Layer 3: Catch 400 errors (empty content, invalid params)
        log.warning(
            "⚠️ Anthropic BadRequestError für Abschnitt '%s': %s — returning empty",
            section, str(exc)[:200]
        )
        return ""

    except anthropic.NotFoundError as exc:
        # Modell nicht gefunden -> Fallback-Versuch
        fallback_model = os.getenv("ANTHROPIC_MODEL_FALLBACK", "claude-sonnet-4-5-20250929")  # K1: updated
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
            if stop_seqs:
                message = client.messages.create(
                    model=fallback_model,
                    max_tokens=max_tok,
                    temperature=temp,
                    system=sys,
                    messages=messages,
                    stop_sequences=stop_seqs,
                )
            else:
                message = client.messages.create(
                    model=fallback_model,
                    max_tokens=max_tok,
                    temperature=temp,
                    system=sys,
                    messages=messages,
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

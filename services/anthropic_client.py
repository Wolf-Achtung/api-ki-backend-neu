# services/anthropic_client.py

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # Wir loggen das später sauber weg

log = logging.getLogger(__name__)

# --- ENV Defaults ----------------------------------------------------------

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet")
DEFAULT_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "3000"))
DEFAULT_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2"))

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


@lru_cache(maxsize=1)
def get_anthropic_client() -> Optional["anthropic.Anthropic"]:
    """
    Liefert eine gecachte Anthropic-Client-Instanz oder None, wenn
    kein API-Key oder kein anthropic-Paket vorhanden ist.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log.warning("ANTHROPIC_API_KEY not set – Anthropic-Client deaktiviert.")
        return None

    if anthropic is None:
        log.error(
            "anthropic-Paket nicht installiert. "
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
                    "Ungültige Temperatur in %s=%r – verwende Default.",
                    env_name,
                    section_temp,
                )

    global_temp = os.getenv("ANTHROPIC_TEMPERATURE")
    if global_temp:
        try:
            return float(global_temp)
        except ValueError:
            log.warning(
                "Ungültige ANTHROPIC_TEMPERATURE=%r – verwende Default.",
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
                    "Ungültige MaxTokens in %s=%r – verwende Default.",
                    env_name,
                    section_max,
                )

    global_max = os.getenv("ANTHROPIC_MAX_TOKENS")
    if global_max:
        try:
            return int(global_max)
        except ValueError:
            log.warning(
                "Ungültige ANTHROPIC_MAX_TOKENS=%r – verwende Default.",
                global_max,
            )

    return DEFAULT_MAX_TOKENS


def should_use_anthropic(section: Optional[str] = None) -> bool:
    """
    Entscheidet, ob für einen Abschnitt Anthropic genutzt werden soll.

    Reihenfolge:
    1. Wenn kein API-Key oder kein Client -> False
    2. Section-Flag: USE_ANTHROPIC_FOR_<SECTION> (wenn gesetzt)
    3. LLM_PROVIDER_DEFAULT == 'anthropic' -> True
    4. sonst False
    """
    client = get_anthropic_client()
    if client is None:
        return False

    suffix = section_to_env_suffix(section) if section else None
    if suffix:
        flag_name = f"{SECTION_FLAG_PREFIX}{suffix}"
        flag_val = os.getenv(flag_name)
        if flag_val is not None:
            # expliziter Override
            use_it = _normalize_bool(flag_val)
            log.debug(
                "Anthropic-Routing für Abschnitt %s (%s=%r) -> %s",
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
            "LLM_PROVIDER_DEFAULT=anthropic – verwende Anthropic für Abschnitt %s",
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
            "call_anthropic() aufgerufen, aber kein gültiger Anthropic-Client verfügbar."
        )
        return None

    model_name = model or _get_model_for_section(section)
    temp = temperature if temperature is not None else _get_temperature_for_section(section)
    max_tok = max_tokens if max_tokens is not None else _get_max_tokens_for_section(section)
    sys = system_prompt or "Du bist ein hilfreicher, präziser KI-Berater."

    try:
        # Siehe Anthropic-Doku: Messages API
        # https://platform.claude.com/docs/en/build-with-claude/working-with-messages
        message = client.messages.create(
            model=model_name,
            max_tokens=max_tok,
            temperature=temp,
            system=sys,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        }
                    ],
                }
            ],
        )
    except Exception as exc:  # pragma: no cover
        log.exception("❌ Fehler beim Aufruf der Anthropic API: %s", exc)
        return None

    # message.content ist eine Liste von Content-Blöcken (typischerweise Text)
    try:
        parts = []
        for block in getattr(message, "content", []) or []:
            # SDK: block.type, block.text
            if getattr(block, "type", None) == "text":
                parts.append(getattr(block, "text", "") or "")
        text = "".join(parts).strip()
        log.debug(
            "✅ Anthropic-Antwort für Abschnitt %s (%s Tokens, Modell %s)",
            section,
            len(text),
            model_name,
        )
        return text or None
    except Exception as exc:  # pragma: no cover
        log.exception(
            "❌ Konnte Anthropic-Antwort nicht auslesen (Abschnitt %s): %s",
            section,
            exc,
        )
        return None

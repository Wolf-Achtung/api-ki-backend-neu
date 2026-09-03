# -*- coding: utf-8 -*-
"""KIS-1272: Der Notfall-Fallback darf die Report-Qualitaet nicht senken.

ANTHROPIC_MODEL_FALLBACK greift an genau einer Stelle
(services/anthropic_client.py) und nur bei anthropic.NotFoundError —
also wenn eine konfigurierte Modell-ID nicht existiert. Das passiert
praktisch nie: bei einem Tippfehler in der ENV oder wenn ein Modell
abgeschaltet wird.

Tritt der Fall aber ein, laufen ALLE Sektionen des Reports auf dem
Fallback. Ein schwaecheres Modell wuerde dann einen sichtbar schlechteren
Beratungsbericht erzeugen — ohne harten Fehler, also unbemerkt.

Weil der Pfad so selten greift, spart ein billigeres Fallback-Modell
nichts Nennenswertes. Der Code-Default ist deshalb bewusst ein
Sonnet-Modell. Dieser Test haelt das fest, damit es niemand spaeter
"optimiert".
"""
from __future__ import annotations

import inspect
import re

import services.anthropic_client as ac

# Modellklassen, die als Notfall-Ersatz fuer einen Beratungsbericht taugen.
TAUGLICHE_KLASSEN = ("sonnet", "opus")


def _code_default() -> str:
    """Liest den Default aus dem Aufruf im Quelltext (nicht aus der ENV)."""
    quelle = inspect.getsource(ac)
    treffer = re.search(
        r'os\.getenv\(\s*["\']ANTHROPIC_MODEL_FALLBACK["\']\s*,\s*["\']([^"\']+)["\']',
        quelle,
    )
    assert treffer, "Default fuer ANTHROPIC_MODEL_FALLBACK nicht gefunden"
    return treffer.group(1)


class TestCodeDefault:

    def test_default_ist_sonnet_oder_opus(self):
        default = _code_default().lower()
        assert any(k in default for k in TAUGLICHE_KLASSEN), (
            f"Fallback-Default '{default}' ist keine Sonnet-/Opus-Klasse. "
            "Der Fallback ersetzt im Ernstfall JEDE Report-Sektion."
        )

    def test_default_ist_kein_haiku(self):
        assert "haiku" not in _code_default().lower()

    def test_default_ist_gesetzt(self):
        assert _code_default().strip()


class TestFallbackPfad:

    def test_greift_nur_bei_notfounderror(self):
        """Waere der Fallback auch bei Ueberlast oder Rate-Limit aktiv,
        traefe er regelmaessig statt nie — dann waere die Modellwahl eine
        Kostenfrage. Ist sie nicht."""
        quelle = inspect.getsource(ac)
        block = quelle.split("ANTHROPIC_MODEL_FALLBACK")[0]
        letzter_except = block.rsplit("except ", 1)[1].split(":")[0]
        assert "NotFoundError" in letzter_except, (
            f"Fallback haengt an '{letzter_except}', nicht an NotFoundError"
        )

    def test_fallback_wird_protokolliert(self):
        """Ein stiller Modellwechsel waere im Betrieb nicht erkennbar."""
        quelle = inspect.getsource(ac)
        stelle = quelle.find("ANTHROPIC_MODEL_FALLBACK")
        umfeld = quelle[stelle:stelle + 600]
        assert "log.warning" in umfeld or "log.error" in umfeld

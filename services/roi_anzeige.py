# -*- coding: utf-8 -*-
"""KIS-1284: ROI-Prozente so anzeigen, dass zwei Sichten zwei Zahlen sind.

Der Status-Report stellt auf der Business-Case-Seite zwei ROI-Sichten
nebeneinander und erklaert darunter: „Beide Werte sind korrekt — sie
unterscheiden sich nur in der Investitionsbasis."

Im Lauf KIS-1268 stand in beiden Zeilen ``1 %``:

    CAPEX-Sicht    (28.500 - 4.200 - 24.000) / 24.000 = 1,25 %
    Gesamt-Sicht   (28.500 - 4.200 - 24.000) / 28.200 = 1,06 %

Beide Rechnungen stimmen. Nur rundet ``int()`` sie auf dieselbe Zahl, und
der Satz darunter behauptet dann einen Unterschied, den der Leser nicht
sieht. Bei kleinen Prozentwerten steckt die Aussage in der ersten
Nachkommastelle — also wird sie dort gezeigt.

Ab zehn Prozent bleibt es bei ganzen Zahlen: „47 %" liest sich besser als
„47,3 %", und der Unterschied zwischen zwei Sichten ist dort ohnehin
sichtbar.
"""
from __future__ import annotations

from typing import Optional

# Unterhalb dieser Grenze entscheidet die erste Nachkommastelle.
DEZIMAL_UNTER = 10.0


def als_prozent(wert, dezimal_unter: float = DEZIMAL_UNTER) -> Optional[str]:
    """Formatiert einen ROI-Prozentwert deutsch: „1,3 %" bzw. „47 %".

    Gibt ``None`` zurueck, wenn der Wert keine Zahl ist — der Aufrufer
    entscheidet dann selbst, was er anzeigt.
    """
    try:
        zahl = float(wert)
    except (TypeError, ValueError):
        return None
    if abs(zahl) < dezimal_unter:
        return f"{zahl:.1f}".replace(".", ",") + " %"
    return f"{int(round(zahl))} %"

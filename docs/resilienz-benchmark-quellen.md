# Resilienz-Check: zitierfähige Quellen für die Geschwindigkeits-Benchmark

Stand: 2026-08-23 · Recherche-Task aus dem Resilienz-Go (offene Frage 3).
Zweck: Die Kernzahl des Reports („Ihr Angreifer braucht ~15 Minuten") braucht
eine öffentliche Quelle statt nur des Buchs.

## Ergebnis in einem Satz

Die 15-Minuten-Benchmark ist durch öffentliche Zahlen nicht nur gedeckt,
sondern **konservativ**: CrowdStrike misst für 2025 eine durchschnittliche
eCrime-Breakout-Zeit von **29 Minuten**, im schnellsten Fall **27 Sekunden**,
mit Datenabfluss **binnen 4 Minuten** nach Erstzugriff.

## Primärquellen

| Quelle | Kernzahl | Verwendung im Report |
|---|---|---|
| **CrowdStrike 2026 Global Threat Report** (Pressemitteilung, 24.02.2026): [Presseseite](https://www.crowdstrike.com/en-us/press-releases/2026-crowdstrike-global-threat-report/) · [Report-Seite](https://www.crowdstrike.com/en-us/global-threat-report/) · [Businesswire](https://secure.businesswire.com/news/home/20260224017260/en/2026-CrowdStrike-Global-Threat-Report-AI-Accelerates-Adversaries-and-Reshapes-the-Attack-Surface) | Ø Breakout-Zeit **29 Minuten** (2025, −65 % ggü. Vorjahr); schnellster Fall **27 Sekunden**; Datenexfiltration in einem Fall **4 Minuten** nach Erstzugriff; KI-gestützte Angriffe **+89 %** | Fußnote zur Zeitstrahl-Grafik (Seite 1) |
| **BSI, Die Lage der IT-Sicherheit in Deutschland 2025**: [Übersicht](https://www.bsi.bund.de/DE/Service-Navi/Publikationen/Lagebericht/lagebericht_node.html) · [Kurzfassung (PDF)](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Publikationen/Lageberichte/Lagebericht2025_Achtseiter.pdf) | Ø **119 neue Schwachstellen/Tag** (+24 %); Ransomware als Hauptbedrohung; zunehmend KI-gestützte Angriffe; KMU besonders verwundbar | Deutscher Behörden-Anker für Pflichtenlage/NIS2-Seite |

## Vorgeschlagene Fußnote für den Report (juristisch unkritisch formuliert)

> Benchmark: Der Sicherheitsanbieter CrowdStrike misst für 2025 eine
> durchschnittliche „Breakout-Zeit" (Erstzugriff bis Ausbreitung) von
> 29 Minuten; der schnellste beobachtete Fall lag bei 27 Sekunden
> (CrowdStrike Global Threat Report 2026). Die im Report verwendete
> 15-Minuten-Marke liegt innerhalb dieser öffentlich dokumentierten
> Spanne.

## Einschränkungen (ehrlich)

- Die Zahlen stammen aus den Such-Snippets der offiziellen Presse- und
  Report-Seiten; der Egress-Proxy dieser Umgebung blockiert den
  Direktabruf von crowdstrike.com. **Vor dem ersten Druck einmal die
  verlinkte Presseseite öffnen und die drei Zahlen gegenlesen.**
- „Breakout-Zeit" (Ausbreitung im Netz) ist nicht identisch mit
  „Angriff abgeschlossen" — die Fußnoten-Formulierung oben trägt dem
  Rechnung und behauptet nur, was die Quelle deckt.

## Marken-Vorrecherche „Reaktionslücke" (offene Frage 4, Vorarbeit)

- Web-Suche (2026-08-23) findet **keine bestehende Marke und keinen
  Wettbewerber-Gebrauch** des Begriffs „Reaktionslücke" im
  Security-Kontext — gutes Vorzeichen, aber kein Beleg.
- Die formale Prüfung läuft über das DPMA-Register:
  [register.dpma.de](https://register.dpma.de/DPMAregister/Uebersicht)
  (kostenlos, Identitäts- und Ähnlichkeitsrecherche), Merkblatt:
  [W 7731](https://www.dpma.de/docs/formulare/marken/w7731.pdf).
  Dieser Schritt und die anwaltliche Prüfung (Haftungsausschluss,
  NIS2-Aussagen) bleiben Wolfs externe Aufgaben — der Entwurfstext
  für den Haftungsausschluss steht in
  `services/resilienz_pipeline.py` (`DISCLAIMER_DE`).

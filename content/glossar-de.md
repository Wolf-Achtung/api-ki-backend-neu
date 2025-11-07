# Glossar (Auszug)

- **RAG (Retrieval‑Augmented Generation)** – Abruf interner Inhalte (Vektorindex) in den Prompt, um fundierte, zitierbare Antworten zu erhalten.
- **Embedding** – Vektor‑Darstellung eines Textes zur semantischen Ähnlichkeitssuche (z. B. E5, Instructor).
- **Vektordatenbank** – Speicher für Embeddings (z. B. FAISS, Chroma) als Wissens‑Index für RAG.
- **Prompt Engineering** – Strukturierte Erstellung/Optimierung von Prompts (Rollen, Beispiele, Format‑Constraints).
- **Zero‑/Few‑Shot** – Keine bzw. wenige Beispiele im Prompt; Few‑Shot steuert Stil & Format.
- **Fine‑Tuning** – Weitertraining auf Beispieldaten; erhöht Konsistenz, benötigt Governance & Test.
- **Halluzination** – Faktisch falsche, aber plausibel klingende Antwort eines Modells; Gegenmittel: RAG, Quellen, Guardrails.
- **Guardrails** – Regeln/Filter zum Schutz von Daten & Ausgaben (PII‑Filter, Blocklisten, Validierung).
- **Context Window** – Maximale Token‑Länge pro Anfrage (z. B. 128k).
- **Token** – Kleinste Verarbeitungseinheit (ähnlich Silben/Wörter). Zählt für Kosten & Limits.
- **DPIA/DSFA** – Datenschutz‑Folgenabschätzung; Pflicht bei bestimmten Risiken/Einsätzen.
- **EU AI Act** – EU‑Rechtsrahmen; Pflichten je nach Risiko‑Level und Use Case.
- **Content Safety** – Dienste zur Moderation/Filterung von Ein-/Ausgaben (z. B. Azure Content Safety).
- **Observability** – Nachvollziehbarkeit & Monitoring von Pipelines/Prompts (z. B. OpenTelemetry Hooks).
- **Payback/ROI** – Rückfluss der Investition / Return on Investment; mit realistischen Annahmen berechnen.
- **Change Management** – Mitarbeiter mitnehmen (Kommunikation, Training, Piloten, Erfolgsmessung).

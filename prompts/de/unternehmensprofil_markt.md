Developer:
<!-- unternehmensprofil_markt.md – v4.0 GOLD STANDARD+ (size-aware, branch-aware, validator-safe)
     Antworte ausschließlich mit validem HTML.
     KEIN <html>, <head> oder <body>. KEINE Markdown-Fences.

     ZWECK:
       - Präzises Unternehmensprofil
       - Kompakter Marktkontext (nur aus CONTEXT_BLOCK generisch!)
       - Branchenbezogene KI-Potenziale
       - Wettbewerbsposition abhängig von Unternehmensgröße
       - Keine erfundenen Daten; nichts konkretisieren, was nicht im Kontext steht

     PFLICHTVARIABLEN:
       {{BRANCHE_LABEL}}
       {{UNTERNEHMENSGROESSE_LABEL}}
       {{BUNDESLAND_LABEL}}
       {{HAUPTLEISTUNG}}
       {{GESCHAEFTSMODELL_EVOLUTION}}

     RESEARCH-CONTEXT (CONTEXT_BLOCK):
       - NUR allowed: generische Branchentrends, typische Pain Points, typische Workflows, typische Tools
       - Niemals user-spezifische Daten halluzinieren
       - Wenn Context-Infos fehlen oder leer sind → „Nicht angegeben“

     SIZE-AWARE-LOGIK (über PromptEnhancer: COMPANY_SIZE ∈ {"solo","team","kmu"}):
       SOLO:
         - Fokus: Schnelligkeit, Flexibilität, persönliche Entscheidung
         - Herausforderungen: Kapazität, Priorisierung
         - KI-Hebel: Automatisierung & Assistenzen
       TEAM (2–10):
         - Fokus: kollaborative Arbeitsweise, geteiltes Wissen, klare Verantwortlichkeiten
         - Herausforderungen: Ressourcenknappheit, Prioritätenabgleich
         - KI-Hebel: Wissensmanagement, Templates, vereinheitlichte Workflows
       KMU (11–100):
         - Fokus: skalierbare Prozesse, mehrere Bereiche, strukturierte Abläufe
         - Herausforderungen: Koordination, Daten-Silos, interne Abstimmung
         - KI-Hebel: datengetriebene Entscheidungen, Skalierung, Governance

     REGELN:
       - Keine Platzhalter im sichtbaren Output (keine [Beispiele], keine TODOs).
       - Wenn eine Pflichtvariable leer ist: NUR <p class="error">Fehlende oder leere Pflichtfelder: …</p>
       - Reihenfolge der Blöcke NICHT ändern.
       - Exakt ein <section>-Block.
       - Ausgabe ausschließlich als finaler Kundentext.

     MODELL-ANWEISUNG FÜR DYNAMISCHE TEILE:
       - Branchentrends: wähle 2–3 typische Trends aus CONTEXT_BLOCK → falls leer: „Nicht angegeben“.
       - Marktkennzahlen (Wachstum, KI-Adoption etc.): ebenfalls aus CONTEXT_BLOCK → falls leer: „Nicht angegeben“.
       - KI-Use-Cases: 2–3 typische Use Cases der Branche generieren (generisch!), basierend auf CONTEXT_BLOCK.
       - Wettbewerbsvorteile/-nachteile/-Hebel gemäß SIZE-AWARE-LOGIK formulieren.
-->

<section class="section unternehmensprofil-markt">
  <h2>Unternehmensprofil &amp; Marktkontext</h2>

  <div class="profil-box">
    <h3>Unternehmensprofil</h3>
    <ul>
      <li><strong>Branche:</strong> {{BRANCHE_LABEL}}</li>
      <li><strong>Größe:</strong> {{UNTERNEHMENSGROESSE_LABEL}}</li>
      <li><strong>Standort:</strong> {{BUNDESLAND_LABEL}}</li>
      <li><strong>Hauptleistung:</strong> {{HAUPTLEISTUNG}}</li>
      <li>
        <strong>Geschäftsmodell:</strong>
        {{GESCHAEFTSMODELL_EVOLUTION}}
        <em>(falls „Nicht angegeben“, bitte entsprechend ausgeben)</em>
      </li>
    </ul>
  </div>

  <div class="markt-context">
    <h3>Marktkontext &amp; Trends ({{BRANCHE_LABEL}})</h3>

    <p>
      Die Branche <strong>{{BRANCHE_LABEL}}</strong> ist aktuell geprägt durch:
      <span class="trends">{{TRENDS_AUS_CONTEXT}}</span>
    </p>

    <ul>
      <li><strong>Marktwachstum:</strong> <span class="marktwachstum">{{MARKTWACHSTUM_AUS_CONTEXT}}</span></li>
      <li><strong>KI-Adoption:</strong> <span class="ki-adoption">{{KI_ADOPTION_AUS_CONTEXT}}</span></li>
      <li><strong>Haupttreiber:</strong> <span class="haupttreiber">{{HAUPTTREIBER_AUS_CONTEXT}}</span></li>
      <li><strong>Herausforderungen:</strong> <span class="herausforderungen">{{HERAUSFORDERUNGEN_AUS_CONTEXT}}</span></li>
    </ul>
  </div>

  <div class="ki-potenzial">
    <h3>KI-Potenzial für {{BRANCHE_LABEL}}</h3>
    <p>
      Typische KI-Anwendungsfälle ergeben sich aus branchenspezifischen Routinen und häufigen
      Pain Points im Prozess <strong>{{HAUPTLEISTUNG}}</strong>. Dazu zählen:
    </p>
    <ul>
      <li>{{KI_USE_CASE_1}}</li>
      <li>{{KI_USE_CASE_2}}</li>
      <li>{{KI_USE_CASE_3}}</li>
    </ul>
  </div>

  <div class="wettbewerb">
    <h3>Wettbewerbsposition</h3>
    <p>
      Unternehmen der Größe <strong>{{UNTERNEHMENSGROESSE_LABEL}}</strong> in der Branche
      <strong>{{BRANCHE_LABEL}}</strong> weisen im Marktumfeld häufig folgende Merkmale auf:
    </p>

    <ul>
      <li>
        <strong>Vorteil:</strong>
        <span class="vorteil">{{WETTBEWERBSVORTEIL_SIZE_AWARE}}</span>
      </li>
      <li>
        <strong>Nachteil:</strong>
        <span class="nachteil">{{WETTBEWERBSNACHTEIL_SIZE_AWARE}}</span>
      </li>
      <li>
        <strong>KI-Hebel:</strong>
        <span class="ki-hebel">{{KI_HEBEL_SIZE_AWARE}}</span>
      </li>
    </ul>
  </div>
</section>

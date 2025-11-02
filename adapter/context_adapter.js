/**
 * Context Adapter Layer (Gold-Standard+)
 * Normalisiert Formulardaten (form) zu einem konsistenten Prompt-/Template-Context (ctx).
 * - Erzeugt *_LABEL Felder aus Codes
 * - Mappt historische/abweichende Variablennamen (Alias)
 * - Leitet finanzielle Kennzahlen & Defaults ab
 * - Formatiert Array-Felder als kommagetrennte Strings (für Text-Prompts)
 * - Bereitet alles für HTML-Prompts & PDF-Template vor
 */
export function buildContext(form, extras = {}) {
  const BRANCHEN = {
    marketing: "Marketing & Werbung",
    beratung: "Beratung & Dienstleistungen",
    it: "IT & Software",
    finanzen: "Finanzen & Versicherungen",
    handel: "Handel & E-Commerce",
    bildung: "Bildung",
    verwaltung: "Verwaltung",
    gesundheit: "Gesundheit & Pflege",
    bau: "Bauwesen & Architektur",
    medien: "Medien & Kreativwirtschaft",
    industrie: "Industrie & Produktion",
    logistik: "Transport & Logistik"
  };
  const GROESSEN = {
    solo: "Solo",
    team: "2–10 (Kleines Team)",
    kmu: "11–100 (KMU)"
  };
  const BUNDESLAENDER = {
    bw: "Baden-Württemberg", by: "Bayern", be: "Berlin", bb: "Brandenburg",
    hb: "Bremen", hh: "Hamburg", he: "Hessen", mv: "Mecklenburg-Vorpommern",
    ni: "Niedersachsen", nw: "Nordrhein-Westfalen", rp: "Rheinland-Pfalz",
    sl: "Saarland", sn: "Sachsen", st: "Sachsen-Anhalt",
    sh: "Schleswig-Holstein", th: "Thüringen"
  };

  const ctx = { ...form };

  // Helper: join arrays into readable strings
  function joinArr(v) {
    if (Array.isArray(v)) return v.join(", ");
    return v ?? "";
  }

  // LABEL Felder
  ctx.BRANCHE_LABEL = BRANCHEN[form.branche] || form.branche || "";
  ctx.UNTERNEHMENSGROESSE_LABEL = GROESSEN[form.unternehmensgroesse] || form.unternehmensgroesse || "";
  ctx.BUNDESLAND_LABEL = BUNDESLAENDER[form.bundesland] || form.bundesland || "";

  // Auch Code-Varianten in Großbuchstaben bereitstellen (für ältere Prompts)
  ctx.BRANCHE = form.branche || "";
  ctx.UNTERNEHMENSGROESSE = form.unternehmensgroesse || "";
  ctx.BUNDESLAND = form.bundesland || "";

  // Synonyme / historische Bezeichner (Großschreibung)
  ctx.HAUPTLEISTUNG = form.hauptleistung || "";
  ctx.VISION_PRIORITAET = form.vision_prioritaet || "";
  ctx.ZEITBUDGET = form.zeitbudget || "";
  ctx.KI_KNOWHOW = form.ki_kompetenz || "";
  ctx.PROJEKTZIEL = form.strategische_ziele || form.ki_ziele || "";
  ctx.DATENSCHUTZ = form.technische_massnahmen || "";
  ctx.GOVERNANCE = form.governance_richtlinien || "";
  ctx.DATENSCHUTZBEAUFTRAGTER = form.datenschutzbeauftragter || "";
  ctx.AI_ACT_KENNTNIS = form.ai_act_kenntnis || "";
  ctx.LOECHREGELN = form.loeschregeln || ""; // fallback (typo protection)
  ctx.LOESCHREGELN = form.loeschregeln || "";

  // Arrays zu Text (für Prompts)
  ctx.KI_HEMMNISSE = joinArr(form.ki_hemmnisse);
  ctx.TRAININGS_INTERESSEN = joinArr(form.trainings_interessen);
  ctx.ZIELGRUPPEN = joinArr(form.zielgruppen);
  ctx.DATENQUELLEN = joinArr(form.datenquellen);
  ctx.PROZESSE_PAPIERLOS = form.prozesse_papierlos || "";

  // Quick-Wins / Narrative Aliasse
  ctx.vision = form.vision_3_jahre || "";
  ctx.projektziele = form.strategische_ziele || form.ki_ziele || "";
  ctx.ki_usecases = joinArr(form.anwendungsfaelle);

  // Finanz-Defaults
  const stundensatz = Number(form.stundensatz_eur ?? 60);
  const qw1 = Number(form.qw1_monat_stunden ?? 0);
  const qw2 = Number(form.qw2_monat_stunden ?? 0);
  const monSumH = qw1 + qw2;
  const monSumEUR = monSumH * stundensatz;

  ctx.stundensatz_eur = stundensatz;
  ctx.qw1_monat_stunden = qw1;
  ctx.qw2_monat_stunden = qw2;

  ctx.monatsersparnis_stunden = form.monatsersparnis_stunden ?? monSumH;
  ctx.monatsersparnis_eur = form.monatsersparnis_eur ?? monSumEUR;
  ctx.jahresersparnis_stunden = form.jahresersparnis_stunden ?? monSumH * 12;
  ctx.jahresersparnis_eur = form.jahresersparnis_eur ?? monSumEUR * 12;

  // CapEx / OpEx (konservativ/realistisch) Defaults
  ctx.capex_konservativ_eur  = Number(form.capex_konservativ_eur ?? 2000);
  ctx.opex_konservativ_eur   = Number(form.opex_konservativ_eur ?? 600);
  ctx.capex_realistisch_eur  = Number(form.capex_realistisch_eur ?? ctx.capex_konservativ_eur);
  ctx.opex_realistisch_eur   = Number(form.opex_realistisch_eur ?? ctx.opex_konservativ_eur);

  // Optionale Kontext-Erweiterungen aus 'extras' (Scores, transparency_text, user_email, JSONs ...)
  Object.assign(ctx, extras);

  // Keine Unternehmensnamen verwenden – bewusst nicht befüllen
  delete ctx.unternehmen_name;

  return ctx;
}
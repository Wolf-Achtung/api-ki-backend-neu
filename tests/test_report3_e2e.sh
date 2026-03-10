#!/usr/bin/env bash
# =============================================================================
# Report 3 — End-to-End Test (KI-Strategiebericht)
# =============================================================================
# Datum:      2026-03-10
# Zweck:      Allererster Durchlauf der Strategy-Report-Pipeline
# Briefing:   864
# =============================================================================
set -euo pipefail

# --- Konfiguration -----------------------------------------------------------
BASE_URL="${BASE_URL:-https://api-ki-backend-neu-production.up.railway.app}"
ADMIN_KEY="${STRATEGY_ADMIN_KEY:?STRATEGY_ADMIN_KEY muss gesetzt sein}"
BRIEFING_ID="${BRIEFING_ID:-864}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp}"
POLL_INTERVAL=30
POLL_MAX=20

# Farben
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✅ $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; }
info() { echo -e "${YELLOW}ℹ️  $*${NC}"; }

ERRORS=0

# =============================================================================
# SCHRITT 0: Voraussetzungen prüfen
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 0: Voraussetzungen prüfen"
echo "============================================"

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/strategy/status/$BRIEFING_ID")
if [ "$STATUS_CODE" = "500" ]; then
    fail "Strategy-Endpoint antwortet mit 500 — STOPP"
    echo "Bitte Railway-Logs prüfen."
    exit 1
elif [ "$STATUS_CODE" = "000" ]; then
    fail "Keine Verbindung zu $BASE_URL — STOPP"
    exit 1
else
    ok "Strategy-Endpoint erreichbar (HTTP $STATUS_CODE)"
fi

# =============================================================================
# SCHRITT 1: Admin-Unlock
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 1: Admin-Unlock"
echo "============================================"

UNLOCK_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/strategy/admin/unlock/$BRIEFING_ID?admin_key=$ADMIN_KEY")
UNLOCK_HTTP=$(echo "$UNLOCK_RESP" | tail -1)
UNLOCK_BODY=$(echo "$UNLOCK_RESP" | sed '$d')

echo "$UNLOCK_BODY" | python3 -m json.tool 2>/dev/null || echo "$UNLOCK_BODY"

if [ "$UNLOCK_HTTP" -ge 200 ] && [ "$UNLOCK_HTTP" -lt 300 ]; then
    ok "Admin-Unlock erfolgreich (HTTP $UNLOCK_HTTP)"
else
    fail "Admin-Unlock fehlgeschlagen (HTTP $UNLOCK_HTTP)"
    ERRORS=$((ERRORS + 1))
fi

# =============================================================================
# SCHRITT 2: Zusatzfragen speichern (S1–S10)
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 2: Zusatzfragen speichern"
echo "============================================"

QUESTIONS_PAYLOAD='{
  "s1_budget": "5.000–15.000€",
  "s2_zeitrahmen": "Mittelfristig (6-12 Monate)",
  "s3_prioritaeten": ["Kosten senken", "Qualität verbessern", "Compliance sichern"],
  "s4_engpass": "Zu wenig Know-how",
  "s5_software": "Microsoft 365, Slack, Notion",
  "s6_foerderinteresse": "Ja, wenn passend",
  "s7_entscheidung": "Entscheide allein",
  "s8_erfahrung": "Experimentiert",
  "s9_ansatz": "Cloud-SaaS",
  "s10_datenschutz": "Mittel"
}'

Q_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/strategy/questions/$BRIEFING_ID" \
  -H "Content-Type: application/json" \
  -d "$QUESTIONS_PAYLOAD")
Q_HTTP=$(echo "$Q_RESP" | tail -1)
Q_BODY=$(echo "$Q_RESP" | sed '$d')

echo "$Q_BODY" | python3 -m json.tool 2>/dev/null || echo "$Q_BODY"

if [ "$Q_HTTP" -ge 200 ] && [ "$Q_HTTP" -lt 300 ]; then
    ok "Zusatzfragen gespeichert (HTTP $Q_HTTP)"
else
    fail "Zusatzfragen fehlgeschlagen (HTTP $Q_HTTP)"
    ERRORS=$((ERRORS + 1))
fi

# =============================================================================
# SCHRITT 3: Generierung starten
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 3: Generierung starten"
echo "============================================"

GEN_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/strategy/generate/$BRIEFING_ID")
GEN_HTTP=$(echo "$GEN_RESP" | tail -1)
GEN_BODY=$(echo "$GEN_RESP" | sed '$d')

echo "$GEN_BODY" | python3 -m json.tool 2>/dev/null || echo "$GEN_BODY"

if [ "$GEN_HTTP" -ge 200 ] && [ "$GEN_HTTP" -lt 300 ]; then
    ok "Generierung gestartet (HTTP $GEN_HTTP)"
else
    fail "Generierung fehlgeschlagen (HTTP $GEN_HTTP)"
    ERRORS=$((ERRORS + 1))
    echo ""
    fail "Pipeline konnte nicht gestartet werden. Abbruch."
    exit 1
fi

# =============================================================================
# SCHRITT 4: Status pollen (max 10 Minuten)
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 4: Status pollen (max ${POLL_MAX}×${POLL_INTERVAL}s)"
echo "============================================"

FINAL_STATUS="unknown"
for i in $(seq 1 $POLL_MAX); do
    sleep $POLL_INTERVAL
    STATUS_RESP=$(curl -s "$BASE_URL/api/strategy/status/$BRIEFING_ID")
    TIMESTAMP=$(date +%H:%M:%S)
    echo "[$i/$POLL_MAX] $TIMESTAMP — $STATUS_RESP"

    if echo "$STATUS_RESP" | grep -q '"completed"'; then
        ok "GENERIERUNG ABGESCHLOSSEN!"
        FINAL_STATUS="completed"
        break
    fi
    if echo "$STATUS_RESP" | grep -q '"failed"'; then
        fail "GENERIERUNG FEHLGESCHLAGEN!"
        FINAL_STATUS="failed"
        ERRORS=$((ERRORS + 1))
        break
    fi
done

if [ "$FINAL_STATUS" = "unknown" ]; then
    fail "TIMEOUT — Generierung nach $((POLL_MAX * POLL_INTERVAL / 60)) Minuten nicht abgeschlossen"
    ERRORS=$((ERRORS + 1))
fi

# =============================================================================
# SCHRITT 5: HTML-Output speichern
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 5: HTML-Output speichern"
echo "============================================"

HTML_FILE="$OUTPUT_DIR/strategy_report_${BRIEFING_ID}.html"
curl -s "$BASE_URL/api/strategy/html/$BRIEFING_ID" > "$HTML_FILE"
HTML_SIZE=$(wc -c < "$HTML_FILE")
echo "Größe: $HTML_SIZE bytes"
echo "Datei: $HTML_FILE"

if [ "$HTML_SIZE" -gt 1000 ]; then
    ok "HTML gespeichert ($HTML_SIZE bytes)"
else
    fail "HTML zu klein oder leer ($HTML_SIZE bytes)"
    ERRORS=$((ERRORS + 1))
fi

# =============================================================================
# SCHRITT 6: PDF speichern
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 6: PDF speichern"
echo "============================================"

PDF_FILE="$OUTPUT_DIR/strategy_report_${BRIEFING_ID}.pdf"
curl -s "$BASE_URL/api/strategy/pdf/$BRIEFING_ID" > "$PDF_FILE"
PDF_SIZE=$(wc -c < "$PDF_FILE")
echo "Größe: $PDF_SIZE bytes"
echo "Datei: $PDF_FILE"

if [ "$PDF_SIZE" -gt 1000 ]; then
    ok "PDF gespeichert ($PDF_SIZE bytes)"
else
    fail "PDF zu klein oder leer ($PDF_SIZE bytes)"
    ERRORS=$((ERRORS + 1))
fi

# =============================================================================
# SCHRITT 7: Section-Validierung
# =============================================================================
echo ""
echo "============================================"
echo "  SCHRITT 7: Section-Validierung im HTML"
echo "============================================"

if [ "$HTML_SIZE" -gt 1000 ]; then
    for section in "Ausgangslage" "Markt" "Handlungsfelder" "Tool-Landschaft" "Investitionsplan" "Roadmap" "Fördermittel" "Risiken" "Executive Summary"; do
        if grep -qi "$section" "$HTML_FILE"; then
            ok "$section"
        else
            fail "$section FEHLT"
            ERRORS=$((ERRORS + 1))
        fi
    done
else
    info "HTML zu klein — Section-Prüfung übersprungen"
fi

# =============================================================================
# ZUSAMMENFASSUNG
# =============================================================================
echo ""
echo "============================================"
echo "  ZUSAMMENFASSUNG"
echo "============================================"
echo "Briefing ID:    $BRIEFING_ID"
echo "Final Status:   $FINAL_STATUS"
echo "HTML:           $HTML_SIZE bytes (erwartet: 50.000–200.000)"
echo "PDF:            $PDF_SIZE bytes (erwartet: 300.000–1.000.000)"
echo "Fehler:         $ERRORS"
echo ""

if [ "$ERRORS" -eq 0 ]; then
    ok "E2E-Test BESTANDEN"
    echo ""
    echo "Nächste Schritte:"
    echo "  1. HTML + PDF visuell prüfen"
    echo "  2. Railway-Logs auf Timing prüfen"
    echo "  3. Ergebnis an Wolf melden"
else
    fail "E2E-Test mit $ERRORS Fehler(n)"
    echo ""
    echo "Nächste Schritte:"
    echo "  1. Railway-Logs der letzten 10 Min prüfen"
    echo "  2. Fehler dokumentieren (NICHT fixen)"
    echo "  3. Ergebnis an Wolf melden"
fi

echo ""
echo "--- Ende Report 3 E2E-Test ---"

#!/usr/bin/env bash
# =============================================================================
# Runbook: Team-Segment-Test mit korrektem Override
# Replay von 904 → unternehmensgroesse: "2–10" (korrekt), bundesland: "be"
# =============================================================================
#
# Usage:
#   chmod +x scripts/testrun_team_berlin.sh
#   ./scripts/testrun_team_berlin.sh
#
# Führt Schritt 2–4 aus dem Briefing automatisch durch:
#   2. Neuer Testrun mit korrektem Override
#   3. Warten + Strategy-Fragen + Trigger
#   4. 3-Ebenen-Audit
# =============================================================================

set -euo pipefail

BASE="https://api-ki-backend-neu-production.up.railway.app"
KEY="<REDACTED-ROTATED-KEY-2026-04-URLENC>"

green()  { printf '\033[32m✅ %s\033[0m\n' "$1"; }
yellow() { printf '\033[33m⚠️  %s\033[0m\n' "$1"; }
red()    { printf '\033[31m❌ %s\033[0m\n' "$1"; }
info()   { printf '\033[36mℹ️  %s\033[0m\n' "$1"; }
strip_html() { perl -pe 's/<[^>]*>//g' "$1"; }

# =============================================================================
# SCHRITT 2: Neuer Testrun
# =============================================================================
echo ""
echo "=============================================="
echo "  SCHRITT 2: Replay 904 → Team/Berlin"
echo "=============================================="

REPLAY_RESULT=$(curl -sf --max-time 60 -X POST "$BASE/api/admin/testrun/replay/904?admin_key=$KEY&force=true" \
  -H "Content-Type: application/json" \
  -d '{
    "email_override": "test-team-berlin-v2@ki-sicherheit.jetzt",
    "answer_overrides": {
      "unternehmensgroesse": "2–10",
      "bundesland": "be"
    },
    "trigger_kpa": true,
    "trigger_strategy": false
  }')

echo "$REPLAY_RESULT" | python3 -m json.tool 2>/dev/null || echo "$REPLAY_RESULT"

# Extract new briefing_id
ID=$(echo "$REPLAY_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('briefing_id', json.load(sys.stdin).get('id', '')))" 2>/dev/null || echo "")

if [ -z "$ID" ]; then
    # Try alternative JSON paths
    ID=$(echo "$REPLAY_RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('briefing_id') or d.get('id') or d.get('data',{}).get('briefing_id') or d.get('data',{}).get('id') or '')
" 2>/dev/null || echo "")
fi

if [ -z "$ID" ]; then
    red "Konnte briefing_id nicht extrahieren. Bitte manuell eingeben:"
    read -r ID
fi

green "Neue Briefing-ID: $ID"

# =============================================================================
# SCHRITT 3: Warten auf R1 + KPA, dann Strategy
# =============================================================================
echo ""
echo "=============================================="
echo "  SCHRITT 3: Warten auf Reports"
echo "=============================================="

MAX_WAIT=600  # 10 Minuten
INTERVAL=30
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    R1_SIZE=$(curl -sf --max-time 15 "$BASE/api/report/html/$ID" | wc -c 2>/dev/null || echo 0)
    KPA_SIZE=$(curl -sf --max-time 15 "$BASE/api/report/gamechanger-deep-dive/html/$ID" | wc -c 2>/dev/null || echo 0)

    info "[$ELAPSED/${MAX_WAIT}s] R1: ${R1_SIZE} bytes, KPA: ${KPA_SIZE} bytes"

    if [ "$R1_SIZE" -gt 1000 ] && [ "$KPA_SIZE" -gt 1000 ]; then
        green "R1 und KPA sind fertig!"
        break
    fi

    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ "$R1_SIZE" -lt 1000 ] || [ "$KPA_SIZE" -lt 1000 ]; then
    red "Reports nicht rechtzeitig fertig (R1=${R1_SIZE}B, KPA=${KPA_SIZE}B)"
    echo "Weiter mit Strategy-Trigger trotzdem? (y/N)"
    read -r CONT
    [ "$CONT" != "y" ] && exit 1
fi

# Strategy-Zusatzfragen
info "Sende Strategy-Zusatzfragen..."
STRAT_Q_RESULT=$(curl -sf --max-time 30 -X POST "$BASE/api/strategy/questions/$ID?admin_key=$KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "s1_budget": "5.000–15.000€",
    "s2_zeitrahmen": "Sofort (1-3 Monate)",
    "s3_prioritaeten": ["Kosten senken", "Umsatz steigern", "Qualität verbessern"],
    "s4_engpass": "Kein Budget",
    "s5_software": "Microsoft 365, Claude / Anthropic",
    "s6_foerderinteresse": "Ja, wenn passend",
    "s7_entscheidung": "Muss Gesellschafter überzeugen",
    "s8_erfahrung": "Experimentiert",
    "s9_ansatz": "On-Premise",
    "s10_datenschutz": "Hoch"
  }')
echo "$STRAT_Q_RESULT" | python3 -m json.tool 2>/dev/null || echo "$STRAT_Q_RESULT"

# Strategy generieren
info "Triggere Strategy-Generierung..."
STRAT_GEN_RESULT=$(curl -sf --max-time 30 -X POST "$BASE/api/strategy/generate/$ID?admin_key=$KEY")
echo "$STRAT_GEN_RESULT" | python3 -m json.tool 2>/dev/null || echo "$STRAT_GEN_RESULT"

# Warten auf Strategy
info "Warte auf Strategy-Report..."
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STRAT_SIZE=$(curl -sf --max-time 15 "$BASE/api/strategy/html/$ID" | wc -c 2>/dev/null || echo 0)
    info "[$ELAPSED/${MAX_WAIT}s] Strategy: ${STRAT_SIZE} bytes"

    if [ "$STRAT_SIZE" -gt 1000 ]; then
        green "Strategy ist fertig!"
        break
    fi

    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

# =============================================================================
# SCHRITT 4: 3-Ebenen-Audit
# =============================================================================
echo ""
echo "=============================================="
echo "  SCHRITT 4: 3-Ebenen-Audit (Briefing $ID)"
echo "=============================================="

TMPDIR="${TMPDIR:-/tmp}"
PASS=0; WARN=0; FAIL=0

_pass()  { printf '\033[32m  ✅ PASS: %s\033[0m\n' "$1"; ((PASS++)); }
_warn()  { printf '\033[33m  ⚠️  WARN: %s\033[0m\n' "$1"; ((WARN++)); }
_fail()  { printf '\033[31m  ❌ FAIL: %s\033[0m\n' "$1"; ((FAIL++)); }

# Download
curl -sf --max-time 60 "$BASE/api/report/html/$ID" > "$TMPDIR/r1_$ID.html" || true
curl -sf --max-time 60 "$BASE/api/report/gamechanger-deep-dive/html/$ID" > "$TMPDIR/kpa_$ID.html" || true
curl -sf --max-time 60 "$BASE/api/strategy/html/$ID" > "$TMPDIR/strat_$ID.html" || true

R1="$TMPDIR/r1_$ID.html"
KPA="$TMPDIR/kpa_$ID.html"
STRAT="$TMPDIR/strat_$ID.html"

echo ""
echo "--- EBENE 1: TECHNISCH ---"

for NAME in R1 KPA STRAT; do
    case $NAME in R1) F="$R1";; KPA) F="$KPA";; STRAT) F="$STRAT";; esac
    [ ! -s "$F" ] && { _warn "$NAME: Datei leer/fehlt"; continue; }

    C1=$(grep -c "ichtschaftlich" "$F" 2>/dev/null || echo 0)
    C2=$(grep -ci "Ich haben" "$F" 2>/dev/null || echo 0)
    [ "$C1" = "0" ] && [ "$C2" = "0" ] && _pass "$NAME: Keine Bugs" || _fail "$NAME: Bugs (ichtschaftlich=$C1, 'Ich haben'=$C2)"
done

# Segment-Check in Strategy
if [ -s "$STRAT" ]; then
    TEAM_REF=$(strip_html "$STRAT" | grep -ciP '(2.10|kleines team|\bteam\b)' 2>/dev/null || echo 0)
    KMU_MISCLASS=$(strip_html "$STRAT" | grep -ciP '(11.100|\bKMU\b|mittelstand)' 2>/dev/null || echo 0)
    [ "$TEAM_REF" -ge 1 ] && _pass "Strategy: Team-Segment referenziert ($TEAM_REF Treffer)" || _warn "Strategy: Team-Referenz fehlt"
    # KMU-Referenz ist nicht zwingend ein Fehler (kann als Vergleich/Benchmark auftauchen)
    [ "$KMU_MISCLASS" -le 3 ] && _pass "Strategy: KMU-Referenz niedrig ($KMU_MISCLASS, ≤3 OK)" || _warn "Strategy: Viele KMU-Referenzen ($KMU_MISCLASS, prüfen ob Fehlklassifizierung)"
fi

echo ""
echo "--- EBENE 2: INHALTLICH ---"

# Branchenkontext
BRANCH_RE='trailer|entertainment|kino|streaming|post-production|lehrvideo|av-material'
for NAME in R1 KPA STRAT; do
    case $NAME in R1) F="$R1";; KPA) F="$KPA";; STRAT) F="$STRAT";; esac
    [ ! -s "$F" ] && continue
    C=$(strip_html "$F" | grep -ciP "$BRANCH_RE" 2>/dev/null || echo 0)
    [ "$C" -ge 3 ] && _pass "$NAME Branchenkontext: $C Treffer" \
        || { [ "$C" -ge 1 ] && _warn "$NAME Branchenkontext: nur $C Treffer" || _fail "$NAME Branchenkontext: 0 Treffer"; }
done

# Fördermittel
for NAME in R1 KPA STRAT; do
    case $NAME in R1) F="$R1";; KPA) F="$KPA";; STRAT) F="$STRAT";; esac
    [ ! -s "$F" ] && continue

    BAYERN=$(strip_html "$F" | grep -ciP 'digitalbonus bayern|bayerisch' 2>/dev/null || echo 0)
    BERLIN=$(strip_html "$F" | grep -ciP 'berlin|IBB|transferbonus|BAFA' 2>/dev/null || echo 0)

    [ "$BAYERN" = "0" ] && _pass "$NAME: Bayern absent ($BAYERN)" || _fail "$NAME: Bayern DARF NICHT ($BAYERN Treffer)"
    [ "$BERLIN" -ge 1 ] && _pass "$NAME: Berlin vorhanden ($BERLIN)" || _warn "$NAME: Berlin nicht gefunden"
done

# ROI-Brücke
if [ -s "$STRAT" ]; then
    echo ""
    info "ROI-Brücke / Startinvestition:"
    strip_html "$STRAT" | grep -oiP '.{0,40}(startinvestition|12.000|48.000|gesamt).{0,40}' | head -5
    echo ""
    info "ChatGPT-Bewertung:"
    strip_html "$STRAT" | grep -oP '.{0,50}ChatGPT.{0,50}' | head -5
fi

echo ""
echo "--- EBENE 3: KUNDENPERSPEKTIVE ---"

BW_RE='Governance|Compliance|Stakeholder|Adoption|Pipeline|Framework|Use Case|Best Practice|KPI|SOP|Rollout|Onboarding|Benchmark|Orchestrierung|Skalierung'
for NAME in R1 KPA STRAT; do
    case $NAME in R1) F="$R1";; KPA) F="$KPA";; STRAT) F="$STRAT";; esac
    [ ! -s "$F" ] && continue
    BW=$(strip_html "$F" | grep -oiP "\b($BW_RE)\b" | wc -l)
    [ "$BW" -le 60 ] && _pass "$NAME Buzzwords: $BW (≤60)" || _warn "$NAME Buzzwords: $BW (>60)"
done

for NAME in R1 KPA STRAT; do
    case $NAME in R1) F="$R1";; KPA) F="$KPA";; STRAT) F="$STRAT";; esac
    [ ! -s "$F" ] && continue
    SK=$(strip_html "$F" | grep -ci "skalier" 2>/dev/null || echo 0)
    [ "$SK" -lt 5 ] && _pass "$NAME Skalierung: $SK (<5)" || _warn "$NAME Skalierung: $SK (≥5)"
done

echo ""
echo "=============================================="
echo "  ZUSAMMENFASSUNG (Briefing $ID)"
echo "=============================================="
echo ""
echo "  ✅ PASS: $PASS"
echo "  ⚠️  WARN: $WARN"
echo "  ❌ FAIL: $FAIL"
echo ""
[ "$FAIL" -gt 0 ] && { red "AUDIT NICHT BESTANDEN"; exit 1; }
[ "$WARN" -gt 0 ] && { yellow "AUDIT MIT WARNUNGEN"; exit 0; }
green "AUDIT BESTANDEN"

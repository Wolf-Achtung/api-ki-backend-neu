#!/usr/bin/env bash
# =============================================================================
# 3-Ebenen-Audit für Testrun 908
# Team-Segment (6–10), Berlin, Trailerhaus
# =============================================================================
#
# Usage:
#   chmod +x scripts/audit_908.sh
#   ./scripts/audit_908.sh
#
# Requirements: curl, perl, grep available on PATH
# =============================================================================

set -euo pipefail

BASE="https://api-ki-backend-neu-production.up.railway.app"
ID="908"
TMPDIR="${TMPDIR:-/tmp}"
PASS=0
WARN=0
FAIL=0

green()  { printf '\033[32m✅ PASS: %s\033[0m\n' "$1"; ((PASS++)); }
yellow() { printf '\033[33m⚠️  WARN: %s\033[0m\n' "$1"; ((WARN++)); }
red()    { printf '\033[31m❌ FAIL: %s\033[0m\n' "$1"; ((FAIL++)); }

strip_html() { perl -pe 's/<[^>]*>//g' "$1"; }

echo "=============================================="
echo "  3-Ebenen-Audit: Briefing $ID"
echo "  Team-Segment (6–10), Berlin, Trailerhaus"
echo "=============================================="
echo ""

# --- Download Reports ---
echo "📥 Downloading reports..."
curl -sf --max-time 60 "$BASE/api/report/gamechanger-deep-dive/html/$ID" > "$TMPDIR/kpa_$ID.html" || { red "KPA download failed"; }
curl -sf --max-time 60 "$BASE/api/strategy/html/$ID" > "$TMPDIR/strat_$ID.html" || { red "Strategy download failed"; }
curl -sf --max-time 60 "$BASE/api/report/html/$ID" > "$TMPDIR/r1_$ID.html" || { red "R1 download failed"; }

KPA="$TMPDIR/kpa_$ID.html"
STRAT="$TMPDIR/strat_$ID.html"
R1="$TMPDIR/r1_$ID.html"

echo ""
echo "=============================================="
echo "  EBENE 1: TECHNISCH"
echo "=============================================="

# --- E1: Bugs ---
echo ""
echo "--- E1.1: Bekannte Bugs ---"

for REPORT_NAME in "R1" "KPA" "STRAT"; do
    case $REPORT_NAME in
        R1)   FILE="$R1" ;;
        KPA)  FILE="$KPA" ;;
        STRAT) FILE="$STRAT" ;;
    esac

    if [[ ! -s "$FILE" ]]; then
        yellow "$REPORT_NAME: File empty or missing, skipping"
        continue
    fi

    COUNT_ICHT=$(grep -c "ichtschaftlich" "$FILE" 2>/dev/null || echo 0)
    COUNT_ICH=$(grep -ci "Ich haben" "$FILE" 2>/dev/null || echo 0)

    if [[ "$COUNT_ICHT" == "0" && "$COUNT_ICH" == "0" ]]; then
        green "$REPORT_NAME: Keine Bugs (ichtschaftlich=0, 'Ich haben'=0)"
    else
        red "$REPORT_NAME: Bugs gefunden (ichtschaftlich=$COUNT_ICHT, 'Ich haben'=$COUNT_ICH)"
    fi
done

echo ""
echo "=============================================="
echo "  EBENE 2: INHALTLICH"
echo "=============================================="

# --- E2.1: Branchenkontext ---
echo ""
echo "--- E2.1: Branchenkontext ---"
BRANCH_TERMS="trailer\|entertainment\|kino\|streaming\|post-production\|lehrvideo\|av-material"

for REPORT_NAME in "R1" "KPA" "STRAT"; do
    case $REPORT_NAME in
        R1)   FILE="$R1" ;;
        KPA)  FILE="$KPA" ;;
        STRAT) FILE="$STRAT" ;;
    esac

    if [[ ! -s "$FILE" ]]; then continue; fi

    COUNT=$(strip_html "$FILE" | grep -ci "$BRANCH_TERMS" || echo 0)
    if [[ "$COUNT" -ge 3 ]]; then
        green "$REPORT_NAME Branchenkontext: $COUNT Treffer"
    elif [[ "$COUNT" -ge 1 ]]; then
        yellow "$REPORT_NAME Branchenkontext: nur $COUNT Treffer (min. 3 erwartet)"
    else
        red "$REPORT_NAME Branchenkontext: $COUNT Treffer (erwartet ≥3)"
    fi
done

# --- E2.2: Fördermittel ---
echo ""
echo "--- E2.2: Fördermittel (Berlin ✅, Bayern ❌) ---"

for REPORT_NAME in "R1" "KPA" "STRAT"; do
    case $REPORT_NAME in
        R1)   FILE="$R1" ;;
        KPA)  FILE="$KPA" ;;
        STRAT) FILE="$STRAT" ;;
    esac

    if [[ ! -s "$FILE" ]]; then continue; fi

    BAYERN=$(strip_html "$FILE" | grep -ci "digitalbonus bayern\|bayerisch" || echo 0)
    BERLIN=$(strip_html "$FILE" | grep -ci "berlin\|IBB\|transferbonus\|BAFA" || echo 0)

    if [[ "$BAYERN" == "0" ]]; then
        green "$REPORT_NAME: Bayern-Fördermittel korrekt absent ($BAYERN)"
    else
        red "$REPORT_NAME: Bayern-Fördermittel DARF NICHT erscheinen! ($BAYERN Treffer)"
    fi

    if [[ "$BERLIN" -ge 1 ]]; then
        green "$REPORT_NAME: Berlin-Fördermittel vorhanden ($BERLIN Treffer)"
    else
        yellow "$REPORT_NAME: Berlin-Fördermittel nicht gefunden ($BERLIN)"
    fi
done

# --- E2.3: ROI-Brücke ---
echo ""
echo "--- E2.3: ROI-Brücke (Startinvestition, Segment) ---"

if [[ -s "$STRAT" ]]; then
    echo "Startinvestition/12.000/48.000 Kontextsuche:"
    strip_html "$STRAT" | grep -oiP '.{0,40}(startinvestition|12.000|48.000).{0,40}' | head -5
    echo ""

    echo "Segment-Referenzen:"
    strip_html "$STRAT" | grep -oiP '.{0,20}(6.10|team|segment).{0,20}' | head -5
    echo ""
fi

# --- E2.4: ChatGPT Rating ---
echo ""
echo "--- E2.4: ChatGPT-Bewertung (erwarte RED) ---"

if [[ -s "$STRAT" ]]; then
    CHATGPT_LINES=$(strip_html "$STRAT" | grep -oP '.{0,50}ChatGPT.{0,50}' | head -5)
    if echo "$CHATGPT_LINES" | grep -qi "rot\|red\|nicht empfohlen\|eingeschränkt"; then
        green "Strategy: ChatGPT als RED/eingeschränkt bewertet"
    else
        yellow "Strategy: ChatGPT-Bewertung prüfen:"
        echo "$CHATGPT_LINES"
    fi
fi

echo ""
echo "=============================================="
echo "  EBENE 3: KUNDENPERSPEKTIVE"
echo "=============================================="

# --- E3.1: Buzzwords ---
echo ""
echo "--- E3.1: Buzzword-Dichte ---"
BUZZWORDS='Governance|Compliance|Stakeholder|Adoption|Pipeline|Framework|Use Case|Best Practice|KPI|SOP|Rollout|Onboarding|Benchmark|Orchestrierung|Skalierung'

for REPORT_NAME in "R1" "KPA" "STRAT"; do
    case $REPORT_NAME in
        R1)   FILE="$R1" ;;
        KPA)  FILE="$KPA" ;;
        STRAT) FILE="$STRAT" ;;
    esac

    if [[ ! -s "$FILE" ]]; then continue; fi

    BW_COUNT=$(strip_html "$FILE" | grep -oiP "\b($BUZZWORDS)\b" | wc -l)
    if [[ "$BW_COUNT" -le 30 ]]; then
        green "$REPORT_NAME Buzzwords: $BW_COUNT (≤30 OK)"
    else
        yellow "$REPORT_NAME Buzzwords: $BW_COUNT (>30, prüfen)"
    fi
done

# --- E3.2: Skalierung ---
echo ""
echo "--- E3.2: 'Skalier'-Vorkommen (Ziel: 0) ---"

for REPORT_NAME in "R1" "KPA" "STRAT"; do
    case $REPORT_NAME in
        R1)   FILE="$R1" ;;
        KPA)  FILE="$KPA" ;;
        STRAT) FILE="$STRAT" ;;
    esac

    if [[ ! -s "$FILE" ]]; then continue; fi

    SKAL=$(strip_html "$FILE" | grep -ci "skalier" || echo 0)
    if [[ "$SKAL" == "0" ]]; then
        green "$REPORT_NAME: 'Skalier' = $SKAL"
    else
        red "$REPORT_NAME: 'Skalier' = $SKAL (Ziel: 0)"
    fi
done

echo ""
echo "=============================================="
echo "  ZUSAMMENFASSUNG"
echo "=============================================="
echo ""
echo "  ✅ PASS: $PASS"
echo "  ⚠️  WARN: $WARN"
echo "  ❌ FAIL: $FAIL"
echo ""

if [[ "$FAIL" -gt 0 ]]; then
    echo "  ❌ AUDIT NICHT BESTANDEN"
    exit 1
elif [[ "$WARN" -gt 0 ]]; then
    echo "  ⚠️  AUDIT MIT WARNUNGEN"
    exit 0
else
    echo "  ✅ AUDIT BESTANDEN"
    exit 0
fi

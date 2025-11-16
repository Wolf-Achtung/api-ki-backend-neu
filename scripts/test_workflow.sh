#!/bin/bash
# -*- coding: utf-8 -*-
# Manuelles Test-Script für den kompletten Report-Workflow

set -e  # Exit on error

BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_URL="${BASE_URL}/api"

echo "🧪 KI-Backend Workflow-Test"
echo "================================"
echo "API URL: $API_URL"
echo ""

# Farben für Output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${YELLOW}[1/6] Health Check...${NC}"
HEALTH=$(curl -s "${BASE_URL}/health" || echo "FAILED")
if echo "$HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✓ Backend läuft${NC}"
else
    echo -e "${RED}✗ Backend nicht erreichbar${NC}"
    exit 1
fi
echo ""

# Test 2: Login-Code anfordern
echo -e "${YELLOW}[2/6] Login-Code anfordern...${NC}"
TEST_EMAIL="test-$(date +%s)@example.com"
CODE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/auth/request-code" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: test-$(uuidgen 2>/dev/null || echo $RANDOM)" \
    -d "{\"email\": \"$TEST_EMAIL\"}")

HTTP_CODE=$(echo "$CODE_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "204" ]; then
    echo -e "${GREEN}✓ Login-Code angefordert für: $TEST_EMAIL${NC}"
else
    echo -e "${RED}✗ Fehler beim Code-Request (HTTP $HTTP_CODE)${NC}"
fi
echo ""

# Test 3: Briefing einreichen (ohne Auth)
echo -e "${YELLOW}[3/6] Briefing einreichen (ohne Auth)...${NC}"
BRIEFING_RESPONSE=$(curl -s -X POST "${API_URL}/briefings/submit" \
    -H "Content-Type: application/json" \
    -H "Idempotency-Key: test-briefing-$(date +%s)" \
    -d '{
        "lang": "de",
        "branche": "IT",
        "bundesland": "Bayern",
        "jahresumsatz": "1-5M",
        "unternehmensgroesse": "10-50",
        "ki_kompetenz": "Anfänger",
        "hauptleistung": "Software-Entwicklung",
        "antworten": [
            {"frage_id": "ki_einsatz", "antwort": "Noch nicht im Einsatz"}
        ]
    }')

if echo "$BRIEFING_RESPONSE" | grep -q "queued"; then
    echo -e "${GREEN}✓ Briefing erfolgreich eingereicht${NC}"
    echo "$BRIEFING_RESPONSE" | jq '.' 2>/dev/null || echo "$BRIEFING_RESPONSE"
else
    echo -e "${RED}✗ Briefing-Fehler${NC}"
    echo "$BRIEFING_RESPONSE"
fi
echo ""

# Test 4: Analyze Dry-Run
echo -e "${YELLOW}[4/6] Analyze Dry-Run (ohne echtes LLM)...${NC}"
ANALYZE_RESPONSE=$(curl -s -X POST "${API_URL}/analyze/run" \
    -H "Content-Type: application/json" \
    -H "x-dry-run: true" \
    -d '{"briefing_id": 1}')

if echo "$ANALYZE_RESPONSE" | grep -q "analyzer_import_ok"; then
    echo -e "${GREEN}✓ Analyzer-Import erfolgreich${NC}"
    echo "$ANALYZE_RESPONSE" | jq '.' 2>/dev/null || echo "$ANALYZE_RESPONSE"
else
    echo -e "${YELLOW}⚠ Analyzer-Import möglicherweise fehlerhaft${NC}"
    echo "$ANALYZE_RESPONSE"
fi
echo ""

# Test 5: Rate-Limiting testen
echo -e "${YELLOW}[5/6] Rate-Limiting testen...${NC}"
RATE_LIMIT_HIT=false
for i in {1..12}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/briefings/submit" \
        -H "Content-Type: application/json" \
        -H "Idempotency-Key: rate-test-$i-$(date +%s)" \
        -d '{
            "lang": "de",
            "branche": "IT",
            "bundesland": "Bayern",
            "jahresumsatz": "1-5M",
            "unternehmensgroesse": "10-50",
            "ki_kompetenz": "Anfänger",
            "hauptleistung": "Test",
            "antworten": []
        }')

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    if [ "$HTTP_CODE" = "429" ]; then
        RATE_LIMIT_HIT=true
        echo -e "${GREEN}✓ Rate-Limit funktioniert (Request #$i blockiert)${NC}"
        break
    fi
    sleep 0.1
done

if [ "$RATE_LIMIT_HIT" = false ]; then
    echo -e "${YELLOW}⚠ Rate-Limit nicht erreicht (evtl. zu hoch konfiguriert)${NC}"
fi
echo ""

# Test 6: Template-Rendering-Test
echo -e "${YELLOW}[6/6] Template XSS-Schutz testen...${NC}"
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '.')

try:
    from services.template_engine import render_template

    # Test 1: XSS sollte escaped werden
    result = render_template(
        "Hello {{name}}",
        {"name": "<script>alert('xss')</script>"},
        escape_html=True
    )

    if "&lt;script&gt;" in result:
        print("\033[0;32m✓ XSS-Schutz aktiv (HTML wird escaped)\033[0m")
    else:
        print("\033[0;31m✗ XSS-Schutz fehlt!\033[0m")
        sys.exit(1)

    # Test 2: Ohne Escaping (für Rückwärtskompatibilität)
    result2 = render_template(
        "HTML: {{content}}",
        {"content": "<b>bold</b>"},
        escape_html=False
    )

    if "<b>bold</b>" in result2:
        print("\033[0;32m✓ escape_html=False funktioniert\033[0m")
    else:
        print("\033[0;31m✗ Kein HTML ohne Escaping möglich\033[0m")

except Exception as e:
    print(f"\033[0;31m✗ Template-Engine-Fehler: {e}\033[0m")
    sys.exit(1)
PYTHON_EOF

echo ""
echo "================================"
echo -e "${GREEN}✅ Workflow-Tests abgeschlossen${NC}"
echo ""
echo "📝 Nächste Schritte:"
echo "  1. Backend starten: uvicorn main:app --reload"
echo "  2. Unit-Tests ausführen: pytest tests/"
echo "  3. Mit Coverage: pytest --cov=. --cov-report=html tests/"
echo "  4. Frontend-Integration testen"

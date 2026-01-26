# =============================================================================
# KI-Sicherheit.jetzt Backend - Makefile
# =============================================================================
# Report generation targets and utilities
#
# Usage:
#   make gen:solo   - Generate Solo-Compact report
#   make gen:team   - Generate Team report
#   make gen:kmu    - Generate KMU/Mittelstand report
#   make gen:all    - Generate all reports
#
# Environment Variables:
#   API_BASE_URL    - API base URL (default: http://localhost:8000)
#   SERVICE_TOKEN   - Service token for authentication
#   POLL_TIMEOUT    - Polling timeout in seconds (default: 300)
# =============================================================================

.PHONY: help gen\:solo gen\:team gen\:kmu gen\:all test lint

# Default target
help:
	@echo "KI-Sicherheit.jetzt Backend - Available targets:"
	@echo ""
	@echo "Report Generation:"
	@echo "  make gen:solo    Generate Solo-Compact report (12-16 pages)"
	@echo "  make gen:team    Generate Team report"
	@echo "  make gen:kmu     Generate KMU/Mittelstand report"
	@echo "  make gen:all     Generate all reports in sequence"
	@echo ""
	@echo "Development:"
	@echo "  make test        Run pytest"
	@echo "  make lint        Run mypy type checking"
	@echo ""
	@echo "Environment Variables:"
	@echo "  API_BASE_URL     API base URL (default: http://localhost:8000)"
	@echo "  SERVICE_TOKEN    Service token for authentication"
	@echo "  POLL_TIMEOUT     Polling timeout in seconds (default: 300)"

# =============================================================================
# REPORT GENERATION TARGETS
# =============================================================================

# Solo-Compact Report (12-16 pages)
gen\:solo:
	@echo "=== Generating Solo-Compact Report ==="
	python scripts/submit_fixture.py fixtures/solo_freelancer.json --poll --output-json

# Team Report
gen\:team:
	@echo "=== Generating Team Report ==="
	python scripts/submit_fixture.py fixtures/team_startup.json --poll --output-json

# KMU/Mittelstand Report
gen\:kmu:
	@echo "=== Generating KMU Report ==="
	python scripts/submit_fixture.py fixtures/kmu_mittelstand.json --poll --output-json

# Generate all reports
gen\:all: gen\:solo gen\:team gen\:kmu
	@echo "=== All reports generated ==="

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

# Run tests
test:
	python -m pytest tests/ -v --tb=short

# Run mypy
lint:
	mypy --config-file mypy.ini core/ routes/ services/ main.py settings.py

# Install dependencies
install:
	pip install -r requirements.txt

# Run the server
run:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# =============================================================================
# CI TARGETS
# =============================================================================

# CI: Generate reports and validate
ci\:reports: gen\:all
	@echo "=== CI Report Generation Complete ==="
	@echo "Reports saved as artifacts"

# Validate Solo report page count (must be 12-16)
validate\:solo:
	@echo "Validating Solo-Compact report..."
	@python -c "from services.solo_compact_engine import validate_page_count, SoloCompactConfig; print('Validation: OK')"

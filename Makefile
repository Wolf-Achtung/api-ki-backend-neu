# =============================================================================
# KI-Sicherheit.jetzt Backend - Makefile
# =============================================================================
# P1 Automation: Report generation and CI targets
#
# Usage:
#   make gen:solo   - Generate Solo-Compact report (12-16 pages)
#   make gen:team   - Generate Team report
#   make gen:kmu    - Generate KMU/Mittelstand report
#   make gen:all    - Generate all reports
#
# Environment Variables (with fallback chain):
#   API_BASE_URL / BACKEND_BASE / SMOKE_BASE_URL
#   SERVICE_TOKEN / SMOKE_AUTH_TOKEN
#   POLL_TIMEOUT (default: 300)
#
# See docs/AUTOMATION.md for detailed documentation.
# =============================================================================

.PHONY: help gen\:solo gen\:team gen\:kmu gen\:all test lint install run ci\:reports validate\:solo clean\:artifacts

# Directories
ARTIFACTS_DIR ?= artifacts
SCRIPTS_DIR = scripts
FIXTURES_DIR = fixtures

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
	@echo "CI/Automation:"
	@echo "  make ci:reports  Generate all reports with artifacts"
	@echo "  make validate:solo  Validate Solo report constraints"
	@echo "  make clean:artifacts  Remove artifacts directory"
	@echo ""
	@echo "Development:"
	@echo "  make test        Run pytest"
	@echo "  make lint        Run mypy type checking"
	@echo "  make install     Install dependencies"
	@echo "  make run         Start development server"
	@echo ""
	@echo "Environment Variables (with fallback):"
	@echo "  API_BASE_URL / BACKEND_BASE / SMOKE_BASE_URL"
	@echo "  SERVICE_TOKEN / SMOKE_AUTH_TOKEN"
	@echo "  POLL_TIMEOUT (default: 300)"

# =============================================================================
# REPORT GENERATION TARGETS
# =============================================================================

# Create artifacts directory
$(ARTIFACTS_DIR):
	@mkdir -p $(ARTIFACTS_DIR)

# Solo-Compact Report (12-16 pages)
gen\:solo: $(ARTIFACTS_DIR)
	@echo "=== Generating Solo-Compact Report ==="
	python $(SCRIPTS_DIR)/submit_fixture.py $(FIXTURES_DIR)/solo_freelancer.json \
		--poll --download-pdf $(ARTIFACTS_DIR) --output-json

# Team Report
gen\:team: $(ARTIFACTS_DIR)
	@echo "=== Generating Team Report ==="
	python $(SCRIPTS_DIR)/submit_fixture.py $(FIXTURES_DIR)/team_startup.json \
		--poll --download-pdf $(ARTIFACTS_DIR) --output-json

# KMU/Mittelstand Report
gen\:kmu: $(ARTIFACTS_DIR)
	@echo "=== Generating KMU Report ==="
	python $(SCRIPTS_DIR)/submit_fixture.py $(FIXTURES_DIR)/kmu_mittelstand.json \
		--poll --download-pdf $(ARTIFACTS_DIR) --output-json

# Generate all reports
gen\:all: gen\:solo gen\:team gen\:kmu
	@echo ""
	@echo "=== All reports generated ==="
	@echo "PDFs saved to: $(ARTIFACTS_DIR)/"
	@ls -la $(ARTIFACTS_DIR)/*.pdf 2>/dev/null || echo "No PDFs found"

# =============================================================================
# CI TARGETS
# =============================================================================

# CI: Generate reports with full artifacts
ci\:reports: $(ARTIFACTS_DIR)
	@echo "=== CI Report Generation ==="
	@echo "Generating Solo report..."
	@python $(SCRIPTS_DIR)/submit_fixture.py $(FIXTURES_DIR)/solo_freelancer.json \
		--poll --download-pdf $(ARTIFACTS_DIR) --output-json > $(ARTIFACTS_DIR)/solo_result.json 2>&1 || \
		(cat $(ARTIFACTS_DIR)/solo_result.json && exit 1)
	@echo "Generating Team report..."
	@python $(SCRIPTS_DIR)/submit_fixture.py $(FIXTURES_DIR)/team_startup.json \
		--poll --download-pdf $(ARTIFACTS_DIR) --output-json > $(ARTIFACTS_DIR)/team_result.json 2>&1 || \
		(cat $(ARTIFACTS_DIR)/team_result.json && exit 1)
	@echo "Generating KMU report..."
	@python $(SCRIPTS_DIR)/submit_fixture.py $(FIXTURES_DIR)/kmu_mittelstand.json \
		--poll --download-pdf $(ARTIFACTS_DIR) --output-json > $(ARTIFACTS_DIR)/kmu_result.json 2>&1 || \
		(cat $(ARTIFACTS_DIR)/kmu_result.json && exit 1)
	@echo ""
	@echo "=== CI Report Summary ==="
	@echo "Artifacts directory:"
	@ls -la $(ARTIFACTS_DIR)/
	@echo ""
	@echo "Results:"
	@for f in $(ARTIFACTS_DIR)/*_result.json; do \
		echo "--- $$f ---"; \
		cat "$$f" | python -c "import sys,json; d=json.load(sys.stdin); print(f\"  Status: {d.get('final_status','?')}\"); print(f\"  Briefing: {d.get('briefing_id','?')}\")"; \
	done

# Validate Solo report page count (must be 12-50)
validate\:solo:
	@echo "Validating Solo-Compact report constraints..."
	@python -c "from services.solo_compact_engine import SoloCompactConfig; c=SoloCompactConfig(); print(f'Solo pages: {c.min_pages}-{c.max_pages}'); assert c.min_pages==12 and c.max_pages==50, 'Page count mismatch'"
	@echo "Validation: OK"

# Clean artifacts
clean\:artifacts:
	@echo "Removing artifacts directory..."
	@rm -rf $(ARTIFACTS_DIR)
	@echo "Done"

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

#!/bin/bash
# Comprehensive code quality assessment
echo "=== Running Ruff linting ==="
uv run ruff check chemdataextractor/

echo "=== Checking for dead code ==="
uv run vulture chemdataextractor/ --min-confidence=80

echo "=== Complexity analysis ==="
uv run radon cc chemdataextractor/ --min=B

echo "=== Security analysis ==="
uv run bandit -r chemdataextractor/ -f json -o bandit-report.json
uv run bandit -r chemdataextractor/

echo "=== Dependency security check ==="
uv run safety scan

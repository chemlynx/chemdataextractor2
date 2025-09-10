#!/bin/bash
# Comprehensive type checking and reporting
echo "=== Running MyPy type checking ==="
uv run mypy chemdataextractor/ --html-report mypy-report/

echo "=== Generating type coverage report ==="
uv run mypy chemdataextractor/ --txt-report type-coverage/ --html-report
type-coverage-html/

echo "=== Type checking complete ==="
echo "HTML report: file://$(pwd)/mypy-report/index.html"
echo "Coverage report: file://$(pwd)/type-coverage-html/index.html"

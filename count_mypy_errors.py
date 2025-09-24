#!/usr/bin/env python
"""
Count MyPy errors by type to get an overview of issues
"""

import re
import subprocess
from collections import defaultdict


def count_mypy_errors():
    """Run mypy and count errors by type."""

    print("🔍 Running mypy and counting errors by type...")

    # Run mypy on specific modules to avoid timeout
    modules = [
        "chemdataextractor/config.py",
        "chemdataextractor/model/base.py",
        "chemdataextractor/doc/text.py",
        "chemdataextractor/parse/base.py",
        "chemdataextractor/nlp/cem.py",
    ]

    error_counts = defaultdict(int)
    total_errors = 0

    for module in modules:
        try:
            result = subprocess.run(
                ["uv", "run", "mypy", module, "--show-error-codes", "--no-error-summary"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse error codes from output
            error_pattern = r"\[(\w+[-\w]*)\]"
            errors = re.findall(error_pattern, result.stdout)

            for error in errors:
                error_counts[error] += 1
                total_errors += 1

            print(f"  {module}: {len(errors)} errors")

        except subprocess.TimeoutExpired:
            print(f"  {module}: timeout")
        except Exception as e:
            print(f"  {module}: error - {e}")

    print("\n📊 MyPy Error Summary (sampled modules):")
    print(f"Total errors: {total_errors}")

    # Sort by frequency
    sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)

    for error_type, count in sorted_errors[:15]:  # Top 15
        print(f"  {error_type:<20}: {count:>3} errors")

    return error_counts, total_errors


if __name__ == "__main__":
    count_mypy_errors()

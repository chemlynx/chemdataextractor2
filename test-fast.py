#!/usr/bin/env python3
"""
Fast test runner that bypasses heavy imports and BERT initialization
for quick test iterations during development.
"""
import os
import sys
import subprocess
import argparse

def run_fast_tests(test_pattern=None, collect_only=False, verbose=False):
    """Run tests with optimizations for speed."""

    # Set environment variables to speed up imports
    env = os.environ.copy()
    env.update({
        'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
        'PYTEST_CURRENT_TEST': '',
        'PYTHONDONTWRITEBYTECODE': '1',  # Don't write .pyc files
        'BERT_MODEL_CACHE': 'disabled',  # Disable BERT model caching if possible
    })

    # Build pytest command
    cmd = [
        sys.executable, '-m', 'pytest',
        '-c', 'pytest-fast.ini',  # Use fast config
        '--tb=short',
        '--no-header',
        '--no-summary',
    ]

    if collect_only:
        cmd.append('--collect-only')

    if verbose:
        cmd.extend(['-v', '-s'])
    else:
        cmd.append('-q')

    if test_pattern:
        cmd.append(test_pattern)

    print(f"Running: {' '.join(cmd)}")
    print(f"Environment optimizations active")

    # Run with optimized environment
    result = subprocess.run(cmd, env=env)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description='Fast test runner for ChemDataExtractor2')
    parser.add_argument('test_pattern', nargs='?', help='Test pattern (e.g., tests/test_extract.py::TestExtract::test_name)')
    parser.add_argument('--collect-only', action='store_true', help='Only collect tests, don\'t run them')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    return run_fast_tests(
        test_pattern=args.test_pattern,
        collect_only=args.collect_only,
        verbose=args.verbose
    )

if __name__ == '__main__':
    sys.exit(main())
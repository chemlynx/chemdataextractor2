# Scripts Directory

This directory contains various scripts for development, examples, and benchmarking of ChemDataExtractor2.

## Directory Structure

- **`examples/`** - Example scripts demonstrating ChemDataExtractor2 usage
  - RSC journal article extraction examples
  - Basic usage demonstrations

- **`development/`** - Development and debugging scripts
  - Trigger phrase debugging and validation
  - MyPy error counting utilities
  - Performance analysis tools

- **`benchmarks/`** - Benchmark results and performance data
  - JSON files containing benchmark results
  - Performance analysis reports
  - Optimization validation data

## Example Scripts

The example scripts show how to:
- Extract chemical data from RSC journal articles
- Configure different extraction models (fast, comprehensive, custom)
- Process scientific literature in various formats
- Generate extraction summaries and reports

## Development Scripts

Development scripts help with:
- Debugging parsing issues
- Validating performance optimizations
- Analyzing type checking errors
- Profiling extraction performance

## Usage

All scripts should be run from the project root directory:

```bash
# Run extraction example
uv run python scripts/examples/extract_rsc_configurable.py

# Run development debugging
uv run python scripts/development/debug_trigger_extraction.py
```
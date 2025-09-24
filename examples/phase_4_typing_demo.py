#!/usr/bin/env python
"""
Phase 4 Advanced Typing Demonstration for ChemDataExtractor2.

This script demonstrates the advanced typing features implemented in Phase 4,
including ParamSpec decorators and TypeVarTuple variadic generics.
"""

from __future__ import annotations

import time
from typing import Any

from chemdataextractor.types import ModelTuple
from chemdataextractor.utils import MultiParser
from chemdataextractor.utils import cache_results
from chemdataextractor.utils import timing_decorator
from chemdataextractor.utils import with_confidence_scoring

# Phase 4a: ParamSpec Decorator Demonstrations


@cache_results
def expensive_calculation(base: float, exponent: int, precision: int = 2) -> float:
    """Expensive calculation that benefits from caching.

    Demonstrates ParamSpec preserving exact function signature.
    """
    # Simulate expensive computation
    time.sleep(0.1)
    result = base**exponent
    return round(result, precision)


@timing_decorator
def parse_chemical_text(text: str, model_type: str = "melting_point") -> list[dict[str, Any]]:
    """Parse chemical text with timing information.

    Demonstrates ParamSpec with performance monitoring.
    """
    # Simulate parsing work
    time.sleep(0.05)

    # Return mock results
    return [
        {
            "type": model_type,
            "value": 125.5,
            "units": "°C",
            "confidence": 0.8,
            "text": text[:50] + "..." if len(text) > 50 else text,
        }
    ]


@with_confidence_scoring(confidence_threshold=0.6)
def extract_melting_points(text: str, strict_mode: bool = False) -> list[dict[str, Any]]:
    """Extract melting points with confidence scoring.

    Demonstrates ParamSpec with enhanced functionality.
    """
    # Simulate extraction
    results = []

    if "melting point" in text.lower() or "mp" in text.lower():
        results.append(
            {"property": "melting_point", "value": 125.5, "units": "°C", "source_text": text}
        )

    return results


# Phase 4b: TypeVarTuple Demonstrations


def demonstrate_multi_parser() -> None:
    """Demonstrate MultiParser with TypeVarTuple."""

    # Create mock parser classes
    class MeltingPointParser:
        def parse(self, text: str) -> list[dict[str, Any]]:
            return [{"type": "melting_point", "value": 125.5, "units": "°C"}]

    class BoilingPointParser:
        def parse(self, text: str) -> list[dict[str, Any]]:
            return [{"type": "boiling_point", "value": 350.2, "units": "°C"}]

    class DensityParser:
        def parse(self, text: str) -> list[dict[str, Any]]:
            return [{"type": "density", "value": 1.25, "units": "g/cm³"}]

    # Create multi-parser with type safety
    multi_parser: MultiParser[MeltingPointParser, BoilingPointParser, DensityParser] = MultiParser(
        MeltingPointParser, BoilingPointParser, DensityParser
    )

    # Parse with preserved type information
    sample_text = "The compound has a melting point of 125°C, boiling point of 350°C, and density of 1.25 g/cm³."
    results = multi_parser.parse(sample_text)

    # Type checker knows this is tuple[MeltingPointParser, BoilingPointParser, DensityParser]
    melting_result, boiling_result, density_result = results

    print(f"✅ MultiParser results: {len(results)} parsers executed")
    print(f"   - Melting Point: {type(melting_result).__name__}")
    print(f"   - Boiling Point: {type(boiling_result).__name__}")
    print(f"   - Density: {type(density_result).__name__}")


def demonstrate_typed_extraction() -> ModelTuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Demonstrate typed extraction with variadic returns."""

    # Simulate extraction of multiple property types
    melting_point = {"property": "melting_point", "value": 125.5, "units": "°C"}
    boiling_point = {"property": "boiling_point", "value": 350.2, "units": "°C"}
    density = {"property": "density", "value": 1.25, "units": "g/cm³"}

    # Return typed tuple
    return melting_point, boiling_point, density


def demonstrate_heterogeneous_processing() -> None:
    """Demonstrate processing of heterogeneous result types."""

    # Get typed results
    mp_result, bp_result, density_result = demonstrate_typed_extraction()

    # Process each type appropriately
    results = {"melting_point": mp_result, "boiling_point": bp_result, "density": density_result}

    print("✅ Heterogeneous processing results:")
    for prop_type, data in results.items():
        print(f"   - {prop_type}: {data['value']} {data['units']}")


def main() -> None:
    """Demonstrate Phase 4 advanced typing features."""

    print("🚀 Phase 4 Advanced Typing Demonstration")
    print("=" * 50)

    # Phase 4a: ParamSpec Demonstrations
    print("\n📋 Phase 4a: ParamSpec Function Decorators")
    print("-" * 40)

    # Test cached function (preserves signature)
    print("Testing cached expensive calculation...")
    start_time = time.perf_counter()
    result1 = expensive_calculation(2.5, 3, precision=3)  # First call
    result2 = expensive_calculation(2.5, 3, precision=3)  # Cached call
    end_time = time.perf_counter()

    print(f"   Results: {result1} (cached: {result2})")
    print(f"   Time: {end_time - start_time:.4f}s (includes caching speedup)")

    # Test timed function
    print("\nTesting timed parsing function...")
    parse_results = parse_chemical_text("The melting point is 125°C", model_type="temperature")
    print(f"   Parsed {len(parse_results)} results")

    # Test confidence-enhanced function
    print("\nTesting confidence-enhanced extraction...")
    confidence_results = extract_melting_points(
        "The melting point of the compound is 125°C", strict_mode=True
    )
    print(f"   Extracted {len(confidence_results)} high-confidence results")

    # Phase 4b: TypeVarTuple Demonstrations
    print("\n📋 Phase 4b: TypeVarTuple Variadic Generics")
    print("-" * 40)

    # Test multi-parser
    print("Testing MultiParser with TypeVarTuple...")
    demonstrate_multi_parser()

    # Test heterogeneous processing
    print("\nTesting heterogeneous result processing...")
    demonstrate_heterogeneous_processing()

    print("\n✅ Phase 4 demonstration completed successfully!")
    print("\n🎯 Key Benefits Demonstrated:")
    print("   • ParamSpec preserves exact function signatures in decorators")
    print("   • TypeVarTuple enables type-safe variadic generic operations")
    print("   • Enhanced IDE support with precise type inference")
    print("   • Runtime type safety with compile-time guarantees")


if __name__ == "__main__":
    main()

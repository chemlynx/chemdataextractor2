#!/usr/bin/env python3
"""
Debug model dependencies to understand why Compound keeps appearing.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor.model.model import Apparatus
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint


def check_model_dependencies():
    """Check what dependencies each model has."""

    print("🔍 Checking Model Dependencies")
    print("=" * 60)

    models_to_check = [Compound, MeltingPoint, Apparatus]

    for model in models_to_check:
        print(f"\n📋 {model.__name__} dependencies:")

        # Get flattened models (includes dependencies)
        flattened = list(model.flatten())
        print(f"  Flattened models: {[m.__name__ for m in flattened]}")

        # Check with and without inferred
        flattened_no_inferred = list(model.flatten(include_inferred=False))
        print(f"  Flattened (no inferred): {[m.__name__ for m in flattened_no_inferred]}")


def test_minimal_model_set():
    """Test what happens with just one model at a time."""

    print("\n🧪 Testing Minimal Model Sets")
    print("=" * 60)

    from chemdataextractor.doc.text import Title

    title = Title("Synthesis of CuSO4 Complexes")

    test_cases = [
        ([MeltingPoint], "MeltingPoint only"),
        ([Apparatus], "Apparatus only"),
        ([MeltingPoint, Apparatus], "MeltingPoint + Apparatus"),
    ]

    for models, description in test_cases:
        print(f"\n🔬 Test: {description}")
        title.models = models

        print(f"  Set models: {[m.__name__ for m in models]}")
        print(f"  Streamlined: {[m.__name__ for m in title._streamlined_models]}")

        # Check if Compound appears in streamlined
        has_compound = any(m.__name__ == "Compound" for m in title._streamlined_models)
        print(f"  Contains Compound: {'❌ YES' if has_compound else '✅ NO'}")


def find_compound_dependency():
    """Find which model is pulling in Compound as a dependency."""

    print("\n🕵️ Finding Compound Dependency Source")
    print("=" * 60)

    # Check each model individually
    models = [MeltingPoint, Apparatus]

    for model in models:
        print(f"\n📋 Analyzing {model.__name__}:")

        # Get the fields
        if hasattr(model, "fields"):
            for field_name, field in model.fields.items():
                print(f"  Field '{field_name}': {type(field).__name__}")

                # Check if it's a ModelType field
                if hasattr(field, "model_class"):
                    print(f"    model_class: {field.model_class.__name__}")

                    if field.model_class.__name__ == "Compound":
                        print(f"    🎯 FOUND: {field_name} field references Compound!")

                # Check if it's a ListType with ModelType
                if hasattr(field, "field") and hasattr(field.field, "model_class"):
                    print(f"    field.field.model_class: {field.field.model_class.__name__}")

                    if field.field.model_class.__name__ == "Compound":
                        print(f"    🎯 FOUND: {field_name} list field references Compound!")


def test_solution():
    """Test a working solution by excluding dependent models."""

    print("\n💡 Testing Solution: Exclude Models with Compound Dependencies")
    print("=" * 60)

    from chemdataextractor.doc.text import Title

    title = Title("Synthesis of CuSO4 Complexes")

    # Test with no models that depend on Compound
    print("🔬 Test 1: Empty models")
    title.models = []
    print(f"  Set models: {title.models}")
    print(f"  Streamlined: {[m.__name__ for m in title._streamlined_models]}")

    records = list(title.records)
    compounds = [r for r in records if isinstance(r, Compound)]
    print(f"  Records: {len(records)}, Compounds: {len(compounds)}")


def main():
    print("🔍 Debugging Model Dependencies")
    print("=" * 80)

    check_model_dependencies()
    test_minimal_model_set()
    find_compound_dependency()
    test_solution()


if __name__ == "__main__":
    main()

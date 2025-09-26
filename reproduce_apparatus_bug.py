#!/usr/bin/env python3
"""
Script to reproduce the specific apparatus bug we saw in the extraction results.
The bug might be more complex than simple merge_contextual - let's investigate.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor.model import Apparatus
from chemdataextractor.model import Compound
from chemdataextractor.model import MeltingPoint


def test_direct_merge_scenarios():
    """Test various direct merge scenarios"""
    print("🧪 Testing Direct Merge Scenarios")
    print("=" * 50)

    # Scenario 1: Different model types
    mp = MeltingPoint(value=[200.0], units="Celsius^(1.0)")
    water_compound = Compound(names=["water"])

    print("Scenario 1: MeltingPoint + Compound(names=['water'])")
    print(
        f"  Before: apparatus={getattr(mp, 'apparatus', None)}, compound={getattr(mp, 'compound', None)}"
    )

    result = mp.merge_contextual(water_compound)
    print(
        f"  After: result={result}, apparatus={getattr(mp, 'apparatus', None)}, compound={getattr(mp, 'compound', None)}"
    )

    if hasattr(mp, "apparatus") and mp.apparatus:
        print(f"  ⚠️  APPARATUS FIELD SET: {mp.apparatus.serialize()}")

    # Scenario 2: Try the reverse
    print("\nScenario 2: Compound(names=['water']) + MeltingPoint")
    compound2 = Compound(names=["water"])
    mp2 = MeltingPoint(value=[200.0], units="Celsius^(1.0)")

    result2 = compound2.merge_contextual(mp2)
    print(f"  Merge result: {result2}")


def test_with_flattened_types():
    """Test what happens with flattened model types"""
    print("\n🔍 Testing Model Type Flattening")
    print("=" * 50)

    mp = MeltingPoint(value=[200.0], units="Celsius^(1.0)")
    print(f"MeltingPoint flattened types: {type(mp).flatten()}")

    compound = Compound(names=["water"])
    print(f"Compound type: {type(compound)}")
    print(f"Is Compound in MeltingPoint.flatten()? {type(compound) in type(mp).flatten()}")


def test_field_inspection():
    """Inspect the exact field definitions"""
    print("\n🔬 Inspecting Field Definitions")
    print("=" * 50)

    mp = MeltingPoint()

    print("MeltingPoint fields:")
    for field_name, field in mp.fields.items():
        print(f"  {field_name}: {field}")
        if hasattr(field, "model_class"):
            print(f"    model_class: {field.model_class}")
        if hasattr(field, "contextual"):
            print(f"    contextual: {field.contextual}")
        if hasattr(field, "field") and hasattr(field.field, "model_class"):
            print(f"    field.field.model_class: {field.field.model_class}")


def test_binding_compatibility():
    """Test binding compatibility logic"""
    print("\n🔗 Testing Binding Compatibility")
    print("=" * 50)

    mp = MeltingPoint(value=[200.0], units="Celsius^(1.0)")
    compound = Compound(names=["water"])
    apparatus = Apparatus(name="DSC")

    print(f"MeltingPoint._binding_compatible(Compound): {mp._binding_compatible(compound)}")
    print(f"MeltingPoint._binding_compatible(Apparatus): {mp._binding_compatible(apparatus)}")


def test_step_by_step_merge():
    """Step through the merge logic to find where the bug occurs"""
    print("\n🐛 Step-by-Step Merge Debug")
    print("=" * 50)

    mp = MeltingPoint(value=[200.0], units="Celsius^(1.0)")
    compound = Compound(names=["water"])

    print("1. Initial state:")
    print(f"   mp.apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"   mp.compound: {getattr(mp, 'compound', None)}")

    print("2. Compatibility checks:")
    print(f"   mp.contextual_fulfilled: {mp.contextual_fulfilled}")
    print(f"   mp._binding_compatible(compound): {mp._binding_compatible(compound)}")
    print(f"   type(mp) == type(compound): {type(mp) == type(compound)}")
    print(f"   type(compound) in type(mp).flatten(): {type(compound) in type(mp).flatten()}")

    # Look at apparatus field specifically
    apparatus_field = mp.fields.get("apparatus")
    print("3. Apparatus field analysis:")
    if apparatus_field:
        print(f"   apparatus field type: {type(apparatus_field)}")
        print(f"   apparatus field.contextual: {apparatus_field.contextual}")
        if hasattr(apparatus_field, "model_class"):
            print(f"   apparatus field.model_class: {apparatus_field.model_class}")
            print(
                f"   isinstance(compound, apparatus_field.model_class): {isinstance(compound, apparatus_field.model_class)}"
            )

    # Look at compound field
    compound_field = mp.fields.get("compound")
    print("4. Compound field analysis:")
    if compound_field:
        print(f"   compound field type: {type(compound_field)}")
        print(f"   compound field.contextual: {compound_field.contextual}")
        if hasattr(compound_field, "model_class"):
            print(f"   compound field.model_class: {compound_field.model_class}")
            print(
                f"   isinstance(compound, compound_field.model_class): {isinstance(compound, compound_field.model_class)}"
            )

    print("\n5. Performing merge...")
    result = mp.merge_contextual(compound)

    print("6. After merge:")
    print(f"   merge result: {result}")
    print(f"   mp.apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"   mp.compound: {getattr(mp, 'compound', None)}")

    if hasattr(mp, "apparatus") and mp.apparatus:
        print(f"   ❌ BUG: apparatus field was set to: {mp.apparatus.serialize()}")


def main():
    print("🔍 Reproducing Apparatus Bug Investigation")
    print("=" * 80)

    try:
        test_direct_merge_scenarios()
        test_with_flattened_types()
        test_field_inspection()
        test_binding_compatibility()
        test_step_by_step_merge()

        print("\n" + "=" * 80)
        print("✅ Investigation complete!")

    except Exception as e:
        print(f"\n❌ Error during investigation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

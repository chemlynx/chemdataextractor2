#!/usr/bin/env python3
"""
Systematic investigation of the H2O apparatus bug.
Focus on finding exactly where/how Compound(names=['H2O']) becomes Apparatus(name='H2O').
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor.model import Apparatus
from chemdataextractor.model import Compound
from chemdataextractor.model import MeltingPoint


def investigate_apparatus_creation():
    """Investigate how Apparatus objects are created"""
    print("🔍 Investigating Apparatus Object Creation")
    print("=" * 60)

    # Test 1: Can we create an Apparatus with H2O name directly?
    try:
        apparatus = Apparatus(name="H2O")
        print(f"✅ Can create Apparatus(name='H2O'): {apparatus.serialize()}")
    except Exception as e:
        print(f"❌ Cannot create Apparatus(name='H2O'): {e}")

    # Test 2: What happens if we serialize a Compound and then deserialize as Apparatus?
    h2o_compound = Compound(names=["H2O"])
    compound_data = h2o_compound.serialize()
    print(f"Compound data: {compound_data}")

    # Test 3: Check if there's any automatic conversion happening
    try:
        # This shouldn't work but let's see
        fake_apparatus = Apparatus(name=list(h2o_compound.names)[0])
        print(f"⚠️  Created apparatus from compound name: {fake_apparatus.serialize()}")
    except Exception as e:
        print(f"✅ Cannot create apparatus from compound: {e}")


def investigate_model_conversion():
    """Investigate if there's any model type conversion happening"""
    print("\n🔄 Investigating Model Type Conversion")
    print("=" * 60)

    h2o_compound = Compound(names=["H2O"])
    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")

    # Test our refactored merge_contextual
    print("Testing refactored merge_contextual...")
    result = mp.merge_contextual(h2o_compound)
    print(f"Merge result: {result}")
    print(f"MP after merge: {mp.serialize()}")

    if hasattr(mp, "apparatus") and mp.apparatus:
        print(f"🐛 BUG: Apparatus field was set: {mp.apparatus.serialize()}")
    else:
        print("✅ No apparatus field set (correct behavior)")


def investigate_copy_operations():
    """Investigate if copy.copy is causing issues"""
    print("\n📋 Investigating Copy Operations")
    print("=" * 60)

    import copy

    h2o_compound = Compound(names=["H2O"])
    print(f"Original compound: {h2o_compound} -> {h2o_compound.serialize()}")

    # Test copy.copy (used in our merge methods)
    copied_compound = copy.copy(h2o_compound)
    print(f"Copied compound: {copied_compound} -> {copied_compound.serialize()}")
    print(f"Types match: {type(h2o_compound) == type(copied_compound)}")
    print(f"Both are Compound: {isinstance(copied_compound, Compound)}")


def investigate_field_assignment():
    """Test direct field assignment scenarios"""
    print("\n📝 Investigating Field Assignment")
    print("=" * 60)

    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    h2o_compound = Compound(names=["H2O"])

    # What happens if we directly assign the wrong type?
    print("Testing direct assignment of Compound to apparatus field...")
    try:
        mp.apparatus = h2o_compound  # This should fail or be converted
        print(f"⚠️  Direct assignment succeeded: {mp.apparatus}")
        print(f"Apparatus type: {type(mp.apparatus)}")
        print(f"Apparatus serialized: {mp.apparatus.serialize()}")

        # Is it still a Compound or was it converted to Apparatus?
        print(f"Is still Compound: {isinstance(mp.apparatus, Compound)}")
        print(f"Is now Apparatus: {isinstance(mp.apparatus, Apparatus)}")

    except Exception as e:
        print(f"✅ Direct assignment failed as expected: {e}")


def investigate_model_field_validation():
    """Check if ModelType fields have validation"""
    print("\n🔍 Investigating ModelType Field Validation")
    print("=" * 60)

    mp = MeltingPoint()

    # Get the apparatus field definition
    apparatus_field = mp.fields.get("apparatus")
    if apparatus_field:
        print(f"Apparatus field type: {type(apparatus_field)}")
        print(f"Expected model class: {getattr(apparatus_field, 'model_class', None)}")

        # Check if the field has any conversion or validation logic
        print(f"Field attributes: {dir(apparatus_field)}")


def investigate_serialization_issue():
    """Check if serialization/deserialization is involved"""
    print("\n💾 Investigating Serialization")
    print("=" * 60)

    # Create MeltingPoint with correct compound
    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    h2o_compound = Compound(names=["H2O"])
    mp.compound = h2o_compound

    print("Original MP:")
    serialized = mp.serialize()
    print(f"  {serialized}")

    # Check if there's any way the serialization could be interpreted wrong
    if "apparatus" in str(serialized):
        print("⚠️  'apparatus' appears in serialization unexpectedly!")
    else:
        print("✅ Serialization looks correct")


def main():
    """Run all investigations"""
    print("🔍 H2O Apparatus Bug Investigation")
    print("=" * 80)
    print("Systematically investigating how H2O compounds become apparatus...")

    try:
        investigate_apparatus_creation()
        investigate_model_conversion()
        investigate_copy_operations()
        investigate_field_assignment()
        investigate_model_field_validation()
        investigate_serialization_issue()

        print("\n" + "=" * 80)
        print("🎯 Investigation Summary")
        print("=" * 80)
        print("Key findings will help locate the exact bug location...")

    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

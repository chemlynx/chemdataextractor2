#!/usr/bin/env python3
"""
Deep investigation into model field assignment to find the H2O apparatus bug.
Focus on ModelType field behavior and automatic conversions.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor.model import Apparatus
from chemdataextractor.model import Compound
from chemdataextractor.model import MeltingPoint
from chemdataextractor.model.base import ModelType


def test_modeltype_field_behavior():
    """Test how ModelType fields handle different assignments"""
    print("🧪 Testing ModelType Field Behavior")
    print("=" * 60)

    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")

    # Test 1: Direct assignment of correct type
    print("Test 1: Assigning correct Apparatus type")
    try:
        proper_apparatus = Apparatus(name="NMR Spectrometer")
        mp.apparatus = proper_apparatus
        print(f"✅ Assignment worked: {mp.apparatus.serialize()}")
        print(f"Type: {type(mp.apparatus)}")
    except Exception as e:
        print(f"❌ Assignment failed: {e}")

    # Test 2: Direct assignment of wrong type (Compound)
    print("\nTest 2: Assigning wrong Compound type")
    mp2 = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    try:
        h2o_compound = Compound(names=["H2O"])
        mp2.apparatus = h2o_compound
        print(f"Result: {mp2.apparatus}")
        print(f"Type: {type(mp2.apparatus) if mp2.apparatus else None}")
        if mp2.apparatus:
            print(f"Serialized: {mp2.apparatus.serialize()}")
    except Exception as e:
        print(f"Assignment failed: {e}")

    # Test 3: Assignment of string (might get auto-converted?)
    print("\nTest 3: Assigning string value")
    mp3 = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    try:
        mp3.apparatus = "H2O"  # Direct string assignment
        print(f"Result: {mp3.apparatus}")
        print(f"Type: {type(mp3.apparatus) if mp3.apparatus else None}")
        if mp3.apparatus:
            print(f"Serialized: {mp3.apparatus.serialize()}")
    except Exception as e:
        print(f"String assignment failed: {e}")

    # Test 4: Assignment of dictionary
    print("\nTest 4: Assigning dictionary")
    mp4 = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    try:
        mp4.apparatus = {"name": "H2O"}
        print(f"Result: {mp4.apparatus}")
        print(f"Type: {type(mp4.apparatus) if mp4.apparatus else None}")
        if mp4.apparatus:
            print(f"Serialized: {mp4.apparatus.serialize()}")
    except Exception as e:
        print(f"Dict assignment failed: {e}")


def test_model_field_setters():
    """Test if there are any custom setters that might do conversion"""
    print("\n🔧 Testing Model Field Setters")
    print("=" * 60)

    mp = MeltingPoint()

    # Check if apparatus field has custom setter logic
    apparatus_field = mp.fields["apparatus"]
    print(f"Apparatus field: {apparatus_field}")
    print(f"Field type: {type(apparatus_field)}")

    # Check ModelType class for any conversion logic
    print(f"ModelType has __set__: {hasattr(ModelType, '__set__')}")

    # Look at the actual setter mechanism
    import inspect

    if hasattr(ModelType, "__set__"):
        print("ModelType __set__ method:")
        print(inspect.getsource(ModelType.__set__))


def test_process_method():
    """Test if the 'process' method on fields does conversion"""
    print("\n⚙️ Testing Field Process Method")
    print("=" * 60)

    mp = MeltingPoint()
    apparatus_field = mp.fields["apparatus"]

    # Test process method with different inputs
    test_values = ["H2O", {"name": "H2O"}, Compound(names=["H2O"]), Apparatus(name="H2O")]

    for i, test_val in enumerate(test_values, 1):
        print(f"Test {i}: Processing {type(test_val)} -> {test_val}")
        try:
            processed = apparatus_field.process(test_val)
            print(f"  Result: {processed}")
            print(f"  Type: {type(processed)}")
            if hasattr(processed, "serialize"):
                print(f"  Serialized: {processed.serialize()}")
        except Exception as e:
            print(f"  Failed: {e}")


def investigate_model_creation_pipeline():
    """Investigate if there's automatic model creation happening"""
    print("\n🏭 Investigating Model Creation Pipeline")
    print("=" * 60)

    # Check if there's any automatic Apparatus creation from strings
    print("Testing Apparatus creation with various inputs:")

    test_inputs = ["H2O", "water", "NMR", "DSC"]

    for input_val in test_inputs:
        try:
            apparatus = Apparatus(name=input_val)
            print(f"✅ Apparatus(name='{input_val}') -> {apparatus.serialize()}")
        except Exception as e:
            print(f"❌ Apparatus(name='{input_val}') failed: {e}")


def investigate_merge_contextual_detailed():
    """Detailed investigation of merge_contextual with debug output"""
    print("\n🔍 Detailed merge_contextual Investigation")
    print("=" * 60)

    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    h2o_compound = Compound(names=["H2O"])

    print("Before merge:")
    print(f"  mp.apparatus: {getattr(mp, 'apparatus', 'not set')}")
    print(f"  mp.compound: {getattr(mp, 'compound', 'not set')}")

    # Manually step through the merge logic
    print("\nCompatibility checks:")
    print(f"  mp._binding_compatible(h2o_compound): {mp._binding_compatible(h2o_compound)}")
    print(f"  type(mp) == type(h2o_compound): {type(mp) == type(h2o_compound)}")
    print(f"  type(h2o_compound) in type(mp).flatten(): {type(h2o_compound) in type(mp).flatten()}")

    # Check field compatibility specifically
    apparatus_field = mp.fields["apparatus"]
    print("\nApparatus field compatibility:")
    print(
        f"  isinstance(h2o_compound, apparatus_field.model_class): {isinstance(h2o_compound, apparatus_field.model_class)}"
    )

    compound_field = mp.fields["compound"]
    print("\nCompound field compatibility:")
    print(
        f"  isinstance(h2o_compound, compound_field.model_class): {isinstance(h2o_compound, compound_field.model_class)}"
    )

    # Now do the actual merge
    result = mp.merge_contextual(h2o_compound)

    print("\nAfter merge:")
    print(f"  Result: {result}")
    print(f"  mp.apparatus: {getattr(mp, 'apparatus', 'not set')}")
    print(f"  mp.compound: {getattr(mp, 'compound', 'not set')}")

    if hasattr(mp, "compound") and mp.compound:
        print(f"  mp.compound type: {type(mp.compound)}")
        print(f"  mp.compound serialized: {mp.compound.serialize()}")


def main():
    """Run all investigations"""
    print("🔍 Deep Model Assignment Investigation")
    print("=" * 80)

    try:
        test_modeltype_field_behavior()
        test_model_field_setters()
        test_process_method()
        investigate_model_creation_pipeline()
        investigate_merge_contextual_detailed()

        print("\n" + "=" * 80)
        print("🎯 Deep Investigation Complete")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

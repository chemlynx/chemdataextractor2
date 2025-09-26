#!/usr/bin/env python3
"""
Comprehensive test to verify that the merge_contextual refactoring
fixed the H2O apparatus bug reported by the user.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor.model import Apparatus
from chemdataextractor.model import Compound
from chemdataextractor.model import MeltingPoint


def test_type_safety_in_merge():
    """Test that merge_contextual respects type safety"""
    print("🔍 Testing Type Safety in Merge Operations")
    print("=" * 60)

    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    h2o_compound = Compound(names=["H2O"])

    print("Before merge:")
    print(f"  MP apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"  MP compound: {getattr(mp, 'compound', None)}")

    # This is the key test - does merge_contextual incorrectly assign H2O to apparatus?
    result = mp.merge_contextual(h2o_compound)
    print(f"\nMerge result: {result}")

    print("After merge:")
    print(f"  MP apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"  MP compound: {getattr(mp, 'compound', None)}")

    # Check for type violations
    if hasattr(mp, "apparatus") and mp.apparatus is not None:
        print(f"  Apparatus type: {type(mp.apparatus)}")
        print(f"  Apparatus data: {mp.apparatus.serialize()}")

        if not isinstance(mp.apparatus, Apparatus):
            print("  🐛 TYPE VIOLATION: apparatus field contains non-Apparatus object!")
            return False

        if hasattr(mp.apparatus, "name") and mp.apparatus.name == "H2O":
            print("  🐛 BUG: H2O compound incorrectly assigned to apparatus field!")
            return False

    if hasattr(mp, "compound") and mp.compound is not None:
        print(f"  Compound type: {type(mp.compound)}")
        print(f"  Compound data: {mp.compound.serialize()}")

        if isinstance(mp.compound, Compound) and "H2O" in mp.compound.names:
            print("  ✅ CORRECT: H2O properly assigned to compound field!")
            return True

    print("  ℹ️  No merge occurred")
    return True


def test_field_compatibility_logic():
    """Test that field compatibility logic works correctly"""
    print("\n🔧 Testing Field Compatibility Logic")
    print("=" * 60)

    mp = MeltingPoint()
    h2o_compound = Compound(names=["H2O"])

    # Check apparatus field compatibility
    apparatus_field = mp.fields["apparatus"]
    print(f"Apparatus field model_class: {apparatus_field.model_class}")
    print(f"H2O is instance of Apparatus: {isinstance(h2o_compound, apparatus_field.model_class)}")

    # Check compound field compatibility
    compound_field = mp.fields["compound"]
    print(f"Compound field model_class: {compound_field.model_class}")
    print(f"H2O is instance of Compound: {isinstance(h2o_compound, compound_field.model_class)}")

    # Test compatibility manually
    apparatus_compatible = isinstance(h2o_compound, apparatus_field.model_class)
    compound_compatible = isinstance(h2o_compound, compound_field.model_class)
    print(f"Manual apparatus compatibility: {apparatus_compatible}")
    print(f"Manual compound compatibility: {compound_compatible}")

    return apparatus_compatible == False and compound_compatible == True


def test_modeltype_process_method():
    """Test that ModelType.process handles type validation correctly"""
    print("\n⚙️ Testing ModelType Process Method")
    print("=" * 60)

    mp = MeltingPoint()
    apparatus_field = mp.fields["apparatus"]
    compound_field = mp.fields["compound"]

    h2o_compound = Compound(names=["H2O"])
    h2o_apparatus = Apparatus(name="H2O")

    # Test apparatus field processing
    print("Testing apparatus field processing:")

    # Should accept Apparatus
    processed_apparatus = apparatus_field.process(h2o_apparatus)
    print(f"  Apparatus -> Apparatus: {processed_apparatus is not None}")

    # Should reject Compound
    processed_compound_as_apparatus = apparatus_field.process(h2o_compound)
    print(f"  Compound -> Apparatus: {processed_compound_as_apparatus is not None}")

    # Test compound field processing
    print("\nTesting compound field processing:")

    # Should accept Compound
    processed_compound = compound_field.process(h2o_compound)
    print(f"  Compound -> Compound: {processed_compound is not None}")

    # Should reject Apparatus
    processed_apparatus_as_compound = compound_field.process(h2o_apparatus)
    print(f"  Apparatus -> Compound: {processed_apparatus_as_compound is not None}")

    # The key test: ModelType should NOT allow cross-type assignments
    if processed_compound_as_apparatus is None and processed_apparatus_as_compound is None:
        print("  ✅ CORRECT: ModelType properly rejects invalid types!")
        return True
    else:
        print("  🐛 BUG: ModelType allows invalid type assignments!")
        return False


def test_comprehensive_merge_scenarios():
    """Test various merge scenarios that could trigger the bug"""
    print("\n🧪 Testing Comprehensive Merge Scenarios")
    print("=" * 60)

    scenarios = [
        (
            "H2O compound to empty MP",
            MeltingPoint(value=[100.0], units="C"),
            Compound(names=["H2O"]),
        ),
        (
            "H2O compound to MP with apparatus",
            MeltingPoint(value=[100.0], units="C", apparatus=Apparatus(name="DSC")),
            Compound(names=["H2O"]),
        ),
        (
            "H2O apparatus to empty MP",
            MeltingPoint(value=[100.0], units="C"),
            Apparatus(name="H2O"),
        ),
        (
            "H2O apparatus to MP with compound",
            MeltingPoint(value=[100.0], units="C", compound=Compound(names=["benzene"])),
            Apparatus(name="H2O"),
        ),
    ]

    all_correct = True
    for i, (description, mp, merge_object) in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {description}")

        original_mp_state = mp.serialize()
        result = mp.merge_contextual(merge_object)
        final_mp_state = mp.serialize()

        print(f"  Before: {original_mp_state}")
        print(f"  After:  {final_mp_state}")
        print(f"  Merge result: {result}")

        # Check for type violations
        if hasattr(mp, "apparatus") and mp.apparatus is not None:
            if not isinstance(mp.apparatus, Apparatus):
                print(f"    🐛 TYPE VIOLATION: apparatus contains {type(mp.apparatus)}")
                all_correct = False

        if hasattr(mp, "compound") and mp.compound is not None:
            if not isinstance(mp.compound, Compound):
                print(f"    🐛 TYPE VIOLATION: compound contains {type(mp.compound)}")
                all_correct = False

    return all_correct


def main():
    print("🔍 Comprehensive Test: Merge Contextual Fix Verification")
    print("=" * 80)
    print("Testing if the refactored merge_contextual fixed the H2O apparatus bug")

    try:
        test_results = []

        # Test 1: Basic type safety
        test_results.append(test_type_safety_in_merge())

        # Test 2: Field compatibility logic
        test_results.append(test_field_compatibility_logic())

        # Test 3: ModelType process method
        test_results.append(test_modeltype_process_method())

        # Test 4: Comprehensive scenarios
        test_results.append(test_comprehensive_merge_scenarios())

        print("\n" + "=" * 80)
        print("🎯 FIX VERIFICATION SUMMARY")
        print("=" * 80)

        if all(test_results):
            print("✅ ALL TESTS PASSED!")
            print("🎉 The refactored merge_contextual correctly handles type safety")
            print("🔧 H2O apparatus bug appears to be FIXED by the refactoring")

            print("\n📋 Key Improvements:")
            print("  • Proper type checking in field compatibility")
            print("  • ModelType.process rejects invalid types")
            print("  • Helper methods ensure consistent logic")
            print("  • No cross-type contamination in merges")
        else:
            print("❌ SOME TESTS FAILED")
            print("🐛 Type safety issues still exist")
            print("🔍 Further investigation needed")

        print(f"\nDetailed results: {test_results}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

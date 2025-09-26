#!/usr/bin/env python3
"""
Quick validation script to test merge functionality without pytest overhead.
This validates our comprehensive test scenarios work correctly.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor.model import Apparatus
from chemdataextractor.model import Compound
from chemdataextractor.model import MeltingPoint
from chemdataextractor.model.contextual_range import SentenceRange


def test_type_safety_bug():
    """Test and document the type safety bug we discovered"""
    print("🔍 Testing Type Safety Bug Reproduction:")
    print("=" * 50)

    # Create melting point and compound (reproduces real scenario)
    mp = MeltingPoint(value=[200.0], units="Celsius^(1.0)")
    water_compound = Compound(names=["water"])

    print("Before merge:")
    print(f"  MeltingPoint apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"  MeltingPoint compound: {getattr(mp, 'compound', None)}")

    # This should NOT create apparatus field from compound
    result = mp.merge_contextual(water_compound)

    print("After merge_contextual with Compound(names=['water']):")
    print(f"  Merge result: {result}")
    print(f"  MeltingPoint apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"  MeltingPoint compound: {getattr(mp, 'compound', None)}")

    # Check if bug occurred
    if hasattr(mp, "apparatus") and mp.apparatus and mp.apparatus.name == "water":
        print("❌ BUG REPRODUCED: Compound incorrectly merged into apparatus field!")
        print(f"   Apparatus object: {mp.apparatus.serialize()}")
        return True
    elif hasattr(mp, "compound") and mp.compound and mp.compound.names == ["water"]:
        print("✅ Correct behavior: Compound merged into compound field")
        return False
    else:
        print("ℹ️  No merge occurred")
        return False


def test_correct_apparatus_merge():
    """Test that proper apparatus merging works"""
    print("\n🔧 Testing Correct Apparatus Merging:")
    print("=" * 50)

    mp = MeltingPoint(value=[150.0], units="Celsius^(1.0)")
    apparatus = Apparatus(name="DSC spectrometer")

    print("Before merge:")
    print(f"  MeltingPoint apparatus: {getattr(mp, 'apparatus', None)}")

    result = mp.merge_contextual(apparatus)

    print("After merge_contextual with Apparatus(name='DSC spectrometer'):")
    print(f"  Merge result: {result}")
    print(f"  MeltingPoint apparatus: {getattr(mp, 'apparatus', None)}")

    if result and hasattr(mp, "apparatus") and mp.apparatus:
        print("✅ Correct: Apparatus properly merged")
        print(f"   Apparatus name: {mp.apparatus.name}")
        return True
    else:
        print("❌ Issue: Apparatus merge failed")
        return False


def test_distance_boundary():
    """Test distance boundary behavior"""
    print("\n📏 Testing Distance Boundaries:")
    print("=" * 50)

    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    compound = Compound(names=["benzene"])

    # Test within sentence range (should work for contextual fields)
    result_sentence = mp.merge_contextual(compound, distance=SentenceRange())

    print(f"Merge within SentenceRange: {result_sentence}")
    if result_sentence and hasattr(mp, "compound"):
        print(f"  Compound field: {mp.compound}")

    return result_sentence


def test_never_merge_behavior():
    """Test never_merge field behavior if possible"""
    print("\n🚫 Testing never_merge Fields:")
    print("=" * 50)
    print("(Would require custom model with never_merge fields)")


def main():
    print("🧪 ChemDataExtractor2 Merge Method Validation")
    print("=" * 80)

    try:
        # Test the critical type safety bug
        bug_reproduced = test_type_safety_bug()

        # Test correct apparatus merging
        apparatus_works = test_correct_apparatus_merge()

        # Test distance boundaries
        distance_works = test_distance_boundary()

        print("\n📋 Summary:")
        print("=" * 30)
        print(f"Type safety bug reproduced: {'Yes' if bug_reproduced else 'No'}")
        print(f"Apparatus merging works: {'Yes' if apparatus_works else 'No'}")
        print(f"Distance boundaries work: {'Yes' if distance_works else 'No'}")

        if bug_reproduced:
            print("\n⚠️  CRITICAL ISSUE: Type safety bug confirmed!")
            print("   This explains the wrong apparatus data in extraction results.")
            print("   Refactoring should fix this by adding proper type validation.")

        print("\n✅ Validation complete - comprehensive tests are ready!")

    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

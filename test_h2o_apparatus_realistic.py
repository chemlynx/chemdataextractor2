#!/usr/bin/env python3
"""
Realistic test to reproduce the H2O apparatus bug based on user report.
The user mentioned seeing 'H2O' as apparatus against melting points in real extraction results.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.doc.text import Paragraph
from chemdataextractor.model.model import Apparatus
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint


def test_apparatus_model_included():
    """Test with Apparatus model included - this might trigger the bug"""
    print("🔍 Testing with Apparatus Model Included")
    print("=" * 60)

    # Create document with a realistic chemical analysis scenario
    doc = Document(
        Paragraph("The compound was synthesized and characterized."),
        Paragraph("Melting point determination was carried out using standard apparatus."),
        Paragraph("The melting point was found to be 89-91°C."),
        Paragraph("H2O was used as the solvent for recrystallization."),
        Paragraph("Another compound showed melting point of 140-143°C."),
    )

    # Include Apparatus model - this might be what triggers the bug
    doc.models = [Compound, MeltingPoint, Apparatus]
    print(f"Models: {[m.__name__ for m in doc.models]}")

    all_records = list(doc.records)
    print(f"\nExtracted {len(all_records)} records:")

    compounds = [r for r in all_records if isinstance(r, Compound)]
    melting_points = [r for r in all_records if isinstance(r, MeltingPoint)]
    apparatus = [r for r in all_records if isinstance(r, Apparatus)]

    print(f"  Compounds: {len(compounds)}")
    for i, comp in enumerate(compounds):
        print(f"    {i + 1}. {comp.serialize()}")

    print(f"  Apparatus: {len(apparatus)}")
    for i, app in enumerate(apparatus):
        print(f"    {i + 1}. {app.serialize()}")

    print(f"  MeltingPoints: {len(melting_points)}")
    bug_found = False
    for i, mp in enumerate(melting_points):
        serialized = mp.serialize()
        print(f"    {i + 1}. {serialized}")

        # Check for H2O apparatus bug
        if hasattr(mp, "apparatus") and mp.apparatus is not None:
            apparatus_data = mp.apparatus.serialize()
            print(f"      ⚠️  HAS APPARATUS: {apparatus_data}")

            if "H2O" in str(apparatus_data):
                print("      🐛 H2O APPARATUS BUG DETECTED!")
                bug_found = True

        # Check compound field too
        if hasattr(mp, "compound") and mp.compound is not None:
            compound_data = mp.compound.serialize()
            print(f"      ✅ Has compound: {compound_data}")

    return bug_found


def test_multiple_model_combinations():
    """Test different model combinations to see which triggers the bug"""
    print("\n🧪 Testing Different Model Combinations")
    print("=" * 60)

    test_text = """
    The melting point was measured as 100-102°C.
    H2O was present in the reaction mixture.
    The apparatus used was a standard melting point determination device.
    """

    model_combinations = [
        [Compound, MeltingPoint],
        [Compound, MeltingPoint, Apparatus],
        [MeltingPoint, Apparatus],
        [Compound, Apparatus],
    ]

    for i, models in enumerate(model_combinations, 1):
        print(f"\nTest {i}: Models = {[m.__name__ for m in models]}")

        doc = Document(Paragraph(test_text.strip()))
        doc.models = models

        records = list(doc.records)
        melting_points = [r for r in records if isinstance(r, MeltingPoint)]

        print(f"  Found {len(melting_points)} melting points")
        for j, mp in enumerate(melting_points):
            if hasattr(mp, "apparatus") and mp.apparatus is not None:
                if "H2O" in str(mp.apparatus.serialize()):
                    print(f"    🐛 H2O APPARATUS BUG with models: {[m.__name__ for m in models]}")
                    return True

    return False


def test_sentence_proximity():
    """Test if sentence proximity affects contextual merging"""
    print("\n📍 Testing Sentence Proximity Effects")
    print("=" * 60)

    # Test different proximities of H2O to melting point
    test_scenarios = [
        # Same sentence
        "The melting point was 100°C in H2O solution.",
        # Adjacent sentences
        "The melting point was 100°C.\nH2O was used as solvent.",
        # Separated by one sentence
        "The melting point was 100°C.\nThe reaction proceeded smoothly.\nH2O was used as solvent.",
    ]

    for i, text in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {repr(text)}")

        doc = Document(*[Paragraph(p) for p in text.split("\n")])
        doc.models = [Compound, MeltingPoint, Apparatus]

        records = list(doc.records)
        melting_points = [r for r in records if isinstance(r, MeltingPoint)]

        for mp in melting_points:
            if hasattr(mp, "apparatus") and mp.apparatus and "H2O" in str(mp.apparatus.serialize()):
                print(f"    🐛 H2O APPARATUS BUG in scenario {i}")
                return True
            else:
                print("    ✅ No H2O apparatus bug")

    return False


def main():
    print("🐛 Realistic H2O Apparatus Bug Investigation")
    print("=" * 80)
    print("Based on user report: 'H2O' appearing as apparatus in melting points")

    try:
        bug_results = []

        # Test 1: With apparatus model included
        bug_results.append(test_apparatus_model_included())

        # Test 2: Different model combinations
        bug_results.append(test_multiple_model_combinations())

        # Test 3: Sentence proximity
        bug_results.append(test_sentence_proximity())

        print("\n" + "=" * 80)
        print("🎯 REALISTIC TEST SUMMARY")
        print("=" * 80)

        if any(bug_results):
            print("❌ H2O apparatus bug reproduced!")
            print("🔍 Bug confirmed in realistic extraction scenarios")
        else:
            print("✅ No H2O apparatus bug found")
            print("💡 Bug may require specific content patterns or model states")

        # Additional debug info
        print(f"\nTest results: {bug_results}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

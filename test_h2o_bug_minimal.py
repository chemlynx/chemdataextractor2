#!/usr/bin/env python3
"""
Minimal test to reproduce the H2O apparatus bug in document processing.
Focus on the specific scenario where H2O compounds get misassigned to apparatus fields.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.doc.text import Paragraph
from chemdataextractor.doc.text import Sentence
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint


def test_minimal_h2o_bug():
    """Test the specific scenario that causes H2O apparatus bug"""
    print("🔍 Minimal H2O Apparatus Bug Test")
    print("=" * 50)

    # Create minimal document with the problematic pattern
    # This simulates finding a melting point near H2O mention
    doc = Document(
        Paragraph("The melting point was measured as 100°C. H2O was present as solvent.")
    )

    # Set models - Apparatus model is NOT included
    doc.models = [Compound, MeltingPoint]
    print(f"Document models: {[m.__name__ for m in doc.models]}")

    # Extract all records
    all_records = list(doc.records)
    print(f"\nExtracted {len(all_records)} records:")

    compounds = [r for r in all_records if isinstance(r, Compound)]
    melting_points = [r for r in all_records if isinstance(r, MeltingPoint)]

    print(f"  Compounds: {len(compounds)}")
    for i, compound in enumerate(compounds):
        print(f"    {i + 1}. {compound.serialize()}")

    print(f"  MeltingPoints: {len(melting_points)}")
    bug_found = False
    for i, mp in enumerate(melting_points):
        print(f"    {i + 1}. {mp.serialize()}")

        # Check for the apparatus bug
        if hasattr(mp, "apparatus") and mp.apparatus is not None:
            print(f"      ⚠️  HAS APPARATUS: {mp.apparatus.serialize()}")
            if hasattr(mp.apparatus, "name") and "H2O" in str(mp.apparatus.name):
                print("      🐛 H2O APPARATUS BUG FOUND!")
                bug_found = True

    return bug_found


def test_sentence_level_parsing():
    """Test at sentence level to see where the bug originates"""
    print("\n🔬 Sentence-Level Analysis")
    print("=" * 50)

    # Test individual sentences
    sentences = ["The melting point was measured as 100°C.", "H2O was present as solvent."]

    for i, sentence_text in enumerate(sentences, 1):
        print(f"\nSentence {i}: '{sentence_text}'")

        # Create sentence directly
        sent = Sentence(sentence_text)
        sent.models = [Compound, MeltingPoint]

        records = list(sent.records)
        print(f"  Records: {len(records)}")

        for j, record in enumerate(records):
            print(f"    {j + 1}. {type(record).__name__}: {record.serialize()}")

            if (
                isinstance(record, MeltingPoint)
                and hasattr(record, "apparatus")
                and record.apparatus
            ):
                print("      🐛 APPARATUS BUG IN SINGLE SENTENCE!")


def test_direct_parsing():
    """Test direct parsing without document context"""
    print("\n🎯 Direct Parser Testing")
    print("=" * 50)

    from chemdataextractor.doc.text import Sentence
    from chemdataextractor.parse.cem import CompoundParser
    from chemdataextractor.parse.mp_new import MpParser

    test_text = "The melting point was measured as 100°C in the presence of H2O."
    sent = Sentence(test_text)

    # Test compound parser
    comp_parser = CompoundParser()
    compounds = list(comp_parser.parse(sent.tagged_tokens))
    print(f"CompoundParser results: {len(compounds)} compounds")
    for comp in compounds:
        print(f"  - {comp.serialize()}")

    # Test melting point parser
    mp_parser = MpParser()
    melting_points = list(mp_parser.parse(sent.tagged_tokens))
    print(f"MpParser results: {len(melting_points)} melting points")
    for mp in melting_points:
        print(f"  - {mp.serialize()}")
        if hasattr(mp, "apparatus") and mp.apparatus:
            print(f"    🐛 APPARATUS BUG IN DIRECT PARSING: {mp.apparatus.serialize()}")


def main():
    print("🐛 Minimal H2O Apparatus Bug Investigation")
    print("=" * 80)

    try:
        # Test 1: Minimal document-level test
        bug_in_document = test_minimal_h2o_bug()

        # Test 2: Sentence-level analysis
        test_sentence_level_parsing()

        # Test 3: Direct parser testing
        test_direct_parsing()

        print("\n" + "=" * 80)
        print("🎯 MINIMAL TEST SUMMARY")
        print("=" * 80)

        if bug_in_document:
            print("❌ Bug reproduced in document-level processing")
            print("🔍 Bug occurs during document contextual merging")
        else:
            print("✅ No bug found in document processing")
            print("💡 Bug may be in specific content or parsing conditions")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

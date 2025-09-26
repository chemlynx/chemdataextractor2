#!/usr/bin/env python3
"""
Debug the document-level contextual merging bug where H2O compound
gets incorrectly merged into apparatus fields of melting points.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor.doc import Document
from chemdataextractor.doc import Paragraph
from chemdataextractor.model import Compound
from chemdataextractor.model import MeltingPoint


def test_document_level_contextual_merging():
    """Test how contextual merging works at the document level"""
    print("🔍 Testing Document-Level Contextual Merging")
    print("=" * 60)

    # Create a simple document that might reproduce the issue
    # Simulate: melting point measurement near H2O compound mention
    doc = Document(
        Paragraph("The melting point was 89-90°C. H2O was used as solvent."),
        Paragraph("Another compound had melting point 140-143°C."),
    )

    # Set up models - this should match the extraction scenario
    doc.models = [Compound, MeltingPoint]  # Note: NO Apparatus model!

    print("Document created with models: Compound, MeltingPoint")
    print("Note: Apparatus model is NOT included - this is key!")

    # Extract records
    all_records = list(doc.records)
    print(f"\nExtracted {len(all_records)} total records:")

    compounds = [r for r in all_records if isinstance(r, Compound)]
    melting_points = [r for r in all_records if isinstance(r, MeltingPoint)]

    print(f"  Compounds: {len(compounds)}")
    for i, compound in enumerate(compounds):
        print(f"    {i + 1}. {compound.serialize()}")

    print(f"  MeltingPoints: {len(melting_points)}")
    for i, mp in enumerate(melting_points):
        serialized = mp.serialize()
        print(f"    {i + 1}. {serialized}")

        # Check if apparatus field got set incorrectly
        if hasattr(mp, "apparatus") and mp.apparatus:
            print(f"        ⚠️  APPARATUS FIELD SET: {mp.apparatus.serialize()}")
            if hasattr(mp.apparatus, "name") and mp.apparatus.name == "H2O":
                print("        🐛 BUG REPRODUCED: H2O compound merged into apparatus field!")


def test_manual_contextual_merging_steps():
    """Manually test the steps that document processing goes through"""
    print("\n🔧 Testing Manual Contextual Merging Steps")
    print("=" * 60)

    # Create the records manually as they might be created during parsing
    mp = MeltingPoint(value=[89.0, 90.0], units="Celsius^(1.0)")
    h2o_compound = Compound(names=["H2O"])

    print("Before merge:")
    print(f"  MeltingPoint.apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"  MeltingPoint.compound: {getattr(mp, 'compound', None)}")

    # This is what our refactored code should do
    result = mp.merge_contextual(h2o_compound)

    print("\nAfter merge_contextual:")
    print(f"  Result: {result}")
    print(f"  MeltingPoint.apparatus: {getattr(mp, 'apparatus', None)}")
    print(f"  MeltingPoint.compound: {getattr(mp, 'compound', None)}")

    # Check for the bug
    if hasattr(mp, "apparatus") and mp.apparatus and hasattr(mp.apparatus, "name"):
        if mp.apparatus.name == "H2O":
            print("  🐛 BUG: H2O compound incorrectly merged into apparatus field!")
            return False
        else:
            print("  ✅ Apparatus field correctly set")
    elif hasattr(mp, "compound") and mp.compound and "H2O" in mp.compound.names:
        print("  ✅ H2O correctly merged into compound field")
        return True
    else:
        print("  ℹ️  No merge occurred")
        return True


def investigate_merge_logic():
    """Investigate the exact merge logic that might be causing the issue"""
    print("\n🕵️ Investigating Merge Logic")
    print("=" * 60)

    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    h2o_compound = Compound(names=["H2O"])

    print("Field analysis:")
    for field_name, field in mp.fields.items():
        print(f"  {field_name}:")
        print(f"    contextual: {getattr(field, 'contextual', False)}")
        print(f"    never_merge: {getattr(field, 'never_merge', False)}")

        if hasattr(field, "model_class"):
            print(f"    model_class: {field.model_class}")
            print(
                f"    isinstance(h2o_compound, model_class): {isinstance(h2o_compound, field.model_class)}"
            )

        if hasattr(field, "field") and hasattr(field.field, "model_class"):
            print(f"    field.field.model_class: {field.field.model_class}")

    # Test the compatibility checking functions
    print("\nCompatibility checks:")
    print(f"  _binding_compatible: {mp._binding_compatible(h2o_compound)}")
    print(f"  _compatible: {mp._compatible(h2o_compound) if hasattr(mp, '_compatible') else 'N/A'}")
    print(f"  type(h2o_compound) in type(mp).flatten(): {type(h2o_compound) in type(mp).flatten()}")


def main():
    print("🐛 Document-Level Type Safety Bug Investigation")
    print("=" * 80)

    try:
        # Test 1: Document-level processing
        test_document_level_contextual_merging()

        # Test 2: Manual step reproduction
        manual_result = test_manual_contextual_merging_steps()

        # Test 3: Logic investigation
        investigate_merge_logic()

        print("\n" + "=" * 80)
        print("🎯 INVESTIGATION SUMMARY")
        print("=" * 80)

        if manual_result:
            print("✅ Direct merge_contextual works correctly")
            print("⚠️  Bug likely occurs in document-level processing (_resolve_contextual)")
            print("💡 Investigation needed in chemdataextractor/doc/text.py")
        else:
            print("❌ Bug reproduced in direct merge_contextual")
            print("🔧 Further refactoring needed in BaseModel merge methods")

    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

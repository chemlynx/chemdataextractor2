#!/usr/bin/env python3
"""
Test to reproduce the real-world H2O apparatus bug that the user is seeing
when using the batch extract script. Focus on the actual parsing pipeline
that creates apparatus objects from H2O/water.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.doc.text import Paragraph
from chemdataextractor.model.model import Apparatus
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint


def test_sentence_apparatus_extraction():
    """Test sentence-level apparatus extraction to see if H2O/water get parsed as apparatus"""
    print("🔍 Testing Sentence-Level Apparatus Extraction")
    print("=" * 60)

    from chemdataextractor.doc.text import Sentence

    test_sentences = [
        "H2O was used as solvent.",
        "Water was used for crystallization.",
        "The melting point was measured using H2O.",
        "Apparatus included H2O bath.",
        "Standard apparatus with water cooling was used.",
        "The experiment used H2O-cooled apparatus.",
        "Water bath apparatus was employed.",
    ]

    for i, sentence_text in enumerate(test_sentences, 1):
        print(f"\nSentence {i}: '{sentence_text}'")
        sent = Sentence(sentence_text)
        sent.models = [Apparatus]  # Only look for apparatus

        apparatus_results = list(sent.records)
        print(f"  Apparatus found: {len(apparatus_results)}")

        for j, apparatus in enumerate(apparatus_results):
            print(f"    {j + 1}. {apparatus.serialize()}")

            if hasattr(apparatus, "name") and (
                "H2O" in str(apparatus.name) or "water" in str(apparatus.name).lower()
            ):
                print("    🐛 H2O/WATER PARSED AS APPARATUS!")


def test_realistic_document_scenarios():
    """Test realistic document scenarios that might trigger the bug"""
    print("\n📄 Testing Realistic Document Scenarios")
    print("=" * 60)

    scenarios = [
        # Scenario 1: H2O mentioned near apparatus
        "The melting point was determined using standard apparatus. H2O was present as solvent.",
        # Scenario 2: Water mentioned in apparatus context
        "Melting point determination was carried out using water-cooled apparatus. The value was 89-91°C.",
        # Scenario 3: H2O in experimental setup
        "The compound was heated until melting occurred at 100°C. H2O bath was used for temperature control.",
        # Scenario 4: Multiple model types present
        "The synthesized compound showed melting point 140-143°C. Standard melting point apparatus with H2O cooling was employed.",
        # Scenario 5: Water as apparatus component
        "Melting point was measured as 75-77°C using apparatus equipped with water jacket.",
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}: {scenario[:60]}...")

        doc = Document(Paragraph(scenario))
        doc.models = [Compound, MeltingPoint, Apparatus]  # All three models

        all_records = list(doc.records)
        compounds = [r for r in all_records if isinstance(r, Compound)]
        melting_points = [r for r in all_records if isinstance(r, MeltingPoint)]
        apparatus = [r for r in all_records if isinstance(r, Apparatus)]

        print(
            f"  Found: {len(compounds)} compounds, {len(melting_points)} MPs, {len(apparatus)} apparatus"
        )

        # Check for H2O/water apparatus
        for app in apparatus:
            app_data = app.serialize()
            if "H2O" in str(app_data) or "water" in str(app_data).lower():
                print(f"    🐛 H2O/WATER APPARATUS: {app_data}")

        # Check melting points for apparatus contamination
        for mp in melting_points:
            if hasattr(mp, "apparatus") and mp.apparatus:
                app_data = mp.apparatus.serialize()
                if "H2O" in str(app_data) or "water" in str(app_data).lower():
                    print(f"    🐛 MP WITH H2O/WATER APPARATUS: {app_data}")


def test_step_by_step_parsing():
    """Step through parsing to see where H2O becomes apparatus"""
    print("\n🔍 Step-by-Step Parsing Analysis")
    print("=" * 60)

    test_text = "The melting point was 89-91°C. H2O was used in the apparatus setup."

    doc = Document(Paragraph(test_text))
    doc.models = [Compound, MeltingPoint, Apparatus]

    print(f"Test text: {test_text}")
    print(f"Models: {[m.__name__ for m in doc.models]}")

    # Get sentence-level records first
    for i, sentence in enumerate(doc.sentences):
        print(f"\nSentence {i + 1}: '{sentence.text}'")
        sentence.models = [Compound, MeltingPoint, Apparatus]

        sent_records = list(sentence.records)
        print(f"  Sentence records: {len(sent_records)}")

        for j, record in enumerate(sent_records):
            print(f"    {j + 1}. {type(record).__name__}: {record.serialize()}")

            if isinstance(record, Apparatus) and (
                "H2O" in str(record.serialize()) or "water" in str(record.serialize()).lower()
            ):
                print("      🐛 H2O/WATER APPARATUS CREATED AT SENTENCE LEVEL!")

    # Now get document-level records
    print("\nDocument-level records:")
    doc_records = list(doc.records)

    for record in doc_records:
        print(f"  {type(record).__name__}: {record.serialize()}")

        if isinstance(record, MeltingPoint) and hasattr(record, "apparatus") and record.apparatus:
            app_data = record.apparatus.serialize()
            if "H2O" in str(app_data) or "water" in str(app_data).lower():
                print("    🐛 H2O/WATER CONTAMINATION IN MP APPARATUS FIELD!")


def test_contextual_merging_with_apparatus_model():
    """Test if including Apparatus model in the mix causes the bug"""
    print("\n🔄 Testing Contextual Merging with Apparatus Model")
    print("=" * 60)

    # Create records as they might be parsed
    mp = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    h2o_compound = Compound(names=["H2O"])
    h2o_apparatus = Apparatus(name="H2O")  # This might be created by apparatus parser

    print("Testing merge scenarios:")

    # Scenario 1: MP + H2O compound (should work correctly)
    mp1 = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    result1 = mp1.merge_contextual(h2o_compound)
    print("\nScenario 1: MP + H2O compound")
    print(f"  Merge result: {result1}")
    print(f"  MP after: {mp1.serialize()}")

    # Scenario 2: MP + H2O apparatus (this might be the problem)
    mp2 = MeltingPoint(value=[100.0], units="Celsius^(1.0)")
    result2 = mp2.merge_contextual(h2o_apparatus)
    print("\nScenario 2: MP + H2O apparatus")
    print(f"  Merge result: {result2}")
    print(f"  MP after: {mp2.serialize()}")

    if hasattr(mp2, "apparatus") and mp2.apparatus and "H2O" in str(mp2.apparatus.serialize()):
        print("  🐛 H2O APPARATUS CORRECTLY MERGED BUT THIS IS THE BUG SOURCE!")


def main():
    print("🐛 Real-World H2O Apparatus Bug Investigation")
    print("=" * 80)
    print("Testing actual parsing scenarios that create H2O/water apparatus")

    try:
        # Test 1: Sentence-level apparatus extraction
        test_sentence_apparatus_extraction()

        # Test 2: Realistic document scenarios
        test_realistic_document_scenarios()

        # Test 3: Step-by-step parsing
        test_step_by_step_parsing()

        # Test 4: Contextual merging with apparatus
        test_contextual_merging_with_apparatus_model()

        print("\n" + "=" * 80)
        print("🎯 REAL-WORLD BUG INVESTIGATION SUMMARY")
        print("=" * 80)
        print("This should help identify exactly where H2O/water apparatus objects are created")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

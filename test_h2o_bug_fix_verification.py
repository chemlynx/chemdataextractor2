#!/usr/bin/env python3
"""
Test to verify the H2O apparatus bug fix is working.
This tests the specific scenarios the user reported from batch extraction.
"""

import sys
sys.path.insert(0, '/home/dave/code/ChemDataExtractor2')

from chemdataextractor import Document
from chemdataextractor.doc.text import Paragraph, Sentence
from chemdataextractor.model.model import Compound, MeltingPoint, Apparatus

def test_h2o_water_blacklist():
    """Test that H2O and water are now properly blacklisted from apparatus parsing"""
    print("🔍 Testing H2O/Water Blacklist in Apparatus Parser")
    print("=" * 70)

    problematic_sentences = [
        # These were creating H2O apparatus before the fix
        "The melting point was measured using H2O.",
        "Standard apparatus with water cooling was used.",
        "The experiment used H2O for temperature control.",
        "Water was used in the apparatus setup.",
        "Measurements were taken using water bath.",
        "The reaction used DMF as solvent with heating apparatus.",
        "Analysis was performed using THF on the spectrometer.",
    ]

    print("Testing sentences that previously created solvent apparatus objects:")

    for i, sentence_text in enumerate(problematic_sentences, 1):
        print(f"\nSentence {i}: '{sentence_text}'")

        sent = Sentence(sentence_text)
        sent.models = [Apparatus]

        apparatus_results = list(sent.records)
        print(f"  Apparatus found: {len(apparatus_results)}")

        if apparatus_results:
            for j, apparatus in enumerate(apparatus_results):
                app_data = apparatus.serialize()
                print(f"    {j+1}. {app_data}")

                # Check for solvent names in apparatus
                app_name = str(app_data).lower()
                solvent_names = ['h2o', 'water', 'thf', 'dmf', 'dmso', 'acetone', 'methanol', 'ethanol', 'chloroform', 'benzene']

                for solvent in solvent_names:
                    if solvent in app_name:
                        print(f"    ⚠️  SOLVENT '{solvent}' STILL IN APPARATUS!")
                        return False
        else:
            print(f"    ✅ No apparatus detected (correct!)")

    return True

def test_document_level_melting_points():
    """Test document-level extraction to ensure no H2O apparatus contamination"""
    print("\n📄 Testing Document-Level Melting Point Extraction")
    print("=" * 70)

    test_scenarios = [
        # Scenarios that should NOT create H2O apparatus in melting points
        "The melting point of the compound was 100-102°C. H2O was used as solvent for recrystallization.",
        "Melting point determination gave 89-91°C using standard apparatus. Water cooling was employed.",
        "The synthesized material melted at 140-143°C. Measurements used H2O bath for temperature control.",
        "Melting point analysis showed 75-77°C. The apparatus included water circulation system.",
    ]

    print("Testing document scenarios that should NOT contaminate melting points:")

    bug_found = False
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {scenario[:60]}...")

        doc = Document(Paragraph(scenario))
        doc.models = [Compound, MeltingPoint, Apparatus]

        records = list(doc.records)
        melting_points = [r for r in records if isinstance(r, MeltingPoint)]

        print(f"  Found {len(melting_points)} melting points")

        for j, mp in enumerate(melting_points):
            mp_data = mp.serialize()
            print(f"    MP {j+1}: {mp_data}")

            # Check if apparatus field has H2O/water contamination
            if hasattr(mp, 'apparatus') and mp.apparatus:
                app_data = str(mp.apparatus.serialize()).lower()
                if 'h2o' in app_data or 'water' in app_data:
                    print(f"      🐛 H2O/WATER CONTAMINATION: {mp.apparatus.serialize()}")
                    bug_found = True
                else:
                    print(f"      ✅ Clean apparatus: {mp.apparatus.serialize()}")
            else:
                print(f"      ✅ No apparatus field (or H2O correctly in compound field)")

    return not bug_found

def test_legitimate_apparatus_still_work():
    """Test that legitimate apparatus detection still works after the fix"""
    print("\n🔬 Testing Legitimate Apparatus Detection Still Works")
    print("=" * 70)

    legitimate_sentences = [
        "The melting point was measured using DSC apparatus.",
        "Analysis was performed using NMR spectrometer.",
        "Standard apparatus with mercury thermometer was used.",
        "The experiment used digital melting point apparatus.",
        "Measurements were taken using Bruker spectrometer.",
    ]

    print("Testing that legitimate apparatus are still detected:")

    for i, sentence_text in enumerate(legitimate_sentences, 1):
        print(f"\nSentence {i}: '{sentence_text}'")

        sent = Sentence(sentence_text)
        sent.models = [Apparatus]

        apparatus_results = list(sent.records)
        print(f"  Apparatus found: {len(apparatus_results)}")

        if apparatus_results:
            for j, apparatus in enumerate(apparatus_results):
                print(f"    {j+1}. {apparatus.serialize()}")
                print(f"    ✅ Legitimate apparatus detected correctly")
        else:
            print(f"    ⚠️  Expected apparatus but none found")

    return len(apparatus_results) > 0

def main():
    print("🧪 H2O Apparatus Bug Fix Verification")
    print("=" * 80)
    print("Testing the apparatus parser blacklist fix for H2O/water/solvents")

    try:
        test_results = []

        # Test 1: Verify blacklist prevents solvent apparatus
        test_results.append(test_h2o_water_blacklist())

        # Test 2: Verify document-level extraction is clean
        test_results.append(test_document_level_melting_points())

        # Test 3: Verify legitimate apparatus still work
        test_results.append(test_legitimate_apparatus_still_work())

        print("\n" + "=" * 80)
        print("🎯 BUG FIX VERIFICATION RESULTS")
        print("=" * 80)

        if all(test_results):
            print("✅ ALL TESTS PASSED!")
            print("🎉 H2O apparatus bug has been FIXED!")
            print("🔧 Apparatus parser blacklist successfully prevents solvent contamination")
            print("✨ Batch extraction should now work correctly without H2O/water apparatus")
        else:
            print("❌ SOME TESTS FAILED")
            print(f"Test results: {test_results}")
            print("🔍 Further investigation needed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
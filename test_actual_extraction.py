#!/usr/bin/env python3
"""
Test extraction on actual paper to see if our refactoring fixed the H2O apparatus bug.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint
from chemdataextractor.reader import HtmlReader


def test_real_extraction():
    """Test extraction on the actual paper that showed H2O apparatus bug"""
    print("🧪 Testing Real Paper Extraction with Refactored Code")
    print("=" * 70)

    # Use a different paper to test (the original one seems to be minified JS)
    test_files = [
        "/home/dave/code/papers/D5OB00672D.html",  # From earlier work
        "/home/dave/code/papers/D4OB01848F.html",  # The one with the bug
    ]

    for test_file in test_files:
        try:
            print(f"\n📄 Testing: {test_file}")
            print("-" * 50)

            with open(test_file, "rb") as f:
                doc = Document.from_file(f, readers=[HtmlReader()])

            # Set up models (same as the bug report)
            doc.models = [Compound, MeltingPoint]
            print(f"Models: {[m.__name__ for m in doc.models]}")

            # Extract records
            compounds = [r for r in doc.records if isinstance(r, Compound)]
            melting_points = [r for r in doc.records if isinstance(r, MeltingPoint)]

            print(f"Found: {len(compounds)} compounds, {len(melting_points)} melting points")

            # Look for H2O compounds
            h2o_compounds = [
                c for c in compounds if "H2O" in c.names or "water" in str(c.names).lower()
            ]
            print(f"H2O/water compounds: {len(h2o_compounds)}")
            for compound in h2o_compounds[:3]:
                print(f"  - {compound.serialize()}")

            # Check melting points for apparatus issues
            apparatus_issues = 0
            h2o_apparatus_issues = 0

            for i, mp in enumerate(melting_points[:10]):  # Check first 10
                serialized = mp.serialize()
                print(f"  MP {i + 1}: {serialized}")

                if hasattr(mp, "apparatus") and mp.apparatus:
                    apparatus_issues += 1
                    print(f"    ⚠️  Has apparatus: {mp.apparatus.serialize()}")

                    if hasattr(mp.apparatus, "name") and "H2O" in str(mp.apparatus.name):
                        h2o_apparatus_issues += 1
                        print("    🐛 H2O APPARATUS BUG DETECTED!")

            print(f"\nSummary for {test_file}:")
            print(f"  Melting points with apparatus: {apparatus_issues}")
            print(f"  H2O apparatus issues: {h2o_apparatus_issues}")

            if h2o_apparatus_issues > 0:
                print("  ❌ Bug still present in this file")
            else:
                print("  ✅ No H2O apparatus bugs detected")

        except FileNotFoundError:
            print(f"❌ File not found: {test_file}")
        except Exception as e:
            print(f"❌ Error processing {test_file}: {e}")


def main():
    print("🔍 Testing Real Paper Extraction After Refactoring")
    print("=" * 80)
    print("This tests if the H2O apparatus bug is fixed in actual document processing")

    test_real_extraction()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Debug why compounds are still being extracted from restricted elements.
"""

import sys

sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.doc.text import Heading
from chemdataextractor.doc.text import Paragraph
from chemdataextractor.doc.text import Title
from chemdataextractor.model.model import Apparatus
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint


def debug_element_extraction():
    """Debug extraction from individual elements."""

    print("🔍 Debugging Element-Level Extraction")
    print("=" * 60)

    # Create test elements
    title = Title("Synthesis of Novel CuSO4 Complexes Using H2O Solvent")
    abstract_para = Paragraph("We report the synthesis of CuSO4 complexes using H2O as solvent.")

    # Test 1: Title with compounds enabled
    print("\nTest 1: Title with compounds enabled")
    title.models = [Compound, MeltingPoint, Apparatus]
    title_records = list(title.records)
    print(f"  Title records: {len(title_records)}")
    for record in title_records:
        print(f"    - {type(record).__name__}: {record.serialize()}")

    # Test 2: Title with compounds disabled
    print("\nTest 2: Title with compounds disabled")
    title.models = [MeltingPoint, Apparatus]  # No Compound
    title_records_disabled = list(title.records)
    print(f"  Title records (no Compound): {len(title_records_disabled)}")
    for record in title_records_disabled:
        print(f"    - {type(record).__name__}: {record.serialize()}")

    # Test 3: Abstract paragraph (should have compounds)
    print("\nTest 3: Abstract paragraph with compounds")
    abstract_para.models = [Compound, MeltingPoint, Apparatus]
    abstract_records = list(abstract_para.records)
    print(f"  Abstract records: {len(abstract_records)}")
    for record in abstract_records:
        print(f"    - {type(record).__name__}: {record.serialize()}")


def debug_document_level_merging():
    """Debug if document-level merging is causing compounds to appear."""

    print("\n🔗 Debugging Document-Level Contextual Merging")
    print("=" * 60)

    # Create document with restricted elements
    doc = Document(
        Title("Synthesis of Novel CuSO4 Complexes"),
        Paragraph("Authors: Dr. John Smith"),
        Heading("Abstract"),
        Paragraph("We synthesized CuSO4 complexes using H2O."),
    )

    # Set document models
    doc.models = [Compound, MeltingPoint, Apparatus]

    # Manually restrict models on pre-abstract elements
    title_element = doc.elements[0]
    author_element = doc.elements[1]

    print("Before restriction:")
    print(f"  Title models: {[m.__name__ for m in title_element.models]}")
    print(f"  Author models: {[m.__name__ for m in author_element.models]}")

    # Remove Compound model from pre-abstract elements
    title_element.models = [m for m in title_element.models if m != Compound]
    author_element.models = [m for m in author_element.models if m != Compound]

    print("After restriction:")
    print(f"  Title models: {[m.__name__ for m in title_element.models]}")
    print(f"  Author models: {[m.__name__ for m in author_element.models]}")

    # Extract records and see where they come from
    all_records = list(doc.records)
    compounds = [r for r in all_records if isinstance(r, Compound)]

    print("\nDocument-level extraction results:")
    print(f"  Total records: {len(all_records)}")
    print(f"  Compounds: {len(compounds)}")

    for compound in compounds:
        print(f"    - {compound.serialize()}")

    # Check individual element records
    print("\nElement-by-element breakdown:")
    for i, element in enumerate(doc.elements):
        element_records = list(element.records)
        element_compounds = [r for r in element_records if isinstance(r, Compound)]
        print(f"  Element {i} ({type(element).__name__}): {len(element_compounds)} compounds")
        for compound in element_compounds:
            print(f"    - {compound.serialize()}")


def main():
    print("🐛 Debugging Compound Restriction Issues")
    print("=" * 80)

    # Test element-level extraction
    debug_element_extraction()

    # Test document-level merging
    debug_document_level_merging()


if __name__ == "__main__":
    main()

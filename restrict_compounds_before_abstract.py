#!/usr/bin/env python3
"""
Implementation to restrict compound extraction before the abstract section.
This helps avoid extracting dates, author names, and other metadata as compounds.
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


def restrict_compounds_before_abstract(doc, include_title_compounds=False):
    """
    Restrict compound extraction to only parts of the document at or after the abstract.

    Args:
        doc: ChemDataExtractor Document instance
        include_title_compounds: If True, allow compound extraction from title

    Returns:
        None (modifies document in place)
    """

    print(f"🔍 Analyzing document with {len(doc.elements)} elements")

    # Find the abstract section
    abstract_found = False
    abstract_index = None

    for i, element in enumerate(doc.elements):
        if isinstance(element, (Heading, Title)):
            text = element.text.lower().strip()

            # Look for abstract indicators
            if any(keyword in text for keyword in ["abstract", "summary"]):
                abstract_found = True
                abstract_index = i
                print(f"📋 Found abstract at element {i}: '{element.text[:50]}...'")
                break

    if not abstract_found:
        print("⚠️  No abstract section found - will restrict compounds from first 10 elements")
        abstract_index = min(
            10, len(doc.elements)
        )  # Fallback: assume first 10 elements are pre-content

    # Configure models for each element
    pre_abstract_count = 0
    post_abstract_count = 0
    title_compound_count = 0

    for i, element in enumerate(doc.elements):
        # Get current models (preserve document-level configuration)
        current_models = list(element.models) if element.models else []

        if i < abstract_index:
            # Before abstract
            pre_abstract_count += 1

            # Special handling for title if requested
            if isinstance(element, Title) and include_title_compounds:
                # Keep compound extraction in title
                title_compound_count += 1
                print(f"📑 Title (keeping compounds): '{element.text[:50]}...'")
            else:
                # Remove compound extraction
                filtered_models = [model for model in current_models if model != Compound]
                element.models = filtered_models

                element_type = type(element).__name__
                print(
                    f"🚫 Pre-abstract {element_type}: '{element.text[:50]}...' (compounds disabled)"
                )

        else:
            # At or after abstract - allow full extraction
            post_abstract_count += 1
            # Keep original models (including Compound)
            if not current_models:
                # If no models set, use document default
                element.models = doc.models

    print("\n📊 Configuration Summary:")
    print(f"  • Pre-abstract elements: {pre_abstract_count} (compounds disabled)")
    if include_title_compounds:
        print(f"  • Title elements with compounds: {title_compound_count}")
    print(f"  • Post-abstract elements: {post_abstract_count} (full extraction)")


def test_restriction_functionality():
    """Test the restriction functionality with a sample document."""

    print("🧪 Testing Compound Restriction Before Abstract")
    print("=" * 60)

    # Create a sample document structure
    from chemdataextractor.doc.text import Heading
    from chemdataextractor.doc.text import Title

    doc = Document(
        Title("Synthesis of Novel CuSO4 Complexes Using H2O Solvent"),
        Paragraph("Authors: Dr. John Smith, Dr. Sarah Johnson"),
        Paragraph("Received: 15 March 2023; Accepted: 20 April 2023"),
        Paragraph("Keywords: copper, sulfate, CuCl2, synthesis"),
        Heading("Abstract"),
        Paragraph(
            "We report the synthesis of CuSO4 complexes using H2O as solvent. The reaction with NaCl produced interesting results."
        ),
        Heading("Introduction"),
        Paragraph(
            "Chemical synthesis of CuSO4 has been studied extensively. Previous work with FeCl3 showed similar patterns."
        ),
        Heading("Experimental"),
        Paragraph(
            "CuSO4 (99% purity) was dissolved in H2O. Addition of NaCl resulted in precipitation."
        ),
    )

    # Set up models
    doc.models = [Compound, MeltingPoint, Apparatus]
    print(f"Document models: {[m.__name__ for m in doc.models]}")

    # Test without title compound extraction
    print("\n🔬 Test 1: Restrict compounds before abstract (excluding title)")
    restrict_compounds_before_abstract(doc, include_title_compounds=False)

    # Extract and analyze
    all_records = list(doc.records)
    compounds = [r for r in all_records if isinstance(r, Compound)]

    print("\nExtraction Results:")
    print(f"  Total records: {len(all_records)}")
    print(f"  Compounds found: {len(compounds)}")

    for i, compound in enumerate(compounds, 1):
        print(f"    {i}. {compound.serialize()}")

    # Check if problematic compounds were avoided
    problematic_names = ["March", "April", "John", "Smith", "Sarah", "Johnson", "Dr"]
    found_problematic = []

    for compound in compounds:
        for name in compound.names:
            if any(prob in str(name) for prob in problematic_names):
                found_problematic.append(name)

    if found_problematic:
        print(f"⚠️  Found potentially problematic compounds: {found_problematic}")
    else:
        print("✅ No problematic author names/dates detected as compounds")


def apply_to_real_document(file_path, include_title_compounds=False):
    """Apply compound restriction to a real document file."""

    print(f"📄 Processing real document: {file_path}")
    print("=" * 60)

    try:
        # Load document
        with open(file_path, "rb") as f:
            doc = Document.from_file(f)

        print(f"Document loaded: {len(doc.elements)} elements")

        # Set models
        doc.models = [Compound, MeltingPoint, Apparatus]

        # Apply restriction
        restrict_compounds_before_abstract(doc, include_title_compounds=include_title_compounds)

        # Extract compounds
        compounds = [r for r in doc.records if isinstance(r, Compound)]

        print("\n📊 Extraction Results:")
        print(f"  Compounds found: {len(compounds)}")

        # Show first few compounds
        for i, compound in enumerate(compounds[:10], 1):
            print(f"    {i}. {compound.serialize()}")

        if len(compounds) > 10:
            print(f"    ... and {len(compounds) - 10} more")

        return compounds

    except Exception as e:
        print(f"❌ Error processing document: {e}")
        return []


def main():
    """Main function demonstrating the compound restriction functionality."""

    print("🔬 Compound Extraction Restriction Demo")
    print("=" * 80)
    print("Restricting compound extraction before abstract to avoid dates/names")

    # Test with sample document
    test_restriction_functionality()

    print("\n" + "=" * 80)
    print("💡 Usage Examples:")
    print("=" * 80)

    print("""
# Basic usage (exclude title compounds):
restrict_compounds_before_abstract(doc, include_title_compounds=False)

# Include title compounds (for chemical titles):
restrict_compounds_before_abstract(doc, include_title_compounds=True)

# Example workflow:
doc = Document.from_file('paper.html')
doc.models = [Compound, MeltingPoint, Apparatus]
restrict_compounds_before_abstract(doc, include_title_compounds=False)
compounds = [r for r in doc.records if isinstance(r, Compound)]
""")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
FIXED implementation to restrict compound extraction before the abstract section.
Handles model dependencies correctly to avoid extracting dates, author names, etc. as compounds.
"""

import sys
sys.path.insert(0, '/home/dave/code/ChemDataExtractor2')

from chemdataextractor import Document
from chemdataextractor.doc.text import Title, Heading, Paragraph, Footnote
from chemdataextractor.model.model import Compound, MeltingPoint, Apparatus

def restrict_compounds_before_abstract(doc, include_title_compounds=False):
    """
    Restrict compound extraction to only parts of the document at or after the abstract.

    IMPORTANT: This handles model dependencies correctly. Since MeltingPoint depends on
    Compound, we must exclude both MeltingPoint and Compound from pre-abstract elements.

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
            if any(keyword in text for keyword in ['abstract', 'summary']):
                abstract_found = True
                abstract_index = i
                print(f"📋 Found abstract at element {i}: '{element.text[:50]}...'")
                break

    if not abstract_found:
        print("⚠️  No abstract section found - will restrict compounds from first 10 elements")
        abstract_index = min(10, len(doc.elements))  # Fallback

    # Analyze model dependencies
    print(f"\n🔍 Analyzing model dependencies:")
    original_models = doc.models

    models_needing_compound = []
    safe_models = []

    for model in original_models:
        dependencies = list(model.flatten(include_inferred=False))
        if Compound in dependencies:
            models_needing_compound.append(model)
            print(f"  ⚠️  {model.__name__} depends on Compound: {[m.__name__ for m in dependencies]}")
        else:
            safe_models.append(model)
            print(f"  ✅ {model.__name__} is safe: {[m.__name__ for m in dependencies]}")

    print(f"\n📊 Dependency Analysis:")
    print(f"  Models requiring Compound: {[m.__name__ for m in models_needing_compound]}")
    print(f"  Models safe to use: {[m.__name__ for m in safe_models]}")

    # Configure models for each element
    pre_abstract_count = 0
    post_abstract_count = 0
    title_compound_count = 0

    for i, element in enumerate(doc.elements):
        if i < abstract_index:
            # Before abstract
            pre_abstract_count += 1

            # Special handling for title if requested
            if isinstance(element, Title) and include_title_compounds:
                # Keep all models in title (including compounds)
                title_compound_count += 1
                element.models = original_models
                print(f"📑 Title (keeping compounds): '{element.text[:50]}...'")
            else:
                # Use only models that don't depend on Compound
                element.models = safe_models

                element_type = type(element).__name__
                restricted_models = [m.__name__ for m in safe_models]
                print(f"🚫 Pre-abstract {element_type}: '{element.text[:50]}...' (models: {restricted_models})")

        else:
            # At or after abstract - allow full extraction
            post_abstract_count += 1
            element.models = original_models

    print(f"\n📊 Configuration Summary:")
    print(f"  • Pre-abstract elements: {pre_abstract_count} (restricted models)")
    if include_title_compounds:
        print(f"  • Title elements with compounds: {title_compound_count}")
    print(f"  • Post-abstract elements: {post_abstract_count} (full extraction)")

def test_fixed_restriction():
    """Test the fixed restriction functionality."""

    print("🧪 Testing FIXED Compound Restriction Before Abstract")
    print("=" * 70)

    # Create a sample document structure
    from chemdataextractor.doc.text import Paragraph, Title, Heading

    doc = Document(
        Title("Synthesis of Novel CuSO4 Complexes Using H2O Solvent"),
        Paragraph("Authors: Dr. John Smith, Dr. Sarah Johnson"),
        Paragraph("Received: 15 March 2023; Accepted: 20 April 2023"),
        Paragraph("Keywords: copper, sulfate, CuCl2, synthesis"),
        Heading("Abstract"),
        Paragraph("We report the synthesis of CuSO4 complexes using H2O as solvent. The reaction with NaCl produced interesting results."),
        Heading("Introduction"),
        Paragraph("Chemical synthesis of CuSO4 has been studied extensively. Previous work with FeCl3 showed similar patterns."),
        Heading("Experimental"),
        Paragraph("CuSO4 (99% purity) was dissolved in H2O. Addition of NaCl resulted in precipitation.")
    )

    # Set up models
    doc.models = [Compound, MeltingPoint, Apparatus]
    print(f"Document models: {[m.__name__ for m in doc.models]}")

    # Apply restriction
    print(f"\n🔬 Applying compound restriction (excluding title)...")
    restrict_compounds_before_abstract(doc, include_title_compounds=False)

    # Extract and analyze
    all_records = list(doc.records)
    compounds = [r for r in all_records if isinstance(r, Compound)]
    melting_points = [r for r in all_records if isinstance(r, MeltingPoint)]

    print(f"\n📊 Extraction Results:")
    print(f"  Total records: {len(all_records)}")
    print(f"  Compounds: {len(compounds)}")
    print(f"  Melting Points: {len(melting_points)}")

    print(f"\n🧪 Compounds found:")
    for i, compound in enumerate(compounds, 1):
        print(f"    {i}. {compound.serialize()}")

    # Check if problematic compounds were avoided
    problematic_names = ['March', 'April', 'John', 'Smith', 'Sarah', 'Johnson', 'Dr', '15', '20', '2023']
    found_problematic = []

    for compound in compounds:
        for name in compound.names:
            if any(prob in str(name) for prob in problematic_names):
                found_problematic.append(name)

    print(f"\n🎯 Quality Check:")
    if found_problematic:
        print(f"⚠️  Found potentially problematic compounds: {found_problematic}")
    else:
        print(f"✅ No problematic author names/dates detected as compounds")

    return len(found_problematic) == 0

def test_with_title_compounds():
    """Test with title compounds included."""

    print(f"\n" + "=" * 70)
    print("🧪 Testing WITH Title Compounds Included")
    print("=" * 70)

    from chemdataextractor.doc.text import Paragraph, Title, Heading

    doc = Document(
        Title("Synthesis of Novel CuSO4 Complexes"),
        Paragraph("Authors: Dr. John Smith"),
        Heading("Abstract"),
        Paragraph("We synthesized CuSO4 complexes.")
    )

    doc.models = [Compound, MeltingPoint, Apparatus]

    # Apply restriction with title compounds enabled
    restrict_compounds_before_abstract(doc, include_title_compounds=True)

    compounds = [r for r in doc.records if isinstance(r, Compound)]

    print(f"\n📊 Results with title compounds:")
    print(f"  Compounds: {len(compounds)}")
    for i, compound in enumerate(compounds, 1):
        print(f"    {i}. {compound.serialize()}")

def main():
    """Main function demonstrating the FIXED compound restriction."""

    print("🔬 FIXED Compound Extraction Restriction Demo")
    print("=" * 80)
    print("Properly handling model dependencies to restrict compounds before abstract")

    # Test the fixed implementation
    success = test_fixed_restriction()

    # Test with title compounds
    test_with_title_compounds()

    print(f"\n" + "=" * 80)
    print("🎯 SOLUTION SUMMARY")
    print("=" * 80)
    print("""
KEY INSIGHT: MeltingPoint model depends on Compound model!

PROBLEM: Setting element.models = [MeltingPoint, Apparatus] still extracts compounds
because MeltingPoint.flatten() includes Compound as a dependency.

SOLUTION: For pre-abstract elements, only use models that don't depend on Compound:
- ✅ Apparatus (no dependencies)
- ❌ MeltingPoint (depends on Compound)
- ❌ Compound (obviously)

USAGE:
restrict_compounds_before_abstract(doc, include_title_compounds=False)
""")

    return success

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Quick ChemDataExtractor2 script for extracting chemical data from RSC publication.
Focuses only on melting points to avoid BERT initialization delays.
"""

import json
import os
import sys

# Add the ChemDataExtractor2 path
sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.model.model import MeltingPoint
from chemdataextractor.reader import HtmlReader


def extract_quick_data(file_path):
    """
    Extract melting point data quickly from the RSC HTML file.

    Args:
        file_path (str): Path to the HTML file

    Returns:
        dict: Extraction results focused on melting points
    """
    print(f"🔬 Starting quick ChemDataExtractor2 analysis of: {file_path}")
    print("=" * 80)

    # Read the document
    try:
        with open(file_path, "rb") as f:
            doc = Document.from_file(f, readers=[HtmlReader()])
        print(f"✅ Successfully loaded document with {len(doc.elements)} elements")
    except Exception as e:
        print(f"❌ Error loading document: {e}")
        return {}

    # Focus only on melting points to avoid CEM initialization
    quick_models = [MeltingPoint]
    doc.models = quick_models
    print(
        f"🎯 Using {len(quick_models)} quick extraction models: {[m.__name__ for m in quick_models]}"
    )

    # Extract records
    print("\n🔍 Extracting records...")
    all_records = list(doc.records)
    print(f"📊 Found {len(all_records)} total records")

    # Organize results
    results = {
        "summary": {
            "total_records": len(all_records),
            "file_path": file_path,
            "extraction_models": [model.__name__ for model in quick_models],
        },
        "melting_points": [],
        "other_records": [],
    }

    # Categorize records
    for record in all_records:
        record_type = type(record).__name__
        serialized = record.serialize()

        if record_type == "MeltingPoint":
            results["melting_points"].append(serialized)
        else:
            results["other_records"].append({"type": record_type, "data": serialized})

    # Update summary
    results["summary"].update(
        {
            "melting_points_found": len(results["melting_points"]),
            "other_records_found": len(results["other_records"]),
        }
    )

    return results


def analyze_document_structure(file_path):
    """Analyze the structure of the document."""
    print("\n🔍 Analyzing document structure...")

    try:
        with open(file_path, "rb") as f:
            doc = Document.from_file(f, readers=[HtmlReader()])

        print(f"📄 Document has {len(doc.elements)} elements")

        # Count element types
        element_types = {}
        for element in doc.elements:
            element_type = type(element).__name__
            element_types[element_type] = element_types.get(element_type, 0) + 1

        print("\n📊 Element breakdown:")
        for element_type, count in sorted(element_types.items()):
            print(f"  {element_type}: {count}")

        # Look for experimental sections
        print("\n🧪 Looking for experimental sections...")
        experimental_elements = []
        for i, element in enumerate(doc.elements):
            if hasattr(element, "text"):
                text = element.text.lower()
                if any(
                    keyword in text
                    for keyword in [
                        "experimental",
                        "synthesis",
                        "procedure",
                        "method",
                        "mp",
                        "melting point",
                    ]
                ):
                    experimental_elements.append(
                        (i, type(element).__name__, element.text[:100] + "...")
                    )

        if experimental_elements:
            print(f"Found {len(experimental_elements)} potentially experimental elements:")
            for i, (idx, elem_type, text) in enumerate(experimental_elements[:10]):
                print(f"  {i + 1}. Element {idx} ({elem_type}): {text}")
        else:
            print("No obvious experimental sections found")

    except Exception as e:
        print(f"❌ Error analyzing document: {e}")


def print_quick_summary(results):
    """Print a quick summary of extraction results."""
    print("\n" + "=" * 80)
    print("📋 QUICK EXTRACTION SUMMARY")
    print("=" * 80)

    summary = results.get("summary", {})
    print(f"📄 File: {summary.get('file_path', 'Unknown')}")
    print(f"🔍 Total Records Found: {summary.get('total_records', 0)}")
    print(f"🧪 Models Used: {', '.join(summary.get('extraction_models', []))}")

    print("\n📊 RECORD BREAKDOWN:")
    print(f"  🌡️  Melting Points: {summary.get('melting_points_found', 0)}")
    print(f"  📦 Other Records: {summary.get('other_records_found', 0)}")


def print_melting_point_details(results):
    """Print detailed melting point results."""
    melting_points = results.get("melting_points", [])
    if melting_points:
        print(f"\n🌡️  MELTING POINTS FOUND ({len(melting_points)}):")
        for i, mp in enumerate(melting_points, 1):
            mp_data = mp.get("MeltingPoint", {})

            # Extract values
            value = mp_data.get("value", [])
            raw_value = mp_data.get("raw_value", "N/A")
            units = mp_data.get("units", mp_data.get("raw_units", "N/A"))
            compound = mp_data.get("compound", {})

            print(f"  {i}. Raw: {raw_value}, Parsed: {value}, Units: {units}")

            # Show compound information if available
            if compound:
                comp_data = compound.get("Compound", {})
                names = comp_data.get("names", [])
                labels = comp_data.get("labels", [])
                if names:
                    print(f"     Compound: {names[0]}")
                if labels:
                    print(f"     Labels: {labels}")
    else:
        print("\n🌡️  No melting points found")


def main():
    """Main execution function."""
    # Input file path
    input_file = "/home/dave/code/ChemDataExtractor2/tests/data/D5OB00672D.html"

    # Output file path
    output_file = "/home/dave/code/ChemDataExtractor2/rsc_quick_extraction_results.json"

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return

    # Analyze document structure first
    analyze_document_structure(input_file)

    # Extract data
    results = extract_quick_data(input_file)

    if not results:
        print("❌ No results obtained from extraction")
        return

    # Print summary and detailed results
    print_quick_summary(results)
    print_melting_point_details(results)

    # Save results to file
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

    print("\n" + "=" * 80)
    print("✅ QUICK EXTRACTION COMPLETE!")
    print("=" * 80)
    print(f"📊 Found {results['summary']['total_records']} total records")
    print(f"💾 Results saved to: {output_file}")

    if results["summary"]["melting_points_found"] > 0:
        print(f"\n🎯 Found {results['summary']['melting_points_found']} melting point measurements")
    else:
        print(
            "\n⚠️  No melting points detected - the document may need different parsing approaches"
        )


if __name__ == "__main__":
    main()

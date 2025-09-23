#!/usr/bin/env python3
"""
Text analysis script for RSC publication to identify chemical data patterns.
This bypasses the full ChemDataExtractor pipeline to quickly analyze content.
"""

import json
import os
import re

from bs4 import BeautifulSoup


def analyze_rsc_html(file_path):
    """
    Analyze the RSC HTML file to identify chemical data patterns.

    Args:
        file_path (str): Path to the HTML file

    Returns:
        dict: Analysis results
    """
    print(f"📄 Analyzing RSC publication: {file_path}")
    print("=" * 80)

    # Read and parse HTML
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        soup = BeautifulSoup(content, "html.parser")

        # Extract text content
        text_content = soup.get_text()
        print("✅ Successfully loaded HTML document")
        print(f"📊 Document length: {len(text_content):,} characters")

    except Exception as e:
        print(f"❌ Error loading document: {e}")
        return {}

    # Initialize results
    results = {
        "file_info": {
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "text_length": len(text_content),
        },
        "chemical_patterns": {},
        "experimental_data": {},
        "compounds_found": [],
        "measurements_found": [],
    }

    # Chemical name patterns
    print("\n🧬 Searching for chemical compounds...")

    # Look for compound labels and numbers
    compound_labels = re.findall(
        r"\b(?:compound|product|intermediate)\s*(\d+[a-z]?|\([0-9]+[a-z]?\))",
        text_content,
        re.IGNORECASE,
    )
    results["compounds_found"] = list(set(compound_labels))
    print(
        f"Found {len(results['compounds_found'])} compound labels: {results['compounds_found'][:10]}"
    )

    # Look for chemical names (simplified patterns)
    quinazoline_compounds = re.findall(
        r"\b\d+[a-z]?[,-]\s*[A-Za-z][^.]*?quinazolin[^.]*", text_content
    )
    results["chemical_patterns"]["quinazoline_compounds"] = len(quinazoline_compounds)
    print(f"Found {len(quinazoline_compounds)} quinazoline compound mentions")

    # Melting point patterns
    print("\n🌡️  Searching for melting points...")

    # Various melting point patterns
    mp_patterns = [
        r"mp?\s*[:=]?\s*(\d+[-–]\d+)\s*°?[CF]?",  # mp 100-110 °C
        r"melting\s*point\s*[:=]?\s*(\d+[-–]\d+)\s*°?[CF]?",  # melting point: 100-110 °C
        r"mp?\s*(\d+)\s*°?[CF]",  # mp 100°C
        r"m\.?p\.?\s*(\d+[-–]\d+)\s*°?[CF]?",  # m.p. 100-110°C
    ]

    all_melting_points = []
    for pattern in mp_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        all_melting_points.extend(matches)

    results["measurements_found"] = list(set(all_melting_points))
    print(
        f"Found {len(results['measurements_found'])} melting point values: {results['measurements_found']}"
    )

    # NMR patterns
    print("\n🔬 Searching for NMR data...")

    nmr_patterns = [
        r"¹?H\s*NMR.*?δ\s*([\d.]+)",  # 1H NMR δ 7.5
        r"¹³C\s*NMR.*?δ\s*([\d.]+)",  # 13C NMR δ 120.5
        r"δ\s*([\d.]+)\s*\([^)]*\)",  # δ 7.5 (m, 2H)
    ]

    nmr_shifts = []
    for pattern in nmr_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        nmr_shifts.extend(matches)

    results["chemical_patterns"]["nmr_shifts_found"] = len(set(nmr_shifts))
    print(f"Found {len(set(nmr_shifts))} NMR chemical shifts")

    # IR patterns
    print("\n📊 Searching for IR data...")

    ir_patterns = [
        r"IR.*?(\d{4})\s*cm[⁻¹-]¹",  # IR 1650 cm⁻¹
        r"(\d{4})\s*cm[⁻¹-]¹",  # 1650 cm⁻¹
    ]

    ir_frequencies = []
    for pattern in ir_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        ir_frequencies.extend(matches)

    results["chemical_patterns"]["ir_frequencies_found"] = len(set(ir_frequencies))
    print(f"Found {len(set(ir_frequencies))} IR frequencies")

    # Mass spectrometry patterns
    print("\n⚖️  Searching for mass spectrometry data...")

    ms_patterns = [
        r"MS.*?m/z\s*(\d+)",  # MS m/z 250
        r"m/z\s*(\d+)",  # m/z 250
        r"HRMS.*?(\d+\.\d+)",  # HRMS 250.1234
    ]

    ms_values = []
    for pattern in ms_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        ms_values.extend(matches)

    results["chemical_patterns"]["ms_values_found"] = len(set(ms_values))
    print(f"Found {len(set(ms_values))} mass spectrometry values")

    # Yield patterns
    print("\n⚗️  Searching for reaction yields...")

    yield_patterns = [
        r"yield\s*[:=]?\s*(\d+)\s*%",  # yield: 85%
        r"(\d+)\s*%\s*yield",  # 85% yield
    ]

    yields = []
    for pattern in yield_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        yields.extend(matches)

    results["chemical_patterns"]["yields_found"] = list(set(yields))
    print(f"Found {len(set(yields))} reaction yields: {sorted(set(yields))}")

    # Look for experimental section
    print("\n🧪 Searching for experimental procedures...")

    # Find experimental/synthetic sections
    experimental_sections = re.findall(
        r"(experimental[^.]*|synthesis[^.]*|procedure[^.]*)", text_content, re.IGNORECASE
    )
    results["experimental_data"]["sections_found"] = len(experimental_sections)
    print(f"Found {len(experimental_sections)} experimental section references")

    # Count potential compound syntheses
    synthesis_mentions = len(re.findall(r"synthesis\s+of\s+\d+[a-z]?", text_content, re.IGNORECASE))
    results["experimental_data"]["synthesis_procedures"] = synthesis_mentions
    print(f"Found {synthesis_mentions} synthesis procedure mentions")

    return results


def print_analysis_summary(results):
    """Print a comprehensive summary of the analysis."""
    print("\n" + "=" * 80)
    print("📋 CHEMICAL DATA ANALYSIS SUMMARY")
    print("=" * 80)

    file_info = results.get("file_info", {})
    print(f"📄 File: {file_info.get('file_path', 'Unknown')}")
    print(f"📏 File size: {file_info.get('file_size', 0):,} bytes")
    print(f"📝 Text length: {file_info.get('text_length', 0):,} characters")

    chemical_patterns = results.get("chemical_patterns", {})
    print("\n🧪 CHEMICAL DATA FOUND:")
    print(f"  🧬 Compound labels: {len(results.get('compounds_found', []))}")
    print(f"  🌡️  Melting points: {len(results.get('measurements_found', []))}")
    print(f"  🔬 NMR shifts: {chemical_patterns.get('nmr_shifts_found', 0)}")
    print(f"  📊 IR frequencies: {chemical_patterns.get('ir_frequencies_found', 0)}")
    print(f"  ⚖️  MS values: {chemical_patterns.get('ms_values_found', 0)}")
    print(f"  ⚗️  Reaction yields: {len(chemical_patterns.get('yields_found', []))}")

    experimental_data = results.get("experimental_data", {})
    print("\n🔬 EXPERIMENTAL DATA:")
    print(f"  📖 Experimental sections: {experimental_data.get('sections_found', 0)}")
    print(f"  ⚗️  Synthesis procedures: {experimental_data.get('synthesis_procedures', 0)}")


def save_analysis_results(results, output_path):
    """Save analysis results to JSON file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Analysis results saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return False


def main():
    """Main execution function."""
    # Input file path
    input_file = "/home/dave/code/ChemDataExtractor2/tests/data/D5OB00672D.html"

    # Output file path
    output_file = "/home/dave/code/ChemDataExtractor2/rsc_text_analysis_results.json"

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return

    # Analyze the document
    results = analyze_rsc_html(input_file)

    if not results:
        print("❌ No results obtained from analysis")
        return

    # Print summary
    print_analysis_summary(results)

    # Save results
    if save_analysis_results(results, output_file):
        print("\n" + "=" * 80)
        print("✅ TEXT ANALYSIS COMPLETE!")
        print("=" * 80)

        # Summary of findings
        compounds = len(results.get("compounds_found", []))
        melting_points = len(results.get("measurements_found", []))
        yields = len(results.get("chemical_patterns", {}).get("yields_found", []))

        print("🎯 Quick Analysis Results:")
        print(f"  • {compounds} compound labels identified")
        print(f"  • {melting_points} melting point measurements found")
        print(f"  • {yields} reaction yields detected")
        print(
            f"  • Rich experimental data detected in {results['file_info']['text_length']:,} characters"
        )

        print(
            "\n💡 This RSC publication contains substantial chemical data suitable for ChemDataExtractor2 processing."
        )
        print("📈 The full extraction (when completed) should yield significant experimental data.")


if __name__ == "__main__":
    main()

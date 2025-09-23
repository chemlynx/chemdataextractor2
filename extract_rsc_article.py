#!/usr/bin/env python3
"""
Comprehensive ChemDataExtractor2 script for extracting chemical data from RSC publication.
This script extracts compounds, yields, melting points, NMR data, mass spectra, and other experimental data.
"""

import json
import os
import sys

# Add the ChemDataExtractor2 path
sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.model.model import Apparatus
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import ElectrochemicalPotential
from chemdataextractor.model.model import FluorescenceLifetime
from chemdataextractor.model.model import GlassTransition
from chemdataextractor.model.model import InteratomicDistance
from chemdataextractor.model.model import IrSpectrum
from chemdataextractor.model.model import MeltingPoint
from chemdataextractor.model.model import NmrSpectrum
from chemdataextractor.model.model import QuantumYield
from chemdataextractor.model.model import UvvisSpectrum
from chemdataextractor.reader import HtmlReader


def extract_all_data(file_path):
    """
    Extract all available chemical data from the RSC HTML file.

    Args:
        file_path (str): Path to the HTML file

    Returns:
        dict: Comprehensive extraction results
    """
    print(f"🔬 Starting ChemDataExtractor2 analysis of: {file_path}")
    print("=" * 80)

    # Read the document
    try:
        with open(file_path, "rb") as f:
            doc = Document.from_file(f, readers=[HtmlReader()])
        print(f"✅ Successfully loaded document with {len(doc.elements)} elements")
    except Exception as e:
        print(f"❌ Error loading document: {e}")
        return {}

    # Set up all models for comprehensive extraction
    available_models = [
        Compound,
        MeltingPoint,
        IrSpectrum,
        NmrSpectrum,
        UvvisSpectrum,
        Apparatus,
        GlassTransition,
        ElectrochemicalPotential,
        FluorescenceLifetime,
        QuantumYield,
        InteratomicDistance,
    ]

    # Set models on document
    doc.models = available_models
    print(f"🎯 Using {len(available_models)} extraction models")

    # Extract all records
    print("\n🔍 Extracting records...")
    all_records = list(doc.records)
    print(f"📊 Found {len(all_records)} total records")

    # Organize results by type
    results = {
        "summary": {
            "total_records": len(all_records),
            "file_path": file_path,
            "extraction_models": [model.__name__ for model in available_models],
        },
        "compounds": [],
        "melting_points": [],
        "ir_spectra": [],
        "nmr_spectra": [],
        "uvvis_spectra": [],
        "apparatus": [],
        "glass_transitions": [],
        "electrochemical_potentials": [],
        "fluorescence_lifetimes": [],
        "quantum_yields": [],
        "interatomic_distances": [],
        "other_records": [],
    }

    # Categorize records
    for i, record in enumerate(all_records):
        record_type = type(record).__name__
        serialized = record.serialize()

        if record_type == "Compound":
            results["compounds"].append(serialized)
        elif record_type == "MeltingPoint":
            results["melting_points"].append(serialized)
        elif record_type == "IrSpectrum":
            results["ir_spectra"].append(serialized)
        elif record_type == "NmrSpectrum":
            results["nmr_spectra"].append(serialized)
        elif record_type == "UvvisSpectrum":
            results["uvvis_spectra"].append(serialized)
        elif record_type == "Apparatus":
            results["apparatus"].append(serialized)
        elif record_type == "GlassTransition":
            results["glass_transitions"].append(serialized)
        elif record_type == "ElectrochemicalPotential":
            results["electrochemical_potentials"].append(serialized)
        elif record_type == "FluorescenceLifetime":
            results["fluorescence_lifetimes"].append(serialized)
        elif record_type == "QuantumYield":
            results["quantum_yields"].append(serialized)
        elif record_type == "InteratomicDistance":
            results["interatomic_distances"].append(serialized)
        else:
            results["other_records"].append({"type": record_type, "data": serialized})

    # Update summary with counts
    results["summary"].update(
        {
            "compounds_found": len(results["compounds"]),
            "melting_points_found": len(results["melting_points"]),
            "ir_spectra_found": len(results["ir_spectra"]),
            "nmr_spectra_found": len(results["nmr_spectra"]),
            "uvvis_spectra_found": len(results["uvvis_spectra"]),
            "apparatus_found": len(results["apparatus"]),
            "glass_transitions_found": len(results["glass_transitions"]),
            "electrochemical_potentials_found": len(results["electrochemical_potentials"]),
            "fluorescence_lifetimes_found": len(results["fluorescence_lifetimes"]),
            "quantum_yields_found": len(results["quantum_yields"]),
            "interatomic_distances_found": len(results["interatomic_distances"]),
            "other_records_found": len(results["other_records"]),
        }
    )

    return results


def print_summary(results):
    """Print a comprehensive summary of extraction results."""
    print("\n" + "=" * 80)
    print("📋 EXTRACTION SUMMARY")
    print("=" * 80)

    summary = results.get("summary", {})
    print(f"📄 File: {summary.get('file_path', 'Unknown')}")
    print(f"🔍 Total Records Found: {summary.get('total_records', 0)}")
    print(f"🧪 Models Used: {', '.join(summary.get('extraction_models', []))}")

    print("\n📊 RECORD BREAKDOWN:")
    print(f"  🧬 Compounds: {summary.get('compounds_found', 0)}")
    print(f"  🌡️  Melting Points: {summary.get('melting_points_found', 0)}")
    print(f"  📊 IR Spectra: {summary.get('ir_spectra_found', 0)}")
    print(f"  🔬 NMR Spectra: {summary.get('nmr_spectra_found', 0)}")
    print(f"  🌈 UV-Vis Spectra: {summary.get('uvvis_spectra_found', 0)}")
    print(f"  🔧 Apparatus: {summary.get('apparatus_found', 0)}")
    print(f"  🌡️  Glass Transitions: {summary.get('glass_transitions_found', 0)}")
    print(f"  ⚡ Electrochemical Potentials: {summary.get('electrochemical_potentials_found', 0)}")
    print(f"  💡 Fluorescence Lifetimes: {summary.get('fluorescence_lifetimes_found', 0)}")
    print(f"  🌟 Quantum Yields: {summary.get('quantum_yields_found', 0)}")
    print(f"  📏 Interatomic Distances: {summary.get('interatomic_distances_found', 0)}")
    print(f"  📦 Other Records: {summary.get('other_records_found', 0)}")


def print_detailed_results(results):
    """Print detailed results for key categories."""
    print("\n" + "=" * 80)
    print("🔬 DETAILED EXTRACTION RESULTS")
    print("=" * 80)

    # Compounds
    compounds = results.get("compounds", [])
    if compounds:
        print(f"\n🧬 COMPOUNDS ({len(compounds)} found):")
        for i, compound in enumerate(compounds[:10], 1):  # Show first 10
            comp_data = compound.get("Compound", {})
            names = comp_data.get("names", [])
            labels = comp_data.get("labels", [])
            roles = comp_data.get("roles", [])
            print(f"  {i}. Names: {names}")
            if labels:
                print(f"     Labels: {labels}")
            if roles:
                print(f"     Roles: {roles}")

        if len(compounds) > 10:
            print(f"     ... and {len(compounds) - 10} more compounds")

    # Melting Points
    melting_points = results.get("melting_points", [])
    if melting_points:
        print(f"\n🌡️  MELTING POINTS ({len(melting_points)} found):")
        for i, mp in enumerate(melting_points[:10], 1):  # Show first 10
            mp_data = mp.get("MeltingPoint", {})
            value = mp_data.get("value", mp_data.get("raw_value", "N/A"))
            units = mp_data.get("units", mp_data.get("raw_units", "N/A"))
            compound = mp_data.get("compound", {})
            print(f"  {i}. Value: {value} {units}")
            if compound:
                comp_names = compound.get("Compound", {}).get("names", [])
                if comp_names:
                    print(f"     Compound: {comp_names[0]}")

        if len(melting_points) > 10:
            print(f"     ... and {len(melting_points) - 10} more melting points")

    # NMR Spectra
    nmr_spectra = results.get("nmr_spectra", [])
    if nmr_spectra:
        print(f"\n🔬 NMR SPECTRA ({len(nmr_spectra)} found):")
        for i, nmr in enumerate(nmr_spectra[:5], 1):  # Show first 5
            nmr_data = nmr.get("NmrSpectrum", {})
            nucleus = nmr_data.get("nucleus", "Unknown")
            solvent = nmr_data.get("solvent", "Unknown")
            peaks = nmr_data.get("peaks", [])
            print(f"  {i}. Nucleus: {nucleus}, Solvent: {solvent}")
            if peaks:
                print(f"     Peaks: {len(peaks)} found")
                # Show first few peaks
                for j, peak in enumerate(peaks[:3]):
                    shift = peak.get("shift", "N/A")
                    print(f"       δ {shift}")

        if len(nmr_spectra) > 5:
            print(f"     ... and {len(nmr_spectra) - 5} more NMR spectra")

    # IR Spectra
    ir_spectra = results.get("ir_spectra", [])
    if ir_spectra:
        print(f"\n📊 IR SPECTRA ({len(ir_spectra)} found):")
        for i, ir in enumerate(ir_spectra[:5], 1):  # Show first 5
            ir_data = ir.get("IrSpectrum", {})
            peaks = ir_data.get("peaks", [])
            print(f"  {i}. IR Spectrum with {len(peaks)} peaks")
            # Show first few peaks
            for j, peak in enumerate(peaks[:3]):
                value = peak.get("value", "N/A")
                units = peak.get("units", "cm⁻¹")
                print(f"       {value} {units}")

    # Apparatus
    apparatus_list = results.get("apparatus", [])
    if apparatus_list:
        print(f"\n🔧 APPARATUS ({len(apparatus_list)} found):")
        for i, app in enumerate(apparatus_list[:5], 1):  # Show first 5
            app_data = app.get("Apparatus", {})
            print(f"  {i}. Apparatus: {app_data}")

    # Glass Transitions
    glass_transitions = results.get("glass_transitions", [])
    if glass_transitions:
        print(f"\n🌡️  GLASS TRANSITIONS ({len(glass_transitions)} found):")
        for i, gt in enumerate(glass_transitions[:5], 1):  # Show first 5
            gt_data = gt.get("GlassTransition", {})
            value = gt_data.get("value", "N/A")
            units = gt_data.get("units", "N/A")
            print(f"  {i}. Tg: {value} {units}")

    # Quantum Yields
    quantum_yields = results.get("quantum_yields", [])
    if quantum_yields:
        print(f"\n🌟 QUANTUM YIELDS ({len(quantum_yields)} found):")
        for i, qy in enumerate(quantum_yields[:5], 1):  # Show first 5
            qy_data = qy.get("QuantumYield", {})
            value = qy_data.get("value", "N/A")
            units = qy_data.get("units", "N/A")
            print(f"  {i}. Quantum Yield: {value} {units}")

    # Other records
    other_records = results.get("other_records", [])
    if other_records:
        print(f"\n📦 OTHER RECORDS ({len(other_records)} found):")
        record_types = {}
        for record in other_records:
            record_type = record.get("type", "Unknown")
            record_types[record_type] = record_types.get(record_type, 0) + 1

        for record_type, count in record_types.items():
            print(f"  {record_type}: {count}")


def save_results_to_file(results, output_path):
    """Save extraction results to JSON file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Main execution function."""
    # Input file path
    input_file = "/home/dave/code/ChemDataExtractor2/tests/data/D5OB00672D.html"

    # Output file path
    output_file = "/home/dave/code/ChemDataExtractor2/rsc_extraction_results.json"

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return

    # Extract data
    results = extract_all_data(input_file)

    if not results:
        print("❌ No results obtained from extraction")
        return

    # Print summary and detailed results
    print_summary(results)
    print_detailed_results(results)

    # Save results to file
    save_results_to_file(results, output_file)

    print("\n" + "=" * 80)
    print("✅ EXTRACTION COMPLETE!")
    print("=" * 80)
    print(f"📊 Found {results['summary']['total_records']} total records")
    print(f"💾 Results saved to: {output_file}")
    print("\n🎯 Key findings:")
    if results["summary"]["compounds_found"] > 0:
        print(f"  • {results['summary']['compounds_found']} chemical compounds identified")
    if results["summary"]["melting_points_found"] > 0:
        print(f"  • {results['summary']['melting_points_found']} melting point measurements")
    if results["summary"]["nmr_spectra_found"] > 0:
        print(f"  • {results['summary']['nmr_spectra_found']} NMR spectra")
    if results["summary"]["ir_spectra_found"] > 0:
        print(f"  • {results['summary']['ir_spectra_found']} IR spectra")
    if results["summary"]["quantum_yields_found"] > 0:
        print(f"  • {results['summary']['quantum_yields_found']} quantum yields")
    if results["summary"]["apparatus_found"] > 0:
        print(f"  • {results['summary']['apparatus_found']} apparatus entries")


if __name__ == "__main__":
    main()

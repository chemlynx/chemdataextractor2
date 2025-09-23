#!/usr/bin/env python3
"""
Focused ChemDataExtractor2 script for extracting key chemical data from RSC publication.
Focuses on compounds, melting points, and NMR data for faster processing.
"""

import json
import os
import sys
from pathlib import Path

# Add the ChemDataExtractor2 path
sys.path.insert(0, '/home/dave/code/ChemDataExtractor2')

from chemdataextractor import Document
from chemdataextractor.model.model import Compound, MeltingPoint, NmrSpectrum
from chemdataextractor.reader import HtmlReader


def extract_focused_data(file_path):
    """
    Extract focused chemical data from the RSC HTML file.

    Args:
        file_path (str): Path to the HTML file

    Returns:
        dict: Extraction results focused on key data types
    """
    print(f"🔬 Starting focused ChemDataExtractor2 analysis of: {file_path}")
    print("=" * 80)

    # Read the document
    try:
        with open(file_path, 'rb') as f:
            doc = Document.from_file(f, readers=[HtmlReader()])
        print(f"✅ Successfully loaded document with {len(doc.elements)} elements")
    except Exception as e:
        print(f"❌ Error loading document: {e}")
        return {}

    # Focus on key models for faster processing
    key_models = [Compound, MeltingPoint, NmrSpectrum]
    doc.models = key_models
    print(f"🎯 Using {len(key_models)} key extraction models: {[m.__name__ for m in key_models]}")

    # Extract records
    print("\n🔍 Extracting records...")
    all_records = list(doc.records)
    print(f"📊 Found {len(all_records)} total records")

    # Organize results
    results = {
        'summary': {
            'total_records': len(all_records),
            'file_path': file_path,
            'extraction_models': [model.__name__ for model in key_models]
        },
        'compounds': [],
        'melting_points': [],
        'nmr_spectra': [],
        'other_records': []
    }

    # Categorize records
    for record in all_records:
        record_type = type(record).__name__
        serialized = record.serialize()

        if record_type == 'Compound':
            results['compounds'].append(serialized)
        elif record_type == 'MeltingPoint':
            results['melting_points'].append(serialized)
        elif record_type == 'NmrSpectrum':
            results['nmr_spectra'].append(serialized)
        else:
            results['other_records'].append({
                'type': record_type,
                'data': serialized
            })

    # Update summary
    results['summary'].update({
        'compounds_found': len(results['compounds']),
        'melting_points_found': len(results['melting_points']),
        'nmr_spectra_found': len(results['nmr_spectra']),
        'other_records_found': len(results['other_records'])
    })

    return results


def print_focused_summary(results):
    """Print a focused summary of extraction results."""
    print("\n" + "=" * 80)
    print("📋 FOCUSED EXTRACTION SUMMARY")
    print("=" * 80)

    summary = results.get('summary', {})
    print(f"📄 File: {summary.get('file_path', 'Unknown')}")
    print(f"🔍 Total Records Found: {summary.get('total_records', 0)}")
    print(f"🧪 Models Used: {', '.join(summary.get('extraction_models', []))}")

    print(f"\n📊 RECORD BREAKDOWN:")
    print(f"  🧬 Compounds: {summary.get('compounds_found', 0)}")
    print(f"  🌡️  Melting Points: {summary.get('melting_points_found', 0)}")
    print(f"  🔬 NMR Spectra: {summary.get('nmr_spectra_found', 0)}")
    print(f"  📦 Other Records: {summary.get('other_records_found', 0)}")


def print_detailed_focused_results(results):
    """Print detailed results for key categories."""
    print("\n" + "=" * 80)
    print("🔬 DETAILED EXTRACTION RESULTS")
    print("=" * 80)

    # Compounds
    compounds = results.get('compounds', [])
    if compounds:
        print(f"\n🧬 COMPOUNDS ({len(compounds)} found):")
        for i, compound in enumerate(compounds[:15], 1):  # Show first 15
            comp_data = compound.get('Compound', {})
            names = comp_data.get('names', [])
            labels = comp_data.get('labels', [])
            roles = comp_data.get('roles', [])

            print(f"  {i}. Names: {names}")
            if labels:
                print(f"     Labels: {labels}")
            if roles:
                print(f"     Roles: {roles}")

        if len(compounds) > 15:
            print(f"     ... and {len(compounds) - 15} more compounds")

    # Melting Points
    melting_points = results.get('melting_points', [])
    if melting_points:
        print(f"\n🌡️  MELTING POINTS ({len(melting_points)} found):")
        for i, mp in enumerate(melting_points[:15], 1):  # Show first 15
            mp_data = mp.get('MeltingPoint', {})
            value = mp_data.get('value', mp_data.get('raw_value', 'N/A'))
            units = mp_data.get('units', mp_data.get('raw_units', 'N/A'))
            compound = mp_data.get('compound', {})

            print(f"  {i}. Value: {value} {units}")
            if compound:
                comp_names = compound.get('Compound', {}).get('names', [])
                if comp_names:
                    print(f"     Compound: {comp_names[0]}")

        if len(melting_points) > 15:
            print(f"     ... and {len(melting_points) - 15} more melting points")

    # NMR Spectra
    nmr_spectra = results.get('nmr_spectra', [])
    if nmr_spectra:
        print(f"\n🔬 NMR SPECTRA ({len(nmr_spectra)} found):")
        for i, nmr in enumerate(nmr_spectra[:10], 1):  # Show first 10
            nmr_data = nmr.get('NmrSpectrum', {})
            nucleus = nmr_data.get('nucleus', 'Unknown')
            solvent = nmr_data.get('solvent', 'Unknown')
            peaks = nmr_data.get('peaks', [])

            print(f"  {i}. Nucleus: {nucleus}, Solvent: {solvent}")
            if peaks:
                print(f"     Peaks: {len(peaks)} found")
                # Show first few peaks
                for j, peak in enumerate(peaks[:3]):
                    shift = peak.get('shift', 'N/A')
                    multiplicity = peak.get('multiplicity', 'N/A')
                    print(f"       δ {shift} ({multiplicity})")

        if len(nmr_spectra) > 10:
            print(f"     ... and {len(nmr_spectra) - 10} more NMR spectra")

    # Other records
    other_records = results.get('other_records', [])
    if other_records:
        print(f"\n📦 OTHER RECORDS ({len(other_records)} found):")
        record_types = {}
        for record in other_records:
            record_type = record.get('type', 'Unknown')
            record_types[record_type] = record_types.get(record_type, 0) + 1

        for record_type, count in record_types.items():
            print(f"  {record_type}: {count}")


def save_focused_results(results, output_path):
    """Save extraction results to JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return False


def main():
    """Main execution function."""
    # Input file path
    input_file = "/home/dave/code/ChemDataExtractor2/tests/data/D5OB00672D.html"

    # Output file path
    output_file = "/home/dave/code/ChemDataExtractor2/rsc_focused_extraction_results.json"

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return

    # Extract data
    results = extract_focused_data(input_file)

    if not results:
        print("❌ No results obtained from extraction")
        return

    # Print summary and detailed results
    print_focused_summary(results)
    print_detailed_focused_results(results)

    # Save results to file
    if save_focused_results(results, output_file):
        print("\n" + "=" * 80)
        print("✅ FOCUSED EXTRACTION COMPLETE!")
        print("=" * 80)
        print(f"📊 Found {results['summary']['total_records']} total records")
        print(f"💾 Results saved to: {output_file}")

        print("\n🎯 Key findings:")
        if results['summary']['compounds_found'] > 0:
            print(f"  • {results['summary']['compounds_found']} chemical compounds identified")
        if results['summary']['melting_points_found'] > 0:
            print(f"  • {results['summary']['melting_points_found']} melting point measurements")
        if results['summary']['nmr_spectra_found'] > 0:
            print(f"  • {results['summary']['nmr_spectra_found']} NMR spectra")
    else:
        print("❌ Failed to save results")


if __name__ == "__main__":
    main()
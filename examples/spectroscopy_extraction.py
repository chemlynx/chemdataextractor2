#!/usr/bin/env python3
"""
Spectroscopy Data Extraction Examples

This module demonstrates how to extract spectroscopic data from chemical
literature using ChemDataExtractor2. Examples include IR, NMR, UV-Vis,
and mass spectrometry data extraction.

Usage:
    python spectroscopy_extraction.py

Requirements:
    - ChemDataExtractor2 installed
    - Sample documents in test data directory
"""

import logging
from pathlib import Path
from typing import Dict, List, Any

from chemdataextractor.doc import Document
from chemdataextractor.model import IrSpectrum, NmrSpectrum, UvvisSpectrum, MassSpectrum, Compound


# Configure logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def extract_ir_spectra_example():
    """Extract IR spectroscopy data from text."""
    print("=== IR Spectrum Extraction ===")
    
    text = """
    The infrared spectrum of benzene shows characteristic peaks at 3030 cm-1 (C-H stretch),
    1480 cm-1 and 1450 cm-1 (C=C aromatic stretch), and 674 cm-1 (C-H bend).
    For toluene, IR peaks appear at 3028, 2920 cm-1 (C-H), 1604, 1496 cm-1 (aromatic C=C),
    and 729 cm-1 (mono-substituted benzene).
    """
    
    doc = Document(text)
    
    # Extract all IR spectra records
    ir_records = []
    for record in doc.records:
        if hasattr(record, 'ir_spectra') and record.ir_spectra:
            ir_records.extend(record.ir_spectra)
    
    print(f"Found {len(ir_records)} IR spectrum records")
    
    for i, spectrum in enumerate(ir_records, 1):
        print(f"\nIR Spectrum {i}:")
        if hasattr(spectrum, 'peaks') and spectrum.peaks:
            print(f"  Peaks: {spectrum.peaks}")
        if hasattr(spectrum, 'compound') and spectrum.compound:
            print(f"  Compound: {spectrum.compound}")
    
    return ir_records


def extract_nmr_spectra_example():
    """Extract NMR spectroscopy data from text."""
    print("\n=== NMR Spectrum Extraction ===")
    
    text = """
    The 1H NMR spectrum (400 MHz, CDCl3) of compound 1 shows signals at
    δ 7.25 ppm (m, 5H, aromatic), 4.15 ppm (q, 2H, CH2), and 1.28 ppm (t, 3H, CH3).
    The 13C NMR (100 MHz, CDCl3) displays peaks at δ 137.2, 128.5, 127.8, 
    and 127.1 ppm (aromatic carbons), 65.3 ppm (CH2), and 14.2 ppm (CH3).
    """
    
    doc = Document(text)
    
    # Extract NMR records
    nmr_records = []
    for record in doc.records:
        if hasattr(record, 'nmr_spectra') and record.nmr_spectra:
            nmr_records.extend(record.nmr_spectra)
    
    print(f"Found {len(nmr_records)} NMR spectrum records")
    
    for i, spectrum in enumerate(nmr_records, 1):
        print(f"\nNMR Spectrum {i}:")
        if hasattr(spectrum, 'nucleus') and spectrum.nucleus:
            print(f"  Nucleus: {spectrum.nucleus}")
        if hasattr(spectrum, 'frequency') and spectrum.frequency:
            print(f"  Frequency: {spectrum.frequency}")
        if hasattr(spectrum, 'solvent') and spectrum.solvent:
            print(f"  Solvent: {spectrum.solvent}")
        if hasattr(spectrum, 'peaks') and spectrum.peaks:
            print(f"  Peaks: {spectrum.peaks[:3]}...")  # Show first 3 peaks
    
    return nmr_records


def extract_uvvis_spectra_example():
    """Extract UV-Vis spectroscopy data from text."""
    print("\n=== UV-Vis Spectrum Extraction ===")
    
    text = """
    The UV-Vis absorption spectrum of the ruthenium complex in acetonitrile
    shows λmax at 285 nm (ε = 15,400 M-1 cm-1) and 454 nm (ε = 8,900 M-1 cm-1).
    The organic dye exhibits absorption maxima at 520 nm and 680 nm in methanol.
    """
    
    doc = Document(text)
    
    # Extract UV-Vis records
    uvvis_records = []
    for record in doc.records:
        if hasattr(record, 'uvvis_spectra') and record.uvvis_spectra:
            uvvis_records.extend(record.uvvis_spectra)
    
    print(f"Found {len(uvvis_records)} UV-Vis spectrum records")
    
    for i, spectrum in enumerate(uvvis_records, 1):
        print(f"\nUV-Vis Spectrum {i}:")
        if hasattr(spectrum, 'lambda_max') and spectrum.lambda_max:
            print(f"  λmax: {spectrum.lambda_max}")
        if hasattr(spectrum, 'extinction') and spectrum.extinction:
            print(f"  Extinction coefficient: {spectrum.extinction}")
        if hasattr(spectrum, 'solvent') and spectrum.solvent:
            print(f"  Solvent: {spectrum.solvent}")
    
    return uvvis_records


def extract_mass_spectra_example():
    """Extract mass spectrometry data from text."""
    print("\n=== Mass Spectrum Extraction ===")
    
    text = """
    Mass spectrometry (ESI-MS) of the synthesized compound showed [M+H]+ at m/z 245.1,
    [M+Na]+ at m/z 267.1, and fragmentation peaks at m/z 217.1 (loss of CO),
    m/z 189.1 (loss of C2H4O), and m/z 161.1 (base peak).
    The molecular ion peak appears at m/z 244.1 with isotope pattern consistent
    with C15H12N2O molecular formula.
    """
    
    doc = Document(text)
    
    # Extract mass spectra records
    ms_records = []
    for record in doc.records:
        if hasattr(record, 'mass_spectra') and record.mass_spectra:
            ms_records.extend(record.mass_spectra)
    
    print(f"Found {len(ms_records)} mass spectrum records")
    
    for i, spectrum in enumerate(ms_records, 1):
        print(f"\nMass Spectrum {i}:")
        if hasattr(spectrum, 'technique') and spectrum.technique:
            print(f"  Technique: {spectrum.technique}")
        if hasattr(spectrum, 'peaks') and spectrum.peaks:
            print(f"  Peaks: {spectrum.peaks}")
        if hasattr(spectrum, 'molecular_ion') and spectrum.molecular_ion:
            print(f"  Molecular ion: {spectrum.molecular_ion}")
    
    return ms_records


def multi_technique_analysis():
    """Demonstrate comprehensive spectroscopic characterization."""
    print("\n=== Multi-Technique Spectroscopic Analysis ===")
    
    text = """
    Compound 2: The 1H NMR (500 MHz, DMSO-d6) spectrum shows δ 8.45 ppm (s, 1H, NH),
    7.85-7.82 ppm (m, 2H, Ar-H), and 7.45-7.41 ppm (m, 3H, Ar-H).
    The IR spectrum (KBr) exhibits peaks at 3285 cm-1 (N-H), 1685 cm-1 (C=O),
    and 1598, 1485 cm-1 (aromatic C=C). UV-Vis (methanol): λmax 295 nm (ε = 12,500 M-1 cm-1).
    ESI-MS: [M+H]+ m/z 198.1, fragmentation at m/z 170.1 (loss of CO).
    """
    
    doc = Document(text)
    records = doc.records
    
    print(f"Total records extracted: {len(records)}")
    
    # Analyze spectroscopic data comprehensively
    spectral_data = {
        'compounds': [],
        'nmr_spectra': [],
        'ir_spectra': [],
        'uvvis_spectra': [],
        'mass_spectra': []
    }
    
    for record in records:
        # Group related spectroscopic data by compound
        if hasattr(record, 'compound') and record.compound:
            spectral_data['compounds'].append(record.compound)
        
        # Extract different types of spectra
        for spectrum_type in ['nmr_spectra', 'ir_spectra', 'uvvis_spectra', 'mass_spectra']:
            if hasattr(record, spectrum_type):
                spectra = getattr(record, spectrum_type)
                if spectra:
                    spectral_data[spectrum_type].extend(spectra)
    
    # Display comprehensive analysis
    print("\nSpectroscopic Summary:")
    for data_type, data_list in spectral_data.items():
        if data_list:
            print(f"  {data_type.replace('_', ' ').title()}: {len(data_list)} entries")
    
    return spectral_data


def spectral_data_validation():
    """Validate and quality-check extracted spectroscopic data."""
    print("\n=== Spectroscopic Data Validation ===")
    
    text = """
    The compound shows 1H NMR signals at 7.25 ppm (incorrect assignment),
    IR peak at 5000 cm-1 (unrealistic frequency), and UV-Vis λmax at 1200 nm
    (likely NIR region). Mass spectrum [M+H]+ at m/z 50.5 (suspicious fractional mass).
    """
    
    doc = Document(text)
    
    validation_results = {
        'valid_data': [],
        'suspicious_data': [],
        'errors': []
    }
    
    for record in doc.records:
        # Validate NMR data
        if hasattr(record, 'nmr_spectra') and record.nmr_spectra:
            for spectrum in record.nmr_spectra:
                if hasattr(spectrum, 'peaks') and spectrum.peaks:
                    for peak in spectrum.peaks:
                        if hasattr(peak, 'shift') and peak.shift:
                            shift_val = peak.shift
                            # Basic validation for 1H NMR chemical shifts
                            if 0 <= shift_val <= 15:
                                validation_results['valid_data'].append(f"1H NMR: {shift_val} ppm")
                            else:
                                validation_results['suspicious_data'].append(f"1H NMR: {shift_val} ppm (unusual)")
        
        # Validate IR data
        if hasattr(record, 'ir_spectra') and record.ir_spectra:
            for spectrum in record.ir_spectra:
                if hasattr(spectrum, 'peaks') and spectrum.peaks:
                    for peak in spectrum.peaks:
                        if hasattr(peak, 'frequency') and peak.frequency:
                            freq_val = peak.frequency
                            # Basic validation for IR frequencies
                            if 400 <= freq_val <= 4000:
                                validation_results['valid_data'].append(f"IR: {freq_val} cm-1")
                            else:
                                validation_results['suspicious_data'].append(f"IR: {freq_val} cm-1 (out of range)")
    
    # Display validation results
    print("Validation Results:")
    for category, data_list in validation_results.items():
        if data_list:
            print(f"\n{category.replace('_', ' ').title()}:")
            for item in data_list:
                print(f"  - {item}")
    
    return validation_results


def export_spectral_data(spectral_data: Dict[str, List[Any]], output_dir: Path):
    """Export extracted spectroscopic data to various formats."""
    print(f"\n=== Exporting Spectral Data to {output_dir} ===")
    
    output_dir.mkdir(exist_ok=True)
    
    # Export to JSON
    import json
    json_file = output_dir / "spectral_data.json"
    
    # Serialize the data (convert complex objects to dictionaries)
    serializable_data = {}
    for key, value_list in spectral_data.items():
        serializable_data[key] = []
        for item in value_list:
            if hasattr(item, 'serialize'):
                serializable_data[key].append(item.serialize())
            else:
                serializable_data[key].append(str(item))
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, indent=2, ensure_ascii=False)
    
    print(f"  JSON export: {json_file}")
    
    # Export to CSV for tabular data
    import csv
    csv_file = output_dir / "nmr_data.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Spectrum_Type', 'Nucleus', 'Frequency', 'Solvent', 'Peak_Count'])
        
        for spectrum in spectral_data.get('nmr_spectra', []):
            writer.writerow([
                'NMR',
                getattr(spectrum, 'nucleus', 'Unknown'),
                getattr(spectrum, 'frequency', 'Unknown'),
                getattr(spectrum, 'solvent', 'Unknown'),
                len(getattr(spectrum, 'peaks', []))
            ])
    
    print(f"  CSV export: {csv_file}")
    
    # Export summary report
    report_file = output_dir / "spectral_summary.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Spectroscopic Data Extraction Summary\n")
        f.write("=" * 40 + "\n\n")
        
        for data_type, data_list in spectral_data.items():
            f.write(f"{data_type.replace('_', ' ').title()}: {len(data_list)} records\n")
        
        f.write("\nDetailed Analysis:\n")
        f.write("-" * 20 + "\n")
        # Add more detailed analysis here
    
    print(f"  Summary report: {report_file}")


def main():
    """Run all spectroscopy extraction examples."""
    print("ChemDataExtractor2 - Spectroscopy Data Extraction Examples")
    print("=" * 60)
    
    try:
        # Run individual extraction examples
        ir_data = extract_ir_spectra_example()
        nmr_data = extract_nmr_spectra_example()
        uvvis_data = extract_uvvis_spectra_example()
        ms_data = extract_mass_spectra_example()
        
        # Run comprehensive analysis
        comprehensive_data = multi_technique_analysis()
        
        # Validate extracted data
        validation_results = spectral_data_validation()
        
        # Export results
        output_dir = Path("spectral_extraction_results")
        export_spectral_data(comprehensive_data, output_dir)
        
        print("\n" + "=" * 60)
        print("Spectroscopy extraction examples completed successfully!")
        print(f"Results exported to: {output_dir.absolute()}")
        
    except Exception as e:
        logger.error(f"Error during spectroscopy extraction: {e}")
        raise


if __name__ == "__main__":
    main()
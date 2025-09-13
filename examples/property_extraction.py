#!/usr/bin/env python3
"""
Chemical Property Extraction Examples for ChemDataExtractor2

This script demonstrates extracting specific chemical properties like melting points,
boiling points, solubility, and other physical/chemical properties from documents.
"""

import json
from collections import defaultdict

from chemdataextractor import Document
from chemdataextractor.model.model import BoilingPoint
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint
from chemdataextractor.model.units.temperature import Celsius


def melting_point_extraction():
    """Demonstrate comprehensive melting point extraction."""
    print("=== Melting Point Extraction ===\n")

    # Sample text with various melting point formats
    mp_text = """
    Physical Properties of Organic Compounds

    Compound 1: Benzene
    The melting point of benzene was determined to be 5.5°C using differential scanning calorimetry.
    This value is consistent with literature reports of 5.5 ± 0.1°C.

    Compound 2: Para-xylene
    Para-xylene exhibits a melting point of 13.2°C (286.35 K). The compound was purified
    by recrystallization before measurement.

    Compound 3: Naphthalene
    Naphthalene: mp 80.2-80.8°C (range due to impurities)

    Compound 4: Anthracene
    The melting point was found to be 218°C, significantly higher than expected.

    Table 1: Melting Points of Aromatic Compounds
    Compound    | Melting Point (°C) | Purity (%)
    Toluene     | -95.0              | 99.8
    Styrene     | -30.6              | 99.5
    Phenol      | 40.9               | 99.9
    """

    doc = Document(mp_text)
    records = doc.records

    print("1. All extracted records:")
    record_counts = defaultdict(int)
    for record in records:
        record_counts[record.__class__.__name__] += 1

    for record_type, count in sorted(record_counts.items()):
        print(f"   {record_type}: {count}")

    print("\n2. Detailed melting point analysis:")
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]

    for i, mp in enumerate(melting_points, 1):
        print(f"\n   Melting Point {i}:")
        print(f"     Raw text: '{mp.raw_value}' '{mp.raw_units}'")

        if mp.value:
            if len(mp.value) == 1:
                print(f"     Parsed value: {mp.value[0]}°C")
            elif len(mp.value) == 2:
                print(f"     Parsed range: {mp.value[0]}-{mp.value[1]}°C")
        else:
            print("     Parsed value: Could not parse")

        if mp.units:
            print(f"     Units: {mp.units}")

        if mp.error:
            print(f"     Error/uncertainty: ±{mp.error}")

    print("\n3. Compound-melting point associations:")
    compounds = [r for r in records if isinstance(r, Compound)]

    for compound in compounds:
        if compound.names:
            print(f"\n   {compound.names[0]}:")

            # Check if compound has associated melting point
            if hasattr(compound, "melting_point") and compound.melting_point:
                mp = compound.melting_point
                if mp.value and mp.units:
                    print(f"     Associated MP: {mp.value[0]} {mp.units}")
            else:
                print("     No associated melting point found")

    print("\n" + "-" * 50 + "\n")


def multi_property_extraction():
    """Demonstrate extraction of multiple property types."""
    print("=== Multi-Property Extraction ===\n")

    comprehensive_text = """
    Comprehensive Analysis of Benzene Derivatives

    1. Benzene (C6H6)
    Melting point: 5.5°C
    Boiling point: 80.1°C
    Density: 0.879 g/mL at 20°C
    Solubility: slightly soluble in water, miscible with organic solvents

    2. Toluene (C7H8)
    Physical properties:
    - Melting point: -95.0°C
    - Boiling point: 110.6°C
    - Density: 0.867 g/cm³
    - Solubility: insoluble in water, soluble in ethanol and ether

    3. Phenol (C6H5OH)
    Mp: 40.9°C
    Bp: 181.7°C
    The compound shows high solubility in water due to hydrogen bonding.

    Spectroscopic Data:
    Benzene IR: 3030, 1480, 1450 cm⁻¹
    Toluene ¹H NMR (CDCl₃): δ 7.2 (5H, aromatic), 2.3 (3H, CH₃)
    """

    doc = Document(comprehensive_text)
    records = doc.records

    print("1. Property distribution:")
    property_types = {
        "MeltingPoint": [],
        "BoilingPoint": [],
        "Density": [],
        "Solubility": [],
        "IrSpectrum": [],
        "NmrSpectrum": [],
        "Compound": [],
    }

    for record in records:
        record_type = record.__class__.__name__
        if record_type in property_types:
            property_types[record_type].append(record)

    for prop_type, records_list in property_types.items():
        print(f"   {prop_type}: {len(records_list)}")

    print("\n2. Detailed property analysis:")

    # Melting Points
    if property_types["MeltingPoint"]:
        print("\n   Melting Points:")
        for mp in property_types["MeltingPoint"]:
            value_str = f"{mp.value[0]}°C" if mp.value else "N/A"
            print(f"     - {value_str} (raw: '{mp.raw_value} {mp.raw_units}')")

    # Boiling Points
    if property_types["BoilingPoint"]:
        print("\n   Boiling Points:")
        for bp in property_types["BoilingPoint"]:
            value_str = f"{bp.value[0]}°C" if bp.value else "N/A"
            print(f"     - {value_str} (raw: '{bp.raw_value} {bp.raw_units}')")

    # IR Spectra
    if property_types["IrSpectrum"]:
        print("\n   IR Spectra:")
        for ir in property_types["IrSpectrum"]:
            print(f"     - Raw data: '{getattr(ir, 'raw_value', 'N/A')}'")

    # NMR Spectra
    if property_types["NmrSpectrum"]:
        print("\n   NMR Spectra:")
        for nmr in property_types["NmrSpectrum"]:
            print(f"     - Raw data: '{getattr(nmr, 'raw_value', 'N/A')}'")

    print("\n3. Compound-property mapping:")
    compounds = property_types["Compound"]

    for compound in compounds:
        if compound.names:
            name = compound.names[0]
            print(f"\n   {name}:")

            # Check for various associated properties
            properties_found = []

            if hasattr(compound, "melting_point") and compound.melting_point:
                mp = compound.melting_point
                if mp.value:
                    properties_found.append(f"MP: {mp.value[0]}°C")

            if hasattr(compound, "boiling_point") and compound.boiling_point:
                bp = compound.boiling_point
                if bp.value:
                    properties_found.append(f"BP: {bp.value[0]}°C")

            if properties_found:
                for prop in properties_found:
                    print(f"     - {prop}")
            else:
                print("     - No associated properties found")

    print("\n" + "-" * 50 + "\n")


def units_and_conversion_examples():
    """Demonstrate units handling and conversion capabilities."""
    print("=== Units and Conversion Examples ===\n")

    units_text = """
    Temperature Measurements in Different Units

    Compound A: melting point 273.15 K (0°C)
    Compound B: mp 373 K
    Compound C: melting point 25°C
    Compound D: mp 298.15 Kelvin

    Mixed unit document:
    The melting point of ice is 0°C (273.15 K, 32°F).
    Benzene melts at 278.65 K, which is 5.5°C.
    """

    doc = Document(units_text)
    records = doc.records

    print("1. Original extracted values with units:")
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]

    for i, mp in enumerate(melting_points, 1):
        print(f"\n   MP {i}:")
        print(f"     Raw: '{mp.raw_value}' '{mp.raw_units}'")
        if mp.value and mp.units:
            print(f"     Parsed: {mp.value[0]} {mp.units}")

        # Demonstrate unit conversion if possible
        if mp.value and mp.units:
            try:
                # Convert to Celsius if not already
                if hasattr(mp, "convert_to"):
                    original_value = mp.value[0]
                    original_units = str(mp.units)

                    # Try to convert to Celsius
                    celsius_temp = Celsius()
                    if str(mp.units) != "Celsius":
                        try:
                            converted_mp = mp.convert_to(celsius_temp)
                            print(f"     Converted to Celsius: {converted_mp.value[0]}°C")
                        except:
                            print("     Conversion failed")

            except Exception as e:
                print(f"     Unit conversion not available: {e}")

    print("\n2. Unit normalization analysis:")
    celsius_values = []
    kelvin_values = []

    for mp in melting_points:
        if mp.value and mp.units:
            unit_str = str(mp.units).lower()
            if "celsius" in unit_str or "°c" in mp.raw_units.lower():
                celsius_values.append(mp.value[0])
            elif "kelvin" in unit_str or "k" in mp.raw_units.lower():
                kelvin_values.append(mp.value[0])

    print(f"   Values in Celsius: {celsius_values}")
    print(f"   Values in Kelvin: {kelvin_values}")

    # Convert Kelvin to Celsius for comparison
    if kelvin_values:
        converted_from_kelvin = [k - 273.15 for k in kelvin_values]
        print(f"   Kelvin converted to Celsius: {converted_from_kelvin}")

    print("\n" + "-" * 50 + "\n")


def range_and_uncertainty_handling():
    """Demonstrate handling of value ranges and uncertainties."""
    print("=== Range and Uncertainty Handling ===\n")

    range_text = """
    Experimental Uncertainties and Ranges

    Compound 1: melting point 80.1 ± 0.5°C
    Compound 2: mp 150-152°C (lit. 151°C)
    Compound 3: melting point approximately 200°C
    Compound 4: mp >300°C (decomposition)
    Compound 5: melting point 25.3°C (±0.2°C, n=3)

    Range measurements:
    - Sample A: 100-105°C
    - Sample B: 45.2-45.8°C
    - Sample C: 200±5°C
    - Sample D: ~75°C
    """

    doc = Document(range_text)
    records = doc.records

    print("1. Range and uncertainty analysis:")
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]

    for i, mp in enumerate(melting_points, 1):
        print(f"\n   MP {i}: '{mp.raw_value}' '{mp.raw_units}'")

        if mp.value:
            if len(mp.value) == 1:
                print(f"     Single value: {mp.value[0]}°C")
            elif len(mp.value) == 2:
                print(f"     Range: {mp.value[0]} - {mp.value[1]}°C")
                range_width = mp.value[1] - mp.value[0]
                print(f"     Range width: {range_width}°C")

        if mp.error:
            print(f"     Uncertainty: ±{mp.error}")

        # Classify measurement type
        raw_text = f"{mp.raw_value} {mp.raw_units}".lower()
        if "±" in raw_text or "+-" in raw_text:
            print("     Type: Explicit uncertainty")
        elif "-" in mp.raw_value and not mp.raw_value.startswith("-"):
            print("     Type: Range measurement")
        elif "~" in raw_text or "approximately" in raw_text:
            print("     Type: Approximate value")
        elif ">" in raw_text or "<" in raw_text:
            print("     Type: Inequality")
        else:
            print("     Type: Point measurement")

    print("\n2. Statistical analysis of ranges:")
    single_values = []
    range_measurements = []
    uncertainties = []

    for mp in melting_points:
        if mp.value:
            if len(mp.value) == 1:
                single_values.append(mp.value[0])
            elif len(mp.value) == 2:
                range_measurements.append((mp.value[0], mp.value[1]))

        if mp.error:
            uncertainties.append(mp.error)

    print(f"   Single values: {len(single_values)}")
    print(f"   Range measurements: {len(range_measurements)}")
    print(f"   Explicit uncertainties: {len(uncertainties)}")

    if range_measurements:
        avg_range = sum(abs(r[1] - r[0]) for r in range_measurements) / len(range_measurements)
        print(f"   Average range width: {avg_range:.1f}°C")

    if uncertainties:
        avg_uncertainty = sum(uncertainties) / len(uncertainties)
        print(f"   Average uncertainty: ±{avg_uncertainty:.2f}°C")

    print("\n" + "-" * 50 + "\n")


def solubility_and_qualitative_properties():
    """Demonstrate extraction of qualitative properties like solubility."""
    print("=== Solubility and Qualitative Properties ===\n")

    solubility_text = """
    Solubility Characteristics

    Benzene:
    - Solubility in water: 0.18 g/100 mL at 25°C (slightly soluble)
    - Miscible with ethanol, ether, and other organic solvents
    - Immiscible with water

    Ethanol:
    - Completely soluble in water in all proportions
    - Solubility: miscible with water
    - Also soluble in ether and chloroform

    Sodium chloride:
    - Water solubility: 36 g/100 mL at 20°C
    - Highly soluble in water
    - Insoluble in organic solvents

    Qualitative descriptions:
    - Compound A: sparingly soluble in cold water
    - Compound B: freely soluble in hot water
    - Compound C: practically insoluble in water
    - Compound D: very soluble in methanol
    """

    doc = Document(solubility_text)
    records = doc.records

    print("1. Solubility record analysis:")
    solubility_records = [
        r
        for r in records
        if r.__class__.__name__ == "Solubility"
        or hasattr(r, "solubility")
        or "solub" in str(r).lower()
    ]

    print(f"   Found {len(solubility_records)} potential solubility records")

    # Look for compounds with solubility information
    compounds = [r for r in records if isinstance(r, Compound)]
    print(f"   Found {len(compounds)} compounds")

    print("\n2. Text-based solubility extraction:")
    # Since solubility extraction might be limited, let's analyze the raw text
    text_lines = solubility_text.strip().split("\n")

    solubility_terms = [
        "soluble",
        "insoluble",
        "miscible",
        "immiscible",
        "dissolves",
        "sparingly",
        "freely",
        "slightly",
        "highly soluble",
        "very soluble",
        "completely soluble",
    ]

    solubility_info = []
    for line in text_lines:
        line_lower = line.lower()
        if any(term in line_lower for term in solubility_terms):
            solubility_info.append(line.strip())

    print("   Solubility-related sentences:")
    for info in solubility_info:
        if info and not info.startswith("Solubility") and info != "-":
            print(f"     - {info}")

    print("\n3. Quantitative vs. qualitative solubility:")
    quantitative_patterns = ["g/100 ml", "g/l", "mg/ml", "mol/l", "%"]
    qualitative_patterns = [
        "slightly soluble",
        "highly soluble",
        "very soluble",
        "sparingly soluble",
        "freely soluble",
        "miscible",
        "immiscible",
    ]

    quantitative_count = 0
    qualitative_count = 0

    text_lower = solubility_text.lower()
    for pattern in quantitative_patterns:
        if pattern in text_lower:
            quantitative_count += text_lower.count(pattern)

    for pattern in qualitative_patterns:
        if pattern in text_lower:
            qualitative_count += text_lower.count(pattern)

    print(f"   Quantitative solubility mentions: {quantitative_count}")
    print(f"   Qualitative solubility mentions: {qualitative_count}")

    print("\n" + "-" * 50 + "\n")


def property_validation_and_quality():
    """Demonstrate validation and quality assessment of extracted properties."""
    print("=== Property Validation and Quality Assessment ===\n")

    mixed_quality_text = """
    Mixed Quality Property Data

    High Quality Data:
    Benzene: mp 5.5°C (lit. 5.53°C), bp 80.1°C, density 0.879 g/mL

    Questionable Data:
    Compound X: melting point 999°C (seems too high for organic compound)
    Compound Y: mp -500°C (below absolute zero - impossible)
    Compound Z: boiling point 25°C, melting point 100°C (bp < mp - impossible)

    Incomplete Data:
    Compound A: melting point not determined
    Compound B: mp ~200°C (approximate)
    Compound C: decomposes before melting

    Inconsistent Data:
    Compound D: mp 50°C (Method A), mp 55°C (Method B), mp 48°C (Method C)
    """

    doc = Document(mixed_quality_text)
    records = doc.records

    print("1. Quality assessment criteria:")
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]

    # Quality assessment for melting points
    high_quality = []
    questionable = []
    incomplete = []

    for mp in melting_points:
        if not mp.value:
            incomplete.append(mp)
            continue

        temp = mp.value[0]

        # Check for physically impossible values
        if temp < -273.15:  # Below absolute zero
            questionable.append((mp, "Below absolute zero"))
        elif temp > 500:  # Very high for typical organic compounds
            questionable.append((mp, "Unusually high temperature"))
        else:
            high_quality.append(mp)

    print(f"   High quality measurements: {len(high_quality)}")
    print(f"   Questionable measurements: {len(questionable)}")
    print(f"   Incomplete measurements: {len(incomplete)}")

    print("\n2. Detailed quality analysis:")

    if questionable:
        print("\n   Questionable measurements:")
        for mp, reason in questionable:
            value_str = f"{mp.value[0]}°C" if mp.value else "N/A"
            print(f"     - {value_str}: {reason} (raw: '{mp.raw_value}')")

    if incomplete:
        print("\n   Incomplete measurements:")
        for mp in incomplete:
            print(f"     - Raw text: '{mp.raw_value}' (could not extract numeric value)")

    print("\n3. Consistency checks:")
    # Group by compound and check for consistency
    compound_properties = defaultdict(lambda: {"mp": [], "bp": []})

    compounds = [r for r in records if isinstance(r, Compound)]

    # This is simplified - in practice you'd need better compound-property linking
    for i, mp in enumerate(melting_points):
        if mp.value:
            compound_properties[f"compound_{i}"]["mp"].append(mp.value[0])

    for i, bp in enumerate(boiling_points):
        if bp.value:
            compound_properties[f"compound_{i}"]["bp"].append(bp.value[0])

    # Check for mp > bp inconsistencies
    inconsistencies = []
    for comp_id, props in compound_properties.items():
        if props["mp"] and props["bp"]:
            mp_val = props["mp"][0]
            bp_val = props["bp"][0]
            if mp_val > bp_val:
                inconsistencies.append((comp_id, mp_val, bp_val))

    if inconsistencies:
        print("   Physical inconsistencies found:")
        for comp_id, mp_val, bp_val in inconsistencies:
            print(f"     - {comp_id}: MP ({mp_val}°C) > BP ({bp_val}°C)")
    else:
        print("   No obvious physical inconsistencies detected")

    print("\n4. Data completeness analysis:")
    total_compounds = len(compounds)
    compounds_with_mp = len(
        [c for c in compounds if hasattr(c, "melting_point") and c.melting_point]
    )
    compounds_with_bp = len(
        [c for c in compounds if hasattr(c, "boiling_point") and c.boiling_point]
    )

    print(f"   Total compounds: {total_compounds}")
    print(f"   Compounds with melting points: {compounds_with_mp}")
    print(f"   Compounds with boiling points: {compounds_with_bp}")

    if total_compounds > 0:
        mp_completeness = (compounds_with_mp / total_compounds) * 100
        bp_completeness = (compounds_with_bp / total_compounds) * 100
        print(f"   Melting point completeness: {mp_completeness:.1f}%")
        print(f"   Boiling point completeness: {bp_completeness:.1f}%")

    print("\n" + "-" * 50 + "\n")


def export_properties_for_analysis():
    """Demonstrate exporting extracted properties for further analysis."""
    print("=== Property Export for Analysis ===\n")

    export_text = """
    Chemical Database Export Example

    1. Acetone (C3H6O)
    Melting point: -94.7°C
    Boiling point: 56.05°C
    Density: 0.791 g/mL

    2. Ethyl acetate (C4H8O2)
    Mp: -83.6°C
    Bp: 77.1°C
    d: 0.902 g/cm³

    3. Chloroform (CHCl3)
    Melting point: -63.5°C
    Boiling point: 61.15°C
    Density: 1.489 g/mL at 20°C
    """

    doc = Document(export_text)
    records = doc.records

    print("1. Structured data export:")

    # Organize data for export
    export_data = {
        "extraction_metadata": {
            "total_records": len(records),
            "timestamp": "2024-01-01T12:00:00Z",
            "extractor": "ChemDataExtractor2",
        },
        "compounds": [],
        "properties": {"melting_points": [], "boiling_points": [], "densities": []},
    }

    # Extract compounds
    compounds = [r for r in records if isinstance(r, Compound)]
    for compound in compounds:
        compound_data = {
            "names": compound.names or [],
            "labels": getattr(compound, "labels", []),
            "formula": None,  # Would need to extract from names/labels
        }
        export_data["compounds"].append(compound_data)

    # Extract properties
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    for mp in melting_points:
        mp_data = {
            "raw_value": mp.raw_value,
            "raw_units": mp.raw_units,
            "parsed_value": mp.value,
            "units": str(mp.units) if mp.units else None,
            "error": mp.error,
        }
        export_data["properties"]["melting_points"].append(mp_data)

    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]
    for bp in boiling_points:
        bp_data = {
            "raw_value": bp.raw_value,
            "raw_units": bp.raw_units,
            "parsed_value": bp.value,
            "units": str(bp.units) if bp.units else None,
            "error": getattr(bp, "error", None),
        }
        export_data["properties"]["boiling_points"].append(bp_data)

    print("   JSON export structure:")
    print(
        json.dumps(export_data, indent=2)[:500] + "..."
        if len(str(export_data)) > 500
        else json.dumps(export_data, indent=2)
    )

    print("\n2. CSV export format:")
    print("   Compound,Formula,Melting_Point_C,Boiling_Point_C,Density_g_mL,Source")

    # Simple CSV export (would need better compound-property linking)
    csv_rows = []
    for i, compound in enumerate(compounds):
        name = compound.names[0] if compound.names else f"Compound_{i+1}"
        formula = "N/A"  # Would extract from compound data

        # Find associated properties (simplified)
        mp_val = "N/A"
        bp_val = "N/A"
        density_val = "N/A"

        if i < len(melting_points) and melting_points[i].value:
            mp_val = melting_points[i].value[0]

        if i < len(boiling_points) and boiling_points[i].value:
            bp_val = boiling_points[i].value[0]

        csv_row = f"   {name},{formula},{mp_val},{bp_val},{density_val},ChemDataExtractor2"
        csv_rows.append(csv_row)

    for row in csv_rows:
        print(row)

    print("\n3. Database-ready format:")
    database_records = []

    for record in records:
        db_record = {
            "record_id": f"{record.__class__.__name__}_{hash(str(record)) % 10000}",
            "record_type": record.__class__.__name__,
            "extracted_data": record.serialize(primitive=True),
            "confidence_score": getattr(record, "confidence", 1.0),
            "extraction_method": "rule_based_parsing",
            "source_document": "example_text",
            "created_at": "2024-01-01T12:00:00Z",
        }
        database_records.append(db_record)

    print("   Database record format:")
    if database_records:
        print(json.dumps(database_records[0], indent=2))
        if len(database_records) > 1:
            print(f"   ... and {len(database_records)-1} more records")

    print("\n" + "-" * 50 + "\n")


def main():
    """Run all property extraction examples."""
    print("ChemDataExtractor2 Chemical Property Extraction Examples")
    print("=" * 60 + "\n")

    try:
        melting_point_extraction()
        multi_property_extraction()
        units_and_conversion_examples()
        range_and_uncertainty_handling()
        solubility_and_qualitative_properties()
        property_validation_and_quality()
        export_properties_for_analysis()

        print("All property extraction examples completed successfully!")

    except Exception as e:
        print(f"Error running property extraction examples: {e}")
        raise


if __name__ == "__main__":
    main()

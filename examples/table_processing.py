#!/usr/bin/env python3
"""
Table Processing Examples for ChemDataExtractor2

This script demonstrates extracting structured data from tables, including
physical property tables, compound databases, and experimental results.
"""

from chemdataextractor import Document
from chemdataextractor.model.model import Compound, MeltingPoint, BoilingPoint
from chemdataextractor.doc.table import Table
from chemdataextractor.doc.text import Cell
import json
from collections import defaultdict
from typing import List, Dict, Any


def simple_property_table():
    """Demonstrate processing a simple property table."""
    print("=== Simple Property Table Processing ===\n")
    
    table_text = """
    Physical Properties of Common Solvents
    
    Table 1. Physical properties of laboratory solvents
    
    Compound      | Melting Point (°C) | Boiling Point (°C) | Density (g/mL)
    Methanol      | -97.6             | 64.7              | 0.792
    Ethanol       | -114.1            | 78.4              | 0.789  
    Propanol      | -126.2            | 97.2              | 0.804
    Acetone       | -94.7             | 56.1              | 0.791
    Chloroform    | -63.5             | 61.2              | 1.489
    
    All measurements were performed at standard atmospheric pressure.
    """
    
    doc = Document(table_text)
    records = doc.records
    
    print("1. Document structure analysis:")
    for i, element in enumerate(doc.elements):
        element_type = element.__class__.__name__
        preview = str(element)[:80].replace('\n', ' ').replace('  ', ' ')
        print(f"   {i+1}. {element_type}: {preview}...")
    
    print("\n2. Table detection:")
    tables = [el for el in doc.elements if isinstance(el, Table)]
    print(f"   Found {len(tables)} table(s)")
    
    if tables:
        table = tables[0]
        print(f"   Table dimensions: {len(table)} rows")
        
        print("\n   Table content preview:")
        for i, row in enumerate(table[:3]):  # Show first 3 rows
            row_content = []
            for cell in row:
                if hasattr(cell, 'text'):
                    row_content.append(cell.text[:20])
            print(f"     Row {i+1}: {' | '.join(row_content)}")
    
    print("\n3. Extracted records analysis:")
    record_types = defaultdict(int)
    for record in records:
        record_types[record.__class__.__name__] += 1
    
    for record_type, count in sorted(record_types.items()):
        print(f"   {record_type}: {count}")
    
    print("\n4. Detailed record analysis:")
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]
    
    print(f"\n   Compounds ({len(compounds)}):")
    for compound in compounds:
        names = compound.names or ['Unknown']
        print(f"     - {', '.join(names)}")
    
    print(f"\n   Melting Points ({len(melting_points)}):")
    for mp in melting_points:
        value_str = f"{mp.value[0]}°C" if mp.value else "N/A"
        print(f"     - {value_str} (raw: '{mp.raw_value}')")
    
    print(f"\n   Boiling Points ({len(boiling_points)}):")
    for bp in boiling_points:
        value_str = f"{bp.value[0]}°C" if bp.value else "N/A"
        print(f"     - {value_str} (raw: '{bp.raw_value}')")
    
    print("\n" + "-"*50 + "\n")


def complex_experimental_table():
    """Demonstrate processing complex experimental data tables."""
    print("=== Complex Experimental Data Table ===\n")
    
    complex_table = """
    Synthesis and Characterization Results
    
    Table 2. Experimental results for benzene derivative synthesis
    
    Entry | Starting Material | Product           | Yield (%) | Mp (°C)   | Bp (°C)   | Purity
    1     | Benzene          | Toluene           | 87        | -95.0     | 110.6     | 99.2%
    2     | Toluene          | Para-xylene       | 92        | 13.2      | 138.4     | 98.8%
    3     | Benzene          | Chlorobenzene     | 78        | -45.6     | 131.7     | 97.5%
    4     | Phenol           | 4-Methylphenol    | 85        | 34.8      | 202.2     | 99.1%
    5     | Aniline          | N-Methylaniline   | 91        | -57.0     | 196.2     | 98.3%
    
    Reaction conditions: 150°C, 24 hours, nitrogen atmosphere.
    Yields are isolated yields after purification by column chromatography.
    """
    
    doc = Document(complex_table)
    records = doc.records
    
    print("1. Complex table structure analysis:")
    tables = [el for el in doc.elements if isinstance(el, Table)]
    
    if tables:
        table = tables[0]
        print(f"   Table has {len(table)} rows")
        
        # Analyze table headers
        if table and len(table) > 0:
            header_row = table[0]
            headers = []
            for cell in header_row:
                if hasattr(cell, 'text'):
                    headers.append(cell.text.strip())
            
            print(f"   Headers detected: {headers}")
            
            print("\n   Sample data rows:")
            for i, row in enumerate(table[1:4]):  # Show first 3 data rows
                row_data = []
                for cell in row:
                    if hasattr(cell, 'text'):
                        row_data.append(cell.text.strip()[:15])
                print(f"     Row {i+2}: {' | '.join(row_data)}")
    
    print("\n2. Extracted chemical information:")
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]
    
    print(f"   Extracted {len(compounds)} compounds")
    print(f"   Extracted {len(melting_points)} melting points")
    print(f"   Extracted {len(boiling_points)} boiling points")
    
    print("\n3. Compound-property relationships:")
    # Try to associate compounds with their properties
    for i, compound in enumerate(compounds):
        if compound.names:
            print(f"\n   {compound.names[0]}:")
            
            # Look for associated properties
            associated_mp = None
            associated_bp = None
            
            # Simple association by index (in practice, more sophisticated linking needed)
            if i < len(melting_points) and melting_points[i].value:
                associated_mp = melting_points[i]
            if i < len(boiling_points) and boiling_points[i].value:
                associated_bp = boiling_points[i]
            
            if associated_mp:
                print(f"     Melting point: {associated_mp.value[0]}°C")
            if associated_bp:
                print(f"     Boiling point: {associated_bp.value[0]}°C")
            
            if not associated_mp and not associated_bp:
                print(f"     No associated properties found")
    
    print("\n4. Data quality assessment:")
    # Check for reasonable values
    valid_mp = 0
    invalid_mp = 0
    
    for mp in melting_points:
        if mp.value:
            temp = mp.value[0]
            if -300 <= temp <= 500:  # Reasonable range for organic compounds
                valid_mp += 1
            else:
                invalid_mp += 1
                print(f"     Questionable MP: {temp}°C")
    
    print(f"   Valid melting points: {valid_mp}")
    print(f"   Questionable melting points: {invalid_mp}")
    
    print("\n" + "-"*50 + "\n")


def multi_table_document():
    """Demonstrate processing documents with multiple tables."""
    print("=== Multi-Table Document Processing ===\n")
    
    multi_table_text = """
    Comprehensive Chemical Database
    
    Physical Properties Section
    
    Table 1: Melting points of aromatic compounds
    Compound    | Mp (°C)
    Benzene     | 5.5
    Toluene     | -95.0
    Xylene      | 13.2
    
    Table 2: Boiling points of the same compounds  
    Compound    | Bp (°C)
    Benzene     | 80.1
    Toluene     | 110.6
    Xylene      | 138.4
    
    Table 3: Density measurements
    Compound    | Density (g/mL) | Temperature (°C)
    Benzene     | 0.879         | 20
    Toluene     | 0.867         | 20
    Xylene      | 0.861         | 20
    
    All measurements were performed under standard conditions.
    """
    
    doc = Document(multi_table_text)
    
    print("1. Multiple table detection:")
    tables = [el for el in doc.elements if isinstance(el, Table)]
    print(f"   Found {len(tables)} tables")
    
    for i, table in enumerate(tables, 1):
        print(f"\n   Table {i}:")
        print(f"     Rows: {len(table)}")
        
        if table and len(table) > 0:
            # Try to identify table type from first few cells
            first_row_text = ""
            for cell in table[0]:
                if hasattr(cell, 'text'):
                    first_row_text += cell.text.lower() + " "
            
            table_type = "Unknown"
            if "melting" in first_row_text or "mp" in first_row_text:
                table_type = "Melting Points"
            elif "boiling" in first_row_text or "bp" in first_row_text:
                table_type = "Boiling Points"
            elif "density" in first_row_text:
                table_type = "Density"
            
            print(f"     Type: {table_type}")
    
    print("\n2. Cross-table data integration:")
    records = doc.records
    
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]
    
    # Create integrated compound database
    compound_database = {}
    
    for compound in compounds:
        if compound.names:
            name = compound.names[0]
            if name not in compound_database:
                compound_database[name] = {}
    
    # Add melting points
    for mp in melting_points:
        # In practice, need better compound-property linking
        # This is simplified for demonstration
        pass
    
    # Manual integration for demonstration
    integration_data = {
        'Benzene': {'mp': 5.5, 'bp': 80.1, 'density': 0.879},
        'Toluene': {'mp': -95.0, 'bp': 110.6, 'density': 0.867},
        'Xylene': {'mp': 13.2, 'bp': 138.4, 'density': 0.861}
    }
    
    print("   Integrated compound properties:")
    for compound, properties in integration_data.items():
        print(f"\n   {compound}:")
        for prop, value in properties.items():
            if prop == 'mp':
                print(f"     Melting point: {value}°C")
            elif prop == 'bp':
                print(f"     Boiling point: {value}°C") 
            elif prop == 'density':
                print(f"     Density: {value} g/mL")
    
    print("\n3. Data completeness analysis:")
    total_compounds = len(integration_data)
    properties = ['mp', 'bp', 'density']
    
    for prop in properties:
        complete_count = sum(1 for comp_data in integration_data.values() if prop in comp_data)
        completeness = (complete_count / total_compounds) * 100
        prop_name = {'mp': 'Melting Point', 'bp': 'Boiling Point', 'density': 'Density'}[prop]
        print(f"   {prop_name} completeness: {completeness:.0f}%")
    
    print("\n" + "-"*50 + "\n")


def malformed_table_handling():
    """Demonstrate handling of malformed or irregular tables."""
    print("=== Malformed Table Handling ===\n")
    
    malformed_table = """
    Irregular Table Formats
    
    Table with missing cells:
    Compound | Mp | Bp | Notes
    Benzene | 5.5°C | 80.1°C | Pure sample
    Toluene | | 110.6°C | Mp not determined
    Xylene | 13.2°C | | Bp measurement failed
    
    Table with merged cells:
    Property Data for Aromatic Compounds
    =====================================
    Benzene: Mp 5.5°C, Bp 80.1°C
    Toluene: Mp -95°C, Bp 110.6°C  
    
    Inconsistent formatting:
    Compound    Melting Point    Boiling Point
    -----------  -------------   --------------
    Phenol       40.9 degrees C  181.7 C
    Aniline      -6.0°C         184.4°C
    Pyridine     -42°C          115.2°C
    """
    
    doc = Document(malformed_table)
    records = doc.records
    
    print("1. Parsing malformed tables:")
    tables = [el for el in doc.elements if isinstance(el, Table)]
    print(f"   Tables detected: {len(tables)}")
    
    # Even with malformed tables, try to extract what we can
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    
    print(f"   Compounds extracted: {len(compounds)}")
    print(f"   Melting points extracted: {len(melting_points)}")
    
    print("\n2. Robustness analysis:")
    
    # Check what was successfully extracted despite formatting issues
    successful_extractions = []
    for compound in compounds:
        if compound.names:
            successful_extractions.append(compound.names[0])
    
    print("   Successfully extracted compounds:")
    for name in successful_extractions:
        print(f"     - {name}")
    
    # Check melting point extraction quality
    valid_mp_count = 0
    for mp in melting_points:
        if mp.value and mp.raw_value:
            valid_mp_count += 1
            print(f"   MP: {mp.value[0]}°C from '{mp.raw_value}'")
    
    print(f"\n   Valid melting point extractions: {valid_mp_count}/{len(melting_points)}")
    
    print("\n3. Error tolerance strategies:")
    print("   Strategies demonstrated:")
    print("     - Flexible parsing of temperature units")
    print("     - Handling missing table cells")
    print("     - Working with non-tabular structured text")
    print("     - Extracting from inconsistent formatting")
    
    print("\n" + "-"*50 + "\n")


def table_metadata_extraction():
    """Demonstrate extracting metadata and context from tables."""
    print("=== Table Metadata and Context Extraction ===\n")
    
    metadata_table = """
    Experimental Conditions and Results
    
    Table 1: Physical properties measured under controlled conditions
    Temperature: 25°C ± 0.1°C
    Pressure: 1 atm (101.325 kPa)
    Humidity: <5% RH
    Equipment: Büchi melting point apparatus (Model B-545)
    
    Compound        | Mp (°C)    | Bp (°C)    | Method         | Uncertainty
    Benzene         | 5.53       | 80.10      | DSC           | ±0.05
    Toluene         | -95.02     | 110.58     | Visual        | ±0.2
    Para-xylene     | 13.26      | 138.37     | DSC           | ±0.05
    Ortho-xylene    | -25.18     | 144.41     | DSC           | ±0.05
    
    Notes:
    - DSC = Differential Scanning Calorimetry
    - Visual method used for subambient temperatures
    - All samples >99% pure by GC-MS
    - Measurements repeated in triplicate
    """
    
    doc = Document(metadata_table)
    records = doc.records
    
    print("1. Metadata extraction from context:")
    
    # Look for experimental conditions in the text
    text_content = metadata_table.lower()
    
    conditions = {}
    if "temperature:" in text_content:
        # Extract temperature condition
        temp_line = [line for line in metadata_table.split('\n') if 'Temperature:' in line]
        if temp_line:
            conditions['temperature'] = temp_line[0].split('Temperature:')[1].strip()
    
    if "pressure:" in text_content:
        pressure_line = [line for line in metadata_table.split('\n') if 'Pressure:' in line]
        if pressure_line:
            conditions['pressure'] = pressure_line[0].split('Pressure:')[1].strip()
    
    if "equipment:" in text_content:
        equip_line = [line for line in metadata_table.split('\n') if 'Equipment:' in line]
        if equip_line:
            conditions['equipment'] = equip_line[0].split('Equipment:')[1].strip()
    
    print("   Experimental conditions found:")
    for key, value in conditions.items():
        print(f"     {key.title()}: {value}")
    
    print("\n2. Enhanced property data with metadata:")
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    
    # Enhanced analysis considering metadata
    high_precision_count = 0
    visual_method_count = 0
    
    for mp in melting_points:
        if mp.value:
            # Check precision based on decimal places
            value_str = mp.raw_value
            if '.' in value_str:
                decimal_places = len(value_str.split('.')[1])
                if decimal_places >= 2:
                    high_precision_count += 1
            
            # Note: Method information would need to be extracted from table context
            # This is simplified for demonstration
    
    print(f"   High precision measurements (≥2 decimal places): {high_precision_count}")
    print(f"   Total measurements: {len(melting_points)}")
    
    print("\n3. Quality indicators from metadata:")
    quality_indicators = []
    
    if "±" in metadata_table:
        quality_indicators.append("Uncertainty values provided")
    if "triplicate" in metadata_table.lower():
        quality_indicators.append("Measurements repeated in triplicate")
    if ">99%" in metadata_table:
        quality_indicators.append("High purity samples (>99%)")
    if "DSC" in metadata_table:
        quality_indicators.append("Differential Scanning Calorimetry used")
    
    print("   Quality indicators detected:")
    for indicator in quality_indicators:
        print(f"     - {indicator}")
    
    print("\n4. Data reliability assessment:")
    reliability_score = 0
    
    # Scoring based on metadata
    if conditions:
        reliability_score += 20  # Experimental conditions specified
    if quality_indicators:
        reliability_score += len(quality_indicators) * 15
    if high_precision_count > 0:
        reliability_score += 20  # High precision data
    
    reliability_score = min(reliability_score, 100)  # Cap at 100%
    
    print(f"   Estimated data reliability: {reliability_score}%")
    print("   Based on:")
    print("     - Experimental conditions specified")
    print("     - Quality indicators present")
    print("     - Measurement precision")
    print("     - Methodological information")
    
    print("\n" + "-"*50 + "\n")


def export_table_data():
    """Demonstrate exporting table data in various formats."""
    print("=== Table Data Export ===\n")
    
    export_table = """
    Chemical Property Database Export
    
    Table: Comprehensive Property Data
    
    ID | Compound    | Formula | Mp (°C) | Bp (°C) | Density | Solubility
    1  | Methanol    | CH4O    | -97.6   | 64.7    | 0.792   | Miscible
    2  | Ethanol     | C2H6O   | -114.1  | 78.4    | 0.789   | Miscible  
    3  | Acetone     | C3H6O   | -94.7   | 56.1    | 0.791   | Miscible
    4  | Benzene     | C6H6    | 5.5     | 80.1    | 0.879   | Immiscible
    """
    
    doc = Document(export_table)
    records = doc.records
    
    print("1. Structured data compilation:")
    
    # Organize extracted data
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]
    
    # Create comprehensive data structure
    export_data = []
    
    # Simple association (in practice, would use more sophisticated linking)
    compound_names = [c.names[0] if c.names else f"Compound_{i}" for i, c in enumerate(compounds)]
    mp_values = [mp.value[0] if mp.value else None for mp in melting_points]
    bp_values = [bp.value[0] if bp.value else None for bp in boiling_points]
    
    max_len = max(len(compound_names), len(mp_values), len(bp_values))
    
    for i in range(max_len):
        record_data = {
            'compound': compound_names[i] if i < len(compound_names) else None,
            'melting_point': mp_values[i] if i < len(mp_values) else None,
            'boiling_point': bp_values[i] if i < len(bp_values) else None,
            'extraction_confidence': 0.85,  # Would calculate from actual confidence scores
            'source': 'table_extraction'
        }
        export_data.append(record_data)
    
    print(f"   Compiled {len(export_data)} compound records")
    
    print("\n2. JSON export format:")
    json_export = {
        'metadata': {
            'extraction_date': '2024-01-01',
            'total_compounds': len(export_data),
            'data_source': 'table',
            'extraction_method': 'ChemDataExtractor2'
        },
        'data': export_data
    }
    
    print(json.dumps(json_export, indent=2)[:400] + "..." if len(str(json_export)) > 400 else json.dumps(json_export, indent=2))
    
    print("\n3. CSV export format:")
    print("   Compound,Melting_Point_C,Boiling_Point_C,Confidence,Source")
    for record in export_data:
        compound = record['compound'] or 'Unknown'
        mp = record['melting_point'] or 'N/A'
        bp = record['boiling_point'] or 'N/A'
        conf = record['extraction_confidence']
        source = record['source']
        print(f"   {compound},{mp},{bp},{conf},{source}")
    
    print("\n4. Database INSERT statements:")
    print("   -- SQL INSERT statements for database import")
    print("   CREATE TABLE IF NOT EXISTS chemical_properties (")
    print("       id SERIAL PRIMARY KEY,")
    print("       compound_name VARCHAR(100),")
    print("       melting_point_c DECIMAL(5,2),")
    print("       boiling_point_c DECIMAL(5,2),")
    print("       confidence DECIMAL(3,2),")
    print("       extraction_source VARCHAR(50)")
    print("   );")
    print()
    
    for i, record in enumerate(export_data[:3], 1):  # Show first 3
        compound = record['compound'] or 'Unknown'
        mp = record['melting_point'] if record['melting_point'] is not None else 'NULL'
        bp = record['boiling_point'] if record['boiling_point'] is not None else 'NULL'
        conf = record['extraction_confidence']
        source = record['source']
        
        print(f"   INSERT INTO chemical_properties (compound_name, melting_point_c, boiling_point_c, confidence, extraction_source)")
        print(f"   VALUES ('{compound}', {mp}, {bp}, {conf}, '{source}');")
    
    if len(export_data) > 3:
        print(f"   -- ... and {len(export_data)-3} more INSERT statements")
    
    print("\n" + "-"*50 + "\n")


def main():
    """Run all table processing examples."""
    print("ChemDataExtractor2 Table Processing Examples")
    print("=" * 50 + "\n")
    
    try:
        simple_property_table()
        complex_experimental_table()
        multi_table_document()
        malformed_table_handling()
        table_metadata_extraction()
        export_table_data()
        
        print("All table processing examples completed successfully!")
        
    except Exception as e:
        print(f"Error running table processing examples: {e}")
        raise


if __name__ == "__main__":
    main()
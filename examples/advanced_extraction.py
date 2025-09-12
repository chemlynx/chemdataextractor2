#!/usr/bin/env python3
"""
Advanced Extraction Examples for ChemDataExtractor2

This script demonstrates advanced features including file processing,
custom models, contextual merging, and integration with external tools.
"""

from chemdataextractor import Document
from chemdataextractor.model.model import Compound, MeltingPoint, BoilingPoint
from chemdataextractor.model.base import BaseModel, StringType, ListType, FloatType
from chemdataextractor.model.units.temperature import Celsius
from chemdataextractor.model.units.quantity_model import QuantityModel
from chemdataextractor.parse.base import BaseParser
from pathlib import Path
import json
import tempfile
import os


def file_processing_examples():
    """Demonstrate processing different file formats."""
    print("=== File Processing Examples ===\n")
    
    # Create sample files for demonstration
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample HTML file
        html_content = """
        <html>
        <head><title>Chemical Research Paper</title></head>
        <body>
            <h1>Synthesis and Properties of Aromatic Compounds</h1>
            <p>We synthesized <b>benzene</b> and determined its melting point to be <b>5.5°C</b>.</p>
            <table>
                <tr><th>Compound</th><th>Melting Point</th></tr>
                <tr><td>Toluene</td><td>-95°C</td></tr>
                <tr><td>Xylene</td><td>13.2°C</td></tr>
            </table>
        </body>
        </html>
        """
        
        html_file = temp_path / "paper.html"
        html_file.write_text(html_content)
        
        print("1. Processing HTML file:")
        try:
            doc = Document.from_file(str(html_file))
            records = doc.records
            print(f"  HTML file processed: {len(records)} records found")
            
            # Show document structure
            print("  Document elements:")
            for i, element in enumerate(doc.elements):
                print(f"    {i+1}. {element.__class__.__name__}: {str(element)[:50]}...")
            
        except Exception as e:
            print(f"  Error processing HTML: {e}")
        
        # Create sample text file
        text_content = """
        Chemical Synthesis Report
        
        Abstract
        This study reports the synthesis of several benzene derivatives.
        
        Results and Discussion
        Benzene (C6H6) was synthesized with 95% yield. The melting point 
        was determined to be 5.5°C using differential scanning calorimetry.
        
        Para-xylene showed a melting point of 13.2°C and boiling point of 138.4°C.
        The compound exhibited good thermal stability.
        
        Experimental
        All compounds were purified by recrystallization from ethanol.
        Melting points were uncorrected.
        """
        
        text_file = temp_path / "paper.txt"
        text_file.write_text(text_content)
        
        print("\n2. Processing text file:")
        try:
            doc = Document.from_file(str(text_file))
            records = doc.records
            print(f"  Text file processed: {len(records)} records found")
            
            # Analyze the records
            compounds = [r for r in records if isinstance(r, Compound)]
            print(f"  Compounds identified: {len(compounds)}")
            for compound in compounds:
                if compound.names:
                    print(f"    - {', '.join(compound.names)}")
            
        except Exception as e:
            print(f"  Error processing text: {e}")
        
    print("\n" + "-"*50 + "\n")


def contextual_merging_examples():
    """Demonstrate how ChemDataExtractor merges information contextually."""
    print("=== Contextual Merging Examples ===\n")
    
    # Example showing how information gets linked across document sections
    complex_document = """
    Chemical Analysis of Organic Solvents
    
    Introduction
    This study focuses on common laboratory solvents and their physical properties.
    
    Benzene Analysis
    Benzene is an important aromatic solvent. Our analysis showed excellent purity.
    The melting point was determined to be 5.5°C using a calibrated apparatus.
    Boiling point measurements yielded 80.1°C at standard atmospheric pressure.
    
    Toluene Characterization  
    Toluene (methylbenzene) is widely used in organic synthesis.
    Melting point: -95.0°C
    Boiling point: 110.6°C
    
    Para-xylene Properties
    Para-xylene showed the following characteristics:
    - Melting point: 13.2°C
    - Boiling point: 138.4°C
    - Density: 0.861 g/mL at 20°C
    
    Conclusion
    All solvents met purity specifications for laboratory use.
    """
    
    doc = Document(complex_document)
    records = doc.records
    
    print("1. Record-level analysis:")
    print(f"Total records found: {len(records)}")
    
    record_types = {}
    for record in records:
        record_type = record.__class__.__name__
        record_types[record_type] = record_types.get(record_type, 0) + 1
    
    for record_type, count in sorted(record_types.items()):
        print(f"  {record_type}: {count}")
    
    print("\n2. Contextual associations:")
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]
    
    print("Compounds with their properties:")
    for compound in compounds:
        names = compound.names or ['Unknown compound']
        print(f"\n  {', '.join(names)}:")
        
        # Check if compound has merged property information
        if hasattr(compound, 'melting_point') and compound.melting_point:
            mp = compound.melting_point
            print(f"    Melting Point: {mp.value} {mp.units} (merged)")
        
        if hasattr(compound, 'boiling_point') and compound.boiling_point:
            bp = compound.boiling_point  
            print(f"    Boiling Point: {bp.value} {bp.units} (merged)")
    
    print("\n3. Standalone properties (not yet merged):")
    print(f"  Standalone melting points: {len(melting_points)}")
    print(f"  Standalone boiling points: {len(boiling_points)}")
    
    print("\n" + "-"*50 + "\n")


def table_processing_examples():
    """Demonstrate table processing and data extraction."""
    print("=== Table Processing Examples ===\n")
    
    # Document with tables
    table_document = """
    Physical Properties of Benzene Derivatives
    
    The following table summarizes the physical properties of various benzene derivatives 
    synthesized in this study:
    
    Table 1. Physical Properties
    
    Compound        Melting Point (°C)    Boiling Point (°C)    Yield (%)
    Benzene         5.5                   80.1                  95
    Toluene         -95.0                 110.6                 88
    Para-xylene     13.2                  138.4                 92
    Ortho-xylene    -25.2                 144.4                 85
    
    All melting points were determined using a Büchi melting point apparatus.
    Boiling points were measured at 1 atm pressure using distillation.
    """
    
    doc = Document(table_document)
    
    print("1. Document structure analysis:")
    for i, element in enumerate(doc.elements):
        element_type = element.__class__.__name__
        content_preview = str(element)[:60].replace('\n', ' ')
        print(f"  {i+1}. {element_type}: {content_preview}...")
    
    print("\n2. Extracted records from table:")
    records = doc.records
    
    # Group records by type
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    boiling_points = [r for r in records if isinstance(r, BoilingPoint)]
    
    print(f"  Found {len(compounds)} compounds")
    print(f"  Found {len(melting_points)} melting points")  
    print(f"  Found {len(boiling_points)} boiling points")
    
    print("\n3. Detailed table data:")
    for compound in compounds:
        if compound.names:
            print(f"\n  Compound: {', '.join(compound.names)}")
            
            # Look for associated properties
            for mp in melting_points:
                if mp.value and mp.units:
                    print(f"    Melting Point: {mp.value[0]} {mp.units}")
                    break
            
            for bp in boiling_points:
                if bp.value and bp.units:
                    print(f"    Boiling Point: {bp.value[0]} {bp.units}")
                    break
    
    print("\n" + "-"*50 + "\n")


def custom_model_examples():
    """Demonstrate creating and using custom models."""
    print("=== Custom Model Examples ===\n")
    
    # Define a custom model for density measurements
    class DensityModel(QuantityModel):
        """Custom model for density measurements."""
        specifier = StringType()
        
        # Inherit value, units, error from QuantityModel
        # Add custom properties if needed
        
        def __init__(self, **kwargs):
            # Set dimensions for density (mass/volume)
            from chemdataextractor.model.units.dimension import Dimension
            # This would normally be defined properly with mass/length^3 dimensions
            super().__init__(**kwargs)
    
    print("1. Custom model definition:")
    print("   Created DensityModel class inheriting from QuantityModel")
    print("   This model can extract density values with units")
    
    print("\n2. Using custom models in extraction:")
    # For this example, we'll work with the existing models
    # In practice, you would register the custom model with parsers
    
    density_text = """
    Physical Properties
    
    The density of benzene was measured as 0.879 g/mL at 20°C.
    Toluene has a density of 0.867 g/cm³ at room temperature.
    """
    
    # Note: Without proper parser registration, custom models won't be
    # automatically extracted. This shows the concept.
    print("   Sample text with density information:")
    print("   " + density_text.strip().replace('\n', '\n   '))
    
    doc = Document(density_text)
    records = doc.records
    print(f"\n   Records found with standard models: {len(records)}")
    
    print("\n" + "-"*50 + "\n")


def data_validation_examples():
    """Demonstrate data validation and quality checking."""
    print("=== Data Validation Examples ===\n")
    
    # Document with mixed quality data
    mixed_quality_text = """
    Experimental Results
    
    Compound A: melting point 150°C (good quality data)
    Compound B: mp approximately 200-250°C (range data)
    Compound C: melting point not determined (missing data)
    Compound D: melting point 99999°C (unrealistic data)
    Compound E: mp 25°C, very pure sample (with note)
    """
    
    doc = Document(mixed_quality_text)
    records = doc.records
    
    print("1. Quality assessment of extracted data:")
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    
    for i, mp in enumerate(melting_points, 1):
        print(f"\n  Melting Point {i}:")
        print(f"    Raw value: {mp.raw_value}")
        print(f"    Raw units: {mp.raw_units}")
        print(f"    Parsed value: {mp.value}")
        print(f"    Units: {mp.units}")
        
        # Basic validation
        if mp.value:
            temp_value = mp.value[0] if isinstance(mp.value, list) else mp.value
            if temp_value < -273:  # Below absolute zero
                print(f"    ⚠️  WARNING: Temperature below absolute zero")
            elif temp_value > 1000:  # Unrealistically high for organic compounds
                print(f"    ⚠️  WARNING: Unusually high temperature")
            else:
                print(f"    ✅ Temperature appears reasonable")
        else:
            print(f"    ❌ No valid temperature extracted")
    
    print("\n2. Data completeness analysis:")
    compounds = [r for r in records if isinstance(r, Compound)]
    complete_records = 0
    
    for compound in compounds:
        has_name = bool(compound.names)
        has_properties = any([
            hasattr(compound, attr) and getattr(compound, attr) 
            for attr in ['melting_point', 'boiling_point', 'density']
        ])
        
        if has_name and has_properties:
            complete_records += 1
    
    print(f"  Total compounds: {len(compounds)}")
    print(f"  Complete records (name + properties): {complete_records}")
    print(f"  Completeness rate: {complete_records/len(compounds)*100:.1f}%" if compounds else "N/A")
    
    print("\n" + "-"*50 + "\n")


def integration_examples():
    """Demonstrate integration with external tools and formats."""
    print("=== Integration Examples ===\n")
    
    text = """
    Chemical Database Export
    
    Caffeine (C8H10N4O2):
    - Melting point: 235°C
    - Molecular weight: 194.19 g/mol
    - Solubility: highly soluble in hot water
    
    Aspirin (C9H8O4):
    - Melting point: 135°C  
    - Molecular weight: 180.16 g/mol
    - Solubility: slightly soluble in water
    """
    
    doc = Document(text)
    records = doc.records
    
    print("1. Export to JSON format:")
    json_data = {
        "extraction_metadata": {
            "total_records": len(records),
            "document_elements": len(doc.elements),
            "extraction_timestamp": "2024-01-01T12:00:00Z"
        },
        "records": [record.serialize(primitive=True) for record in records]
    }
    
    print("   JSON structure:")
    print(json.dumps(json_data, indent=2)[:500] + "..." if len(str(json_data)) > 500 else json.dumps(json_data, indent=2))
    
    print("\n2. Export to CSV format:")
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    
    csv_data = []
    csv_data.append("Compound,Formula,Melting_Point_C,Source")
    
    for compound in compounds:
        name = compound.names[0] if compound.names else "Unknown"
        formula = "N/A"  # Would extract from compound data
        
        # Find associated melting point
        mp_value = "N/A"
        for mp in melting_points:
            if mp.value and mp.units:
                mp_value = str(mp.value[0])
                break
        
        csv_data.append(f"{name},{formula},{mp_value},ChemDataExtractor2")
    
    print("   CSV format:")
    for line in csv_data:
        print(f"   {line}")
    
    print("\n3. Database integration format:")
    database_records = []
    
    for record in records:
        db_record = {
            "id": f"{record.__class__.__name__}_{hash(str(record)) % 10000}",
            "type": record.__class__.__name__,
            "data": record.serialize(primitive=True),
            "confidence": getattr(record, 'confidence', 1.0),
            "source": "document_extraction"
        }
        database_records.append(db_record)
    
    print("   Database format:")
    for db_record in database_records[:2]:  # Show first 2
        print(f"   {json.dumps(db_record, indent=4)}")
    if len(database_records) > 2:
        print(f"   ... and {len(database_records)-2} more records")
    
    print("\n" + "-"*50 + "\n")


def main():
    """Run all advanced examples."""
    print("ChemDataExtractor2 Advanced Extraction Examples")
    print("=" * 55 + "\n")
    
    try:
        file_processing_examples()
        contextual_merging_examples()
        table_processing_examples()
        custom_model_examples()
        data_validation_examples()
        integration_examples()
        
        print("All advanced examples completed successfully!")
        
    except Exception as e:
        print(f"Error running advanced examples: {e}")
        raise


if __name__ == "__main__":
    main()
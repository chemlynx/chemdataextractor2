#!/usr/bin/env python3
"""
Basic Usage Examples for ChemDataExtractor2

This script demonstrates the fundamental operations for extracting chemical
data from scientific documents using ChemDataExtractor2.
"""

from chemdataextractor import Document
from chemdataextractor.model.model import Compound, MeltingPoint, BoilingPoint
from chemdataextractor.model.units.temperature import Celsius, Kelvin
import json
from pathlib import Path


def basic_document_processing():
    """Demonstrate basic document processing from different sources."""
    print("=== Basic Document Processing ===\n")
    
    # Example 1: Processing from text string
    print("1. Processing from text string:")
    text = """
    Synthesis of Benzene Derivatives
    
    Benzene (C6H6) is an important aromatic compound with a melting point of 5.5°C 
    and boiling point of 80.1°C. The compound was crystallized from ethanol to 
    yield colorless crystals.
    
    Para-xylene has a melting point of 13.2°C and was obtained in 85% yield.
    """
    
    doc = Document(text)
    records = doc.records
    
    print(f"Found {len(records)} chemical records:")
    for i, record in enumerate(records, 1):
        print(f"  {i}. {record.__class__.__name__}: {dict(record)}")
    
    print("\n" + "-"*50 + "\n")
    
    # Example 2: Filtering specific record types
    print("2. Filtering specific record types:")
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    
    print(f"Compounds found: {len(compounds)}")
    for compound in compounds:
        names = compound.names or ['Unknown']
        print(f"  - {', '.join(names)}")
    
    print(f"Melting points found: {len(melting_points)}")
    for mp in melting_points:
        if mp.value and mp.units:
            print(f"  - {mp.value[0]}°C")
    
    print("\n" + "-"*50 + "\n")


def advanced_record_analysis():
    """Demonstrate advanced record analysis and property access."""
    print("=== Advanced Record Analysis ===\n")
    
    # Create a more complex document
    complex_text = """
    Chemical Properties Study
    
    Table 1. Physical properties of aromatic compounds
    
    Compound        | Melting Point | Boiling Point | Density
    Benzene         | 5.5°C         | 80.1°C        | 0.879 g/mL
    Toluene         | -95.0°C       | 110.6°C       | 0.867 g/mL  
    Para-xylene     | 13.2°C        | 138.4°C       | 0.861 g/mL
    
    Experimental Details:
    Benzene was purified by distillation. The melting point was determined 
    using a Büchi apparatus. All measurements were performed at standard 
    atmospheric pressure.
    """
    
    doc = Document(complex_text)
    records = doc.records
    
    print("1. Complete record analysis:")
    record_types = {}
    for record in records:
        record_type = record.__class__.__name__
        record_types[record_type] = record_types.get(record_type, 0) + 1
    
    for record_type, count in record_types.items():
        print(f"  {record_type}: {count}")
    
    print("\n2. Detailed compound information:")
    compounds = [r for r in records if isinstance(r, Compound)]
    
    for compound in compounds:
        print(f"\nCompound: {compound.names or ['Unknown']}")
        
        # Check for associated melting point
        if hasattr(compound, 'melting_point') and compound.melting_point:
            mp = compound.melting_point
            if mp.value and mp.units:
                print(f"  Melting Point: {mp.value} {mp.units}")
        
        # Check for associated boiling point  
        if hasattr(compound, 'boiling_point') and compound.boiling_point:
            bp = compound.boiling_point
            if bp.value and bp.units:
                print(f"  Boiling Point: {bp.value} {bp.units}")
    
    print("\n" + "-"*50 + "\n")


def data_serialization_examples():
    """Demonstrate different ways to serialize extracted data."""
    print("=== Data Serialization Examples ===\n")
    
    text = """
    Compound Analysis
    
    Caffeine (C8H10N4O2) has a melting point of 235-238°C and is highly soluble 
    in hot water. The molecular weight is 194.19 g/mol.
    """
    
    doc = Document(text)
    records = doc.records
    
    print("1. Raw record structure:")
    for record in records:
        print(f"  {record}")
    
    print("\n2. Serialized as dictionaries:")
    serialized = [record.serialize() for record in records]
    for data in serialized:
        print(f"  {data}")
    
    print("\n3. Serialized as primitive types (JSON-ready):")
    primitive_data = [record.serialize(primitive=True) for record in records]
    for data in primitive_data:
        print(f"  {json.dumps(data, indent=2)}")
    
    print("\n4. Custom filtering and extraction:")
    # Extract just the information we want
    extracted_data = []
    
    compounds = [r for r in records if isinstance(r, Compound)]
    melting_points = [r for r in records if isinstance(r, MeltingPoint)]
    
    for compound in compounds:
        compound_info = {
            'name': compound.names[0] if compound.names else 'Unknown',
            'formula': None,  # Would need to extract from names or labels
            'properties': {}
        }
        
        # Look for associated melting points
        for mp in melting_points:
            if mp.value and mp.units:
                compound_info['properties']['melting_point'] = {
                    'value': mp.value,
                    'units': str(mp.units)
                }
        
        extracted_data.append(compound_info)
    
    print("Custom extracted data:")
    print(json.dumps(extracted_data, indent=2))
    
    print("\n" + "-"*50 + "\n")


def error_handling_examples():
    """Demonstrate proper error handling when processing documents."""
    print("=== Error Handling Examples ===\n")
    
    # Example 1: Handling empty documents
    print("1. Processing empty document:")
    try:
        empty_doc = Document("")
        records = empty_doc.records
        print(f"  Empty document processed successfully: {len(records)} records")
    except Exception as e:
        print(f"  Error processing empty document: {e}")
    
    # Example 2: Handling malformed content
    print("\n2. Processing malformed content:")
    try:
        malformed_doc = Document("Random text with no chemical information")
        records = malformed_doc.records
        print(f"  Malformed content processed: {len(records)} records found")
    except Exception as e:
        print(f"  Error processing malformed content: {e}")
    
    # Example 3: Processing with validation
    print("\n3. Processing with validation:")
    text = "Benzene melting point: not a number°C"
    doc = Document(text)
    records = doc.records
    
    print(f"  Found {len(records)} records from invalid data")
    for record in records:
        if isinstance(record, MeltingPoint):
            print(f"    Melting point value: {record.value} (may be None if invalid)")
    
    print("\n" + "-"*50 + "\n")


def performance_tips():
    """Demonstrate performance optimization techniques."""
    print("=== Performance Tips ===\n")
    
    print("1. Batch processing multiple documents:")
    documents = [
        "Compound A has melting point 100°C",
        "Compound B has melting point 150°C", 
        "Compound C has melting point 200°C"
    ]
    
    all_records = []
    for i, text in enumerate(documents):
        print(f"  Processing document {i+1}...")
        doc = Document(text)
        records = doc.records
        all_records.extend(records)
        print(f"    Found {len(records)} records")
    
    print(f"Total records from batch processing: {len(all_records)}")
    
    print("\n2. Caching expensive operations:")
    text = "Benzene melting point 5.5°C, boiling point 80.1°C"
    doc = Document(text)
    
    # First call - expensive
    print("  First records call (expensive)...")
    records1 = doc.records
    
    # Subsequent calls use the same result if document unchanged
    print("  Second records call (should be cached)...")
    records2 = doc.records
    
    print(f"  Records are identical: {records1 is records2}")
    
    print("\n" + "-"*50 + "\n")


def main():
    """Run all examples."""
    print("ChemDataExtractor2 Basic Usage Examples")
    print("=" * 50 + "\n")
    
    try:
        basic_document_processing()
        advanced_record_analysis()
        data_serialization_examples()
        error_handling_examples()
        performance_tips()
        
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
# ChemDataExtractor2 Examples

This directory contains comprehensive examples demonstrating how to use ChemDataExtractor2 for extracting chemical information from scientific documents.

## Quick Start

### Prerequisites

```bash
# Install ChemDataExtractor2
pip install chemdataextractor2

# Or install from source
pip install -e .
```

### Basic Usage

```python
from chemdataextractor import Document

# Extract data from text
doc = Document("Benzene has a melting point of 5.5°C")
records = doc.records
print(f"Found {len(records)} chemical records")
```

## Example Files

### 1. `basic_usage.py`
**Beginner-friendly introduction to ChemDataExtractor2**

**What you'll learn:**
- Basic document processing from text strings
- Filtering records by type (Compound, MeltingPoint, etc.)
- Accessing extracted properties
- Data serialization for JSON output
- Error handling best practices
- Performance optimization tips

**Run it:**
```bash
python basic_usage.py
```

**Key concepts covered:**
- Document creation and processing
- Record type filtering
- Property access patterns
- Serialization methods
- Batch processing

### 2. `advanced_extraction.py`
**Advanced features and integration scenarios**

**What you'll learn:**
- Processing different file formats (HTML, text, PDF)
- Understanding contextual merging
- Working with table data
- Creating custom models
- Data validation and quality assessment
- Integration with external systems

**Run it:**
```bash
python advanced_extraction.py
```

**Key concepts covered:**
- File format handling
- Contextual information linking
- Table processing
- Custom model development
- Data quality assessment
- Export formats (JSON, CSV, database)

### 3. `property_extraction.py`
**Specialized chemical property extraction**

**What you'll learn:**
- Extracting melting points, boiling points, and solubility data
- Working with units and unit conversions
- Handling value ranges and uncertainties
- Property validation and quality assessment
- Data export and visualization

**Run it:**
```bash
python property_extraction.py
```

**Key concepts covered:**
- Property-specific extraction techniques
- Units handling and dimensional analysis
- Range and uncertainty processing
- Multi-property compound analysis
- Data validation patterns

### 4. `table_processing.py`
**Advanced table data extraction**

**What you'll learn:**
- Processing simple property tables
- Handling complex experimental data tables
- Managing malformed or incomplete tables
- Extracting metadata and context
- Multiple export formats

**Run it:**
```bash
python table_processing.py
```

**Key concepts covered:**
- Table structure recognition
- Cell-based property extraction
- Metadata association
- Error handling for malformed data
- Format-specific export options

### 5. `spectroscopy_extraction.py`
**Spectroscopic data extraction and analysis**

**What you'll learn:**
- Extracting IR, NMR, UV-Vis, and MS data
- Multi-technique spectroscopic characterization
- Data validation for spectroscopic parameters
- Comprehensive analysis workflows
- Export to analysis-ready formats

**Run it:**
```bash
python spectroscopy_extraction.py
```

**Key concepts covered:**
- Spectrum-specific extraction patterns
- Peak assignment and integration
- Multi-technique data correlation
- Spectroscopic data validation
- Analysis-ready data formatting

### 6. `batch_processing.py`
**Large-scale document processing**

**What you'll learn:**
- Sequential vs parallel processing workflows
- Progress tracking and error handling
- Performance optimization strategies
- Result aggregation and analysis
- Scalable processing architectures

**Run it:**
```bash
python batch_processing.py --parallel --create-samples
```

**Key concepts covered:**
- Concurrent processing patterns
- Resource management and optimization
- Error recovery strategies
- Statistical analysis of results
- Production deployment patterns

### 7. `custom_models.py`
**Custom model development**

**What you'll learn:**
- Creating custom dimensions and units
- Developing complex nested models
- Advanced parsing expression design
- Model validation systems
- Schema documentation and reuse

**Run it:**
```bash
python custom_models.py
```

**Key concepts covered:**
- Custom dimension and unit creation
- Complex model architectures
- Advanced parsing grammar
- Validation and quality assurance
- Model documentation patterns

## Common Use Cases

### 1. Processing Research Papers

```python
from chemdataextractor import Document

# Process a PDF research paper
doc = Document.from_file('research_paper.pdf')
records = doc.records

# Extract specific information
compounds = [r for r in records if r.__class__.__name__ == 'Compound']
melting_points = [r for r in records if r.__class__.__name__ == 'MeltingPoint']

print(f"Found {len(compounds)} compounds and {len(melting_points)} melting points")
```

### 2. Batch Processing Multiple Documents

```python
import json
from pathlib import Path

results = []
paper_directory = Path("papers/")

for paper_file in paper_directory.glob("*.pdf"):
    doc = Document.from_file(paper_file)
    records = doc.records
    
    # Serialize for storage
    paper_data = {
        "filename": paper_file.name,
        "records": [r.serialize(primitive=True) for r in records]
    }
    results.append(paper_data)

# Save results
with open("extraction_results.json", "w") as f:
    json.dump(results, f, indent=2)
```

### 3. Table Data Extraction

```python
# Document with tabular data
table_text = """
Physical Properties of Solvents

Compound    | Melting Point | Boiling Point
Benzene     | 5.5°C         | 80.1°C
Toluene     | -95°C         | 110.6°C
"""

doc = Document(table_text)
records = doc.records

# Process table data
for record in records:
    print(f"{record.__class__.__name__}: {record}")
```

### 4. Integration with Databases

```python
import sqlite3

# Create database
conn = sqlite3.connect('chemical_data.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS compounds (
    id INTEGER PRIMARY KEY,
    name TEXT,
    melting_point REAL,
    boiling_point REAL,
    source_document TEXT
)
''')

# Process document and insert data
doc = Document.from_file('chemical_paper.pdf')
compounds = [r for r in doc.records if r.__class__.__name__ == 'Compound']

for compound in compounds:
    name = compound.names[0] if compound.names else 'Unknown'
    mp = None
    bp = None
    
    # Extract associated properties
    if hasattr(compound, 'melting_point') and compound.melting_point:
        mp = compound.melting_point.value[0] if compound.melting_point.value else None
    
    cursor.execute('''
    INSERT INTO compounds (name, melting_point, boiling_point, source_document)
    VALUES (?, ?, ?, ?)
    ''', (name, mp, bp, 'chemical_paper.pdf'))

conn.commit()
conn.close()
```

## Understanding the Output

### Record Types

ChemDataExtractor2 extracts various types of chemical records:

- **Compound**: Chemical entities with names, formulas, labels
- **MeltingPoint**: Melting point data with values and units
- **BoilingPoint**: Boiling point information  
- **IrSpectrum**: Infrared spectroscopy data
- **NmrSpectrum**: NMR spectroscopy information
- **UvvisSpectrum**: UV-Vis spectroscopy data
- **And many more...**

### Record Structure

Each record is a structured object with typed fields:

```python
# Example MeltingPoint record
{
    'MeltingPoint': {
        'raw_value': '5.5',
        'raw_units': '°C', 
        'value': [5.5],
        'units': 'Celsius',
        'error': None
    }
}
```

### Contextual Merging

ChemDataExtractor2 intelligently links related information:

```python
# Input text: "Benzene Analysis\nThe melting point was 5.5°C"
# 
# Output records:
# 1. Compound(names=['Benzene'])
# 2. MeltingPoint(value=[5.5], units='°C')
#
# These may be contextually merged into:
# Compound(names=['Benzene'], melting_point=MeltingPoint(...))
```

## Performance Tips

### 1. File Processing

```python
# Good: Let ChemDataExtractor handle file opening
doc = Document.from_file('paper.pdf')

# Also good: Use context managers for file objects  
with open('paper.pdf', 'rb') as f:
    doc = Document.from_file(f, fname='paper.pdf')
```

### 2. Batch Processing

```python
# Process multiple documents efficiently
documents = ['paper1.pdf', 'paper2.pdf', 'paper3.pdf']
all_records = []

for doc_path in documents:
    doc = Document.from_file(doc_path)
    records = doc.records  # Cache this result
    all_records.extend(records)
    
    # Clear document from memory if processing many files
    del doc
```

### 3. Selective Processing

```python
# Only extract specific record types for better performance
doc = Document.from_file('paper.pdf')
records = doc.records

# Filter early to save memory
compounds = [r for r in records if isinstance(r, Compound)]
melting_points = [r for r in records if r.__class__.__name__ == 'MeltingPoint']

# Don't keep full records list if not needed
del records
```

## Error Handling

### Common Issues and Solutions

**1. File Reading Errors**
```python
try:
    doc = Document.from_file('paper.pdf')
except FileNotFoundError:
    print("File not found - check path")
except PermissionError:
    print("Permission denied - check file permissions")
except Exception as e:
    print(f"Unknown error: {e}")
```

**2. Empty or Invalid Documents**
```python
doc = Document("No chemical information here")
records = doc.records

if not records:
    print("No chemical data found in document")
else:
    print(f"Found {len(records)} records")
```

**3. Invalid Property Values**
```python
melting_points = [r for r in records if r.__class__.__name__ == 'MeltingPoint']

for mp in melting_points:
    if mp.value:
        temp = mp.value[0]
        if temp < -273:  # Below absolute zero
            print(f"Warning: Invalid temperature {temp}")
        else:
            print(f"Valid temperature: {temp}°C")
```

## Advanced Topics

### Custom Models

Create custom models for specialized data extraction:

```python
from chemdataextractor.model.base import BaseModel, StringType, FloatType
from chemdataextractor.model.units.quantity_model import QuantityModel

class DensityModel(QuantityModel):
    """Custom model for density extraction."""
    specifier = StringType()
    # Inherits value, units, error from QuantityModel
    
# Register with appropriate parsers for automatic extraction
```

### Parser Customization

Customize parsing rules for specific document types:

```python
from chemdataextractor.parse.base import BaseParser
from chemdataextractor.parse.elements import W, I, R, Optional

# Define custom parsing grammar
density_phrase = (
    Optional(W('density')).hide() +
    R(r'\d+\.?\d*') +
    (W('g/mL') | W('g/cm³'))
)

# Use in custom parser implementation
```

## Getting Help

- **Documentation**: [ReadTheDocs](https://chemdataextractor.readthedocs.io/)
- **GitHub Issues**: [Report bugs and request features](https://github.com/CambridgeMolecularEngineering/ChemDataExtractor/issues)
- **Community**: Join discussions on the project GitHub page
- **Examples**: These example files demonstrate most common use cases

## Contributing

Found a bug in the examples or want to add more? Please:

1. Fork the repository
2. Create a feature branch
3. Add your example or fix
4. Submit a pull request

## License

These examples are provided under the same MIT license as ChemDataExtractor2.
# Pre-Abstract Model Restriction

## Overview

ChemDataExtractor2 now includes built-in pre-abstract model restriction to prevent extraction models from running on document elements before the abstract section. This feature automatically excludes author names, dates, affiliations, and other metadata from being incorrectly identified as chemical compounds.

## Features

- **Automatic by default**: Pre-abstract restriction is enabled by default
- **Smart abstract detection**: Automatically finds abstract sections by looking for "Abstract" or "Summary" headings
- **Configurable**: Can be disabled when needed for special use cases
- **Performance improvement**: Reduces unnecessary processing of metadata sections
- **Clean results**: Prevents extraction of non-chemical entities as compounds

## Usage

### Default Behavior (Recommended)

```python
from chemdataextractor import Document
from chemdataextractor.model.model import Compound, MeltingPoint

# Restriction is enabled by default
doc = Document.from_file('research_paper.pdf')
doc.models = [Compound, MeltingPoint]

# Author names, dates, etc. are automatically excluded from extraction
records = doc.records
compounds = [r for r in records if isinstance(r, Compound)]
```

### Disabling Restriction

```python
# Disable for special cases where you need extraction from all elements
doc = Document.from_file('paper.pdf', restrict_pre_abstract=False)
doc.models = [Compound, MeltingPoint]

# Or when creating documents manually
doc = Document(
    Title("Chemical Synthesis"),
    Paragraph("Authors: Dr. John Smith"),
    restrict_pre_abstract=False
)
```

### Manual Document Creation

```python
from chemdataextractor.doc.text import Title, Heading, Paragraph

doc = Document(
    Title("Synthesis of CuSO4 Complexes"),
    Paragraph("Authors: Dr. John Smith, Dr. Sarah Johnson"),
    Paragraph("Received: 15 March 2023"),
    Heading("Abstract"),
    Paragraph("We synthesized CuSO4 complexes using H2O as solvent.")
)

doc.models = [Compound, MeltingPoint]

# Elements 0-2 (before abstract) will have no extraction models
# Elements 3+ (abstract and after) will have full extraction models
```

## How It Works

1. **Abstract Detection**: The system searches for elements containing "abstract" or "summary" (case-insensitive)
2. **Fallback Strategy**: If no abstract is found, assumes first 10 elements are pre-content
3. **Model Assignment**:
   - Elements before abstract: Empty models list `[]`
   - Elements at/after abstract: Full models list as specified

## Benefits

### Before (without restriction)
```
Authors: Dr. Al Smith, Dr. Silicon Jones
Keywords: copper, synthesis, catalysis

Found compounds: Al, Silicon, copper
```

### After (with restriction enabled)
```
Authors: Dr. Al Smith, Dr. Silicon Jones  <- No extraction
Keywords: copper, synthesis, catalysis    <- No extraction

Abstract: We used copper catalysts...     <- Extraction enabled

Found compounds: copper
```

## Configuration Options

### Document Creation
```python
# Enable restriction (default)
doc = Document(..., restrict_pre_abstract=True)

# Disable restriction
doc = Document(..., restrict_pre_abstract=False)
```

### File Loading
```python
# Enable restriction (default)
doc = Document.from_file('paper.pdf', restrict_pre_abstract=True)

# Disable restriction
doc = Document.from_file('paper.pdf', restrict_pre_abstract=False)
```

### String Loading
```python
# Enable restriction (default)
doc = Document.from_string(content, restrict_pre_abstract=True)

# Disable restriction
doc = Document.from_string(content, restrict_pre_abstract=False)
```

## Technical Details

### Abstract Detection Logic
1. Search for `Heading` or `Title` elements containing "abstract" or "summary"
2. Case-insensitive matching
3. Fallback to `min(10, len(elements))` if no abstract found

### Model Application
- **Pre-abstract elements**: `element.models = []`
- **Post-abstract elements**: `element.models = [all specified models]`

### Logging
The system logs abstract detection and restriction application:
```
DEBUG: Found abstract at element 5: 'Abstract...'
INFO: Applied pre-abstract restriction: 5 elements restricted, 10 elements with full extraction (abstract at index 5)
```

## Migration from Previous Versions

### No Changes Required
Existing code works without modification - restriction is applied automatically:

```python
# This code works exactly the same, just with better results
doc = Document.from_file('paper.pdf')
doc.models = [Compound, MeltingPoint, Apparatus]
records = doc.records
```

### Disabling for Backward Compatibility
If you need the old behavior for any reason:

```python
# Restore old behavior where extraction runs on all elements
doc = Document.from_file('paper.pdf', restrict_pre_abstract=False)
```

## Examples

### Research Paper Processing
```python
from chemdataextractor import Document
from chemdataextractor.model.model import Compound, MeltingPoint, Apparatus

# Process a research paper
doc = Document.from_file('synthesis_paper.pdf')
doc.models = [Compound, MeltingPoint, Apparatus]

# Extract clean results without author names as compounds
compounds = [r for r in doc.records if isinstance(r, Compound)]
melting_points = [r for r in doc.records if isinstance(r, MeltingPoint)]

print(f"Found {len(compounds)} compounds and {len(melting_points)} melting points")
```

### Batch Processing
```python
import os
from chemdataextractor import Document
from chemdataextractor.model.model import Compound

results = {}

for filename in os.listdir('papers/'):
    if filename.endswith('.pdf'):
        doc = Document.from_file(f'papers/{filename}')
        doc.models = [Compound]

        compounds = [r for r in doc.records if isinstance(r, Compound)]
        results[filename] = len(compounds)

print("Compounds found per paper:", results)
```

## Testing

The feature includes comprehensive tests covering:
- Abstract detection (various formats)
- Model restriction application
- Edge cases (no abstract, empty documents)
- Integration with file loading
- Backward compatibility

Run tests with:
```bash
uv run pytest tests/test_pre_abstract_restriction.py -v
```

## Performance Impact

- **Positive**: Reduced processing time by skipping extraction on metadata elements
- **Positive**: Cleaner results with fewer false positive compounds
- **Minimal**: Abstract detection adds negligible overhead
- **Configurable**: Can be disabled if maximum performance is needed

---

This feature significantly improves the quality of chemical data extraction by preventing common false positives from document metadata while maintaining full extraction capability for the scientific content.
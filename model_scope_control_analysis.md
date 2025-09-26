# Model Scope Control Analysis

## Current Capabilities for Controlling Model Application

Based on the codebase analysis, here are the **existing mechanisms** for controlling where models run and tracking location information:

### 1. Element-Level Model Control ✅ **Currently Available**

Each document element can have its own model configuration:

```python
# Document-level (applies to all elements)
doc.models = [Compound, MeltingPoint, Apparatus]

# Element-specific override
for element in doc.elements:
    if isinstance(element, Title):
        element.models = []  # No models run on titles
    elif isinstance(element, Heading):
        element.models = []  # No models run on headings
    elif isinstance(element, Footnote):
        element.models = [Compound]  # Only compound detection in footnotes
    elif isinstance(element, Caption):
        element.models = [Compound, Apparatus]  # Different set for captions
```

### 2. Built-in Element Restrictions ✅ **Already Implemented**

Some elements have default restrictions:

```python
# From the codebase:
class Title(Text):
    def __init__(self, text, **kwargs):
        super().__init__(text, **kwargs)
        self.models = []  # ← Empty by default

class Heading(Text):
    def __init__(self, text, **kwargs):
        super().__init__(text, **kwargs)
        self.models = []  # ← Empty by default

class Footnote(Text):
    def __init__(self, text, **kwargs):
        super().__init__(text, **kwargs)
        self.models = []  # ← Empty by default
```

### 3. Position Information in Parsers ✅ **Currently Available**

All parsers receive position information during interpretation:

```python
def interpret(self, result: Any, start: int, end: int) -> Generator[BaseModel, None, None]:
    """Interpret parsed results.

    Args:
        result: Parsed result containing data
        start: Starting character position in text
        end: Ending character position in text
    """
```

**However**: This position information is currently **not stored** in the extracted records.

## Implementation Examples

### Example 1: Excluding Compounds from Specific Elements

```python
from chemdataextractor import Document
from chemdataextractor.model.model import Compound, MeltingPoint, Apparatus
from chemdataextractor.doc.text import Title, Heading, Footnote

# Load document
doc = Document.from_file('paper.html')

# Set default models
doc.models = [Compound, MeltingPoint, Apparatus]

# Override for specific element types
for element in doc.elements:
    if isinstance(element, (Title, Heading)):
        # Don't extract compounds from titles/headings
        element.models = [MeltingPoint, Apparatus]
    elif isinstance(element, Footnote):
        # Only extract compounds from footnotes, no melting points
        element.models = [Compound]

# Extract records
records = list(doc.records)
```

### Example 2: Section-Based Model Control

```python
def configure_models_by_section(doc):
    """Configure models based on document sections."""

    current_section = None

    for element in doc.elements:
        # Track current section
        if isinstance(element, Heading):
            current_section = element.text.lower()

        # Configure models based on section
        if current_section and 'experimental' in current_section:
            # Full extraction in experimental section
            element.models = [Compound, MeltingPoint, Apparatus]
        elif current_section and 'introduction' in current_section:
            # Only compounds in introduction
            element.models = [Compound]
        elif current_section and 'references' in current_section:
            # No extraction in references
            element.models = []
        else:
            # Default for other sections
            element.models = [Compound, MeltingPoint]
```

## Tracking Source Location Information

### Current Limitation
Position information (`start`, `end`) is available during parsing but **not preserved** in extracted records.

### Potential Enhancement

To track where compounds were found, you could enhance the parser interpretation:

```python
# Example enhancement (would require model field additions)
class CompoundParser(BaseSentenceParser):
    def interpret(self, result: Any, start: int, end: int) -> Generator[BaseModel, None, None]:
        compound = self.model(
            names=[first(result.xpath("./text()"))],
            # Additional location tracking fields
            source_start_pos=start,
            source_end_pos=end,
            source_element_type=self._get_element_type(),  # Would need implementation
        )
        yield compound
```

## Advanced Use Cases

### Use Case 1: Compound Extraction Restrictions

```python
def restrict_compound_extraction(doc):
    """Restrict compound extraction from certain document parts."""

    for element in doc.elements:
        # Skip compound extraction in:
        if isinstance(element, Title):
            element.models = [model for model in element.models if model != Compound]
        elif isinstance(element, Heading):
            element.models = [model for model in element.models if model != Compound]
        elif hasattr(element, 'text') and 'reference' in element.text.lower():
            element.models = [model for model in element.models if model != Compound]
```

### Use Case 2: Context-Aware Model Selection

```python
def context_aware_models(doc):
    """Apply different models based on document context."""

    in_methods_section = False
    in_results_section = False

    for element in doc.elements:
        if isinstance(element, Heading):
            heading_text = element.text.lower()
            in_methods_section = 'method' in heading_text or 'experimental' in heading_text
            in_results_section = 'result' in heading_text or 'discussion' in heading_text

        # Methods section: focus on apparatus and compounds
        if in_methods_section:
            element.models = [Compound, Apparatus]

        # Results section: focus on measurements
        elif in_results_section:
            element.models = [Compound, MeltingPoint, NmrSpectrum]

        # Other sections: minimal extraction
        else:
            element.models = [Compound]
```

## Summary

**✅ What's Currently Possible:**
1. **Element-level model control** - You can set different models for different document elements
2. **Built-in restrictions** - Some elements (Title, Heading, Footnote) have no models by default
3. **Position information** - Available during parsing (but not stored in records)

**❌ What's Currently Limited:**
1. **Source tracking** - Records don't store which element type they came from
2. **Fine-grained location** - No built-in way to know exact document position of extracted data

**💡 Recommendation:**
The existing element-level model control is quite powerful and should meet most use cases for restricting where compound models run. For source location tracking, you'd need to enhance the models with additional fields to store position/source information.
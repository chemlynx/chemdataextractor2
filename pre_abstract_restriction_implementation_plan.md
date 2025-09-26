# Implementation Plan: Built-in Pre-Abstract Model Restriction

## 🎯 Goal
Prevent all extraction models from running on document parts before the abstract (author names, dates, affiliations, keywords, etc.) by default in the main ChemDataExtractor2 application.

## 📋 Current Analysis

### Where Models Are Set
1. **Document level**: `Document.models` setter propagates to all elements
2. **Element level**: Each element can override with its own models
3. **Default behavior**: All elements inherit document models

### Key Discovery
- **Model dependencies**: MeltingPoint depends on Compound, so excluding Compound requires excluding MeltingPoint
- **Best approach**: Set empty models `[]` for all pre-abstract elements

## 🏗️ Implementation Plan

### Option 1: Modify Document.models setter (RECOMMENDED)
**Location**: `chemdataextractor/doc/document.py` lines 225-234

**Benefits**:
- ✅ Automatic - works for all users without code changes
- ✅ Centralized - one place to implement
- ✅ Configurable - can be disabled via parameter

**Implementation**:
```python
@models.setter
def models(self, value: list[type[BaseModel]]) -> None:
    """Set the models for extraction and propagate to all elements."""
    self._models = value

    # Apply intelligent model restriction
    self._apply_models_with_pre_abstract_restriction(value)

def _apply_models_with_pre_abstract_restriction(self, models: list[type[BaseModel]]) -> None:
    """Apply models with automatic pre-abstract restriction."""
    abstract_index = self._find_abstract_index()

    for i, element in enumerate(self.elements):
        if i < abstract_index:
            # Before abstract: no extraction models
            element.models = []
        else:
            # At/after abstract: full models
            element.models = models
```

### Option 2: Configuration-based approach
**Location**: Add configuration parameter to Document class

**Benefits**:
- ✅ User choice - can be enabled/disabled
- ✅ Backward compatible

**Implementation**:
```python
class Document:
    def __init__(self, *elements, restrict_pre_abstract=True, **kwargs):
        self.restrict_pre_abstract = restrict_pre_abstract
        # ... existing init code
```

### Option 3: Smart element defaults
**Location**: Modify individual element classes (Title, Heading, etc.)

**Benefits**:
- ✅ Element-specific control
- ❌ More complex, multiple files to modify

## 🛠️ Detailed Implementation Steps

### Step 1: Add Abstract Detection Method
```python
def _find_abstract_index(self) -> int:
    """Find the index of the abstract section in the document."""
    for i, element in enumerate(self.elements):
        if isinstance(element, (Heading, Title)):
            text = element.text.lower().strip()
            if any(keyword in text for keyword in ['abstract', 'summary']):
                return i

    # Fallback: assume first 10 elements are pre-content
    return min(10, len(self.elements))
```

### Step 2: Modify Models Setter
```python
@models.setter
def models(self, value: list[type[BaseModel]]) -> None:
    """Set models with intelligent pre-abstract restriction."""
    self._models = value

    if getattr(self, 'restrict_pre_abstract', True):
        self._apply_models_with_restriction(value)
    else:
        # Original behavior
        for element in self.elements:
            element.models = value

def _apply_models_with_restriction(self, models: list[type[BaseModel]]) -> None:
    """Apply models with pre-abstract restriction."""
    abstract_index = self._find_abstract_index()

    for i, element in enumerate(self.elements):
        if i < abstract_index:
            element.models = []  # No models before abstract
        else:
            element.models = models  # Full models after abstract
```

### Step 3: Add Configuration Option
```python
# In Document.__init__
def __init__(self, *elements, restrict_pre_abstract=True, **kwargs):
    # ... existing code
    self.restrict_pre_abstract = restrict_pre_abstract
```

### Step 4: Add Logging for Transparency
```python
def _apply_models_with_restriction(self, models: list[type[BaseModel]]) -> None:
    """Apply models with pre-abstract restriction."""
    abstract_index = self._find_abstract_index()

    log.info(f"Applying pre-abstract restriction: abstract found at element {abstract_index}")

    pre_abstract_count = 0
    for i, element in enumerate(self.elements):
        if i < abstract_index:
            element.models = []
            pre_abstract_count += 1
        else:
            element.models = models

    log.info(f"Restricted models on {pre_abstract_count} pre-abstract elements")
```

## 🧪 Testing Strategy

### Test Cases
1. **Document with abstract**: Verify restriction works
2. **Document without abstract**: Verify fallback works
3. **Configuration disabled**: Verify original behavior
4. **Edge cases**: Empty document, abstract-only document

### Test Implementation
```python
def test_pre_abstract_restriction():
    doc = Document(
        Title("Synthesis of CuSO4"),
        Paragraph("Authors: John Smith"),
        Heading("Abstract"),
        Paragraph("We synthesized CuSO4...")
    )

    doc.models = [Compound, MeltingPoint]

    # Check pre-abstract elements have no models
    assert doc.elements[0].models == []  # Title
    assert doc.elements[1].models == []  # Authors

    # Check post-abstract elements have full models
    assert Compound in doc.elements[3].models  # Abstract paragraph
```

## 📝 Documentation Updates

### User-facing changes
1. **README.md**: Document the new behavior
2. **Examples**: Update examples to show the feature
3. **Migration guide**: How to disable if needed

### Example documentation
```python
# NEW: Pre-abstract restriction is automatic
doc = Document.from_file('paper.html')
doc.models = [Compound, MeltingPoint, Apparatus]
# Author names, dates, etc. are automatically excluded

# To disable (old behavior):
doc = Document.from_file('paper.html', restrict_pre_abstract=False)
doc.models = [Compound, MeltingPoint, Apparatus]
```

## 🎯 Recommendation

**I recommend Option 1 (Modify Document.models setter) with configuration**:

1. **Automatic by default** - Solves the problem for all users
2. **Configurable** - Can be disabled if needed
3. **Clean implementation** - Centralized in one method
4. **Backward compatible** - Existing code works, just better

## 📍 Files to Modify

1. **`chemdataextractor/doc/document.py`** - Main implementation
2. **Tests** - Add comprehensive test coverage
3. **Documentation** - Update user guides

Would you like me to proceed with implementing this plan?
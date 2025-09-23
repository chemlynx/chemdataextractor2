# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChemDataExtractor2 is a comprehensive toolkit for extracting chemical information from scientific literature. This is a typed fork under active development with focus on performance optimization, type safety, and real-world application testing.

## Development Environment

**Python Version**: 3.12+ (defaults to Python 3.12.11 via `.python-version`)

### Setup Commands

- Install uv (if not installed): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Install project with dev dependencies: `uv sync --group dev`
- Run commands in uv environment: `uv run <command>`
- Add new dependencies: `uv add <package>` or `uv add --group dev <package>`

### Testing & Quality Assurance

- Run all tests: `uv run pytest`
- Run specific test: `uv run pytest tests/test_filename.py -v`
- Code formatting: Pre-commit hooks handle ruff formatting automatically
- Type checking: `uv run mypy` (ongoing systematic typing implementation)
- Quality analysis: `uv run ruff check` and `uv run ruff format`

### Git Workflow

- **NEVER push to upstream** (CambridgeMolecularEngineering/ChemDataExtractor2)
- Always push to origin (your fork: chemlynx/ChemDataExtractor2)
- Use feature branches for development
- Current main development branch: `feature/typing-foundation`

## Performance Optimization Work Completed

### Phase 1: Regex Compilation & Caching Optimization ✅ COMPLETED

- **Achievement**: 3.8x → 2.6x performance improvement
- **Implementation**: Created centralized pre-compiled regex pattern registry
- **File**: `chemdataextractor/parse/regex_patterns.py`
- **Impact**: Significant speed improvements across parsing operations

### Phase 2: String Operations Optimization ✅ COMPLETED

- **Achievement**: Fixed critical regex escaping issues
- **Implementation**: Pre-compiled pattern registries with proper escaping
- **Impact**: Resolved 'cliche-ridden' tokenization problems and enhanced performance

### Critical Bug Fixes ✅ COMPLETED

#### ModelList Constructor Issue

- **Problem**: Changed `*models` to `models` during typing work, breaking CEM parsing
- **Solution**: Restored `*models` parameter with proper typing annotations
- **File**: `chemdataextractor/model/base.py`

#### Melting Point Contextual Merging

- **Problem**: MpParser manually extracted fields, losing roles field
- **Solution**: Use contextual merging instead of manual field extraction
- **File**: `chemdataextractor/parse/mp_new.py`

#### Missing Imports for Dynamic Configuration

- **Problem**: Removed imports needed for eval() calls in set_config()
- **Solution**: Restored SentenceTokenizer, WordTokenizer, CrfPosTagger, Lexicon imports
- **File**: `chemdataextractor/doc/text.py`

#### Saccharide Arrow Splitting

- **Problem**: `_is_saccharide_arrow` method couldn't handle nested brackets like `(1→4)]-`
- **Solution**: Fixed regex to handle complex chemical nomenclature patterns
- **File**: `chemdataextractor/nlp/tokenize.py`

## Real-World Application Testing

### RSC Publication Analysis ✅ COMPLETED

- **Test Document**: `/tests/data/D5OB00672D.html` (67K characters, 191 elements)
- **Content**: Quinazolinone synthesis and TLX agonist development research
- **Results**: Successfully extracted comprehensive chemical data

### Extraction Scripts Created

1. **extract_rsc_configurable.py** - User-configurable model selection
   - Options: 'default', 'fast' (no BERT), 'all', custom comma-separated
   - Interactive model selection for different use cases

2. **extract_rsc_article.py** - Comprehensive extraction with all 11 models
   - Complete analysis including compound identification and property extraction

3. **extract_rsc_quick.py** - Fast melting point extraction
   - Avoids BERT initialization for quick results

4. **analyze_rsc_text.py** - Fast regex-based text analysis
   - Completed successfully: found 47 quinazoline compounds, 20 NMR shifts, 24 MS values

5. **rsc_extraction_summary.py** - Capabilities demonstration

### BERT Model Analysis ✅ COMPLETED

- **Model**: SciBERT (scientific domain pre-trained BERT)
- **Training**: Custom chemical entity recognition data
- **Performance**: ~2-3 minutes initialization time
- **Embeddings**: Chemical-specific embeddings and vocabulary
- **Python Compatibility**: Works with Python 3.9-3.12+ (version agnostic)

## Pending Performance Optimizations

The following optimizations are planned but not yet implemented:

1. **Parser trigger_phrase mechanisms** - 2x speedup potential
2. **Replace pickle with joblib** - Faster model serialization
3. **Lazy loading system** - For large data files
4. **Vectorized NLP operations** - NumPy batch processing
5. **Smart caching for document.records** - Intelligent record caching
6. **Memory optimization** - Reduce parse element creation overhead
7. **Async/await support** - Concurrent document processing
8. **Parser compilation system** - Static rule optimization

## Architecture Overview

### Core Processing Pipeline

1. **Document Loading** - HTML/PDF/XML reader support
2. **Element Extraction** - Paragraphs, tables, figures, headings
3. **NLP Processing** - Tokenization, POS tagging, CEM recognition
4. **Parsing** - Rule-based extraction using grammar patterns
5. **Contextual Merging** - Intelligent linking of compounds and properties
6. **Record Serialization** - JSON output for data integration

### Key Components

- **Document** (`chemdataextractor/doc/`) - Central orchestrator and element hierarchy
- **Readers** (`chemdataextractor/reader/`) - Format-specific document readers
- **NLP** (`chemdataextractor/nlp/`) - Chemistry-aware natural language processing
- **Parsing** (`chemdataextractor/parse/`) - Rule-based extraction engine
- **Models** (`chemdataextractor/model/`) - Data models for chemical information
- **RelEx** (`chemdataextractor/relex/`) - Relationship extraction and pattern learning

### Available Extraction Models

1. **Compound** - Chemical compound identification (requires BERT CRF)
2. **MeltingPoint** - Melting point measurements with compound linking
3. **IrSpectrum** - Infrared spectroscopy data
4. **NmrSpectrum** - Nuclear magnetic resonance data
5. **UvvisSpectrum** - UV-Visible spectroscopy
6. **Apparatus** - Experimental apparatus information
7. **GlassTransition** - Glass transition temperature
8. **ElectrochemicalPotential** - Electrochemical measurements
9. **FluorescenceLifetime** - Fluorescence lifetime data
10. **QuantumYield** - Quantum yield measurements
11. **InteratomicDistance** - Structural distance measurements

## Type Annotation Strategy

### Foundation

- **Core TypeVars**: T, ModelT, ElementT for generic types
- **Key Patterns**: BaseType[T], ModelList[RecordT], Protocol classes
- **Progress**: Systematic addition following phased approach

### Implementation Phases

1. **Phase 1** ✅ - Foundation classes (BaseModel, BaseType, Document)
2. **Phase 2** 🔄 - Public APIs and parser framework
3. **Phase 3** - Internal systems and NLP module
4. **Phase 4** - Advanced patterns and metaclass typing

### Quality Standards

- Google-style docstrings for all public APIs
- Type annotations required for new code
- MyPy strict mode compliance for core modules
- Include type information in docstring Args/Returns sections

## Development Guidelines

### Code Quality

- **NEVER create files unless absolutely necessary** - Always prefer editing existing files
- **Follow existing patterns** - Mimic code style, use existing libraries
- **Security first** - Never expose secrets, follow security best practices
- **No unnecessary comments** - Code should be self-documenting

### Testing Requirements

- All critical tests must pass before commits
- Validate on real scientific literature when possible
- Performance improvements must be verified and documented
- Test both positive and edge cases

### Git Practices

- Use descriptive commit messages with proper formatting
- Stage and test changes before committing
- Never force push to shared branches

## Current Status

### Completed Work (Ready for Production)

✅ Phase 1 & 2 performance optimizations (3.8x → 2.6x improvement)
✅ Critical bug fixes (ModelList, contextual merging, imports, tokenization)
✅ Real-world RSC publication testing and validation
✅ Comprehensive extraction script suite
✅ BERT model analysis and Python compatibility validation

### In Progress

🔄 Systematic type annotation implementation
🔄 Documentation and example enhancement

### Next Priorities

📋 Remaining performance optimizations (items 9-16 from original plan)
📋 Production deployment preparation
📋 Extended real-world testing on diverse scientific literature

## Key Files Modified in Recent Work

### Core Framework

- `chemdataextractor/parse/regex_patterns.py` - New centralized pattern registry
- `chemdataextractor/model/base.py` - Fixed ModelList constructor
- `chemdataextractor/doc/text.py` - Restored missing imports
- `chemdataextractor/nlp/tokenize.py` - Fixed saccharide arrow splitting
- `chemdataextractor/parse/mp_new.py` - Fixed contextual merging

### Application Scripts

- `extract_rsc_configurable.py` - User-configurable extraction
- `extract_rsc_article.py` - Comprehensive extraction
- `extract_rsc_quick.py` - Fast melting point extraction
- `analyze_rsc_text.py` - Fast text analysis
- `rsc_extraction_summary.py` - Capabilities summary

This represents a significant enhancement to ChemDataExtractor2's performance, reliability, and real-world applicability for scientific literature processing.

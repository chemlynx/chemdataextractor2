ChemDataExtractor2
==================

ChemDataExtractor2 is a comprehensive toolkit for extracting chemical information from the scientific literature. This is a typed fork with focus on performance optimization, type safety, and real-world application testing.

**Python Support**: 3.9+ (recommended: Python 3.12+)

This project is forked from [CambridgeMolecularEngineering/ChemDataExtractor2](https://github.com/CambridgeMolecularEngineering/ChemDataExtractor2) and includes significant enhancements for production use.

## Installation

### Option 1: Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. Install uv first, then the package:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project and install ChemDataExtractor2
uv init my-cde-project
cd my-cde-project
uv add chemdataextractor2

# Run your extraction scripts
uv run python your_script.py
```

### Option 2: Using conda + pip

Create a conda environment and install with pip:

```bash
# Create and activate environment
conda create -n cde2 python=3.12
conda activate cde2

# Install package
pip install chemdataextractor2
```

### Option 3: Development Installation

For development or to use the latest features:

```bash
git clone https://github.com/your-username/ChemDataExtractor2.git
cd ChemDataExtractor2
uv sync --group dev  # Install with development dependencies
```

## Features

- **HTML, XML and PDF document readers** - Support for major scientific publishers
- **Chemistry-aware natural language processing** - Specialized tokenization and NLP pipeline
- **Chemical named entity recognition** - BERT-based chemical compound identification
- **Rule-based parsing grammars** - Extract properties and spectra data
- **Table parser** - Extract tabulated chemical data
- **Document processing pipeline** - Resolve data interdependencies and relationships
- **Performance optimized** - 3.8x faster than original with regex compilation and caching
- **Type safety** - Comprehensive type annotations for Python 3.12+
- **Real-world tested** - Validated on scientific literature from major publishers

## Quick Start

```python
from chemdataextractor.doc import Document

# Parse a document
doc = Document.from_file('scientific_paper.html')

# Extract all chemical records
for record in doc.records:
    print(record.serialize())

# Extract specific properties
melting_points = doc.records.filter(lambda r: 'MeltingPoint' in r)
compounds = doc.records.filter(lambda r: 'Compound' in r)
```

## Available Extraction Models

- **Compound** - Chemical compound identification
- **MeltingPoint** - Melting point measurements
- **NmrSpectrum** - NMR spectroscopy data
- **IrSpectrum** - Infrared spectroscopy data
- **UvvisSpectrum** - UV-Visible spectroscopy
- **GlassTransition** - Glass transition temperatures
- **ElectrochemicalPotential** - Electrochemical measurements
- **FluorescenceLifetime** - Fluorescence data
- **QuantumYield** - Quantum yield measurements
- **Apparatus** - Experimental apparatus information
- **InteratomicDistance** - Structural measurements

## Examples

See the `scripts/examples/` directory for comprehensive usage examples including:

- RSC journal article processing
- Configurable model selection
- Batch document processing
- Custom extraction workflows

## License

ChemDataExtractor2 is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

This project builds upon the original ChemDataExtractor developed by the Cambridge Molecular Engineering group.

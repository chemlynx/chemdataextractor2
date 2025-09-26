#!/usr/bin/env python3
"""
Debug why setting models on Title elements doesn't work.
"""

import sys
sys.path.insert(0, '/home/dave/code/ChemDataExtractor2')

from chemdataextractor import Document
from chemdataextractor.doc.text import Title, Heading, Paragraph
from chemdataextractor.model.model import Compound, MeltingPoint, Apparatus

def debug_models_setting():
    """Debug the models property behavior."""

    print("🔍 Debugging Models Property Behavior")
    print("=" * 60)

    # Create a title
    title = Title("Synthesis of CuSO4 Complexes")

    print("Initial state:")
    print(f"  title.models: {title.models}")
    print(f"  title._models: {getattr(title, '_models', 'NOT SET')}")

    # Set document-level models
    doc = Document(title)
    doc.models = [Compound, MeltingPoint, Apparatus]

    print(f"\nAfter doc.models = [Compound, MeltingPoint, Apparatus]:")
    print(f"  doc.models: {[m.__name__ for m in doc.models]}")
    print(f"  title.models: {[m.__name__ for m in title.models]}")
    print(f"  title._models: {getattr(title, '_models', 'NOT SET')}")

    # Try to override title models
    print(f"\nTrying to set title.models = [MeltingPoint, Apparatus]")
    title.models = [MeltingPoint, Apparatus]

    print(f"After setting:")
    print(f"  title.models: {[m.__name__ for m in title.models]}")
    print(f"  title._models: {[m.__name__ for m in title._models]}")

    # Check streamlined models
    print(f"  title._streamlined_models: {[m.__name__ for m in title._streamlined_models]}")

    # Test extraction
    print(f"\nTesting extraction:")
    records = list(title.records)
    compounds = [r for r in records if isinstance(r, Compound)]
    print(f"  Records found: {len(records)}")
    print(f"  Compounds found: {len(compounds)}")

    for compound in compounds:
        print(f"    - {compound.serialize()}")

def debug_title_default_behavior():
    """Check if Title has special default behavior."""

    print("\n🎭 Debugging Title Default Behavior")
    print("=" * 60)

    # Check Title class definition
    title = Title("Test CuSO4")

    print("Title class inspection:")
    print(f"  Title.__init__ sets models to: {getattr(title, 'models', 'NOT SET')}")
    print(f"  Title._models: {getattr(title, '_models', 'NOT SET')}")

    # Check if Title overrides anything
    import inspect
    print(f"  Title class methods: {[m for m in dir(title) if 'model' in m.lower()]}")

    # Check parent class
    from chemdataextractor.doc.text import Text
    print(f"  Text class methods: {[m for m in dir(Text) if 'model' in m.lower()]}")

def debug_force_empty_models():
    """Try to force empty models on Title."""

    print("\n🔨 Debugging Force Empty Models")
    print("=" * 60)

    title = Title("Synthesis of CuSO4 Complexes")

    # Set to document first
    doc = Document(title)
    doc.models = [Compound, MeltingPoint, Apparatus]

    print("Before forcing empty:")
    print(f"  title.models: {[m.__name__ for m in title.models]}")

    # Force empty
    title.models = []

    print("After forcing empty:")
    print(f"  title.models: {title.models}")
    print(f"  title._streamlined_models: {title._streamlined_models}")

    # Test extraction
    records = list(title.records)
    print(f"  Records with empty models: {len(records)}")

def main():
    print("🐛 Debugging Models Inheritance and Setting")
    print("=" * 80)

    debug_models_setting()
    debug_title_default_behavior()
    debug_force_empty_models()

if __name__ == '__main__':
    main()
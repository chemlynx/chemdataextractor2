"""
Utility modules for ChemDataExtractor2.

This package provides various utility functions and advanced typing patterns
for enhanced functionality and type safety.
"""

from __future__ import annotations

# Import existing core utilities to maintain backward compatibility
from .core import *  # noqa: F403,F401

# Import advanced typing utilities for Phase 4
from .advanced_typing import (
    MultiParser,
    cache_results,
    create_multi_extractor,
    process_heterogeneous_results,
    timing_decorator,
    validation_decorator,
    with_confidence_scoring,
)

# Re-export core utilities for backward compatibility
from .core import (
    Singleton,
    first,
    flatten,
    memoize,
    memoized_property,
)

__all__ = [
    # Core utilities (backward compatibility)
    "memoized_property",
    "memoize",
    "Singleton",
    "flatten",
    "first",
    # Phase 4a: ParamSpec Decorators
    "cache_results",
    "with_confidence_scoring",
    "timing_decorator",
    "validation_decorator",
    # Phase 4b: TypeVarTuple Classes and Functions
    "MultiParser",
    "create_multi_extractor",
    "process_heterogeneous_results",
]

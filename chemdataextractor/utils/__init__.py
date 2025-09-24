"""
Utility modules for ChemDataExtractor2.

This package provides various utility functions and advanced typing patterns
for enhanced functionality and type safety.
"""

from __future__ import annotations

# Import advanced typing utilities for Phase 4
from .advanced_typing import MultiParser
from .advanced_typing import cache_results
from .advanced_typing import create_multi_extractor
from .advanced_typing import process_heterogeneous_results
from .advanced_typing import timing_decorator
from .advanced_typing import validation_decorator
from .advanced_typing import with_confidence_scoring

# Import existing core utilities to maintain backward compatibility
from .core import *  # noqa: F403,F401

# Re-export core utilities for backward compatibility
from .core import Singleton
from .core import first
from .core import flatten
from .core import memoize
from .core import memoized_property

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

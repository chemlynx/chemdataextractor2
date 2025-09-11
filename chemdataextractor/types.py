"""
Typing foundation for ChemDataExtractor2.

This module provides the core TypeVars, Protocols, and type definitions
used throughout the codebase for robust type annotation support.
"""

from __future__ import annotations

from typing import Any
from typing import Protocol
from typing import TypeVar
from typing import Union

try:
    from typing import NotRequired
    from typing import Self

    from typing_extensions import TypedDict
except ImportError:
    from typing import NotRequired
    from typing import Self
    from typing import TypedDict  # type: ignore[attr-defined]

# Core TypeVars for generic programming
T = TypeVar("T")  # Generic type parameter for BaseType descriptors
ModelT = TypeVar("ModelT", bound="BaseModel")  # For ModelType fields
ElementT = TypeVar("ElementT", bound="BaseElement")  # For Document elements
RecordT = TypeVar("RecordT", bound="BaseModel")  # For ModelList containers

# Forward references (will be resolved at runtime)
BaseModel = "chemdataextractor.model.base.BaseModel"
BaseElement = "chemdataextractor.doc.element.BaseElement"
ContextualRange = "chemdataextractor.model.contextual_range.ContextualRange"


class Serializable(Protocol):
    """Protocol for objects that can be serialized to dictionaries."""

    def serialize(self, primitive: bool = False) -> dict[str, Any]:
        """Serialize object to dictionary representation."""
        ...


class Mergeable(Protocol):
    """Protocol for objects that support contextual merging."""

    def merge_contextual(self, other: Self, distance: ContextualRange) -> bool:
        """Merge contextual fields from another object."""
        ...

    def _compatible(self, other: Self) -> bool:
        """Check if two objects can be merged."""
        ...


# Configuration type definitions
class ParserConfig(TypedDict):
    """Configuration for parser behavior."""

    trigger_phrase: NotRequired[str]
    skip_section_phrase: NotRequired[str]
    allow_section_phrase: NotRequired[str]
    confidence_threshold: NotRequired[float]


class ModelConfig(TypedDict):
    """Configuration for model behavior."""

    parsers: list[Any]  # BaseParser - avoiding circular import
    contextual_range: Any  # ContextualRange
    required: NotRequired[bool]
    contextual: NotRequired[bool]


# Type aliases for common patterns
RecordDict = dict[str, Any]
SerializedRecord = dict[str, RecordDict]
ElementList = list[Any]  # List[BaseElement]
ModelList = list[Any]  # List[BaseModel]

# Enhanced type aliases from Phase 3 work
TokenSpan = tuple[int, int]  # Start and end positions of tokens
TokenList = list[str]  # List of token strings
CEMTag = str  # Chemical entity mention tag (e.g., 'B-CM', 'I-CM')
TokenTags = list[tuple[str, CEMTag]]  # List of (token, tag) pairs
AbbreviationDef = tuple[list[str], list[str], str]  # (definition_tokens, abbrev_tokens, abbrev_str)

# Table processing types
TableData = list[list[Any]]  # Raw table data structure
CDETable = list[Any]  # CDE table with Cell objects (avoiding circular import)
CDETables = list[Any]  # List of CDE tables  
CategoryTable = list[Any]  # Table category data
TableRecords = Any  # ModelList collection (avoiding circular import)

# Contextual merging types  
RangeCount = dict[Any, float]  # Maps ContextualRange types to counts (avoiding circular import)
NumericValue = Union[int, float]  # Numeric values for range calculations

# Parser types
ParseResult = tuple[list[Any], int]  # Parse result with tokens and position
ParserFunction = callable[[ParseResult], bool]  # Function to validate parse results
EntityList = list[Any]  # List of parser elements (avoiding circular import)

__all__ = [
    "T",
    "ModelT", 
    "ElementT",
    "RecordT",
    "BaseModel",
    "BaseElement",
    "ContextualRange",
    "Serializable",
    "Mergeable",
    "ParserConfig",
    "ModelConfig",
    "RecordDict",
    "SerializedRecord",
    "ElementList",
    "ModelList",
    # Enhanced types from Phase 3
    "TokenSpan",
    "TokenList",
    "CEMTag",
    "TokenTags",
    "AbbreviationDef",
    "TableData",
    "CDETable",
    "CDETables",
    "CategoryTable",
    "TableRecords",
    "RangeCount",
    "NumericValue",
    "ParseResult",
    "ParserFunction",
    "EntityList",
]

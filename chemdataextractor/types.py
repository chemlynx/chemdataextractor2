"""
Typing foundation for ChemDataExtractor2.

This module provides the core TypeVars, Protocols, and type definitions
used throughout the codebase for robust type annotation support.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Protocol
from typing import Tuple
from typing import TypeVar
from typing import Union
from typing import runtime_checkable

try:
    from typing import NotRequired
    from typing import Self

    from typing_extensions import TypedDict
except ImportError:
    from typing import NotRequired
    from typing import Self
    from typing import TypedDict

# Enhanced TypeVars for generic programming with proper bounds and constraints
T = TypeVar("T")  # Generic type parameter for BaseType descriptors

# Numeric constraints for quantity fields
NumericT = TypeVar("NumericT", int, float, complex)  # For numeric fields and calculations
Comparable = TypeVar("Comparable", int, float, str)  # For comparable types

# Model hierarchy constraints
ModelT = TypeVar("ModelT", bound="BaseModel")  # For ModelType fields and model operations
ElementT = TypeVar("ElementT", bound="BaseElement")  # For Document elements
RecordT = TypeVar("RecordT", bound="BaseModel")  # For ModelList containers
SerializableT = TypeVar("SerializableT", bound="Serializable")  # For serializable objects

# Parser and processing constraints
ParseableT = TypeVar("ParseableT", bound="Parseable")  # For parseable elements
UnitT = TypeVar("UnitT", bound="Unit")  # For unit types and conversions
DimensionT = TypeVar("DimensionT", bound="Dimension")  # For dimensional analysis

if TYPE_CHECKING:
    from chemdataextractor.doc.element import BaseElement
    from chemdataextractor.model.base import BaseModel
    from chemdataextractor.model.contextual_range import ContextualRange
    from chemdataextractor.model.units.dimension import Dimension
    from chemdataextractor.model.units.unit import Unit

    # BaseParserElement may not exist yet, use generic parsing type
    BaseParserElement = Any
else:
    # Forward references for runtime (will be resolved when needed)
    BaseModel = "chemdataextractor.model.base.BaseModel"
    BaseElement = "chemdataextractor.doc.element.BaseElement"
    ContextualRange = "chemdataextractor.model.contextual_range.ContextualRange"
    Unit = "chemdataextractor.model.units.unit.Unit"
    Dimension = "chemdataextractor.model.units.dimension.Dimension"
    BaseParserElement = "chemdataextractor.parse.base.BaseParserElement"


@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized to dictionaries.

    This protocol defines the interface for objects that can be converted
    to and from dictionary representations for data persistence and exchange.
    """

    def serialize(self, primitive: bool = False) -> Dict[str, Any]:
        """Serialize object to dictionary representation.

        Args:
            primitive: Whether to use primitive types only (no custom objects)

        Returns:
            Dictionary representation of the object
        """
        ...

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Self:
        """Deserialize object from dictionary representation.

        Args:
            data: Dictionary containing object data

        Returns:
            New instance of the object
        """
        ...


@runtime_checkable
class Mergeable(Protocol):
    """Protocol for objects that support contextual merging.

    This protocol defines the interface for objects that can intelligently
    merge their fields with other compatible objects based on contextual distance.
    """

    def merge_contextual(self, other: Self, distance: ContextualRange | None = None) -> bool:
        """Merge contextual fields from another object.

        Args:
            other: The object to merge fields from
            distance: Maximum contextual distance for merging

        Returns:
            True if any fields were successfully merged, False otherwise
        """
        ...

    def can_merge_with(self, other: Self) -> bool:
        """Check if two objects are compatible for merging.

        Args:
            other: The object to check compatibility with

        Returns:
            True if objects can be merged, False otherwise
        """
        ...


@runtime_checkable
class Parseable(Protocol):
    """Protocol for elements that can be parsed for data extraction.

    This protocol defines the interface for objects that can parse text
    and extract structured information using parsing expressions.
    """

    def parse(self, text: str, **kwargs: Any) -> List[BaseModel]:
        """Parse text and extract model instances.

        Args:
            text: The text to parse
            **kwargs: Additional parsing options

        Returns:
            List of extracted model instances
        """
        ...

    @property
    def parse_expression(self) -> BaseParserElement | None:
        """The parsing expression used by this parseable element.

        Returns:
            The parser element, or None if no specific parser is defined
        """
        ...


@runtime_checkable
class ChemicalEntity(Protocol):
    """Protocol for chemical entities with standard properties.

    This protocol defines the interface for objects representing
    chemical compounds, molecules, or other chemical entities.
    """

    @property
    def names(self) -> List[str]:
        """List of names for this chemical entity."""
        ...

    @property
    def labels(self) -> List[str]:
        """List of labels/identifiers for this entity."""
        ...

    def canonical_smiles(self) -> str | None:
        """Get the canonical SMILES representation if available.

        Returns:
            SMILES string or None if not available
        """
        ...


@runtime_checkable
class QuantitativeProperty(Protocol[NumericT]):
    """Protocol for properties with numeric values and units.

    This protocol defines the interface for quantitative properties
    that have values, units, and can be converted between unit systems.
    """

    @property
    def value(self) -> List[NumericT]:
        """Numeric value(s) for this property."""
        ...

    @property
    def units(self) -> Unit | None:
        """Units for the numeric values."""
        ...

    @property
    def error(self) -> NumericT | None:
        """Error/uncertainty values if available."""
        ...

    def convert_to(self, target_unit: Unit) -> Self:
        """Convert to different units.

        Args:
            target_unit: The unit to convert to

        Returns:
            New instance with converted values
        """
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

    parsers: List[Any]  # BaseParser - avoiding circular import
    contextual_range: Any  # ContextualRange
    required: NotRequired[bool]
    contextual: NotRequired[bool]


# Type aliases for common patterns
RecordDict = Dict[str, Any]
SerializedRecord = Dict[str, RecordDict]
ElementList = List[Any]  # List[BaseElement]
ModelList = List[Any]  # List[BaseModel]

# Enhanced type aliases from Phase 3 work
TokenSpan = Tuple[int, int]  # Start and end positions of tokens
TokenList = List[str]  # List of token strings
CEMTag = str  # Chemical entity mention tag (e.g., 'B-CM', 'I-CM')
TokenTags = List[Tuple[str, CEMTag]]  # List of (token, tag) pairs
AbbreviationDef = Tuple[List[str], List[str], str]  # (definition_tokens, abbrev_tokens, abbrev_str)

# Table processing types
TableData = List[List[Any]]  # Raw table data structure
CDETable = List[Any]  # CDE table with Cell objects (avoiding circular import)
CDETables = List[Any]  # List of CDE tables
CategoryTable = List[Any]  # Table category data
TableRecords = Any  # ModelList collection (avoiding circular import)

# Contextual merging types
RangeCount = Dict[Any, float]  # Maps ContextualRange types to counts (avoiding circular import)
NumericValue = Union[int, float]  # Numeric values for range calculations

# Parser types
ParseResult = Tuple[List[Any], int]  # Parse result with tokens and position
ParserFunction = Callable[[ParseResult], bool]  # Function to validate parse results
EntityList = List[Any]  # List of parser elements (avoiding circular import)

__all__ = [
    # Enhanced TypeVars
    "T",
    "NumericT",
    "Comparable",
    "ModelT",
    "ElementT",
    "RecordT",
    "SerializableT",
    "ParseableT",
    "UnitT",
    "DimensionT",
    # Forward references (resolved at runtime)
    "BaseModel",
    "BaseElement",
    "ContextualRange",
    "Unit",
    "Dimension",
    "BaseParserElement",
    # Enhanced Protocols
    "Serializable",
    "Mergeable",
    "Parseable",
    "ChemicalEntity",
    "QuantitativeProperty",
    # Configuration types
    "ParserConfig",
    "ModelConfig",
    # Common type aliases
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

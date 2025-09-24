"""
Typing foundation for ChemDataExtractor2.

This module provides the core TypeVars, Protocols, and type definitions
used throughout the codebase for robust type annotation support.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import Final
from typing import Literal
from typing import Protocol
from typing import TypeVar
from typing import Union
from typing import runtime_checkable

try:
    from typing import NotRequired
    from typing import ParamSpec
    from typing import Self
    from typing import TypeVarTuple

    from typing_extensions import TypedDict
except ImportError:
    from typing import NotRequired
    from typing import Self
    from typing import TypedDict
    from typing_extensions import ParamSpec
    from typing_extensions import TypeVarTuple

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

# Phase 4: Advanced Generic Patterns
P = ParamSpec("P")  # For function signatures in decorators and higher-order functions
Ts = TypeVarTuple("Ts")  # For variadic generics (multiple model types)

# Phase 4a: ParamSpec for advanced callable typing
DecoratorP = ParamSpec("DecoratorP")  # For decorator function signatures
CallbackP = ParamSpec("CallbackP")  # For callback function signatures
ParserP = ParamSpec("ParserP")  # For parser function signatures

# Phase 4b: TypeVarTuple for variadic model collections
ModelTs = TypeVarTuple("ModelTs")  # For multiple model types in parsers
PropertyTs = TypeVarTuple("PropertyTs")  # For multiple property types
ElementTs = TypeVarTuple("ElementTs")  # For multiple element types

# Final constants for ChemDataExtractor
DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.7
MIN_CONFIDENCE_SCORE: Final[float] = 0.0
MAX_CONFIDENCE_SCORE: Final[float] = 1.0
DEFAULT_TIMEOUT_SECONDS: Final[int] = 30
MAX_DOCUMENT_SIZE_MB: Final[int] = 100
DEFAULT_ENCODING: Final[str] = "utf-8"
VERSION_PATTERN: Final[str] = r"\d+\.\d+\.\d+"
CHEMICAL_FORMULA_PATTERN: Final[str] = r"[A-Z][a-z]?(\d+)?(\([A-Z][a-z]?\d*\)\d*)?"
TEMPERATURE_UNITS: Final[tuple[str, ...]] = ("°C", "°F", "K", "celsius", "fahrenheit", "kelvin")
MASS_UNITS: Final[tuple[str, ...]] = ("g", "kg", "mg", "μg", "ng", "lb", "oz")
SUPPORTED_ELEMENTS: Final[frozenset[str]] = frozenset(
    [
        "H",
        "He",
        "Li",
        "Be",
        "B",
        "C",
        "N",
        "O",
        "F",
        "Ne",
        "Na",
        "Mg",
        "Al",
        "Si",
        "P",
        "S",
        "Cl",
        "Ar",
        "K",
        "Ca",
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Ga",
        "Ge",
        "As",
        "Se",
        "Br",
        "Kr",
        "Rb",
        "Sr",
        "Y",
        "Zr",
    ]
)

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

    def serialize(self, primitive: bool = False) -> dict[str, Any]:
        """Serialize object to dictionary representation.

        Args:
            primitive: Whether to use primitive types only (no custom objects)

        Returns:
            Dictionary representation of the object
        """
        ...

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> Self:
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

    def parse(self, text: str, **kwargs: Any) -> list[BaseModel]:
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
    def names(self) -> list[str]:
        """List of names for this chemical entity."""
        ...

    @property
    def labels(self) -> list[str]:
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
    def value(self) -> list[NumericT]:
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


@runtime_checkable
class Cacheable(Protocol):
    """Protocol for objects that support caching operations.

    This protocol defines the interface for objects that can be cached
    and invalidated for performance optimization.
    """

    def cache_key(self) -> str:
        """Generate a unique cache key for this object.

        Returns:
            A unique string identifier for caching
        """
        ...

    def is_cache_valid(self) -> bool:
        """Check if cached data is still valid.

        Returns:
            True if cache is valid, False if needs refresh
        """
        ...

    def invalidate_cache(self) -> None:
        """Invalidate any cached data for this object."""
        ...


@runtime_checkable
class Configurable(Protocol):
    """Protocol for objects that can be configured with settings.

    This protocol defines the interface for objects that accept
    configuration dictionaries and can validate settings.
    """

    def configure(self, config: dict[str, Any]) -> None:
        """Apply configuration settings to this object.

        Args:
            config: Dictionary of configuration settings
        """
        ...

    def get_config(self) -> dict[str, Any]:
        """Get current configuration settings.

        Returns:
            Dictionary of current configuration
        """
        ...

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate configuration settings.

        Args:
            config: Dictionary of configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        ...


@runtime_checkable
class Extractable(Protocol):
    """Protocol for objects that can extract structured data.

    This protocol defines the interface for data extraction operations
    that return confidence-scored results.
    """

    def extract(self, source: str) -> list[dict[str, Any]]:
        """Extract structured data from source text.

        Args:
            source: Source text to extract from

        Returns:
            List of extracted data dictionaries
        """
        ...

    def extract_with_confidence(self, source: str) -> list[tuple[dict[str, Any], float]]:
        """Extract data with confidence scores.

        Args:
            source: Source text to extract from

        Returns:
            List of (data, confidence) tuples
        """
        ...


@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can validate their data.

    This protocol defines the interface for self-validating objects
    that can check their internal consistency and data quality.
    """

    def validate(self) -> bool:
        """Validate the object's data.

        Returns:
            True if data is valid, False otherwise
        """
        ...

    def get_validation_errors(self) -> list[str]:
        """Get detailed validation error messages.

        Returns:
            List of validation error descriptions
        """
        ...

    def is_complete(self) -> bool:
        """Check if the object has all required data.

        Returns:
            True if complete, False if missing required data
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

    parsers: list[Any]  # BaseParser - avoiding circular import
    contextual_range: Any  # ContextualRange
    required: NotRequired[bool]
    contextual: NotRequired[bool]


class ExtractionResult(TypedDict):
    """Structured result from data extraction operations."""

    text: str  # Original text that was extracted from
    value: Any  # Extracted value (could be string, number, etc.)
    confidence: NotRequired[float]  # Confidence score (0.0-1.0)
    units: NotRequired[str]  # Units for numeric values
    error: NotRequired[float]  # Error/uncertainty values
    context: NotRequired[str]  # Surrounding context text
    start_pos: NotRequired[int]  # Start position in source text
    end_pos: NotRequired[int]  # End position in source text


class CompoundData(TypedDict):
    """Structured data for chemical compounds."""

    names: list[str]  # List of compound names
    labels: NotRequired[list[str]]  # List of labels/identifiers
    smiles: NotRequired[str]  # SMILES representation
    inchi: NotRequired[str]  # InChI representation
    formula: NotRequired[str]  # Molecular formula
    properties: NotRequired[dict[str, Any]]  # Associated properties
    confidence: NotRequired[float]  # Identification confidence


class PropertyData(TypedDict):
    """Structured data for chemical properties."""

    property_type: str  # Type of property (e.g., 'melting_point')
    value: list[float]  # Numeric value(s)
    units: NotRequired[str]  # Units of measurement
    error: NotRequired[float]  # Uncertainty/error value
    conditions: NotRequired[dict[str, Any]]  # Experimental conditions
    method: NotRequired[str]  # Measurement method
    reference: NotRequired[str]  # Literature reference
    confidence: NotRequired[float]  # Extraction confidence


class SpectroscopyData(TypedDict):
    """Structured data for spectroscopic measurements."""

    spectrum_type: str  # Type (e.g., 'IR', 'NMR', 'UV-Vis')
    peaks: list[dict[str, Any]]  # List of peak data
    solvent: NotRequired[str]  # Solvent used
    temperature: NotRequired[float]  # Measurement temperature
    frequency_range: NotRequired[tuple[float, float]]  # Frequency range
    instrument: NotRequired[str]  # Instrument used
    conditions: NotRequired[dict[str, Any]]  # Other conditions


class ValidationError(TypedDict):
    """Structured validation error information."""

    field: str  # Field name that failed validation
    message: str  # Error message
    value: Any  # Invalid value
    expected_type: NotRequired[str]  # Expected type/format
    severity: NotRequired[str]  # Error severity level


# Type aliases for common patterns
type RecordDict = dict[str, Any]
type SerializedRecord = dict[str, RecordDict]
type ElementList = list[Any]  # List[BaseElement]
type ModelList = list[Any]  # List[BaseModel]

# Enhanced type aliases from Phase 3 work
type TokenSpan = tuple[int, int]  # Start and end positions of tokens
type TokenList = list[str]  # List of token strings
type CEMTag = str  # Chemical entity mention tag (e.g., 'B-CM', 'I-CM')
type TokenTags = list[tuple[str, CEMTag]]  # List of (token, tag) pairs
type AbbreviationDef = tuple[
    list[str], list[str], str
]  # (definition_tokens, abbrev_tokens, abbrev_str)

# Table processing types
type TableData = list[list[Any]]  # Raw table data structure
type CDETable = list[Any]  # CDE table with Cell objects (avoiding circular import)
type CDETables = list[Any]  # List of CDE tables
type CategoryTable = list[Any]  # Table category data
type TableRecords = Any  # ModelList collection (avoiding circular import)

# Contextual merging types
type RangeCount = dict[
    Any, float
]  # Maps ContextualRange types to counts (avoiding circular import)
type NumericValue = int | float  # Numeric values for range calculations

# Parser types
type ParseResult = tuple[list[Any], int]  # Parse result with tokens and position
type ParserFunction = Callable[[ParseResult], bool]  # Function to validate parse results
type EntityList = list[Any]  # List of parser elements (avoiding circular import)

# Literal types for constants and enums
type PropertyType = Literal[
    "melting_point",
    "boiling_point",
    "glass_transition",
    "density",
    "refractive_index",
    "molecular_weight",
    "solubility",
    "vapor_pressure",
    "dielectric_constant",
    "thermal_conductivity",
]

type SpectrumType = Literal[
    "IR", "NMR", "UV-Vis", "MS", "Raman", "XRD", "XPS", "TGA", "DSC", "GC-MS"
]

type UnitCategory = Literal[
    "temperature",
    "mass",
    "length",
    "volume",
    "pressure",
    "energy",
    "frequency",
    "concentration",
    "time",
    "electrical",
]

type ConfidenceLevel = Literal["high", "medium", "low"]

type ExtractionMode = Literal["strict", "relaxed", "experimental"]

type DocumentType = Literal["html", "xml", "pdf", "txt", "json"]

type ElementType = Literal[
    "paragraph", "heading", "table", "figure", "caption", "list_item", "footnote", "reference"
]

type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Phase 4a: Advanced Callable Types with ParamSpec
type ParserFunction[P: ParamSpec, T] = Callable[P, list[T]]  # Parser with preserved signature
type DecoratedParser[P: ParamSpec, T] = Callable[P, T]  # Decorated function with exact signature
type CacheableFunction[P: ParamSpec, T] = Callable[P, T]  # Function that can be cached
type ConfidenceFunction[P: ParamSpec, T] = Callable[
    P, tuple[T, float]
]  # Function returning confidence

# Phase 4a: Specific decorator type patterns
type CachingDecorator[P: ParamSpec, T] = Callable[
    [CacheableFunction[P, T]], CacheableFunction[P, T]
]
type ConfidenceDecorator[P: ParamSpec, T] = Callable[
    [ParserFunction[P, T]], Callable[P, list[tuple[T, float]]]
]
type ValidationDecorator[P: ParamSpec, T] = Callable[[Callable[P, T]], Callable[P, T]]
type TimingDecorator[P: ParamSpec, T] = Callable[[Callable[P, T]], Callable[P, T]]

# Phase 4b: Variadic Generic Types with TypeVarTuple
type MultiModelParser[*Ts] = Callable[[str], tuple[*Ts]]  # Parser returning multiple model types
type MultiPropertyExtractor[*Ts] = Callable[[str], tuple[*Ts]]  # Multiple property extractors
type VariadicProcessor[*Ts] = Callable[[*Ts], Any]  # Function accepting variable model types
type ModelTuple[*Ts] = tuple[*Ts]  # Tuple of specific model types

# Phase 4b: Advanced collection types
type HeterogeneousResults[*Ts] = dict[str, tuple[*Ts]]  # Results with different types per key
type TypedExtractionResults[*Ts] = dict[PropertyType, tuple[*Ts]]  # Property-specific result types

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
    # Phase 3 Enhanced Protocols
    "Cacheable",
    "Configurable",
    "Extractable",
    "Validatable",
    # Phase 3 Enhanced TypedDicts
    "ExtractionResult",
    "CompoundData",
    "PropertyData",
    "SpectroscopyData",
    "ValidationError",
    # Phase 3 Literal Types
    "PropertyType",
    "SpectrumType",
    "UnitCategory",
    "ConfidenceLevel",
    "ExtractionMode",
    "DocumentType",
    "ElementType",
    "LogLevel",
    # Phase 3 Final Constants
    "DEFAULT_CONFIDENCE_THRESHOLD",
    "MIN_CONFIDENCE_SCORE",
    "MAX_CONFIDENCE_SCORE",
    "DEFAULT_TIMEOUT_SECONDS",
    "MAX_DOCUMENT_SIZE_MB",
    "DEFAULT_ENCODING",
    "VERSION_PATTERN",
    "CHEMICAL_FORMULA_PATTERN",
    "TEMPERATURE_UNITS",
    "MASS_UNITS",
    "SUPPORTED_ELEMENTS",
    # Phase 4 Advanced Generic Patterns
    "P",
    "Ts",
    "DecoratorP",
    "CallbackP",
    "ParserP",
    "ModelTs",
    "PropertyTs",
    "ElementTs",
    # Phase 4a ParamSpec Function Types
    "ParserFunction",
    "DecoratedParser",
    "CacheableFunction",
    "ConfidenceFunction",
    "CachingDecorator",
    "ConfidenceDecorator",
    "ValidationDecorator",
    "TimingDecorator",
    # Phase 4b TypeVarTuple Types
    "MultiModelParser",
    "MultiPropertyExtractor",
    "VariadicProcessor",
    "ModelTuple",
    "HeterogeneousResults",
    "TypedExtractionResults",
]

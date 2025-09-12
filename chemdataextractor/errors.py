"""
Comprehensive error handling system for ChemDataExtractor.

This module provides a hierarchical error system with detailed context information,
validation capabilities, and recovery suggestions for chemical data extraction operations.
"""

from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List


class ChemDataExtractorError(Exception):
    """Base exception for all ChemDataExtractor errors.

    Provides enhanced error reporting with context information, suggestions,
    and support for error chaining and recovery strategies.

    Attributes:
        message: Primary error message
        context: Additional context information
        suggestions: List of suggested solutions
        error_code: Unique error code for programmatic handling
        source_location: Location where error occurred
        original_error: Original exception if this is a wrapped error
    """

    def __init__(
        self,
        message: str,
        *,
        context: Dict[str, Any] | None = None,
        suggestions: List[str] | None = None,
        error_code: str | None = None,
        source_location: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []
        self.error_code = error_code
        self.source_location = source_location
        self.original_error = original_error

    def __str__(self) -> str:
        """Enhanced error message with context and suggestions."""
        lines = [self.message]

        if self.error_code:
            lines.append(f"Error Code: {self.error_code}")

        if self.source_location:
            lines.append(f"Location: {self.source_location}")

        if self.context:
            lines.append("Context:")
            for key, value in self.context.items():
                lines.append(f"  {key}: {value}")

        if self.suggestions:
            lines.append("Suggestions:")
            for suggestion in self.suggestions:
                lines.append(f"  - {suggestion}")

        if self.original_error:
            lines.append(f"Original Error: {self.original_error}")

        return "\n".join(lines)

    def add_context(self, key: str, value: Any) -> ChemDataExtractorError:
        """Add context information to the error.

        Args:
            key: Context key
            value: Context value

        Returns:
            Self for method chaining
        """
        self.context[key] = value
        return self

    def add_suggestion(self, suggestion: str) -> ChemDataExtractorError:
        """Add a suggestion for resolving the error.

        Args:
            suggestion: Suggested solution

        Returns:
            Self for method chaining
        """
        self.suggestions.append(suggestion)
        return self


# === Document Processing Errors ===


class DocumentError(ChemDataExtractorError):
    """Base class for document processing errors."""


class ReaderError(DocumentError):
    """Raised when a reader is unable to read a document.

    This error indicates issues with document parsing, format detection,
    or content extraction from input files.
    """


class DocumentFormatError(ReaderError):
    """Raised when document format is unsupported or corrupted."""


class DocumentStructureError(DocumentError):
    """Raised when document structure is invalid or unexpected."""


# === Model and Data Errors ===


class ModelError(ChemDataExtractorError):
    """Base class for model-related errors."""


class ModelNotFoundError(ModelError):
    """Raised when a required model file could not be found."""


class ModelValidationError(ModelError):
    """Raised when model data validation fails."""


class FieldError(ModelError):
    """Base class for model field-related errors."""


class FieldValidationError(FieldError):
    """Raised when field validation fails."""


class FieldTypeError(FieldError):
    """Raised when field type is incompatible with operation."""


class InferenceError(ModelError):
    """Raised when property inference fails."""


# === Units and Quantities Errors ===


class UnitsError(ChemDataExtractorError):
    """Base class for units and quantities errors."""


class DimensionError(UnitsError):
    """Raised when dimensional analysis fails."""


class UnitConversionError(UnitsError):
    """Raised when unit conversion fails."""


class QuantityValidationError(UnitsError):
    """Raised when quantity validation fails."""


# === Parsing Errors ===


class ParsingError(ChemDataExtractorError):
    """Base class for parsing-related errors."""


class PatternMatchError(ParsingError):
    """Raised when pattern matching fails."""


class ExtractionError(ParsingError):
    """Raised when data extraction fails."""


class TemplateError(ParsingError):
    """Raised when template parsing fails."""


# === NLP Processing Errors ===


class NLPError(ChemDataExtractorError):
    """Base class for NLP processing errors."""


class TokenizationError(NLPError):
    """Raised when tokenization fails."""


class TaggingError(NLPError):
    """Raised when POS tagging or NER fails."""


class DependencyError(NLPError):
    """Raised when dependency parsing fails."""


# === Configuration and Validation Errors ===


class ConfigurationError(ChemDataExtractorError):
    """Raised when configuration is invalid or incomplete.

    The exception raised by any NLP object when it's misconfigured
    (e.g. missing properties, invalid properties, unknown properties).
    Originally implemented by AllenNLP, now enhanced with context.
    """

    def __reduce__(self) -> str | tuple[Any, ...]:
        return type(self), (self.message,)


class ValidationError(ChemDataExtractorError):
    """Base class for input validation errors."""


class SchemaValidationError(ValidationError):
    """Raised when data doesn't match expected schema."""


class RangeValidationError(ValidationError):
    """Raised when values are outside valid ranges."""


class TypeValidationError(ValidationError):
    """Raised when type validation fails."""


# === Recovery and Context Errors ===


class RecoveryError(ChemDataExtractorError):
    """Raised when error recovery strategies fail."""


class ContextualError(ChemDataExtractorError):
    """Base class for errors that depend on context."""


class MergeError(ContextualError):
    """Raised when contextual merging fails."""


class ResolutionError(ContextualError):
    """Raised when entity resolution fails."""


# === Utility Functions ===


def wrap_exception(
    original_error: Exception,
    error_class: type[ChemDataExtractorError] = ChemDataExtractorError,
    message: str | None = None,
    **kwargs: Any,
) -> ChemDataExtractorError:
    """Wrap a generic exception with enhanced ChemDataExtractor error.

    Args:
        original_error: The original exception to wrap
        error_class: ChemDataExtractor error class to use
        message: Override message (defaults to original message)
        **kwargs: Additional arguments for error constructor

    Returns:
        Enhanced error with original exception preserved

    Example:
        >>> try:
        ...     risky_operation()
        ... except ValueError as e:
        ...     raise wrap_exception(e, ValidationError,
        ...                         context={"operation": "data_validation"})
    """
    error_message = message or str(original_error)
    return error_class(error_message, original_error=original_error, **kwargs)


def validate_not_none(value: Any, name: str, *, context: Dict[str, Any] | None = None) -> Any:
    """Validate that a value is not None.

    Args:
        value: Value to validate
        name: Name of the value for error reporting
        context: Additional context for error reporting

    Returns:
        The value if valid

    Raises:
        ValidationError: If value is None

    Example:
        >>> user_input = validate_not_none(user_input, "user_input")
    """
    if value is None:
        raise ValidationError(
            f"{name} cannot be None",
            context=context or {},
            suggestions=[f"Provide a valid {name} value"],
            error_code="VALIDATION_NONE",
        )
    return value


def validate_type(
    value: Any, expected_type: type, name: str, *, context: Dict[str, Any] | None = None
) -> Any:
    """Validate that a value is of expected type.

    Args:
        value: Value to validate
        expected_type: Expected type
        name: Name of the value for error reporting
        context: Additional context for error reporting

    Returns:
        The value if valid

    Raises:
        TypeValidationError: If value is not of expected type

    Example:
        >>> temperature = validate_type(temp_value, float, "temperature")
    """
    if not isinstance(value, expected_type):
        raise TypeValidationError(
            f"{name} must be of type {expected_type.__name__}, got {type(value).__name__}",
            context={
                "expected_type": expected_type.__name__,
                "actual_type": type(value).__name__,
                "value": str(value),
                **(context or {}),
            },
            suggestions=[f"Convert {name} to {expected_type.__name__}"],
            error_code="VALIDATION_TYPE",
        )
    return value


def validate_range(
    value: int | float,
    min_val: int | float | None = None,
    max_val: int | float | None = None,
    name: str = "value",
    *,
    context: Dict[str, Any] | None = None,
) -> int | float:
    """Validate that a numeric value is within specified range.

    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        name: Name of the value for error reporting
        context: Additional context for error reporting

    Returns:
        The value if valid

    Raises:
        RangeValidationError: If value is outside valid range

    Example:
        >>> temperature = validate_range(temp, 0, 1000, "temperature")
    """
    if min_val is not None and value < min_val:
        raise RangeValidationError(
            f"{name} {value} is below minimum value {min_val}",
            context={"value": value, "min_value": min_val, "max_value": max_val, **(context or {})},
            suggestions=[f"Use a {name} value >= {min_val}"],
            error_code="VALIDATION_RANGE_MIN",
        )

    if max_val is not None and value > max_val:
        raise RangeValidationError(
            f"{name} {value} is above maximum value {max_val}",
            context={"value": value, "min_value": min_val, "max_value": max_val, **(context or {})},
            suggestions=[f"Use a {name} value <= {max_val}"],
            error_code="VALIDATION_RANGE_MAX",
        )

    return value

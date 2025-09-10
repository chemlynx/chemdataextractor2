 """
  Typing foundation for ChemDataExtractor2.

  This module provides the core TypeVars, Protocols, and type definitions
  used throughout the codebase for robust type annotation support.
  """

  from __future__ import annotations

  from typing import (
      Any,
      Dict,
      Generic,
      List,
      Optional,
      Protocol,
      Type,
      TypeVar,
      Union,
  )

  try:
      from typing_extensions import NotRequired, Self, TypedDict
  except ImportError:
      from typing import TypedDict  # type: ignore[attr-defined]
      from typing_extensions import NotRequired, Self

  # Core TypeVars for generic programming
  T = TypeVar('T')  # Generic type parameter for BaseType descriptors
  ModelT = TypeVar('ModelT', bound='BaseModel')  # For ModelType fields
  ElementT = TypeVar('ElementT', bound='BaseElement')  # For Document elements
  RecordT = TypeVar('RecordT', bound='BaseModel')  # For ModelList containers

  # Forward references (will be resolved at runtime)
  BaseModel = 'chemdataextractor.model.base.BaseModel'
  BaseElement = 'chemdataextractor.doc.element.BaseElement'
  ContextualRange = 'chemdataextractor.model.contextual_range.ContextualRange'


  class Serializable(Protocol):
      """Protocol for objects that can be serialized to dictionaries."""

      def serialize(self, primitive: bool = False) -> Dict[str, Any]:
          """Serialize object to dictionary representation."""
          ...


  class Mergeable(Protocol):
      """Protocol for objects that support contextual merging."""

      def merge_contextual(
          self,
          other: Self,
          distance: ContextualRange
      ) -> bool:
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
      parsers: List[Any]  # BaseParser - avoiding circular import
      contextual_range: Any  # ContextualRange
      required: NotRequired[bool]
      contextual: NotRequired[bool]


  # Type aliases for common patterns
  RecordDict = Dict[str, Any]
  SerializedRecord = Dict[str, RecordDict]
  ElementList = List[Any]  # List[BaseElement]
  ModelList = List[Any]   # List[BaseModel]

  __all__ = [
      'T', 'ModelT', 'ElementT', 'RecordT',
      'BaseModel', 'BaseElement', 'ContextualRange',
      'Serializable', 'Mergeable',
      'ParserConfig', 'ModelConfig',
      'RecordDict', 'SerializedRecord', 'ElementList', 'ModelList'
  ]

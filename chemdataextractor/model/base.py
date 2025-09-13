"""
Data model for extracted information.

This module provides the foundational classes for ChemDataExtractor's model system,
including BaseModel metaclass-based records and BaseType descriptor fields.
"""

from __future__ import annotations

import copy
import json
import logging
import math
from abc import ABCMeta
from collections.abc import Callable
from collections.abc import MutableSequence
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Generic
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union
from typing import overload

try:
    from typing import Self
except ImportError:
    from typing import Self  # type: ignore[attr-defined]

from ..parse.elements import I
from ..parse.elements import W

# Import type definitions
from ..types import ModelT
from ..types import T
from .confidence_pooling import min_value
from .contextual_range import ContextualRange
from .contextual_range import DocumentRange
from .contextual_range import SentenceRange

if TYPE_CHECKING:
    from ..parse.base import BaseParser
    from ..parse.base import BaseParserElement

log = logging.getLogger(__name__)


class BaseType(Generic[T], metaclass=ABCMeta):
    """Base class for all field types in ChemDataExtractor models.

    BaseType implements the descriptor protocol to provide type-safe field access
    and automatic value processing for model instances.

    Type Parameters:
        T: The type of value this field stores and returns
    """

    # This is assigned by ModelMeta to match the attribute on the Model
    name: Optional[str] = None

    def __init__(
        self,
        default: Optional[T] = None,
        null: bool = False,
        required: bool = False,
        requiredness: float = 1.0,
        contextual: bool = False,
        contextual_range: ContextualRange = DocumentRange(),
        parse_expression: Optional[BaseParserElement] = None,
        updatable: bool = False,
        binding: bool = False,
        ignore_when_merging: bool = False,
        never_merge: bool = False,
    ) -> None:
        """Initialize a BaseType field descriptor.

        Args:
            default: The default value for this field if none is set
            null: Include in serialized output even if value is None
            required: Whether a value is required
            requiredness: Strength of requirement (0.0-1.0), affects confidence
            contextual: Whether this value can be extracted from context
            contextual_range: Maximum distance for contextual merging
            parse_expression: Parser expression for extracting this field
            updatable: Whether parse_expression can be modified during parsing
            binding: Whether submodels must have matching values for this field
            ignore_when_merging: Whether to ignore conflicts during merging
            never_merge: Whether to completely prevent merging for this field
        """
        self.default = copy.deepcopy(default)
        self.null = null
        self.required = required
        self.requiredness = requiredness
        self.contextual = contextual
        self.contextual_range = contextual_range
        self.parse_expression = parse_expression
        self.updatable = updatable
        self.binding = binding
        self.ignore_when_merging = ignore_when_merging
        self.never_merge = never_merge
        if self.parse_expression is None and self.updatable:
            print(
                "No parse_expression supplied but updatable set as True for ",
                type(self),
            )
            print(
                "updatable refers to whether parse_expression can be changed by the document as parsing occurs. Setting updatable to False."
            )
            self.updatable = False
        self.parse_expression = copy.copy(parse_expression)
        self._default_parse_expression = parse_expression
        # When a record is created from a table, these are filled with row/col header category strings
        # which helps merging based on same row/column category
        self.table_row_categories: Optional[List[str]] = None
        self.table_col_categories: Optional[List[str]] = None

    def reset(self) -> None:
        """Reset the parse expression to the initial value."""
        if self.updatable:
            self.parse_expression = copy.copy(self._default_parse_expression)

    @overload
    def __get__(self, instance: None, owner: type[BaseModel]) -> Self:
        ...

    @overload
    def __get__(self, instance: BaseModel, owner: type[BaseModel]) -> T:
        ...

    def __get__(self, instance: Optional[BaseModel], owner: type[BaseModel]) -> Union[T, Self]:
        """Descriptor for retrieving a value from a field in a Model.

        Args:
            instance: The model instance, or None if accessed from class
            owner: The model class

        Returns:
            The field descriptor if accessed from class, otherwise the field value
        """
        # Check if Model class is being called, rather than Model instance
        if instance is None:
            return self
        # Get value from Model instance if available
        value = instance._values.get(self.name)
        # If value is None or empty string then return the default value, if set
        # if value in [None, ''] and self.default is not None:
        #     return self.default
        return value

    def __set__(self, instance: BaseModel, value: Optional[T]) -> None:
        """Descriptor for assigning a value to a field in a Model.

        Args:
            instance: The model instance
            value: The value to assign
        """
        instance._values[self.name] = self.process(value)

    def process(self, value: Any) -> T:
        """Convert an assigned value into the desired data format for this field.

        Args:
            value: The raw value to process

        Returns:
            The processed value in the correct type for this field
        """
        return value

    def serialize(self, value: T, primitive: bool = False) -> Any:
        """Serialize this field value for output.

        Args:
            value: The field value to serialize
            primitive: Whether to serialize to primitive types only

        Returns:
            The serialized representation of the value
        """
        if hasattr(value, "serialize"):
            # i.e. value is a nested model
            return value.serialize(primitive=primitive)
        else:
            return value

    def is_empty(self, value: T) -> bool:
        """Return whether a value is considered empty for this field.

        Args:
            value: The value to check

        Returns:
            True if the value is considered empty, False otherwise
        """
        return False


class StringType(BaseType[Optional[str]]):
    """A string field type that converts values to Unicode strings."""

    def process(self, value: Any) -> Optional[str]:
        """Convert value to a unicode string.

        Useful in case lxml _ElementUnicodeResult are passed from parser.

        Args:
            value: The value to convert to string

        Returns:
            The string representation of the value, or None if value is None
        """
        return str(value) if value is not None else None

    def is_empty(self, value: Optional[str]) -> bool:
        """Check if string value is empty.

        Args:
            value: The string value to check

        Returns:
            True if value is None, empty string, or not a string; False otherwise
        """
        if value is not None and isinstance(value, str) and value:
            return False
        return True


class FloatType(BaseType[Optional[float]]):
    """A floating point number field."""

    def process(self, value: Any) -> Optional[float]:
        """Convert value to a float.

        Args:
            value: The value to convert to float

        Returns:
            The float representation of the value, or None if value is None
        """
        if value is not None:
            return float(value)
        return None

    def is_empty(self, value: Optional[float]) -> bool:
        """Check if float value is empty.

        Args:
            value: The float value to check

        Returns:
            True if value is None; False otherwise
        """
        if value is not None:
            return False
        return True


class ModelType(BaseType[Optional[ModelT]]):
    """A field type for nested model instances.

    Type Parameters:
        ModelT: The type of model this field contains
    """

    def __init__(self, model: type[ModelT], **kwargs: Any) -> None:
        """Initialize a ModelType field.

        Args:
            model: The model class this field will contain
            **kwargs: Additional field configuration options
        """
        self.model_class: type[ModelT] = model
        self.model_name: str = self.model_class.__name__
        super(ModelType, self).__init__(**kwargs)

    def process(self, value: Any) -> Optional[ModelT]:
        """Process a value into a model instance.

        Args:
            value: The value to process

        Returns:
            The model instance if value is of correct type, None otherwise
        """
        if isinstance(value, self.model_class):
            return value
        else:
            return None

    def serialize(
        self, value: Optional[ModelT], primitive: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Serialize the nested model.

        Args:
            value: The model instance to serialize
            primitive: Whether to serialize to primitive types only

        Returns:
            The serialized model, or None if value is None
        """
        if value is not None:
            return value.serialize(primitive=primitive)
        return None

    def is_empty(self, value: Optional[ModelT]) -> bool:
        """Check if the model value is empty.

        Args:
            value: The model instance to check

        Returns:
            True if value is None or the model instance is empty; False otherwise
        """
        if isinstance(value, self.model_class):
            return value.is_empty
        return True


class ListType(BaseType[Optional[List[T]]]):
    """A field type for lists of values processed by a nested field type.

    Type Parameters:
        T: The type of items in the list (determined by the nested field)
    """

    def __init__(
        self,
        field: BaseType[T],
        default: Optional[List[T]] = None,
        sorted_: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize a ListType field.

        Args:
            field: The field type for processing individual list items
            default: Default value for the list (empty list if None)
            sorted_: Whether to keep the list sorted
            **kwargs: Additional field configuration options
        """
        super(ListType, self).__init__(**kwargs)
        self.field: BaseType[T] = field
        self.default: List[T] = default if default is not None else []
        self.sorted: bool = sorted_

    def __set__(self, instance: BaseModel, value: Optional[List[Any]]) -> None:
        """Descriptor for assigning a value to a ListField in a Model.

        Args:
            instance: The model instance
            value: The list value to assign
        """
        # Run process for the nested field type for each value in list
        if value is None:
            instance._values[self.name] = None
        else:
            processed = [self.field.process(v) for v in value]
            if self.sorted:
                processed = sorted(processed)
            instance._values[self.name] = processed

    def serialize(self, value: Optional[List[T]], primitive: bool = False) -> Optional[List[Any]]:
        """Serialize the list field.

        Args:
            value: The list to serialize
            primitive: Whether to serialize to primitive types only

        Returns:
            The serialized list, or None if value is None or empty
        """
        if value:
            return [self.field.serialize(v, primitive=primitive) for v in value]
        else:
            return None

    def is_empty(self, value: Optional[List[T]]) -> bool:
        """Check if the list value is empty.

        Args:
            value: The list value to check

        Returns:
            True if value is None or empty list; False otherwise
        """
        if isinstance(value, list) and len(value) != 0:
            return False
        return True


class InferredProperty(BaseType[T]):
    """
    A property that is inferred from the value of another property via an inferrer function.
    An example is the processing the raw value extracted from a document into a list of floats,
    which can be seen in :class:`~chemdataextractor.model.units.quantity_model.QuantityModel`, where
    :attr:`~chemdataextractor.model.units.quantity_model.QuantityModel.value` is inferred from
    :attr:`~chemdataextractor.model.units.quantity_model.QuantityModel.raw_value`.
    """

    def __init__(
        self,
        field: BaseType[T],
        origin_field: str,
        inferrer: Callable[[Any, BaseModel], T],
        **kwargs: Any,
    ) -> None:
        """Initialize an InferredProperty field.

        Args:
            field: The field type expected as a result of inference
            origin_field: The name of the field from which to infer the value
                         (can be a keypath like 'compound.names')
            inferrer: Function to infer the value. Should have signature:
                     (origin_value, model_instance) -> inferred_value
            **kwargs: Additional field configuration options
        """
        self.field: BaseType[T] = field
        self.origin_field: str = origin_field
        self.inferrer: Callable[[Any, BaseModel], T] = inferrer
        super(InferredProperty, self).__init__(**kwargs)

    def __get__(self, instance: Optional[BaseModel], owner: type[BaseModel]) -> Union[T, Self]:
        """Get the inferred value, computing it if necessary.

        Args:
            instance: The model instance
            owner: The model class

        Returns:
            The field descriptor if accessed from class, otherwise the inferred value
        """
        if instance is None:
            return self
        value = instance._values.get(self.name)
        if value is not None and value != self.default:
            return value

        value = self.inferrer(instance[self.origin_field], instance)
        self.__set__(instance, value)
        if value is None:
            value = self.default
        return value

    def process(self, value: Any) -> T:
        """Process a value using the nested field's processing logic.

        Args:
            value: The value to process

        Returns:
            The processed value
        """
        return self.field.process(value)

    def serialize(self, value: T, primitive: bool = False) -> Any:
        """Serialize the inferred value using the nested field's serialization.

        Args:
            value: The value to serialize
            primitive: Whether to serialize to primitive types only

        Returns:
            The serialized value
        """
        return self.field.serialize(value, primitive=primitive)

    def is_empty(self, value: T) -> bool:
        """Check if the inferred value is empty using the nested field's logic.

        Args:
            value: The value to check

        Returns:
            True if the value is considered empty, False otherwise
        """
        return self.field.is_empty(value)


class SetType(BaseType[Optional[Set[T]]]):
    """A field type for sets of values processed by a nested field type.

    Type Parameters:
        T: The type of items in the set (determined by the nested field)
    """

    def __init__(self, field: BaseType[T], default: Optional[Set[T]] = None, **kwargs: Any) -> None:
        """Initialize a SetType field.

        Args:
            field: The field type for processing individual set items
            default: Default value for the set (empty set if None)
            **kwargs: Additional field configuration options
        """
        super(SetType, self).__init__(**kwargs)
        self.field: BaseType[T] = field
        self.default: Set[T] = default if default is not None else set()

    def __set__(self, instance: BaseModel, value: Optional[Set[Any]]) -> None:
        """Descriptor for assigning a value to a SetField in a Model.

        Args:
            instance: The model instance
            value: The set value to assign
        """
        # Run process for the nested field type for each value in set
        if value is None:
            instance._values[self.name] = None
        else:
            instance._values[self.name] = set(self.field.process(v) for v in value if v is not None)

    def serialize(self, value: Optional[Set[T]], primitive: bool = False) -> Optional[List[Any]]:
        """Serialize the set field to a sorted list for JSON compatibility.

        Args:
            value: The set to serialize
            primitive: Whether to serialize to primitive types only

        Returns:
            A sorted list representation, or None if value is None or empty
        """
        if value is None or len(value) == 0:
            return None
        # A list, instead of a set is needed for easy compatibility with JSON output formats
        # A new sorted list instance ensures the same order for different runs
        # Sorting in place results in an empty list in this case
        rec_list = list(self.field.serialize(v, primitive=primitive) for v in value)
        return sorted(rec_list)

    def is_empty(self, value: Optional[Set[T]]) -> bool:
        """Check if the set value is empty.

        Args:
            value: The set value to check

        Returns:
            True if value is None or empty set; False otherwise
        """
        if isinstance(value, set) and len(value) != 0:
            return False
        return True


class ModelMeta(ABCMeta):
    """Metaclass for BaseModel that collects field descriptors and sets up parsers."""

    def __new__(mcs, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]) -> type[BaseModel]:
        """Create a new model class with field descriptors and parsers configured.

        Args:
            name: The name of the new class
            bases: Base classes
            attrs: Class attributes dictionary

        Returns:
            The new model class
        """
        cls = super(ModelMeta, mcs).__new__(mcs, name, bases, attrs)
        fields: Dict[str, BaseType] = {}

        # Inherit fields from base classes
        for base in bases:
            if hasattr(base, "fields"):
                for field_name, field in base.fields.items():
                    fields[field_name] = copy.copy(field)

        # Add fields from this class
        for attr_name, attr_value in attrs.items():
            if isinstance(attr_value, BaseType):
                # Set the name attribute on the Type to the attribute name on the Model
                attr_value.name = str(attr_name)
                fields[attr_name] = attr_value
        cls.fields = fields

        # Configure parsers
        parsers = []
        for parser in cls.parsers:
            p = copy.copy(parser)
            p.model = cls
            parsers.append(p)
        cls.parsers = parsers
        return cls

    def __setattr__(cls, key: str, value: Any) -> None:
        """Set attribute on model class, handling BaseType fields specially.

        Args:
            key: The attribute name
            value: The attribute value
        """
        if isinstance(value, BaseType):
            value.name = str(key)
            cls.fields[key] = value
        return super(ModelMeta, cls).__setattr__(key, value)

    @property
    def required_fields(cls) -> list[str]:
        """Get a list of all required field paths for this model.

        Returns:
            List of required field names, with nested fields using '__' separator
        """
        output: List[str] = []
        for key, field in cls.fields.items():
            if hasattr(field, "model_class"):
                nest_req_fields = field.model_class.required_fields
                for nrf in nest_req_fields:
                    output.append(key + "__" + nrf)
            else:
                if field.required:
                    output.append(key)
        return output


class BaseModel(metaclass=ModelMeta):
    """
    A base class for representing a model within ChemDataExtractor.
    Each model can have a number of fields that are declared with the class::

        class ExampleModel(BaseModel):
            string_field = StringType()
            number_field = FloatType()

    See the documentation for :class:`~chemdataextractor.model.base.BaseType` for
    more information. These fields are required for ChemDataExtractor to correctly
    identify what to extract and for merging different records for the same model.

    The attributes in the models can then be accessed via either dot notation::

        example_record.string_field

    or dictionary notation::

        example_record["string_field"]

    You can have nexted models, as in the example below, where a
    new class, ``ExampleModel2`` can contain an ``ExampleModel``::

        class ExampleModel2(BaseModel):
            model_field = ModelType(ExampleModel)

    keypath notation can be used to find the nested properties::

        example_record2["model_field.string_field"]
    """

    fields: Dict[str, BaseType] = {}
    parsers: List[BaseParser] = []
    specifier: Optional[BaseType] = None
    _updated: bool = False

    def __init__(self, **raw_data: Any) -> None:
        """"""
        self._values: Dict[str, Any] = {}
        self._confidences: Dict[str, Optional[float]] = {}
        for key, value in raw_data.items():
            setattr(self, key, value)
        # Set defaults
        for key, field in self.fields.items():
            if key not in raw_data:
                setattr(self, key, copy.copy(field.default))
        self._record_method: Optional[str] = None
        self.was_updated: bool = self._updated
        # Keep track of the number of times we've merged contextually.
        # This is then used to diminish the confidence if we've merged many times.
        self._contextual_merge_count: int = 0
        self._no_merge_ranges: Dict[str, ContextualRange] = {}

    @classmethod
    def deserialize(cls, serialized: Dict[str, Any]) -> Self:
        record = cls()
        flattened_serialized = cls._flatten_serialized(serialized)
        cleaned_serialized = [(cls._clean_key(key), value) for (key, value) in flattened_serialized]
        for key, value in cleaned_serialized:
            if isinstance(cls.fields[key[0]], ListType) and isinstance(
                cls.fields[key[0]].field, ModelType
            ):
                model = cls.fields[key[0]].field.model_class
                value = [model.deserialize(val) for val in value]
                record[key] = value
            else:
                record[key] = value
        return record

    @classmethod
    def _flatten_serialized(cls, serialized):
        flattened = []
        for key, value in serialized.items():
            if isinstance(value, dict):
                flattened_for_key = cls._flatten_serialized(value)
                flattened.extend(
                    [([key, *sub_key], sub_value) for (sub_key, sub_value) in flattened_for_key]
                )
            else:
                flattened.append(([key], value))
        return flattened

    @classmethod
    def _clean_key(cls, key):
        # Hack to get rid of bits of keys where the type is included
        return [key_el for key_el in key if key_el.lower() == key_el]

    def get_confidence(self, key, default_confidence=None, pooling_method=min_value):
        if not isinstance(key, list):
            key = self._get_keypath(key)
        if len(key) == 1 and key[0] == "self":
            return self.total_confidence()
        if key[0] in self.fields:
            try:
                attribute = getattr(self, key[0])

                # Should raise an error for empty fields as empty fields cannot have confidences
                if attribute is None or (attribute == [] and len(key) != 1):
                    raise AttributeError()

                if len(key) == 1:
                    confidence = None
                    if isinstance(attribute, BaseModel):
                        confidence = attribute.total_confidence(pooling_method=pooling_method)
                    else:
                        if key[0] in self._confidences:
                            confidence = self._confidences[key[0]]
                    if confidence is not None:
                        return confidence
                    return default_confidence
                else:
                    if isinstance(attribute, list):
                        attribute = attribute[0]
                    return attribute.get_confidence(key[1:])
            except AttributeError:
                return default_confidence
        else:
            raise KeyError(key)

    def set_confidence(self, key, value):
        try:
            if not isinstance(key, list):
                key = self._get_keypath(key)
            if len(key) == 1 and key[0] == "self":
                self._confidences["self"] = value
            elif key[0] in self.fields:
                attribute = getattr(self, key[0])

                # Should raise an error for empty fields as empty fields cannot have confidences
                if attribute is None or (attribute == [] and len(key) != 1):
                    raise AttributeError()

                if len(key) == 1:
                    if isinstance(attribute, BaseModel):
                        attribute._confidences["self"] = value
                    else:
                        self._confidences[key[0]] = value
                else:
                    if isinstance(attribute, list):
                        attribute = attribute[0]
                    return attribute.set_confidence(key[1:], value)
        except AttributeError:
            pass

    def total_confidence(self, pooling_method=min_value, _account_for_merging=False):
        if "self" in self._confidences and self._confidences["self"] is not None:
            return self._confidences["self"]

        total_confidence = pooling_method(self)
        if total_confidence is None:
            # TODO(ti250): Make this configurable instead of arbitrarily being 1
            total_confidence = 1.0
            # return total_confidence

        merging_factor = 1.0
        # Operate on the assumption that each merge decreases confidence by some constant factor?
        # This doesn't seem to make a difference on the photocatalysis dataset-disabling
        # if _account_for_merging:
        #     merging_factor = 0.1 ** self._contextual_merge_count
        requiredness_factor = self._requiredness_factor()
        return total_confidence * merging_factor * requiredness_factor

    def _requiredness_factor(self):
        total_factor = 1.0
        for field_name, field in self.fields.items():
            if field.required and field.requiredness != 1.0:
                if field.is_empty(self._values[field_name]):
                    total_factor *= 1.0 - field.requiredness
                else:
                    total_factor *= 1.0
            if hasattr(field, "model_class") and self._values[field_name] is not None:
                total_factor *= self._values[field_name]._requiredness_factor()
        return total_factor

    @property
    def is_unidentified(self):
        """
        If there is no 'compound' field associated with the model but the compound is contextual
        """
        try:
            if "compound" not in self.fields:
                return False
            if not self.compound.contextual_fulfilled:
                return self.compound.is_unidentified
        except AttributeError:
            return True

    def __repr__(self):
        return "<%s>" % (self.__class__.__name__,)

    def __str__(self):
        return "<%s>" % (self.__class__.__name__,)

    def __eq__(self, other):
        # TODO: Check this actually works as expected (what about default values?)
        if isinstance(other, self.__class__):
            log.debug(self._values, other._values)
            return self._values == other._values
        return False

    def __iter__(self):
        return iter(self.fields)

    def __delattr__(self, attr):
        """Handle deletion of field values by setting to default if specified."""
        # Set to default value
        if attr in self.fields:
            setattr(self, attr, self.fields[attr].default)
        else:
            super(BaseModel, self).__delattr__(attr)

    def __getitem__(self, key):
        """Redirect dictionary-style field access to attribute-style."""
        return self._get_item(key)

    def _get_item(self, key, create_defaults=False):
        """
        A recursive way to items given a key, which can either be a simple property name for a top
        level property (e.g. `names` for a compound), or a keypath to be able to drill down
        a record (e.g. `compound.names`) for a property.
        """
        try:
            if not isinstance(key, list):
                key = self._get_keypath(key)
            if key[0] in self.fields:
                attribute = getattr(self, key[0])

                if (attribute is None or (attribute == [] and len(key) != 1)) and create_defaults:
                    field = self.fields[key[0]]
                    is_list = False
                    while hasattr(field, "field"):
                        if isinstance(field, ListType):
                            is_list = True
                        field = field.field

                    if isinstance(field, ModelType):
                        created_attr = field.model_class()
                    else:
                        created_attr = field("")
                    if is_list:
                        created_attr = [created_attr]
                    attribute = created_attr
                    self[key[0]] = created_attr

                if len(key) == 1:
                    return attribute
                else:
                    if isinstance(attribute, list):
                        attribute = attribute[0]
                    return attribute._get_item(key[1:], create_defaults=create_defaults)
        except AttributeError:
            pass
        raise KeyError(key)

    def __setitem__(self, key, value):
        """Redirect dictionary-style field setting to attribute-style."""
        if not isinstance(key, list):
            key = self._get_keypath(key)
        if key[0] not in self.fields:
            raise KeyError(key)
        target = self
        if len(key) > 1:
            target = self._get_item(key[:-1], create_defaults=True)
            if isinstance(target, list):
                if len(target) == 0:
                    self._get_item(key, create_defaults=True)
                    target = self._get_item(key[:-1], create_defaults=True)[0]
                else:
                    target = target[0]
        return setattr(target, key[-1], value)

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __hash__(self):
        return str(self.serialize()).__hash__()

    def _get_keypath(self, string):
        return string.split(".")

    @classmethod
    def reset_updatables(cls):
        """
        Reset all updatable parse_expressions of properties associated with the class.
        """
        for key, field in cls.fields.items():
            if cls.fields[key].updatable:
                cls.fields[key].reset()
                cls._updated = False

    @classmethod
    def update(cls, definitions, strict=True):
        """Update this Element's updatable attributes with new information from definitions

        Arguments:
            definitions {list} -- list of definitions found in this element
        """
        log.debug("Updating model")
        for definition in definitions:
            for field in cls.fields:
                if cls.fields[field].updatable:
                    matches = [
                        i for i in cls.fields[field].parse_expression.scan(definition["tokens"])
                    ]
                    # print(matches)
                    if any(matches):
                        cls._updated = True
                        if strict:
                            cls.fields[field].parse_expression = cls.fields[
                                field
                            ].parse_expression | W(str(definition["specifier"]))
                        else:
                            cls.fields[field].parse_expression = cls.fields[
                                field
                            ].parse_expression | I(str(definition["specifier"]))
        return

    @property
    def updated(self):
        """
        True/False dependent on if a specifier within the model was updated.
        """
        for field_name, field in self.fields.items():
            if hasattr(field, "model_class"):
                if hasattr(self[field_name], "updated") and self[field_name].was_updated:
                    return True
        return self.was_updated

    def keys(self):
        return list(iter(self))

    def items(self):
        return [(k, getattr(self, k)) for k in self]

    def values(self):
        return [getattr(self, k) for k in self]

    def get(self, key, default=None):
        return getattr(self, key, default)

    @property
    def contextual_fulfilled(self):
        """
        Whether all the contextual fields have been extracted.

        :return: True if all fields have been found, False if not.
        :rtype: bool
        """

        for field_name, field in self.fields.items():
            if hasattr(field, "model_class"):
                if self[field_name] == field.default and field.contextual:
                    return False
                if (
                    hasattr(self[field_name], "contextual_fulfilled")
                    and not self[field_name].contextual_fulfilled
                ):
                    log.debug("Is contextual")
                    return False
            elif field.contextual and self[field_name] == field.default:
                log.debug("Is contextual")
                return False
        log.debug("Not contextual")
        return True

    @property
    def required_fulfilled(self):
        """
        Whether all the required fields have been extracted.

        :return: True if all fields have been found, False if not.
        :rtype: bool
        """
        return self._required_fulfilled(strict=True)

    @property
    def noncontextual_required_fulfilled(self):
        """
        Whether all the non-contextual required fields have been extracted.

        :return: True if all fields have been found, False if not.
        :rtype: bool
        """
        return self._required_fulfilled(strict=False)

    def _required_fulfilled(self, strict):
        for field_name, field in self.fields.items():
            if hasattr(field, "model_class"):
                if (
                    self[field_name] == field.default
                    and field.required
                    and math.isclose(field.requiredness, 1.0)
                ):
                    if not strict and field.contextual:
                        pass
                    else:
                        return False
                if (
                    field.required
                    and field.requiredness == 1.0
                    and hasattr(self[field_name], "required_fulfilled")
                    and not self[field_name].required_fulfilled
                ):
                    if not strict and field.contextual:
                        pass
                    else:
                        log.debug("Required unfulfilled")
                        return False
            elif field.required and field.requiredness == 1.0 and self[field_name] == field.default:
                # print(self.serialize(), field_name, "did not exist")
                if not strict and field.contextual:
                    pass
                else:
                    return False
        return True

    def serialize(self, primitive: bool = False) -> Dict[str, Any]:
        """Convert Model to python dictionary representation.

        This method serializes all non-empty fields of the model into a dictionary
        format suitable for JSON output, database storage, or API responses.

        Args:
            primitive: Whether to use only primitive types (bool, int, float, str, list, dict).
                When True, nested models are serialized recursively to primitive types.
                When False, may include complex objects that aren't JSON-serializable.

        Returns:
            A dictionary with the class name as key and field data as value.
            The structure is: {ClassName: {field_name: field_value, ...}}
            Empty fields are excluded unless explicitly marked as nullable.

        Example:
            >>> from chemdataextractor.model.model import Compound, MeltingPoint
            >>> mp = MeltingPoint(raw_value='80.1', raw_units='°C', value=[80.1])
            >>> mp.serialize()
            {'MeltingPoint': {'raw_value': '80.1', 'raw_units': '°C', 'value': [80.1]}}

            >>> # Serialize with primitive types only
            >>> compound = Compound(names=['benzene'])
            >>> compound.melting_point = mp
            >>> compound.serialize(primitive=True)
            {'Compound': {'names': ['benzene'], 'melting_point': {'raw_value': '80.1', ...}}}

        Note:
            - Fields with None, empty string, or empty list values are excluded by default
            - Use field.null = True to include None values in serialization
            - Nested models are serialized recursively using their own serialize() method
        """
        # Serialize fields to a dict
        data = {}
        for field_name in self:
            value = getattr(self, field_name)
            field = self.fields.get(field_name)
            if value is not None:
                value = field.serialize(value, primitive=primitive)
            # Skip empty fields unless field.null
            if not field.null and value in [None, "", []]:
                continue
            data[field.name] = value
        record = {self.__class__.__name__: data}
        return record

    def to_json(self, *args, **kwargs):
        """Convert Model to JSON."""
        return json.dumps(self.serialize(primitive=True), *args, **kwargs)

    def is_superset(self, other):
        """
        Whether this model instance is a 'superset' of the other model instance.

        A model instance is a 'superset' of another if it satisfies the following conditions:

        - The model instances are of the same type

        - For each of the attributes of the model instances, either:

            - This instance has more information, or

            - Both instances have the same information

        :param other: The other model instance to compare with this model instance
        :type other: BaseModel
        :return: Whether this model instance is a superset of the other model instance
        :rtype: bool
        """
        if type(self) != type(other):
            return False
        for field_name, field in self.fields.items():
            # Method works recursively so it works with nested models
            if hasattr(field, "model_class"):
                if not self[field_name]:
                    if other[field_name]:
                        return False
                elif not other[field_name]:
                    pass
                elif not self[field_name].is_superset(other[field_name]):
                    return False
            else:
                if other[field_name] and self[field_name] != other[field_name]:
                    return False
        return True

    def is_subset(self, other):
        """
        Whether this model instance is a 'subset' of the other model instance.

        A model instance is a 'subset' of another if it satisfies the following conditions:

        - The model instances are of the same type

        - For each of the attributes of the model instances, either:

            - The other instance has more information, or

            - Both instances have the same information

        :param other: The other model instance to compare with this model instance
        :type other: BaseModel
        :return: Whether this model instance is a subset of the other model instance
        :rtype: bool
        """
        return other.is_superset(self)

    def merge_contextual(
        self, other: BaseModel, distance: ContextualRange = SentenceRange()
    ) -> bool:
        """Merge contextual fields from another model within specified distance.

        Merges any fields marked contextual with additional information from other provided that:

        - other is of the same type and they don't have any conflicting fields

        or

        - other is a model type that is part of this model and that field is currently
          set to be the default value or the field can be merged with the other.

        .. note::

            This method mutates the model it's called on **and** returns a boolean.

        Args:
            other: The other model to merge into this model
            distance: Maximum distance for contextual merging

        Returns:
            True if any fields were merged, False otherwise

        Example:
            >>> compound = Compound(names=['benzene'])
            >>> mp = MeltingPoint(value=[80.1], units='°C')
            >>> mp.merge_contextual(compound, distance=SentenceRange())
            True
        """
        # TODO(ti250): Add behaviour to actually take the distance into account

        log.debug(self.serialize())
        log.debug(other.serialize())
        did_merge = False
        should_keep_both_records = self._should_keep_both_records(other)
        if self.contextual_fulfilled:
            return self
        if self._binding_compatible(other):
            # Merging in a model of a different type
            _compatible = False
            if type(self) == type(other) and self._compatible(other):
                _compatible = True
            if type(self) != type(other):
                if type(other) not in type(self).flatten():
                    # If the type of the other is not part of the flattened model,
                    # no point trying to merge
                    return False
                for field_name, field in self.fields.items():
                    if (
                        hasattr(field, "field")
                        and hasattr(field.field, "model_class")
                        and isinstance(other, field.field.model_class)
                    ):
                        log.debug("model class list case")
                        # Basic merging in of lists/sets of models by just creating a list with one element
                        if (
                            not field.never_merge
                            and field.contextual
                            and not self[field_name]
                            and other
                            and distance <= self.contextual_range(field_name)
                            and distance > self.no_merge_range(field_name)
                        ):
                            log.debug(field_name)
                            self[field_name] = [other]
                            # self.merge_confidence(other, field_name)
                            did_merge = True
                    elif (
                        hasattr(field, "model_class")
                        and isinstance(other, field.model_class)
                        and not field.never_merge
                    ):
                        # Merging when there already exists a partial record
                        if (
                            self[field_name] is not None
                            and field.contextual
                            and not self[field_name].contextual_fulfilled
                            and distance <= self.contextual_range(field_name)
                            and distance > self.no_merge_range(field_name)
                        ):
                            log.debug("reconciling model classes")
                            if self[field_name].merge_contextual(other):
                                did_merge = True
                        # Merging when there is no partial record
                        elif (
                            field.contextual
                            and not self[field_name]
                            and other
                            and distance <= self.contextual_range(field_name)
                            and distance > self.no_merge_range(field_name)
                        ):
                            log.debug(field_name)
                            self[field_name] = copy.copy(other)
                            # self.merge_confidence(other, field_name)
                            did_merge = True
            # Case when merging two records of the same type
            elif self._compatible(other):
                for field_name, field in self.fields.items():
                    if (
                        field.contextual
                        and not field.never_merge
                        and not self[field_name]
                        and other.get(field_name, None)
                        and distance <= self.contextual_range(field_name)
                        and distance > self.no_merge_range(field_name)
                    ):
                        self[field_name] = other[field_name]
                        self.merge_confidence(other, field_name)
                        did_merge = True
        self._consolidate_binding()
        if did_merge:
            self._contextual_merge_count += 1
            if "self" in other._confidences:
                self.merge_confidence(other, "self")
            if should_keep_both_records:
                did_merge = False
        return did_merge

    def contextual_range(self, field_name: str) -> ContextualRange:
        """Get the contextual range for a field.

        Override this method to allow for contextual ranges to change with time.

        Args:
            field_name: The name of the field for which to calculate the contextual range

        Returns:
            The contextual range for the field given the current record
        """
        return self.fields[field_name].contextual_range

    def no_merge_range(self, field_name: str) -> ContextualRange:
        """Get the range within which the model should not merge the field.

        Args:
            field_name: The name of the field for which to calculate the no-merge range

        Returns:
            The contextual range within which the field should not be merged
        """
        if field_name in self._no_merge_ranges:
            return self._no_merge_ranges[field_name]
        return 0 * SentenceRange()

    def merge_all(
        self, other: BaseModel, strict: bool = True, distance: ContextualRange = SentenceRange()
    ) -> bool:
        """Merge all compatible fields from another model, regardless of contextual setting.

        Merges any properties between other and self, regardless of whether that field is contextual.
        Checks to make sure that there are no conflicts between the values contained in self and those in other.

        .. note::

            This method mutates the model it's called on **and** returns a boolean.

        Args:
            other: The other model to merge into this model
            strict: Whether to perform strict compatibility checking
            distance: Maximum distance for merging

        Returns:
            True if any fields were merged, False otherwise
        """

        log.debug(self.serialize())
        log.debug(other.serialize())
        did_merge = False
        should_keep_both_records = self._should_keep_both_records(other)
        if self._binding_compatible(other):
            if type(self) != type(other):
                if type(other) not in type(self).flatten():
                    # If the type of the other is not part of the flattened model,
                    # no point trying to merge
                    return False
                for field_name, field in self.fields.items():
                    if (
                        hasattr(field, "field")
                        and hasattr(field.field, "model_class")
                        and isinstance(other, field.field.model_class)
                        and not field.never_merge
                    ):
                        log.debug("model list case")
                        if self[field_name] and distance > self.no_merge_range(field_name):
                            for el in self[field_name]:
                                if el.merge_all(other):
                                    did_merge = True
                        elif (
                            not self[field_name]
                            and other
                            and distance > self.no_merge_range(field_name)
                        ):
                            log.debug(field_name)
                            self[field_name] = [copy.copy(other)]
                            did_merge = True
                    elif (
                        hasattr(field, "model_class")
                        and isinstance(other, field.model_class)
                        and not field.never_merge
                    ):
                        log.debug("model class case")
                        if self[field_name] and distance > self.no_merge_range(field_name):
                            if self[field_name].merge_all(other):
                                did_merge = True
                        elif (
                            not self[field_name]
                            and other
                            and distance > self.no_merge_range(field_name)
                        ):
                            log.debug(field_name)
                            self[field_name] = copy.copy(other)
                            did_merge = True
            elif self._compatible(other):
                for field_name, field in self.fields.items():
                    if (
                        not self[field_name]
                        and other.get(field_name, None)
                        and not field.never_merge
                        and distance > self.no_merge_range(field_name)
                    ):
                        did_merge = True
                        self[field_name] = other[field_name]
                        self.merge_confidence(other, field_name)
        self._consolidate_binding()
        if did_merge:
            if "self" in other._confidences:
                self.merge_confidence(other, "self")
            if should_keep_both_records:
                did_merge = False
        return did_merge

    def merge_confidence(self, other: BaseModel, field_name: str) -> None:
        """Merge confidence values for a specific field.

        Keeps the lower confidence value between this model and the other.

        Args:
            other: The other model to merge confidence from
            field_name: The field name to merge confidence for
        """
        # Keep the lower confidence value
        self_confidence = self.get_confidence(field_name, pooling_method=lambda x: None)
        other_confidence = other.get_confidence(field_name, pooling_method=lambda x: None)
        if self_confidence is None and other_confidence is not None:
            self.set_confidence(field_name, other_confidence)
        elif self_confidence is not None and other_confidence is not None:
            new_confidence = (
                self_confidence if self_confidence < other_confidence else other_confidence
            )
            self.set_confidence(field_name, new_confidence)

    def _compatible(self, other: BaseModel) -> bool:
        """Check whether two records are compatible for merging.

        This means no conflicting fields, unless `ignore_when_merging` is set.

        Args:
            other: The other model to check compatibility with

        Returns:
            True if models are compatible for merging, False otherwise
        """
        match = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, field in self.fields.items():
                if isinstance(field, ModelType):
                    if (
                        not field.ignore_when_merging
                        and self[field_name] is not None
                        and other[field_name] is not None
                        and not self[field_name]._compatible(other[field_name])
                    ):
                        match = False
                        break
                elif isinstance(field, ListType) or isinstance(field, SetType):
                    if (
                        not field.ignore_when_merging
                        and self[field_name] is not None
                        and len(self[field_name])
                        and other[field_name] is not None
                        and len(other[field_name])
                        and self[field_name] != other[field_name]
                    ):
                        match = False
                        break
                else:
                    if (
                        not field.ignore_when_merging
                        and self[field_name] is not None
                        and other[field_name] is not None
                        and self[field_name] != other[field_name]
                    ):
                        match = False
                        break
        return match

    def can_merge_with(self, other: BaseModel) -> bool:
        """Check if two models are compatible for merging.

        This is the public interface method required by the Mergeable protocol.
        It wraps the internal _compatible method with additional type checking.

        Args:
            other: The model to check compatibility with

        Returns:
            True if objects can be merged, False otherwise
        """
        if not isinstance(other, BaseModel):
            return False

        return (
            type(self) == type(other)
            and self._binding_compatible(other)
            and self._compatible(other)
        )

    def _compatible_legacy(self, other):
        match = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, field in self.fields.items():
                if (
                    not field.ignore_when_merging
                    and self[field_name] is not None
                    and other[field_name] is not None
                    and self[field_name] != other[field_name]
                ):
                    match = False
                    break
        return match

    def _should_keep_both_records(self, other: BaseModel) -> bool:
        """Determine if both records should be kept after merging.

        Args:
            other: The other model to check against

        Returns:
            True if both records should be preserved, False otherwise
        """
        should_keep_both = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            for field_name, field in self.fields.items():
                if isinstance(field, ModelType):
                    if (
                        field.ignore_when_merging
                        and self[field_name] is not None
                        and other[field_name] is not None
                        and not self[field_name]._compatible(other[field_name])
                    ):
                        should_keep_both = True
                        break
                else:
                    if (
                        field.ignore_when_merging
                        and self[field_name] is not None
                        and other[field_name] is not None
                        and self[field_name] != other[field_name]
                    ):
                        should_keep_both = True
                        break
        return should_keep_both

    @classmethod
    def flatten(cls, include_inferred=True):
        """
        A set of all models that are associated with this model.
        For example, if we have a model like the following with multiple submodels:

        .. code-block:: python

            class A(BaseModel):
                pass

            class B(BaseModel):
                a = ModelType(A)

            class C(BaseModel):
                b = ModelType(B)

        then `C.flatten()` would give the result::

            set(C, B, A)

        :return: The set of all models associated with this model.
        :rtype: set(BaseModel)
        """
        model_set = {cls}
        for field_name, field in cls.fields.items():
            while hasattr(field, "field") and (
                include_inferred or not isinstance(field, InferredProperty)
            ):
                if hasattr(field, "model_class"):
                    model_set.update(field.model_class.flatten(include_inferred=include_inferred))
                field = field.field
            if hasattr(field, "model_class"):
                model_set.update(field.model_class.flatten(include_inferred=include_inferred))
        log.debug(model_set)
        return model_set

    def _flatten_instance(self, include_inferred=True):
        """
        A set of all records that are associated with this record.
        Essentially, an instance version of the flatten classmethod.
        For example, if we have a model like the following with multiple submodels:

        .. code-block:: python

            class A(BaseModel):
                pass

            class B(BaseModel):
                a = ModelType(A)

            class C(BaseModel):
                b = ModelType(B)

            a = A()
            b = B(a=a)
            c = C(b=b)

        then `C._flatten_instance()` would give the result::

            set(c, b, a)

        :return: The set of all records associated with this record.
        :rtype: set(BaseModel instances)
        """
        subrecords_set = {self}
        for field_name, field in self.fields.items():
            while hasattr(field, "field") and (
                include_inferred or not isinstance(field, InferredProperty)
            ):
                if hasattr(field, "model_class"):
                    break
                field = field.field
            if hasattr(field, "model_class") and self[field_name]:
                subrecord = self[field_name]
                if isinstance(subrecord, list):
                    for list_el in subrecord:
                        subrecords_set.update(
                            list_el._flatten_instance(include_inferred=include_inferred)
                        )
                else:
                    subrecords_set.update(
                        subrecord._flatten_instance(include_inferred=include_inferred)
                    )
        return subrecords_set

    @property
    def binding_properties(self) -> dict[str, Any]:
        """Get all binding properties in this model and their values.

        .. note::

            This function only returns those properties that are immediately binding for this
            model, and not for any submodels.

        Returns:
            Dictionary with the names of all binding fields as keys and their values
        """
        binding_properties: Dict[str, Any] = {}
        for field_name, field in self.fields.items():
            if field.binding and self[field_name]:
                binding_properties[field_name] = self[field_name]
        return binding_properties

    def _binding_compatible(
        self, other: BaseModel, binding_properties: Optional[dict[str, Any]] = None
    ) -> bool:
        """Check whether two models are compatible in terms of their binding properties.

        For example, if this model had a compound associated with it and the field was binding,
        a model that is associated with another compound will not be merged in.

        Args:
            other: The other model that will be checked for compatibility
            binding_properties: Any binding properties from a model that contains this model

        Returns:
            Whether the two models are compatible in terms of their binding properties
        """
        if binding_properties is None:
            binding_properties = self.binding_properties
        if not binding_properties:
            return True

        if type(other) == type(self):
            for field_name, field in binding_properties.items():
                if other[field_name] != binding_properties[field_name]:
                    return False
        elif not other:
            pass
        else:
            for field_name, field in other.fields.items():
                if field_name in binding_properties:
                    if other[field_name]:
                        if not (
                            binding_properties[field_name].is_superset(other[field_name])
                            or binding_properties[field_name].is_subset(other[field_name])
                        ):
                            return False
                elif hasattr(field, "model_class"):
                    if not self._binding_compatible(other[field_name]):
                        return False
        return True

    def _consolidate_binding(self, binding_properties: Optional[dict[str, Any]] = None) -> None:
        """Consolidate binding properties across model fields.

        Args:
            binding_properties: Binding properties to consolidate
        """
        # TODO: This doesn't update all the confidences for the submodels yet
        if binding_properties is None:
            binding_properties = self.binding_properties
        if binding_properties == {}:
            return
        for field_name, field in self.fields.items():
            if field_name in binding_properties:
                self[field_name] = binding_properties[field_name]
            elif hasattr(field, "model_class") and self[field_name]:
                self[field_name]._consolidate_binding(binding_properties)

    @property
    def record_method(self):
        """
        Description (string) of which method was used to create this record.
        """
        return self._record_method

    @record_method.setter
    def record_method(self, text):
        if not isinstance(text, str):
            raise TypeError("Record method description is not string.")
        self._record_method = text

    def _clean(self, clean_contextual=True):
        """
        Removes any subrecords where the required properties have not been fulfilled.

        clean_contextual determines whether contextual fields that are unfulfilled are
        removed or not.
        """
        for field_name, field in self.fields.items():
            if hasattr(field, "model_class") and self[field_name]:
                self[field_name]._clean(clean_contextual=clean_contextual)
                if clean_contextual:
                    if not self[field_name].required_fulfilled:
                        self[field_name] = field.default
                else:
                    if not self[field_name].noncontextual_required_fulfilled:
                        self[field_name] = field.default

    @classmethod
    def _all_keypaths(cls, include_model_lists=True):
        all_keypaths = []
        for field_name, field in cls.fields.items():
            if include_model_lists:
                while hasattr(field, "field"):
                    field = field.field
            if hasattr(field, "model_class"):
                sub_keypaths = field.model_class._all_keypaths()
                for keypath in sub_keypaths:
                    all_keypaths.append(field_name + "." + keypath)
            else:
                all_keypaths.append(field_name)
        return all_keypaths

    @property
    def is_empty(self):
        for field_name, field_type in self.fields.items():
            if not field_type.is_empty(self[field_name]):
                return False
        return True


class ModelList(MutableSequence[ModelT], Generic[ModelT]):
    """Type-safe wrapper around a list of Model objects with enhanced operations.

    This generic container provides type safety for collections of model instances
    and supports advanced operations like contextual merging and serialization.

    Type Parameters:
        ModelT: The type of models contained in this list (bound to BaseModel)
    """

    def __init__(self, models: Optional[Iterable[ModelT]] = None) -> None:
        """Initialize a ModelList with optional model instances.

        Args:
            models: Iterable of model instances to initialize with
        """
        if models is None:
            self.models: List[ModelT] = []
        else:
            self.models = list(models)

    @overload
    def __getitem__(self, index: int) -> ModelT:
        ...

    @overload
    def __getitem__(self, index: slice) -> ModelList[ModelT]:
        ...

    def __getitem__(self, index: Union[int, slice]) -> Union[ModelT, ModelList[ModelT]]:
        """Get item(s) from the list with proper type annotation.

        Args:
            index: Integer index or slice object

        Returns:
            Single model for int index, ModelList for slice
        """
        result = self.models[index]
        if isinstance(index, slice):
            return ModelList(result)
        return result

    def __setitem__(self, index: Union[int, slice], value: Union[ModelT, Iterable[ModelT]]) -> None:
        """Set item(s) in the list with type safety.

        Args:
            index: Integer index or slice object
            value: Model instance or iterable of models
        """
        self.models[index] = value

    def __delitem__(self, index: Union[int, slice]) -> None:
        """Delete item(s) from the list.

        Args:
            index: Integer index or slice object
        """
        del self.models[index]

    def __len__(self) -> int:
        """Get the number of models in the list.

        Returns:
            Number of model instances
        """
        return len(self.models)

    def __iter__(self) -> Iterator[ModelT]:
        """Iterate over the model instances.

        Returns:
            Iterator over model instances
        """
        return iter(self.models)

    def __repr__(self) -> str:
        """String representation of the ModelList.

        Returns:
            String representation
        """
        return self.models.__repr__()

    def __str__(self) -> str:
        """String conversion of the ModelList.

        Returns:
            String representation
        """
        return self.models.__str__()

    def __contains__(self, element: object) -> bool:
        """Check if an element is in the ModelList.

        Args:
            element: Element to check for

        Returns:
            True if element is in the list
        """
        log.debug(element.serialize())
        log.debug(self.serialize())
        log.debug(self.models.__contains__(element))
        return self.models.__contains__(element)

    def insert(self, index: int, value: ModelT) -> None:
        """Insert a model at the specified index.

        Args:
            index: Index to insert at
            value: Model instance to insert
        """
        self.models.insert(index, value)

    def append(self, value: ModelT) -> None:
        """Append a model to the end of the list.

        Args:
            value: Model instance to append
        """
        self.models.append(value)

    def extend(self, values: Iterable[ModelT]) -> None:
        """Extend the list with multiple models.

        Args:
            values: Iterable of model instances to add
        """
        self.models.extend(values)

    def serialize(self, primitive: bool = False) -> List[Dict[str, Any]]:
        """Serialize to a list of python dictionaries.

        Args:
            primitive: Whether to use primitive types only

        Returns:
            List of serialized model dictionaries
        """
        return [e.serialize(primitive=primitive) for e in self.models]

    def to_json(self, *args, **kwargs) -> str:
        """Convert ModelList to JSON.

        Returns:
            JSON string representation
        """
        return json.dumps(self.serialize(), *args, **kwargs)

    def merge_contextual(self, distance: ContextualRange = None) -> ModelList[ModelT]:
        """Perform contextual merging on compatible models in the list.

        Args:
            distance: Maximum contextual distance for merging

        Returns:
            New ModelList with merged models
        """
        if distance is None:
            from .contextual_range import DocumentRange

            distance = DocumentRange()

        merged_models: List[ModelT] = []
        used_indices: Set[int] = set()

        for i, model in enumerate(self.models):
            if i in used_indices:
                continue

            # Try to merge with subsequent models
            current_model = model
            used_indices.add(i)

            for j in range(i + 1, len(self.models)):
                if j in used_indices:
                    continue

                other_model = self.models[j]
                if hasattr(current_model, "merge_contextual") and hasattr(
                    other_model, "can_merge_with"
                ):
                    if current_model.can_merge_with(other_model):
                        if current_model.merge_contextual(other_model, distance):
                            used_indices.add(j)

            merged_models.append(current_model)

        return ModelList(merged_models)

    def remove_subsets(self, strict=False):
        """
        Remove any subsets contained within the ModelList.

        :param bool strict: Default True. Whether only strict subsets are removed. When this is False, duplicates are removed too.
        """
        # A dictionary with the type of each element as the key, and the element itself as the value
        typed_list = {}
        for element in self.models:
            if type(element) in typed_list:
                typed_list[type(element)].append(element)
            else:
                typed_list[type(element)] = [element]
        new_models = []
        for _, elements in typed_list.items():
            i = 0
            elements.sort(
                key=lambda el: (
                    el.total_confidence(_account_for_merging=True)
                    if el.total_confidence(_account_for_merging=True) is not None
                    else -10000
                ),
                reverse=True,
            )
            length = len(elements)
            to_remove = []
            # Iterate through the list of elements and if any subsets are found, add the
            # indices to a list of values to remove
            while i < length:
                j = 0
                while j < length:
                    if i != j and elements[i].is_subset(elements[j]) and j not in to_remove:
                        if strict and elements[i] == elements[j]:
                            # Do not remove the element if it is not a strict subset depending on the value of strict
                            pass
                        else:
                            to_remove.append(i)
                    j += 1
                i += 1

            # Append any values that are not in the list of objects to remove
            i = 0
            while i < length:
                if i not in to_remove:
                    new_models.append(elements[i])
                i += 1
        self.models = new_models

    def _remove_used_subrecords(self):
        to_remove = set()
        for element in self.models:
            flattened_instance = element._flatten_instance()
            flattened_instance.remove(element)
            to_remove.update(flattened_instance)

        new_models = []
        for model in self.models:
            if model not in to_remove:
                new_models.append(model)
        self.models = new_models


def sort_merge_candidates(
    merge_candidates: List[Tuple[ContextualRange, BaseModel]], adjust_by_confidence: bool = True
) -> List[Tuple[ContextualRange, BaseModel]]:
    """Sort merge candidates by distance and optionally by confidence.

    Args:
        merge_candidates: List of tuples containing (distance, merge_candidate)
        adjust_by_confidence: Whether to adjust sorting by confidence scores

    Returns:
        Sorted list of merge candidates
    """
    # merge_candidates is a list of tuples (distance, merge candidate)
    if adjust_by_confidence:
        return sorted(
            merge_candidates,
            key=lambda x: (
                x[0] / (x[1].total_confidence() + 0.01)
                if x[1].total_confidence() is not None
                else x[0]
            ),
        )
    else:
        return sorted(merge_candidates, lambda x: x[0])

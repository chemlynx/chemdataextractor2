"""
Base types for making quantity models.

Provides base classes for physical quantity models that can automatically
extract values, units, and errors from chemical literature.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from ...parse.auto import AutoTableParser
from ...parse.auto import construct_unit_element
from ...parse.quantity import infer_error
from ...parse.quantity import infer_unit
from ...parse.quantity import infer_value
from ...parse.quantity import value_element
from ...parse.template import MultiQuantityModelTemplateParser
from ...parse.template import QuantityModelTemplateParser
from ..base import BaseModel
from ..base import FloatType
from ..base import InferredProperty
from ..base import ListType
from ..base import ModelMeta
from ..base import StringType
from .unit import UnitType

if TYPE_CHECKING:
    from typing import Self

    from .dimension import Dimension
    from .unit import Unit
else:
    # Import Self for runtime compatibility
    try:
        from typing import Self
    except ImportError:
        from typing import Self


class _QuantityModelMeta(ModelMeta):
    """Metaclass for QuantityModel that sets up unit and value parsing.

    Automatically configures parse expressions for raw_units and raw_value
    fields based on the model's dimensions.
    """

    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        cls = super().__new__(mcs, name, bases, attrs)
        unit_element = construct_unit_element(cls.dimensions)
        if unit_element:
            cls.fields["raw_units"].parse_expression = unit_element(None)
        cls.fields["raw_value"].parse_expression = value_element()(None)
        return cls


class QuantityModel(BaseModel, metaclass=_QuantityModelMeta):
    """Base class for modeling physical quantities.

    Subclasses of this model can be used with autoparsers to extract properties
    with zero human intervention. For optimal autoparser integration, models should have:

    - A specifier field with an associated parse expression (optional, only required
      for autoparsers). Parse expressions are updated automatically using forward-looking
      Interdependency Resolution when updatable=True.
    - Specifiers should have required=True to prevent spurious matches.
    - If applicable, a compound field named 'compound'.

    Parse expressions should use actions to ensure single-word results,
    for example by calling add_action(join) on each expression.

    Attributes:
        raw_value: str - Raw value text (required, contextual)
        raw_units: str - Raw units text (required, contextual)
        value: List[float] - Inferred numeric values (contextual)
        units: UnitType - Inferred unit object (contextual)
        error: float - Inferred error value (contextual)
        dimensions: Dimension - Physical dimensions for this quantity
        specifier: str - Quantity specifier text
    """

    raw_value = StringType(required=True, contextual=True)
    raw_units = StringType(required=True, contextual=True)
    value = InferredProperty(
        ListType(FloatType(), sorted_=True),
        origin_field="raw_value",
        inferrer=infer_value,
        contextual=True,
    )
    units = InferredProperty(
        UnitType(), origin_field="raw_units", inferrer=infer_unit, contextual=True
    )
    error = InferredProperty(
        FloatType(), origin_field="raw_value", inferrer=infer_error, contextual=True
    )
    dimensions: Dimension = None  # type: ignore[assignment]
    specifier = StringType()
    parsers = [
        MultiQuantityModelTemplateParser(),
        QuantityModelTemplateParser(),
        AutoTableParser(),
    ]

    # Operators are implemented so that composite quantities can be created easily
    # on the fly, such as the following code snippet:

    # .. code-block:: python

    #     length = LengthModel()
    #     length.unit = Meter()
    #     length.value = 10
    #     time = TimeModel()
    #     time.unit = Second()
    #     time.value = [2]
    #     speed = length / time
    #     print("Speed in miles per hour is: ", speed.convert_to(Mile() / Hour()).value[0])

    # Which has an expected output of

    # Speed in miles per hour is:  11.184709259696522

    def __truediv__(self, other: QuantityModel) -> QuantityModel:
        """Divide this quantity by another quantity.

        Args:
            other: QuantityModel - The quantity to divide by

        Returns:
            QuantityModel - The resulting quantity
        """
        other_inverted = other ** (-1.0)
        new_model = self * other_inverted
        return new_model

    def __pow__(self, other: float) -> QuantityModel:
        """Raise this quantity to a power.

        Args:
            other: float - The power to raise to

        Returns:
            QuantityModel - The resulting quantity
        """
        from .dimension import Dimensionless

        new_model = QuantityModel()
        new_model.dimensions = self.dimensions**other
        if self.value is not None:
            new_val = []
            for val in self.value:
                new_val.append(val**other)
            new_model.value = new_val
        if self.units is not None:
            new_model.units = self.units**other
        # Handle case that we have a dimensionless quantity, so we don't get dimensionless units squared.
        if isinstance(new_model.dimensions, Dimensionless):
            dimensionless_model = DimensionlessModel()
            dimensionless_model.value = new_model.value
            dimensionless_model.units = new_model.units
            return dimensionless_model

        return new_model

    def __mul__(self, other: QuantityModel) -> QuantityModel:
        """Multiply this quantity by another quantity.

        Args:
            other: QuantityModel - The quantity to multiply by

        Returns:
            QuantityModel - The resulting quantity
        """
        from .dimension import Dimensionless

        new_model = QuantityModel()
        new_model.dimensions = self.dimensions * other.dimensions
        if self.value is not None and other.value is not None:
            if len(self.value) == 2 and len(other.value) == 2:
                # The following always encompasses the whole range because
                # value has sorted_=True, so it should sort any values.
                new_val = [
                    self.value[0] * other.value[0],
                    self.value[1] * other.value[1],
                ]
                new_model.value = new_val
            elif len(self.value) == 2:
                new_val = [
                    self.value[0] * other.value[0],
                    self.value[1] * other.value[0],
                ]
                new_model.value = new_val
            elif len(self.value) == 2 and len(other.value) == 2:
                new_val = [
                    self.value[0] * other.value[0],
                    self.value[0] * other.value[1],
                ]
                new_model.value = new_val
            else:
                new_model.value = [self.value[0] * other.value[0]]
        if self.units is not None and other.units is not None:
            new_model.units = self.units * other.units
        if isinstance(new_model.dimensions, Dimensionless):
            dimensionless_model = DimensionlessModel()
            dimensionless_model.value = new_model.value
            dimensionless_model.units = new_model.units
            return dimensionless_model

        return new_model

    def convert_to(self, target_unit: Unit) -> Self:
        """Convert from current units to the given units.

        Raises AttributeError if the current unit is not set.

        Note:
            This method both modifies the current model and returns the modified model.

        Args:
            target_unit: The Unit to convert to

        Returns:
            The quantity in the given units (self for chaining)

        Raises:
            AttributeError: If current unit is not set
            ValueError: If conversion fails due to incompatible dimensions
        """
        if self.units:
            try:
                converted_values = self.convert_value(self.units, target_unit)
                if self.error:
                    converted_error = self.convert_error(self.units, target_unit)
                    self.error = converted_error
                self.value = converted_values
                self.units = target_unit
            except ZeroDivisionError:
                raise ValueError("Model not converted due to zero division error")
        else:
            raise AttributeError("Current units not set")
        return self

    def convert_to_standard(self):
        """
        Convert from current units to the standard units.
        Raises AttributeError if the current unit has not been set or the dimensions do not have standard units.

        .. note::

            This method both modifies the current model and returns the modified model.

        :returns: The quantity in the given units.
        :rtype: QuantityModel
        """
        standard_units = self.dimensions.standard_units
        if self.units and standard_units is not None:
            self.convert_to(standard_units)
        else:
            if not self.units:
                raise AttributeError("Current units not set")
            elif not self.dimensions.standard_units:
                raise AttributeError("Standard units for dimension", self.dimension, "not set")
        return self

    def convert_value(self, from_unit, to_unit):
        """
        Convert between the given units.
        If no units have been set for this model, assumes that it's in standard units.

        :param Unit from_unit: The Unit to convert from
        :param Unit to_unit: The Unit to convert to
        :returns: The value as expressed in the new unit
        :rtype: float
        """
        if self.value is not None:
            if to_unit.dimensions == from_unit.dimensions:
                if len(self.value) == 2:
                    standard_vals = [
                        from_unit.convert_value_to_standard(self.value[0]),
                        from_unit.convert_value_to_standard(self.value[1]),
                    ]
                    return [
                        to_unit.convert_value_from_standard(standard_vals[0]),
                        to_unit.convert_value_from_standard(standard_vals[1]),
                    ]
                else:
                    standard_val = from_unit.convert_value_to_standard(self.value[0])
                    return [to_unit.convert_value_from_standard(standard_val)]
            else:
                raise ValueError("Unit to convert to must have same dimensions as current unit")
            raise AttributeError("Unit to convert from not set")
        else:
            raise AttributeError("Value for model not set")

    def convert_error(self, from_unit, to_unit):
        """
        Converts error between given units
        If no units have been set for this model, assumes that it's in standard units.

        :param Unit from_unit: The Unit to convert from
        :param Unit to_unit: The Unit to convert to
        :returns: The error as expressed in the new unit
        :rtype: float
        """

        if self.error is not None:
            if to_unit.dimensions == from_unit.dimensions:
                standard_error = from_unit.convert_error_to_standard(self.error)
                return to_unit.convert_error_from_standard(standard_error)
            else:
                raise ValueError("Unit to convert to must have same dimensions as current unit")
            raise AttributeError("Unit to convert from not set")
        else:
            raise AttributeError("Value for model not set")

    def is_equal(self, other):
        """
        Tests whether the two quantities are physically equal, i.e. whether they represent the same value just in different units.

        :param QuantityModel other: The quantity being compared with
        :returns: Whether the two quantities are equal
        :rtype: bool
        """
        if self.value is None or other.value is None:
            raise AttributeError("Value for model not set")
        if self.units is None or other.units is None:
            raise AttributeError("Units not set")
        converted_value = self.convert_value(self.units, other.units)

        min_converted_value = converted_value[0]
        max_converted_value = converted_value[0]
        if len(converted_value) == 2:
            max_converted_value = converted_value[1]
        if self.error is not None:
            converted_error = self.convert_error(self.units, other.units)
            min_converted_value = min_converted_value - converted_error
            max_converted_value = max_converted_value + converted_error

        min_other_value = other.value[0]
        max_other_value = other.value[0]
        if len(other.value) == 2:
            max_other_value = other.value[1]
        if other.error is not None:
            min_other_value = min_other_value - other.error
            max_other_value = max_other_value + other.error
        return bool(
            min_converted_value <= max_other_value or max_converted_value >= min_other_value
        )

    def is_superset(self, other):
        if type(self) != type(other):
            return False
        for field_name, field in self.fields.items():
            # Method works recursively so it works with nested models
            if hasattr(field, "model_class"):
                if self[field_name] is None:
                    if other[field_name] is not None:
                        return False
                elif other[field_name] is None:
                    pass
                elif not self[field_name].is_superset(other[field_name]):
                    return False
            else:
                if (
                    field_name == "raw_value"
                    and other[field_name] == "NoValue"
                    and self[field_name] is not None
                ):
                    pass
                elif other[field_name] is not None and self[field_name] != other[field_name]:
                    return False
        return True

    def _compatible(self, other):
        match = False
        if type(other) == type(self):
            # Check if the other seems to be describing the same thing as self.
            match = True
            for field_name, _field in self.fields.items():
                if (
                    field_name == "raw_value"
                    and other[field_name] == "NoValue"
                    and self[field_name] is not None
                ):
                    pass
                elif (
                    self[field_name] is not None
                    and other[field_name] is not None
                    and self[field_name] != other[field_name]
                ):
                    match = False
                    break
        return match

    def __str__(self):
        string = "Quantity with " + self.dimensions.__str__() + ", " + self.units.__str__()
        string += " and a value of " + str(self.value)
        return string


class DimensionlessModel(QuantityModel):
    """Special case to handle dimensionless quantities.

    Represents physical quantities that have no dimensions,
    such as ratios, percentages, or pure numbers.
    """

    raw_units = StringType(required=False, contextual=False)


# Initialize dimensions after class definition to avoid circular import
def _init_dimensionless_model():
    from .dimension import Dimensionless

    DimensionlessModel.dimensions = Dimensionless()


_init_dimensionless_model()

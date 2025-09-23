"""
Base types for making units. Refer to the example on :ref:`creating new units and dimensions<creating_units>` for more detail on how to create your own units.

.. codeauthor:: Taketomo Isazawa <ti250@cam.ac.uk>
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from ..base import BaseType

if TYPE_CHECKING:
    from ..base import BaseModel
    from .dimension import Dimension


class UnitType(BaseType[Optional["Unit"]]):
    """A field containing a :class:`Unit` of some type.

    Field descriptor for handling unit values in chemical models.
    Ensures dimensional consistency when units are assigned.
    """

    def __set__(self, instance: BaseModel, value: Any) -> None:
        """Set unit value with dimensional validation.

        Ensures that any units assigned to models have the same dimensions
        as the model. Invalid units are set to None.

        Args:
            instance: BaseModel - The model instance
            value: Any - The unit value to assign
        """

        if hasattr(value, "dimensions"):
            if value.dimensions == instance.dimensions:
                instance._values[self.name] = self.process(value)
            else:
                instance._values[self.name] = None
        else:
            instance._values[self.name] = None

    def process(self, value: Any) -> Unit | None:
        """Process and validate unit value.

        Args:
            value: Any - The value to process

        Returns:
            Optional[Unit] - Processed unit or None if invalid
        """
        if isinstance(value, Unit):
            return value
        return None

    def serialize(self, value: Unit | None, primitive: bool = False) -> str:
        """Serialize unit to string representation.

        Args:
            value: Optional[Unit] - The unit to serialize
            primitive: bool - Whether to use primitive serialization (unused)

        Returns:
            str - String representation of the unit
        """
        return str(value**1.0)

    def is_empty(self, value: Any) -> bool:
        """Check if unit value is empty.

        Args:
            value: Any - The value to check

        Returns:
            bool - True if value is not a valid Unit
        """
        if isinstance(value, Unit):
            return False
        return True


class MetaUnit(type):
    """Metaclass to ensure that all subclasses of :class:`Unit` take magnitude into account.

    Ensures that all subclasses of Unit properly handle magnitude when converting
    to and from standard units by wrapping conversion methods.
    """

    def __new__(mcs, name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> type:
        cls = type.__new__(mcs, name, bases, attrs)

        if hasattr(cls, "convert_value_to_standard"):
            sub_convert_to_standard = cls.convert_value_to_standard

            def new_convert_to_standard(self, value):
                val = value * 10 ** (self.magnitude + self.base_magnitude)
                return sub_convert_to_standard(self, val)

            cls.convert_value_to_standard = new_convert_to_standard

        if hasattr(cls, "convert_value_from_standard"):
            sub_convert_from_standard = cls.convert_value_from_standard

            def new_convert_from_standard(self, value):
                val = value * 10 ** (-1 * (self.magnitude + self.base_magnitude))
                return sub_convert_from_standard(self, val)

            cls.convert_value_from_standard = new_convert_from_standard

        if hasattr(cls, "convert_error_to_standard"):
            sub_convert_err_to_standard = cls.convert_error_to_standard

            def new_convert_err_to_standard(self, value):
                val = value * 10 ** (self.magnitude + self.base_magnitude)
                return sub_convert_err_to_standard(self, val)

            cls.convert_error_to_standard = new_convert_err_to_standard

        if hasattr(cls, "convert_error_from_standard"):
            sub_convert_err_from_standard = cls.convert_error_from_standard

            def new_convert_err_from_standard(self, value):
                val = value * 10 ** (-1 * (self.magnitude + self.base_magnitude))
                return sub_convert_err_from_standard(self, val)

            cls.convert_error_from_standard = new_convert_err_from_standard

        if hasattr(cls, "constituent_units") and cls.constituent_units is not None:
            cls.base_magnitude = cls.constituent_units.magnitude

            def new_initializer(self, magnitude=0.0):
                Unit.__init__(
                    self,
                    cls.constituent_units.dimensions,
                    magnitude,
                    powers=cls.constituent_units.powers,
                )

            cls.__init__ = new_initializer

        return cls


class Unit(metaclass=MetaUnit):
    """
    Object represeting units. Implement subclasses of this for basic units.
    Units like meters, seconds, and Kelvins are already implemented in ChemDataExtractor.
    These can then be combined by simply dividing or multiplying them to create
    more complex units. Alternatively, one can create these by subclassing Unit
    and setting the powers parameter as desired. For example, a speed could be
    represented as either:

    .. code-block:: python

        speedunit = Meter() / Second()

    or

    .. code-block:: python

        class SpeedUnit(Unit):

            def __init__(self, magnitude=1.0):
                super(SpeedUnit, self).__init__(Length()/Time(),
                                                powers={Meter():1.0, Second():-1.0} )

        speedunit = SpeedUnit()

    and either method should produce the same results.

    Any subclass of Unit which represents a real unit should implement the following methods:

    - convert_value_to_standard
    - convert_value_from_standard
    - convert_error_to_standard
    - convert_error_from_standard

    These methods ensure that Units can be seamlessly converted to other ones. Any
    magnitudes placed in front of the units, e.g. kilometers, are handled automatically.
    Care must be taken that the 'standard' unit chosen is obvious, consistent, and documented,
    else another user may implement new units with the same dimensions but a different
    standard unit, resulting in unexpected errors. To ensure correct behaviour, one should also define
    the standard unit in code by setting the corresponding dimension's
    :attr:`~chemdataextractor.model.units.dimension.Dimension.standard_units`, unless the
    dimension is a composite one, in which case the standard unit can often be inferred from
    the constituent units' standard untis
    """

    base_magnitude = 0.0
    constituent_units = None
    """
    :class:`~chemdataextractor.model.units.unit.Unit` instance for showing constituent units.
    Used for creating more complex models. An example would be::

        class Newton(Unit):
            constituent_units = Gram(magnitude=3.0) * Meter() * (Second()) ** (-2.0)
    """

    def __init__(
        self,
        dimensions: Dimension,
        magnitude: float = 0.0,
        powers: dict[Unit, float] | None = None,
    ) -> None:
        """Create a unit object.

        Subclass Unit to create concrete units. For examples, see lengths.py and times.py

        Args:
            dimensions: Dimension - The dimensions this unit is for (e.g., Temperature)
            magnitude: float - The magnitude of the unit (e.g., km would be meters with magnitude of 3)
            powers: Optional[Dict[Unit, float]] - For complex units (e.g., m/s: {Meter():1.0, Second():-1.0})
        """
        self.dimensions = dimensions
        self.magnitude = magnitude
        self.powers = powers

    def convert_value_to_standard(self, value: float) -> float:
        """Convert from this unit to the standard value, usually the SI unit.

        Overload this in child classes when implementing new units.

        Args:
            value: float - The value to convert to standard units

        Returns:
            float - The value converted to standard units
        """
        for unit, power in self.powers.items():
            value = unit.convert_value_to_standard(value ** (1 / power)) ** power
        return value

    def convert_value_from_standard(self, value: float) -> float:
        """Convert to this unit from the standard value, usually the SI unit.

        Overload this in child classes when implementing new units.

        Args:
            value: float - The value to convert from standard units

        Returns:
            float - The value converted from standard units
        """
        for unit, power in self.powers.items():
            value = unit.convert_value_from_standard(value ** (1 / power)) ** power
        return value

    def convert_error_to_standard(self, error: float) -> float:
        """Convert error from this unit to the standard value, usually the SI unit.

        Overload this in child classes when implementing new units.

        Args:
            error: float - The error to convert to standard units

        Returns:
            float - The error converted to standard units
        """

        for unit, power in self.powers.items():
            error = unit.convert_error_to_standard(error ** (1 / power)) ** power
        return error

    def convert_error_from_standard(self, error: float) -> float:
        """Convert error to this unit from the standard value, usually the SI unit.

        Overload this in child classes when implementing new units.

        Args:
            error: float - The error to convert from standard units

        Returns:
            float - The error converted from standard units
        """

        for unit, power in self.powers.items():
            error = unit.convert_error_from_standard(error ** (1 / power)) ** power
        return error

    """
    Operators are implemented for the easy creation of complicated units out of
    simpler, fundamental units. This means that every combination of magnitudes
    and units need not be accounted for.
    """

    def __truediv__(self, other: Unit) -> Unit:
        """Divide this unit by another unit.

        Args:
            other: Unit - The unit to divide by

        Returns:
            Unit - The resulting unit
        """
        other_inverted = other ** (-1.0)
        new_unit = self * other_inverted
        return new_unit

    def __pow__(self, other: float) -> Unit:
        """Raise this unit to a power.

        Args:
            other: float - The power to raise to

        Returns:
            Unit - The resulting unit
        """
        # Handle dimensionless units so we don't get things like dimensionless units squared.
        if isinstance(self, DimensionlessUnit) or other == 0:
            new_unit = DimensionlessUnit(magnitude=self.magnitude * other)
            return new_unit

        powers = {}
        if self.powers:
            for key, value in self.powers.items():
                powers[key] = self.powers[key] * other
        else:
            new_key = copy.deepcopy(self)
            new_key.magnitude = 0.0
            powers[new_key] = other
        return Unit(self.dimensions**other, powers=powers, magnitude=self.magnitude * other)

    def __mul__(self, other: Unit) -> Unit:
        """Multiply this unit by another unit.

        Args:
            other: Unit - The unit to multiply by

        Returns:
            Unit - The resulting unit
        """
        dimensions = self.dimensions * other.dimensions
        powers = {}
        # normalised_values is created as searching for keys won't always work
        # when the different units have different magnitudes, even though
        # they are essentially the same unit and they should be unified.
        normalised_values = {}
        magnitude = self.magnitude + other.magnitude

        if self.powers:
            for key, value in self.powers.items():
                powers[key] = self.powers[key]
                normalised_key = copy.deepcopy(key)
                normalised_key.magnitude = 0.0
                normalised_values[normalised_key] = key.magnitude

        else:
            if not isinstance(self, DimensionlessUnit):
                new_key = copy.deepcopy(self)
                new_key.magnitude = 0.0
                powers[new_key] = 1.0
                normalised_values[new_key] = self.magnitude

        if other.powers:
            for key, value in other.powers.items():
                normalised_key = copy.deepcopy(key)
                normalised_key.magnitude = 0.0
                if normalised_key in normalised_values.keys():
                    powers[key] += value
                    if powers[key] == 0:
                        powers.pop(key)
                else:
                    powers[normalised_key] = value

        else:
            if not isinstance(other, DimensionlessUnit):
                normalised_other = copy.deepcopy(other)
                normalised_other.magnitude = 0.0
                if normalised_other in normalised_values:
                    powers[normalised_other] += 1.0
                    if powers[normalised_other] == 0:
                        powers.pop(other)
                else:
                    powers[normalised_other] = 1.0
        # powers.pop(DimensionlessUnit(), None)
        if len(powers) == 0:
            return DimensionlessUnit(magnitude=magnitude)

        return Unit(dimensions=dimensions, powers=powers, magnitude=magnitude)

    # eq and hash implemented so Units can be used as keys in dictionaries

    def __eq__(self, other: Any) -> bool:
        """Check equality with another unit.

        Args:
            other: Any - The object to compare with

        Returns:
            bool - True if units are equal
        """
        if not isinstance(other, Unit):
            return False
        if self.powers:
            if other.powers:
                if self.powers == other.powers and self.magnitude == other.magnitude:
                    return True
            else:
                if self.powers == (other**1.0).powers:
                    return True
        elif other.powers:
            if other.powers == (self**1.0).powers:
                return True
        else:
            if (
                type(self) == type(other)
                and self.magnitude == other.magnitude
                and self.dimensions == other.dimensions
            ):
                return True
        return False

    def __hash__(self) -> int:
        """Generate hash for this unit.

        Returns:
            int - Hash value for this unit
        """
        string = str(self.__class__.__name__)
        string += str(self.dimensions.__hash__())
        string += str(float(self.magnitude))
        # TODO: Should use the powers as part of the hash as well, but does not seem to work.
        # Can't just hash the dictionary as that would lead to two units that are actually equal hashing to different values depending on the order in which the dictionary is iterated through, which is not neccesarily deterministic. Better to have it this way, as it's okay for two hashes to clash.
        # if self.powers is not None:
        #     for key in sorted(str(self.powers.items())):
        #         string += str(key)
        return string.__hash__()

    def __str__(self) -> str:
        """String representation of this unit.

        Returns:
            str - String representation
        """
        string = ""
        if self.magnitude != 0:
            string += "(10^" + str(self.magnitude) + ") * "
        name_list = []
        if self.powers is not None:
            for key, value in self.powers.items():
                name_list.append(type(key).__name__ + "^(" + str(value) + ")  ")
            for name in sorted(name_list):
                string += name
            string = string[:-2]
        else:
            string += type(self).__name__
        return string


class DimensionlessUnit(Unit):
    """Special case to handle dimensionless quantities.

    Represents quantities that have no physical dimensions,
    such as ratios, percentages, or pure numbers.
    """

    def __init__(self, magnitude: float = 0.0) -> None:
        """Initialize dimensionless unit.

        Args:
            magnitude: float - The magnitude of the unit
        """
        from .dimension import Dimensionless

        self.dimensions = Dimensionless()
        self.magnitude = magnitude
        self.powers = None

    def convert_to_standard(self, value: float) -> float:
        """Convert to standard (identity operation for dimensionless).

        Args:
            value: float - The value to convert

        Returns:
            float - The same value (no conversion needed)
        """
        return value

    def convert_from_standard(self, value: float) -> float:
        """Convert from standard (identity operation for dimensionless).

        Args:
            value: float - The value to convert

        Returns:
            float - The same value (no conversion needed)
        """
        return value

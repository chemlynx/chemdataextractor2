"""
Units and models for charge.

.. codeauthor:: Batuhan Yildirim (by256@cam.ac.uk)

"""

import logging

from ...parse.elements import R
from .current import ElectricalCurrent
from .dimension import Dimension
from .quantity_model import QuantityModel
from .time import Time
from .unit import Unit

log = logging.getLogger(__name__)


class Charge(Dimension):
    constituent_dimensions = ElectricalCurrent() * Time()


class ChargeModel(QuantityModel):
    dimensions = Charge()


class ChargeUnit(Unit):
    def __init__(self, magnitude=0.0, powers=None):
        super().__init__(Charge(), magnitude, powers)


class Coulomb(ChargeUnit):
    def convert_value_to_standard(self, value):
        return value

    def convert_value_from_standard(self, value):
        return value

    def convert_error_to_standard(self, error):
        return error

    def convert_error_from_standard(self, error):
        return error


units_dict = {R("(C|c)(oulomb(s)?)?", group=0): Coulomb}
Charge.units_dict.update(units_dict)
Charge.standard_units = Coulomb()

"""
Glass transition temperature parser.

Provides parsing capabilities for glass transition temperature measurements,
including temperature values, units, and compound associations.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from ..model.base import BaseModel

from ..utils import first
from .actions import merge
from .base import BaseParser
from .cem import cem
from .cem import chemical_label
from .common import lbrct
from .common import rbrct
from .elements import Any
from .elements import I
from .elements import Not
from .elements import OneOrMore
from .elements import Optional
from .elements import R
from .elements import W
from .elements import ZeroOrMore
from .quantity import value_element

log = logging.getLogger(__name__)


prefix = (
    Optional(I("a")).hide()
    + (
        Optional(lbrct) + W("Tg") + Optional(rbrct)
        | I("glass")
        + Optional(I("transition"))
        + Optional(I("temperature") | I("range") | (I("temp") + I(".")))
        | W("transition") + Optional(I("temperature") | I("range") | I("temp."))
    ).hide()
    + Optional(lbrct + W("Tg") + rbrct)
    + Optional(W("=") | I("of") | I("was") | I("is") | I("at")).hide()
    + Optional(
        I("in") + I("the") + I("range") + Optional(I("of"))
        | I("about")
        | ("around")
        | I("ca")
        | I("ca.")
    ).hide()
)


delim = R(r"^[:;\.,]$")

# TODO: Consider allowing degree symbol to be optional. The prefix should be restrictive enough to stop false positives.
units = (W("°") + Optional(R(r"^[CFK]\.?$")) | W(r"K\.?") | W("°C"))("units").add_action(merge)

value = value_element()(None)
temp_range = (Optional(R(r"^[\-–−]$")) + value)("value").add_action(merge)
temp_value = value("value").add_action(merge)
temp = Optional(lbrct).hide() + (temp_range | temp_value)("value") + Optional(rbrct).hide()

tg = (prefix + Optional(delim).hide() + temp + units)("tg")

bracket_any = lbrct + OneOrMore(Not(tg) + Not(rbrct) + Any()) + rbrct

cem_tg_phrase = (
    Optional(cem)
    + Optional(I("having")).hide()
    + Optional(delim).hide()
    + Optional(bracket_any).hide()
    + Optional(delim).hide()
    + Optional(lbrct)
    + tg
    + Optional(rbrct)
)("tg_phrase")

obtained_tg_phrase = (
    (cem | chemical_label)
    + (I("is") | I("are") | I("was")).hide()
    + (I("measured") | I("obtained") | I("yielded")).hide()
    + ZeroOrMore(Not(tg) + Not(cem) + Any()).hide()
    + tg
)("tg_phrase")

tg_phrase = cem_tg_phrase | obtained_tg_phrase


class TgParser(BaseParser):
    """Parser for glass transition temperature measurements."""

    root = tg_phrase

    def interpret(self, result: Any, start: int, end: int) -> Generator[BaseModel, None, None]:
        """Interpret parsed glass transition temperature results.

        Args:
            result: Parsed result containing glass transition data
            start: Starting position in text
            end: Ending position in text

        Yields:
            BaseModel instances containing glass transition temperature data
        """
        compound = self.model.fields["compound"].model_class()
        glass_transition = self.model(
            value=first(result.xpath("./tg/value/text()")),
            units=first(result.xpath("./tg/units/text()")),
        )
        cem_el = first(result.xpath("./cem"))
        if cem_el is not None:
            compound.names = cem_el.xpath("./name/text()")
            compound.labels = cem_el.xpath("./label/text()")
        glass_transition.compound = compound
        yield glass_transition

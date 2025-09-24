"""
IR spectrum text parser.

Provides parsing capabilities for Infrared spectroscopy data,
including peak values, units, solvent information, and bond types.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Generator
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from ..model.base import BaseModel

# Type aliases for IR parsing
TokenList = list[str]  # List of tokens
ParseResult = list[Any]  # List of XML elements from parsing

from lxml.builder import E

from ..utils import first
from .actions import join
from .actions import merge
from .actions import strip_stop
from .base import BaseSentenceParser
from .cem import chemical_name
from .common import hyphen
from .elements import I
from .elements import Not
from .elements import OneOrMore
from .elements import Optional
from .elements import R
from .elements import T
from .elements import W
from .elements import ZeroOrMore

log = logging.getLogger(__name__)


def extract_units(tokens: TokenList, start: int, result: ParseResult) -> ParseResult:
    """Extract units from bracketed after nu."""
    for e in result:
        for child in e.iter():
            if "cm−1" in child.text:
                return [E("units", "cm−1")]
    return []


delim = R(r"^[;:,\./]$").hide()

# Not really just solvent, also nujol suspension, pellet, or ATR
ir_solvent = (
    I("KBr") | I("ATR") | I("neat") | I("NaCl") | I("CaF2") | I("AgCl") | I("CsI")
) + Optional(I("pellet"))

solvent = (ir_solvent | chemical_name)("solvent").add_action(join)

units = Optional(W("/")).hide() + (
    (Optional(W("[")) + R(r"^\[?cm[-–−‒]?1\]?$") + Optional(W("]")))
    | (W("cm") + R("^[-–−‒]$") + W("1"))
    | (W("cm") + W("-1"))
)("units").add_action(merge)


value_range = (
    R(r"^\d{,2}[ ,]?\d{3}(\.\d+)?[\-–−‒]\d{,2}[ ,]?\d{3}(\.\d+)?$")
    | (R(r"^\d{,2}[ ,]?\d{3}(\.\d+)?$") + R(r"^[\-–−‒]$") + R(r"^\d{,2}[ ,]?\d{3}(\.\d+)?$"))
)("value").add_action(merge)
value = R(r"^\d{,2}[ ,]?\d{3}(\.\d+)?\.?$")("value").add_action(strip_stop)

strength = (
    R("^(m|medium|w|weak|s|strong|n|narrow|b|broad|sh|sharp)$", re.I)("strength")
    + Optional(I("peak")).hide()
)

bond = OneOrMore(
    Not(W(")"))
    + (
        T("B-CM")
        | T("I-CM")
        | T("JJ")
        | T("NN")
        | T("NNP")
        | T("NNS")
        | T("HYPH")
        | T("CD")
        | T("LS")
        | T("CC")
    )
)("bond").add_action(join)

peak_meta_options = strength | bond

peak_meta = (
    W("(").hide() + peak_meta_options + ZeroOrMore(delim + peak_meta_options) + W(")").hide()
)

nu = (R(r"^[vνυ]̃?(max)?(\(cm−1\))?$") + Optional(W("max")) + Optional(W("="))).add_action(
    extract_units
)

spectrum_meta = (
    W("(").hide()
    + (units | solvent | nu)
    + ZeroOrMore(delim + (units | solvent | nu))
    + W(")").hide()
)


insolvent = T("IN") + solvent

ir_type = (
    Optional(W("FT") + hyphen) + R("^(FT-?)?IR|FT-?IS|IR-ATR$") + Optional(hyphen + W("ATR"))
)("type").add_action(merge)

prelude = (
    (ir_type | R("^[vνυ]max$").hide())
    + Optional(I("data"))
    + Optional(insolvent)
    + ZeroOrMore(spectrum_meta)
    + Optional(delim)
    + Optional(nu)
    + Optional(delim)
    + Optional(units)
)

peak = ((value_range | value) + Optional(peak_meta))("peak")

peaks = (peak + ZeroOrMore(ZeroOrMore(delim | W("and")).hide() + peak))("peaks")


ir = (prelude + peaks + Optional(delim) + Optional(units))("ir")


class IrParser(BaseSentenceParser):
    """Parser for Infrared spectroscopy data."""

    root = ir
    parse_full_sentence = True

    def interpret(self, result: Any, start: int, end: int) -> Generator[BaseModel, None, None]:
        """Interpret parsed IR spectrum results.

        Args:
            result: Parsed result containing IR spectrum data
            start: Starting position in text
            end: Ending position in text

        Yields:
            BaseModel instances containing IR spectrum data
        """
        c = self.model.fields["compound"].model_class()
        i = self.model(solvent=first(result.xpath("./solvent/text()")))
        peak_model = self.model.fields["peaks"].field.model_class
        units = first(result.xpath("./units/text()"))
        for peak_result in result.xpath("./peaks/peak"):
            ir_peak = peak_model(
                value=first(peak_result.xpath("./value/text()")),
                units=units,
                strength=first(peak_result.xpath("./strength/text()")),
                bond=first(peak_result.xpath("./bond/text()")),
            )
            i.peaks.append(ir_peak)
        i.compound = c
        yield i

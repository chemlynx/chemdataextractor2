"""
NMR text parser.

Provides parsing capabilities for Nuclear Magnetic Resonance (NMR) spectroscopy data,
including chemical shifts, coupling constants, and peak multiplicities.
"""

from __future__ import annotations

import copy
import logging
import re
from collections.abc import Generator
from typing import TYPE_CHECKING
from typing import Any

from ..utils import first
from .actions import fix_whitespace
from .actions import join
from .actions import merge
from .actions import strip_stop
from .base import BaseSentenceParser
from .cem import chemical_name
from .cem import nmr_solvent
from .common import cc
from .common import equals
from .elements import Group
from .elements import I
from .elements import Not
from .elements import OneOrMore
from .elements import Optional
from .elements import R
from .elements import SkipTo
from .elements import T
from .elements import W
from .elements import ZeroOrMore

if TYPE_CHECKING:
    from ..model.base import BaseModel

# Type aliases for NMR parsing
TokenList = list[str]  # List of tokens
ParseResult = list[Any]  # List of XML elements from parsing

log = logging.getLogger(__name__)


number = R(r"^\d+(\.\d+)?$")

nucleus = (
    (W("13C") + W("{") + W("1H") + W("}"))
    | W("1H")
    | W("13C")
    | W("15N")
    | W("31P")
    | W("19F")
    | W("11B")
    | W("29Si")
    | W("17O")
    | W("73Ge")
    | W("195Pt")
    | W("33S")
    | W("13C{1H") + W("}")
    | W("H1")
    | W("C13")
    | W("N15")
    | W("P31")
    | W("F19")
    | W("B11")
    | W("Si29")
    | W("Ge73")
    | W("Pt195")
    | W("S33")
)("nucleus").add_action(merge)

nmr_name = R(r"^N\.?M\.?R\.?\(?$", re.I).hide()

nmr_name_with_nucleus = R(r"^(1H|13C)N\.?M\.?R\.?\(?$", re.I, group=1)("nucleus")

frequency = (number("value") + R("^M?Hz$")("units"))("frequency")

delim = R(r"^[;:,\./]$").hide()

solvent = (
    (
        (nmr_solvent | chemical_name)
        + Optional((R(r"^(\+|&|and)$") | cc) + (nmr_solvent | chemical_name))
        + Optional(SkipTo(R(r"^([;:,\.\)]|at)$")))
        + Optional(Optional(delim) + I("solvent").hide())
    )("solvent")
    .add_action(join)
    .add_action(fix_whitespace)
)

temp_value = (Optional(R(r"^[~∼\<\>]$")) + Optional(R(r"^[\-–−]$")) + R(r"^[\+\-–−]?\d+(\.\d+)?$"))(
    "value"
).add_action(merge)
temp_word = (I("room") + R("^temp(erature)?$") | R(r"^r\.?t\.?$", re.I))("value").add_action(join)
temp_units = (W("°") + R("[CFK]") | W("K"))("units").add_action(merge)
temperature = Optional(I("at").hide()) + Group((temp_value + temp_units) | temp_word)("temperature")


def fix_nmr_peak_whitespace_error(
    tokens: TokenList, start: int, result: ParseResult
) -> ParseResult:
    """Split comma-separated NMR peaks into individual peak elements."""
    new_result = []
    for e in result:
        shift = e.find("shift")
        if "," in shift.text:
            for peak_text in shift.text.split(","):
                new_e = copy.deepcopy(e)
                new_e.find("shift").text = peak_text
                new_result.append(new_e)
        else:
            new_result.append(e)
    return new_result


def strip_delta(tokens: TokenList, start: int, result: ParseResult) -> ParseResult:
    """Remove delta symbol (δ) from chemical shift values."""
    for e in result:
        for child in e.iter():
            if child.text.startswith("δ"):
                child.text = child.text[1:]
    return result


shift_range = (
    Optional(R(r"^[\-–−‒]$"))
    + (
        R(r"^δ?[\+\-–−‒]?\d+(\.+\d+)?[\-–−‒]\d+(\.+\d+)?\.?$")
        | (
            R(r"^[\+\-–−‒]?\d+(\.+\d+)?$")
            + Optional(R(r"^[\-–−‒]$"))
            + R(r"^[\+\-–−‒]?\d+(\.+\d+)?\.?$")
        )
    )
)("shift").add_action(merge)
shift_value = (Optional(R(r"^[\-–−‒]$")) + R(r"^δ?[\+\-–−‒]?\d+(\.+\d+)?\.?$"))("shift").add_action(
    merge
)
shift_error = (Optional(R(r"^[\-–−‒]$")) + R(r"^δ?[\+\-–−‒]?\d+(\.+\d+)?,\d+(\.+\d+)?\.?$"))(
    "shift"
).add_action(merge)
shift = (shift_range | shift_value | shift_error).add_action(strip_stop).add_action(strip_delta)

split = R(
    "^(br?)?(s|S|d|D|t|T|q|Q|quint|sept|m|M|dd|ddd|dt|td|tt|br|bs|sb|h|ABq|broad|singlet|doublet|triplet|qua(rtet)?|quintet|septet|multiplet|multiple|peaks)$"
)
multiplicity = (OneOrMore(split) + Optional(W("of") + split))("multiplicity").add_action(join)

coupling_value = (number + ZeroOrMore(R("^[,;&]$") + number + Not(W("H"))))("value").add_action(
    join
)
# coupling = ((R('^\d?J([HCNPFD\d,]*|cis|trans)$') + Optional(R('^[\-–−‒]$') + R('^[HCNPF\d]$')) + Optional('=')).hide() + coupling_value + Optional(W('Hz')('units')) + ZeroOrMore(R('^[,;&]$').hide() + coupling_value + W('Hz')('units')))('coupling')
coupling = (
    (
        R(r"^\d?J([HCNPFD\d,]*|cis|trans)$")
        + ZeroOrMore(R(r"^J?([HCNPFD\d,]*|cis|trans)$"))
        + Optional(R(r"^[\-–−‒]$") + R(r"^[HCNPF\d]$"))
        + Optional("=")
    ).hide()
    + coupling_value
    + Optional(W("Hz")("units"))
    + ZeroOrMore(R("^[,;&]$").hide() + coupling_value + W("Hz")("units"))
)("coupling")

number = (R(r"^\d+(\.\d+)?[HCNPF]\.?$") | (R(r"^\d+(\.\d+)?$") + R(r"^[HCNPF]\.?$")))(
    "number"
).add_action(merge)

assignment_options = (
    OneOrMore(
        R(r"([CNHOPS\-–−‒=]+\d*[A-Za-z]?′*)+")
        | W("′")
        | chemical_name
        | R(r"^(C?quat\.?|Ac|Ar|Ph|linker|bridge)$")
    )
    + Optional(W("×") + R(r"^\d+$"))
)("assignment").add_action(join)
assignment = Optional(R(r"^\d{1,2}$")("number") + Optional(W("×")).hide()) + (
    assignment_options + ZeroOrMore(T("CC").hide() + assignment_options)
)

note = (W("overlapped") | (W("×") + R(r"^\d+$")))("note").add_action(join)

peak_meta_options = multiplicity | coupling | number | assignment | note
peak_meta = (
    W("(").hide()
    + peak_meta_options
    + ZeroOrMore(ZeroOrMore(delim) + peak_meta_options)
    + Optional(delim)
    + W(")").hide()
)

delta = (R("^[δd][HCNPF]?$") + Optional(equals)).hide()
ppm = Optional(R(r"^[(\[]$")) + Optional(I("in")) + I("ppm") + Optional(R(r"^[)\]]$"))

spectrum_meta = (
    Optional(W("(").hide())
    + (frequency | solvent | delta | temperature)
    + ZeroOrMore(Optional(delim) + (frequency | solvent | I("ppm") | delta | temperature))
    + Optional(temperature)
    + Optional(W(")").hide())
)

prelude_options = spectrum_meta | delta | delim | ppm.hide() | equals.hide()
prelude = (
    (nucleus + Optional(R(r"^[\-–−‒]$")).hide() + nmr_name | nmr_name_with_nucleus)
    + ZeroOrMore(prelude_options)
) | (R("^δ[HC]?$")("nucleus") + spectrum_meta + ZeroOrMore(prelude_options))

peak = Optional(delta) + (shift + Not(R("^M?Hz$")) + Optional(ppm).hide() + Optional(peak_meta))(
    "peak"
).add_action(fix_nmr_peak_whitespace_error)
peaks = (peak + ZeroOrMore(ZeroOrMore(delim | W("and")).hide() + peak))("peaks")

nmr = (prelude + peaks)("nmr")


class NmrParser(BaseSentenceParser):
    """"""

    root = nmr
    parse_full_sentence = True

    def __init__(self) -> None:
        pass

    def interpret(self, result: Any, start: int, end: int) -> Generator[BaseModel, None, None]:
        c = self.model.fields["compound"].model_class()

        n = self.model(
            nucleus=first(result.xpath("./nucleus/text()")),
            solvent=first(result.xpath("./solvent/text()")),
            frequency=first(result.xpath("./frequency/value/text()")),
            frequency_units=first(result.xpath("./frequency/units/text()")),
            temperature=first(result.xpath("./temperature/value/text()")),
            temperature_units=first(result.xpath("./temperature/units/text()")),
        )
        peak_model = self.model.fields["peaks"].field.model_class
        for peak_result in result.xpath("./peaks/peak"):
            nmr_peak = peak_model(
                shift=first(peak_result.xpath("./shift/text()")),
                multiplicity=first(peak_result.xpath("./multiplicity/text()")),
                coupling=first(peak_result.xpath("./coupling/value/text()")),
                coupling_units=first(peak_result.xpath("./coupling/units/text()")),
                number=first(peak_result.xpath("./number/text()")),
                assignment=first(peak_result.xpath("./assignment/text()")),
            )
            n.peaks.append(nmr_peak)

        n.compound = c
        yield n

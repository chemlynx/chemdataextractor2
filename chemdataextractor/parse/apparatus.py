"""
Parser for sentences that provide contextual information, such as apparatus, solvent, and temperature.

Provides parsing capabilities for scientific instrument and apparatus identification,
including brands, models, and instrument types used in experimental procedures.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Generator
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from ..model.base import BaseModel

from lxml import etree

from ..parse.base import BaseSentenceParser
from ..utils import first
from .actions import fix_whitespace
from .actions import join
from .elements import I
from .elements import Not
from .elements import OneOrMore
from .elements import Optional
from .elements import R
from .elements import T
from .elements import W
from .elements import ZeroOrMore

log = logging.getLogger(__name__)

dt = T("DT")

apparatus_type = R(r"^\d{2,}$") + W("MHz")
brands = (
    I("HORIBA") + I("Jobin") + I("Yvon")
    | I("Hitachi")
    | I("Bruker")
    | I("Cary")
    | I("Jeol")
    | I("PerkinElmer")
    | I("Agilent")
    | I("Shimadzu")
    | I("Varian")
    | I("Reach Devices")
    | I("Waters")
    | I("Micromass")
)
models = (
    I("FluoroMax-4")
    | I("F-7000")
    | I("AVANCE")
    | I("Digital")
    | R(r"\d\d\d+")
    | I("UV–vis-NIR")
    | I("Mercury")
    | I("Avatar")
    | I("thermonicolet")
    | I("pulsed")
    | I("Fourier")
    | I("transform")
)
instrument = (
    I("spectrofluorimeter")
    | I("spectrophotometer")
    | Optional(I("fluorescence")) + I("spectrometer")
    | Optional(I("nmr")) + I("workstation")
    | W("NMR")
    | I("instrument")
    | I("spectrometer")
)
apparatus = (
    (
        ZeroOrMore(T("JJ"))
        + Optional(apparatus_type)
        + OneOrMore(T("NNP") | T("NN") | brands)
        + ZeroOrMore(T("NNP") | T("NN") | T("HYPH") | T("CD") | brands | models)
        + Optional(instrument)
    )("apparatus")
    .add_action(join)
    .add_action(fix_whitespace)
)
apparatus_blacklist = R(
    "^(following|usual|equation|standard|accepted|method|point|temperature|melting|boiling|H2O|water|solvent|solution|THF|DMF|DMSO|acetone|methanol|ethanol|chloroform|benzene|mixing|stirring)$",
    re.I,
)
apparatus_phrase = (
    (W("with") | W("using") | W("on")).hide()
    + Optional(dt).hide()
    + Not(apparatus_blacklist)
    + apparatus
)


class ApparatusParser(BaseSentenceParser):
    """Parser for scientific apparatus and instrument identification."""

    root = apparatus_phrase

    def interpret(self, result: Any, start: int, end: int) -> Generator[BaseModel, None, None]:
        """Interpret parsed apparatus results.

        Args:
            result: Parsed result containing apparatus data
            start: Starting position in text
            end: Ending position in text

        Yields:
            BaseModel instances containing apparatus information
        """
        log.debug(etree.tostring(result))
        apparatus = self.model(name=first(result.xpath("./text()")))
        log.debug(apparatus.serialize())
        yield apparatus

"""
Parsers for generic specifier definitions
"""
import logging

from .actions import join
from .common import delim
from .common import rbrct
from .elements import OneOrMore
from .elements import Optional
from .elements import R
from .elements import T

log = logging.getLogger(__name__)

#: Greek symbols
greek_symbols = R("[\u0370-\u03ff\u1f00-\u1fff]")("specifier")

#: Critical temperature e.g. Tc, Tmax, etc
critical_temperature = R("T[C|c|N|n|max|on|1-2|A-Z]")("specifier")

#: Possible definition specifiers
specifier_options = greek_symbols | critical_temperature

#: Definition phrase 1: "definition, specifier" or "definition (specifier)"
definition_phrase_1 = (
    OneOrMore(T("JJ") | T("NN") | T("NNP") | T("HYPH") | T("VBG"))("phrase").add_action(
        join
    )
    + Optional(delim)
    + Optional(rbrct)
    + specifier_options
    + Optional(rbrct)
)("definition")

#: Add new definitions to this phrase
specifier_definition = (definition_phrase_1)("definition")

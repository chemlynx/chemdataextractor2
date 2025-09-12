"""
Parse text using rule-based grammars.

"""

from .actions import fix_whitespace
from .actions import join
from .actions import merge
from .actions import strip_stop
from .auto import AutoSentenceParser
from .auto import AutoTableParser
from .auto import BaseAutoParser
from .base import BaseParser
from .base import BaseSentenceParser
from .base import BaseTableParser
from .elements import And
from .elements import Any
from .elements import End
from .elements import Every
from .elements import First
from .elements import Group
from .elements import H
from .elements import Hide
from .elements import I
from .elements import IWord
from .elements import Not
from .elements import OneOrMore
from .elements import Optional
from .elements import Or
from .elements import R
from .elements import Regex
from .elements import SkipTo
from .elements import Start
from .elements import T
from .elements import Tag
from .elements import W
from .elements import Word
from .elements import ZeroOrMore

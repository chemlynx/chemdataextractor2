"""
Chemistry-aware natural language processing framework.

Provides comprehensive NLP tools specifically designed for processing
chemical and scientific literature, including tokenization, tagging,
named entity recognition, and abbreviation detection.
"""

from __future__ import annotations

from .abbrev import AbbreviationDetector
from .abbrev import ChemAbbreviationDetector
from .cem import CiDictCemTagger
from .cem import CrfCemTagger
from .cem import CsDictCemTagger
from .cem import LegacyCemTagger
from .crf import ConditionalRandomField
from .lexicon import ChemLexicon
from .lexicon import Lexicon
from .new_cem import CemTagger
from .pos import ApPosTagger
from .pos import ChemApPosTagger
from .pos import ChemCrfPosTagger
from .pos import CrfPosTagger
from .tag import ApTagger
from .tag import CrfTagger
from .tag import DictionaryTagger
from .tag import NoneTagger
from .tag import RegexTagger
from .tokenize import BertWordTokenizer
from .tokenize import ChemSentenceTokenizer
from .tokenize import ChemWordTokenizer
from .tokenize import FineWordTokenizer
from .tokenize import SentenceTokenizer
from .tokenize import WordTokenizer

"""
Configuration for making ChemDataExtractor revert to legacy versions of NER and tokenisation.
This is also much faster than the current NER when run on CPU.

:codeauthor: Taketomo Isazawa (ti250@cam.ac.uk)
"""

from chemdataextractor.doc.text import Sentence
from chemdataextractor.doc.text import Text
from chemdataextractor.nlp.cem import LegacyCemTagger
from chemdataextractor.nlp.pos import ChemCrfPosTagger
from chemdataextractor.nlp.tokenize import ChemWordTokenizer

Text.taggers = [ChemCrfPosTagger(), LegacyCemTagger()]
Text.word_tokenizer = ChemWordTokenizer()
Sentence.taggers = [ChemCrfPosTagger(), LegacyCemTagger()]
Sentence.word_tokenizer = ChemWordTokenizer()

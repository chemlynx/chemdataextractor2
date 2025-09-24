"""
New and improved named entity recognition (NER) for Chemical entity mentions (CEM).

Provides state-of-the-art chemical entity recognition using BERT-CRF models
for both organic and inorganic materials identification in scientific text.
"""

from __future__ import annotations

from .bertcrf_tagger import BertCrfTagger
from .bertcrf_tagger import ProcessedTextTagger
from .bertcrf_tagger import _BertCrfTokenTagger
from .tag import EnsembleTagger

tokentagger = _BertCrfTokenTagger()
processtagger = ProcessedTextTagger()


class CemTagger(EnsembleTagger):
    """
    A state of the art Named Entity Recognition tagger for both organic and inorganic materials
    that uses a tagger based on BERT with a Conditional Random Field to constrain the outputs.
    More details in the paper (https://pubs.acs.org/doi/full/10.1021/acs.jcim.1c01199).
    """

    taggers = [
        tokentagger,
        processtagger,
        BertCrfTagger(),
    ]

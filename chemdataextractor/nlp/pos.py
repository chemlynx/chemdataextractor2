"""
Part-of-speech tagging.

Provides part-of-speech taggers optimized for chemical and scientific text,
including Averaged Perceptron and Conditional Random Field implementations
with chemistry-aware feature extraction.
"""

from __future__ import annotations

import logging

from .lexicon import ChemLexicon
from .tag import POS_TAG_TYPE
from .tag import ApTagger
from .tag import CrfTagger

log = logging.getLogger(__name__)


#: Complete set of POS tags. Ordered by decreasing frequency in WSJ corpus.
TAGS = [
    "NN",  # NN : 174028
    "IN",  # IN : 132241
    "NNP",  # NNP : 115653
    "DT",  # DT : 101067
    "NNS",  # NNS : 74257
    "JJ",  # JJ : 71238
    ",",  # , : 60488
    ".",  # . : 48689
    "CD",  # CD : 47449
    "RB",  # RB : 40004
    "VBD",  # VBD : 37236
    "VB",  # VB : 32781
    "CC",  # CC : 29607
    "VBN",  # VBN : 26807
    "VBZ",  # VBZ : 26335
    "PRP",  # PRP : 21368
    "VBG",  # VBG : 18693
    "TO",  # TO : 16252
    "VBP",  # VBP : 15370
    "HYPH",  # HYPH : 14789
    "MD",  # MD : 12010
    "POS",  # POS : 10844
    "PRP$",  # PRP$ : 10252
    "$",  # $ : 9217
    "``",  # `` : 8879
    "''",  # '' : 8649
    ":",  # : : 6074
    "WDT",  # WDT : 5824
    "JJR",  # JJR : 4370
    "RP",  # RP : 3509
    "NNPS",  # NNPS : 3186
    "WP",  # WP : 2885
    "WRB",  # WRB : 2629
    "RBR",  # RBR : 2189
    "JJS",  # JJS : 2129
    "-RRB-",  # -RRB- : 1689
    "-LRB-",  # -LRB- : 1672
    "EX",  # EX : 1094
    "RBS",  # RBS : 946
    "PDT",  # PDT : 504
    "SYM",  # SYM : 379
    "FW",  # FW : 279
    "WP$",  # WP$ : 219
    "UH",  # UH : 127
    "LS",  # LS : 102
    "NFP",  # NFP : 14
    "AFX",  # AFX : 4
]


class ApPosTagger(ApTagger):
    """Greedy Averaged Perceptron POS tagger trained on WSJ corpus."""

    model = "models/pos_ap_wsj_nocluster-1.0.pickle"
    tag_type = POS_TAG_TYPE
    clusters = False

    def _get_features(self, i: int, context: list[str], prev: str, prev2: str) -> list[str]:
        """Map tokens into a feature representation.

        Args:
            i: Current token index
            context: List of tokens
            prev: Previous tag
            prev2: Tag before previous

        Returns:
            List of feature strings
        """
        w = self.lexicon[context[i]]
        features = [
            "bias",
            f"w:shape={w.shape}",
            f"w:lower={w.lower}",
            f"p1:tag={prev}",
            f"p2:tag={prev2}",
            f"p1:tag+w:lower={prev}+{w.lower}",
            f"p1:tag+p2:tag={prev}+{prev2}",
        ]
        if w.like_number:
            features.append("w:like_number")
        elif w.is_punct:
            features.append("w:is_punct")
        elif w.like_url:
            features.append("w:like_url")
        else:
            features.extend(
                [
                    f"w:suffix2={w.lower[-2:]}",
                    f"w:suffix3={w.lower[-3:]}",
                    f"w:suffix4={w.lower[-4:]}",
                    f"w:suffix5={w.lower[-5:]}",
                    f"w:prefix1={w.lower[:1]}",
                    f"w:prefix2={w.lower[:2]}",
                    f"w:prefix3={w.lower[:3]}",
                ]
            )
            if w.is_alpha:
                features.append("w:is_alpha")
            elif w.is_hyphenated:
                features.append("w:is_hyphenated")
            if w.is_upper:
                features.append("w:is_upper")
            elif w.is_lower:
                features.append("w:is_lower")
            elif w.is_title:
                features.append("w:is_title")
        if self.clusters and w.cluster:
            features.extend(
                [
                    f"w:cluster4={w.cluster[:4]}",
                    f"w:cluster6={w.cluster[:6]}",
                    f"w:cluster10={w.cluster[:10]}",
                    f"w:cluster20={w.cluster[:20]}",
                ]
            )
        # Add features for previous tokens if present
        if i > 0:
            p1 = self.lexicon[context[i - 1]]
            features.extend(
                [
                    f"p1:lower={p1.lower}",
                    f"p1:shape={p1.shape}",
                ]
            )
            if not (p1.like_number or p1.is_punct or p1.like_url):
                features.append(f"p1:suffix3={p1.lower[-3:]}")
            if self.clusters and p1.cluster:
                features.extend(
                    [
                        f"p1:cluster4={p1.cluster[:4]}",
                        f"p1:cluster6={p1.cluster[:6]}",
                        f"p1:cluster10={p1.cluster[:10]}",
                        f"p1:cluster20={p1.cluster[:20]}",
                    ]
                )
            if i > 1:
                p2 = self.lexicon[context[i - 2]]
                features.extend(
                    [
                        f"p2:lower={p2.lower}",
                        f"p2:shape={p2.shape}",
                    ]
                )
                if self.clusters and p2.cluster:
                    features.extend(
                        [
                            f"p2:cluster4={p2.cluster[:4]}",
                            f"p2:cluster6={p2.cluster[:6]}",
                            f"p2:cluster10={p2.cluster[:10]}",
                            f"p2:cluster20={p2.cluster[:20]}",
                        ]
                    )
        # Add features for next tokens if present
        end = len(context) - 1
        if i < end:
            n1 = self.lexicon[context[i + 1]]
            features.extend([f"n1:lower={n1.lower}", f"n1:shape={n1.shape}"])
            if not (n1.like_number or n1.is_punct or n1.like_url):
                features.append(f"n1:suffix3={n1.lower[-3:]}")
            if self.clusters and n1.cluster:
                features.extend(
                    [
                        f"n1:cluster4={n1.cluster[:4]}",
                        f"n1:cluster6={n1.cluster[:6]}",
                        f"n1:cluster10={n1.cluster[:10]}",
                        f"n1:cluster20={n1.cluster[:20]}",
                    ]
                )
            if i < end - 1:
                n2 = self.lexicon[context[i + 2]]
                features.extend([f"n2:lower={n2.lower}", f"n2:shape={n2.shape}"])
                if self.clusters and n2.cluster:
                    features.extend(
                        [
                            f"n2:cluster4={n2.cluster[:4]}",
                            f"n2:cluster6={n2.cluster[:6]}",
                            f"n2:cluster10={n2.cluster[:10]}",
                            f"n2:cluster20={n2.cluster[:20]}",
                        ]
                    )
        # Add position features
        if i == 0:
            features.append("-firsttoken-")
        elif i == 1:
            features.append("-secondtoken-")
        elif i == end - 1:
            features.append("-secondlasttoken-")
        elif i == end:
            features.append("-lasttoken-")
        return features


class ChemApPosTagger(ApPosTagger):
    """Greedy Averaged Perceptron POS tagger trained on both WSJ and GENIA corpora.

    Uses features based on word clusters from chemistry text.
    """

    model = "models/pos_ap_wsj_genia-1.0.pickle"
    lexicon = ChemLexicon()
    tag_type = POS_TAG_TYPE
    clusters = True


class CrfPosTagger(CrfTagger):
    """"""

    model = "models/pos_crf_wsj_nocluster-1.0.pickle"
    tag_type = POS_TAG_TYPE
    clusters = False

    def _get_features(self, tokens: list[str], i: int) -> list[str]:
        """Extract features for CRF-based POS tagging.

        Args:
            tokens: List of tokens
            i: Current token index

        Returns:
            List of feature strings
        """
        token = tokens[i]
        w = self.lexicon[token]
        features = [
            f"w.shape={w.shape}",
            # 'w.normalized=%s' % w.normalized,
            f"w.lower={w.lower}",
            f"w.length={w.length}",
        ]
        if w.like_number:
            features.append("w.like_number")
        elif w.is_punct:
            features.append("w.is_punct")
        # elif w.like_url:
        #     features.append('w.like_url')
        else:
            features.extend(
                [
                    f"w.suffix1={w.lower[-1:]}",
                    f"w.suffix2={w.lower[-2:]}",
                    f"w.suffix3={w.lower[-3:]}",
                    f"w.suffix4={w.lower[-4:]}",
                    f"w.suffix5={w.lower[-5:]}",
                    f"w.prefix1={w.lower[:1]}",
                    f"w.prefix2={w.lower[:2]}",
                    f"w.prefix3={w.lower[:3]}",
                    f"w.prefix4={w.lower[:4]}",
                    f"w.prefix5={w.lower[:5]}",
                ]
            )
            if w.is_alpha:
                features.append("w.is_alpha")
            elif w.is_hyphenated:
                features.append("w.is_hyphenated")
            if w.is_upper:
                features.append("w.is_upper")
            elif w.is_lower:
                features.append("w.is_lower")
            elif w.is_title:
                features.append("w.is_title")
        if self.clusters and w.cluster:
            features.extend(
                [
                    f"w.cluster4={w.cluster[:4]}",
                    f"w.cluster6={w.cluster[:6]}",
                    f"w.cluster10={w.cluster[:10]}",
                    f"w.cluster20={w.cluster[:20]}",
                ]
            )
        # Add features for previous tokens if present
        if i > 0:
            p1token = tokens[i - 1]
            p1 = self.lexicon[p1token]
            features.extend(
                [
                    f"p1.lower={p1.lower}",
                    f"p1.lower={p1.lower}+w.lower={w.lower}",
                    f"p1.shape={p1.shape}",
                ]
            )
            if not (p1.like_number or p1.is_punct or p1.like_url):
                features.append(f"p1:suffix3={p1.lower[-3:]}")
            if self.clusters and p1.cluster:
                features.extend(
                    [
                        f"p1.cluster4={p1.cluster[:4]}",
                        f"p1.cluster6={p1.cluster[:6]}",
                        f"p1.cluster10={p1.cluster[:10]}",
                        f"p1.cluster20={p1.cluster[:20]}",
                    ]
                )
            if i > 1:
                p2token = tokens[i - 2]
                p2 = self.lexicon[p2token]
                features.extend(
                    [
                        f"p2.lower={p2.lower}",
                        f"p2.lower={p2.lower}+p1.lower={p1.lower}",
                        f"p2.lower={p2.lower}+p1.lower={p1.lower}+w.lower={w.lower}",
                        f"p2.shape={p2.shape}",
                    ]
                )
                if self.clusters and p2.cluster:
                    features.extend(
                        [
                            f"p2.cluster4={p2.cluster[:4]}",
                            f"p2.cluster6={p2.cluster[:6]}",
                            f"p2.cluster10={p2.cluster[:10]}",
                            f"p2.cluster20={p2.cluster[:20]}",
                        ]
                    )
        # Add features for next tokens if present
        end = len(tokens) - 1
        if i < end:
            n1token = tokens[i + 1]
            n1 = self.lexicon[n1token]
            features.extend(
                [
                    f"n1.lower={n1.lower}",
                    f"w.lower={w.lower}+n1.lower={n1.lower}",
                    f"n1.shape={n1.shape}",
                ]
            )
            if not (n1.like_number or n1.is_punct or n1.like_url):
                features.append(f"n1.suffix3={n1.lower[-3:]}")
            if self.clusters and n1.cluster:
                features.extend(
                    [
                        f"n1.cluster4={n1.cluster[:4]}",
                        f"n1.cluster6={n1.cluster[:6]}",
                        f"n1.cluster10={n1.cluster[:10]}",
                        f"n1.cluster20={n1.cluster[:20]}",
                    ]
                )
            if i < end - 1:
                n2token = tokens[i + 2]
                n2 = self.lexicon[n2token]
                features.extend(
                    [
                        f"n2.lower={n2.lower}",
                        f"n1.lower={n1.lower}+n2.lower={n2.lower}",
                        f"w.lower={w.lower}+n1.lower={n1.lower}+n2.lower={n2.lower}",
                        f"n2.shape={n2.shape}",
                    ]
                )
                if self.clusters and n2.cluster:
                    features.extend(
                        [
                            f"n2.cluster4={n2.cluster[:4]}",
                            f"n2.cluster6={n2.cluster[:6]}",
                            f"n2.cluster10={n2.cluster[:10]}",
                            f"n2.cluster20={n2.cluster[:20]}",
                        ]
                    )
        if i == 0:
            features.append("-firsttoken-")
        elif i == 1:
            features.append("-secondtoken-")
        elif i == end - 1:
            features.append("-secondlasttoken-")
        elif i == end:
            features.append("-lasttoken-")
        return features


class ChemCrfPosTagger(CrfPosTagger):
    """"""

    model = "models/pos_crf_wsj_genia-1.0.pickle"
    tag_type = POS_TAG_TYPE
    lexicon = ChemLexicon()
    clusters = True

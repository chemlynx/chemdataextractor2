"""
Cache features of previously seen words.

Provides lexicon classes for caching and analyzing word features,
including morphological, orthographic, and cluster-based features
for natural language processing tasks.
"""

from __future__ import annotations

import logging

from ..data import load_model
from ..text import is_ascii
from ..text import is_punct
from ..text import like_number
from ..text import like_url
from ..text import word_shape
from ..text.normalize import ChemNormalizer
from ..text.normalize import Normalizer
from ..utils import Singleton

log = logging.getLogger(__name__)


class Lexeme:
    """Represents a word with cached morphological and orthographic features."""

    __slots__ = (
        "text",
        "normalized",
        "lower",
        "first",
        "suffix",
        "shape",
        "length",
        "upper_count",
        "lower_count",
        "digit_count",
        "is_alpha",
        "is_ascii",
        "is_digit",
        "is_lower",
        "is_upper",
        "is_title",
        "is_punct",
        "is_hyphenated",
        "like_url",
        "like_number",
        "cluster",
    )

    def __init__(
        self,
        text: str,
        normalized: str,
        lower: str,
        first: str,
        suffix: str,
        shape: str,
        length: int,
        upper_count: int,
        lower_count: int,
        digit_count: int,
        is_alpha: bool,
        is_ascii: bool,
        is_digit: bool,
        is_lower: bool,
        is_upper: bool,
        is_title: bool,
        is_punct: bool,
        is_hyphenated: bool,
        like_url: bool,
        like_number: bool,
        cluster: str | None,
    ) -> None:
        #: Original Lexeme text.
        self.text = text
        #: The Brown Word Cluster for this Lexeme.
        self.cluster = cluster
        #: Normalized text, using the Lexicon Normalizer.
        self.normalized = normalized
        #: Lowercase text.
        self.lower = lower
        #: First character.
        self.first = first
        #: Three-character suffix
        self.suffix = suffix
        #: Word shape. Derived by replacing every number with 'd', every greek letter with 'g', and every latin letter with 'X' or 'x' for uppercase and lowercase respectively.
        self.shape = shape
        #: Lexeme length.
        self.length = length
        #: Count of uppercase characters.
        self.upper_count = upper_count
        #: Count of lowercase characters.
        self.lower_count = lower_count
        #: Count of digits.
        self.digit_count = digit_count
        #: Whether the text is entirely alphabetical characters.
        self.is_alpha = is_alpha
        #: Whether the text is entirely ASCII characters.
        self.is_ascii = is_ascii
        #: Whether the text is entirely digits.
        self.is_digit = is_digit
        #: Whether the text is entirely lowercase.
        self.is_lower = is_lower
        #: Whether the text is entirely uppercase.
        self.is_upper = is_upper
        #: Whether the text is title cased.
        self.is_title = is_title
        #: Whether the text is entirely punctuation characters.
        self.is_punct = is_punct
        #: Whether the text is hyphenated.
        self.is_hyphenated = is_hyphenated
        #: Whether the text looks like a URL.
        self.like_url = like_url
        #: Whether the text looks like a number.
        self.like_number = like_number


class Lexicon(metaclass=Singleton):
    """Lexicon for caching word features and Brown word clusters."""

    #: The Normalizer for this Lexicon.
    normalizer = Normalizer()

    #: Path to the Brown clusters model file for this Lexicon.
    clusters_path: str | None = None

    def __init__(self) -> None:
        """Initialize lexicon with empty caches."""
        self.lexemes: dict[str, Lexeme] = {}
        self.clusters: dict[str, str] = {}
        self._loaded_clusters = False

    def __len__(self) -> int:
        """The current number of lexemes stored."""
        return len(self.lexemes)

    def add(self, text: str) -> None:
        """Add text to the lexicon.

        Args:
            text: The text to add.
        """
        # logging.debug('Adding to lexicon: %s' % text)
        if text not in self.lexemes:
            normalized = self.normalized(text)
            self.lexemes[text] = Lexeme(
                text=text,
                normalized=normalized,
                lower=self.lower(normalized),
                first=self.first(normalized),
                suffix=self.suffix(normalized),
                shape=self.shape(normalized),
                length=self.length(normalized),
                upper_count=self.upper_count(normalized),
                lower_count=self.lower_count(normalized),
                digit_count=self.digit_count(normalized),
                is_alpha=self.is_alpha(normalized),
                is_ascii=self.is_ascii(normalized),
                is_digit=self.is_digit(normalized),
                is_lower=self.is_lower(normalized),
                is_upper=self.is_upper(normalized),
                is_title=self.is_title(normalized),
                is_punct=self.is_punct(normalized),
                is_hyphenated=self.is_hyphenated(normalized),
                like_url=self.like_url(normalized),
                like_number=self.like_number(normalized),
                cluster=self.cluster(normalized),
            )

    def __getitem__(self, text: str) -> Lexeme:
        """Return the requested lexeme from the Lexicon.

        Args:
            text: Text of the lexeme to retrieve.

        Returns:
            The requested Lexeme.
        """
        self.add(text)
        return self.lexemes[text]

    def cluster(self, text: str) -> str | None:
        """Get Brown word cluster for text."""
        if not self._loaded_clusters and self.clusters_path:
            self.clusters = load_model(self.clusters_path)
            self._loaded_clusters = True
        return self.clusters.get(text, None)

    def normalized(self, text: str) -> str:
        """Get normalized text."""
        return self.normalizer(text)

    def lower(self, text: str) -> str:
        """Get lowercase text."""
        return text.lower()

    def first(self, text: str) -> str:
        """Get first character."""
        return text[:1]

    def suffix(self, text: str) -> str:
        """Get three-character suffix."""
        return text[-3:]

    def shape(self, text: str) -> str:
        """Get word shape."""
        return word_shape(text)

    def length(self, text: str) -> int:
        """Get text length."""
        return len(text)

    def digit_count(self, text: str) -> int:
        """Count digit characters."""
        return sum(c.isdigit() for c in text)

    def upper_count(self, text: str) -> int:
        """Count uppercase characters."""
        return sum(c.isupper() for c in text)

    def lower_count(self, text: str) -> int:
        """Count lowercase characters."""
        return sum(c.islower() for c in text)

    def is_alpha(self, text: str) -> bool:
        """Check if text is entirely alphabetical."""
        return text.isalpha()

    def is_ascii(self, text: str) -> bool:
        """Check if text is entirely ASCII."""
        return is_ascii(text)

    def is_digit(self, text: str) -> bool:
        """Check if text is entirely digits."""
        return text.isdigit()

    def is_lower(self, text: str) -> bool:
        """Check if text is entirely lowercase."""
        return text.islower()

    def is_upper(self, text: str) -> bool:
        """Check if text is entirely uppercase."""
        return text.isupper()

    def is_title(self, text: str) -> bool:
        """Check if text is title cased."""
        return text.istitle()

    def is_punct(self, text: str) -> bool:
        """Check if text is entirely punctuation."""
        return is_punct(text)

    def is_hyphenated(self, text: str) -> bool:
        """Check if text is hyphenated."""
        # TODO: What about '--'?
        return "-" in text and text != "-"

    def like_url(self, text: str) -> bool:
        """Check if text looks like a URL."""
        return like_url(text)

    def like_number(self, text: str) -> bool:
        """Check if text looks like a number."""
        return like_number(text)


class ChemLexicon(Lexicon):
    """A Lexicon that is pre-configured with a Chemistry-aware Normalizer and Brown word clusters derived from a
    chemistry corpus."""

    normalizer = ChemNormalizer()
    clusters_path = "models/clusters_chem1500-1.0.pickle"

"""
Text processors for cleaning and normalizing text.

Provides various text processing utilities for preparing chemical text
for parsing and extraction operations.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from abc import ABCMeta
from abc import abstractmethod

from ..parse.regex_patterns import convert_scientific_notation
from ..parse.regex_patterns import remove_bracketed_numbers
from ..parse.regex_patterns import remove_uncertainty
from . import APOSTROPHES
from . import EMAIL_RE

log = logging.getLogger(__name__)


class BaseProcessor(metaclass=ABCMeta):
    """Abstract processor class from which all processors inherit.

    Subclasses must implement a ``__call__()`` method to process text.
    """

    @abstractmethod
    def __call__(self, text: str) -> str | None:
        """Process the input text.

        Args:
            text: The input text to process

        Returns:
            The processed text, or None if text should be discarded
        """
        return text


class Chain:
    """Apply a series of processors in turn. Stops if a processors returns None."""

    def __init__(self, *callables: BaseProcessor) -> None:
        self.callables = callables

    def __call__(self, value: str | None) -> str | None:
        for func in self.callables:
            if value is None:
                break
            value = func(value)
        return value


class Discard:
    """Return None if value matches a string."""

    def __init__(self, *match: str) -> None:
        self.match = match

    def __call__(self, value: str | None) -> str | None:
        if value in self.match:
            return None
        return value


class LAdd:
    """Add a substring to the start of a value."""

    def __init__(self, substring: str) -> None:
        self.substring = substring

    def __call__(self, value: str | None) -> str | None:
        return f"{self.substring}{value}"


class RAdd:
    """Add a substring to the end of a value."""

    def __init__(self, substring: str) -> None:
        self.substring = substring

    def __call__(self, value: str | None) -> str | None:
        return f"{value}{self.substring}"


class LStrip:
    """Remove a substring from the start of a value."""

    def __init__(self, *substrings: str) -> None:
        self.substrings = substrings

    def __call__(self, value: str | None) -> str | None:
        for substring in self.substrings:
            if value.startswith(substring):
                return value[len(substring) :]
        return value


class RStrip:
    """Remove a substring from the end of a value."""

    def __init__(self, *substrings: str) -> None:
        self.substrings = substrings

    def __call__(self, value: str | None) -> str | None:
        for substring in self.substrings:
            if value.endswith(substring):
                return value[: -len(substring)]
        return value


def floats(s: str) -> float:
    """Convert string to float. Handles more string formats that the standard python conversion."""
    try:
        return float(s)
    except ValueError:
        s = remove_bracketed_numbers(s)  # Remove bracketed numbers from end
        s = remove_uncertainty(s)  # Remove uncertainties from end
        s = s.rstrip("'\"+-=<>/,.:;!?)]}…∼~≈×*_≥≤")  # Remove trailing punctuation
        s = s.lstrip("'\"+=<>/([{∼~≈×*_≥≤£$€#§")  # Remove leading punctuation
        s = s.replace(",", "")  # Remove commas
        s = "".join(s.split())  # Strip whitespace
        s = convert_scientific_notation(s)  # Convert scientific notation
        return float(s)


def strip_querystring(url: str) -> str:
    """Remove the querystring from the end of a URL."""
    p = urllib.parse.urlparse(url)
    return p.scheme + "://" + p.netloc + p.path


class Substitutor:
    """Perform a list of substitutions defined by regex on text.

    Useful to clean up text where placeholders are used in place of actual unicode characters.
    """

    def __init__(self, substitutions: list[tuple[str | re.Pattern[str], str]]) -> None:
        """Initialize with substitution patterns.

        Args:
            substitutions: List of (regex, string) tuples that define the substitution.
        """
        self.substitutions = []
        for pattern, replacement in substitutions:
            if isinstance(pattern, str):
                pattern = re.compile(pattern, re.I | re.U)
            self.substitutions.append((pattern, replacement))

    def __call__(self, t: str) -> str:
        """Run substitutions on given text and return it.

        Args:
            t: The text to run substitutions on.

        Returns:
            The text with substitutions applied.
        """
        for pattern, replacement in self.substitutions:
            t = pattern.sub(replacement, t)
        return t


def extract_emails(text: str) -> list[str]:
    """Return a list of email addresses extracted from the string."""
    text = text.replace("\u2024", ".")
    emails = []
    for m in EMAIL_RE.findall(text):
        emails.append(m[0])
    return emails


def unapostrophe(text: str) -> str:
    """Strip apostrophe and 's' from the end of a string."""
    text = re.sub(r"[{}]s?$".format("".join(APOSTROPHES)), "", text)
    return text

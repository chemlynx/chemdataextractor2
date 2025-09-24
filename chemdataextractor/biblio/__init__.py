"""
Tools for dealing with bibliographic information.

Provides comprehensive bibliographic parsing utilities including BibTeX parsing,
person name handling, and XMP metadata extraction.
"""

from __future__ import annotations

from .bibtex import BibtexParser
from .bibtex import parse_bibtex
from .person import PersonName
from .xmp import XmpParser
from .xmp import parse_xmp

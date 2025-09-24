"""
Plain text document reader.

Provides functionality to parse plain text documents and convert them
into structured ChemDataExtractor Document objects.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..text import get_encoding
from .base import BaseReader

if TYPE_CHECKING:
    from ..doc.document import Document


class PlainTextReader(BaseReader):
    """Read plain text and split into Paragraphs based on newline patterns."""

    def detect(self, fstring: str | bytes, fname: str | None = None) -> bool:
        """Detect if this reader can parse the input.

        Args:
            fstring: Input data to check
            fname: Optional filename for format hints

        Returns:
            True if this reader can likely parse the input
        """
        if fname is not None and "." in fname:
            extension = fname.rsplit(".", 1)[1]
            if extension in {"pdf", "html", "xml"}:
                return False
        return True

    def parse(self, fstring: str | bytes) -> Document:
        """Parse plain text input and return a Document.

        Args:
            fstring: Plain text input data

        Returns:
            Document with paragraphs split by double newlines
        """
        # Import here to avoid circular imports
        from ..doc.document import Document

        if isinstance(fstring, bytes):
            fstring = fstring.decode(get_encoding(fstring))
        para_strings = [
            p.strip() for p in re.split(r"\r\n[ \t]*\r\n|\r[ \t]*\r|\n[ \t]*\n", fstring)
        ]
        return Document(*para_strings)

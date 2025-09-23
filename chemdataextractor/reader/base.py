"""
Abstract base classes for document readers.

Provides the fundamental interfaces for reading various document formats
and converting them into ChemDataExtractor Document objects.
"""

from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import BinaryIO
from typing import Optional
from typing import TextIO
from typing import Union

if TYPE_CHECKING:
    from ..doc.document import Document

# Type aliases for file-like objects
type FileInput = str | bytes | BinaryIO | TextIO


class BaseReader(metaclass=ABCMeta):
    """Abstract base class for all document readers.

    All Document Readers should implement a parse method that converts
    input data into a structured Document object.

    Attributes:
        root: Any - Root element for parsed document structure
    """

    def __init__(self) -> None:
        """Initialize the reader."""
        self.root: Any | None = None

    def detect(self, fstring: str | bytes, fname: str | None = None) -> bool:
        """Quickly check if this reader can parse the input.

        Reader subclasses should override this method to provide format detection.
        Used to quickly skip attempting to parse when trying different readers.
        If in doubt, return True and raise ReaderError in parse() if it fails.

        Args:
            fstring: Union[str, bytes] - Input data to check
            fname: Optional[str] - Optional filename for format hints

        Returns:
            bool - True if this reader can likely parse the input
        """
        return True

    @abstractmethod
    def parse(self, fstring: str | bytes) -> Document:
        """Parse the input and return a Document.

        Args:
            fstring: Union[str, bytes] - Input data to parse

        Returns:
            Document - Parsed document structure

        Raises:
            ReaderError: If the parse fails
        """
        pass

    def read(self, f: BinaryIO | TextIO) -> Document:
        """Read a file-like object and return a Document.

        Args:
            f: Union[BinaryIO, TextIO] - File-like object to read

        Returns:
            Document - Parsed document structure
        """
        return self.parse(f.read())

    def readstring(self, fstring: str | bytes) -> Document:
        """Read a file string and return a Document.

        Args:
            fstring: Union[str, bytes] - String data to parse

        Returns:
            Document - Parsed document structure
        """
        return self.parse(fstring)

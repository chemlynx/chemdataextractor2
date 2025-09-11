"""
Error classes for ChemDataExtractor.

"""

from typing import Any
from typing import Union


class ChemDataExtractorError(Exception):
    """Base ChemDataExtractor exception."""


class ReaderError(ChemDataExtractorError):
    """Raised when a reader is unable to read a document."""


class ModelNotFoundError(ChemDataExtractorError):
    """Raised when a model file could not be found."""


class ConfigurationError(Exception):
    """
    The exception raised by any NLP object when it's misconfigured
    (e.g. missing properties, invalid properties, unknown properties).
    Originally implemented by AllenNLP.
    """

    def __reduce__(self) -> Union[str, tuple[Any, ...]]:
        return type(self), (self.message,)

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message

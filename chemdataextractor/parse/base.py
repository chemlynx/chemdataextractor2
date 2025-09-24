"""
Base classes for parsing sentences and tables.

Provides abstract base classes for implementing parsers that extract
structured chemical data from text and tables.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

from .quantity import extract_error
from .quantity import extract_units
from .quantity import extract_value

if TYPE_CHECKING:
    from ..doc.element import BaseElement
    from ..model.base import BaseModel

log = logging.getLogger(__name__)


class BaseParser:
    """Abstract base class for all parsers.

    Provides the fundamental interface for parsing chemical data from
    document elements. Parsers extract structured data using grammar
    rules and convert it into model instances.

    Attributes:
        model: type[BaseModel] - The model class this parser creates
        trigger_phrase: Optional[BaseParserElement] - Fast pre-filter for performance
        skip_section_phrase: Optional[BaseParserElement] - Sections to skip
        allow_section_phrase: Optional[BaseParserElement] - Sections to allow
    """

    model: type[BaseModel] | None = None
    trigger_phrase: Any | None = None  # BaseParserElement
    skip_section_phrase: Any | None = None  # BaseParserElement
    allow_section_phrase: Any | None = None  # BaseParserElement
    """
    Optional :class:`~chemdataextractor.parse.elements.BaseParserElement` instance.
    All sentences are run through this before the full root phrase is applied to the
    sentence. If nothing is found for this phrase, the sentence will not go through
    the full root phrase. This is done for performance reasons, and if not set,
    ChemDataExtractor will perform as it did in previous versions. If this phrase is
    set to an appropriate value, it can help ChemDataExtractor perform at up to 2x
    its previous speed.

    To ensure that this works as intended, the :class:`~chemdataextractor.parse.elements.BaseParserElement`
    should be a simple parse rule (substantially simpler than the :class:`~chemdataextractor.parse.base.BaseParser.root`)
    that takes little time to process.
    """

    @property
    @abstractmethod
    def root(self) -> Any:
        """The root parsing element for this parser.

        Returns:
            BaseParserElement - The main parsing rule
        """
        pass

    @abstractmethod
    def interpret(self, result: Any, start: int, end: int) -> list[BaseModel]:
        """Interpret a parse result into model instances.

        Args:
            result: Any - The parse result to interpret
            start: int - Start position in the text
            end: int - End position in the text

        Returns:
            list[BaseModel] - List of extracted model instances
        """
        pass

    def extract_error(self, string: str) -> float | None:
        """Extract the error from a value string.

        Usage::

            bp = BaseParser()
            test_string = '150±5'
            end_value = bp.extract_error(test_string)
            print(end_value)  # 5.0

        Args:
            string: str - A representation of the value and error as a string

        Returns:
            Optional[float] - The error value, or None if no error found
        """
        return extract_error(string)

    def extract_value(self, string: str) -> list[float]:
        """Extract numeric values from a string.

        Usage::

            bp = BaseParser()
            test_string = '150 to 160'
            end_value = bp.extract_value(test_string)
            print(end_value)  # [150.0, 160.0]

        Args:
            string: str - A representation of the values as a string

        Returns:
            list[float] - Single value or range as list of floats
        """
        return extract_value(string)

    def extract_units(self, string: str, strict: bool = False) -> Any | None:
        """Extract units from a string.

        Raises TypeError if strict=True and dimensions don't match expected
        dimensions or string has extraneous characters.

        Usage::

            bp = QuantityParser()
            bp.model = QuantityModel()
            bp.model.dimensions = Temperature() * Length()**0.5 * Time()**(1.5)
            test_string = 'Kh2/(km/s)-1/2'
            end_units = bp.extract_units(test_string, strict=True)
            print(end_units)  # Units of: (10^1.5) * Hour^(2.0)  Meter^(0.5)  ...

        Args:
            string: str - A representation of the units as a string
            strict: bool - Whether to raise TypeError for dimension mismatches

        Returns:
            Optional[Unit] - The parsed unit, or None if parsing failed

        Raises:
            TypeError: If strict=True and dimensions don't match
        """
        return extract_units(string, self.model.dimensions, strict)


class BaseSentenceParser(BaseParser):
    """Base class for parsing sentences.

    Specialized parser for extracting data from sentence-level text.
    To implement a parser for a new property, implement the interpret function.
    """

    parse_full_sentence: bool = False

    def should_read_section(self, heading: BaseElement) -> bool:
        """Determine if a section should be read based on section phrases.

        Args:
            heading: BaseElement - The section heading to evaluate

        Returns:
            bool - True if section should be processed
        """
        should_read = True
        for sentence in heading.sentences:
            if self.allow_section_phrase is not None:
                allow_phrase_results = list(self.allow_section_phrase.scan(sentence.tokens))
                if allow_phrase_results:
                    should_read = True
                    break

            if self.skip_section_phrase is not None:
                skip_phrase_results = list(self.skip_section_phrase.scan(sentence.tokens))
                if skip_phrase_results:
                    should_read = False
        return should_read

    def parse_sentence(self, sentence: BaseElement) -> Any:
        """Parse a sentence for chemical data.

        This function is primarily called by the
        :attr:`~chemdataextractor.doc.text.Sentence.records` property.

        Args:
            sentence: BaseElement - The sentence element to parse

        Yields:
            BaseModel - Extracted model instances from the sentence
        """
        if self.trigger_phrase is not None:
            trigger_phrase_results = list(self.trigger_phrase.scan(sentence.tokens))
        if self.trigger_phrase is None or trigger_phrase_results:
            for result in self.root.scan(sentence.tokens):
                yield from self.interpret(*result)


class BaseTableParser(BaseParser):
    """Base class for parsing table data.

    Specialized parser for extracting data from table cells.
    To implement a parser for a new property, implement the interpret function.
    """

    def parse_cell(self, cell: BaseElement) -> Any:
        """Parse a table cell for chemical data.

        This function is primarily called by the
        :attr:`~chemdataextractor.doc.table.Table.records` property.

        Args:
            cell: BaseElement - The table cell element to parse

        Yields:
            BaseModel - Extracted model instances from the cell
        """
        if self.trigger_phrase is not None:
            trigger_phrase_results = list(self.trigger_phrase.scan(cell.tokens))
        if (self.trigger_phrase is None or trigger_phrase_results) and self.root is not None:
            for result in self.root.scan(cell.tokens):
                try:
                    yield from self.interpret(*result)
                except (AttributeError, TypeError) as e:
                    print(e)
                    pass

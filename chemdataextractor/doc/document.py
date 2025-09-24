"""
Document model.

This module provides the Document class, which is the central orchestrator for
chemical data extraction from scientific documents.
"""

from __future__ import annotations

import collections
import copy
import json
import logging
from abc import ABCMeta
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import BinaryIO
from typing import TextIO

try:
    from typing import Self
except ImportError:
    from typing import Self  # type: ignore[attr-defined]

from ..config import Config
from ..errors import ReaderError
from ..model.base import ModelList
from ..model.contextual_range import ParagraphRange
from ..model.contextual_range import SectionRange
from ..model.contextual_range import SentenceRange
from ..model.model import Compound
from ..text import get_encoding

# Import type definitions
from .element import CaptionedElement
from .figure import Figure
from .meta import MetaData
from .table import Table
from .text import Caption
from .text import Cell
from .text import Citation
from .text import Footnote
from .text import Heading
from .text import Paragraph
from .text import RichToken
from .text import Sentence
from .text import Title

if TYPE_CHECKING:
    from ..model.base import BaseModel
    from ..reader.base import BaseReader
    from .element import BaseElement

    # Type aliases using forward references
    FileInput = str | BinaryIO | TextIO
    ElementInput = str | bytes | "BaseElement"
    AbbreviationDef = tuple[list[str], list[str], str]
else:
    # Runtime type aliases
    FileInput = str | BinaryIO | TextIO
    ElementInput = str | bytes | Any  # BaseElement not available at runtime
    AbbreviationDef = tuple[list[str], list[str], str]

log = logging.getLogger(__name__)


class BaseDocument(collections.abc.Sequence, metaclass=ABCMeta):
    """Abstract base class for a Document.

    Provides the basic sequence interface for accessing document elements
    and defines the abstract interface for extracting chemical records.
    """

    def __repr__(self) -> str:
        """Return string representation of the document."""
        return f"<{self.__class__.__name__}: {len(self)} elements>"

    def __str__(self) -> str:
        """Return string representation of the document."""
        return f"<{self.__class__.__name__}: {len(self)} elements>"

    def __getitem__(self, index: int) -> BaseElement:
        """Get document element by index.

        Args:
            index: The element index

        Returns:
            The document element at the specified index
        """
        return self.elements[index]

    def __len__(self) -> int:
        """Return the number of elements in the document.

        Returns:
            The number of document elements
        """
        return len(self.elements)

    @property
    @abstractmethod
    def elements(self) -> list[BaseElement]:
        """Return a list of document elements.

        Returns:
            List of all elements in this document
        """
        return []

    @property
    @abstractmethod
    def records(self):
        """Chemical records that have been parsed from this Document.

        Returns:
            List of all extracted chemical records
        """
        return []


class Document(BaseDocument):
    """A document to extract data from. Contains a list of document elements.

    The Document class is the main entry point for chemical data extraction.
    It processes scientific documents through a multi-stage pipeline:

    1. Reader stage: Converts input formats to structured elements
    2. NLP processing: Tokenization, POS tagging, NER
    3. Parsing: Rule-based extraction of structured data
    4. Contextual merging: Links related information across the document

    Example:
        >>> doc = Document.from_file('paper.pdf')
        >>> records = doc.records
        >>> compounds = [r for r in records if isinstance(r, Compound)]
    """

    def __init__(self, *elements: ElementInput, **kwargs: Any) -> None:
        """Initialize a Document manually by passing document elements.

        Strings and byte strings are automatically wrapped into Paragraph elements.

        Args:
            *elements: Document elements (Paragraph, Heading, Table, etc.) or strings
            **kwargs: Additional configuration options:
                - config: Config file for the Document
                - models: List of models for data extraction
                - adjacent_sections_for_merging: Section pairs treated as adjacent
                - skip_elements: Element types to skip during parsing
                - _should_remove_subrecord_if_merged_in: Internal flag for merging
        """
        self._elements: list[BaseElement] = []
        for element in elements:
            # Convert raw text to Paragraph elements
            if isinstance(element, str):
                element = Paragraph(element)
            elif isinstance(element, bytes):
                # Try guess encoding if byte string
                encoding = get_encoding(element)
                log.warning(
                    "Guessed bytestring encoding as %s. Use unicode strings to avoid this warning.",
                    encoding,
                )
                element = Paragraph(element.decode(encoding))
            element.document = self
            self._elements.append(element)
        # Configuration
        self.config: Config = kwargs.get("config", Config())

        # Model configuration
        if "models" in kwargs:
            self.models = kwargs["models"]
        else:
            self._models: list[type[BaseModel]] = []

        # Merging configuration
        self.adjacent_sections_for_merging: list[tuple[list[str], list[str]]] | None = (
            copy.copy(kwargs["adjacent_sections_for_merging"])
            if "adjacent_sections_for_merging" in kwargs
            else None
        )

        # Element processing configuration
        self.skip_elements: list[type[BaseElement]] = kwargs.get("skip_elements", [])
        self._should_remove_subrecord_if_merged_in: bool = kwargs.get(
            "_should_remove_subrecord_if_merged_in", False
        )

        # Set parameters from configuration file
        for element in elements:
            if callable(getattr(element, "set_config", None)):
                element.set_config()
        self.skip_parsers: list[Any] = []  # List of parsers to skip
        log.debug(f"{self.__class__.__name__}: Initializing with {len(self.elements)} elements")

    def add_models(self, models: list[type[BaseModel]]) -> None:
        """Add models to all elements for data extraction.

        Args:
            models: List of model classes to add for extraction

        Example:
            >>> d = Document.from_file('paper.pdf')
            >>> d.add_models([MeltingPoint, BoilingPoint])
        """
        log.debug("Setting models")
        self._models.extend(models)
        for element in self.elements:
            if callable(getattr(element, "add_models", None)):
                element.add_models(models)
            # print(element.models)
        return

    @property
    def models(self) -> list[type[BaseModel]]:
        """Get the list of models configured for extraction.

        Returns:
            List of model classes used for data extraction
        """
        return self._models

    @models.setter
    def models(self, value: list[type[BaseModel]]) -> None:
        """Set the models for extraction and propagate to all elements.

        Args:
            value: List of model classes to use for extraction
        """
        self._models = value
        for element in self.elements:
            element.models = value

    @classmethod
    def from_file(
        cls,
        f: FileInput,
        fname: str | None = None,
        readers: list[BaseReader] | None = None,
    ) -> Self:
        """Create a Document from a file with automatic format detection.

        This is the primary entry point for processing scientific documents.
        The method automatically detects the file format and applies appropriate
        readers to extract structured content for chemical data extraction.

        Args:
            f: File input - can be:
                - str: Path to the file (recommended for most use cases)
                - BinaryIO: Open binary file object
                - TextIO: Open text file object
            fname: Optional filename override for format detection. Useful when
                reading from file-like objects without names or when the actual
                filename differs from the source.
            readers: Optional list of specific readers to try. If None, tries all
                available readers in order until one succeeds. Use this to:
                - Force a specific reader for known formats
                - Skip expensive readers for performance
                - Handle edge cases with custom readers

        Returns:
            A Document instance containing structured elements ready for data extraction.
            The document will have elements like Paragraph, Table, Figure, etc.

        Raises:
            ReaderError: If no reader can successfully process the file
            FileNotFoundError: If the specified file path doesn't exist
            PermissionError: If the file cannot be read due to permissions

        Example:
            Basic usage with automatic format detection:

            >>> # Most common usage - let ChemDataExtractor handle everything
            >>> doc = Document.from_file('research_paper.pdf')
            >>> records = doc.records
            >>> compounds = [r for r in records if r.__class__.__name__ == 'Compound']

            >>> # Process multiple file formats
            >>> for paper in ['paper.pdf', 'article.html', 'data.xml']:
            ...     doc = Document.from_file(paper)
            ...     print(f"{paper}: {len(doc.records)} records extracted")

            Using file objects (useful for web uploads, memory buffers):

            >>> with open('paper.html', 'rb') as f:
            ...     doc = Document.from_file(f, fname='paper.html')
            ...     melting_points = [r for r in doc.records
            ...                      if r.__class__.__name__ == 'MeltingPoint']

            Using specific readers for performance:

            >>> from chemdataextractor.reader.markup import HtmlReader
            >>> # Skip PDF readers if you know it's HTML
            >>> doc = Document.from_file('paper.html', readers=[HtmlReader()])

            Processing from web content:

            >>> import requests
            >>> from io import BytesIO
            >>> response = requests.get('https://example.com/paper.pdf')
            >>> doc = Document.from_file(BytesIO(response.content), fname='paper.pdf')

        Note:
            - Files are automatically opened in binary mode when a path is provided
            - Format detection uses file extensions and content analysis
            - For best results, ensure filenames have correct extensions
            - Large PDF files may take significant time to process
            - The Document retains all extracted elements for debugging and analysis

        See Also:
            - Document.from_string(): Create from string content
            - Document(): Create manually from elements
            - Reader classes: For understanding specific format handling
        """
        if isinstance(f, str):
            with open(f, "rb") as file:
                return cls.from_string(file.read(), fname=fname or f, readers=readers)
        if not fname and hasattr(f, "name"):
            fname = f.name
        return cls.from_string(f.read(), fname=fname, readers=readers)

    @classmethod
    def from_string(
        cls,
        fstring: bytes,
        fname: str | None = None,
        readers: list[BaseReader] | None = None,
    ) -> Self:
        """Create a Document from a byte string containing file contents.

        Args:
            fstring: A byte string containing the contents of a file
            fname: Optional filename to help determine file format
            readers: Optional list of readers to use. If not set, will try all default readers

        Returns:
            A new Document instance created from the byte string

        Note:
            This method expects a byte string, not a unicode string.

        Example:
            >>> contents = open('paper.html', 'rb').read()
            >>> doc = Document.from_string(contents)

        Raises:
            ReaderError: If no reader can process the input or if a unicode string is passed
        """
        if readers is None:
            from ..reader import DEFAULT_READERS

            readers = DEFAULT_READERS

        if isinstance(fstring, str):
            raise ReaderError("from_string expects a byte string, not a unicode string")

        for reader in readers:
            # Skip reader if we don't think it can read file
            if not reader.detect(fstring, fname=fname):
                continue
            try:
                d = reader.readstring(fstring)
                log.debug(f"Parsed document with {reader.__class__.__name__}")
                return d
            except ReaderError:
                pass
        raise ReaderError("Unable to read document")

    @property
    def elements(self) -> list[BaseElement]:
        """All elements in this document.

        Elements subclass from BaseElement and represent document components
        such as paragraphs, tables, figures, headings, etc.

        Returns:
            List of all document elements
        """
        return self._elements

    # TODO: memoized_property?
    @property
    def records(self):
        """Extract all chemical records found in this Document.

        This property triggers the complete data extraction pipeline, including:
        1. Parsing each element for structured data using model-specific parsers
        2. Contextual merging to link related information across document sections
        3. Confidence-based resolution when multiple values are found for the same property

        The extraction process is intelligent and context-aware:
        - Chemical entities mentioned in headings are associated with properties in subsequent paragraphs
        - Table data is parsed and linked to relevant compounds
        - Units and values are normalized and validated
        - Duplicate information is consolidated

        Returns:
            ModelList: A list of BaseModel instances representing extracted chemical records.
            Common record types include:
            - Compound: Chemical entities with names, labels, and properties
            - MeltingPoint: Melting point data with values and units
            - BoilingPoint: Boiling point information
            - IrSpectrum: Infrared spectroscopy data
            - NmrSpectrum: NMR spectroscopy information
            - And many others defined in chemdataextractor.model

        Example:
            >>> doc = Document.from_file('chemical_paper.pdf')
            >>> records = doc.records
            >>> print(f"Found {len(records)} chemical records")

            >>> # Filter by record type
            >>> compounds = [r for r in records if r.__class__.__name__ == 'Compound']
            >>> melting_points = [r for r in records if r.__class__.__name__ == 'MeltingPoint']

            >>> # Access properties
            >>> for compound in compounds:
            ...     print(f"Compound: {compound.names}")
            ...     if compound.melting_point:
            ...         print(f"  Melting point: {compound.melting_point.value} {compound.melting_point.units}")

            >>> # Serialize for JSON output
            >>> import json
            >>> json_data = [record.serialize(primitive=True) for record in records]

        Note:
            - This property performs expensive computation and should be cached if called multiple times
            - The extraction quality depends on document structure and content quality
            - Complex documents may take significant time to process
            - Results include confidence scores and contextual information for validation

        See Also:
            - ModelList: Container class with additional filtering methods
            - BaseModel.serialize(): Convert records to dictionary format
            - Individual model classes: For understanding specific record types
        """
        log.debug("Getting chemical records")
        records = ModelList()  # Final list of records -- output
        for rec in records:
            print(rec)
        records_by_el = []  # List of records by element -- used for some merging, should contain all the same records as records
        head_def_record = None  # Most recent record from a heading, title or short paragraph
        head_def_record_i = None  # Element index of head_def_record
        last_product_record = None
        title_record = None  # Records found in the title
        record_id_el_map = {}  # A dictionary that tells what element each record ID came from. We use their IDs as the records themselves change as they are updated

        prev_records = []
        el_records = []

        self._batch_parse_sentences()

        # Main loop, over all elements in the document
        for i, el in enumerate(self.elements):
            if type(el) in self.skip_elements:
                continue

            log.debug(f"Element {i}, type {str(type(el))}")
            last_id_record = None

            # FORWARD INTERDEPENDENCY RESOLUTION -- Updated model parsers to reflect defined entities
            # 1. Find any defined entities in the element e.g. "Curie Temperature, Tc"
            # 2. Update the relevant models
            element_definitions = el.definitions
            chemical_defs = el.chemical_definitions

            for model in el._streamlined_models:
                if hasattr(model, "is_id_only"):
                    model.update(chemical_defs)
                # TODO(ti250): Why is this an if-else? Shouldn't we be updating this for any model?
                # - it was this way before I changed this...
                else:
                    model.update(element_definitions)

            # Check any parsers that should be skipped
            if isinstance(el, Title | Heading):
                self.skip_parsers = []
                for model in el._streamlined_models:
                    for parser in model.parsers:
                        if hasattr(
                            parser, "should_read_section"
                        ) and not parser.should_read_section(el):
                            self.skip_parsers.append(parser)
                # print(f"\nElement: {el.text}")
                # print(f"SKIP_PARSERS: {self.skip_parsers}")

            prev_records = el_records
            el_records = el.records
            # Save the title compound
            if isinstance(el, Title) and (
                len(el_records) == 1
                and isinstance(el_records[0], Compound)
                and el_records[0].is_id_only
            ):
                title_record = el_records[0]  # TODO: why the first only?

            # Reset head_def_record unless consecutive heading with no records
            if isinstance(el, Heading) and head_def_record is not None:
                if not (i == head_def_record_i + 1 and len(el_records) == 0):
                    head_def_record = None
                    head_def_record_i = None

            # Paragraph with single sentence with single ID record considered a head_def_record
            if isinstance(el, Paragraph) and len(el.sentences) == 1:
                if (
                    len(el_records) == 1
                    and isinstance(el_records[0], Compound)
                    and el_records[0].is_id_only
                ):
                    head_def_record = el_records[0]
                    head_def_record_i = i

            # Paragraph with multiple sentences
            # We assume that if the first sentence of a paragraph contains only 1 ID Record, we can treat it as a header definition record, unless directly proceeding a header def record
            elif isinstance(el, Paragraph) and len(el.sentences) > 0:
                if not (isinstance(self.elements[i - 1], Heading) and head_def_record_i == i - 1):
                    first_sent_records = el.sentences[0].records
                    if (
                        len(first_sent_records) == 1
                        and isinstance(first_sent_records[0], Compound)
                        and first_sent_records[0].is_id_only
                    ):
                        sent_record = first_sent_records[0]
                        if sent_record.names:
                            longest_name = sorted(sent_record.names, key=len)[0]
                        if (
                            sent_record.labels
                            or (
                                sent_record.names
                                and len(longest_name) > len(el.sentences[0].text) / 2
                            )
                        ):  # TODO: Why do the length check? Maybe to make sure that the sentence mostly refers to a compound?
                            head_def_record = sent_record
                            head_def_record_i = i

            cleaned_el_records = []
            #: BACKWARD INTERDEPENDENCY RESOLUTION BEGINS HERE
            for record in el_records:
                if isinstance(record, MetaData):
                    continue
                if isinstance(record, Compound):
                    # Keep track of the most recent compound record with labels
                    if isinstance(el, Paragraph) and record.labels:
                        last_id_record = record
                    # # Keep track of the most recent compound 'product' record
                    if record.roles and "product" in record.roles:
                        last_product_record = record

                    # Heading records with compound ID's
                    if isinstance(el, Heading) and (record.labels or record.names):
                        head_def_record = record
                        head_def_record_i = i
                        # If 2 consecutive headings with compound ID, merge in from previous
                        if i > 0 and isinstance(self.elements[i - 1], Heading):
                            self.elements[i - 1]
                            if (
                                len(el_records) == 1
                                and record.is_id_only
                                and len(prev_records) == 1
                                and isinstance(prev_records[0], Compound)
                                and prev_records[0].is_id_only
                                and not (record.labels and prev_records[0].labels)
                                and not (record.names and prev_records[0].names)
                            ):
                                record.names.update(prev_records[0].names)
                                record.labels.update(prev_records[0].labels)
                                record.roles.update(prev_records[0].roles)

                # Unidentified records -- those without compound names or labels
                if record.is_unidentified:
                    if hasattr(record, "compound"):
                        # We have property values but no names or labels... try merge those from previous records
                        if isinstance(el, Paragraph) and (
                            head_def_record or last_product_record or last_id_record or title_record
                        ):
                            # head_def_record from heading takes priority if the heading directly precedes the paragraph ( NOPE: or the last_id_record has no name)
                            if (
                                head_def_record_i and head_def_record_i + 1 == i
                            ):  # or (last_id_record and not last_id_record.names)):
                                if head_def_record:
                                    record.compound = head_def_record
                                elif last_id_record:
                                    record.compound = last_id_record
                                elif last_product_record:
                                    record.compound = last_product_record
                                elif title_record:
                                    record.compound = title_record
                            else:
                                if last_id_record:
                                    record.compound = last_id_record
                                elif head_def_record:
                                    record.compound = head_def_record
                                elif last_product_record:
                                    record.compound = last_product_record
                                elif title_record:
                                    record.compound = title_record
                        else:
                            # Consider continue here to filter records missing name/label...
                            pass
                if record not in records:
                    log.debug(record.serialize())
                    cleaned_el_records.append(record)

            records.extend(cleaned_el_records)
            records_by_el.append(cleaned_el_records)
            for record in cleaned_el_records:
                record_id_el_map[id(record)] = el

        # for record in records:
        #     for contextual_record in contextual_records:
        #         # record.merge_contextual(contextual_record)
        #         contextual_record.merge_contextual(record)
        #         if not contextual_record.is_contextual:
        #             print("No longer contextual:", contextual_record)
        #             records.append(contextual_record)
        #             contextual_records.remove(contextual_record)
        #     log.debug(records.serialize())

        # Merge abbreviation definitions
        for record in records:
            compound = None
            if hasattr(record, "compound"):
                compound = record.compound
            elif isinstance(record, Compound):
                compound = record
            if compound is not None:
                for short, long_, entity in self.abbreviation_definitions:
                    if entity == "CM":
                        name = " ".join(long_)
                        abbrev = " ".join(short)
                        if compound.names:
                            if name in compound.names and abbrev not in compound.names:
                                compound.names.add(abbrev)
                            if abbrev in compound.names and name not in compound.names:
                                compound.names.add(name)

        # Merge Compound records with any shared name/label
        len_l = len(records)
        log.debug(records)
        i = 0
        removed_records = []
        while i < (len_l - 1):
            j = i + 1
            while j < len_l:
                r = records[i]
                other_r = records[j]
                r_compound = None
                if isinstance(r, Compound):
                    r_compound = r
                elif hasattr(r, "compound") and isinstance(r.compound, Compound):
                    r_compound = r.compound
                other_r_compound = None
                if isinstance(other_r, Compound):
                    other_r_compound = other_r
                elif hasattr(other_r, "compound") and isinstance(other_r.compound, Compound):
                    other_r_compound = other_r.compound
                if r_compound and other_r_compound:
                    # Strip whitespace and lowercase to compare names
                    r_names = r_compound.names
                    if r_names is None:
                        r_names = []

                    other_r_names = other_r_compound.names
                    if other_r_names is None:
                        other_r_names = []

                    rnames_std = {"".join(n.split()).lower() for n in r_names}
                    onames_std = {"".join(n.split()).lower() for n in other_r_names}

                    # Clashing labels, don't merge
                    if (
                        r_compound.labels is not None
                        and other_r_compound.labels is not None
                        and len(r_compound.labels - other_r_compound.labels) > 0
                        and len(other_r_compound.labels - r_compound.labels) > 0
                    ):
                        j += 1
                        continue

                    if (
                        r_compound.labels is not None
                        and other_r_compound.labels is not None
                        and rnames_std is not None
                        and onames_std is not None
                        and (
                            any(name in rnames_std for name in onames_std)
                            or any(label in r_compound.labels for label in other_r_compound.labels)
                        )
                    ):
                        r_compound.merge(other_r_compound)
                        other_r_compound.merge(r_compound)
                        if isinstance(r, Compound) and isinstance(other_r, Compound):
                            j_record = records.pop(j)
                            i_record = records.pop(i)
                            if i_record == r_compound:
                                removed_records.append(j_record)
                            else:
                                removed_records.append(i_record)
                            records.append(r_compound)
                            len_l -= 1
                            i -= 1
                        break
                j += 1
            i += 1

        # Be smarter about merging: Merge with closest records instead
        # of earlier records always having precedence
        i = 0
        length = len(records_by_el)

        # Iterate through the elements. We use records_by_el instead of just
        # doing element.records because element.records is not cached, and
        # extracting more than once for any element would be wasteful.
        while i < length:
            if len(records_by_el[i]) == 0:
                i += 1
                continue
            offset = 1
            max_offset = max(length - i, i)
            el = record_id_el_map[id(records_by_el[i][0])]
            merge_candidates = []
            # Collect merge candidates, starting with the records closest
            # to the current element.
            while offset <= max_offset:
                backwards_index = i - offset
                forwards_index = i + offset
                if backwards_index >= 0 and len(records_by_el[backwards_index]) != 0:
                    backwards_el = record_id_el_map[id(records_by_el[backwards_index][0])]
                    distance = self._element_distance(el, backwards_el)
                    # If we're going backwards, we should iterate over the corresponding record backwards
                    # as those at the end will be closest to the current record
                    merge_candidates.extend(
                        (distance, candidate)
                        for candidate in reversed(records_by_el[backwards_index])
                    )
                if forwards_index < length and len(records_by_el[forwards_index]) != 0:
                    forwards_el = record_id_el_map[id(records_by_el[forwards_index][0])]
                    distance = self._element_distance(el, forwards_el)
                    merge_candidates.extend(
                        (distance, candidate) for candidate in records_by_el[forwards_index]
                    )
                offset += 1

            # For each record in this current element, try merging with all of the merge candidates. The merge
            # candidates are already in a sensible order as we ordered them by their distance from the current element.
            for record in records_by_el[i]:
                for distance, candidate in merge_candidates:
                    candidate_el = record_id_el_map[id(candidate)]
                    record.merge_contextual(candidate, distance=distance)
                    record_id_el_map[id(record)] = el
                    record_id_el_map[id(candidate)] = candidate_el
            i += 1

        # clean up records
        cleaned_records = ModelList()
        for record in records:
            if (self.models and type(record) in self.models) or not self.models:
                record._clean()
                # print("\nCLEANEDRECORD:", record.required_fulfilled, record not in cleaned_records)
                # pprint(record.serialize())
                if record.required_fulfilled and record not in cleaned_records:
                    cleaned_records.append(record)

        cleaned_records.remove_subsets()

        # Reset updatables
        for el in self.elements:
            for model in el._streamlined_models:
                model.reset_updatables()

        # Append contextual records if they've filled required fields
        # for record in contextual_records:
        #     if record.required_fulfilled:
        #         records.append(record)

        self._clean_batch_parsed_records_dict()

        return cleaned_records

    def get_element_with_id(self, id: str) -> BaseElement | None:
        """Get element with the specified ID.

        Args:
            id: Identifier to search for

        Returns:
            Element with specified ID, or None if not found

        Note:
            Elements can contain nested elements (captions, footnotes, table cells, etc.)
            but this method only searches top-level elements.
        """
        return next((el for el in self.elements if el.id == id), None)

    @property
    def figures(self) -> list[Figure]:
        """All Figure elements in this Document.

        Returns:
            List of all Figure elements
        """
        return [el for el in self.elements if isinstance(el, Figure)]

    @property
    def tables(self) -> list[Table]:
        """All Table elements in this Document.

        Returns:
            List of all Table elements
        """
        return [el for el in self.elements if isinstance(el, Table)]

    @property
    def citations(self) -> list[Citation]:
        """All Citation elements in this Document.

        Returns:
            List of all Citation elements
        """
        return [el for el in self.elements if isinstance(el, Citation)]

    @property
    def footnotes(self) -> list[Footnote]:
        """All Footnote elements in this Document.

        Returns:
            List of all Footnote elements

        Note:
            Elements (e.g. Tables) can contain nested Footnotes which are not included.
        """
        # TODO: Elements (e.g. Tables) can contain nested Footnotes
        return [el for el in self.elements if isinstance(el, Footnote)]

    @property
    def titles(self) -> list[Title]:
        """All Title elements in this Document.

        Returns:
            List of all Title elements
        """
        return [el for el in self.elements if isinstance(el, Title)]

    @property
    def headings(self) -> list[Heading]:
        """All Heading elements in this Document.

        Returns:
            List of all Heading elements
        """
        return [el for el in self.elements if isinstance(el, Heading)]

    @property
    def paragraphs(self) -> list[Paragraph]:
        """All Paragraph elements in this Document.

        Returns:
            List of all Paragraph elements
        """
        return [el for el in self.elements if isinstance(el, Paragraph)]

    @property
    def captions(self) -> list[Caption]:
        """All Caption elements in this Document.

        Returns:
            List of all Caption elements
        """
        return [el for el in self.elements if isinstance(el, Caption)]

    @property
    def captioned_elements(self) -> list[CaptionedElement]:
        """All CaptionedElement elements in this Document.

        Returns:
            List of all CaptionedElement elements
        """
        return [el for el in self.elements if isinstance(el, CaptionedElement)]

    @property
    def metadata(self) -> MetaData:
        """Return metadata information.

        Returns:
            The first MetaData element found in the document

        Raises:
            IndexError: If no metadata element is found
        """
        return [el for el in self.elements if isinstance(el, MetaData)][0]

    @property
    def abbreviation_definitions(self) -> list[AbbreviationDef]:
        """All abbreviation definitions in this Document.

        Each abbreviation is a tuple of (short_form, long_form, ner_tag).

        Returns:
            List of abbreviation definition tuples
        """
        return [ab for el in self.elements for ab in el.abbreviation_definitions]

    @property
    def ner_tags(self) -> list[str | None]:
        """All Named Entity Recognition tags in this Document.

        Returns:
            List of NER tags. None for non-entities, 'B-CM' for beginning
            of chemical mentions, 'I-CM' for continuation of mentions.
        """
        return [n for el in self.elements for n in el.ner_tags]

    @property
    def cems(self) -> list[Any]:  # TODO: Type as List[Span] when Span is typed
        """All Chemical Entity Mentions in this document.

        Returns:
            List of unique chemical entity mention Spans
        """
        return list({n for el in self.elements for n in el.cems})

    @property
    def definitions(self) -> list[dict[str, Any]]:
        """All recognized definitions within this Document.

        Returns:
            List of definition dictionaries
        """
        return [defn for el in self.elements for defn in el.definitions]

    def serialize(self) -> dict[str, Any]:
        """Convert Document to Python dictionary.

        Returns:
            Dictionary with 'type': 'document' and 'elements' containing
            serialized representations of all document elements.
        """
        elements = [element.serialize() for element in self.elements]
        return {"type": "document", "elements": elements}

    def to_json(self, *args: Any, **kwargs: Any) -> str:
        """Convert Document to JSON string.

        Args:
            *args: Arguments passed to json.dumps
            **kwargs: Keyword arguments passed to json.dumps

        Returns:
            JSON string representation of the document
        """
        return json.dumps(self.serialize(), *args, **kwargs)

    def _repr_html_(self) -> str:
        """Return HTML representation for Jupyter notebook display.

        Returns:
            HTML string representation of the document
        """
        html_lines = ['<div class="cde-document">']
        for element in self.elements:
            html_lines.append(element._repr_html_())
        html_lines.append("</div>")
        return "\n".join(html_lines)

    def _batch_assign_tags(self, tagger, tag_type):
        """
        Batch assign all the tags for a certain tag type.
        This is called by the :class:`Sentence` class when it encounters
        a token without tags of a given tag type, and the tagger for that
        tag type implements the `batch_tag` method.

        See :ref:`this guide<creating_taggers>` for more details.
        """
        elements = copy.copy(self.elements)

        all_tokens = []
        for element in elements:
            if element.elements is not None:
                elements.extend(element.elements)
            if (
                hasattr(element, "tokens")
                and tagger in element.taggers
                and (
                    len(element.tokens)
                    and isinstance(element.tokens[0], RichToken)
                    and tag_type not in element.tokens[0]._tags
                )
            ):
                all_tokens.append(element.tokens)

        if hasattr(tagger, "batch_tag_for_type"):
            tag_results = tagger.batch_tag_for_type(all_tokens, tag_type)
        else:
            tag_results = tagger.batch_tag(all_tokens)

        for tag_result in tag_results:
            for token, tag in tag_result:
                token._tags[tag_type] = tag

    def _batch_parse_sentences(self):
        sentences = self.sentences
        self._batch_parsers = []
        sentences_for_parser_at_index = []
        for sentence in sentences:
            for model in sentence._streamlined_models:
                parsers = model.parsers
                for parser in parsers:
                    if hasattr(parser, "batch_parse_sentences"):
                        if parser not in self._batch_parsers:
                            self._batch_parsers.append(parser)
                            sentences_for_parser_at_index.append([sentence])
                        else:
                            batch_parser_index = self._batch_parsers.index(parser)
                            sentences_for_parser_at_index[batch_parser_index].append(sentence)
        for parser, sentences in zip(
            self._batch_parsers, sentences_for_parser_at_index, strict=False
        ):
            records_dict = parser.batch_parse_sentences(sentences)
            parser._batch_parsed_records_dict = records_dict

    def _clean_batch_parsed_records_dict(self):
        for batch_parser in self._batch_parsers:
            batch_parser._batch_parsed_records_dict = {}
        self._batch_parsers = []

    @property
    def sentences(self):
        elements = copy.copy(self.elements)

        sentences = []
        for element in elements:
            if element.elements is not None:
                elements.extend(element.elements)
            if isinstance(element, Sentence) and not isinstance(element, Cell):
                sentences.append(element)
        return sentences

    def heading_for_sentence(self, sentence):
        # Note: By design, this returns None if we are passing in a sentence
        # that's part of a heading
        elements = copy.copy(self.elements)

        elements_under_heading = []
        current_heading = None
        for element in elements:
            if isinstance(element, Heading):
                if self._sentence_in_elements(sentence, elements_under_heading):
                    return current_heading
                current_heading = element
                elements_under_heading = []
                continue
            else:
                elements_under_heading.append(element)
        if self._sentence_in_elements(sentence, elements_under_heading):
            return current_heading
        return None

    def _sentence_in_elements(self, sentence, elements):
        # Warning: this method mutates the elements argument
        for element in elements:
            if element is sentence:
                return True
            elif element.elements is not None:
                elements.extend(element.elements)
        return False

    def adjacent_sentences(self, sentence, num_adjacent=2):
        sentences = self.sentences
        sentence_index = sentences.index(sentence)
        adjacent_sentences = sentences[
            max(0, sentence_index - num_adjacent) : sentence_index + num_adjacent
        ]
        return adjacent_sentences

    def preceding_sentences(self, sentence, num_preceding=2):
        sentences = self.sentences
        sentence_index = sentences.index(sentence)
        adjacent_sentences = sentences[max(0, sentence_index - num_preceding) : sentence_index]
        return adjacent_sentences

    def following_sentences(self, sentence, num_following=2):
        sentences = self.sentences
        sentence_index = sentences.index(sentence)
        adjacent_sentences = sentences[sentence_index + 1 : sentence_index + num_following + 1]
        return adjacent_sentences

    def _element_distance(self, element_a, element_b):
        """
        This method works by getting the indices for the elements. The elements between are
        counted, with each heading in between being a section.

        Because of the way this works, the elements must be those directly contained by the document,
        e.g. paragraphs.
        """
        try:
            index_a = self.elements.index(element_a)
            index_b = self.elements.index(element_b)
        except ValueError:
            raise ValueError(f"Elements {index_a} and {index_b} not in elements for this document")
        if index_a == index_b:
            return SentenceRange()
        if index_a > index_b:
            index_a, index_b = index_b, index_a
        num_sections = 0
        num_paragraphs = 0
        for el in self.elements[index_a + 1 : index_b + 1]:
            if isinstance(el, Heading):
                num_paragraphs = 0
                num_sections += 1
            else:
                num_paragraphs += 1
        if num_paragraphs == 0 and num_sections == 0:
            print(
                f"SentenceRange returned despite non-equal indices ({index_a}, {index_b}), this is probably a bug"
            )
            return SentenceRange()
        if self._are_adjacent_sections_for_merging(
            self._section_name_for_index(index_a), self._section_name_for_index(index_b)
        ):
            # Should this be 1?
            num_sections = 0
        return num_sections * SectionRange() + num_paragraphs * ParagraphRange()

    def _section_name_for_index(self, index):
        while index >= 0:
            el = self.elements[index]
            if isinstance(el, Heading | Title):
                return el.text
            index -= 1
        return None

    def _one_of_substrings_is_in_parent(self, substrings, parent_string):
        return any(substring in parent_string for substring in substrings)

    def _are_adjacent_sections_for_merging(self, section_a, section_b):
        if self.adjacent_sections_for_merging is None or section_a is None or section_b is None:
            return False
        section_a = section_a.lower()
        section_b = section_b.lower()
        for pair_a, pair_b in self.adjacent_sections_for_merging:
            if self._one_of_substrings_is_in_parent(pair_a, section_a):
                if self._one_of_substrings_is_in_parent(pair_b, section_b):
                    return True
            if self._one_of_substrings_is_in_parent(pair_b, section_a):
                if self._one_of_substrings_is_in_parent(pair_a, section_b):
                    return True
        return False

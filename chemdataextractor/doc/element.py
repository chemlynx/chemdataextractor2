"""
Document elements.

This module provides the base classes for all document elements in ChemDataExtractor.
Elements represent structural components of documents such as paragraphs, headings,
tables, figures, and more specialized chemical text elements.
"""

from __future__ import annotations

import json
import logging
import operator
from abc import ABCMeta
from abc import abstractproperty
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import TYPE_CHECKING

try:
    from typing_extensions import Self
except ImportError:
    from typing import Self  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from ..model.base import BaseModel
    from ..model.base import ModelList
    from .document import Document

# Type aliases
ElementID = Any  # Element identifiers can be any equatable type
Citation = Any   # TODO: Type when Citation class is typed
Span = Any       # TODO: Type when Span class is typed
AbbreviationDef = tuple[List[str], List[str], str]

log = logging.getLogger(__name__)


class BaseElement(metaclass=ABCMeta):
    """Abstract base class for all Document Elements.
    
    BaseElement provides the foundational interface for all document components
    including text elements (paragraphs, sentences), structural elements (tables, figures),
    and specialized chemical text processing capabilities.
    
    Attributes:
        id: Optional identifier for this element
        models: List of models this element will use for data extraction
        document: The containing Document instance
        references: List of citations referenced in this element
    """

    def __init__(
        self,
        document: Optional["Document"] = None,
        references: Optional[List[Citation]] = None,
        id: Optional[ElementID] = None,
        models: Optional[List[type["BaseModel"]]] = None,
        **kwargs: Any
    ) -> None:
        """Initialize a BaseElement.
        
        Args:
            document: The document containing this element
            references: Citations referenced in this element  
            id: Optional identifier for this element (must be equatable)
            models: Models for this element to use for data extraction
            **kwargs: Additional keyword arguments
            
        Note:
            If this element is part of a Document, either initialize with a document
            reference or set the document attribute as soon as possible. When passed
            to a Document constructor, the document attribute is set automatically.
        """
        # The containing Document
        self._document: Optional["Document"] = document
        self.id: Optional[ElementID] = id
        self.references: List[Citation] = references if references is not None else []
        
        # Model configuration
        if models:
            self.models = models
        else:
            self.models = []
        self._streamlined_models_list: Optional[List[type["BaseModel"]]] = None

    def __repr__(self) -> str:
        """Return string representation of the element."""
        return "<%s>" % (self.__class__.__name__,)

    def __str__(self) -> str:
        """Return string representation of the element."""
        return "<%s>" % (self.__class__.__name__,)

    @property
    def document(self) -> Optional["Document"]:
        """The Document that this element belongs to.
        
        Returns:
            The containing Document, or None if not set
        """
        return self._document

    @document.setter
    def document(self, document: Optional["Document"]) -> None:
        """Set the containing Document.
        
        Args:
            document: The Document this element belongs to
            
        Note:
            Subclasses may need to override this to also assign the document to sub-elements.
        """
        self._document = document
        # If we have problems with garbage collection, use a weakref to document to avoid circular references:
        # try:
        #     self._document = weakref.proxy(document)
        # except TypeError:
        #     self._document = document

    @abstractproperty
    def records(self) -> "ModelList[BaseModel]":
        """All records found in this Element.
        
        Returns:
            ModelList of extracted BaseModel instances
        """
        return []

    # @abstractmethod  # TODO: Put this back?
    # def serialize(self):
    #     """Convert Element to python dictionary."""
    #     return []

    def add_models(self, models: List[type["BaseModel"]]) -> None:
        """Add models to this element for data extraction.
        
        Args:
            models: List of model classes to add
        """
        log.debug("Setting models on %s" % self)
        self._streamlined_models_list = None
        self.models.extend(models)
        self.models = self.models

    @property
    def models(self) -> List[type["BaseModel"]]:
        """Get the list of models configured for this element.
        
        Returns:
            List of model classes used for data extraction
        """
        return self._models

    @models.setter
    def models(self, value: List[type["BaseModel"]]) -> None:
        """Set the models for this element.
        
        Args:
            value: List of model classes to use for data extraction
        """
        self._models = value
        self._streamlined_models_list = None

    @property
    def _streamlined_models(self) -> List[type["BaseModel"]]:
        """Get the flattened and sorted list of models for this element.
        
        Returns:
            Sorted list of model classes including nested dependencies
        """
        if self._streamlined_models_list is None:
            models: Set[type["BaseModel"]] = set()
            log.debug(self.models)
            for model in self.models:
                models.update(model.flatten(include_inferred=False))
            self._streamlined_models_list = sorted(
                list(models), key=operator.attrgetter("__name__")
            )
        for model in self._streamlined_models_list:
            for parser in model.parsers:
                parser.model = model
        return self._streamlined_models_list

    def to_json(self, *args: Any, **kwargs: Any) -> str:
        """Convert element to JSON string.
        
        Args:
            *args: Arguments passed to json.dumps
            **kwargs: Keyword arguments passed to json.dumps
            
        Returns:
            JSON string representation of the element
        """
        return json.dumps(self.serialize(), *args, **kwargs)

    @property
    def elements(self) -> Optional[List["BaseElement"]]:
        """List of child elements.
        
        Returns:
            List of child elements, or None if this element has no children
        """
        return None


class CaptionedElement(BaseElement):
    """Document Element with a caption.
    
    CaptionedElement is a base class for document elements that have associated
    captions, such as figures and tables. The caption is processed for chemical
    data extraction alongside the main element content.
    
    Attributes:
        caption: The caption element for this captioned element
        label: Optional label identifier (e.g., "1" for "Table 1")
    """

    def __init__(
        self,
        caption: "BaseElement",
        label: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Initialize a CaptionedElement.
        
        Args:
            caption: The caption element for this captioned element
            label: Optional label identifier (e.g., "1" for "Table 1")
            **kwargs: Additional arguments passed to BaseElement
            
        Note:
            If this element is part of a Document, ensure the document attribute
            is set. When passed to a Document constructor, this is handled automatically.
        """
        self.caption: "BaseElement" = caption
        self.label: Optional[str] = label
        super(CaptionedElement, self).__init__(**kwargs)
        self.caption.document = self.document

    def __repr__(self) -> str:
        """Return detailed string representation of the captioned element."""
        return "%s(id=%r, references=%r, caption=%r)" % (
            self.__class__.__name__,
            self.id,
            self.references,
            self.caption.text,
        )

    def __str__(self) -> str:
        """Return the caption text as string representation."""
        return self.caption.text

    @property
    def document(self) -> Optional["Document"]:
        """The Document that this element belongs to.
        
        Returns:
            The containing Document, or None if not set
        """
        return self._document

    @document.setter
    def document(self, document: Optional["Document"]) -> None:
        """Set the containing Document and propagate to caption.
        
        Args:
            document: The Document this element belongs to
        """
        self._document = document
        self.caption.document = document

    @property
    def records(self) -> "ModelList[BaseModel]":
        """All records found in this element.
        
        Returns:
            Records extracted from the caption. Subclasses may extend this.
        """
        return self.caption.records

    @property
    def abbreviation_definitions(self) -> List[AbbreviationDef]:
        """All abbreviation definitions in this element's caption.
        
        Returns:
            List of abbreviation definition tuples from the caption
        """
        return self.caption.abbreviation_definitions

    @property
    def ner_tags(self) -> List[Optional[str]]:
        """All Named Entity Recognition tags in the caption.
        
        Returns:
            List of NER tags from the caption. None for non-entities,
            'B-CM' for beginning of chemical mentions, 'I-CM' for continuation.
        """
        return self.caption.ner_tags

    @property
    def cems(self) -> List[Span]:
        """All Chemical Entity Mentions in the caption.
        
        Returns:
            List of chemical entity mention Spans from the caption
        """
        return self.caption.cems

    @property
    def definitions(self) -> List[Dict[str, Any]]:
        """All specifier definitions in the caption.
        
        Returns:
            List of specifier definition dictionaries from the caption
        """
        return self.caption.definitions

    @property
    def chemical_definitions(self) -> List[Dict[str, Any]]:
        """All chemical definitions in the caption.
        
        Returns:
            List of chemical definition dictionaries from the caption
        """
        return self.caption.chemical_definitions

    @property
    def models(self) -> List[type["BaseModel"]]:
        """Get the list of models configured for this element.
        
        Returns:
            List of model classes used for data extraction
        """
        return self._models

    @models.setter
    def models(self, value: List[type["BaseModel"]]) -> None:
        """Set the models for this element and propagate to caption.
        
        Args:
            value: List of model classes to use for data extraction
        """
        self._models = value
        self.caption.models = value

    def serialize(self) -> Dict[str, Any]:
        """Convert this element to a dictionary.
        
        Returns:
            Dictionary with 'type' containing the class name and 'caption'
            containing the serialized caption element
        """
        data = {"type": self.__class__.__name__, "caption": self.caption.serialize()}
        return data

    @property
    def elements(self) -> List["BaseElement"]:
        """List of child elements.
        
        Returns:
            List containing the caption element
        """
        return [self.caption]

"""
Extraction pattern objects for relationship learning.

Patterns represent learned linguistic structures that can identify
relationships between chemical entities in text.

Note: Modify generate_cde_element() function to adapt the changes of phrase.py.
If any prefix/middle/suffix are empty (blank), do not add it to the resulting phrase.
Modified by jz449
"""

from __future__ import annotations

from typing import Any
from typing import List
from typing import Optional

from ..parse.elements import And
from ..parse.elements import I
from .entity import Entity
from .relationship import Relation

# Type aliases for pattern learning
PatternElements = List[Any]  # Elements that make up a pattern
EntityList = List[Entity]  # List of entities in a pattern
RelationList = List[Relation]  # List of relations associated with a pattern


class Pattern:
    """Pattern object for representing learned extraction patterns.

    Fundamentally similar to a phrase but includes confidence scoring
    for pattern quality assessment.
    """

    def __init__(
        self,
        entities: Optional[EntityList] = None,
        elements: Optional[PatternElements] = None,
        label: Optional[str] = None,
        sentences: Optional[List[str]] = None,
        order: Optional[List[int]] = None,
        relations: Optional[RelationList] = None,
        confidence: float = 0.0,
    ) -> None:
        """Initialize a Pattern.

        Args:
            entities: Entities involved in this pattern
            elements: Parser elements that make up the pattern
            label: Cluster label for this pattern
            sentences: Example sentences containing this pattern
            order: Order of entities in the pattern
            relations: Relations associated with this pattern
            confidence: Confidence score for pattern quality
        """
        self.cluster_label = label
        self.elements = elements
        self.entities = entities
        self.number_of_entities = len(order)
        self.order = order
        self.relations = relations
        self.confidence = confidence
        self.parse_expression = self.generate_cde_parse_expression()

    def __repr__(self):
        return self.to_string()

    def to_string(self):
        output_string = ""
        output_string += " ".join(self.elements["prefix"]["tokens"]) + " "
        if isinstance(self.entities[0].tag, tuple):
            output_string += "(" + ", ".join([i for i in self.entities[0].tag]) + ") "
        else:
            output_string += "(" + self.entities[0].tag + ") "
        for i in range(0, self.number_of_entities - 1):
            output_string += " ".join(self.elements["middle_" + str(i + 1)]["tokens"]) + " "
            if isinstance(self.entities[i + 1].tag, tuple):
                output_string += "(" + ", ".join([i for i in self.entities[i + 1].tag]) + ") "
            else:
                output_string += "(" + self.entities[i + 1].tag + ") "
        output_string = output_string
        output_string += " ".join(self.elements["suffix"]["tokens"])

        return output_string

    # TODO: Finish this once new parse_expressions are handled

    def generate_cde_parse_expression(self):
        """Create a CDE parse expression for this extraction pattern"""
        elements = []
        prefix_tokens = self.elements["prefix"]["tokens"]
        for token in prefix_tokens:
            if token == "<Blank>":
                continue
            elements.append(I(token))

        elements.append(self.entities[0].parse_expression)

        for middle in range(0, self.number_of_entities - 1):
            middle_tokens = self.elements["middle_" + str(middle + 1)]["tokens"]
            for token in middle_tokens:
                if token == "<Blank>":
                    continue
                elements.append(I(token))
            elements.append(self.entities[middle + 1].parse_expression)

        suffix_tokens = self.elements["suffix"]["tokens"]
        for token in suffix_tokens:
            if token == "<Blank>":
                continue
            elements.append(I(token))

        final_phrase = And(exprs=elements)
        parse_expression = (final_phrase)("phrase")
        return parse_expression

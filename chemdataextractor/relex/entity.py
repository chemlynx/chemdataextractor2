"""
Entity objects for relationship extraction.

Defines entities that participate in chemical relationships,
including their text spans, tags, and parsing expressions.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING
from typing import List
from typing import Tuple
from typing import Union

import six

from ..parse import Group
from ..parse import join

if TYPE_CHECKING:
    from ..parse.base import BaseParserElement

# Type aliases for entities
type EntityTag = str | list[str]  # Tag(s) for entity classification
type TextSpan = tuple[int, int]  # Start and end positions in text


class Entity:
    """A base entity, the fundamental unit of a Relation.

    Represents a chemical entity (compound, property, etc.) that participates
    in relationships extracted from text.
    """

    def __init__(
        self, text: str, tag: EntityTag, parse_expression: BaseParserElement, start: int, end: int
    ) -> None:
        """Create a new Entity.

        Args:
            text: The text content of the entity
            tag: Classification tag(s) for the entity
            parse_expression: Parser element used to identify this entity in text
            start: Starting token index of the entity
            end: Ending token index of the entity
        """
        self.text = six.text_type(text)
        self.tag = tag
        self.parse_expression = copy.copy(parse_expression)
        self.parse_expression.set_name(None)

        if self.parse_expression.name is None or self.parse_expression.name == "compound":
            if isinstance(self.tag, tuple):
                for sub_tag in self.tag:
                    self.parse_expression = Group(self.parse_expression)(sub_tag)
            else:
                self.parse_expression = Group(self.parse_expression)(self.tag).add_action(join)

        self.end = end
        self.start = start

    def __eq__(self, other):
        if self.text == other.text and self.end == other.end and self.start == other.start:
            return True
        else:
            return False

    def __repr__(self):
        if isinstance(self.tag, str):
            return (
                "(" + self.text + "," + self.tag + "," + str(self.start) + "," + str(self.end) + ")"
            )
        else:
            return (
                "("
                + self.text
                + ","
                + "_".join([i for i in self.tag])
                + ","
                + str(self.start)
                + ","
                + str(self.end)
                + ")"
            )

    def __str__(self):
        return self.__repr__()

    def serialize(self):
        output = current = {}
        if "__" in self.tag:
            tag = [i for i in self.tag.split("__")]
            for i, t in enumerate(tag):
                if i == len(tag) - 1:
                    current[t] = self.text
                else:
                    current[t] = {}
                current = current[t]
        else:
            output[self.tag] = self.text
        return output

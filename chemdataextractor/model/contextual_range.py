from __future__ import annotations

import numbers
from functools import total_ordering
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    pass

# Type aliases for contextual distance calculations
type RangeCount = dict["ContextualRange", float]  # Maps range types to counts
type NumericValue = int | float  # Numeric values for range calculations


@total_ordering
class ContextualRange:
    """Base class for representing contextual distances in document processing.

    ContextualRange provides a hierarchical system for measuring distances between
    document elements (sentences, paragraphs, sections, documents) to control
    contextual merging of extracted information.
    """

    @classmethod
    def _create_with_ranges(cls, ranges: RangeCount) -> ContextualRange:
        """Create a ContextualRange instance with pre-configured ranges.

        Args:
            ranges: Dictionary mapping range types to their counts

        Returns:
            New ContextualRange instance with the specified ranges
        """
        new_instance = cls()
        new_instance._constituent_ranges = ranges
        return new_instance

    def __init__(self) -> None:
        """Initialize a ContextualRange.

        Creates an empty range with no constituent ranges defined.
        """
        # Constituent ranges in form {ContextualRange instance: count}
        self._constituent_ranges: RangeCount = {}

    @property
    def constituent_ranges(self) -> RangeCount:
        """Get the constituent ranges for this contextual range.

        Returns:
            Dictionary mapping range types to their counts, defaults to {self: 1}
        """
        return self._constituent_ranges if self._constituent_ranges else {self: 1}

    def __add__(self, other: ContextualRange) -> ContextualRange:
        """Add two contextual ranges together.

        Args:
            other: Another ContextualRange to add to this one

        Returns:
            New ContextualRange with combined ranges

        Raises:
            TypeError: If other is not a ContextualRange
        """
        if not isinstance(other, ContextualRange):
            raise TypeError("ContextualRanges can only be added to other ContextualRanges")
        # Handle case when it's just e.g. DocumentRange
        new_ranges: RangeCount = {}
        # TODO(ti250): Repeated calls to the contituent_ranges method is a little wasteful.
        # I don't think this is a performance constraint right now but it may be worth
        # having some sort of memoization (or getting the dictionary once only)
        for key in self.constituent_ranges:
            if key in other.constituent_ranges:
                new_ranges[key] = self.constituent_ranges[key] + other.constituent_ranges[key]
            else:
                new_ranges[key] = self.constituent_ranges[key]
        for key in other.constituent_ranges:
            if key not in self.constituent_ranges:
                new_ranges[key] = other.constituent_ranges[key]
        return ContextualRange._create_with_ranges(new_ranges)

    def __sub__(self, other: ContextualRange) -> ContextualRange:
        """Subtract one contextual range from another.

        Args:
            other: ContextualRange to subtract from this one

        Returns:
            New ContextualRange with the difference

        Raises:
            TypeError: If other is not a ContextualRange
        """
        if not isinstance(other, ContextualRange):
            raise TypeError("ContextualRanges can only be subtracted from other ContextualRanges")
        negative_ranges: RangeCount = {}
        for key in other.constituent_ranges:
            negative_ranges[key] = -1.0 * other.constituent_ranges[key]
        negative_contextual_range = ContextualRange._create_with_ranges(negative_ranges)
        return self + negative_contextual_range

    def __mul__(self, other: NumericValue) -> ContextualRange:
        """Multiply a contextual range by a numeric value.

        Args:
            other: Numeric value to multiply by

        Returns:
            New ContextualRange with scaled values

        Raises:
            TypeError: If other is not a number
        """
        if isinstance(other, ContextualRange):
            raise TypeError(
                "Cannot multiply a ContextualRange with a ContextualRange, only numbers are supported"
            )
        elif isinstance(other, numbers.Number):
            new_ranges: RangeCount = {}
            for key in self.constituent_ranges:
                new_ranges[key] = self.constituent_ranges[key] * other
            return ContextualRange._create_with_ranges(new_ranges)
        else:
            raise TypeError(
                f"Cannot multiply a ContextualRange with a {type(other)}, only numbers are supported."
            )

    def __rmul__(self, other: NumericValue) -> ContextualRange:
        """Right multiplication for contextual ranges.

        Args:
            other: Numeric value to multiply by

        Returns:
            New ContextualRange with scaled values
        """
        return self.__mul__(other)

    def __truediv__(self, other: NumericValue) -> ContextualRange:
        """Divide a contextual range by a numeric value.

        Division is implemented for weighting distances by confidence.

        Args:
            other: Numeric value to divide by

        Returns:
            New ContextualRange with scaled values

        Raises:
            TypeError: If other is not a number
        """
        if isinstance(other, ContextualRange):
            raise TypeError(
                "Cannot divide a ContextualRange with a ContextualRange, only numbers are supported"
            )
        return self.__mul__(1.0 / other)

    def __rtruediv__(self, other: Any) -> None:
        """Right division - not supported for contextual ranges.

        Args:
            other: Any value

        Raises:
            TypeError: Always, as right division is not supported
        """
        raise TypeError("Cannot divide something by a ContextualRange")

    def __hash__(self) -> int:
        """Get hash value for the contextual range.

        Returns:
            Hash value based on the class name
        """
        string = str(self.__class__.__name__)
        return string.__hash__()

    def __eq__(self, other: Any) -> bool:
        """Check equality between contextual ranges.

        Args:
            other: Object to compare with

        Returns:
            True if ranges are equal, False otherwise
        """
        if not isinstance(other, ContextualRange):
            return False
        if self._constituent_ranges:
            for key in self.constituent_ranges:
                if (
                    key in other.constituent_ranges
                    and other.constituent_ranges[key] == self.constituent_ranges[key]
                ):
                    pass
                else:
                    return False
            return True
        else:
            return type(self) == type(other)

    def __lt__(self, other: ContextualRange) -> bool:
        """Compare contextual ranges by magnitude.

        Like comparing digits, with DocumentRange being the largest.

        Args:
            other: ContextualRange to compare with

        Returns:
            True if this range is less than other, False otherwise
        """
        ranges_by_magnitude = [
            DocumentRange(),
            SectionRange(),
            ParagraphRange(),
            SentenceRange(),
        ]
        for range_type in ranges_by_magnitude:
            self_range_count = (
                self.constituent_ranges[range_type] if range_type in self.constituent_ranges else 0
            )
            other_range_count = (
                other.constituent_ranges[range_type]
                if range_type in other.constituent_ranges
                else 0
            )
            if self_range_count < other_range_count:
                return True
            elif self_range_count > other_range_count:
                return False
        return False


# TODO(ti250): Perhaps this is nicer syntactically as ContextualRange.document?
class DocumentRange(ContextualRange):
    """Contextual range spanning an entire document.

    This is the largest contextual range, allowing merging across
    any distance within a document.
    """

    pass


class SectionRange(ContextualRange):
    """Contextual range spanning a document section.

    Allows merging within the same section but not across sections.
    """

    pass


class ParagraphRange(ContextualRange):
    """Contextual range spanning a single paragraph.

    Allows merging within the same paragraph but not across paragraphs.
    """

    pass


class SentenceRange(ContextualRange):
    """Contextual range spanning a single sentence.

    The smallest contextual range, only allowing merging within
    the same sentence.
    """

    pass


# class _NoRange(ContextualRange):
#     pass

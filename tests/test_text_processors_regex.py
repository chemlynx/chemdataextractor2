#!/usr/bin/env python
"""
test_text_processors_regex
~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Phase 2 text processing regex operations optimization.

Tests the text processing functions that will be optimized with pre-compiled patterns:
- strip_extras_text() function in text processors
- Various regex operations in document text processing

These tests ensure our optimization preserves existing functionality while
providing performance improvements through pre-compiled regex patterns.
"""

import logging
import unittest

from chemdataextractor.text.processors import floats

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestFloatsRegexOperations(unittest.TestCase):
    """Test the floats function that uses multiple regex substitutions."""

    def test_floats_bracketed_numbers_happy_path(self):
        """Test removing bracketed numbers from text - happy path."""
        result = floats("123(45)")
        # Should remove the bracketed number and return float
        self.assertEqual(result, 123.0)

        result = floats("456(78)")
        self.assertEqual(result, 456.0)

        result = floats("100(200)")
        self.assertEqual(result, 100.0)

    def test_floats_uncertainty_notation_happy_path(self):
        """Test removing uncertainty notation from text - happy path."""
        result = floats("123±45")
        # Should remove the uncertainty part and return float
        self.assertEqual(result, 123.0)

        result = floats("456.7±8.9")
        self.assertEqual(result, 456.7)

        result = floats("100±5")
        self.assertEqual(result, 100.0)

    def test_floats_scientific_notation_happy_path(self):
        """Test converting scientific notation - happy path."""
        result = floats("1.5×10^3")
        # Should convert to exponential notation
        self.assertEqual(result, 1500.0)

        result = floats("2.3x10^-4")
        self.assertEqual(result, 0.00023)

        result = floats("5×10^2")
        self.assertEqual(result, 500.0)

    def test_floats_combined_operations_happy_path(self):
        """Test multiple operations on same text - happy path."""
        result = floats("123(45)±6")
        # Should remove both bracketed number and uncertainty
        self.assertEqual(result, 123.0)

        result = floats("1.5×10^3(20)")
        # Should convert scientific notation and remove brackets
        self.assertEqual(result, 1500.0)

    def test_floats_simple_numbers_sad_path(self):
        """Test when no regex operations are needed - sad path."""
        result = floats("123")
        self.assertEqual(result, 123.0)

        result = floats("456.7")
        self.assertEqual(result, 456.7)

        result = floats("0")
        self.assertEqual(result, 0.0)

    def test_floats_invalid_input_sad_path(self):
        """Test with invalid input - sad path."""
        with self.assertRaises(ValueError):
            floats("not_a_number")

        with self.assertRaises(ValueError):
            floats("abc123def")

        with self.assertRaises(ValueError):
            floats("")

    def test_floats_with_punctuation(self):
        """Test handling of punctuation around numbers."""
        result = floats("123.45,")
        # Should strip trailing comma
        self.assertEqual(result, 123.45)

        result = floats("$123.45")
        # Should strip leading currency symbol
        self.assertEqual(result, 123.45)

        result = floats("(123.45)")
        # Should handle parentheses around entire number
        self.assertEqual(result, 123.45)

    def test_floats_with_whitespace(self):
        """Test handling of whitespace in numbers."""
        result = floats("123 456")
        # Should handle numbers with spaces (after stripping whitespace)
        self.assertEqual(result, 123456.0)

        result = floats("  123.45  ")
        # Should handle leading/trailing whitespace
        self.assertEqual(result, 123.45)

    def test_floats_edge_cases(self):
        """Test edge cases with number formatting."""
        result = floats("0(1)")
        self.assertEqual(result, 0.0)

        result = floats("123.0(0.1)")
        self.assertEqual(result, 123.0)

        result = floats("1000(50)")
        self.assertEqual(result, 1000.0)

    def test_floats_commas_in_numbers(self):
        """Test that commas are removed from numbers."""
        result = floats("1,234.56")
        # Should remove comma and parse correctly
        self.assertEqual(result, 1234.56)

        result = floats("12,345")
        self.assertEqual(result, 12345.0)


if __name__ == "__main__":
    unittest.main()

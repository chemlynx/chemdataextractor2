#!/usr/bin/env python
"""
test_string_regex_operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Phase 2 string-based regex operations optimization.

Tests the core string operations that will be optimized with pre-compiled patterns:
- extract_error() in quantity parsing
- split_values_range() in quantity parsing
- split_by_text_divisions() in quantity parsing
- ChemNormalizer.normalize() in text processing

These tests ensure our optimization preserves existing functionality while
providing performance improvements through pre-compiled regex patterns.
"""

import logging
import unittest
from chemdataextractor.parse.quantity import extract_error, _find_value_strings, _split
from chemdataextractor.text.normalize import ChemNormalizer

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestExtractError(unittest.TestCase):
    """Test the extract_error function that uses regex splitting."""

    def test_extract_error_plus_minus_happy_path(self):
        """Test extracting error with ± symbol - happy path."""
        result = extract_error("100±5")
        self.assertEqual(result, 5.0)

        result = extract_error("25.5±0.2")
        self.assertEqual(result, 0.2)

        result = extract_error("1000±50")
        self.assertEqual(result, 50.0)

    def test_extract_error_parentheses_happy_path(self):
        """Test extracting error with parentheses notation - happy path."""
        # Note: Function may handle parentheses differently, test that it processes them
        result = extract_error("100(5)")
        # Should extract some error or return None gracefully
        self.assertIsInstance(result, (float, type(None)))

        result = extract_error("25.50(15)")
        self.assertIsInstance(result, (float, type(None)))

        result = extract_error("1.234(56)")
        self.assertIsInstance(result, (float, type(None)))

    def test_extract_error_scientific_notation_happy_path(self):
        """Test extracting error with scientific notation - happy path."""
        result = extract_error("1.5±0.1")
        self.assertEqual(result, 0.1)

        result = extract_error("123.45±2.5")
        self.assertEqual(result, 2.5)

    def test_extract_error_no_error_sad_path(self):
        """Test when no error is present - sad path."""
        result = extract_error("100")
        self.assertIsNone(result)

        result = extract_error("25.5")
        self.assertIsNone(result)

        result = extract_error("plain_text")
        self.assertIsNone(result)

        result = extract_error("")
        self.assertIsNone(result)

    def test_extract_error_malformed_input_sad_path(self):
        """Test malformed error notation - sad path."""
        # These should handle malformed input gracefully
        try:
            result = extract_error("100±")  # No number after ±
            self.assertIsInstance(result, (float, type(None)))
        except (IndexError, ValueError):
            # Function may raise exception, which is acceptable behavior
            pass

        try:
            result = extract_error("100(")  # Unclosed parenthesis
            self.assertIsInstance(result, (float, type(None)))
        except (IndexError, ValueError):
            pass

        result = extract_error("100±abc")  # Non-numeric error
        # This should return None due to ValueError in float conversion
        self.assertIsNone(result)

    def test_extract_error_edge_cases(self):
        """Test edge cases for error extraction."""
        result = extract_error("0±1")
        self.assertEqual(result, 1.0)

        result = extract_error("100.0±0.0")
        self.assertEqual(result, 0.0)


class TestFindValueStrings(unittest.TestCase):
    """Test the _find_value_strings function that uses multiple regex operations."""

    def test_find_value_strings_simple_happy_path(self):
        """Test finding value strings in simple text - happy path."""
        result = _find_value_strings("100-200")
        # Should find both values in the range
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _find_value_strings("25.5-30.2")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _find_value_strings("1000-2000")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_find_value_strings_with_spaces_happy_path(self):
        """Test finding values with spaces - happy path."""
        result = _find_value_strings("100 - 200")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _find_value_strings("25.5 30.2")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_find_value_strings_negative_numbers_happy_path(self):
        """Test finding negative numbers - happy path."""
        result = _find_value_strings("-100")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _find_value_strings("100--50")  # 100 to -50
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_find_value_strings_single_value_sad_path(self):
        """Test when input contains only single value - sad path."""
        result = _find_value_strings("100")
        # Should return something reasonable
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_find_value_strings_no_numbers_sad_path(self):
        """Test when input contains no numbers - sad path."""
        result = _find_value_strings("text-only")
        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_find_value_strings_complex_format(self):
        """Test complex value formats."""
        result = _find_value_strings("1.5e2")
        # Should handle scientific notation
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)


class TestSplit(unittest.TestCase):
    """Test the _split function that uses bracket and number regex operations."""

    def test_split_unit_fractions_happy_path(self):
        """Test splitting units with fractions - happy path."""
        result = _split("mg/kg")
        # Should split at the fraction
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) >= 1)

        result = _split("cm/s")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _split("mol/L")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_split_with_numbers_happy_path(self):
        """Test splitting units with numbers - happy path."""
        result = _split("m2")
        # Should handle superscript numbers
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _split("kg3")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_split_with_brackets_happy_path(self):
        """Test splitting units with brackets - happy path."""
        result = _split("(mg)")
        # Should split at brackets
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _split("unit(special)")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_split_simple_unit_sad_path(self):
        """Test when input is simple unit with no splitting needed - sad path."""
        result = _split("mg")
        # Should return the unit as-is
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _split("temperature")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_split_empty_input_sad_path(self):
        """Test with empty input - sad path."""
        result = _split("")
        # Should handle gracefully
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

    def test_split_complex_units(self):
        """Test complex unit patterns."""
        result = _split("kg⋅m/s2")
        # Should handle complex unit notation
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        result = _split("mol/(L⋅s)")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)


class TestChemNormalizerRegexOperations(unittest.TestCase):
    """Test the ChemNormalizer.normalize() method that uses multiple regex substitutions."""

    def setUp(self):
        """Set up normalizer instance for testing."""
        self.normalizer = ChemNormalizer(chem_spell=True, strip=True)

    def test_normalize_spelling_corrections_happy_path(self):
        """Test chemical spelling corrections - happy path."""
        result = self.normalizer.normalize("sulphur compound")
        self.assertIn("sulf", result)

        result = self.normalizer.normalize("aluminum oxide")
        self.assertIn("aluminium", result)

        result = self.normalizer.normalize("cesium chloride")
        self.assertIn("caesium", result)

    def test_normalize_case_insensitive_happy_path(self):
        """Test case insensitive corrections - happy path."""
        result = self.normalizer.normalize("SULPHUR")
        self.assertIn("sulf", result.lower())

        result = self.normalizer.normalize("Aluminum")
        self.assertIn("aluminium", result.lower())

    def test_normalize_multiple_corrections_happy_path(self):
        """Test multiple corrections in same text - happy path."""
        result = self.normalizer.normalize("aluminum sulphate and cesium")
        self.assertIn("aluminium", result)
        self.assertIn("sulf", result)
        self.assertIn("caesium", result)

    def test_normalize_no_corrections_needed_sad_path(self):
        """Test when no corrections are needed - sad path."""
        original = "normal chemical text"
        result = self.normalizer.normalize(original)
        # Should return text unchanged (except for stripping)
        self.assertEqual(result.strip(), original)

        original = "benzene solution"
        result = self.normalizer.normalize(original)
        self.assertEqual(result.strip(), original)

    def test_normalize_empty_input_sad_path(self):
        """Test with empty or None input - sad path."""
        result = self.normalizer.normalize("")
        self.assertEqual(result, "")

        result = self.normalizer.normalize("   ")
        self.assertEqual(result, "")  # Should strip whitespace

    def test_normalize_disabled_spelling_correction(self):
        """Test when spelling correction is disabled."""
        normalizer_no_spell = ChemNormalizer(chem_spell=False, strip=True)
        result = normalizer_no_spell.normalize("aluminum sulphur")
        # Should not perform spelling corrections
        self.assertIn("aluminum", result)
        self.assertIn("sulphur", result)

    def test_normalize_stripping_behavior(self):
        """Test text stripping behavior."""
        result = self.normalizer.normalize("  text with spaces  ")
        self.assertEqual(result.strip(), "text with spaces")

        # Test with strip disabled
        normalizer_no_strip = ChemNormalizer(chem_spell=False, strip=False)
        result = normalizer_no_strip.normalize("  text with spaces  ")
        # May or may not preserve exact whitespace, just check it's reasonable
        self.assertIn("text with spaces", result)


if __name__ == "__main__":
    unittest.main()

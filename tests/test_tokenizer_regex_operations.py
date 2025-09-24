#!/usr/bin/env python
"""
test_tokenizer_regex_operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for Phase 2 tokenizer regex operations optimization.

Tests the tokenizer functions that will be optimized with pre-compiled patterns.
These operations are high-frequency and critical for performance.

These tests ensure our optimization preserves existing functionality while
providing performance improvements through pre-compiled regex patterns.
"""

import logging
import re
import unittest

from chemdataextractor.nlp.tokenize import ChemWordTokenizer

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestChemWordTokenizerRegexOperations(unittest.TestCase):
    """Test ChemWordTokenizer regex operations that will be optimized."""

    def setUp(self):
        """Set up tokenizer instance for testing."""
        self.tokenizer = ChemWordTokenizer()

    def test_tokenize_simple_chemical_names_happy_path(self):
        """Test tokenizing simple chemical names - happy path."""
        result = self.tokenizer.tokenize("benzene")
        self.assertIn("benzene", result)

        result = self.tokenizer.tokenize("sodium chloride")
        self.assertIn("sodium", result)
        self.assertIn("chloride", result)

        result = self.tokenizer.tokenize("methanol")
        self.assertIn("methanol", result)

    def test_tokenize_chemical_formulas_happy_path(self):
        """Test tokenizing chemical formulas - happy path."""
        result = self.tokenizer.tokenize("H2SO4")
        self.assertIn("H2SO4", result)

        result = self.tokenizer.tokenize("C6H6")
        self.assertIn("C6H6", result)

        result = self.tokenizer.tokenize("NaCl")
        self.assertIn("NaCl", result)

    def test_tokenize_numbers_and_units_happy_path(self):
        """Test tokenizing numbers with units - happy path."""
        result = self.tokenizer.tokenize("25°C")
        # Should handle temperature notation
        self.assertTrue(any("25" in token for token in result))
        self.assertTrue(any("°C" in token or "C" in token for token in result))

        result = self.tokenizer.tokenize("100mg")
        self.assertTrue(any("100" in token for token in result))
        self.assertTrue(any("mg" in token for token in result))

    def test_tokenize_complex_chemical_names_happy_path(self):
        """Test tokenizing complex chemical names with special characters - happy path."""
        result = self.tokenizer.tokenize("2,4-dichlorobenzene")
        # Should handle hyphens and commas in chemical names
        self.assertTrue(len(result) >= 1)

        result = self.tokenizer.tokenize("α-methylstyrene")
        # Should handle Greek letters
        self.assertTrue(len(result) >= 1)

        result = self.tokenizer.tokenize("tert-butanol")
        # Should handle chemical prefixes
        self.assertTrue(len(result) >= 1)

    def test_tokenize_empty_input_sad_path(self):
        """Test tokenizing empty input - sad path."""
        result = self.tokenizer.tokenize("")
        self.assertEqual(result, [])

        result = self.tokenizer.tokenize("   ")
        # Should handle whitespace appropriately
        self.assertTrue(len(result) == 0 or all(token.isspace() for token in result))

    def test_tokenize_special_characters_sad_path(self):
        """Test tokenizing text with only special characters - sad path."""
        result = self.tokenizer.tokenize("!@#$%")
        # Should handle gracefully, not crash
        self.assertIsInstance(result, list)

        result = self.tokenizer.tokenize("()[]{}")
        self.assertIsInstance(result, list)

    def test_tokenize_mixed_content_complex(self):
        """Test tokenizing mixed content with various patterns."""
        text = "The melting point of benzene (C6H6) is 5.5°C at 1 atm pressure."
        result = self.tokenizer.tokenize(text)

        # Should contain key chemical terms
        self.assertTrue(any("benzene" in token.lower() for token in result))
        self.assertTrue(any("C6H6" in token for token in result))
        self.assertTrue(any("5.5" in token for token in result))

    def test_tokenize_preserves_chemical_structure(self):
        """Test that chemical structure notation is preserved."""
        result = self.tokenizer.tokenize("CH3-CH2-OH")
        # Should maintain chemical structure connectivity
        self.assertTrue(any("-" in token or "CH" in token for token in result))

        result = self.tokenizer.tokenize("H-C≡C-H")
        # Should handle triple bond notation
        self.assertTrue(len(result) >= 1)

    def test_tokenize_scientific_notation(self):
        """Test tokenizing scientific notation."""
        result = self.tokenizer.tokenize("1.5×10^3")
        # Should handle scientific notation appropriately
        self.assertTrue(any("1.5" in token for token in result))

        result = self.tokenizer.tokenize("2.3e-4")
        self.assertTrue(any("2.3" in token for token in result))

    def test_tokenize_unicode_characters(self):
        """Test tokenizing text with unicode characters."""
        result = self.tokenizer.tokenize("α-helix β-sheet")
        # Should handle Greek letters
        self.assertTrue(len(result) >= 2)

        result = self.tokenizer.tokenize("±0.1")
        # Should handle plus-minus symbol
        self.assertTrue(len(result) >= 1)


class TestRegexPatternMatching(unittest.TestCase):
    """Test specific regex pattern matching used in tokenization."""

    def test_number_pattern_matching_happy_path(self):
        """Test number pattern matching - happy path."""
        # Simulate the regex patterns used in tokenizer
        number_pattern = r"(\d+\.?(?:\d+)?)"

        result = re.findall(number_pattern, "123.45")
        self.assertIn("123.45", result)

        result = re.findall(number_pattern, "100")
        self.assertIn("100", result)

        result = re.findall(number_pattern, "0.5")
        self.assertIn("0.5", result)

    def test_number_pattern_matching_edge_cases_happy_path(self):
        """Test number pattern edge cases - happy path."""
        number_pattern = r"(\d+\.?(?:\d+)?)"

        result = re.findall(number_pattern, "0")
        self.assertIn("0", result)

        result = re.findall(number_pattern, "1000")
        self.assertIn("1000", result)

        result = re.findall(number_pattern, "123.")
        self.assertTrue(len(result) >= 1)

    def test_number_pattern_no_match_sad_path(self):
        """Test number pattern when no numbers present - sad path."""
        number_pattern = r"(\d+\.?(?:\d+)?)"

        result = re.findall(number_pattern, "no_numbers_here")
        self.assertEqual(result, [])

        result = re.findall(number_pattern, "text only")
        self.assertEqual(result, [])

        result = re.findall(number_pattern, "")
        self.assertEqual(result, [])

    def test_parentheses_pattern_matching_happy_path(self):
        """Test parentheses pattern matching - happy path."""
        # Pattern used for bracket detection
        bracket_pattern = r"(\))|(\()"

        result = re.findall(bracket_pattern, "text(inside)more")
        # Should find both opening and closing brackets
        self.assertTrue(len(result) >= 2)

        result = re.findall(bracket_pattern, "(simple)")
        self.assertTrue(len(result) >= 2)

    def test_parentheses_pattern_unmatched_sad_path(self):
        """Test parentheses pattern with unmatched brackets - sad path."""
        bracket_pattern = r"(\))|(\()"

        result = re.findall(bracket_pattern, "text(unmatched")
        # Should find only the opening bracket
        self.assertEqual(len(result), 1)

        result = re.findall(bracket_pattern, "unmatched)text")
        # Should find only the closing bracket
        self.assertEqual(len(result), 1)

        result = re.findall(bracket_pattern, "no_brackets")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()

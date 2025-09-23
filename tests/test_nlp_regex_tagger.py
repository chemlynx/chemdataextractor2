#!/usr/bin/env python
"""
test_nlp_regex_tagger
~~~~~~~~~~~~~~~~~~~~

Unit tests for RegexTagger.

"""

import logging
import unittest

from chemdataextractor.nlp.tag import RegexTagger

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestRegexTagger(unittest.TestCase):
    """Test the RegexTagger class."""

    def test_regex_tagger_default_patterns_happy_path(self):
        """Test RegexTagger with default patterns - happy path."""
        tagger = RegexTagger()
        tokens = ["25", "degrees", "celsius"]

        result = tagger.tag(tokens)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ("25", "CD"))  # Number should be tagged as cardinal
        self.assertEqual(result[1][0], "degrees")  # Token should be preserved
        self.assertEqual(result[2][0], "celsius")

    def test_regex_tagger_custom_patterns_happy_path(self):
        """Test RegexTagger with custom patterns - happy path."""
        custom_patterns = [
            (r"^temp(erature)?$", "TEMP"),
            (r"^\d+°[CF]$", "TEMP_VALUE"),
            (r"^.*ing$", "GERUND"),
            (r"^.*", "OTHER"),  # Default fallback
        ]
        tagger = RegexTagger(patterns=custom_patterns)
        tokens = ["temperature", "25°C", "heating", "solution"]

        result = tagger.tag(tokens)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], ("temperature", "TEMP"))
        self.assertEqual(result[1], ("25°C", "TEMP_VALUE"))
        self.assertEqual(result[2], ("heating", "GERUND"))
        self.assertEqual(result[3], ("solution", "OTHER"))

    def test_regex_tagger_chemical_patterns_happy_path(self):
        """Test RegexTagger with chemical-specific patterns - happy path."""
        chem_patterns = [
            (r"^C\d+H\d+", "HYDROCARBON"),
            (r"^\d+(\.\d+)?\s*°C$", "CELSIUS_TEMP"),
            (r"^(Carbon|Hydrogen|Oxygen|Nitrogen)$", "ELEMENT"),  # Specific element names
            (r"^.*", "OTHER"),
        ]
        tagger = RegexTagger(patterns=chem_patterns)
        tokens = ["C6H6", "80.5°C", "Carbon", "benzene"]

        result = tagger.tag(tokens)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], ("C6H6", "HYDROCARBON"))
        self.assertEqual(result[1], ("80.5°C", "CELSIUS_TEMP"))
        self.assertEqual(result[2], ("Carbon", "ELEMENT"))
        self.assertEqual(result[3], ("benzene", "OTHER"))

    def test_regex_tagger_empty_tokens_sad_path(self):
        """Test RegexTagger with empty token list - sad path."""
        tagger = RegexTagger()
        tokens = []

        result = tagger.tag(tokens)

        self.assertEqual(result, [])

    def test_regex_tagger_pattern_compilation(self):
        """Test that RegexTagger properly compiles patterns."""
        patterns = [
            (r"^\d+$", "NUMBER"),
            (r"^[A-Z]+$", "CAPS"),
        ]
        tagger = RegexTagger(patterns=patterns)

        # Check that regexes are compiled
        self.assertEqual(len(tagger.regexes), 2)
        self.assertEqual(tagger.regexes[0][1], "NUMBER")
        self.assertEqual(tagger.regexes[1][1], "CAPS")

        # Test that compiled regexes work
        tokens = ["123", "ABC", "mixed"]
        result = tagger.tag(tokens)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], ("123", "NUMBER"))
        self.assertEqual(result[1], ("ABC", "CAPS"))


if __name__ == "__main__":
    unittest.main()

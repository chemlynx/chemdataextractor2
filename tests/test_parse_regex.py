#!/usr/bin/env python
"""
test_parse_regex
~~~~~~~~~~~~~~~

Unit tests for Regex parser element.

"""

import logging
import re
import unittest

from chemdataextractor.parse.elements import ParseException
from chemdataextractor.parse.elements import Regex

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestRegex(unittest.TestCase):
    """Test the Regex parser element."""

    def test_regex_simple_pattern_happy_path(self):
        """Test Regex with simple pattern - happy path."""
        regex_element = Regex(r"\d+")
        tokens = [("123", "CD"), ("text", "NN")]

        result, next_pos = regex_element._parse_tokens(tokens, 0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "123")
        self.assertEqual(next_pos, 1)

    def test_regex_word_pattern_happy_path(self):
        """Test Regex with word pattern - happy path."""
        regex_element = Regex(r"[Tt]emperature")
        tokens = [("Temperature", "NN"), ("is", "VBZ"), ("high", "JJ")]

        result, next_pos = regex_element._parse_tokens(tokens, 0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "Temperature")
        self.assertEqual(next_pos, 1)

    def test_regex_compiled_pattern_happy_path(self):
        """Test Regex with pre-compiled pattern - happy path."""
        compiled_pattern = re.compile(r"C\d+H\d+", re.I)
        regex_element = Regex(compiled_pattern)
        tokens = [("C6H6", "NN"), ("is", "VBZ"), ("benzene", "NN")]

        result, next_pos = regex_element._parse_tokens(tokens, 0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "C6H6")
        self.assertEqual(next_pos, 1)

    def test_regex_group_extraction_happy_path(self):
        """Test Regex with group extraction - happy path."""
        regex_element = Regex(r"(\d+)°C", group=1)
        tokens = [("25°C", "NN"), ("temperature", "NN")]

        result, next_pos = regex_element._parse_tokens(tokens, 0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "25")  # Should extract just the number
        self.assertEqual(next_pos, 1)

    def test_regex_no_match_sad_path(self):
        """Test Regex when pattern doesn't match - sad path."""
        regex_element = Regex(r"\d+")
        tokens = [("text", "NN"), ("only", "RB")]

        with self.assertRaises(ParseException) as context:
            regex_element._parse_tokens(tokens, 0)

        self.assertIn("Expected", str(context.exception))
        self.assertIn("got text", str(context.exception))

    def test_regex_flags_case_insensitive(self):
        """Test Regex with case-insensitive flag."""
        regex_element = Regex(r"temperature", flags=re.I)
        tokens = [("TEMPERATURE", "NN"), ("is", "VBZ")]

        result, next_pos = regex_element._parse_tokens(tokens, 0)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].text, "TEMPERATURE")
        self.assertEqual(next_pos, 1)

    def test_regex_deepcopy(self):
        """Test Regex deepcopy functionality."""
        import copy

        original = Regex(r"\d+")
        copied = copy.deepcopy(original)

        self.assertEqual(original.pattern, copied.pattern)
        # The regex objects may be the same due to Python's regex caching,
        # but the important thing is that deepcopy works without errors
        self.assertIsInstance(copied.regex, type(original.regex))


if __name__ == "__main__":
    unittest.main()

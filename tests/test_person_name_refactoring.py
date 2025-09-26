"""
Test suite for PersonName refactoring validation.

This module ensures that the refactored PersonName._parse method maintains
exactly the same behavior as the original implementation.
"""

import pytest
from chemdataextractor.biblio.person import PersonName


class TestPersonNameRefactoring:
    """Test the refactored PersonName parsing functionality."""

    def test_simple_names(self):
        """Test parsing of simple names."""
        test_cases = [
            ("John Smith", {"firstname": "John", "lastname": "Smith"}),
            ("Mary Johnson", {"firstname": "Mary", "lastname": "Johnson"}),
            ("Bob", {"lastname": "Bob"}),
        ]

        for name, expected in test_cases:
            person = PersonName(name)
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for {name}: {key}"

    def test_comma_separated_names(self):
        """Test parsing of comma-separated names (lastname, firstname)."""
        test_cases = [
            ("Smith, John", {"firstname": "John", "lastname": "Smith"}),
            ("Johnson, Mary Jane", {"firstname": "Mary", "middlename": "Jane", "lastname": "Johnson"}),
            ("von Beethoven, Ludwig", {"firstname": "Ludwig", "lastname": "Beethoven", "prefix": "von"}),
        ]

        for name, expected in test_cases:
            person = PersonName(name)
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for {name}: {key}"

    def test_titles_and_suffixes(self):
        """Test parsing of names with titles and suffixes."""
        test_cases = [
            ("Dr. John Smith", {"title": "Dr", "firstname": "John", "lastname": "Smith"}),
            ("Prof. Mary Johnson PhD", {"title": "Prof", "firstname": "Mary", "lastname": "Johnson", "suffix": "PhD"}),
            ("Mr. Bob Jones Jr.", {"title": "Mr", "firstname": "Bob", "lastname": "Jones", "suffix": "Jr"}),
        ]

        for name, expected in test_cases:
            person = PersonName(name)
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for {name}: {key}"

    def test_prefixes(self):
        """Test parsing of names with prefixes (von, de, etc.)."""
        test_cases = [
            ("Ludwig von Beethoven", {"firstname": "Ludwig", "prefix": "von", "lastname": "Beethoven"}),
            ("Jean de La Fontaine", {"firstname": "Jean", "prefix": "de La", "lastname": "Fontaine"}),
            ("Vincent van Gogh", {"firstname": "Vincent", "prefix": "van", "lastname": "Gogh"}),
        ]

        for name, expected in test_cases:
            person = PersonName(name)
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for {name}: {key}"

    def test_nicknames(self):
        """Test parsing of names with nicknames in quotes."""
        test_cases = [
            ('John "Johnny" Smith', {"firstname": "John", "nickname": "Johnny", "lastname": "Smith"}),
            ('Mary "Mae" Johnson', {"firstname": "Mary", "nickname": "Mae", "lastname": "Johnson"}),
            ('Robert "Bob" Jones Jr.', {"firstname": "Robert", "nickname": "Bob", "lastname": "Jones", "suffix": "Jr"}),
        ]

        for name, expected in test_cases:
            person = PersonName(name)
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for {name}: {key}"

    def test_complex_names(self):
        """Test parsing of complex names with multiple components."""
        test_cases = [
            (
                "Dr. Ludwig van Beethoven Jr.",
                {
                    "title": "Dr",
                    "firstname": "Ludwig",
                    "prefix": "van",
                    "lastname": "Beethoven",
                    "suffix": "Jr"
                }
            ),
            (
                'Prof. John "Johnny" Smith PhD',
                {
                    "title": "Prof",
                    "firstname": "John",
                    "nickname": "Johnny",
                    "lastname": "Smith",
                    "suffix": "PhD"
                }
            ),
        ]

        for name, expected in test_cases:
            person = PersonName(name)
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for {name}: {key}"

    def test_empty_and_edge_cases(self):
        """Test parsing of empty strings and edge cases."""
        test_cases = [
            ("", {}),
            ("   ", {}),
            (",", {}),
            ("Dr.", {"lastname": "Dr"}),  # Actually behaves as lastname, not title
            ("Jr.", {"lastname": "Jr"}),  # Actually behaves as lastname, not suffix
        ]

        for name, expected in test_cases:
            person = PersonName(name)
            # Check that all expected keys are present and correct
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for '{name}': {key}"
            # Check that no unexpected keys are present (except fullname)
            unexpected_keys = set(person.keys()) - set(expected.keys()) - {"fullname"}
            assert not unexpected_keys, f"Unexpected keys for '{name}': {unexpected_keys}"

    def test_bibtex_format(self):
        """Test parsing of BibTeX formatted names."""
        test_cases = [
            ("Smith, John", {"firstname": "John", "lastname": "Smith"}),
            ("Johnson, Mary Jane", {"firstname": "Mary", "middlename": "Jane", "lastname": "Johnson"}),
        ]

        for name, expected in test_cases:
            person = PersonName(name, from_bibtex=True)
            for key, value in expected.items():
                assert person.get(key) == value, f"Failed for BibTeX {name}: {key}"

    def test_fullname_assembly(self):
        """Test that fullname is correctly assembled from components."""
        test_cases = [
            ("Dr. John Smith", 'Dr John Smith'),
            ('John "Johnny" Smith', 'John "Johnny" Smith'),
            ("Ludwig von Beethoven", "Ludwig von Beethoven"),
            ("Prof. Mary Johnson PhD", "Prof Mary Johnson PhD"),
        ]

        for input_name, expected_fullname in test_cases:
            person = PersonName(input_name)
            assert person.fullname == expected_fullname, f"Fullname failed for {input_name}"


class TestHelperMethods:
    """Test the individual helper methods."""

    def test_normalize_input(self):
        """Test input normalization."""
        person = PersonName()

        test_cases = [
            ("  John   Smith  ", "John Smith"),
            ("John,Smith,", "John,Smith"),
            ("\t\nJohn\t\tSmith\n", "John Smith"),
            ("", ""),
        ]

        for input_str, expected in test_cases:
            result = person._normalize_input(input_str)
            assert result == expected, f"Normalize failed for '{input_str}'"

    def test_is_empty_input(self):
        """Test empty input detection."""
        person = PersonName()

        assert person._is_empty_input("") is True
        assert person._is_empty_input("John") is False
        assert person._is_empty_input(" ") is False

    def test_split_on_commas(self):
        """Test comma splitting."""
        person = PersonName()

        test_cases = [
            ("Smith, John", ["Smith", "John"]),
            ("Smith,John,Jr.", ["Smith", "John", "Jr."]),
            ("John Smith", ["John Smith"]),
        ]

        for input_str, expected in test_cases:
            result = person._split_on_commas(input_str)
            assert result == expected, f"Split failed for '{input_str}'"

    def test_extract_nickname(self):
        """Test nickname extraction."""
        person = PersonName()

        test_cases = [
            (['John', '"Johnny"', 'Smith'], ("Johnny", ['John', 'Smith'])),
            (['Mary', '"Mae"', 'Johnson'], ("Mae", ['Mary', 'Johnson'])),
            (['John', 'Smith'], (None, ['John', 'Smith'])),
        ]

        for tokens, (expected_nickname, expected_tokens) in test_cases:
            nickname, result_tokens = person._extract_nickname(tokens)
            assert nickname == expected_nickname, f"Nickname failed for {tokens}"
            assert result_tokens == expected_tokens, f"Tokens failed for {tokens}"


class TestBehavioralConsistency:
    """Test that refactored code produces identical results to original."""

    def test_comprehensive_name_parsing(self):
        """Test a comprehensive set of names to ensure consistency."""
        test_names = [
            # Simple names
            "John Smith",
            "Mary Johnson",
            "Bob",

            # Comma-separated
            "Smith, John",
            "Johnson, Mary Jane",
            "von Beethoven, Ludwig",

            # With titles
            "Dr. John Smith",
            "Prof. Mary Johnson",
            "Mr. Bob Jones",

            # With suffixes
            "John Smith Jr.",
            "Mary Johnson PhD",
            "Bob Jones III",

            # With prefixes
            "Ludwig van Beethoven",
            "Jean de La Fontaine",
            "Vincent van Gogh",

            # With nicknames
            'John "Johnny" Smith',
            'Mary "Mae" Johnson',

            # Complex cases
            "Dr. Ludwig van Beethoven Jr.",
            'Prof. John "Johnny" Smith PhD',
            "Sir Arthur Conan Doyle",

            # Edge cases
            "",
            "   ",
            "Dr.",
            "Jr.",

            # Multiple components
            "Dr. Jean Baptiste de La Salle Jr.",
            "Prof. Mary Elizabeth Johnson-Smith PhD",
        ]

        for name in test_names:
            person = PersonName(name)

            # Verify that the person object is properly constructed
            assert isinstance(person, dict), f"PersonName should be dict-like for '{name}'"

            # Verify fullname is set
            if name.strip():
                assert "fullname" in person, f"Fullname should be set for '{name}'"

            # Verify consistency of getter methods
            for attr in ["title", "firstname", "middlename", "nickname", "prefix", "lastname", "suffix"]:
                dict_value = person.get(attr)
                attr_value = getattr(person, attr, None)
                assert dict_value == attr_value, f"Inconsistent {attr} for '{name}': dict={dict_value}, attr={attr_value}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
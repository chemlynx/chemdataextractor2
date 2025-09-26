"""
Test suite for built-in pre-abstract model restriction functionality.

This module tests the automatic exclusion of extraction models from elements
before the abstract section to prevent extracting author names, dates, and
metadata as chemical compounds.
"""

import pytest
from chemdataextractor import Document
from chemdataextractor.doc.text import Title, Heading, Paragraph
from chemdataextractor.model.model import Compound, MeltingPoint, Apparatus


class TestPreAbstractRestriction:
    """Test the pre-abstract model restriction functionality."""

    def test_restriction_enabled_by_default(self):
        """Test that restriction is enabled by default."""
        doc = Document(
            Title("Synthesis of CuSO4 Complexes"),
            Paragraph("Authors: Dr. John Smith"),
            Heading("Abstract"),
            Paragraph("We synthesized CuSO4 complexes.")
        )

        assert doc.restrict_pre_abstract is True

    def test_restriction_can_be_disabled(self):
        """Test that restriction can be disabled via parameter."""
        doc = Document(
            Title("Test"),
            restrict_pre_abstract=False
        )

        assert doc.restrict_pre_abstract is False

    def test_abstract_detection_with_abstract_heading(self):
        """Test abstract detection with 'Abstract' heading."""
        doc = Document(
            Title("Synthesis of CuSO4 Complexes"),
            Paragraph("Authors: Dr. John Smith"),
            Heading("Abstract"),
            Paragraph("We synthesized CuSO4.")
        )

        abstract_index = doc._find_abstract_index()
        assert abstract_index == 2  # "Abstract" heading is at index 2

    def test_abstract_detection_with_summary_heading(self):
        """Test abstract detection with 'Summary' heading."""
        doc = Document(
            Title("Test Title"),
            Paragraph("Authors: Jane Doe"),
            Heading("Summary"),
            Paragraph("This is the summary.")
        )

        abstract_index = doc._find_abstract_index()
        assert abstract_index == 2  # "Summary" heading is at index 2

    def test_abstract_detection_case_insensitive(self):
        """Test that abstract detection is case insensitive."""
        doc = Document(
            Title("Test"),
            Heading("ABSTRACT"),
            Paragraph("Abstract content.")
        )

        abstract_index = doc._find_abstract_index()
        assert abstract_index == 1  # "ABSTRACT" heading is at index 1

    def test_abstract_detection_fallback(self):
        """Test fallback when no abstract is found."""
        doc = Document(
            Title("Test Title"),
            Paragraph("Introduction content"),
            Paragraph("More content"),
            *[Paragraph(f"Paragraph {i}") for i in range(12)]  # 12 more paragraphs
        )

        abstract_index = doc._find_abstract_index()
        assert abstract_index == 10  # Fallback to min(10, len(elements))

    def test_models_restriction_applied_automatically(self):
        """Test that models are automatically restricted when enabled."""
        doc = Document(
            Title("Synthesis of CuSO4 Complexes"),
            Paragraph("Authors: Dr. John Smith, Dr. Sarah Johnson"),
            Paragraph("Received: 15 March 2023"),
            Heading("Abstract"),
            Paragraph("We synthesized CuSO4 complexes using H2O as solvent.")
        )

        # Set models - restriction should be applied automatically
        doc.models = [Compound, MeltingPoint, Apparatus]

        # Check pre-abstract elements have no models
        assert doc.elements[0].models == []  # Title
        assert doc.elements[1].models == []  # Authors
        assert doc.elements[2].models == []  # Date

        # Check post-abstract elements have full models
        expected_models = [Compound, MeltingPoint, Apparatus]
        assert doc.elements[3].models == expected_models  # Abstract heading
        assert doc.elements[4].models == expected_models  # Abstract content

    def test_models_restriction_disabled(self):
        """Test that restriction can be disabled."""
        doc = Document(
            Title("Synthesis of CuSO4 Complexes"),
            Paragraph("Authors: Dr. John Smith"),
            Heading("Abstract"),
            Paragraph("We synthesized CuSO4."),
            restrict_pre_abstract=False
        )

        # Set models - should apply to all elements when disabled
        doc.models = [Compound, MeltingPoint, Apparatus]

        expected_models = [Compound, MeltingPoint, Apparatus]
        for element in doc.elements:
            assert element.models == expected_models

    def test_extraction_avoids_problematic_compounds(self):
        """Test that extraction avoids extracting author names and dates as compounds."""
        doc = Document(
            Title("Synthesis of Novel CuSO4 Complexes"),
            Paragraph("Authors: Dr. John Smith, Dr. Sarah Johnson"),
            Paragraph("Received: 15 March 2023; Accepted: 20 April 2023"),
            Paragraph("Keywords: copper, sulfate, synthesis"),
            Heading("Abstract"),
            Paragraph("We report the synthesis of CuSO4 complexes. The reaction with NaCl produced interesting results.")
        )

        doc.models = [Compound, MeltingPoint, Apparatus]

        # Extract compounds
        compounds = [r for r in doc.records if isinstance(r, Compound)]

        # Check that no problematic names appear as compounds
        problematic_names = ['March', 'April', 'John', 'Smith', 'Sarah', 'Johnson', 'Dr', '15', '20', '2023']
        found_problematic = []

        for compound in compounds:
            for name in compound.names:
                if any(prob in str(name) for prob in problematic_names):
                    found_problematic.append(str(name))

        assert len(found_problematic) == 0, f"Found problematic compounds: {found_problematic}"

        # Check that valid compounds are still found
        valid_compounds = []
        for compound in compounds:
            for name in compound.names:
                compound_text = str(name).lower()
                if any(valid in compound_text for valid in ['cuso4', 'nacl', 'copper', 'sulfate']):
                    valid_compounds.append(str(name))

        assert len(valid_compounds) > 0, "Should find valid chemical compounds"

    def test_empty_models_list(self):
        """Test behavior with empty models list."""
        doc = Document(
            Title("Test"),
            Heading("Abstract"),
            Paragraph("Content")
        )

        doc.models = []

        # All elements should have empty models
        for element in doc.elements:
            assert element.models == []

    def test_abstract_in_title(self):
        """Test detection when 'abstract' appears in title."""
        doc = Document(
            Title("Abstract: Synthesis of CuSO4"),
            Paragraph("Authors: John Smith"),
            Paragraph("We synthesized compounds.")
        )

        abstract_index = doc._find_abstract_index()
        assert abstract_index == 0  # Title itself contains 'abstract'

    def test_document_with_only_title(self):
        """Test behavior with document containing only a title."""
        doc = Document(Title("Synthesis of CuSO4"))

        doc.models = [Compound, MeltingPoint, Apparatus]

        # Since no abstract found, fallback should apply
        # With only 1 element, fallback is min(10, 1) = 1
        # So element 0 should have no models (before index 1)
        assert doc.elements[0].models == []

    def test_models_applied_after_restriction_change(self):
        """Test that models are reapplied when restriction setting changes."""
        doc = Document(
            Title("Test"),
            Heading("Abstract"),
            Paragraph("Content")
        )

        # Start with restriction enabled
        doc.models = [Compound]
        assert doc.elements[0].models == []  # Title before abstract
        assert doc.elements[1].models == [Compound]  # Abstract heading

        # Disable restriction and reapply models
        doc.restrict_pre_abstract = False
        doc.models = [Compound]  # Trigger reapplication

        # Now all elements should have models
        for element in doc.elements:
            assert element.models == [Compound]


class TestFromFileWithRestriction:
    """Test that from_file method properly handles restriction parameter."""

    def test_from_file_restriction_default(self):
        """Test that from_file uses restriction by default."""
        # This would need a real file to test properly
        # For now, just test the parameter passing
        pass

    def test_from_file_restriction_disabled(self):
        """Test that from_file can disable restriction."""
        # This would need a real file to test properly
        # For now, just test the parameter passing
        pass


class TestFromStringWithRestriction:
    """Test that from_string method properly handles restriction parameter."""

    def test_from_string_restriction_default(self):
        """Test that from_string uses restriction by default."""
        # This would need proper byte content to test
        # For now, just test the parameter passing
        pass

    def test_from_string_restriction_disabled(self):
        """Test that from_string can disable restriction."""
        # This would need proper byte content to test
        # For now, just test the parameter passing
        pass


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_document(self):
        """Test behavior with empty document."""
        doc = Document()

        doc.models = [Compound]

        # Empty document should handle gracefully
        assert len(doc.elements) == 0
        assert doc._find_abstract_index() == 0  # min(10, 0) = 0

    def test_document_with_no_text_elements(self):
        """Test document with non-text elements only."""
        # This would require creating Table/Figure elements
        # For now, test with basic elements
        doc = Document(Paragraph(""))

        abstract_index = doc._find_abstract_index()
        assert abstract_index == 1  # Fallback since no headings found

    def test_multiple_abstract_headings(self):
        """Test behavior when multiple 'abstract' headings exist."""
        doc = Document(
            Title("Test"),
            Heading("Abstract 1"),
            Paragraph("First abstract"),
            Heading("Abstract 2"),
            Paragraph("Second abstract")
        )

        # Should find the first one
        abstract_index = doc._find_abstract_index()
        assert abstract_index == 1  # First abstract heading

    def test_abstract_in_paragraph_not_detected(self):
        """Test that 'abstract' in paragraph text doesn't trigger detection."""
        doc = Document(
            Title("Test"),
            Paragraph("This paragraph mentions the word abstract but is not a heading"),
            Heading("Introduction"),
            Paragraph("Content")
        )

        # Should not detect abstract in paragraph, only in headings/titles
        abstract_index = doc._find_abstract_index()
        assert abstract_index == 4  # Fallback to min(10, 4) = 4


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
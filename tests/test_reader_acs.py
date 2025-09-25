"""
test_reader_acs
~~~~~~~~~~~~~~~

Test ACS reader.

"""

import logging
import os
import unittest
from pathlib import Path

from chemdataextractor import Document
from chemdataextractor.reader import AcsHtmlReader

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestAcsHtmlReader(unittest.TestCase):
    maxDiff = None

    def test_detect(self):
        """Test AcsHtmlReader can detect an ACS document."""
        r = AcsHtmlReader()
        fname = "acs.jmedchem.6b00723.html"
        with open(Path(__file__).parent / "data" / "acs" / fname, "rb") as f:
            content = f.read()
        self.assertEqual(r.detect(content, fname=fname), True)

    def test_direct_usage(self):
        """Test AcsHtmlReader used directly to parse file."""
        r = AcsHtmlReader()
        fname = "acs.jmedchem.6b00723.html"
        with open(Path(__file__).parent / "data" / "acs" / fname, "rb") as f:
            content = f.read()
            d = r.readstring(content)
        self.assertEqual(len(d.elements), 198)

    def test_document_usage(self):
        """Test AcsHtmlReader used via Document.from_file."""
        fname = "acs.jmedchem.6b00723.html"
        with open(Path(__file__).parent / "data" / "acs" / fname, "rb") as f:
            d = Document.from_file(f, readers=[AcsHtmlReader()])
        self.assertEqual(len(d.elements), 198)


if __name__ == "__main__":
    unittest.main()

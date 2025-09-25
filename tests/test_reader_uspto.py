"""
test_reader_uspto
~~~~~~~~~~~~~~~~~

Test USPTO reader.

"""

import logging
import os
import unittest
from pathlib import Path

from chemdataextractor import Document
from chemdataextractor.reader import UsptoXmlReader

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestUsptoReader(unittest.TestCase):
    maxDiff = None

    def test_detect(self):
        """Test UsptoXmlReader can detect a USPTO XML document."""
        r = UsptoXmlReader()
        fname = "US06840965B2.xml"
        with open(Path(__file__).parent / "data" / "uspto" / fname, "rb") as f:
            content = f.read()
        self.assertEqual(r.detect(content, fname=fname), True)

    def test_direct_usage(self):
        """Test UsptoXmlReader used directly to parse file."""
        r = UsptoXmlReader()
        fname = "US06840965B2.xml"
        with open(Path(__file__).parent / "data" / "uspto" / fname, "rb") as f:
            content = f.read()
            d = r.readstring(content)
        self.assertEqual(len(d.elements), 112)

    def test_document_usage(self):
        """Test UsptoXmlReader used via Document.from_file."""
        fname = "US06840965B2.xml"
        with open(Path(__file__).parent / "data" / "uspto" / fname, "rb") as f:
            d = Document.from_file(f, readers=[UsptoXmlReader()])
        self.assertEqual(len(d.elements), 112)


if __name__ == "__main__":
    unittest.main()

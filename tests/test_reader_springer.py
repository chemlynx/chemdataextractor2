"""
test_reader_springer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Test reader for Springer.

.. codeauthor:: Shu Huang <sh2009@cam.ac.uk>
"""

import logging
import os
import unittest
from pathlib import Path

from chemdataextractor.doc.document import Document
from chemdataextractor.reader.springer_jats import SpringerJatsReader

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class TestSpringerJatsReader(unittest.TestCase):
    def test_detect(self):
        """Test RscXMLReader can detect an RSC document."""
        r = SpringerJatsReader()
        fname = "spr_test1.xml"
        with open(Path(__file__).parent / "data" / "springer" / fname, "rb") as f:
            content = f.read()
        self.assertEqual(r.detect(content, fname=fname), True)

    def test_direct_usage(self):
        """Test RscXMLReader used directly to parse file."""
        r = SpringerJatsReader()
        fname = "spr_test1.xml"
        with open(Path(__file__).parent / "data" / "springer" / fname, "rb") as f:
            content = f.read()
            d = r.readstring(content)
        self.assertEqual(len(d.elements), 307)

    def test_document_usage(self):
        """Test RscXMLReader used via Document.from_file."""
        fname = "spr_test1.xml"
        with open(Path(__file__).parent / "data" / "springer" / fname, "rb") as f:
            d = Document.from_file(f, readers=[SpringerJatsReader()])
        self.assertEqual(len(d.elements), 307)


if __name__ == "__main__":
    unittest.main()

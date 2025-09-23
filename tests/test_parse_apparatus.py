"""
test_parse_apparatus
~~~~~~~~~~~~~~~~~~~~



"""

import logging
import unittest

from lxml import etree

from chemdataextractor.doc.text import Paragraph
from chemdataextractor.doc.text import Sentence
from chemdataextractor.model import Apparatus
from chemdataextractor.parse.apparatus import apparatus_phrase

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TestParseApparatus(unittest.TestCase):
    """Simple apparatus parse tests."""

    maxDiff = None

    def do_parse(self, input, expected):
        s = Sentence(input)
        log.debug(s)
        log.debug(s.tokens)
        results = []
        for i, r in enumerate(apparatus_phrase.scan(s.tokens)):
            log.debug(etree.tostring(r[0], pretty_print=True, encoding="unicode"))
            results.append(etree.tostring(r[0], encoding="unicode"))
        self.assertEqual(expected, results)

    def test_apparatus(self):
        """"""

        s = "The photoluminescence quantum yield (PLQY) was measured using a HORIBA Jobin Yvon FluoroMax-4 spectrofluorimeter"
        expected = [
            "<apparatus>HORIBA Jobin Yvon FluoroMax-4 spectrofluorimeter</apparatus>"
        ]
        self.do_parse(s, expected)

    def test_apparatus2(self):
        """"""
        s = "1H NMR spectra were recorded on a Varian MR-400 MHz instrument."
        expected = ["<apparatus>Varian MR-400 MHz instrument</apparatus>"]
        self.do_parse(s, expected)

    def test_apparatus_record(self):
        """"""
        p = Paragraph(
            "The photoluminescence quantum yield (PLQY) was measured using a HORIBA Jobin Yvon FluoroMax-4 spectrofluorimeter."
        )
        p.models = [Apparatus]
        expected = [
            {"Apparatus": {"name": "HORIBA Jobin Yvon FluoroMax-4 spectrofluorimeter"}}
        ]
        self.assertEqual(expected, [r.serialize() for r in p.records])

    def test_apparatus_record2(self):
        """"""
        p = Paragraph("NMR was run on a 400 MHz Varian NMR.")
        p.models = [Apparatus]
        expected = [{"Apparatus": {"name": "400 MHz Varian NMR"}}]
        self.assertEqual(expected, [r.serialize() for r in p.records])


if __name__ == "__main__":
    unittest.main()

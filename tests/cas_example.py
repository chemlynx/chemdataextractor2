from lxml import etree

from chemdataextractor.doc.document import Document
from chemdataextractor.doc.text import Heading
from chemdataextractor.doc.text import Paragraph
from chemdataextractor.doc.text import Sentence
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import MeltingPoint
from chemdataextractor.parse.cem import cem_phrase
from chemdataextractor.parse.cem import chemical_label_phrase
from chemdataextractor.parse.cem import compound_heading_phrase

s = Sentence("CAS 1242336-53-3")
s.models = [Compound]

results = [r.serialize() for r in s.records]

print("Done")

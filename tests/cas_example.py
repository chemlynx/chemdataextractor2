from chemdataextractor.doc.text import Sentence
from chemdataextractor.model.model import Compound

s = Sentence("CAS 1242336-53-3")
s.models = [Compound]

results = [r.serialize() for r in s.records]

print("Done")

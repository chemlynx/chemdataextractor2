"""
Reader classes that read a file and produce a ChemDataExtractor Document object.

"""

from .acs import AcsHtmlReader
from .cssp import CsspHtmlReader
from .elsevier import ElsevierXmlReader
from .markup import HtmlReader
from .markup import XmlReader
from .nlm import NlmXmlReader
from .pdf import PdfReader
from .plaintext import PlainTextReader
from .rsc import RscHtmlReader
from .springer_jats import SpringerJatsReader
from .uspto import UsptoXmlReader

DEFAULT_READERS = [
    AcsHtmlReader(),
    RscHtmlReader(),
    NlmXmlReader(),
    UsptoXmlReader(),
    CsspHtmlReader(),
    ElsevierXmlReader(),
    XmlReader(),
    HtmlReader(),
    PdfReader(),
    PlainTextReader(),
    SpringerJatsReader(),
]

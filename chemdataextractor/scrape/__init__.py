"""
Declarative scraping framework for extracting structured data from HTML and XML documents.

"""


#: Block level HTML elements
BLOCK_ELEMENTS = {
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "pre",
    "dd",
    "dl",
    "div",
    "noscript",
    "blockquote",
    "form",
    "hr",
    "table",
    "fieldset",
    "address",
    "article",
    "aside",
    "audio",
    "canvas",
    "figcaption",
    "figure",
    "footer",
    "header",
    "hgroup",
    "output",
    "section",
    "body",
    "head",
    "title",
    "tr",
    "td",
    "th",
    "thead",
    "tfoot",
    "dt",
    "li",
    "tbody",
}

#: Inline level HTML elements
INLINE_ELEMENTS = {
    "b",
    "big",
    "i",
    "small",
    "tt",
    "abbr",
    "acronym",
    "cite",
    "code",
    "dfn",
    "em",
    "kbd",
    "strong",
    "samp",
    "var",
    "a",
    "bdo",
    "br",
    "img",
    "map",
    "object",
    "q",
    "script",
    "span",
    "sub",
    "sup",
    "button",
    "input",
    "label",
    "select",
    "textarea",
    "blink",
    "font",
    "marquee",
    "nobr",
    "s",
    "strike",
    "u",
    "wbr",
}


from .clean import Cleaner
from .clean import clean
from .clean import clean_html
from .clean import clean_markup
from .entity import DocumentEntity
from .entity import Entity
from .entity import EntityList
from .fields import BoolField
from .fields import DateTimeField
from .fields import EntityField
from .fields import FloatField
from .fields import IntField
from .fields import StringField
from .fields import UrlField
from .pub.elsevier import ElsevierHtmlDocument
from .pub.elsevier import ElsevierXmlDocument
from .pub.nlm import NlmXmlDocument
from .pub.rsc import RscHtmlDocument
from .pub.springer import SpringerXmlDocument
from .scraper import GetRequester
from .scraper import HtmlFormat
from .scraper import PostRequester
from .scraper import RssScraper
from .scraper import SearchScraper
from .scraper import UrlScraper
from .scraper import XmlFormat
from .selector import Selector
from .selector import SelectorList

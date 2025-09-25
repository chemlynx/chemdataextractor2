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


from .clean import Cleaner  # noqa: E402
from .clean import clean  # noqa: E402
from .clean import clean_html  # noqa: E402
from .clean import clean_markup  # noqa: E402
from .entity import DocumentEntity  # noqa: E402
from .entity import Entity  # noqa: E402
from .entity import EntityList  # noqa: E402
from .fields import BoolField  # noqa: E402
from .fields import DateTimeField  # noqa: E402
from .fields import EntityField  # noqa: E402
from .fields import FloatField  # noqa: E402
from .fields import IntField  # noqa: E402
from .fields import StringField  # noqa: E402
from .fields import UrlField  # noqa: E402
from .pub.elsevier import ElsevierHtmlDocument  # noqa: E402
from .pub.elsevier import ElsevierXmlDocument  # noqa: E402
from .pub.nlm import NlmXmlDocument  # noqa: E402
from .pub.rsc import RscHtmlDocument  # noqa: E402
from .pub.springer import SpringerXmlDocument  # noqa: E402
from .scraper import GetRequester  # noqa: E402
from .scraper import HtmlFormat  # noqa: E402
from .scraper import PostRequester  # noqa: E402
from .scraper import RssScraper  # noqa: E402
from .scraper import SearchScraper  # noqa: E402
from .scraper import UrlScraper  # noqa: E402
from .scraper import XmlFormat  # noqa: E402
from .selector import Selector  # noqa: E402
from .selector import SelectorList  # noqa: E402

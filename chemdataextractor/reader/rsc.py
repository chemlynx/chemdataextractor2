"""
Readers for documents from the RSC.

Provides specialized HTML reader for Royal Society of Chemistry (RSC) publications
with custom cleaning functions and table processing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

from ..doc.text import Footnote
from ..scrape.clean import Cleaner
from ..scrape.clean import clean
from ..scrape.pub.rsc import replace_rsc_img_chars
from .markup import HtmlReader

if TYPE_CHECKING:
    from lxml.html import HtmlElement

log = logging.getLogger(__name__)

# XML stripper that removes the tags around numbers in chemical formulas
strip_rsc_html = Cleaner(
    strip_xpath=".//b",
    kill_xpath=".//p[contains(@class, 'header_text')] | //*[@id='art-admin']",
)


def rsc_html_whitespace(document: HtmlElement) -> HtmlElement:
    """Remove whitespace in xml.text or xml.tails for all elements, if it is only whitespace.

    Args:
        document: HTML document element to clean

    Returns:
        Cleaned HTML document element
    """
    # selects all tags and checks if the text or tail are spaces
    for el in document.xpath("//*"):
        if el.tag == "b":
            continue
        if str(el.text).isspace():
            el.text = ""
        if str(el.tail).isspace():
            el.tail = ""
        if el.text:
            el.text = el.text.replace("\n", " ")
    return document


def join_rsc_table_captions(document: HtmlElement) -> HtmlElement:
    """Add wrapper tag around Tables and their respective captions.

    Args:
        document: HTML document element to process

    Returns:
        Processed HTML document element
    """
    for el in document.xpath('//div[@class="table_caption"]'):
        next_el = el.getnext()
        if next_el.tag == "div" and next_el.attrib["class"] == "rtable__wrapper":
            caption_el = el
            table_el = next_el
            table_el.insert(0, caption_el)
    return document


class RscHtmlReader(HtmlReader):
    """Reader for HTML documents from the RSC."""

    cleaners = [
        clean,
        rsc_html_whitespace,
        replace_rsc_img_chars,
        join_rsc_table_captions,
        strip_rsc_html,
    ]

    root_css = "html"
    title_css = "h1, .title_heading"
    heading_css = "h2, h3, h4, h5, h6, .a_heading, .b_heading, .c_heading, .c_heading_indent, .d_heading, .d_heading_indent"
    citation_css = 'span[id^="cit"]'
    table_css = 'div[class^="rtable__wrapper"]'
    table_caption_css = ".table_caption"
    table_head_row_css = "table thead tr"
    table_body_row_css = "table tbody tr"
    table_footnote_css = "table tfoot tr th .sup_inf"
    reference_css = 'small sup a, a[href^="#cit"], a[href^="#fn"], a[href^="#tab"]'
    figure_css = ".image_table"
    figure_caption_css = ".graphic_title"
    figure_label_css = "td.image_title b"
    figure_download_link_css = "img::attr(src)"
    ignore_css = '.table_caption + table, .left_head, sup span.sup_ref, small sup a, a[href^="#fn"], .PMedLink'

    def _parse_table_footnotes(
        self, fns: list[HtmlElement], refs: dict[str, Any], specials: dict[str, Any]
    ) -> list[Footnote]:
        """Override to account for awkward RSC table footnotes.

        Args:
            fns: List of footnote elements
            refs: Reference mapping dictionary
            specials: Special elements mapping dictionary

        Returns:
            List of parsed Footnote objects
        """
        footnotes = []
        for fn in fns:
            footnote = self._parse_text(fn, refs=refs, specials=specials, element_cls=Footnote)[0]
            footnote += Footnote("", id=fn.getprevious().get("id"))
            footnotes.append(footnote)
        return footnotes

    def detect(self, fstring: str | bytes, fname: str | None = None) -> bool:
        """Detect RSC HTML documents.

        Args:
            fstring: Input data to check
            fname: Optional filename for format hints

        Returns:
            True if this appears to be an RSC HTML document
        """
        if fname and not (fname.endswith(".html") or fname.endswith(".htm")):
            return False
        return bool(
            b'meta name="citation_doi" content="10.1039' in fstring
            or b'meta content="Royal Society of Chemistry"' in fstring
        )

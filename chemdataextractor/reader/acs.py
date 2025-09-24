"""
Readers for documents from the ACS.

Provides specialized HTML reader for American Chemical Society (ACS) publications
with custom CSS selectors and cleaning rules.
"""

from __future__ import annotations

from ..scrape.clean import Cleaner
from ..scrape.clean import clean
from .markup import HtmlReader

#: Additional cleaner for ACS HTML  TODO: Move to ignore_css?
clean_acs_html = Cleaner(kill_xpath='.//ul[@class="anchors"] | .//div[@class="citationLinks"]')


class AcsHtmlReader(HtmlReader):
    """Reader for HTML documents from the ACS."""

    cleaners = [clean, clean_acs_html]

    root_css = "#articleMain, article"
    title_css = "h1.articleTitle"
    heading_css = "h2, h3, h4, h5, h6, .title1, span.title2, span.title3"
    table_css = ".NLM_table-wrap"
    table_caption_css = ".NLM_caption"
    table_footnote_css = ".footnote"
    figure_css = ".figure"
    figure_caption_css = ".caption"
    citation_css = ".reference"
    ignore_css = 'a[href="JavaScript:void(0);"], a.ref sup'

    def detect(self, fstring: str | bytes, fname: str | None = None) -> bool:
        """Detect ACS HTML documents.

        Args:
            fstring: Input data to check
            fname: Optional filename for format hints

        Returns:
            True if this appears to be an ACS HTML document
        """
        if fname and not (fname.endswith(".html") or fname.endswith(".htm")):
            return False
        return b'<meta name="dc.Identifier" scheme="doi" content="10.1021/' in fstring

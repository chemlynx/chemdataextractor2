"""
Readers for ChemSpider SyntheticPages.

Provides specialized HTML reader for ChemSpider SyntheticPages documents
with custom CSS selectors and table footnote processing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

from ..doc.text import Footnote
from .markup import HtmlReader

if TYPE_CHECKING:
    from lxml.html import HtmlElement

log = logging.getLogger(__name__)


class CsspHtmlReader(HtmlReader):
    """Reader for ChemSpider SyntheticPages HTML documents."""

    root_css = ".article-container"
    title_css = ".article-container > h2"
    heading_css = "h3, h4, h5, h6"
    citation_css = "#csm-article-part-lead_ref > p, #csm-article-part-other_refs > p"

    def _parse_table_footnotes(
        self, fns: list[HtmlElement], refs: dict[str, Any], specials: dict[str, Any]
    ) -> list[Footnote]:
        """Override to account for awkward CSSP table footnotes.

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
        """Detect ChemSpider SyntheticPages HTML documents.

        Args:
            fstring: Input data to check
            fname: Optional filename for format hints

        Returns:
            True if this appears to be a CSSP HTML document
        """
        if fname and not (fname.endswith(".html") or fname.endswith(".htm")):
            return False
        return b'meta name="DC.Publisher" content="ChemSpider SyntheticPages"' in fstring

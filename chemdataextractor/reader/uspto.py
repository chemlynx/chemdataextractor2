"""
Readers for USPTO patents.

Provides specialized XML reader for US Patent and Trademark Office (USPTO) patent
documents with comprehensive table parsing and cell handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from ..doc.table import Table
from ..doc.text import Caption
from ..doc.text import Cell
from ..doc.text import Footnote
from ..scrape.clean import clean
from .markup import XmlReader

if TYPE_CHECKING:
    from lxml.html import HtmlElement

# TODO: The below has only been tested with us-patent-grant-v42


class UsptoXmlReader(XmlReader):
    """Reader for USPTO XML documents."""

    cleaners = [clean]  # tidy_nlm_references, space_labels

    root_css = "us-patent-grant"  # TODO: Other roots
    title_css = "invention-title"
    heading_css = 'heading, p[id^="h-"]'
    table_css = "table"
    table_body_row_css = "table row"
    table_cell_css = "entry"
    # figure_css = 'img'
    reference_css = "claim-ref"
    # citation_css = 'ref-list ref'
    ignore_css = "us-bibliographic-data-grant *:not(invention-title)"

    inline_elements = {
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
        "xref",
        "underline",
        "italic",
        "bold",
        "inline-formula",
        "alternatives",
        "tex-math",
        "{http://www.w3.org/1998/math/mathml}math",
        "{http://www.w3.org/1998/math/mathml}msubsup",
        "{http://www.w3.org/1998/math/mathml}mrow",
        "{http://www.w3.org/1998/math/mathml}mo",
        "{http://www.w3.org/1998/math/mathml}mi",
        "{http://www.w3.org/1998/math/mathml}mn",
        "claim-ref",
        "figref",
    }

    def detect(self, fstring: str | bytes, fname: str | None = None) -> bool:
        """Detect USPTO XML patent documents.

        Args:
            fstring: Input data to check
            fname: Optional filename for format hints

        Returns:
            True if this appears to be a USPTO XML document
        """
        if fname and not fname.lower().endswith(".xml"):
            return False
        if b"us-patent-grant" in fstring:
            return True
        # TODO: Other DTDs
        return False

    def _parse_table(
        self, el: HtmlElement, refs: dict[str, Any], specials: dict[str, Any]
    ) -> list[Table]:
        """Parse USPTO table structure with complex cell handling.

        Args:
            el: Table element to parse
            refs: Reference mapping dictionary
            specials: Special elements mapping dictionary

        Returns:
            List containing single Table object
        """
        hdict: dict[int, dict[int, Cell]] = {}
        for row, tr in enumerate(self._css(self.table_body_row_css, el)):
            colnum = 0
            for td in self._css(self.table_cell_css, tr):
                cell = self._parse_text(td, refs=refs, specials=specials, element_cls=Cell)
                colspan = int(td.get("colspan", "1"))
                rowspan = int(td.get("rowspan", "1"))
                for i in range(colspan):
                    for j in range(rowspan):
                        rownum = row + j
                        if rownum not in hdict:
                            hdict[rownum] = {}
                        while colnum in hdict[rownum]:
                            colnum += 1
                        hdict[rownum][colnum] = cell[0] if len(cell) > 0 else Cell("")
                    colnum += 1
        potential_rows = []
        most_cols = 0
        for row in sorted(hdict):
            potential_rows.append([])
            most_cols = max(most_cols, len(hdict[row]))
            for col in sorted(hdict[row]):
                potential_rows[-1].append(hdict[row][col])
        hrows = []
        rows = []
        label = None
        caption = None
        footnotes = []
        for i, r in enumerate(potential_rows):
            # Skip empty rows
            if all(cell.text.strip() == "" for cell in r):
                continue
            # Top row label?
            if (
                len(rows) == 0
                and len(r) == 1
                and r[0].text.lower().startswith("table ")
                and not label
            ):
                label = r[0].text
                continue
            # Top row caption?
            if len(rows) == 0 and len(r) == 1 and r[0].text.strip() and not caption:
                caption = Caption(r[0].text)
                continue
            # Top row heading?
            if len(rows) == 0:
                # If any blank rows between here and 10th row of table, this is a heading
                max_heading_row = min(10, int(len(potential_rows) / 2))
                if i < max_heading_row:
                    hasblank = False
                    for nextrow in potential_rows[i + 1 : max_heading_row]:
                        if all(cell.text.strip() == "" for cell in nextrow):
                            hasblank = True
                    if hasblank:
                        hrows.append(r)
                        continue
            # Footnotes in final rows? (all remaining rows only have 1 cell)
            if all(len(frow) == 1 for frow in potential_rows[i:]):
                footnotes.append(Footnote(r[0].text))
                continue
            rows.append(r)
        for r in hrows:
            r.extend([Cell("")] * (len(max(hrows, key=len)) - len(r)))
        for r in rows:
            r.extend([Cell("")] * (len(max(rows, key=len)) - len(r)))
        rows = [r for r in rows if any(r)]

        tab = Table(
            label=label,
            caption=caption or Caption(""),
            headings=hrows,
            rows=rows,
            footnotes=footnotes,
            id=el.get("id", None),
        )
        return [tab]

    def _parse_table_rows(
        self, els: list[HtmlElement], refs: dict[str, Any], specials: dict[str, Any]
    ) -> list[list[Cell]]:
        """Parse table rows with cell spanning support.

        Args:
            els: List of table row elements
            refs: Reference mapping dictionary
            specials: Special elements mapping dictionary

        Returns:
            List of table rows, each containing Cell objects
        """
        hdict: dict[int, dict[int, Cell]] = {}
        for row, tr in enumerate(els):
            colnum = 0
            for td in self._css(self.table_cell_css, tr):
                cell = self._parse_text(td, refs=refs, specials=specials, element_cls=Cell)
                colspan = int(td.get("colspan", "1"))
                rowspan = int(td.get("rowspan", "1"))
                for _i in range(colspan):
                    for j in range(rowspan):
                        rownum = row + j
                        if rownum not in hdict:
                            hdict[rownum] = {}
                        while colnum in hdict[rownum]:
                            colnum += 1
                        hdict[rownum][colnum] = cell[0] if len(cell) > 0 else Cell("")
                    colnum += 1
        rows = []
        for row in sorted(hdict):
            rows.append([])
            for col in sorted(hdict[row]):
                rows[-1].append(hdict[row][col])
        for r in rows:
            r.extend([Cell("")] * (len(max(rows, key=len)) - len(r)))
        rows = [r for r in rows if any(r)]
        return rows

    def _parse_table_footnotes(
        self, fns: list[HtmlElement], refs: dict[str, Any], specials: dict[str, Any]
    ) -> list[Footnote]:
        """Parse table footnotes.

        Args:
            fns: List of footnote elements
            refs: Reference mapping dictionary
            specials: Special elements mapping dictionary

        Returns:
            List of Footnote objects
        """
        return [
            self._parse_text(fn, refs=refs, specials=specials, element_cls=Footnote)[0]
            for fn in fns
        ]

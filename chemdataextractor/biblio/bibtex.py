"""
BibTeX parser.

Provides comprehensive BibTeX parsing functionality to convert BibTeX data
into structured Python dictionaries or JSON format.
"""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from typing import TYPE_CHECKING
from typing import Any

from ..text.latex import latex_to_unicode

if TYPE_CHECKING:
    pass


class BibtexParser:
    """A class for parsing a BibTeX string into JSON or a python data structure.

    Example usage:

    .. code-block:: python

        with open(example.bib, 'r') as f:
            bib = BibtexParser(f.read())
            bib.parse()
            print bib.records_list
            print bib.json

    """

    def __init__(self, data: str, **kwargs: Any) -> None:
        """Initialize BibtexParser with data.

        Optional metadata passed as keyword arguments will be included in the JSON output.
        e.g. collection, label, description, id, owner, created, modified, source

        Example usage:

        .. code-block:: python

            bib = BibtexParser(data, created=unicode(datetime.utcnow()), owner='mcs07')

        """
        self.data: str = data
        self.meta: dict[str, Any] = kwargs
        self._token: str | None = None
        self.token_type: str | None = None
        self._tokens: Iterator[re.Match[str]] = re.compile(r'([^\s"\'#%@{}()=,]+|\s|"|\'|#|%|@|{|}|\(|\)|=|,)').finditer(
            self.data
        )
        self.mode: str | None = None
        self.definitions: dict[str, str] = {}
        self.records: OrderedDict[str, dict[str, Any]] = OrderedDict()

        # Key name normalizations
        self.keynorms = {
            "keyw": "keyword",
            "keywords": "keyword",
            "authors": "author",
            "editors": "editor",
            "url": "link",
            "urls": "link",
            "links": "link",
            "subjects": "subject",
        }

    def _next_token(self, skipws: bool = True) -> str:
        """Increment _token to the next token and return it."""
        self._token = next(self._tokens).group(0)
        return self._next_token() if skipws and self._token.isspace() else self._token

    def parse(self) -> None:
        """Parse self.data and store the parsed BibTeX to self.records."""
        while True:
            try:
                # TODO: If self._next_token() == '%' skip to newline?
                if self._next_token() == "@":
                    self._parse_entry()
            except StopIteration:
                break

    def _parse_entry(self) -> None:
        """Parse an entry."""
        entry_type = self._next_token().lower()
        if entry_type == "string":
            self._parse_string()
        elif entry_type not in ["comment", "preamble"]:
            self._parse_record(entry_type)

    def _parse_string(self) -> None:
        """Parse a string entry and store the definition."""
        if self._next_token() in ["{", "("]:
            field = self._parse_field()
            if field:
                self.definitions[field[0]] = field[1]

    def _parse_record(self, record_type: str) -> None:
        """Parse a record."""
        if self._next_token() in ["{", "("]:
            key = self._next_token()
            self.records[key] = {"id": key, "type": record_type.lower()}
            if self._next_token() == ",":
                while True:
                    field = self._parse_field()
                    if field:
                        k, v = field[0], field[1]
                        if k in self.keynorms:
                            k = self.keynorms[k]
                        if k == "pages":
                            v = v.replace(" ", "").replace("--", "-")
                        if k == "author" or k == "editor":
                            v = self.parse_names(v)
                        # Recapitalizing the title generally causes more problems than it solves
                        # elif k == 'title':
                        #     v = latex_to_unicode(v, capitalize='title')
                        else:
                            v = latex_to_unicode(v)
                        self.records[key][k] = v
                    if self._token != ",":
                        break

    def _parse_field(self) -> tuple[str, str] | None:
        """Parse a Field."""
        name = self._next_token()
        if self._next_token() == "=":
            value = self._parse_value()
            return name, value

    def _parse_value(self) -> str:
        """Parse a value. Digits, definitions, and the contents of double quotes or curly brackets."""
        val = []
        while True:
            t = self._next_token()
            if t == '"':
                brac_counter = 0
                while True:
                    t = self._next_token(skipws=False)
                    if t == "{":
                        brac_counter += 1
                    if t == "}":
                        brac_counter -= 1
                    if t == '"' and brac_counter <= 0:
                        break
                    else:
                        val.append(t)
            elif t == "{":
                brac_counter = 0
                while True:
                    t = self._next_token(skipws=False)
                    if t == "{":
                        brac_counter += 1
                    if t == "}":
                        brac_counter -= 1
                    if brac_counter < 0:
                        break
                    else:
                        val.append(t)
            elif re.match(r"\w", t):
                val.extend([self.definitions.get(t, t), " "])
            elif t.isdigit():
                val.append([t, " "])
            elif t == "#":
                pass
            else:
                break

        value = " ".join("".join(val).split())
        return value

    @classmethod
    def parse_names(cls, names: str) -> list[str]:
        """Parse a string of names separated by "and" like in a BibTeX authors field."""
        names = [latex_to_unicode(n) for n in re.split(r"\sand\s(?=[^{}]*(?:\{|$))", names) if n]
        return names

    @property
    def size(self) -> int:
        """Return the number of records parsed."""
        return len(self.records)

    @property
    def records_list(self) -> list[dict[str, Any]]:
        """Return the records as a list of dictionaries."""
        return list(self.records.values())

    @property
    def metadata(self) -> dict[str, Any]:
        """Return metadata for the parsed collection of records."""
        auto = {"records": self.size}
        auto.update(self.meta)
        return auto

    @property
    def json(self) -> str:
        """Return a list of records as a JSON string. Follows the BibJSON convention."""
        return json.dumps(
            OrderedDict([("metadata", self.metadata), ("records", self.records.values())])
        )


def parse_bibtex(data: str) -> list[dict[str, Any]]:
    """Parse BibTeX data and return a list of records.

    Args:
        data: BibTeX data string

    Returns:
        List of parsed bibliography record dictionaries
    """
    bib = BibtexParser(data)
    bib.parse()
    return bib.records_list


# TODO: Improvements to BibTexParser
# - Initialize with options, then pass text to .parse method to reuse an instance?
# - Initialize with a single entry, and have attributes that correspond to the bibtex fields?
# - Have a classmethod that takes text containing multiple entries, then returns a list of instances
# - Have a list wrapper class that allows serialization of all at once?

# TODO: BibtexWriter - write python dict or BibJSON to BibTeX

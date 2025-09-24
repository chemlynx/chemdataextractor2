"""
Parse metadata stored as XMP (Extensible Metadata Platform).

This is commonly embedded within PDF documents, and can be extracted using the PDFMiner framework.
Provides functionality to parse XMP metadata into structured Python dictionaries.

More information is available on the Adobe website:

    http://www.adobe.com/products/xmp/index.html
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING
from typing import Any

from lxml import etree

if TYPE_CHECKING:
    from lxml.etree import _Element

RDF_NS = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"
NS_MAP = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://ns.adobe.com/xap/1.0/": "xap",
    "http://ns.adobe.com/pdf/1.3/": "pdf",
    "http://ns.adobe.com/xap/1.0/mm/": "xapmm",
    "http://ns.adobe.com/pdfx/1.3/": "pdfx",
    "http://prismstandard.org/namespaces/basic/2.0/": "prism",
    "http://crossref.org/crossmark/1.0/": "crossmark",
    "http://ns.adobe.com/xap/1.0/rights/": "rights",
    "http://www.w3.org/XML/1998/namespace": "xml",
}


class XmpParser:
    """A parser that converts an XMP metadata string into a python dictionary.

    Usage::

        parser = XmpParser()
        metadata = parser.parse(xmpstring)

    Common namespaces are abbreviated in the output using the definitions in ``xmp.NS_MAP``. If an abbreviation for a
    namespace is not defined in ``NS_MAP``, the full URL is used as the key in the output dictionary. It is possible to
    override ``NS_MAP`` when initializing the parser::

        parser = XmpParser(ns_map={'http://www.w3.org/XML/1998/namespace': 'xml'})
        metadata = parser.parse(xmpstring)

    """

    def __init__(self, ns_map: dict[str, str] = NS_MAP) -> None:
        """Initialize XMP parser with namespace mappings.

        Args:
            ns_map: Dictionary mapping namespace URIs to abbreviations
        """
        self.ns_map: dict[str, str] = ns_map

    def parse(self, xmp: str | bytes) -> dict[str, dict[str, Any]]:
        """Run parser and return a dictionary of all the parsed metadata.

        Args:
            xmp: XMP metadata string or bytes

        Returns:
            Dictionary with namespace keys containing metadata dictionaries
        """
        tree = etree.fromstring(xmp)
        rdf_tree = tree.find(RDF_NS + "RDF")
        meta: defaultdict[str, dict[str, Any]] = defaultdict(dict)
        for desc in rdf_tree.findall(RDF_NS + "Description"):
            for el in desc.getchildren():
                ns, tag = self._parse_tag(el)
                value = self._parse_value(el)
                meta[ns][tag] = value
        return dict(meta)

    def _parse_tag(self, el: _Element) -> tuple[str | None, str]:
        """Extract the namespace and tag from an element.

        Args:
            el: XML element to parse

        Returns:
            Tuple of (namespace, tag_name)
        """
        ns: str | None = None
        tag = el.tag
        if tag[0] == "{":
            ns, tag = tag[1:].split("}", 1)
            if self.ns_map and ns in self.ns_map:
                ns = self.ns_map[ns]
        return ns, tag

    def _parse_value(self, el: _Element) -> Any:
        """Extract the metadata value from an element.

        Args:
            el: XML element to extract value from

        Returns:
            Parsed value (string, list, or dict depending on structure)
        """
        if el.find(RDF_NS + "Bag") is not None:
            value: list[str | None] = []
            for li in el.findall(RDF_NS + "Bag/" + RDF_NS + "li"):
                value.append(li.text)
        elif el.find(RDF_NS + "Seq") is not None:
            value = []
            for li in el.findall(RDF_NS + "Seq/" + RDF_NS + "li"):
                value.append(li.text)
        elif el.find(RDF_NS + "Alt") is not None:
            value_dict: dict[str | None, str | None] = {}
            for li in el.findall(RDF_NS + "Alt/" + RDF_NS + "li"):
                value_dict[li.get(XML_NS + "lang")] = li.text
            value = value_dict
        else:
            value = el.text
        return value


def parse_xmp(xmp: str | bytes) -> dict[str, dict[str, Any]]:
    """Shorthand function for parsing an XMP string into a python dictionary.

    Args:
        xmp: XMP metadata string or bytes

    Returns:
        Dictionary with namespace keys containing metadata dictionaries
    """
    return XmpParser().parse(xmp)

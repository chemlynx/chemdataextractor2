"""
Actions to perform during parsing.

Parse actions are functions that transform parsing results, typically
used to clean up, merge, or format extracted text data.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from lxml.builder import E
from lxml.etree import strip_tags

from ..text import HYPHENS

# Type aliases for parse actions
TokenList = list[str]  # List of tokens
ParseResult = list[Any]  # List of XML elements from parsing

log = logging.getLogger(__name__)


def flatten(tokens: TokenList, start: int, result: ParseResult) -> ParseResult:
    """Replace all child results with their text contents.
    
    Args:
        tokens: The original token list
        start: Starting position in tokens
        result: Parse result to flatten
        
    Returns:
        Flattened parse result
    """
    for e in result:
        strip_tags(e, "*")
    return result


def join(tokens: TokenList, start: int, result: ParseResult) -> ParseResult:
    """Join tokens into a single string with spaces between.
    
    Args:
        tokens: The original token list
        start: Starting position in tokens  
        result: Parse result to join
        
    Returns:
        Joined parse result as single element
    """
    texts = []
    if len(result) > 0:
        for e in result:
            for child in e.iter():
                if child.text is not None:
                    texts.append(child.text)
        return [E(result[0].tag, " ".join(texts))]


def merge(tokens, start, result):
    """Join tokens into a single string with no spaces."""
    texts = []
    if len(result) > 0:
        for e in result:
            for child in e.iter():
                if child.text is not None:
                    texts.append(child.text)
        return [E(result[0].tag, "".join(texts))]


def strip_stop(tokens, start, result):
    """Remove trailing full stop from tokens."""
    for e in result:
        for child in e.iter():
            if child.text.endswith("."):
                child.text = child.text[:-1]
    return result


def fix_whitespace(tokens, start, result):
    """Fix whitespace around hyphens and commas. Can be used to remove whitespace tokenization artefacts."""
    for e in result:
        for child in e.iter():
            # if check added by Juraj, it has to exist
            if child.text:
                child.text = child.text.replace(" , ", ", ")
                for hyphen in HYPHENS:
                    child.text = child.text.replace(" %s " % hyphen, "%s" % hyphen)
                child.text = re.sub(r"- (.) -", r"-\1-", child.text)
                child.text = child.text.replace(" -", "-")
                child.text = child.text.replace(" : ", ":").replace(" ) ", ")")

                child.text = child.text.replace(" ( ", "(").replace(" ) ", ")")
                child.text = child.text.replace(" / ", "/")
                child.text = child.text.replace(" [ ", "[").replace(" ] ", "]")
                child.text = child.text.replace("( ", "(").replace(" )", ")")
                child.text = child.text.replace("[ ", "[").replace(" ]", "]")
    return result

"""
Optimized trigger phrase processing for ChemDataExtractor2.

This module implements high-performance trigger phrase matching and parser selection
to achieve significant speedup in document parsing operations.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import TYPE_CHECKING
from typing import Any

from ..types import Final
from ..utils import memoize

if TYPE_CHECKING:
    from ..doc.element import BaseElement
    from .base import BaseParser

# Constants for optimization tuning
BLOOM_FILTER_SIZE: Final[int] = 10000
CACHE_SIZE: Final[int] = 1000
BATCH_SIZE: Final[int] = 50


class BloomFilter:
    """Simple bloom filter for ultra-fast negative lookups."""

    def __init__(self, size: int = BLOOM_FILTER_SIZE):
        self.size = size
        self.bit_array = [False] * size
        self.hash_count = 3

    def _hash(self, item: str, seed: int) -> int:
        """Generate hash for item with given seed."""
        return hash(item + str(seed)) % self.size

    def add(self, item: str) -> None:
        """Add item to bloom filter."""
        for i in range(self.hash_count):
            index = self._hash(item.lower(), i)
            self.bit_array[index] = True

    def might_contain(self, item: str) -> bool:
        """Check if item might be in the set (no false negatives)."""
        for i in range(self.hash_count):
            index = self._hash(item.lower(), i)
            if not self.bit_array[index]:
                return False
        return True


class TriggerPhraseIndex:
    """Pre-compiled index of all trigger phrases for fast lookup."""

    def __init__(self):
        self.phrase_to_parsers: dict[str, list[BaseParser]] = defaultdict(list)
        self.compiled_patterns: dict[str, re.Pattern[str]] = {}
        self.bloom_filter: BloomFilter = BloomFilter()
        self.simple_phrases: set[str] = set()
        self._compiled = False

    def add_parser(self, parser: BaseParser) -> None:
        """Add parser and its trigger phrases to the index."""
        if not hasattr(parser, "trigger_phrase") or parser.trigger_phrase is None:
            return

        # Extract trigger phrases from parser element
        phrases = self._extract_trigger_phrases(parser.trigger_phrase)

        # If no meaningful phrases extracted, use parser-specific heuristics
        if not phrases or all(p.lower() == "none" for p in phrases):
            phrases = self._get_heuristic_phrases(parser)

        for phrase in phrases:
            phrase_lower = phrase.lower().strip()
            if phrase_lower and phrase_lower != "none":
                self.phrase_to_parsers[phrase_lower].append(parser)
                self.bloom_filter.add(phrase_lower)

                # Categorize phrase type
                if self._is_simple_phrase(phrase_lower):
                    self.simple_phrases.add(phrase_lower)
                else:
                    # Compile regex for complex patterns
                    try:
                        pattern = re.compile(phrase_lower, re.IGNORECASE | re.MULTILINE)
                        self.compiled_patterns[phrase_lower] = pattern
                    except re.error:
                        # Fallback for malformed patterns
                        self.simple_phrases.add(phrase_lower)

    def _extract_trigger_phrases(self, trigger_element: Any) -> list[str]:
        """Extract string phrases from trigger element."""
        phrases = []

        # Handle different trigger element types
        if hasattr(trigger_element, "pattern"):
            # Regex element
            phrases.append(str(trigger_element.pattern))
        elif hasattr(trigger_element, "name"):
            # Word element
            phrases.append(str(trigger_element.name))
        elif hasattr(trigger_element, "exprs"):
            # Compound elements like And, Or - recursively extract from sub-expressions
            for expr in trigger_element.exprs:
                phrases.extend(self._extract_trigger_phrases(expr))
        elif hasattr(trigger_element, "expr"):
            # Elements with single expression like Optional, Hide
            phrases.extend(self._extract_trigger_phrases(trigger_element.expr))
        elif hasattr(trigger_element, "match"):
            # Word elements - extract the string to match
            match_str = str(trigger_element.match)
            if match_str and len(match_str) > 1:
                phrases.append(match_str.strip("\"'"))
        else:
            # Try to get string representation and extract meaningful phrases
            phrase_str = str(trigger_element)
            if phrase_str and phrase_str.lower() != "none":
                # Clean up common parser element artifacts
                cleaned = re.sub(r"[<>{}()\[\]|*+?^$\\]", " ", phrase_str)
                words = [
                    w.strip() for w in cleaned.split() if len(w.strip()) > 2 and not w.isdigit()
                ]
                # Filter out class names and common artifacts
                filtered_words = [
                    w
                    for w in words
                    if not any(
                        artifact in w.lower()
                        for artifact in [
                            "chemdataextractor",
                            "parse",
                            "elements",
                            "object",
                            "class",
                            "at",
                            "0x",
                            "and",
                            "or",
                            "not",
                            "optional",
                        ]
                    )
                ]
                phrases.extend(filtered_words)

        return phrases

    def _get_heuristic_phrases(self, parser: BaseParser) -> list[str]:
        """Get heuristic trigger phrases based on parser type."""
        parser_name = parser.__class__.__name__.lower()

        # Parser-specific heuristics
        if "mp" in parser_name or "melting" in parser_name:
            return ["melting", "point", "mp", "m.p", "m.pt", "melt"]
        elif "tg" in parser_name or "glass" in parser_name:
            return ["glass", "transition", "tg", "glass transition"]
        elif "ir" in parser_name:
            return ["ir", "infrared", "spectrum", "cm-1"]
        elif "nmr" in parser_name:
            return ["nmr", "nuclear", "magnetic", "resonance", "ppm", "chemical shift"]
        elif "uvvis" in parser_name:
            return ["uv", "vis", "ultraviolet", "visible", "absorption", "nm"]

        # Default fallback
        return [parser_name.replace("parser", "").strip()]

    def _is_simple_phrase(self, phrase: str) -> bool:
        """Check if phrase is a simple string (not regex)."""
        # Simple heuristic - contains regex metacharacters
        regex_chars = set(".*+?^${}[]|()")
        return not any(char in phrase for char in regex_chars)

    def get_candidate_parsers(self, text: str) -> set[BaseParser]:
        """Get parsers whose trigger phrases match the text."""
        if not self._compiled:
            self.compile()

        text_lower = text.lower()
        candidates: set[BaseParser] = set()

        # Fast string search for simple phrases
        for phrase in self.simple_phrases:
            if self.bloom_filter.might_contain(phrase) and phrase in text_lower:
                candidates.update(self.phrase_to_parsers[phrase])

        # Regex search for complex patterns
        for phrase, pattern in self.compiled_patterns.items():
            if self.bloom_filter.might_contain(phrase) and pattern.search(text_lower):
                candidates.update(self.phrase_to_parsers[phrase])

        return candidates

    def compile(self) -> None:
        """Finalize compilation of the index."""
        self._compiled = True

    def get_stats(self) -> dict[str, Any]:
        """Get index statistics for debugging."""
        return {
            "total_phrases": len(self.phrase_to_parsers),
            "simple_phrases": len(self.simple_phrases),
            "regex_phrases": len(self.compiled_patterns),
            "total_parsers": len(
                {parser for parsers in self.phrase_to_parsers.values() for parser in parsers}
            ),
            "compiled": self._compiled,
        }


class FastTriggerMatcher:
    """Ultra-fast string-based trigger phrase matching using optimized algorithms."""

    def __init__(self):
        self.trigger_index = TriggerPhraseIndex()
        self.sentence_cache: dict[str, set[BaseParser]] = {}

    @memoize
    def _hash_tokens(self, tokens: tuple[str, ...]) -> str:
        """Create hash key for token sequence."""
        # Handle both string tokens and RichToken objects
        token_strings = []
        for token in tokens:
            if hasattr(token, "text"):
                token_strings.append(str(token.text))
            else:
                token_strings.append(str(token))

        text = " ".join(token_strings).lower()
        return hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()[:16]

    def add_parser(self, parser: BaseParser) -> None:
        """Add parser to the matching system."""
        self.trigger_index.add_parser(parser)

    def find_matching_parsers(self, tokens: list[str]) -> set[BaseParser]:
        """Find all parsers with matching trigger phrases."""
        # Create cache key
        tokens_tuple = tuple(tokens)
        cache_key = self._hash_tokens(tokens_tuple)

        # Check cache first
        if cache_key in self.sentence_cache:
            return self.sentence_cache[cache_key]

        # Convert tokens to text, handling RichToken objects
        token_strings = []
        for token in tokens:
            if hasattr(token, "text"):
                token_strings.append(str(token.text))
            else:
                token_strings.append(str(token))

        text = " ".join(token_strings)
        matches = self.trigger_index.get_candidate_parsers(text)

        # Cache result (with size limit)
        if len(self.sentence_cache) < CACHE_SIZE:
            self.sentence_cache[cache_key] = matches

        return matches

    def compile_triggers(self, parsers: list[BaseParser]) -> None:
        """Compile all parser triggers for optimized matching."""
        for parser in parsers:
            self.add_parser(parser)
        self.trigger_index.compile()

    def clear_cache(self) -> None:
        """Clear the sentence matching cache."""
        self.sentence_cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get matcher statistics."""
        stats = self.trigger_index.get_stats()
        stats.update(
            {
                "cache_size": len(self.sentence_cache),
                "cache_hit_ratio": len(self.sentence_cache) / max(1, len(self.sentence_cache)),
            }
        )
        return stats


class BatchTriggerProcessor:
    """Process multiple sentences in batches for better cache locality."""

    def __init__(self, trigger_matcher: FastTriggerMatcher):
        self.trigger_matcher = trigger_matcher
        self.batch_cache: dict[str, dict[str, set[BaseParser]]] = {}

    def process_sentences_batch(self, sentences: list[BaseElement]) -> dict[str, set[BaseParser]]:
        """Process multiple sentences at once for better performance."""

        # Group sentences by similar token patterns for deduplication
        sentence_groups = self._group_sentences_by_similarity(sentences)
        results: dict[str, set[BaseParser]] = {}

        for group_key, sentence_group in sentence_groups.items():
            # Check batch cache
            if group_key in self.batch_cache:
                cached_results = self.batch_cache[group_key]
                for sentence in sentence_group:
                    sentence_key = str(id(sentence))
                    if sentence_key in cached_results:
                        results[sentence_key] = cached_results[sentence_key]
                        continue

            # Process uncached sentences
            group_results = {}
            for sentence in sentence_group:
                sentence_key = str(id(sentence))
                if sentence_key not in results:
                    matches = self.trigger_matcher.find_matching_parsers(sentence.tokens)
                    results[sentence_key] = matches
                    group_results[sentence_key] = matches

            # Cache group results
            self.batch_cache[group_key] = group_results

            # Limit cache size
            if len(self.batch_cache) > 100:
                # Remove oldest entry
                oldest_key = next(iter(self.batch_cache))
                del self.batch_cache[oldest_key]

        return results

    def _group_sentences_by_similarity(
        self, sentences: list[BaseElement]
    ) -> dict[str, list[BaseElement]]:
        """Group sentences by token similarity for batch processing."""

        groups: dict[str, list[BaseElement]] = defaultdict(list)

        for sentence in sentences:
            # Create similarity key based on sentence length and first/last tokens
            if sentence.tokens:
                # Handle RichToken objects
                first_token_text = (
                    sentence.tokens[0].text
                    if hasattr(sentence.tokens[0], "text")
                    else str(sentence.tokens[0])
                )
                last_token_text = (
                    sentence.tokens[-1].text
                    if hasattr(sentence.tokens[-1], "text")
                    else str(sentence.tokens[-1])
                )

                first_token = first_token_text.lower()
                last_token = last_token_text.lower() if len(sentence.tokens) > 1 else ""
                token_count = len(sentence.tokens)

                group_key = f"{token_count}_{first_token[:3]}_{last_token[:3]}"
                groups[group_key].append(sentence)
            else:
                groups["empty"].append(sentence)

        return groups

    def clear_cache(self) -> None:
        """Clear the batch processing cache."""
        self.batch_cache.clear()


class TriggerResultPool:
    """Object pool to reduce memory allocation overhead."""

    def __init__(self, max_pool_size: int = 100):
        self.result_lists: list[list[Any]] = []
        self.parser_sets: list[set[BaseParser]] = []
        self.max_pool_size = max_pool_size

    def get_result_list(self) -> list[Any]:
        """Get reusable result list from pool."""
        if self.result_lists:
            return self.result_lists.pop()
        return []

    def return_result_list(self, result_list: list[Any]) -> None:
        """Return list to pool after clearing."""
        result_list.clear()
        if len(self.result_lists) < self.max_pool_size:
            self.result_lists.append(result_list)

    def get_parser_set(self) -> set[BaseParser]:
        """Get reusable parser set from pool."""
        if self.parser_sets:
            return self.parser_sets.pop()
        return set()

    def return_parser_set(self, parser_set: set[BaseParser]) -> None:
        """Return set to pool after clearing."""
        parser_set.clear()
        if len(self.parser_sets) < self.max_pool_size:
            self.parser_sets.append(parser_set)

    def get_stats(self) -> dict[str, Any]:
        """Get pool statistics."""
        return {
            "available_lists": len(self.result_lists),
            "available_sets": len(self.parser_sets),
            "max_pool_size": self.max_pool_size,
        }

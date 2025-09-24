"""
Integrated Trigger Processing Engine for ChemDataExtractor2.

This module provides the main TriggerEngine class that integrates all optimization
components for maximum performance in parser trigger phrase processing.
"""

from __future__ import annotations

import time
from typing import Any
from typing import ClassVar
from typing import TYPE_CHECKING

from .optimized_triggers import (
    BatchTriggerProcessor,
    FastTriggerMatcher,
    TriggerResultPool,
)

if TYPE_CHECKING:
    from .base import BaseParser
    from ..doc.element import BaseElement


class TriggerEngine:
    """High-performance integrated trigger processing engine."""

    _global_instance: ClassVar[TriggerEngine | None] = None
    _parser_registry: ClassVar[list[BaseParser]] = []

    def __init__(self):
        # Core components
        self.trigger_matcher = FastTriggerMatcher()
        self.batch_processor = BatchTriggerProcessor(self.trigger_matcher)
        self.result_pool = TriggerResultPool()

        # Performance tracking
        self.stats = {
            "total_lookups": 0,
            "cache_hits": 0,
            "batch_processes": 0,
            "total_time": 0.0,
            "compilation_time": 0.0
        }

        self._compiled = False
        self._parsers_added = 0

    @classmethod
    def get_global_instance(cls) -> TriggerEngine:
        """Get or create the global trigger engine instance."""
        if cls._global_instance is None:
            cls._global_instance = cls()
        return cls._global_instance

    @classmethod
    def register_parser(cls, parser: BaseParser) -> None:
        """Register a parser with the global trigger engine."""
        cls._parser_registry.append(parser)
        instance = cls.get_global_instance()
        instance.add_parser(parser)

    def add_parser(self, parser: BaseParser) -> None:
        """Add a parser to the engine."""
        self.trigger_matcher.add_parser(parser)
        self._parsers_added += 1

        # Auto-compile after adding multiple parsers
        if self._parsers_added % 10 == 0:
            self.compile_triggers()

    def compile_triggers(self) -> None:
        """Compile all trigger patterns for optimized matching."""
        if self._compiled:
            return

        start_time = time.perf_counter()

        # Compile the trigger matcher
        self.trigger_matcher.compile_triggers(self._parser_registry)

        self.stats["compilation_time"] = time.perf_counter() - start_time
        self._compiled = True

    def should_parse(self, parser: BaseParser, tokens: list[str]) -> bool:
        """Fast check if parser should be applied to tokens."""
        start_time = time.perf_counter()

        # If no trigger phrase, always parse
        if not hasattr(parser, 'trigger_phrase') or parser.trigger_phrase is None:
            return True

        # Find matching parsers
        matching_parsers = self.trigger_matcher.find_matching_parsers(tokens)

        # Update stats
        self.stats["total_lookups"] += 1
        self.stats["total_time"] += time.perf_counter() - start_time

        return parser in matching_parsers

    def process_sentences_batch(
        self,
        sentences: list[BaseElement],
        target_parsers: list[BaseParser] | None = None
    ) -> dict[str, set[BaseParser]]:
        """Process multiple sentences efficiently in batch."""

        if not self._compiled:
            self.compile_triggers()

        start_time = time.perf_counter()

        # Use batch processor for efficiency
        results = self.batch_processor.process_sentences_batch(sentences)

        # Filter by target parsers if specified
        if target_parsers is not None:
            target_set = set(target_parsers)
            for sentence_key in results:
                results[sentence_key] &= target_set

        # Update stats
        self.stats["batch_processes"] += 1
        self.stats["total_time"] += time.perf_counter() - start_time

        return results

    def get_parser_suggestions(
        self,
        text: str,
        limit: int = 5
    ) -> list[tuple[BaseParser, float]]:
        """Get suggested parsers for text with confidence scores."""

        if not self._compiled:
            self.compile_triggers()

        # Get all matching parsers
        tokens = text.split()  # Simple tokenization
        matching_parsers = self.trigger_matcher.find_matching_parsers(tokens)

        # Score parsers by trigger phrase relevance
        scored_parsers = []
        for parser in matching_parsers:
            score = self._calculate_parser_score(parser, text)
            scored_parsers.append((parser, score))

        # Sort by score and return top suggestions
        scored_parsers.sort(key=lambda x: x[1], reverse=True)
        return scored_parsers[:limit]

    def _calculate_parser_score(self, parser: BaseParser, text: str) -> float:
        """Calculate relevance score for parser and text."""

        if not hasattr(parser, 'trigger_phrase') or parser.trigger_phrase is None:
            return 0.5  # Default score for parsers without triggers

        # Simple scoring based on trigger phrase match quality
        text_lower = text.lower()

        # Extract trigger phrases
        phrases = self.trigger_matcher.trigger_index._extract_trigger_phrases(
            parser.trigger_phrase
        )

        max_score = 0.0
        for phrase in phrases:
            phrase_lower = phrase.lower()
            if phrase_lower in text_lower:
                # Score based on phrase length and position
                phrase_score = len(phrase_lower) / len(text_lower)
                max_score = max(max_score, phrase_score)

        return max_score

    def optimize_for_document_type(self, document_type: str) -> None:
        """Optimize engine for specific document types."""

        # Clear caches to start fresh
        self.clear_caches()

        # Document-specific optimizations
        if document_type == "chemical_paper":
            # Increase cache sizes for chemistry-heavy documents
            self.result_pool = TriggerResultPool(max_pool_size=200)
        elif document_type == "patent":
            # Patents have repetitive structure - optimize for batching
            pass  # Current batch processing is already optimized
        elif document_type == "short_text":
            # Reduce cache sizes for memory efficiency
            self.result_pool = TriggerResultPool(max_pool_size=50)

    def clear_caches(self) -> None:
        """Clear all internal caches."""
        self.trigger_matcher.clear_cache()
        self.batch_processor.clear_cache()
        self.stats["cache_hits"] = 0

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics."""

        # Get component stats
        matcher_stats = self.trigger_matcher.get_stats()
        pool_stats = self.result_pool.get_stats()

        # Combine with engine stats
        combined_stats = {
            "engine": self.stats,
            "trigger_matcher": matcher_stats,
            "result_pool": pool_stats,
            "compiled": self._compiled,
            "parsers_registered": len(self._parser_registry),
            "average_lookup_time_ms": (
                self.stats["total_time"] / max(1, self.stats["total_lookups"]) * 1000
            )
        }

        return combined_stats

    def benchmark_performance(self, test_sentences: list[str]) -> dict[str, Any]:
        """Benchmark engine performance with test data."""

        if not self._compiled:
            self.compile_triggers()

        # Create mock sentence objects for testing
        class MockSentence:
            def __init__(self, text: str):
                self.tokens = text.split()

        mock_sentences = [MockSentence(text) for text in test_sentences]

        # Benchmark individual lookups
        start_time = time.perf_counter()
        individual_results = 0
        for sentence in mock_sentences:
            matches = self.trigger_matcher.find_matching_parsers(sentence.tokens)
            individual_results += len(matches)
        individual_time = time.perf_counter() - start_time

        # Benchmark batch processing
        start_time = time.perf_counter()
        batch_results = self.process_sentences_batch(mock_sentences)
        batch_time = time.perf_counter() - start_time

        return {
            "test_sentences": len(test_sentences),
            "individual_processing": {
                "time_seconds": individual_time,
                "sentences_per_second": len(test_sentences) / max(individual_time, 0.001),
                "total_matches": individual_results
            },
            "batch_processing": {
                "time_seconds": batch_time,
                "sentences_per_second": len(test_sentences) / max(batch_time, 0.001),
                "speedup_factor": individual_time / max(batch_time, 0.001),
                "total_results": len(batch_results)
            }
        }
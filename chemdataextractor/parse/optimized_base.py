"""
Optimized Base Parser with High-Performance Trigger Processing.

This module provides OptimizedBaseParser classes that integrate with the
TriggerEngine for significant performance improvements in parsing operations.
"""

from __future__ import annotations

from typing import Any
from typing import ClassVar
from typing import Iterator
from typing import TYPE_CHECKING

from .base import BaseParser, BaseSentenceParser, BaseTableParser
from .trigger_engine import TriggerEngine

if TYPE_CHECKING:
    from ..doc.element import BaseElement
    from ..model.base import BaseModel


class OptimizedBaseParser(BaseParser):
    """Base parser with optimized trigger phrase processing."""

    _global_trigger_engine: ClassVar[TriggerEngine | None] = None
    _optimization_enabled: ClassVar[bool] = True

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        # Register with global trigger engine
        if self._optimization_enabled:
            if self.__class__._global_trigger_engine is None:
                self.__class__._global_trigger_engine = TriggerEngine.get_global_instance()

            TriggerEngine.register_parser(self)

    @classmethod
    def enable_optimization(cls, enabled: bool = True) -> None:
        """Enable or disable trigger optimization globally."""
        cls._optimization_enabled = enabled

    @classmethod
    def compile_all_triggers(cls) -> None:
        """Compile all parser triggers into optimized engine."""
        if cls._global_trigger_engine:
            cls._global_trigger_engine.compile_triggers()

    @classmethod
    def get_engine_stats(cls) -> dict[str, Any]:
        """Get trigger engine performance statistics."""
        if cls._global_trigger_engine:
            return cls._global_trigger_engine.get_performance_stats()
        return {}

    @classmethod
    def benchmark_trigger_performance(cls, test_sentences: list[str]) -> dict[str, Any]:
        """Benchmark trigger processing performance."""
        if cls._global_trigger_engine:
            return cls._global_trigger_engine.benchmark_performance(test_sentences)
        return {}

    @classmethod
    def optimize_for_document_type(cls, document_type: str) -> None:
        """Optimize trigger engine for specific document types."""
        if cls._global_trigger_engine:
            cls._global_trigger_engine.optimize_for_document_type(document_type)

    def should_parse_sentence(self, sentence: BaseElement) -> bool:
        """Fast check if this parser should process the sentence."""

        if not self._optimization_enabled or self._global_trigger_engine is None:
            # Fallback to original trigger phrase logic
            return self._original_trigger_check(sentence)

        # Use optimized trigger engine
        return self._global_trigger_engine.should_parse(self, sentence.tokens)

    def _original_trigger_check(self, sentence: BaseElement) -> bool:
        """Original trigger phrase checking logic (fallback)."""
        if self.trigger_phrase is not None:
            trigger_phrase_results = [
                result for result in self.trigger_phrase.scan(sentence.tokens)
            ]
            return bool(trigger_phrase_results)
        return True  # No trigger phrase means always parse


class OptimizedSentenceParser(OptimizedBaseParser, BaseSentenceParser):
    """Sentence parser with optimized trigger processing."""

    def parse_sentence(self, sentence: BaseElement) -> Iterator[BaseModel]:
        """Parse sentence with optimized trigger checking."""

        # Fast trigger pre-filter
        if not self.should_parse_sentence(sentence):
            return

        # Original parsing logic
        for result in self.root.scan(sentence.tokens):
            yield from self.interpret(*result)


class OptimizedTableParser(OptimizedBaseParser, BaseTableParser):
    """Table parser with optimized trigger processing."""

    def parse_cell(self, cell: BaseElement) -> Iterator[BaseModel]:
        """Parse table cell with optimized trigger checking."""

        # Fast trigger pre-filter for table cells
        if self.trigger_phrase is not None:
            if not self._global_trigger_engine or not self._optimization_enabled:
                # Fallback to original logic
                trigger_phrase_results = [
                    result for result in self.trigger_phrase.scan(cell.tokens)
                ]
                if not trigger_phrase_results:
                    return
            else:
                # Use optimized checking
                if not self._global_trigger_engine.should_parse(self, cell.tokens):
                    return

        # Original parsing logic
        for result in self.root.scan(cell.tokens):
            yield from self.interpret(*result)


class BatchOptimizedParser:
    """Helper class for batch processing multiple sentences efficiently."""

    def __init__(self, parsers: list[OptimizedBaseParser]):
        self.parsers = parsers
        self.trigger_engine = TriggerEngine.get_global_instance()

    def parse_sentences_batch(
        self,
        sentences: list[BaseElement]
    ) -> dict[str, dict[str, list[BaseModel]]]:
        """Parse multiple sentences in batch for maximum efficiency."""

        # Get parser assignments for all sentences at once
        parser_assignments = self.trigger_engine.process_sentences_batch(
            sentences, self.parsers
        )

        results: dict[str, dict[str, list[BaseModel]]] = {}

        # Process each sentence with its assigned parsers
        for sentence in sentences:
            sentence_key = str(id(sentence))
            sentence_results: dict[str, list[BaseModel]] = {}

            if sentence_key in parser_assignments:
                matching_parsers = parser_assignments[sentence_key]

                for parser in matching_parsers:
                    parser_name = parser.__class__.__name__
                    parser_results = list(parser.parse_sentence(sentence))
                    if parser_results:
                        sentence_results[parser_name] = parser_results

            results[sentence_key] = sentence_results

        return results


# Backwards compatibility aliases
class FastBaseParser(OptimizedBaseParser):
    """Alias for OptimizedBaseParser for backwards compatibility."""
    pass


class FastSentenceParser(OptimizedSentenceParser):
    """Alias for OptimizedSentenceParser for backwards compatibility."""
    pass


class FastTableParser(OptimizedTableParser):
    """Alias for OptimizedTableParser for backwards compatibility."""
    pass


def create_optimized_parser_class(original_parser_class: type[BaseParser]) -> type[OptimizedBaseParser]:
    """Create an optimized version of an existing parser class."""

    class OptimizedWrapper(OptimizedSentenceParser):
        """Dynamically created optimized wrapper."""

        # Copy class attributes from original
        root = getattr(original_parser_class, 'root', None)
        trigger_phrase = getattr(original_parser_class, 'trigger_phrase', None)
        model = getattr(original_parser_class, 'model', None)

        def interpret(self, *args, **kwargs):
            """Delegate to original parser's interpret method."""
            # Create temporary instance of original class to call interpret
            original_instance = original_parser_class()
            return original_instance.interpret(*args, **kwargs)

    # Set appropriate class name
    OptimizedWrapper.__name__ = f"Optimized{original_parser_class.__name__}"
    OptimizedWrapper.__qualname__ = f"Optimized{original_parser_class.__qualname__}"

    return OptimizedWrapper


# Performance monitoring utilities
class TriggerPerformanceMonitor:
    """Monitor and report trigger processing performance."""

    def __init__(self):
        self.reset_stats()

    def reset_stats(self) -> None:
        """Reset performance statistics."""
        self.stats = {
            "sentences_processed": 0,
            "trigger_checks": 0,
            "cache_hits": 0,
            "total_processing_time": 0.0,
            "average_sentence_time": 0.0
        }

    def record_sentence_processing(self, processing_time: float) -> None:
        """Record time taken to process a sentence."""
        self.stats["sentences_processed"] += 1
        self.stats["total_processing_time"] += processing_time
        self.stats["average_sentence_time"] = (
            self.stats["total_processing_time"] / self.stats["sentences_processed"]
        )

    def record_trigger_check(self, cache_hit: bool = False) -> None:
        """Record a trigger phrase check."""
        self.stats["trigger_checks"] += 1
        if cache_hit:
            self.stats["cache_hits"] += 1

    def get_performance_report(self) -> dict[str, Any]:
        """Get comprehensive performance report."""
        cache_hit_rate = (
            self.stats["cache_hits"] / max(1, self.stats["trigger_checks"])
        )

        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "sentences_per_second": (
                self.stats["sentences_processed"] / max(0.001, self.stats["total_processing_time"])
            )
        }


# Global performance monitor instance
performance_monitor = TriggerPerformanceMonitor()
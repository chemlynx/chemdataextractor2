#!/usr/bin/env python
"""
Validate Optimized Trigger System Performance

Compares the performance of the original trigger mechanism against
the new optimized system to verify 2x speedup target is achieved.
"""

from __future__ import annotations

import json
import time
import statistics
from typing import Any

from chemdataextractor.doc import Document
from chemdataextractor.parse.mp_new import MpParser
from chemdataextractor.parse.optimized_base import OptimizedSentenceParser, TriggerPerformanceMonitor
from chemdataextractor.parse.trigger_engine import TriggerEngine


def create_validation_documents() -> list[Document]:
    """Create comprehensive test documents for validation."""

    test_texts = [
        # Melting point examples
        "The melting point of the compound is 125°C under standard conditions.",
        "This material exhibits a melting point of 250-260°C when measured at atmospheric pressure.",
        "Compound 1 has mp 150°C while compound 2 shows a melting temperature of 300°C.",
        "The crystalline solid melts at 180°C with decomposition occurring at higher temperatures.",

        # Non-matching examples (should be filtered out quickly)
        "The molecular weight was determined by mass spectrometry.",
        "UV-Vis spectroscopy revealed absorption maxima at 350 nm and 450 nm.",
        "The reaction proceeded smoothly at room temperature for 2 hours.",
        "NMR analysis confirmed the structure of the synthesized compound.",

        # Complex melting point examples
        "DSC analysis revealed an endothermic peak at 220°C corresponding to the melting point.",
        "The crude product melted at 140-145°C after recrystallization from ethanol.",
        "Melting points were determined using a Kofler hot stage microscope: 165-167°C.",
        "No melting behavior was observed up to 400°C during thermal analysis.",
    ]

    documents = []
    for text in test_texts:
        # Create multiple copies to get statistically significant results
        for _ in range(25):  # 300 total documents
            documents.append(Document(text))

    return documents


class OptimizedMpParser(OptimizedSentenceParser):
    """Optimized version of MpParser for testing."""

    def __init__(self):
        super().__init__()
        # Get original parser attributes
        original = MpParser()
        # Use dynamic wrapper approach since properties are read-only
        self._original_parser = original

    @property
    def root(self):
        return self._original_parser.root

    @property
    def trigger_phrase(self):
        return self._original_parser.trigger_phrase

    @property
    def model(self):
        return self._original_parser.model

    def interpret(self, *args, **kwargs):
        """Delegate to original parser's interpret method."""
        return self._original_parser.interpret(*args, **kwargs)


def benchmark_original_system(documents: list[Document]) -> dict[str, Any]:
    """Benchmark the original trigger phrase system."""

    print("🔍 Benchmarking Original System...")

    parser = MpParser()
    trigger_times = []
    parse_times = []
    total_sentences = 0
    sentences_with_triggers = 0

    # Warm-up
    for doc in documents[:10]:
        for sentence in doc.sentences:
            list(parser.parse_sentence(sentence))

    start_time = time.perf_counter()

    for doc in documents:
        for sentence in doc.sentences:
            total_sentences += 1

            # Time trigger checking
            trigger_start = time.perf_counter()
            trigger_results = []
            if parser.trigger_phrase is not None:
                trigger_results = [
                    result for result in parser.trigger_phrase.scan(sentence.tokens)
                ]
            trigger_end = time.perf_counter()
            trigger_times.append(trigger_end - trigger_start)

            # Time full parsing if trigger matches
            if not parser.trigger_phrase or trigger_results:
                sentences_with_triggers += 1
                parse_start = time.perf_counter()
                list(parser.parse_sentence(sentence))
                parse_end = time.perf_counter()
                parse_times.append(parse_end - parse_start)

    total_time = time.perf_counter() - start_time

    return {
        "total_sentences": total_sentences,
        "sentences_with_triggers": sentences_with_triggers,
        "total_time_seconds": total_time,
        "average_trigger_time_ms": statistics.mean(trigger_times) * 1000,
        "median_trigger_time_ms": statistics.median(trigger_times) * 1000,
        "trigger_time_stddev_ms": statistics.stdev(trigger_times) * 1000 if len(trigger_times) > 1 else 0,
        "average_parse_time_ms": statistics.mean(parse_times) * 1000 if parse_times else 0,
        "sentences_per_second": total_sentences / total_time,
        "trigger_hit_rate": sentences_with_triggers / total_sentences if total_sentences > 0 else 0
    }


def benchmark_optimized_system(documents: list[Document]) -> dict[str, Any]:
    """Benchmark the optimized trigger system."""

    print("⚡ Benchmarking Optimized System...")

    # Reset global engine
    TriggerEngine._global_instance = None
    TriggerEngine._parser_registry = []

    parser = OptimizedMpParser()

    # Force compilation
    OptimizedMpParser.compile_all_triggers()

    trigger_times = []
    parse_times = []
    total_sentences = 0
    sentences_with_triggers = 0

    # Warm-up
    for doc in documents[:10]:
        for sentence in doc.sentences:
            list(parser.parse_sentence(sentence))

    start_time = time.perf_counter()

    for doc in documents:
        for sentence in doc.sentences:
            total_sentences += 1

            # Time optimized trigger checking
            trigger_start = time.perf_counter()
            should_parse = parser.should_parse_sentence(sentence)
            trigger_end = time.perf_counter()
            trigger_times.append(trigger_end - trigger_start)

            # Time full parsing if trigger matches
            if should_parse:
                sentences_with_triggers += 1
                parse_start = time.perf_counter()
                list(parser.parse_sentence(sentence))
                parse_end = time.perf_counter()
                parse_times.append(parse_end - parse_start)

    total_time = time.perf_counter() - start_time

    # Get engine statistics
    engine_stats = OptimizedMpParser.get_engine_stats()

    return {
        "total_sentences": total_sentences,
        "sentences_with_triggers": sentences_with_triggers,
        "total_time_seconds": total_time,
        "average_trigger_time_ms": statistics.mean(trigger_times) * 1000,
        "median_trigger_time_ms": statistics.median(trigger_times) * 1000,
        "trigger_time_stddev_ms": statistics.stdev(trigger_times) * 1000 if len(trigger_times) > 1 else 0,
        "average_parse_time_ms": statistics.mean(parse_times) * 1000 if parse_times else 0,
        "sentences_per_second": total_sentences / total_time,
        "trigger_hit_rate": sentences_with_triggers / total_sentences if total_sentences > 0 else 0,
        "engine_stats": engine_stats
    }


def run_batch_processing_benchmark(documents: list[Document]) -> dict[str, Any]:
    """Benchmark the batch processing capabilities."""

    print("📦 Benchmarking Batch Processing...")

    # Reset and setup
    TriggerEngine._global_instance = None
    TriggerEngine._parser_registry = []

    parser = OptimizedMpParser()
    OptimizedMpParser.compile_all_triggers()

    # Collect all sentences
    all_sentences = []
    for doc in documents:
        all_sentences.extend(doc.sentences)

    # Benchmark batch processing
    start_time = time.perf_counter()

    from chemdataextractor.parse.optimized_base import BatchOptimizedParser
    batch_parser = BatchOptimizedParser([parser])
    results = batch_parser.parse_sentences_batch(all_sentences)

    batch_time = time.perf_counter() - start_time

    # Count successful extractions
    total_extractions = 0
    for sentence_results in results.values():
        for parser_results in sentence_results.values():
            total_extractions += len(parser_results)

    return {
        "total_sentences": len(all_sentences),
        "batch_processing_time": batch_time,
        "sentences_per_second": len(all_sentences) / batch_time,
        "total_extractions": total_extractions,
        "extractions_per_second": total_extractions / batch_time if batch_time > 0 else 0
    }


def main():
    """Run comprehensive validation of trigger optimization."""

    print("🚀 Trigger Optimization Validation")
    print("=" * 50)

    # Create test documents
    documents = create_validation_documents()
    print(f"📄 Testing with {len(documents)} documents")

    # Run benchmarks
    original_results = benchmark_original_system(documents)
    optimized_results = benchmark_optimized_system(documents)
    batch_results = run_batch_processing_benchmark(documents)

    # Calculate improvements
    trigger_speedup = (
        original_results["average_trigger_time_ms"] /
        optimized_results["average_trigger_time_ms"]
        if optimized_results["average_trigger_time_ms"] > 0 else 1.0
    )

    overall_speedup = (
        original_results["sentences_per_second"] /
        optimized_results["sentences_per_second"]
        if original_results["sentences_per_second"] > 0 else 1.0
    )

    # Display results
    print(f"\n📊 Original System Performance:")
    print(f"   • Average trigger time: {original_results['average_trigger_time_ms']:.3f}ms")
    print(f"   • Sentences per second: {original_results['sentences_per_second']:.1f}")
    print(f"   • Trigger hit rate: {original_results['trigger_hit_rate']:.1%}")
    print(f"   • Total processing time: {original_results['total_time_seconds']:.3f}s")

    print(f"\n⚡ Optimized System Performance:")
    print(f"   • Average trigger time: {optimized_results['average_trigger_time_ms']:.3f}ms")
    print(f"   • Sentences per second: {optimized_results['sentences_per_second']:.1f}")
    print(f"   • Trigger hit rate: {optimized_results['trigger_hit_rate']:.1%}")
    print(f"   • Total processing time: {optimized_results['total_time_seconds']:.3f}s")

    print(f"\n📦 Batch Processing Performance:")
    print(f"   • Batch sentences/sec: {batch_results['sentences_per_second']:.1f}")
    print(f"   • Total extractions: {batch_results['total_extractions']}")
    print(f"   • Extractions per second: {batch_results['extractions_per_second']:.1f}")

    print(f"\n🎯 Performance Improvements:")
    print(f"   • Trigger speedup: {trigger_speedup:.2f}x")
    print(f"   • Overall speedup: {overall_speedup:.2f}x")
    print(f"   • Target achieved: {'✅ YES' if trigger_speedup >= 2.0 else '❌ NO'}")

    # Engine statistics
    if "engine_stats" in optimized_results and optimized_results["engine_stats"]:
        stats = optimized_results["engine_stats"]
        print(f"\n🔧 Engine Statistics:")
        print(f"   • Parsers registered: {stats.get('parsers_registered', 0)}")
        print(f"   • Engine compiled: {stats.get('compiled', False)}")
        print(f"   • Average lookup time: {stats.get('average_lookup_time_ms', 0):.3f}ms")

    # Save validation results
    validation_data = {
        "timestamp": time.time(),
        "test_configuration": {
            "documents": len(documents),
            "total_sentences": original_results["total_sentences"]
        },
        "original_system": original_results,
        "optimized_system": optimized_results,
        "batch_processing": batch_results,
        "performance_improvements": {
            "trigger_speedup": trigger_speedup,
            "overall_speedup": overall_speedup,
            "target_achieved": trigger_speedup >= 2.0
        }
    }

    with open("trigger_optimization_validation.json", "w") as f:
        json.dump(validation_data, f, indent=2)

    print(f"\n✅ Validation complete!")
    print(f"   Results saved to: trigger_optimization_validation.json")

    if trigger_speedup >= 2.0:
        print(f"   🎉 SUCCESS: {trigger_speedup:.2f}x speedup achieved (target: 2.0x)")
    else:
        print(f"   ⚠️  Target not met: {trigger_speedup:.2f}x achieved (target: 2.0x)")


if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
String Regex Performance Benchmark Script - Phase 2

This script benchmarks the current string-based regex performance in ChemDataExtractor2
to establish baseline metrics before Phase 2 optimization.

Phase 2 focuses on optimizing:
- re.split, re.search, re.match, re.sub calls throughout the codebase
- String operations in quantity parsing, text processing, and tokenization
- Pre-compiled pattern lookups vs runtime compilation

Usage:
    python benchmark_string_regex_performance.py

Results are saved to string_regex_baseline.json for comparison after optimization.
"""

import json
import re
import statistics
import time
from datetime import datetime

from chemdataextractor.doc import Document
from chemdataextractor.nlp.tokenize import ChemWordTokenizer
from chemdataextractor.parse.quantity import _find_value_strings
from chemdataextractor.parse.quantity import _split
from chemdataextractor.parse.quantity import extract_error
from chemdataextractor.text.normalize import ChemNormalizer
from chemdataextractor.text.processors import floats


class StringRegexBenchmark:
    """Comprehensive string-based regex performance benchmark suite."""

    def __init__(self, iterations: int = 1000):
        self.iterations = iterations
        self.results = {}

        # Test data for various string operations
        self.error_strings = [
            "100±5",
            "25.3±0.1",
            "123(45)",
            "456.7(8.9)",
            "78±2.1",
            "1000±50",
            "0.5(0.1)",
            "234±15",
            "89.2(3.4)",
            "567±23",
        ] * 10  # Multiply for realistic batch size

        self.value_strings = [
            "100-200",
            "25.5-30.2",
            "-100",
            "1000",
            "123 456",
            "78.9±2.1",
            "45(3)",
            "scientific 1.5e3",
            "range 10-20",
            "negative -45.2",
            "decimal 123.456",
            "integer 789",
        ] * 10

        self.unit_strings = [
            "mg/kg",
            "cm/s",
            "mol/L",
            "m2",
            "kg3",
            "(mg)",
            "unit(special)",
            "kg⋅m/s2",
            "mol/(L⋅s)",
            "°C",
            "kJ/mol",
            "g/cm3",
            "Hz",
            "Pa⋅s",
        ] * 10

        self.float_strings = [
            "123(45)",
            "456.7±8.9",
            "1.5×10^3",
            "2.3x10^-4",
            "100±5",
            "123.45,",
            "$123.45",
            "(123.45)",
            "123 456",
            "  123.45  ",
            "1,234.56",
            "12,345",
            "0(1)",
            "123.0(0.1)",
            "1000(50)",
        ] * 10

        self.normalizer_strings = [
            "aluminum sulphate",
            "cesium chloride",
            "SULPHUR compound",
            "aluminum oxide",
            "cesium",
            "sulphur dioxide",
            "Aluminum",
            "normal chemical text",
            "benzene solution",
            "sodium chloride",
        ] * 10

        self.tokenizer_strings = [
            "benzene",
            "sodium chloride",
            "H2SO4",
            "C6H6",
            "25°C",
            "100mg",
            "2,4-dichlorobenzene",
            "α-methylstyrene",
            "tert-butanol",
            "The melting point of benzene (C6H6) is 5.5°C at 1 atm pressure.",
            "CH3-CH2-OH",
            "1.5×10^3",
            "±0.1",
            "α-helix β-sheet",
        ] * 5

        # Sample chemical text for document processing
        self.document_text = (
            """
        The melting point of benzene (C6H6) is 5.5°C and its boiling point is 80.1°C.
        Aluminum sulphate was dissolved in 50 mL of water and heated to 40±2°C.
        Cesium chloride (CsCl) has a melting point of 645°C. The reaction yielded
        123.45±0.5 mg of crystalline product with 95% purity. IR spectroscopy showed
        characteristic peaks at 1650±10 cm⁻¹ and 3400±20 cm⁻¹. The molecular weight
        was determined to be 254.3(1.2) g/mol using mass spectrometry. Scientific notation
        values included 1.5×10^3 M and 2.3x10^-4 mol/L concentrations.
        """
            * 20
        )  # Multiply for realistic document size

    def time_function(self, func, *args, **kwargs):
        """Time a function execution with multiple iterations."""
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)

        return {
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "stdev": statistics.stdev(times) if len(times) > 1 else 0,
            "min": min(times),
            "max": max(times),
            "total": sum(times),
            "iterations": len(times),
        }

    def benchmark_extract_error_operations(self):
        """Benchmark extract_error function string operations."""
        print("Benchmarking extract_error regex operations...")

        def test_extract_error_batch():
            results = []
            for error_string in self.error_strings:
                try:
                    result = extract_error(error_string)
                    results.append(result)
                except:
                    results.append(None)
            return results

        self.results["extract_error_operations"] = self.time_function(test_extract_error_batch)
        self.results["extract_error_operations"]["strings_per_iteration"] = len(self.error_strings)

    def benchmark_find_value_strings_operations(self):
        """Benchmark _find_value_strings function regex operations."""
        print("Benchmarking _find_value_strings regex operations...")

        def test_find_value_strings_batch():
            results = []
            for value_string in self.value_strings:
                try:
                    result = _find_value_strings(value_string)
                    results.append(result)
                except:
                    results.append(None)
            return results

        self.results["find_value_strings_operations"] = self.time_function(
            test_find_value_strings_batch
        )
        self.results["find_value_strings_operations"]["strings_per_iteration"] = len(
            self.value_strings
        )

    def benchmark_split_operations(self):
        """Benchmark _split function regex operations."""
        print("Benchmarking _split regex operations...")

        def test_split_batch():
            results = []
            for unit_string in self.unit_strings:
                try:
                    result = _split(unit_string)
                    results.append(result)
                except:
                    results.append(None)
            return results

        self.results["split_operations"] = self.time_function(test_split_batch)
        self.results["split_operations"]["strings_per_iteration"] = len(self.unit_strings)

    def benchmark_floats_operations(self):
        """Benchmark floats function regex operations."""
        print("Benchmarking floats regex operations...")

        def test_floats_batch():
            results = []
            for float_string in self.float_strings:
                try:
                    result = floats(float_string)
                    results.append(result)
                except:
                    results.append(None)
            return results

        self.results["floats_operations"] = self.time_function(test_floats_batch)
        self.results["floats_operations"]["strings_per_iteration"] = len(self.float_strings)

    def benchmark_normalizer_operations(self):
        """Benchmark ChemNormalizer regex operations."""
        print("Benchmarking ChemNormalizer regex operations...")

        normalizer = ChemNormalizer(chem_spell=True, strip=True)

        def test_normalizer_batch():
            results = []
            for norm_string in self.normalizer_strings:
                try:
                    result = normalizer.normalize(norm_string)
                    results.append(result)
                except:
                    results.append(None)
            return results

        self.results["normalizer_operations"] = self.time_function(test_normalizer_batch)
        self.results["normalizer_operations"]["strings_per_iteration"] = len(
            self.normalizer_strings
        )

    def benchmark_tokenizer_operations(self):
        """Benchmark ChemWordTokenizer regex operations."""
        print("Benchmarking ChemWordTokenizer regex operations...")

        tokenizer = ChemWordTokenizer()

        def test_tokenizer_batch():
            results = []
            for token_string in self.tokenizer_strings:
                try:
                    result = tokenizer.tokenize(token_string)
                    results.append(result)
                except:
                    results.append(None)
            return results

        self.results["tokenizer_operations"] = self.time_function(test_tokenizer_batch)
        self.results["tokenizer_operations"]["strings_per_iteration"] = len(self.tokenizer_strings)

    def benchmark_raw_regex_operations(self):
        """Benchmark raw regex operations that will be optimized."""
        print("Benchmarking raw regex operations...")

        # Test the specific regex patterns used in the functions
        test_patterns = [
            r"(\d+\.?(?:\d+)?)|(±)|(\()",  # extract_error pattern
            r" |(-)",  # space/dash splitting
            r"(\))|(\()",  # bracket patterns
            r"(\d)\s*\(\d+(\.\d+)?\)",  # bracketed numbers
            r"(\d)\s*±\s*\d+(\.\d+)?",  # uncertainty notation
            r"(\d)\s*[×x]\s*10\^?(-?\d)",  # scientific notation
            r"sulph",
            r"aluminum",
            r"cesium",  # normalization patterns
        ]

        test_strings = [
            "100±5",
            "123(45)",
            "text(more)",
            "456.7±8.9",
            "1.5×10^3",
            "aluminum sulphate",
            "cesium chloride",
            "100 - 200",
        ]

        def test_raw_regex_compile_every_time():
            matches = 0
            for pattern in test_patterns:
                for string in test_strings:
                    regex = re.compile(pattern, re.I | re.U)  # Compile every time
                    if regex.search(string):
                        matches += 1
            return matches

        def test_raw_regex_precompiled():
            compiled_patterns = [re.compile(p, re.I | re.U) for p in test_patterns]
            matches = 0
            for pattern in compiled_patterns:
                for string in test_strings:
                    if pattern.search(string):
                        matches += 1
            return matches

        self.results["raw_regex_operations"] = {
            "compile_every_time": self.time_function(test_raw_regex_compile_every_time),
            "precompiled": self.time_function(test_raw_regex_precompiled),
        }

        # Calculate overhead
        compile_time = self.results["raw_regex_operations"]["compile_every_time"]["mean"]
        precompiled_time = self.results["raw_regex_operations"]["precompiled"]["mean"]
        overhead_ratio = compile_time / precompiled_time if precompiled_time > 0 else 0
        self.results["raw_regex_operations"]["overhead_ratio"] = overhead_ratio

    def benchmark_document_processing_with_strings(self):
        """Benchmark document processing that triggers string regex operations."""
        print("Benchmarking document processing with string operations...")

        def test_document_processing():
            doc = Document(self.document_text)
            # Force processing that uses string regex operations
            sentences = []
            for element in doc.elements:
                if hasattr(element, "sentences"):
                    sentences.extend(element.sentences)

            # Additional processing that might trigger string operations
            tokens = []
            for sentence in sentences[:10]:  # Limit to prevent excessive runtime
                tokens.extend(sentence.tokens)

            return len(sentences), len(tokens)

        # Reduce iterations for document processing (it's expensive)
        doc_times = []
        for _ in range(min(5, self.iterations // 200)):
            start = time.perf_counter()
            sentence_count, token_count = test_document_processing()
            end = time.perf_counter()
            doc_times.append(end - start)

        self.results["document_processing_strings"] = {
            "mean": statistics.mean(doc_times),
            "median": statistics.median(doc_times),
            "stdev": statistics.stdev(doc_times) if len(doc_times) > 1 else 0,
            "min": min(doc_times),
            "max": max(doc_times),
            "total": sum(doc_times),
            "iterations": len(doc_times),
            "text_length": len(self.document_text),
        }

    def benchmark_string_splitting_patterns(self):
        """Benchmark common string splitting patterns used throughout codebase."""
        print("Benchmarking string splitting patterns...")

        split_test_data = [
            ("100±5", r"(\d+\.?(?:\d+)?)|(±)|(\()"),
            ("100 - 200", r" |(-)"),
            ("mg/kg", r"/"),
            ("text(more)end", r"(\))|(\()"),
            ("1.5×10^3", r"(\d)\s*[×x]\s*10\^?(-?\d)"),
        ] * 20

        def test_splits_compile_every_time():
            results = []
            for text, pattern in split_test_data:
                splits = re.split(pattern, text)
                results.append([s for s in splits if s and s != " "])
            return results

        # Pre-compile patterns
        compiled_split_patterns = {}
        for text, pattern in split_test_data:
            if pattern not in compiled_split_patterns:
                compiled_split_patterns[pattern] = re.compile(pattern)

        def test_splits_precompiled():
            results = []
            for text, pattern in split_test_data:
                compiled_pattern = compiled_split_patterns[pattern]
                splits = compiled_pattern.split(text)
                results.append([s for s in splits if s and s != " "])
            return results

        self.results["string_splitting_patterns"] = {
            "compile_every_time": self.time_function(test_splits_compile_every_time),
            "precompiled": self.time_function(test_splits_precompiled),
        }

        # Calculate overhead
        compile_time = self.results["string_splitting_patterns"]["compile_every_time"]["mean"]
        precompiled_time = self.results["string_splitting_patterns"]["precompiled"]["mean"]
        overhead_ratio = compile_time / precompiled_time if precompiled_time > 0 else 0
        self.results["string_splitting_patterns"]["overhead_ratio"] = overhead_ratio

    def run_all_benchmarks(self):
        """Run all benchmark tests."""
        print(f"Starting string regex performance benchmarks with {self.iterations} iterations...")
        print("=" * 70)

        start_time = time.time()

        self.benchmark_raw_regex_operations()
        self.benchmark_string_splitting_patterns()
        self.benchmark_extract_error_operations()
        self.benchmark_find_value_strings_operations()
        self.benchmark_split_operations()
        self.benchmark_floats_operations()
        self.benchmark_normalizer_operations()
        self.benchmark_tokenizer_operations()
        self.benchmark_document_processing_with_strings()

        total_time = time.time() - start_time

        # Add metadata
        self.results["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "total_benchmark_time": total_time,
            "iterations": self.iterations,
            "python_version": __import__("sys").version,
            "platform": __import__("platform").platform(),
            "optimization_phase": "Phase 2 - String Operations Baseline",
        }

        print(f"\nBenchmarks completed in {total_time:.2f} seconds")
        print("=" * 70)

    def print_summary(self):
        """Print a summary of benchmark results."""
        print("\n" + "=" * 70)
        print("STRING REGEX PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 70)

        # Raw regex overhead
        if "raw_regex_operations" in self.results:
            raw = self.results["raw_regex_operations"]
            print("\n📊 RAW REGEX COMPILATION OVERHEAD:")
            print(f"   Compile every time: {raw['compile_every_time']['mean'] * 1000:.3f}ms")
            print(f"   Use pre-compiled:   {raw['precompiled']['mean'] * 1000:.3f}ms")
            print(f"   Overhead ratio:     {raw['overhead_ratio']:.1f}x")

        # String splitting overhead
        if "string_splitting_patterns" in self.results:
            split = self.results["string_splitting_patterns"]
            print("\n✂️  STRING SPLITTING PATTERNS:")
            print(f"   Compile every time: {split['compile_every_time']['mean'] * 1000:.3f}ms")
            print(f"   Use pre-compiled:   {split['precompiled']['mean'] * 1000:.3f}ms")
            print(f"   Overhead ratio:     {split['overhead_ratio']:.1f}x")

        # Function-specific operations
        function_benchmarks = [
            ("extract_error_operations", "EXTRACT ERROR"),
            ("find_value_strings_operations", "FIND VALUE STRINGS"),
            ("split_operations", "SPLIT OPERATIONS"),
            ("floats_operations", "FLOATS CONVERSION"),
            ("normalizer_operations", "TEXT NORMALIZATION"),
            ("tokenizer_operations", "TOKENIZATION"),
        ]

        for key, name in function_benchmarks:
            if key in self.results:
                ops = self.results[key]
                strings_per_sec = ops["strings_per_iteration"] / ops["mean"]
                print(f"\n🔧 {name}:")
                print(f"   Mean time:        {ops['mean'] * 1000:.3f}ms")
                print(f"   Strings/second:   {strings_per_sec:.0f}")
                print(f"   Strings/iter:     {ops['strings_per_iteration']}")

        # Document processing
        if "document_processing_strings" in self.results:
            doc = self.results["document_processing_strings"]
            chars_per_second = doc["text_length"] / doc["mean"]
            print("\n📄 DOCUMENT PROCESSING (with string ops):")
            print(f"   Mean time:       {doc['mean']:.3f}s")
            print(f"   Characters/sec:  {chars_per_second:.0f}")
            print(f"   Text length:     {doc['text_length']:,} chars")

        print(f"\n⏱️  TOTAL BENCHMARK TIME: {self.results['metadata']['total_benchmark_time']:.2f}s")
        print("=" * 70)

    def save_results(self, filename: str = "string_regex_baseline.json"):
        """Save benchmark results to JSON file."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

    def compare_with_previous(self, filename: str = "string_regex_baseline.json"):
        """Compare current results with previous benchmark."""
        try:
            with open(filename) as f:
                previous = json.load(f)

            print("\n📊 COMPARISON WITH PREVIOUS BENCHMARK:")
            print("=" * 70)

            # Compare key metrics
            comparisons = [
                ("raw_regex_operations.overhead_ratio", "Raw Regex Overhead Ratio"),
                ("string_splitting_patterns.overhead_ratio", "String Splitting Overhead"),
                ("extract_error_operations.mean", "Extract Error Time"),
                ("floats_operations.mean", "Floats Conversion Time"),
                ("normalizer_operations.mean", "Normalization Time"),
                ("tokenizer_operations.mean", "Tokenization Time"),
                ("document_processing_strings.mean", "Document Processing Time"),
            ]

            for path, name in comparisons:
                try:
                    current_val = self._get_nested_value(self.results, path)
                    previous_val = self._get_nested_value(previous, path)

                    if current_val and previous_val:
                        change = ((current_val - previous_val) / previous_val) * 100
                        symbol = "📈" if change > 0 else "📉"
                        print(f"{symbol} {name}: {change:+.1f}%")
                except:
                    pass

        except FileNotFoundError:
            print(f"\n⚠️  No previous benchmark file found ({filename})")

    def _get_nested_value(self, data: dict, path: str):
        """Get nested dictionary value using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value


def main():
    """Main benchmark execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark ChemDataExtractor string regex performance"
    )
    parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=500,
        help="Number of iterations for each test (default: 500)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="string_regex_baseline.json",
        help="Output file for results (default: string_regex_baseline.json)",
    )
    parser.add_argument(
        "--compare", "-c", action="store_true", help="Compare with previous results"
    )

    args = parser.parse_args()

    benchmark = StringRegexBenchmark(iterations=args.iterations)

    if args.compare:
        benchmark.compare_with_previous(args.output)

    benchmark.run_all_benchmarks()
    benchmark.print_summary()
    benchmark.save_results(args.output)

    if args.compare:
        benchmark.compare_with_previous(args.output)


if __name__ == "__main__":
    main()

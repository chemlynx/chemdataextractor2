#!/usr/bin/env python
"""
Regex Performance Benchmark Script

This script benchmarks the current regex performance in ChemDataExtractor2
to establish baseline metrics before optimization.

Usage:
    python benchmark_regex_performance.py

The script tests:
1. Regex parser element creation and matching
2. RegexTagger pattern compilation and tagging
3. Real-world document processing scenarios

Results are saved to benchmark_results.json for comparison after optimization.
"""

import json
import re
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any

from chemdataextractor.parse.elements import Regex
from chemdataextractor.nlp.tag import RegexTagger
from chemdataextractor.doc import Document


class RegexBenchmark:
    """Comprehensive regex performance benchmark suite."""
    
    def __init__(self, iterations: int = 1000):
        self.iterations = iterations
        self.results = {}
        
        # Test patterns commonly used in ChemDataExtractor
        self.test_patterns = [
            r'\d+',
            r'[Tt]emperature',
            r'C\d+H\d+',
            r'\d+(\.\d+)?\s*°[CF]',
            r'[A-Za-z]+\s*\(\s*\d+\s*\)',
            r'(?i)(melting|boiling)\s+point',
            r'\d+\.\d+\s*(nm|μm|mm|cm|m)',
            r'[A-Z][a-z]*\s*-?\s*\d+',
            r'(?:solvent|solution|dissolved)\s+in\s+\w+',
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:g|kg|mg|μg)\b'
        ]
        
        # Test tokens commonly found in chemical documents
        self.test_tokens = [
            '25', 'degrees', 'celsius', 'temperature', 'C6H6', 'benzene',
            '80.5°C', 'melting', 'point', 'solution', 'dissolved', 'water',
            'sodium', 'chloride', 'NaCl', '123.45', 'mg', 'crystalline',
            'powder', 'synthesis', 'reaction', 'catalyst', 'product',
            'yield', '95%', 'purity', 'analysis', 'spectroscopy'
        ] * 50  # Multiply to get more realistic token count
        
        # Sample chemical text for document processing
        self.sample_text = """
        The melting point of benzene (C6H6) is 5.5°C and its boiling point is 80.1°C.
        The compound was dissolved in 50 mL of dichloromethane and heated to 40°C.
        Sodium chloride (NaCl) has a melting point of 801°C. The reaction yielded
        123.45 mg of crystalline product with 95% purity. IR spectroscopy showed
        characteristic peaks at 1650 cm⁻¹ and 3400 cm⁻¹. The molecular weight
        was determined to be 254.3 g/mol using mass spectrometry.
        """ * 100  # Multiply for more realistic document size

    def time_function(self, func, *args, **kwargs):
        """Time a function execution with multiple iterations."""
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'min': min(times),
            'max': max(times),
            'total': sum(times),
            'iterations': len(times)
        }

    def benchmark_regex_element_creation(self):
        """Benchmark Regex parser element creation."""
        print("Benchmarking Regex element creation...")
        
        def create_regex_elements():
            elements = []
            for pattern in self.test_patterns:
                elements.append(Regex(pattern))
            return elements
        
        # Benchmark with reduced iterations for creation (it's expensive)
        creation_times = []
        for _ in range(min(100, self.iterations)):
            start = time.perf_counter()
            create_regex_elements()
            end = time.perf_counter()
            creation_times.append(end - start)
        
        self.results['regex_element_creation'] = {
            'mean': statistics.mean(creation_times),
            'median': statistics.median(creation_times),
            'stdev': statistics.stdev(creation_times) if len(creation_times) > 1 else 0,
            'min': min(creation_times),
            'max': max(creation_times),
            'total': sum(creation_times),
            'iterations': len(creation_times),
            'patterns_per_iteration': len(self.test_patterns)
        }

    def benchmark_regex_element_matching(self):
        """Benchmark Regex parser element matching."""
        print("Benchmarking Regex element matching...")
        
        # Create regex elements once
        regex_elements = [Regex(pattern) for pattern in self.test_patterns]
        test_tokens = [('test123', 'CD'), ('Temperature', 'NN'), ('C6H6', 'NN')]
        
        def test_matching():
            matches = 0
            for element in regex_elements:
                for i, token in enumerate(test_tokens):
                    try:
                        result, next_pos = element._parse_tokens(test_tokens, i)
                        matches += 1
                    except:
                        pass  # No match, continue
            return matches
        
        self.results['regex_element_matching'] = self.time_function(test_matching)

    def benchmark_regex_tagger_creation(self):
        """Benchmark RegexTagger creation with different pattern sets."""
        print("Benchmarking RegexTagger creation...")
        
        # Test with different pattern configurations
        pattern_sets = {
            'small': [(pattern, 'TEST') for pattern in self.test_patterns[:3]],
            'medium': [(pattern, 'TEST') for pattern in self.test_patterns[:6]],
            'large': [(pattern, 'TEST') for pattern in self.test_patterns]
        }
        
        for size, patterns in pattern_sets.items():
            def create_tagger():
                return RegexTagger(patterns=patterns)
            
            # Reduce iterations for creation benchmarks
            times = []
            for _ in range(min(50, self.iterations)):
                start = time.perf_counter()
                create_tagger()
                end = time.perf_counter()
                times.append(end - start)
            
            self.results[f'regex_tagger_creation_{size}'] = {
                'mean': statistics.mean(times),
                'median': statistics.median(times),
                'stdev': statistics.stdev(times) if len(times) > 1 else 0,
                'min': min(times),
                'max': max(times),
                'total': sum(times),
                'iterations': len(times),
                'pattern_count': len(patterns)
            }

    def benchmark_regex_tagger_tagging(self):
        """Benchmark RegexTagger tagging performance."""
        print("Benchmarking RegexTagger tagging...")
        
        # Create tagger once
        patterns = [(pattern, 'TEST') for pattern in self.test_patterns]
        tagger = RegexTagger(patterns=patterns)
        
        def tag_tokens():
            return tagger.tag(self.test_tokens)
        
        self.results['regex_tagger_tagging'] = self.time_function(tag_tokens)
        self.results['regex_tagger_tagging']['tokens_per_iteration'] = len(self.test_tokens)

    def benchmark_document_processing(self):
        """Benchmark regex usage in real document processing."""
        print("Benchmarking document processing...")
        
        def process_document():
            doc = Document(self.sample_text)
            # Force parsing to trigger regex usage
            sentences = []
            for element in doc.elements:
                if hasattr(element, 'sentences'):
                    sentences.extend(element.sentences)
            return len(sentences)
        
        # Reduce iterations for document processing (it's very expensive)
        doc_times = []
        for _ in range(min(10, self.iterations // 100)):
            start = time.perf_counter()
            sentence_count = process_document()
            end = time.perf_counter()
            doc_times.append(end - start)
        
        self.results['document_processing'] = {
            'mean': statistics.mean(doc_times),
            'median': statistics.median(doc_times),
            'stdev': statistics.stdev(doc_times) if len(doc_times) > 1 else 0,
            'min': min(doc_times),
            'max': max(doc_times),
            'total': sum(doc_times),
            'iterations': len(doc_times),
            'text_length': len(self.sample_text)
        }

    def benchmark_regex_compilation_overhead(self):
        """Benchmark the overhead of regex compilation vs reuse."""
        print("Benchmarking regex compilation overhead...")
        
        pattern = r'C\d+H\d+O\d+'
        test_text = 'C6H12O6 glucose and C2H6O ethanol'
        
        # Test compilation on every use
        def compile_every_time():
            regex = re.compile(pattern)
            return regex.findall(test_text)
        
        # Test with pre-compiled regex
        pre_compiled = re.compile(pattern)
        def use_precompiled():
            return pre_compiled.findall(test_text)
        
        self.results['regex_compilation_overhead'] = {
            'compile_every_time': self.time_function(compile_every_time),
            'use_precompiled': self.time_function(use_precompiled)
        }
        
        # Calculate overhead
        overhead_ratio = (self.results['regex_compilation_overhead']['compile_every_time']['mean'] / 
                         self.results['regex_compilation_overhead']['use_precompiled']['mean'])
        self.results['regex_compilation_overhead']['overhead_ratio'] = overhead_ratio

    def run_all_benchmarks(self):
        """Run all benchmark tests."""
        print(f"Starting regex performance benchmarks with {self.iterations} iterations...")
        print("=" * 60)
        
        start_time = time.time()
        
        self.benchmark_regex_compilation_overhead()
        self.benchmark_regex_element_creation()
        self.benchmark_regex_element_matching()
        self.benchmark_regex_tagger_creation()
        self.benchmark_regex_tagger_tagging()
        self.benchmark_document_processing()
        
        total_time = time.time() - start_time
        
        # Add metadata
        self.results['metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'total_benchmark_time': total_time,
            'iterations': self.iterations,
            'python_version': __import__('sys').version,
            'platform': __import__('platform').platform()
        }
        
        print(f"\nBenchmarks completed in {total_time:.2f} seconds")
        print("=" * 60)

    def print_summary(self):
        """Print a summary of benchmark results."""
        print("\n" + "="*60)
        print("REGEX PERFORMANCE BENCHMARK SUMMARY")
        print("="*60)
        
        # Compilation overhead
        if 'regex_compilation_overhead' in self.results:
            overhead = self.results['regex_compilation_overhead']
            print(f"\n📊 REGEX COMPILATION OVERHEAD:")
            print(f"   Compile every time: {overhead['compile_every_time']['mean']*1000:.3f}ms")
            print(f"   Use pre-compiled:   {overhead['use_precompiled']['mean']*1000:.3f}ms")
            print(f"   Overhead ratio:     {overhead['overhead_ratio']:.1f}x")
        
        # Element creation
        if 'regex_element_creation' in self.results:
            creation = self.results['regex_element_creation']
            print(f"\n🏗️  REGEX ELEMENT CREATION:")
            print(f"   Mean time:     {creation['mean']*1000:.3f}ms")
            print(f"   Patterns/iter: {creation['patterns_per_iteration']}")
            print(f"   Total time:    {creation['total']:.3f}s")
        
        # Tagger creation
        for size in ['small', 'medium', 'large']:
            key = f'regex_tagger_creation_{size}'
            if key in self.results:
                tagger = self.results[key]
                print(f"\n🏷️  REGEX TAGGER CREATION ({size.upper()}):")
                print(f"   Mean time:     {tagger['mean']*1000:.3f}ms")
                print(f"   Pattern count: {tagger['pattern_count']}")
        
        # Tagging performance
        if 'regex_tagger_tagging' in self.results:
            tagging = self.results['regex_tagger_tagging']
            tokens_per_second = tagging['tokens_per_iteration'] / tagging['mean']
            print(f"\n⚡ REGEX TAGGER TAGGING:")
            print(f"   Mean time:       {tagging['mean']*1000:.3f}ms")
            print(f"   Tokens/second:   {tokens_per_second:.0f}")
            print(f"   Tokens/iter:     {tagging['tokens_per_iteration']}")
        
        # Document processing
        if 'document_processing' in self.results:
            doc = self.results['document_processing']
            chars_per_second = doc['text_length'] / doc['mean']
            print(f"\n📄 DOCUMENT PROCESSING:")
            print(f"   Mean time:       {doc['mean']:.3f}s")
            print(f"   Characters/sec:  {chars_per_second:.0f}")
            print(f"   Text length:     {doc['text_length']:,} chars")
        
        print(f"\n⏱️  TOTAL BENCHMARK TIME: {self.results['metadata']['total_benchmark_time']:.2f}s")
        print("="*60)

    def save_results(self, filename: str = 'benchmark_results.json'):
        """Save benchmark results to JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Results saved to {filename}")

    def compare_with_previous(self, filename: str = 'benchmark_results.json'):
        """Compare current results with previous benchmark."""
        try:
            with open(filename, 'r') as f:
                previous = json.load(f)
            
            print(f"\n📊 COMPARISON WITH PREVIOUS BENCHMARK:")
            print("="*60)
            
            # Compare key metrics
            comparisons = [
                ('regex_compilation_overhead.overhead_ratio', 'Compilation Overhead Ratio'),
                ('regex_element_creation.mean', 'Element Creation Time'),
                ('regex_tagger_creation_large.mean', 'Tagger Creation Time'),
                ('regex_tagger_tagging.mean', 'Tagging Time'),
                ('document_processing.mean', 'Document Processing Time')
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

    def _get_nested_value(self, data: Dict, path: str):
        """Get nested dictionary value using dot notation."""
        keys = path.split('.')
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
    
    parser = argparse.ArgumentParser(description='Benchmark ChemDataExtractor regex performance')
    parser.add_argument('--iterations', '-i', type=int, default=1000,
                       help='Number of iterations for each test (default: 1000)')
    parser.add_argument('--output', '-o', type=str, default='benchmark_results.json',
                       help='Output file for results (default: benchmark_results.json)')
    parser.add_argument('--compare', '-c', action='store_true',
                       help='Compare with previous results')
    
    args = parser.parse_args()
    
    benchmark = RegexBenchmark(iterations=args.iterations)
    
    if args.compare:
        benchmark.compare_with_previous(args.output)
    
    benchmark.run_all_benchmarks()
    benchmark.print_summary()
    benchmark.save_results(args.output)
    
    if args.compare:
        benchmark.compare_with_previous(args.output)


if __name__ == '__main__':
    main()
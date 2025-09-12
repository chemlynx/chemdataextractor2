#!/usr/bin/env python3
"""
Batch Processing Examples

This module demonstrates how to process multiple documents efficiently
using ChemDataExtractor2, including parallel processing, progress tracking,
error handling, and result aggregation.

Usage:
    python batch_processing.py [--parallel] [--input-dir PATH] [--output-dir PATH]

Requirements:
    - ChemDataExtractor2 installed
    - Multiple documents for processing
    - Optional: concurrent.futures for parallel processing
"""

import argparse
import logging
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from chemdataextractor.doc import Document
from chemdataextractor.model import Compound, MeltingPoint, BoilingPoint, IrSpectrum


# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingStats:
    """Statistics for batch processing."""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_records: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass 
class DocumentResult:
    """Result of processing a single document."""
    filename: str
    success: bool
    records: List[Dict[str, Any]] = None
    error_message: str = ""
    processing_time: float = 0.0
    record_count: int = 0
    
    def __post_init__(self):
        if self.records is None:
            self.records = []
        self.record_count = len(self.records)


def process_single_document(file_path: Path) -> DocumentResult:
    """Process a single document and return results."""
    start_time = time.time()
    result = DocumentResult(filename=file_path.name, success=False)
    
    try:
        logger.info(f"Processing: {file_path.name}")
        
        # Create document from file
        doc = Document.from_file(str(file_path))
        
        # Extract records
        records = []
        for record in doc.records:
            if hasattr(record, 'serialize'):
                records.append(record.serialize())
            else:
                # Fallback for non-serializable records
                records.append({
                    'type': type(record).__name__,
                    'data': str(record)
                })
        
        result.records = records
        result.record_count = len(records)
        result.success = True
        
        logger.info(f"Successfully processed {file_path.name}: {len(records)} records")
        
    except Exception as e:
        error_msg = f"Error processing {file_path.name}: {str(e)}"
        logger.error(error_msg)
        result.error_message = error_msg
    
    finally:
        result.processing_time = time.time() - start_time
    
    return result


def batch_process_sequential(file_paths: List[Path]) -> Tuple[List[DocumentResult], ProcessingStats]:
    """Process documents sequentially."""
    print("=== Sequential Batch Processing ===")
    
    results = []
    stats = ProcessingStats(total_files=len(file_paths))
    start_time = time.time()
    
    for i, file_path in enumerate(file_paths, 1):
        print(f"Progress: {i}/{len(file_paths)} ({i/len(file_paths)*100:.1f}%)")
        
        result = process_single_document(file_path)
        results.append(result)
        
        if result.success:
            stats.processed_files += 1
            stats.total_records += result.record_count
        else:
            stats.failed_files += 1
            stats.errors.append(result.error_message)
    
    stats.processing_time = time.time() - start_time
    
    print(f"\nSequential processing completed in {stats.processing_time:.2f} seconds")
    print(f"Processed: {stats.processed_files}, Failed: {stats.failed_files}")
    
    return results, stats


def batch_process_parallel(file_paths: List[Path], max_workers: int = 4) -> Tuple[List[DocumentResult], ProcessingStats]:
    """Process documents in parallel using multiprocessing."""
    print(f"=== Parallel Batch Processing (workers: {max_workers}) ===")
    
    results = []
    stats = ProcessingStats(total_files=len(file_paths))
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_path = {executor.submit(process_single_document, path): path 
                         for path in file_paths}
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_path):
            completed += 1
            print(f"Progress: {completed}/{len(file_paths)} ({completed/len(file_paths)*100:.1f}%)")
            
            try:
                result = future.result()
                results.append(result)
                
                if result.success:
                    stats.processed_files += 1
                    stats.total_records += result.record_count
                else:
                    stats.failed_files += 1
                    stats.errors.append(result.error_message)
                    
            except Exception as e:
                error_msg = f"Future execution error: {str(e)}"
                logger.error(error_msg)
                stats.failed_files += 1
                stats.errors.append(error_msg)
    
    stats.processing_time = time.time() - start_time
    
    print(f"\nParallel processing completed in {stats.processing_time:.2f} seconds")
    print(f"Processed: {stats.processed_files}, Failed: {stats.failed_files}")
    
    return results, stats


def create_sample_documents(sample_dir: Path, num_docs: int = 10) -> List[Path]:
    """Create sample documents for batch processing demonstration."""
    print(f"=== Creating {num_docs} Sample Documents ===")
    
    sample_dir.mkdir(exist_ok=True)
    
    sample_texts = [
        "Benzene has a melting point of 5.5°C and boiling point of 80.1°C. IR shows peaks at 3030, 1480 cm-1.",
        "Toluene melts at -95°C and boils at 110.6°C. The compound exhibits IR absorption at 3028, 2920 cm-1.", 
        "Phenol has mp 40.5°C, bp 181.7°C. IR spectrum: 3200-3600 cm-1 (O-H), 1590, 1500 cm-1 (aromatic).",
        "Aniline: melting point -6.0°C, boiling point 184.1°C. IR: 3400, 3300 cm-1 (N-H), 1600 cm-1.",
        "Chlorobenzene mp -45.6°C, bp 131.7°C. IR shows C-Cl stretch at 750 cm-1, aromatic at 1590 cm-1.",
        "Nitrobenzene has a melting point of 5.7°C and boiling point of 210.9°C. IR: 1520, 1350 cm-1 (NO2).",
        "Acetone melts at -94.7°C and boils at 56.0°C. IR spectrum shows C=O stretch at 1715 cm-1.",
        "Ethanol: mp -114.1°C, bp 78.2°C. IR: 3200-3600 cm-1 (O-H), 2950, 2850 cm-1 (C-H), 1050 cm-1 (C-O).",
        "Acetic acid has melting point 16.6°C, boiling point 117.9°C. IR: 2500-3300 cm-1 (COOH), 1760 cm-1 (C=O).",
        "Diethyl ether mp -116.3°C, bp 34.6°C. IR spectrum: 2950, 2850 cm-1 (C-H), 1120 cm-1 (C-O-C)."
    ]
    
    file_paths = []
    for i in range(num_docs):
        file_path = sample_dir / f"sample_document_{i+1:02d}.txt"
        
        # Cycle through sample texts and add some variation
        text_index = i % len(sample_texts)
        text = sample_texts[text_index]
        
        # Add some document structure
        full_text = f"""
        Title: Chemical Properties of Compound {i+1}
        
        Abstract: This document describes the physical and spectroscopic properties 
        of an organic compound.
        
        Results: {text}
        
        Conclusion: The compound shows typical behavior expected for this class of molecules.
        """
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_text.strip())
        
        file_paths.append(file_path)
    
    print(f"Created {len(file_paths)} sample documents in {sample_dir}")
    return file_paths


def analyze_batch_results(results: List[DocumentResult]) -> Dict[str, Any]:
    """Analyze and summarize batch processing results."""
    print("\n=== Analyzing Batch Results ===")
    
    analysis = {
        'summary': {
            'total_documents': len(results),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'total_records': sum(r.record_count for r in results),
            'avg_records_per_doc': 0.0,
            'avg_processing_time': 0.0
        },
        'record_types': Counter(),
        'processing_times': [],
        'errors': []
    }
    
    # Calculate averages
    successful_results = [r for r in results if r.success]
    if successful_results:
        analysis['summary']['avg_records_per_doc'] = analysis['summary']['total_records'] / len(successful_results)
        analysis['summary']['avg_processing_time'] = sum(r.processing_time for r in successful_results) / len(successful_results)
    
    # Analyze record types
    for result in successful_results:
        for record in result.records:
            record_type = record.get('type', 'Unknown')
            analysis['record_types'][record_type] += 1
    
    # Collect processing times and errors
    analysis['processing_times'] = [r.processing_time for r in results]
    analysis['errors'] = [r.error_message for r in results if not r.success and r.error_message]
    
    # Display summary
    print(f"Documents processed: {analysis['summary']['successful']}/{analysis['summary']['total_documents']}")
    print(f"Total records extracted: {analysis['summary']['total_records']}")
    print(f"Average records per document: {analysis['summary']['avg_records_per_doc']:.1f}")
    print(f"Average processing time: {analysis['summary']['avg_processing_time']:.3f}s")
    
    if analysis['record_types']:
        print("\nRecord types found:")
        for record_type, count in analysis['record_types'].most_common():
            print(f"  {record_type}: {count}")
    
    if analysis['errors']:
        print(f"\nErrors encountered: {len(analysis['errors'])}")
        for error in analysis['errors'][:3]:  # Show first 3 errors
            print(f"  - {error}")
        if len(analysis['errors']) > 3:
            print(f"  ... and {len(analysis['errors']) - 3} more")
    
    return analysis


def export_batch_results(results: List[DocumentResult], analysis: Dict[str, Any], 
                        output_dir: Path, format: str = 'json'):
    """Export batch processing results to files."""
    print(f"\n=== Exporting Results to {output_dir} ===")
    
    output_dir.mkdir(exist_ok=True)
    
    # Export individual results
    if format.lower() == 'json':
        results_file = output_dir / "batch_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(result) for result in results], f, indent=2, ensure_ascii=False)
        print(f"Results exported to: {results_file}")
        
        # Export analysis
        analysis_file = output_dir / "batch_analysis.json"
        # Convert Counter to dict for JSON serialization
        analysis_copy = analysis.copy()
        analysis_copy['record_types'] = dict(analysis_copy['record_types'])
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_copy, f, indent=2, ensure_ascii=False)
        print(f"Analysis exported to: {analysis_file}")
    
    # Export consolidated records
    all_records = []
    for result in results:
        if result.success:
            for record in result.records:
                record['source_file'] = result.filename
                all_records.append(record)
    
    consolidated_file = output_dir / "consolidated_records.json"
    with open(consolidated_file, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)
    print(f"Consolidated records: {consolidated_file}")
    
    # Export CSV summary for easy analysis
    import csv
    summary_file = output_dir / "processing_summary.csv"
    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Filename', 'Success', 'Records', 'Processing_Time', 'Error'])
        
        for result in results:
            writer.writerow([
                result.filename,
                result.success,
                result.record_count,
                f"{result.processing_time:.3f}",
                result.error_message
            ])
    print(f"Summary CSV: {summary_file}")


def performance_comparison():
    """Compare sequential vs parallel processing performance."""
    print("\n=== Performance Comparison ===")
    
    # Create test documents
    test_dir = Path("batch_test_documents")
    file_paths = create_sample_documents(test_dir, num_docs=12)
    
    # Test sequential processing
    seq_results, seq_stats = batch_process_sequential(file_paths)
    
    # Test parallel processing
    par_results, par_stats = batch_process_parallel(file_paths, max_workers=4)
    
    # Compare performance
    speedup = seq_stats.processing_time / par_stats.processing_time if par_stats.processing_time > 0 else 0
    
    print("\nPerformance Comparison:")
    print(f"Sequential: {seq_stats.processing_time:.2f}s ({seq_stats.processed_files} files)")
    print(f"Parallel:   {par_stats.processing_time:.2f}s ({par_stats.processed_files} files)")
    print(f"Speedup:    {speedup:.2f}x")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return seq_stats, par_stats


def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="ChemDataExtractor2 Batch Processing Examples")
    parser.add_argument('--parallel', action='store_true', help='Use parallel processing')
    parser.add_argument('--input-dir', type=Path, help='Input directory with documents')
    parser.add_argument('--output-dir', type=Path, default=Path('batch_results'), help='Output directory')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--create-samples', action='store_true', help='Create sample documents')
    
    args = parser.parse_args()
    
    print("ChemDataExtractor2 - Batch Processing Examples")
    print("=" * 50)
    
    try:
        # Determine input files
        if args.create_samples or not args.input_dir:
            sample_dir = Path("sample_documents")
            file_paths = create_sample_documents(sample_dir, num_docs=8)
        else:
            file_paths = list(args.input_dir.glob('*'))
            file_paths = [p for p in file_paths if p.is_file() and p.suffix in ['.txt', '.pdf', '.html', '.xml']]
        
        if not file_paths:
            print("No documents found for processing!")
            return
        
        print(f"\nFound {len(file_paths)} documents to process")
        
        # Process documents
        if args.parallel:
            results, stats = batch_process_parallel(file_paths, max_workers=args.workers)
        else:
            results, stats = batch_process_sequential(file_paths)
        
        # Analyze results
        analysis = analyze_batch_results(results)
        
        # Export results
        export_batch_results(results, analysis, args.output_dir)
        
        # Performance comparison demonstration
        if args.create_samples:
            performance_comparison()
        
        print(f"\nBatch processing completed successfully!")
        print(f"Results available in: {args.output_dir.absolute()}")
        
    except Exception as e:
        logger.error(f"Error during batch processing: {e}")
        raise


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Batch ChemDataExtractor2 script for processing multiple HTML files from a papers folder.
Processes all HTML files in /home/dave/code/papers and saves results with timestamped filenames.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the ChemDataExtractor2 path
sys.path.insert(0, "/home/dave/code/ChemDataExtractor2")

from chemdataextractor import Document
from chemdataextractor.model.model import Apparatus
from chemdataextractor.model.model import Compound
from chemdataextractor.model.model import ElectrochemicalPotential
from chemdataextractor.model.model import FluorescenceLifetime
from chemdataextractor.model.model import GlassTransition
from chemdataextractor.model.model import InteratomicDistance
from chemdataextractor.model.model import IrSpectrum
from chemdataextractor.model.model import MeltingPoint
from chemdataextractor.model.model import NmrSpectrum
from chemdataextractor.model.model import QuantumYield
from chemdataextractor.model.model import UvvisSpectrum
from chemdataextractor.reader import HtmlReader

# Available models with descriptions
AVAILABLE_MODELS = {
    "compound": (Compound, "Chemical compound identification and properties"),
    "melting_point": (MeltingPoint, "Melting point measurements with compound linking"),
    "ir_spectrum": (IrSpectrum, "Infrared spectroscopy data"),
    "nmr_spectrum": (NmrSpectrum, "Nuclear magnetic resonance data"),
    "uvvis_spectrum": (UvvisSpectrum, "UV-Visible spectroscopy"),
    "apparatus": (Apparatus, "Experimental apparatus information"),
    "glass_transition": (GlassTransition, "Glass transition temperature"),
    "electrochemical_potential": (
        ElectrochemicalPotential,
        "Electrochemical measurements",
    ),
    "fluorescence_lifetime": (FluorescenceLifetime, "Fluorescence lifetime data"),
    "quantum_yield": (QuantumYield, "Quantum yield measurements"),
    "interatomic_distance": (InteratomicDistance, "Structural distance measurements"),
}

# Default recommended models for chemical synthesis papers
DEFAULT_MODELS = ["compound", "melting_point", "nmr_spectrum", "ir_spectrum"]

# Models that require BERT CRF (slower initialization)
BERT_DEPENDENT_MODELS = ["compound"]

# Input and output directories
PAPERS_DIR = Path("/home/dave/code/papers")
OUTPUT_DIR = Path("/home/dave/code/papers/outputs")


def show_available_models():
    """Display all available models with descriptions."""
    print("📊 AVAILABLE EXTRACTION MODELS:")
    print("=" * 60)

    for key, (model_class, description) in AVAILABLE_MODELS.items():
        bert_note = " (requires BERT CRF)" if key in BERT_DEPENDENT_MODELS else ""
        print(f"  {key:<20} - {description}{bert_note}")

    print(f"\n💡 Default models: {', '.join(DEFAULT_MODELS)}")
    print(
        f"⚡ Fast models (no BERT): {', '.join([k for k in AVAILABLE_MODELS if k not in BERT_DEPENDENT_MODELS])}"
    )


def parse_model_selection(model_input):
    """
    Parse user model selection input.

    Args:
        model_input (str): Comma-separated model names or 'default' or 'all' or 'fast'

    Returns:
        tuple: (list of model class objects, list of model keys, option name)
    """
    option_name = model_input.lower()

    if not model_input or model_input.lower() == "default":
        selected_keys = DEFAULT_MODELS
        option_name = "default"
    elif model_input.lower() == "all":
        selected_keys = list(AVAILABLE_MODELS.keys())
        option_name = "all"
    elif model_input.lower() == "fast":
        # Only models that don't require BERT
        selected_keys = [k for k in AVAILABLE_MODELS if k not in BERT_DEPENDENT_MODELS]
        option_name = "fast"
    else:
        # Parse comma-separated list
        selected_keys = [key.strip().lower() for key in model_input.split(",")]
        option_name = "custom"

    # Validate and get model classes
    selected_models = []
    invalid_models = []

    for key in selected_keys:
        if key in AVAILABLE_MODELS:
            model_class, _ = AVAILABLE_MODELS[key]
            selected_models.append(model_class)
        else:
            invalid_models.append(key)

    if invalid_models:
        print(f"⚠️  Warning: Unknown models ignored: {invalid_models}")

    return selected_models, selected_keys, option_name


def find_html_files(papers_dir):
    """
    Find all HTML files in the papers directory.

    Args:
        papers_dir (Path): Directory to search for HTML files

    Returns:
        list: List of Path objects for HTML files
    """
    html_files = list(papers_dir.glob("*.html"))
    return sorted(html_files)


def generate_output_filename(input_path, option_name, timestamp):
    """
    Generate timestamped output filename.

    Args:
        input_path (Path): Original HTML file path
        option_name (str): Processing option used (default, fast, all, custom)
        timestamp (str): Timestamp string

    Returns:
        str: Output filename
    """
    # Get base filename without extension
    base_name = input_path.stem
    return f"{base_name}_{option_name}_{timestamp}.json"


def extract_data_from_file(file_path, selected_models, model_keys):
    """
    Extract chemical data from a single HTML file.

    Args:
        file_path (Path): Path to the HTML file
        selected_models (list): List of model classes to use
        model_keys (list): List of model key names for organization

    Returns:
        dict: Extraction results or None if error
    """
    print(f"🔬 Processing: {file_path.name}")

    try:
        # Read the document
        with open(file_path, "rb") as f:
            doc = Document.from_file(f, readers=[HtmlReader()])
        print(f"   ✅ Loaded document with {len(doc.elements)} elements")

        # Set models on document
        doc.models = selected_models

        # Extract records
        all_records = list(doc.records)
        print(f"   📊 Found {len(all_records)} total records")

        # Organize results by type
        results = {
            "summary": {
                "total_records": len(all_records),
                "file_path": str(file_path),
                "file_name": file_path.name,
                "selected_models": model_keys,
                "extraction_models": [m.__name__ for m in selected_models],
                "processed_at": datetime.now().isoformat(),
            },
            "records_by_type": {},
            "all_records": [],
        }

        # Initialize result categories for selected models
        for key in model_keys:
            results["records_by_type"][key] = []

        # Categorize records
        for record in all_records:
            record_type = type(record).__name__
            serialized = record.serialize()
            results["all_records"].append({"type": record_type, "data": serialized})

            # Map to our key names
            type_to_key = {
                "Compound": "compound",
                "MeltingPoint": "melting_point",
                "IrSpectrum": "ir_spectrum",
                "NmrSpectrum": "nmr_spectrum",
                "UvvisSpectrum": "uvvis_spectrum",
                "Apparatus": "apparatus",
                "GlassTransition": "glass_transition",
                "ElectrochemicalPotential": "electrochemical_potential",
                "FluorescenceLifetime": "fluorescence_lifetime",
                "QuantumYield": "quantum_yield",
                "InteratomicDistance": "interatomic_distance",
            }

            key = type_to_key.get(record_type)
            if key and key in results["records_by_type"]:
                results["records_by_type"][key].append(serialized)

        # Update summary with counts
        for key in model_keys:
            count_key = f"{key}_found"
            results["summary"][count_key] = len(results["records_by_type"][key])

        return results

    except Exception as e:
        print(f"   ❌ Error processing {file_path.name}: {e}")
        return None


def save_results(results, output_path):
    """Save extraction results to JSON file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"   ❌ Error saving results: {e}")
        return False


def print_batch_summary(processed_files, failed_files, model_keys):
    """Print summary of batch processing."""
    print("\n" + "=" * 80)
    print("📋 BATCH PROCESSING SUMMARY")
    print("=" * 80)

    print(f"✅ Successfully processed: {len(processed_files)} files")
    print(f"❌ Failed to process: {len(failed_files)} files")

    if processed_files:
        print(f"\n📊 TOTAL RECORDS ACROSS ALL FILES:")
        total_counts = {}
        for key in model_keys:
            total_counts[key] = 0

        for file_path, results in processed_files:
            for key in model_keys:
                count_key = f"{key}_found"
                total_counts[key] += results["summary"].get(count_key, 0)

        for key, total_count in total_counts.items():
            if total_count > 0:
                model_class, description = AVAILABLE_MODELS[key]
                print(f"  {key:<20}: {total_count} records total")

    if failed_files:
        print(f"\n❌ Failed files:")
        for file_path in failed_files:
            print(f"  • {file_path.name}")


def main():
    """Main execution function for batch processing."""
    print("🔬 ChemDataExtractor2 - Batch Paper Processing")
    print("=" * 80)

    # Check if papers directory exists
    if not PAPERS_DIR.exists():
        print(f"❌ Papers directory not found: {PAPERS_DIR}")
        print("Please create the directory and add HTML files to process.")
        return

    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"📂 Papers directory: {PAPERS_DIR}")
    print(f"📂 Output directory: {OUTPUT_DIR}")

    # Find HTML files
    html_files = find_html_files(PAPERS_DIR)

    if not html_files:
        print(f"❌ No HTML files found in {PAPERS_DIR}")
        print("Please add HTML files to the papers directory.")
        return

    print(f"📄 Found {len(html_files)} HTML files to process:")
    for file_path in html_files:
        print(f"  • {file_path.name}")

    # Show available models
    print("\n")
    show_available_models()

    print("\n🎯 MODEL SELECTION OPTIONS:")
    print(f"  'default'  - Use recommended models: {', '.join(DEFAULT_MODELS)}")
    print("  'fast'     - Use models without BERT (faster): non-compound models")
    print("  'all'      - Use all available models")
    print("  'model1,model2' - Specify models by name (comma-separated)")
    print("  ''         - Use default models")

    # Get user input
    model_input = input(
        "\n📝 Enter model selection for batch processing (or press Enter for default): "
    ).strip()

    if not model_input:
        model_input = "default"

    # Parse model selection
    selected_models, model_keys, option_name = parse_model_selection(model_input)

    if not selected_models:
        print("❌ No valid models selected. Exiting.")
        return

    print(f"\n✅ Selected models: {', '.join(model_keys)}")

    # Show BERT warning if needed
    bert_models = [key for key in model_keys if key in BERT_DEPENDENT_MODELS]
    if bert_models:
        print(f"⏳ Note: {bert_models} require BERT CRF initialization (may take 2-3 minutes)")

    # Generate timestamp for this batch
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")

    print(f"\n🚀 Starting batch processing with timestamp: {timestamp}")
    print("=" * 80)

    # Process each file
    processed_files = []
    failed_files = []

    for i, file_path in enumerate(html_files, 1):
        print(f"\n[{i}/{len(html_files)}] Processing: {file_path.name}")

        # Extract data
        results = extract_data_from_file(file_path, selected_models, model_keys)

        if results is None:
            failed_files.append(file_path)
            continue

        # Generate output filename
        output_filename = generate_output_filename(file_path, option_name, timestamp)
        output_path = OUTPUT_DIR / output_filename

        # Save results
        if save_results(results, output_path):
            print(f"   💾 Saved to: {output_filename}")
            processed_files.append((file_path, results))
        else:
            failed_files.append(file_path)

    # Print final summary
    print_batch_summary(processed_files, failed_files, model_keys)

    if processed_files:
        print(f"\n💾 All results saved to: {OUTPUT_DIR}")
        print(f"📁 Output files use format: filename_{option_name}_{timestamp}.json")

    print("\n" + "=" * 80)
    print("✅ BATCH PROCESSING COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
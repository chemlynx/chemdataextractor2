#!/usr/bin/env python3
"""
Configurable ChemDataExtractor2 script for extracting chemical data from RSC publication.
Allows user to select which models to use for extraction.
"""

import json
import os
import sys

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
    "electrochemical_potential": (ElectrochemicalPotential, "Electrochemical measurements"),
    "fluorescence_lifetime": (FluorescenceLifetime, "Fluorescence lifetime data"),
    "quantum_yield": (QuantumYield, "Quantum yield measurements"),
    "interatomic_distance": (InteratomicDistance, "Structural distance measurements"),
}

# Default recommended models for chemical synthesis papers
DEFAULT_MODELS = ["compound", "melting_point", "nmr_spectrum", "ir_spectrum"]

# Models that require BERT CRF (slower initialization)
BERT_DEPENDENT_MODELS = ["compound"]


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
        list: List of model class objects
    """
    if not model_input or model_input.lower() == "default":
        selected_keys = DEFAULT_MODELS
    elif model_input.lower() == "all":
        selected_keys = list(AVAILABLE_MODELS.keys())
    elif model_input.lower() == "fast":
        # Only models that don't require BERT
        selected_keys = [k for k in AVAILABLE_MODELS if k not in BERT_DEPENDENT_MODELS]
    else:
        # Parse comma-separated list
        selected_keys = [key.strip().lower() for key in model_input.split(",")]

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

    return selected_models, selected_keys


def extract_configurable_data(file_path, selected_models, model_keys):
    """
    Extract chemical data using selected models.

    Args:
        file_path (str): Path to the HTML file
        selected_models (list): List of model classes to use
        model_keys (list): List of model key names for organization

    Returns:
        dict: Extraction results
    """
    print("🔬 Starting configurable ChemDataExtractor2 analysis")
    print(f"📄 File: {file_path}")
    print("=" * 80)

    # Read the document
    try:
        with open(file_path, "rb") as f:
            doc = Document.from_file(f, readers=[HtmlReader()])
        print(f"✅ Successfully loaded document with {len(doc.elements)} elements")
    except Exception as e:
        print(f"❌ Error loading document: {e}")
        return {}

    # Set models on document
    doc.models = selected_models
    model_names = [m.__name__ for m in selected_models]
    print(f"🎯 Using {len(selected_models)} selected models: {model_names}")

    # Show BERT warning if needed
    bert_models = [key for key in model_keys if key in BERT_DEPENDENT_MODELS]
    if bert_models:
        print(f"⏳ Note: {bert_models} require BERT CRF initialization (may take 2-3 minutes)")

    # Extract records
    print("\n🔍 Extracting records...")
    all_records = list(doc.records)
    print(f"📊 Found {len(all_records)} total records")

    # Organize results by type
    results = {
        "summary": {
            "total_records": len(all_records),
            "file_path": file_path,
            "selected_models": model_keys,
            "extraction_models": model_names,
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


def print_configurable_summary(results):
    """Print a summary of configurable extraction results."""
    print("\n" + "=" * 80)
    print("📋 CONFIGURABLE EXTRACTION SUMMARY")
    print("=" * 80)

    summary = results.get("summary", {})
    print(f"📄 File: {summary.get('file_path', 'Unknown')}")
    print(f"🔍 Total Records Found: {summary.get('total_records', 0)}")
    print(f"🎯 Selected Models: {', '.join(summary.get('selected_models', []))}")

    print("\n📊 RECORD BREAKDOWN:")
    records_by_type = results.get("records_by_type", {})
    for model_key, records in records_by_type.items():
        if records:  # Only show models that found data
            model_class, description = AVAILABLE_MODELS[model_key]
            print(f"  {model_key:<20}: {len(records)} records - {description}")


def print_detailed_configurable_results(results, max_items=10):
    """Print detailed results for found data."""
    print("\n" + "=" * 80)
    print("🔬 DETAILED EXTRACTION RESULTS")
    print("=" * 80)

    records_by_type = results.get("records_by_type", {})

    for model_key, records in records_by_type.items():
        if not records:
            continue

        model_class, description = AVAILABLE_MODELS[model_key]
        print(f"\n📋 {model_key.upper().replace('_', ' ')} ({len(records)} found):")

        for i, record in enumerate(records[:max_items], 1):
            # Extract the main data (skip the wrapper key)
            main_key = list(record.keys())[0]
            data = record[main_key]

            if model_key == "compound":
                names = data.get("names", [])
                labels = data.get("labels", [])
                roles = data.get("roles", [])
                print(f"  {i}. Names: {names}")
                if labels:
                    print(f"     Labels: {labels}")
                if roles:
                    print(f"     Roles: {roles}")

            elif model_key == "melting_point":
                value = data.get("value", data.get("raw_value", "N/A"))
                units = data.get("units", data.get("raw_units", "N/A"))
                compound = data.get("compound", {})
                print(f"  {i}. Value: {value} {units}")
                if compound:
                    comp_names = compound.get("Compound", {}).get("names", [])
                    if comp_names:
                        print(f"     Compound: {comp_names[0]}")

            elif model_key == "nmr_spectrum":
                nucleus = data.get("nucleus", "Unknown")
                solvent = data.get("solvent", "Unknown")
                peaks = data.get("peaks", [])
                print(f"  {i}. Nucleus: {nucleus}, Solvent: {solvent}")
                if peaks:
                    print(f"     Peaks: {len(peaks)} found")
                    for j, peak in enumerate(peaks[:3]):
                        shift = peak.get("shift", "N/A")
                        multiplicity = peak.get("multiplicity", "N/A")
                        print(f"       δ {shift} ({multiplicity})")

            else:
                # Generic display for other models
                print(f"  {i}. {data}")

        if len(records) > max_items:
            print(f"     ... and {len(records) - max_items} more {model_key} records")


def save_configurable_results(results, output_path):
    """Save extraction results to JSON file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return False


def main():
    """Main execution function with interactive model selection."""
    print("🔬 ChemDataExtractor2 - Configurable RSC Publication Extraction")
    print("=" * 80)

    # Input file path
    input_file = "/home/dave/code/ChemDataExtractor2/tests/data/D5OB00672D.html"

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return

    # Show available models
    show_available_models()

    print("\n🎯 MODEL SELECTION OPTIONS:")
    print(f"  'default'  - Use recommended models: {', '.join(DEFAULT_MODELS)}")
    print("  'fast'     - Use models without BERT (faster): non-compound models")
    print("  'all'      - Use all available models")
    print("  'model1,model2' - Specify models by name (comma-separated)")
    print("  ''         - Use default models")

    # Get user input (or use default for script execution)
    model_input = input("\n📝 Enter model selection (or press Enter for default): ").strip()

    if not model_input:
        model_input = "default"

    # Parse model selection
    selected_models, model_keys = parse_model_selection(model_input)

    if not selected_models:
        print("❌ No valid models selected. Exiting.")
        return

    print(f"\n✅ Selected models: {', '.join(model_keys)}")

    # Generate output filename based on selection
    if model_input.lower() == "default":
        output_suffix = "default"
    elif model_input.lower() == "fast":
        output_suffix = "fast"
    elif model_input.lower() == "all":
        output_suffix = "all"
    else:
        output_suffix = "custom"

    output_file = f"/home/dave/code/ChemDataExtractor2/rsc_extraction_{output_suffix}_results.json"

    # Extract data
    results = extract_configurable_data(input_file, selected_models, model_keys)

    if not results:
        print("❌ No results obtained from extraction")
        return

    # Print results
    print_configurable_summary(results)
    print_detailed_configurable_results(results)

    # Save results
    if save_configurable_results(results, output_file):
        print("\n" + "=" * 80)
        print("✅ CONFIGURABLE EXTRACTION COMPLETE!")
        print("=" * 80)
        print(f"📊 Found {results['summary']['total_records']} total records")
        print(f"💾 Results saved to: {output_file}")

        # Show key findings
        print("\n🎯 Key findings:")
        for key in model_keys:
            count_key = f"{key}_found"
            count = results["summary"].get(count_key, 0)
            if count > 0:
                model_class, description = AVAILABLE_MODELS[key]
                print(f"  • {count} {key.replace('_', ' ')} records")


if __name__ == "__main__":
    main()

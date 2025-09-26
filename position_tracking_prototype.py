#!/usr/bin/env python3
"""
Prototype for position tracking in ChemDataExtractor compound extraction.

This demonstrates how to capture token positions and document context
without modifying the core ChemDataExtractor behavior.
"""

import json
import sys
from pathlib import Path

# Add ChemDataExtractor2 to path
sys.path.insert(0, str(Path(__file__).parent))

from chemdataextractor import Document
from chemdataextractor.model.model import Compound
from chemdataextractor.reader import HtmlReader


class PositionTracker:
    """Enhanced position tracking for ChemDataExtractor compounds."""

    def __init__(self, document):
        self.document = document
        self.preprocessed_text = None
        self.sentence_map = {}
        self._build_position_maps()

    def _build_position_maps(self):
        """Build position mapping for the document."""
        # Reconstruct the preprocessed text and create sentence mapping
        text_parts = []
        current_pos = 0

        for sent_idx, sentence in enumerate(self.document.sentences):
            sentence_text = " ".join(
                token.text if hasattr(token, "text") else str(token)
                for token in sentence.tokens
            )

            # Store sentence information
            self.sentence_map[sent_idx] = {
                "text": sentence_text,
                "start_pos": current_pos,
                "end_pos": current_pos + len(sentence_text),
                "tokens": sentence.tokens,
            }

            text_parts.append(sentence_text)
            current_pos += len(sentence_text) + 1  # +1 for space between sentences

        self.preprocessed_text = " ".join(text_parts)

    def get_compound_positions(self, compound_record):
        """Extract position information for compound names."""
        positions = []
        compound_data = compound_record.serialize()

        # Get the compound data (unwrap the outer dictionary)
        if "Compound" in compound_data:
            names = compound_data["Compound"].get("names", [])
        else:
            names = []

        # Find positions of each name in the document
        for name in names:
            name_positions = self._find_name_positions(name)
            positions.extend(name_positions)

        return positions

    def _find_name_positions(self, name):
        """Find all positions of a compound name in the document."""
        positions = []

        # Search through each sentence
        for sent_idx, sent_info in self.sentence_map.items():
            sentence_text = sent_info["text"].lower()
            name_lower = name.lower()

            # Find all occurrences in this sentence
            start = 0
            while True:
                pos = sentence_text.find(name_lower, start)
                if pos == -1:
                    break

                # Calculate absolute position in preprocessed text
                abs_start = sent_info["start_pos"] + pos
                abs_end = abs_start + len(name)

                position_info = {
                    "name": name,
                    "start_pos": abs_start,
                    "end_pos": abs_end,
                    "sentence_index": sent_idx,
                    "sentence_text": (
                        sent_info["text"][:100] + "..."
                        if len(sent_info["text"]) > 100
                        else sent_info["text"]
                    ),
                    "local_start": pos,
                    "local_end": pos + len(name),
                }

                positions.append(position_info)
                start = pos + 1  # Continue searching for more occurrences

        return positions


def extract_with_positions(html_file, max_compounds=5):
    """
    Extract compounds with position information.

    This is a prototype showing how position tracking would work
    without modifying core ChemDataExtractor behavior.
    """
    print(f"🔬 Loading document: {html_file}")

    # Load document
    with open(html_file, "rb") as f:
        doc = Document.from_file(f, readers=[HtmlReader()])

    print(
        f"   Document loaded: {len(doc.elements)} elements, {len(list(doc.sentences))} sentences"
    )

    # Set up compound extraction
    doc.models = [Compound]

    # Create position tracker
    tracker = PositionTracker(doc)

    print(f"   Preprocessed text length: {len(tracker.preprocessed_text)} characters")
    print(f"   Sentence mapping: {len(tracker.sentence_map)} sentences")

    # Extract compounds
    compounds = [record for record in doc.records if isinstance(record, Compound)]
    print(f"   Found {len(compounds)} compound records")

    # Enhanced results with position information
    enhanced_results = {
        "summary": {
            "total_compounds": len(compounds),
            "document_length": len(tracker.preprocessed_text),
            "total_sentences": len(tracker.sentence_map),
            "file_path": str(html_file),
        },
        "compounds_with_positions": [],
        "_document_artifact": {
            "preprocessed_text": tracker.preprocessed_text,
            "sentence_count": len(tracker.sentence_map),
            "truncated": len(tracker.preprocessed_text)
            > 10000,  # For demo, truncate very long documents
        },
    }

    # Process each compound (limit for demo)
    for i, compound in enumerate(compounds[:max_compounds]):
        print(f"   Processing compound {i+1}/{min(len(compounds), max_compounds)}...")

        # Get standard serialization
        standard_data = compound.serialize()

        # Get position information
        positions = tracker.get_compound_positions(compound)

        # Create enhanced record
        enhanced_record = {
            "standard_data": standard_data,
            "position_metadata": {
                "positions": positions,
                "total_occurrences": len(positions),
            },
        }

        enhanced_results["compounds_with_positions"].append(enhanced_record)

    if len(compounds) > max_compounds:
        print(
            f"   Note: Showing first {max_compounds} compounds out of {len(compounds)} total"
        )

    return enhanced_results


def print_position_demo(results):
    """Print a demo of the position tracking results."""
    print("\n" + "=" * 80)
    print("📍 POSITION TRACKING PROTOTYPE RESULTS")
    print("=" * 80)

    summary = results["summary"]
    print(f"📄 Document: {summary['file_path']}")
    print(f"📊 Total compounds found: {summary['total_compounds']}")
    print(f"📝 Document length: {summary['document_length']:,} characters")
    print(f"📑 Total sentences: {summary['total_sentences']}")

    print(
        f"\n🔍 POSITION DETAILS (showing {len(results['compounds_with_positions'])} compounds):"
    )

    for i, compound in enumerate(results["compounds_with_positions"], 1):
        standard = compound["standard_data"]["Compound"]
        positions = compound["position_metadata"]["positions"]

        names = standard.get("names", [])
        labels = standard.get("labels", [])

        print(f"\n  [{i}] Compound:")
        print(f"      Names: {names}")
        if labels:
            print(f"      Labels: {labels}")

        print(f"      Positions found: {len(positions)}")

        for j, pos in enumerate(positions[:3]):  # Show first 3 positions
            print(
                f"        {j+1}. '{pos['name']}' at chars {pos['start_pos']}-{pos['end_pos']}"
            )
            print(
                f"           Sentence {pos['sentence_index']}: {pos['sentence_text']}"
            )

        if len(positions) > 3:
            print(f"        ... and {len(positions) - 3} more occurrences")


def main():
    """Demo the position tracking prototype."""
    print("🧪 ChemDataExtractor2 Position Tracking Prototype")
    print("=" * 80)

    # Use a test file - you can change this path
    test_file = Path("/home/dave/code/papers/D5OB00672D.html")

    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("Please update the test_file path to an existing HTML file.")
        return

    try:
        # Extract with position information
        results = extract_with_positions(test_file, max_compounds=3)

        # Show the results
        print_position_demo(results)

        # Save results to JSON for inspection
        output_file = "position_tracking_demo.json"

        # Create a cleaned version for JSON (truncate very long text)
        json_results = results.copy()
        if len(json_results["_document_artifact"]["preprocessed_text"]) > 5000:
            json_results["_document_artifact"]["preprocessed_text"] = (
                json_results["_document_artifact"]["preprocessed_text"][:5000]
                + f"\n\n... [TRUNCATED - full length: {len(results['_document_artifact']['preprocessed_text'])} chars]"
            )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Demo results saved to: {output_file}")

        print("\n" + "=" * 80)
        print("✅ PROTOTYPE DEMONSTRATION COMPLETE")
        print("=" * 80)
        print("This shows how position tracking can be added as an optional feature")
        print("without modifying core ChemDataExtractor behavior.")

    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

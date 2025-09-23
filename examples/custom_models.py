#!/usr/bin/env python3
"""
Custom Model Development Examples

This module demonstrates how to create custom data models for ChemDataExtractor2
to extract domain-specific chemical properties and relationships not covered
by the built-in models.

Usage:
    python custom_models.py

Requirements:
    - ChemDataExtractor2 installed
    - Understanding of model architecture
"""

import logging
from typing import Any
from typing import Dict

from chemdataextractor.doc import Document
from chemdataextractor.model import BaseModel
from chemdataextractor.model import Compound
from chemdataextractor.model.base import FloatType
from chemdataextractor.model.base import ListType
from chemdataextractor.model.base import ModelType
from chemdataextractor.model.base import StringType
from chemdataextractor.model.units import QuantityModel
from chemdataextractor.model.units.dimension import Dimension
from chemdataextractor.model.units.unit import Unit
from chemdataextractor.parse import I
from chemdataextractor.parse import Optional as Opt
from chemdataextractor.parse import R
from chemdataextractor.parse import W
from chemdataextractor.parse import join
from chemdataextractor.parse import merge
from chemdataextractor.parse.auto import AutoTableParser
from chemdataextractor.parse.template import QuantityModelTemplateParser

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Example 1: Custom Dimension and Unit for Catalytic Activity
class CatalyticActivity(Dimension):
    """Custom dimension for catalytic activity (mol/g/h)."""

    constituent_dimensions = {"amount": 1, "mass": -1, "time": -1}


class MolePerGramPerHour(Unit):
    """Unit for catalytic activity: mol/(g·h)."""

    def __init__(self):
        self.dimensions = CatalyticActivity()
        self.magnitude = 1.0
        self.powers = {"mol": 1, "g": -1, "h": -1}

    def __str__(self):
        return "mol/(g·h)"


# Example 2: Custom Quantity Model for Catalytic Activity
class CatalyticActivityModel(QuantityModel):
    """Model for extracting catalytic activity measurements."""

    dimensions = CatalyticActivity()
    specifier = StringType(
        parse_expression=(
            R("catalytic", group=0) + R("activity|performance|efficiency", group=0)
        )().add_action(join),
        required=True,
    )

    # Custom parser expressions can be added here
    parsers = [
        QuantityModelTemplateParser(),
        AutoTableParser(),
    ]


# Example 3: Custom Property Model for Photoluminescence
class PhotoluminescenceModel(BaseModel):
    """Model for photoluminescence properties."""

    compound = ModelType(Compound)
    excitation_wavelength = FloatType(
        parse_expression=(
            (I("λ") + I("ex") | I("excitation"))
            + Opt(I("wavelength") | I("λ"))
            + Opt(W("=") | W("at") | W(":"))
            + R(r"\d+\.?\d*")
            + (I("nm") | I("nanometer"))
        )().add_action(merge),
        contextual=True,
    )
    emission_wavelength = FloatType(
        parse_expression=(
            (I("λ") + I("em") | I("emission"))
            + Opt(I("wavelength") | I("λ"))
            + Opt(W("=") | W("at") | W(":"))
            + R(r"\d+\.?\d*")
            + (I("nm") | I("nanometer"))
        )().add_action(merge),
        contextual=True,
    )
    quantum_yield = FloatType(
        parse_expression=(
            (I("quantum") + I("yield") | I("QY") | I("Φ"))
            + Opt(W("=") | W("of") | W(":"))
            + R(r"0?\.\d+|\d+\.?\d*%?")
        )().add_action(merge),
        contextual=True,
    )
    lifetime = FloatType(
        parse_expression=(
            (I("lifetime") | I("τ"))
            + Opt(W("=") | W("of") | W(":"))
            + R(r"\d+\.?\d*")
            + (I("ns") | I("μs") | I("ms") | I("nanosecond") | I("microsecond"))
        )().add_action(merge),
        contextual=True,
    )
    solvent = StringType(
        parse_expression=(
            I("in")
            + (
                I("water")
                | I("methanol")
                | I("ethanol")
                | I("acetonitrile")
                | I("dichloromethane")
                | I("chloroform")
                | I("toluene")
                | I("DMSO")
            )
        )().add_action(join),
        contextual=True,
    )


# Example 4: Complex Nested Model for Electrochemical Properties
class RedoxPotential(BaseModel):
    """Model for individual redox potentials."""

    potential = FloatType(
        parse_expression=(
            Opt(I("E") + R(r"\d*/\d*") + Opt("°")) + Opt(W("=")) + R(r"-?\d+\.?\d*") + I("V")
        )().add_action(merge)
    )
    assignment = StringType(
        parse_expression=(
            I("oxidation")
            | I("reduction")
            | I("ox")
            | I("red")
            | R(r"M\+?/?M\d*\+?")
            | R(r"L/?L\+")
        )().add_action(join)
    )
    reversible = StringType(
        parse_expression=(
            I("reversible") | I("irreversible") | I("quasi-reversible") | I("rev") | I("irrev")
        )().add_action(join)
    )


class ElectrochemicalModel(BaseModel):
    """Model for comprehensive electrochemical data."""

    compound = ModelType(Compound)
    technique = StringType(
        parse_expression=(
            I("CV")
            | I("cyclic") + I("voltammetry")
            | I("DPV")
            | I("differential") + I("pulse") + I("voltammetry")
            | I("square") + I("wave") + I("voltammetry")
        )().add_action(join),
        required=True,
    )
    solvent = StringType(
        parse_expression=(
            I("in")
            + (
                I("acetonitrile")
                | I("DMF")
                | I("DMSO")
                | I("dichloromethane")
                | I("water")
                | I("methanol")
                | R(r"CH\d?Cl\d?")
            )
        )().add_action(join)
    )
    electrolyte = StringType(
        parse_expression=(
            R(r"\d+\.?\d*")
            + I("M")
            + (
                I("TBAPF6")
                | I("TBABF4")
                | I("LiClO4")
                | I("KCl")
                | R(r"[A-Z][a-z]?\d*[A-Z][a-z]?\d*")
            )
        )().add_action(join)
    )
    redox_potentials = ListType(ModelType(RedoxPotential))
    scan_rate = FloatType(
        parse_expression=(
            I("scan") + I("rate") + Opt(W("=") | W("of")) + R(r"\d+\.?\d*") + (I("mV/s") | I("V/s"))
        )().add_action(merge)
    )


# Example 5: Template-Based Model for Crystal Structure Data
class CrystalStructureModel(BaseModel):
    """Model for crystal structure information."""

    compound = ModelType(Compound)
    space_group = StringType(
        parse_expression=(
            (I("space") + I("group") | I("S.G."))
            + Opt(W(":") | W("="))
            + R(r"[PCIFR][1-6]?[a-z]*/?[a-z]*")
        )().add_action(merge)
    )
    crystal_system = StringType(
        parse_expression=(
            (I("crystal") + I("system") | I("system"))
            + Opt(W(":") | W("="))
            + (
                I("cubic")
                | I("tetragonal")
                | I("orthorhombic")
                | I("hexagonal")
                | I("trigonal")
                | I("monoclinic")
                | I("triclinic")
            )
        )().add_action(join)
    )
    unit_cell_a = FloatType(
        parse_expression=(I("a") + W("=") + R(r"\d+\.?\d*") + I("Å"))().add_action(merge)
    )
    unit_cell_b = FloatType(
        parse_expression=(I("b") + W("=") + R(r"\d+\.?\d*") + I("Å"))().add_action(merge)
    )
    unit_cell_c = FloatType(
        parse_expression=(I("c") + W("=") + R(r"\d+\.?\d*") + I("Å"))().add_action(merge)
    )
    density = FloatType(
        parse_expression=(
            (I("density") | I("ρ")) + Opt(W("=")) + R(r"\d+\.?\d*") + I("g/cm3")
        )().add_action(merge)
    )


def test_catalytic_activity_extraction():
    """Test custom catalytic activity model."""
    print("=== Testing Catalytic Activity Extraction ===")

    text = """
    The platinum catalyst showed excellent catalytic activity of 145.2 mol/(g·h)
    for the hydrogenation reaction at 200°C and 10 bar pressure. The palladium
    catalyst exhibited lower catalytic performance of 89.7 mol/(g·h) under
    similar conditions.
    """

    doc = Document(text)

    # Extract catalytic activity records
    activity_records = []
    for record in doc.records:
        if isinstance(record, CatalyticActivityModel):
            activity_records.append(record)

    print(f"Found {len(activity_records)} catalytic activity records")

    for i, record in enumerate(activity_records, 1):
        print(f"\nCatalytic Activity {i}:")
        if record.value:
            print(f"  Value: {record.value}")
        if record.units:
            print(f"  Units: {record.units}")
        if record.specifier:
            print(f"  Specifier: {record.specifier}")

    return activity_records


def test_photoluminescence_extraction():
    """Test custom photoluminescence model."""
    print("\n=== Testing Photoluminescence Extraction ===")

    text = """
    The quantum dots showed strong photoluminescence with excitation wavelength
    at 380 nm and emission wavelength at 520 nm. The quantum yield was 0.85 in
    toluene with a lifetime of 12.4 ns. In water, the quantum yield decreased
    to 0.42 and lifetime to 8.7 ns.
    """

    doc = Document(text)

    # Register custom model for parsing
    # Note: In actual usage, you would register this globally or in a configuration

    # Extract photoluminescence records
    pl_records = []
    for record in doc.records:
        if isinstance(record, PhotoluminescenceModel):
            pl_records.append(record)

    print(f"Found {len(pl_records)} photoluminescence records")

    for i, record in enumerate(pl_records, 1):
        print(f"\nPhotoluminescence {i}:")
        for field_name in [
            "excitation_wavelength",
            "emission_wavelength",
            "quantum_yield",
            "lifetime",
            "solvent",
        ]:
            value = getattr(record, field_name)
            if value:
                print(f"  {field_name.replace('_', ' ').title()}: {value}")

    return pl_records


def test_electrochemical_extraction():
    """Test complex electrochemical model."""
    print("\n=== Testing Electrochemical Data Extraction ===")

    text = """
    Cyclic voltammetry of the ruthenium complex in acetonitrile with 0.1 M TBAPF6
    showed a reversible oxidation at E1/2 = +0.85 V and an irreversible reduction
    at -1.25 V vs SCE. The scan rate was 100 mV/s. DPV confirmed the redox potentials.
    """

    doc = Document(text)

    # Extract electrochemical records
    ec_records = []
    for record in doc.records:
        if isinstance(record, ElectrochemicalModel):
            ec_records.append(record)

    print(f"Found {len(ec_records)} electrochemical records")

    for i, record in enumerate(ec_records, 1):
        print(f"\nElectrochemical Data {i}:")
        for field_name in ["technique", "solvent", "electrolyte", "scan_rate"]:
            value = getattr(record, field_name)
            if value:
                print(f"  {field_name.replace('_', ' ').title()}: {value}")

        if record.redox_potentials:
            print("  Redox Potentials:")
            for j, redox in enumerate(record.redox_potentials, 1):
                print(
                    f"    {j}. Potential: {redox.potential}, "
                    f"Assignment: {redox.assignment}, "
                    f"Reversible: {redox.reversible}"
                )

    return ec_records


def test_crystal_structure_extraction():
    """Test crystal structure model."""
    print("\n=== Testing Crystal Structure Extraction ===")

    text = """
    X-ray crystallography revealed that compound 1 crystallizes in the monoclinic
    crystal system with space group P21/c. Unit cell parameters: a = 10.456 Å,
    b = 15.234 Å, c = 8.932 Å. The calculated density is 1.524 g/cm3.
    """

    doc = Document(text)

    # Extract crystal structure records
    cs_records = []
    for record in doc.records:
        if isinstance(record, CrystalStructureModel):
            cs_records.append(record)

    print(f"Found {len(cs_records)} crystal structure records")

    for i, record in enumerate(cs_records, 1):
        print(f"\nCrystal Structure {i}:")
        fields = [
            "space_group",
            "crystal_system",
            "unit_cell_a",
            "unit_cell_b",
            "unit_cell_c",
            "density",
        ]
        for field_name in fields:
            value = getattr(record, field_name)
            if value:
                print(f"  {field_name.replace('_', ' ').title()}: {value}")

    return cs_records


def demonstrate_model_serialization():
    """Demonstrate how to serialize custom models."""
    print("\n=== Custom Model Serialization ===")

    # Create a mock photoluminescence record
    pl_record = PhotoluminescenceModel()
    pl_record.excitation_wavelength = 380.0
    pl_record.emission_wavelength = 520.0
    pl_record.quantum_yield = 0.85
    pl_record.lifetime = 12.4
    pl_record.solvent = "toluene"

    # Serialize to dictionary
    if hasattr(pl_record, "serialize"):
        serialized = pl_record.serialize()
        print("Serialized Photoluminescence Record:")
        for key, value in serialized.items():
            if value is not None:
                print(f"  {key}: {value}")
    else:
        print("Serialization method not available")

    return pl_record


def create_model_validation_system():
    """Create a validation system for custom models."""
    print("\n=== Model Validation System ===")

    def validate_photoluminescence(record: PhotoluminescenceModel) -> Dict[str, Any]:
        """Validate photoluminescence data."""
        validation = {"valid": True, "warnings": [], "errors": []}

        # Check wavelength ranges
        if record.excitation_wavelength:
            if not (200 <= record.excitation_wavelength <= 800):
                validation["warnings"].append(
                    f"Unusual excitation wavelength: {record.excitation_wavelength} nm"
                )

        if record.emission_wavelength:
            if not (250 <= record.emission_wavelength <= 900):
                validation["warnings"].append(
                    f"Unusual emission wavelength: {record.emission_wavelength} nm"
                )

        # Check quantum yield range
        if record.quantum_yield:
            if not (0 <= record.quantum_yield <= 1):
                validation["errors"].append(f"Invalid quantum yield: {record.quantum_yield}")
                validation["valid"] = False

        # Check lifetime range
        if record.lifetime:
            if record.lifetime < 0:
                validation["errors"].append(f"Negative lifetime: {record.lifetime}")
                validation["valid"] = False

        return validation

    # Test validation
    test_record = PhotoluminescenceModel()
    test_record.excitation_wavelength = 380.0
    test_record.emission_wavelength = 1200.0  # Unusual value
    test_record.quantum_yield = 1.5  # Invalid value
    test_record.lifetime = -5.0  # Invalid value

    validation_result = validate_photoluminescence(test_record)

    print("Validation Results:")
    print(f"  Valid: {validation_result['valid']}")
    if validation_result["warnings"]:
        print("  Warnings:")
        for warning in validation_result["warnings"]:
            print(f"    - {warning}")
    if validation_result["errors"]:
        print("  Errors:")
        for error in validation_result["errors"]:
            print(f"    - {error}")

    return validation_result


def export_custom_model_schema():
    """Export schema information for custom models."""
    print("\n=== Custom Model Schema Export ===")

    models = [
        CatalyticActivityModel,
        PhotoluminescenceModel,
        ElectrochemicalModel,
        CrystalStructureModel,
    ]

    schema_info = {}

    for model in models:
        model_name = model.__name__
        schema_info[model_name] = {
            "fields": {},
            "description": model.__doc__ or "No description available",
        }

        # Extract field information
        if hasattr(model, "fields"):
            for field_name, field_obj in model.fields.items():
                schema_info[model_name]["fields"][field_name] = {
                    "type": type(field_obj).__name__,
                    "required": getattr(field_obj, "required", False),
                    "contextual": getattr(field_obj, "contextual", False),
                }

    print("Custom Model Schema:")
    for model_name, info in schema_info.items():
        print(f"\n{model_name}:")
        print(f"  Description: {info['description']}")
        print("  Fields:")
        for field_name, field_info in info["fields"].items():
            print(
                f"    {field_name}: {field_info['type']} "
                f"(required: {field_info['required']}, "
                f"contextual: {field_info['contextual']})"
            )

    return schema_info


def main():
    """Run all custom model examples."""
    print("ChemDataExtractor2 - Custom Model Development Examples")
    print("=" * 60)

    try:
        # Test individual custom models
        activity_records = test_catalytic_activity_extraction()
        pl_records = test_photoluminescence_extraction()
        ec_records = test_electrochemical_extraction()
        cs_records = test_crystal_structure_extraction()

        # Demonstrate advanced features
        demonstrate_model_serialization()
        create_model_validation_system()
        export_custom_model_schema()

        print("\n" + "=" * 60)
        print("Custom model development examples completed successfully!")
        print("Key takeaways:")
        print("- Custom dimensions and units can be created for specialized quantities")
        print("- Complex nested models enable sophisticated data extraction")
        print("- Parse expressions provide fine-grained control over extraction")
        print("- Validation systems ensure data quality")
        print("- Schema export facilitates model documentation and reuse")

    except Exception as e:
        logger.error(f"Error during custom model examples: {e}")
        raise


if __name__ == "__main__":
    main()

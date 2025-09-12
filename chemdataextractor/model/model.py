"""
Model classes for physical properties.

This module provides concrete implementations of chemical models for extracting
and representing various types of chemical data from scientific literature.
Each model corresponds to a specific type of chemical property or measurement.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

if TYPE_CHECKING:
    from ..typing import Self

from ..model.units.quantity_model import DimensionlessModel
from ..parse.actions import join
from ..parse.actions import merge
from ..parse.apparatus import ApparatusParser
from ..parse.auto import AutoSentenceParser
from ..parse.auto import AutoTableParser
from ..parse.cem import ChemicalLabelParser
from ..parse.cem import CompoundHeadingParser
from ..parse.cem import CompoundParser
from ..parse.cem import CompoundTableParser
from ..parse.cem import names_only
from ..parse.cem import roles_only
from ..parse.elements import Group
from ..parse.elements import I
from ..parse.elements import NoMatch
from ..parse.elements import R
from ..parse.elements import W
from ..parse.ir import IrParser
from ..parse.mp_new import MpParser
from ..parse.nmr import NmrParser
from ..parse.tg import TgParser
from ..parse.uvvis import UvvisParser
from .base import BaseModel
from .base import ListType
from .base import ModelType
from .base import SetType
from .base import StringType
from .units.length import LengthModel
from .units.temperature import TemperatureModel

log = logging.getLogger(__name__)


class Compound(BaseModel):
    """Model for chemical compound identification and properties.

    Represents a chemical compound with names, labels, and roles extracted
    from scientific text. Supports merging of compound information from
    different sources within a document.

    Attributes:
        names: Set[str] - Chemical names for this compound
        labels: Set[str] - Reference labels (e.g., "1", "2a") for this compound
        roles: Set[str] - Chemical roles (e.g., "catalyst", "product")
    """

    names = SetType(StringType(), parse_expression=names_only, updatable=True)
    labels = SetType(StringType(), parse_expression=NoMatch(), updatable=True)
    roles = SetType(StringType(), parse_expression=roles_only, updatable=True)
    parsers = [
        CompoundParser(),
        CompoundHeadingParser(),
        ChemicalLabelParser(),
        CompoundTableParser(),
    ]
    # parsers = [CompoundParser(), CompoundHeadingParser(), ChemicalLabelParser()]
    # parsers = [CompoundParser()]

    def merge(self, other: Compound) -> Self:
        """Merge data from another Compound into this Compound.

        Args:
            other: Compound - The compound to merge data from

        Returns:
            Self - This compound instance with merged data
        """
        log.debug("Merging: %s and %s" % (self.serialize(), other.serialize()))
        if type(other) is not type(self):
            return self
        for k in self.keys():
            if other[k] is not None:
                if self[k] is not None:
                    for new_item in other[k]:
                        if new_item not in self[k]:
                            self[k].add(new_item)
        log.debug("Result: %s" % self.serialize())
        return self

    @property
    def is_unidentified(self) -> bool:
        """Check if this compound has no identifying information.

        Returns:
            bool - True if compound has no names or labels
        """
        if not self.names and not self.labels:
            return True
        return False

    @property
    def is_id_only(self) -> bool:
        """Check if this compound only contains identifier information.

        Returns:
            bool - True if only names, labels, or roles are present
        """
        for key, value in self.items():
            if key not in {"names", "labels", "roles"} and value:
                return False
        if self.names or self.labels:
            return True
        return False

    @classmethod
    def update(cls, definitions: List[Dict[str, Any]], strict: bool = True) -> None:
        """Update the Compound labels parse expression.

        Args:
            definitions: List[Dict[str, Any]] - List of definition dictionaries
            strict: bool - Whether to use strict word matching (default: True)
        """
        log.debug("Updating Compound")
        for definition in definitions:
            label = definition["label"]
            if strict:
                new_label_expression = Group(W(label)("labels"))
            else:
                new_label_expression = Group(I(label)("labels"))
            if not cls.labels.parse_expression:
                cls.labels.parse_expression = new_label_expression
            else:
                cls.labels.parse_expression = (
                    cls.labels.parse_expression | new_label_expression
                )
        return

    def construct_label_expression(self, label: str) -> Any:
        """Construct a parse expression for a compound label.

        Args:
            label: str - The label text to create an expression for

        Returns:
            Parse expression for matching the label
        """
        return W(label)("labels")


class Apparatus(BaseModel):
    """Model for analytical apparatus/instrument information.

    Represents laboratory equipment and instrumentation details
    used in chemical measurements and analyses.

    Attributes:
        name: str - Name or model of the analytical apparatus
    """

    name = StringType()
    parsers = [ApparatusParser()]


class UvvisPeak(BaseModel):
    """Model for individual UV-Vis spectroscopy peaks.

    Represents a single absorption peak in UV-Vis spectroscopy data,
    including wavelength, extinction coefficient, and peak characteristics.

    Attributes:
        value: str - Peak wavelength value
        units: str - Wavelength units (contextual)
        extinction: str - Extinction coefficient value
        extinction_units: str - Extinction coefficient units (contextual)
        shape: str - Peak shape description (e.g., shoulder, broad)
    """

    #: Peak value, i.e. wavelength
    value = StringType()
    #: Peak value units
    units = StringType(contextual=True)
    # Extinction value
    extinction = StringType()
    # Extinction units
    extinction_units = StringType(contextual=True)
    # Peak shape information (e.g. shoulder, broad)
    shape = StringType()


class UvvisSpectrum(BaseModel):
    """Model for complete UV-Vis spectroscopy measurements.

    Represents a full UV-Vis spectrum with experimental conditions,
    apparatus information, and associated peaks.

    Attributes:
        solvent: str - Solvent used (contextual)
        temperature: str - Measurement temperature (contextual)
        temperature_units: str - Temperature units (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        apparatus: Apparatus - Instrument used (contextual)
        peaks: List[UvvisPeak] - List of spectral peaks
        compound: Compound - Associated chemical compound
    """

    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(UvvisPeak))
    compound = ModelType(Compound)
    parsers = [UvvisParser()]


class IrPeak(BaseModel):
    """Model for individual IR spectroscopy peaks.

    Represents a single absorption peak in IR spectroscopy data,
    including frequency, intensity, and bond assignment.

    Attributes:
        value: str - Peak frequency/wavenumber value
        units: str - Frequency units (contextual)
        strength: str - Peak intensity or strength
        bond: str - Bond assignment for this peak
    """

    value = StringType()
    units = StringType(contextual=True)
    strength = StringType()
    bond = StringType()


class IrSpectrum(BaseModel):
    """Model for complete IR spectroscopy measurements.

    Represents a full IR spectrum with experimental conditions,
    apparatus information, and associated peaks.

    Attributes:
        solvent: str - Solvent used (contextual)
        temperature: str - Measurement temperature (contextual)
        temperature_units: str - Temperature units (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        apparatus: Apparatus - Instrument used (contextual)
        peaks: List[IrPeak] - List of spectral peaks
        compound: Compound - Associated chemical compound
    """

    solvent = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(IrPeak))
    compound = ModelType(Compound)
    parsers = [IrParser()]


class NmrPeak(BaseModel):
    """Model for individual NMR spectroscopy peaks.

    Represents a single peak in NMR spectroscopy data with chemical shift,
    multiplicity, coupling information, and structural assignment.

    Attributes:
        shift: str - Chemical shift value
        intensity: str - Peak intensity or integration
        multiplicity: str - Peak splitting pattern (s, d, t, q, etc.)
        coupling: str - Coupling constant value
        coupling_units: str - Coupling constant units (contextual)
        number: str - Number of protons for this peak
        assignment: str - Structural assignment for this peak
    """

    shift = StringType()
    intensity = StringType()
    multiplicity = StringType()
    coupling = StringType()
    coupling_units = StringType(contextual=True)
    number = StringType()
    assignment = StringType()


class NmrSpectrum(BaseModel):
    """Model for complete NMR spectroscopy measurements.

    Represents a full NMR spectrum with experimental conditions,
    nucleus type, apparatus information, and associated peaks.

    Attributes:
        nucleus: str - NMR nucleus (1H, 13C, etc.) (contextual)
        solvent: str - NMR solvent used (contextual)
        frequency: str - Spectrometer frequency (contextual)
        frequency_units: str - Frequency units (contextual)
        standard: str - Chemical shift reference (contextual)
        temperature: str - Measurement temperature (contextual)
        temperature_units: str - Temperature units (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        apparatus: Apparatus - NMR spectrometer used (contextual)
        peaks: List[NmrPeak] - List of NMR peaks
        compound: Compound - Associated chemical compound
    """

    nucleus = StringType(contextual=True)
    solvent = StringType(contextual=True)
    frequency = StringType(contextual=True)
    frequency_units = StringType(contextual=True)
    standard = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    peaks = ListType(ModelType(NmrPeak))
    compound = ModelType(Compound)
    parsers = [NmrParser()]


class MeltingPoint(TemperatureModel):
    """Model for melting point measurements.

    Represents melting point data with experimental conditions
    and associated compound information. Inherits temperature
    handling from TemperatureModel.

    Attributes:
        solvent: str - Solvent used (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        apparatus: Apparatus - Measurement apparatus (contextual)
        compound: Compound - Associated chemical compound (contextual)
    """

    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)
    compound = ModelType(Compound, contextual=True)
    parsers = [MpParser()]


class GlassTransition(BaseModel):
    """Model for glass transition temperature measurements.

    Represents glass transition temperature (Tg) data with measurement
    method and experimental conditions.

    Attributes:
        value: str - Glass transition temperature value
        units: str - Temperature units (contextual)
        method: str - Measurement method used (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        compound: Compound - Associated chemical compound
    """

    value = StringType()
    units = StringType(contextual=True)
    method = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    compound = ModelType(Compound)
    parsers = [TgParser()]


class QuantumYield(BaseModel):
    """Model for quantum yield measurements.

    Represents photoluminescence quantum yield data with experimental
    conditions, standards, and measurement parameters.

    Attributes:
        value: str - Quantum yield value
        units: str - Units (typically dimensionless) (contextual)
        solvent: str - Solvent used (contextual)
        type: str - Type of quantum yield measurement (contextual)
        standard: str - Reference standard used (contextual)
        standard_value: str - Standard quantum yield value (contextual)
        standard_solvent: str - Standard solvent (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        temperature: str - Measurement temperature (contextual)
        temperature_units: str - Temperature units (contextual)
        apparatus: Apparatus - Measurement apparatus (contextual)
    """

    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    type = StringType(contextual=True)
    standard = StringType(contextual=True)
    standard_value = StringType(contextual=True)
    standard_solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class FluorescenceLifetime(BaseModel):
    """Model for fluorescence lifetime measurements.

    Represents fluorescence decay time measurements with experimental
    conditions and apparatus information.

    Attributes:
        value: str - Fluorescence lifetime value
        units: str - Time units (contextual)
        solvent: str - Solvent used (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        temperature: str - Measurement temperature (contextual)
        temperature_units: str - Temperature units (contextual)
        apparatus: Apparatus - Measurement apparatus (contextual)
    """

    value = StringType()
    units = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class ElectrochemicalPotential(BaseModel):
    """Model for electrochemical potential measurements.

    Represents oxidation or reduction potentials from cyclic voltammetry
    and other electrochemical techniques.

    Attributes:
        value: str - Potential value
        units: str - Potential units (contextual)
        type: str - Type of potential (oxidation/reduction) (contextual)
        solvent: str - Solvent/electrolyte used (contextual)
        concentration: str - Sample concentration (contextual)
        concentration_units: str - Concentration units (contextual)
        temperature: str - Measurement temperature (contextual)
        temperature_units: str - Temperature units (contextual)
        apparatus: Apparatus - Electrochemical apparatus (contextual)
    """

    value = StringType()
    units = StringType(contextual=True)
    type = StringType(contextual=True)
    solvent = StringType(contextual=True)
    concentration = StringType(contextual=True)
    concentration_units = StringType(contextual=True)
    temperature = StringType(contextual=True)
    temperature_units = StringType(contextual=True)
    apparatus = ModelType(Apparatus, contextual=True)


class NeelTemperature(TemperatureModel):
    """Model for Néel temperature measurements.

    Represents the temperature at which antiferromagnetic materials
    lose their magnetic ordering. Inherits temperature handling
    from TemperatureModel.

    Attributes:
        specifier: str - Temperature specifier (required, non-contextual)
        compound: Compound - Associated chemical compound (optional)
    """

    # expression = (I('T')+I('N')).add_action(merge)
    expression = I("TN")
    # specifier = I('TN')
    specifier = StringType(
        parse_expression=expression, required=True, contextual=False, updatable=False
    )
    compound = ModelType(Compound, required=False, contextual=False)


class CurieTemperature(TemperatureModel):
    """Model for Curie temperature measurements.

    Represents the temperature at which ferromagnetic materials
    lose their permanent magnetic properties. Inherits temperature
    handling from TemperatureModel.

    Attributes:
        specifier: str - Temperature specifier (required, non-contextual)
        compound: Compound - Associated chemical compound (optional)
    """

    # expression = (I('T') + I('C')).add_action(merge)
    expression = ((I("Curie") + R("^temperature(s)?$")) | R(r"T[Cc]\d?")).add_action(
        join
    )
    specifier = StringType(
        parse_expression=expression, required=True, contextual=False, updatable=False
    )
    compound = ModelType(Compound, required=False, contextual=False)


class InteratomicDistance(LengthModel):
    """Model for interatomic distance measurements.

    Represents bond lengths and atomic distances with species
    identification. Inherits length handling from LengthModel.

    Attributes:
        specifier: str - Distance specifier (optional, contextual)
        species: str - Element pair specification (required, non-contextual)
        compound: Compound - Associated chemical compound (required, contextual)
        another_label: str - Additional label field (optional, non-contextual)
    """

    specifier_expression = (R("^bond$") + R("^distance")).add_action(merge)
    specifier = StringType(
        parse_expression=specifier_expression, required=False, contextual=True
    )
    rij_label = R(
        r"^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$"
    )
    species = StringType(parse_expression=rij_label, required=True, contextual=False)
    compound = ModelType(Compound, required=True, contextual=True)
    another_label = StringType(
        parse_expression=R("^adgahg$"), required=False, contextual=False
    )


class CoordinationNumber(DimensionlessModel):
    """Model for coordination number measurements.

    Represents the number of atoms coordinated to a central atom
    in a chemical structure. Inherits dimensionless quantity handling.

    Note:
        Labels like NTi-O will not work with this parser - requires space
        between the label and specifier.

    Attributes:
        specifier: str - Coordination number specifier (required, contextual)
        cn_label: str - Element coordination label (required, contextual)
        compound: Compound - Associated chemical compound (required, contextual)
    """

    # something like NTi-O will not work with this, only work if there is space between the label and specifier
    coordination_number_label = R(
        r"^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$"
    )
    # specifier = (R('^(N|n|k)$') | (I('Pair') + I('ij')).add_action(merge)
    specifier_expression = R("^(N|n|k)$")
    specifier = StringType(
        parse_expression=specifier_expression, required=True, contextual=True
    )

    cn_label = StringType(
        parse_expression=coordination_number_label, required=True, contextual=True
    )
    compound = ModelType(Compound, required=True, contextual=True)


class CNLabel(BaseModel):
    """Model for coordination number labels.

    Separate model for testing automated parsing of coordination
    number information that are not quantities.

    Attributes:
        label_Juraj: str - Coordination number label for elements
        compound: Compound - Associated chemical compound (optional)
    """

    # separate model to test automated parsing for stuff that are not quantities
    coordination_number_label = R(
        r"^((X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr)\-?(X|Ac|Ag|Al|Am|Ar|As|At|Au|B|Ba|Be|Bh|Bi|Bk|Br|C|Ca|Cd|Ce|Cf|Cl|Cm|Cn|Co|Cr|Cs|Cu|Db|Ds|Dy|Er|Es|Eu|F|Fe|Fl|Fm|Fr|Ga|Gd|Ge|H|He|Hf|Hg|Ho|Hs|I|In|Ir|K|Kr|La|Li|Lr|Lu|Lv|Mc|Md|Mg|Mn|Mo|Mt|N|Na|Nb|Nd|Ne|Nh|Ni|No|Np|O|Og|Os|P|Pa|Pb|Pd|Pm|Po|Pr|Pt|Pu|Ra|Rb|Re|Rf|Rg|Rh|Rn|Ru|S|Sb|Sc|Se|Sg|Si|Sm|Sn|Sr|Ta|Tb|Tc|Te|Th|Ti|Tl|Tm|Ts|U|V|W|Xe|Y|Yb|Zn|Zr))$"
    )
    specifier = (I("Pair") + I("ij")).add_action(merge)
    label_Juraj = StringType(parse_expression=coordination_number_label)
    compound = ModelType(Compound, required=False)
    parsers = [AutoSentenceParser(), AutoTableParser()]

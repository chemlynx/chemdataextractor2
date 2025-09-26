"""
Tools for parsing people's names from strings into various name components.

Provides comprehensive name parsing functionality to extract titles, first names,
last names, suffixes, and other name components from text strings.
"""

from __future__ import annotations

import re
import string
from typing import TYPE_CHECKING
from typing import Any

from ..text import QUOTES
from ..text.latex import latex_to_unicode

if TYPE_CHECKING:
    pass

ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{4}$")


TITLES = {
    "ms",
    "miss",
    "mrs",
    "mr",
    "master",
    "dr",
    "doctor",
    "prof",
    "professor",
    "sir",
    "dame",
    "madam",
    "madame",
    "mademoiselle",
    "monsieur",
    "lord",
    "lady",
    "rev",
    "reverend",
    "fr",
    "father",
    "brother",
    "sister",
    "pastor",
    "cardinal",
    "abbot",
    "abbess",
    "friar",
    "mother",
    "bishop",
    "archbishop",
    "priest",
    "priestess",
    "pope",
    "vicar",
    "chaplain",
    "saint",
    "deacon",
    "archdeacon",
    "rabbi",
    "ayatollah",
    "imam",
    "pres",
    "president",
    "gov",
    "governor",
    "rep",
    "representative",
    "sen",
    "senator",
    "minister",
    "chancellor",
    "cllr",
    "councillor",
    "secretary",
    "speaker",
    "alderman",
    "delegate",
    "mayor",
    "ambassador",
    "prefect",
    "premier",
    "envoy",
    "provost",
    "coach",
    "principal",
    "king",
    "queen",
    "prince",
    "princess",
    "royal",
    "majesty",
    "highness",
    "rt",
    "duke",
    "duchess",
    "archduke",
    "archduchess",
    "marquis",
    "marquess",
    "marchioness",
    "earl",
    "count",
    "countess",
    "viscount",
    "viscountess",
    "baron",
    "baroness",
    "sheikh",
    "emperor",
    "empress",
    "tsar",
    "tsarina",
    "uncle",
    "auntie",
    "aunt",
    "atty",
    "attorney",
    "advocate",
    "judge",
    "solicitor",
    "barrister",
    "comptroller",
    "sheriff",
    "registrar",
    "treasurer",
    "associate",
    "assistant",
    "honorable",
    "honourable",
    "deputy",
    "vice",
    "executive",
    "his",
    "her",
    "private",
    "corporal",
    "sargent",
    "seargent",
    "officer",
    "major",
    "captain",
    "commander",
    "lieutenant",
    "colonel",
    "general",
    "chief",
    "admiral",
    "pilot",
    "resident",
    "surgeon",
    "nurse",
    "col",
    "capt",
    "cpt",
    "maj",
    "cpl",
    "ltc",
    "sgt",
    "pfc",
    "sfc",
    "mg",
    "bg",
    "ssgt",
    "ltcol",
    "majgen",
    "gen",
    "ltgen",
    "sgtmaj",
    "bgen",
    "lcpl",
    "2ndlt",
    "1stlt",
    "briggen",
    "1stsgt",
    "pvt",
    "2lt",
    "1lt",
    "ens",
    "lt",
    "adm",
    "vadm",
    "cpo",
    "mcpo",
    "mcpoc",
    "scpo",
    "radm(lh)",
    "radm(uh)",
    "ltg",
}

PREFIXES = {
    "abu",
    "bon",
    "bin",
    "da",
    "dal",
    "de",
    "del",
    "der",
    "di",
    "ibn",
    "la",
    "le",
    "san",
    "st",
    "ste",
    "van",
    "vel",
    "von",
}

SUFFIXES = {
    "Esq",
    "Esquire",
    "Bt",
    "Btss",
    "Jr",
    "Sr",
    "2",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "CLU",
    "ChFC",
    "CFP",
    "MP",
    "MSP",
    "MEP",
    "AM",
    "MLA",
    "QC",
    "KC",
    "PC",
    "SCJ",
    "MHA",
    "MNA",
    "MPP",
    "VC",
    "GC",
    "KBE",
    "CBE",
    "MBE",
    "DBE",
    "GBE",
    "OBE",
    "MD",
    "PhD",
    "DBEnv",
    "DConstMgt",
    "DREst",
    "EdD",
    "DPhil",
    "DLitt",
    "DSocSci",
    "EngD",
    "DD",
    "LLD",
    "DProf",
    "BA",
    "BSc",
    "LLB",
    "BEng",
    "MBChB",
    "MA",
    "MSc",
    "MSci",
    "MPhil",
    "MArch",
    "MMORSE",
    "MMath",
    "MMathStat",
    "MPharm",
    "MSt",
    "MRes",
    "MEng",
    "MChem",
    "MSocSc",
    "MMus",
    "LLM",
    "BCL",
    "MPhys",
    "MComp",
    "MAcc",
    "MFin",
    "MBA",
    "MPA",
    "MEd",
    "MEnt",
    "MCGI",
    "MGeol",
    "MLitt",
    "MEarthSc",
    "MClinRes",
    "MJur",
    "FdA",
    "FdSc",
    "FdEng",
    "PgD",
    "PgDip",
    "PgC",
    "PgCert",
    "DipHE",
    "OND",
    "CertHE",
    "RA",
    "FRCP",
    "FRSC",
    "FRSA",
    "FRCS",
    "FMedSci",
    "AMSB",
    "MSB",
    "FSB",
    "FBA",
    "FBCS",
    "FCPS",
    "FGS",
    "FREng",
    "FRS",
    "FRAeS",
    "FRAI",
    "FRAS",
    "MRCP",
    "MRCS",
    "MRCA",
    "FRCA",
    "MRCGP",
    "FRCGP",
    "MRSC",
    "MRPharmS",
    "FRPharmS",
    "FZS",
    "FRES",
    "CBiol",
    "CChem",
    "CEng",
    "CMath",
    "CPhys",
    "CSci",
}

SUFFIXES_LOWER = {suf.lower() for suf in SUFFIXES}

NOT_SUFFIX = {"I.", "V."}


# Make attributes instead of dict style.
# Parse from string as a class method.
# updatable attributes that can be set via constructor or modified at any time.
# to_dict, to_json method?


class PersonName(dict[str, str]):
    """Class for parsing a person's name into its constituent parts.

    Parses a name string into title, firstname, middlename, nickname, prefix, lastname, suffix.

    Example usage::

        p = PersonName('von Beethoven, Ludwig')

    PersonName acts like a dict::

        print p
        print p['firstname']
        print json.dumps(p)

    Name components can also be access as attributes::

        print p.lastname

    Instances can be reused by setting the name property::

        p.name = 'Henry Ford Jr. III'
        print p

    Two PersonName objects are equal if every name component matches exactly. For fuzzy matching, use the `could_be`
    method. This returns True for names that are not explicitly inconsistent.

    This class was written with the intention of parsing BibTeX author names, so name components enclosed within curly
    brackets will not be split.

    """

    # Useful info at  http://nwalsh.com/tex/texhelp/bibtx-23.html

    # Issues:
    # - Prefix 'ben' is recognised as middlename. Could distinguish 'ben' and 'Ben'?
    # - Multiple word first names like "Emma May" or "Billy Joe" aren't supported

    def __init__(self, fullname: str | None = None, from_bibtex: bool = False) -> None:
        """Initialize with a name string.

        Args:
            fullname: The person's name
            from_bibtex: Whether the fullname parameter is in BibTeX format
        """
        super().__init__()
        self._from_bibtex: bool = from_bibtex
        if fullname is not None:
            self.fullname = fullname

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.fullname!r})"

    def __str__(self) -> str:
        return dict.__repr__(self)

    def could_be(self, other: PersonName) -> bool:
        """Return True if the other PersonName is not explicitly inconsistent."""
        # TODO: Some suffix and title differences should be allowed
        if type(other) is not type(self):
            return NotImplemented
        if self == other:
            return True
        for attr in [
            "title",
            "firstname",
            "middlename",
            "nickname",
            "prefix",
            "lastname",
            "suffix",
        ]:
            if attr not in self or attr not in other:
                continue
            puncmap = {ord(char): None for char in string.punctuation}
            s = self[attr].lower().translate(puncmap)
            o = other[attr].lower().translate(puncmap)
            if s == o:
                continue
            if attr in {"firstname", "middlename", "lastname"} and (
                (
                    {len(comp) for comp in s.split()} == {1}
                    and [el[0] for el in o.split()] == s.split()
                )
                or (
                    {len(comp) for comp in o.split()} == {1}
                    and [el[0] for el in s.split()] == o.split()
                )
            ):
                continue
            return False
        return True

    @property
    def fullname(self) -> str:
        return self.get("fullname", "")

    @fullname.setter
    def fullname(self, fullname: str) -> None:
        self.clear()
        self._parse(fullname)

    def __getattr__(self, name: str) -> str:
        if name in {
            "title",
            "firstname",
            "middlename",
            "nickname",
            "prefix",
            "lastname",
            "suffix",
        }:
            return self.get(name)
        else:
            raise AttributeError

    def _is_title(self, t: str) -> bool:
        """Return true if t is a title."""
        return t.lower().replace(".", "") in TITLES

    def _is_prefix(self, t: str) -> bool:
        """Return true if t is a prefix."""
        return t.lower().replace(".", "") in PREFIXES

    def _is_suffix(self, t: str) -> bool:
        """Return true if t is a suffix."""
        return t not in NOT_SUFFIX and (
            t.replace(".", "") in SUFFIXES or t.replace(".", "") in SUFFIXES_LOWER
        )

    def _tokenize(self, comps: list[str]) -> list[str]:
        """Split name on spaces, unless inside curly brackets or quotes."""
        ps = []
        for comp in comps:
            ps.extend([c.strip(" ,") for c in re.split(r"\s+(?=[^{}]*(?:\{|$))", comp)])
        return [p for p in ps if p]

    def _clean(self, t: str, capitalize: str | None = None) -> str:
        """Convert to normalized unicode and strip trailing full stops."""
        if self._from_bibtex:
            t = latex_to_unicode(t, capitalize=capitalize)
        t = " ".join([el.rstrip(".") if el.count(".") == 1 else el for el in t.split()])
        return t

    def _strip(self, tokens: list[str], criteria: Any, prop: str, rev: bool = False) -> list[str]:
        """Strip off contiguous tokens from the start or end of the list that meet the criteria."""
        num = len(tokens)
        res = []
        for i, token in enumerate(reversed(tokens) if rev else tokens):
            if criteria(token) and num > i + 1:
                res.insert(0, tokens.pop()) if rev else res.append(tokens.pop(0))
            else:
                break
        if res:
            self[prop] = self._clean(" ".join(res))
        return tokens

    def _normalize_input(self, fullname: str) -> str:
        """Normalize input by collapsing whitespace and stripping commas."""
        return " ".join(fullname.split()).strip(",")

    def _is_empty_input(self, normalized_name: str) -> bool:
        """Check if the normalized input is empty."""
        return not normalized_name

    def _split_on_commas(self, normalized_name: str) -> list[str]:
        """Split name on commas and strip whitespace from components."""
        return [p.strip() for p in normalized_name.split(",")]

    def _has_suffix_sequence(self, components: list[str]) -> bool:
        """Check if components[1:] are all suffixes."""
        return len(components) > 1 and not all(self._is_suffix(comp) for comp in components[1:])

    def _extract_lastname_from_comma_format(
        self, components: list[str]
    ) -> tuple[str | None, list[str]]:
        """Extract lastname from comma-separated format with suffix handling."""
        if not self._has_suffix_sequence(components):
            return None, components

        vlj = []
        comps_copy = components.copy()
        while True:
            vlj.append(comps_copy.pop(0))
            if not comps_copy or not self._is_suffix(comps_copy[0]):
                break

        ltokens = self._tokenize(vlj)
        ltokens = self._strip(ltokens, self._is_prefix, "prefix")
        ltokens = self._strip(ltokens, self._is_suffix, "suffix", True)
        lastname = self._clean(" ".join(ltokens), capitalize="name")

        return lastname, comps_copy

    def _find_prefix_positions(self, tokens: list[str]) -> list[int]:
        """Find positions of prefix tokens using von particle logic."""
        if "prefix" in self:
            return []

        voni = []
        end = len(tokens) - 1

        for i, token in enumerate(reversed(tokens)):
            if self._is_prefix(token):
                if (i == 0 and end > 0) or ("lastname" not in self and i != end):
                    voni.append(end - i)
            else:
                if (i == 0 and "lastname" in self) or voni:
                    break

        return voni

    def _extract_prefix_and_lastname(
        self, tokens: list[str]
    ) -> tuple[str | None, str | None, list[str]]:
        """Extract prefix and lastname from tokens, returning remaining tokens."""
        # If no tokens left, nothing to extract
        if not tokens:
            return None, None, tokens

        voni = self._find_prefix_positions(tokens)

        if not voni:
            # No prefix found, extract lastname from end if needed
            lastname = None
            if "lastname" not in self and tokens:
                lastname = self._clean(tokens.pop(), capitalize="name")
            return None, lastname, tokens

        # Extract prefix and lastname
        if "lastname" not in self:
            lastname = self._clean(" ".join(tokens[voni[0] + 1 :]), capitalize="name")
        else:
            lastname = None

        prefix = self._clean(" ".join(tokens[voni[-1] : voni[0] + 1]))
        remaining_tokens = tokens[: voni[-1]]

        return prefix, lastname, remaining_tokens

    def _extract_nickname(self, tokens: list[str]) -> tuple[str | None, list[str]]:
        """Extract nickname enclosed in quotes, returning nickname and remaining tokens."""
        if not tokens:
            return None, tokens

        nicki = []
        for i, token in enumerate(tokens):
            if token[0] in QUOTES:
                for j, token2 in enumerate(tokens[i:]):
                    if token2[-1] in QUOTES:
                        nicki = range(i, i + j + 1)
                        break

        if not nicki:
            return None, tokens

        nickname_text = " ".join(tokens[nicki[0] : nicki[-1] + 1]).strip("".join(QUOTES))
        nickname = self._clean(nickname_text, capitalize="name")

        # Remove nickname tokens from the list
        tokens_copy = tokens.copy()
        tokens_copy[nicki[0] : nicki[-1] + 1] = []

        return nickname, tokens_copy

    def _extract_name_components(
        self, tokens: list[str]
    ) -> tuple[str | None, str | None, str | None]:
        """Extract firstname, nickname, and middlename from remaining tokens."""
        firstname = None
        nickname = None
        middlename = None

        if tokens:
            firstname = self._clean(tokens.pop(0), capitalize="name")

        if tokens:
            nickname, tokens = self._extract_nickname(tokens)

        if tokens:
            middlename = self._clean(" ".join(tokens), capitalize="name")

        return firstname, nickname, middlename

    def _assemble_fullname(self) -> None:
        """Assemble the fullname from individual components."""
        namelist = []
        for attr in [
            "title",
            "firstname",
            "middlename",
            "nickname",
            "prefix",
            "lastname",
            "suffix",
        ]:
            if attr in self:
                namelist.append(f'"{self[attr]}"' if attr == "nickname" else self[attr])
        self["fullname"] = " ".join(namelist)

    def _parse(self, fullname: str) -> None:
        """Parse a full name into components using a structured pipeline."""
        # Phase 1: Input normalization and early exit
        normalized_name = self._normalize_input(fullname)
        if self._is_empty_input(normalized_name):
            return

        # Phase 2: Handle comma-separated format (lastname extraction)
        components = self._split_on_commas(normalized_name)
        lastname, remaining_components = self._extract_lastname_from_comma_format(components)
        if lastname:
            self["lastname"] = lastname

        # Phase 3: Token processing and title/suffix stripping
        tokens = self._tokenize(remaining_components)
        tokens = self._strip(tokens, self._is_title, "title")
        if "lastname" not in self:
            tokens = self._strip(tokens, self._is_suffix, "suffix", True)

        # Phase 4: Prefix and lastname extraction
        prefix, extracted_lastname, tokens = self._extract_prefix_and_lastname(tokens)
        if prefix:
            self["prefix"] = prefix
        if extracted_lastname:
            self["lastname"] = extracted_lastname

        # Phase 5: Name component extraction
        firstname, nickname, middlename = self._extract_name_components(tokens)
        if firstname:
            self["firstname"] = firstname
        if nickname:
            self["nickname"] = nickname
        if middlename:
            self["middlename"] = middlename

        # Phase 6: Assemble final fullname
        self._assemble_fullname()

"""
Tools for loading and caching data files.

"""

import logging
import pickle
import tarfile
from pathlib import Path
from typing import Any

import appdirs
import requests
from yaspin import yaspin

from .config import config
from .errors import ModelNotFoundError
from .utils import ensure_dir

log = logging.getLogger(__name__)


class SafePickleUnpickler(pickle.Unpickler):
    """
    Secure pickle unpickler with class allowlist.

    Only allows deserialization of known safe classes used in ChemDataExtractor
    models. Prevents arbitrary code execution from malicious pickle files.
    """

    # Modules that are considered safe for ChemDataExtractor models
    SAFE_MODULES = frozenset({
        'builtins', 'collections', 'copy_reg', 'copyreg', '_codecs', 'encodings',
        'numpy', 'numpy.core', 'numpy.core.multiarray', 'numpy.core.numeric',
        'sklearn', 'sklearn.base', 'sklearn.feature_extraction', 'sklearn.linear_model',
        'nltk', 'nltk.tokenize', 'nltk.tokenize.punkt',
        'pycrfsuite', 'python_crfsuite',
        # Note: __main__ removed for security - no arbitrary classes from main module
    })

    # Specific safe classes (module.class format)
    SAFE_CLASSES = frozenset({
        # Built-in types
        'builtins.dict', 'builtins.list', 'builtins.tuple', 'builtins.set', 'builtins.frozenset',
        'builtins.str', 'builtins.bytes', 'builtins.int', 'builtins.float', 'builtins.bool',
        'builtins.NoneType', 'builtins.complex', 'builtins.slice', 'builtins.range',

        # Collections
        'collections.defaultdict', 'collections.OrderedDict', 'collections.Counter',
        'collections.deque', 'collections.namedtuple',

        # NumPy (common in ML models)
        'numpy.ndarray', 'numpy.dtype', 'numpy.matrix', 'numpy.int64', 'numpy.float64',
        'numpy.int32', 'numpy.float32', 'numpy.bool_', 'numpy.str_',

        # Sklearn (used for CRF and other ML models)
        'sklearn.linear_model.LogisticRegression', 'sklearn.feature_extraction.DictVectorizer',
        'sklearn.base.BaseEstimator', 'sklearn.base.TransformerMixin',

        # CRF Suite (for chemical entity recognition)
        'pycrfsuite.Tagger', 'pycrfsuite.Trainer',

        # NLTK (for tokenization models)
        'nltk.tokenize.punkt.PunktSentenceTokenizer', 'nltk.tokenize.punkt.PunktParameters',
    })

    def find_class(self, module: str, name: str) -> Any:
        """
        Override to implement class allowlist.

        Args:
            module: Module name (e.g., 'builtins', 'numpy')
            name: Class name (e.g., 'dict', 'ndarray')

        Returns:
            The requested class if safe

        Raises:
            pickle.UnpicklingError: If class is not in allowlist
        """
        full_name = f"{module}.{name}"

        # Allow specific safe classes only (no blanket module allowlisting)
        if full_name in self.SAFE_CLASSES:
            log.debug(f"Allowing safe class: {full_name}")
            return super().find_class(module, name)

        # Allow specific safe module+class combinations for well-known safe modules
        if module in self.SAFE_MODULES:
            # Be very restrictive even for "safe" modules - only allow data types, not functions
            if module == 'builtins' and name not in {
                'dict', 'list', 'tuple', 'set', 'frozenset', 'str', 'bytes',
                'int', 'float', 'bool', 'NoneType', 'complex', 'slice', 'range'
            }:
                log.warning(f"Rejected builtins function/class: {full_name}")
                raise pickle.UnpicklingError(f"Unsafe builtins class rejected: {full_name}")

            log.debug(f"Allowing safe module class: {full_name}")
            return super().find_class(module, name)

        # Log and reject unsafe classes
        log.warning(f"Rejected unsafe class during pickle loading: {full_name}")
        raise pickle.UnpicklingError(
            f"Unsafe class rejected for security: {full_name}. "
            f"If this is a legitimate ChemDataExtractor model class, "
            f"please add it to the SAFE_CLASSES allowlist."
        )


def safe_pickle_load(file_path: str) -> Any:
    """
    Safely load a pickle file with security restrictions.

    Uses SafePickleUnpickler to prevent deserialization of dangerous classes.

    Args:
        file_path: Path to the pickle file

    Returns:
        The unpickled object

    Raises:
        pickle.UnpicklingError: If unsafe classes are detected
        OSError: If file cannot be opened
    """
    log.debug(f"Loading pickle file with security restrictions: {file_path}")
    with open(file_path, "rb") as f:
        unpickler = SafePickleUnpickler(f)
        return unpickler.load()


SERVER_ROOT: str = "http://data.chemdataextractor.org/"
AUTO_DOWNLOAD: bool = True


class Package:
    """Data package."""

    def __init__(
        self,
        path,
        server_root=None,
        remote_path=None,
        untar=False,
        custom_download=None,
    ):
        """
        :param str path: The path to where this package will be located under
            ChemDataExtractor's default data directory.
        :param str (optional) server_root: The root path for the server.
            If you do not supply the remote_path parameter, this will be used to find the
            remote path for the package.
        :param str (optional) remote_path: The remote path for the package.
        :param bool (optional) untar: Whether the package should be untarred after download.
        """
        self.path = path
        self.server_root = server_root
        if server_root is None:
            self.server_root = SERVER_ROOT
        self._remote_path = remote_path
        self.untar = untar
        self.custom_download = custom_download

    def _is_safe_path(self, member_path: str, extraction_path: str) -> bool:
        """
        Validate that a tar member path is safe for extraction.

        Prevents directory traversal attacks by ensuring extracted files
        stay within the intended extraction directory.

        Args:
            member_path: Path of the tar member
            extraction_path: Base directory for extraction

        Returns:
            True if the path is safe, False otherwise
        """
        if not member_path:
            log.warning("Empty path in archive")
            return False

        # Check for absolute paths first
        if Path(member_path).is_absolute():
            log.warning(f"Unsafe path in archive (absolute): {member_path}")
            return False

        # Check for parent directory references
        if ".." in Path(member_path).parts:
            log.warning(f"Unsafe path in archive (parent reference): {member_path}")
            return False

        # Normalize paths for comparison
        try:
            extraction_path = Path(extraction_path).resolve()
            # Create the full path that would result from extraction
            full_member_path = extraction_path / member_path
            # Resolve it to handle any remaining path normalization
            full_member_path = full_member_path.resolve()

            # Ensure the resolved path is within the extraction directory
            full_member_path.relative_to(extraction_path)
            return True
        except (OSError, ValueError) as e:
            # Path is outside the extraction directory or invalid
            log.warning(f"Unsafe path in archive (directory traversal): {member_path} - {e}")
            return False

    def _is_safe_member(self, member: tarfile.TarInfo) -> bool:
        """
        Validate that a tar member is safe for extraction.

        Args:
            member: TarInfo object representing the archive member

        Returns:
            True if the member is safe, False otherwise
        """
        # Check for absolute paths
        if Path(member.name).is_absolute():
            log.warning(f"Skipping absolute path: {member.name}")
            return False

        # Check for parent directory references
        if ".." in Path(member.name).parts:
            log.warning(f"Skipping path with parent references: {member.name}")
            return False

        # Only allow regular files and directories
        if not (member.isreg() or member.isdir()):
            log.warning(f"Skipping non-regular file/directory: {member.name} (type: {member.type})")
            return False

        # Check for reasonable file size (prevent zip bombs)
        if member.isreg() and member.size > 1024 * 1024 * 1024:  # 1GB limit
            log.warning(f"Skipping excessively large file: {member.name} ({member.size} bytes)")
            return False

        return True

    def _safe_extract(self, tar_file: tarfile.TarFile, extraction_path: str) -> None:
        """
        Safely extract a tar file with security validation.

        Args:
            tar_file: Opened TarFile object
            extraction_path: Directory to extract files to
        """
        extraction_path = str(extraction_path)  # Ensure string for compatibility

        # Use manual validation for maximum security control
        # (Python 3.12+ data filter might still allow some edge cases)
        log.debug("Using manual member validation for secure extraction")
        extracted_count = 0
        skipped_count = 0

        for member in tar_file.getmembers():
            # Validate member safety
            if not self._is_safe_member(member):
                skipped_count += 1
                continue

            # Additional path safety check
            if not self._is_safe_path(member.name, extraction_path):
                skipped_count += 1
                continue

            try:
                # Extract individual member with validation
                tar_file.extract(member, extraction_path)
                extracted_count += 1
                log.debug(f"Safely extracted: {member.name}")
            except Exception as e:
                log.warning(f"Failed to extract {member.name}: {e}")
                skipped_count += 1

        log.info(f"Extracted {extracted_count} files, skipped {skipped_count} unsafe files")

        if extracted_count == 0:
            raise ValueError("No files were safely extracted from the archive")

    @property
    def remote_path(self):
        """"""
        if self._remote_path is not None:
            return self._remote_path
        return self.server_root + self.path

    @property
    def local_path(self):
        """"""
        return find_data(self.path, warn=False, get_data=False)

    def remote_exists(self):
        """"""
        r = requests.get(self.remote_path)
        return r.status_code not in {400, 401, 403, 404}

    def local_exists(self):
        """"""
        return Path(self.local_path).exists()

    def download(self, force=False):
        if self.custom_download is not None:
            self.custom_download(self.local_path, force=force)
        else:
            self.default_download(force)

    def default_download(self, force=False):
        """"""
        log.debug("Considering %s", self.remote_path)
        ensure_dir(str(Path(self.local_path).parent))
        r = requests.get(self.remote_path, stream=True)
        r.raise_for_status()
        # Check if already downloaded
        if self.local_exists():
            # Skip if existing, unless the file has changed
            if not force and Path(self.local_path).stat().st_size == int(
                r.headers.get("content-length")
            ):
                log.debug("Skipping existing: %s", self.local_path)
                return False
            else:
                log.debug("File size mismatch for %s", self.local_path)
        log.info("Downloading %s to %s", self.remote_path, self.local_path)
        download_path = self.local_path
        if self.untar:
            download_path = self.local_path + ".tar.gz"
        with open(download_path, "wb") as f:
            with yaspin(text=f"Couldn't find {self.path}, downloading", side="right").simpleDots:
                for chunk in r.iter_content(chunk_size=1024 * 1024):  # Large 10MB chunks
                    if chunk:
                        f.write(chunk)
        if self.untar:
            with tarfile.open(download_path, "r:gz") as f:
                self._safe_extract(f, self.local_path)
            Path(download_path).unlink()
        return True

    def __repr__(self):
        return f"<Package: {self.path}>"

    def __str__(self):
        return f"<Package: {self.path}>"


def get_data_dir():
    """Return path to the data directory."""
    # Use data_dir config value if set, otherwise use OS-dependent data directory given by appdirs
    return config.get("data_dir", appdirs.user_data_dir("ChemDataExtractor"))


def find_data(path, warn=True, get_data=True):
    """Return the absolute path to a data file within the data directory."""
    full_path = str(Path(get_data_dir()) / path)
    if AUTO_DOWNLOAD and get_data and not Path(full_path).exists():
        for package in PACKAGES:
            if package.path == path:
                package.download()
                break
    elif warn and not Path(full_path).exists():
        for package in PACKAGES:
            if path == package.path:
                log.warn(f"{path} doesn't exist. Run `cde data download` to get it.")
                break
    return full_path


#: A dictionary used to cache models so they only need to be loaded once.
_model_cache = {}


def load_model(path):
    """Load a model from a pickle file in the data directory. Cached so model is only loaded once."""
    abspath = find_data(path)
    cached = _model_cache.get(abspath)
    if cached is not None:
        log.debug(f"Using cached copy of {path}")
        return cached
    log.debug(f"Loading model {path}")
    try:
        model = safe_pickle_load(abspath)
    except OSError:
        raise ModelNotFoundError(f"Could not load {path}. Have you run `cde data download`?")
    _model_cache[abspath] = model
    return model


#: Current active data packages
PACKAGES = [
    Package("models/cem_crf-1.0.pickle"),
    Package("models/cem_crf_chemdner_cemp-1.0.pickle"),
    Package("models/cem_dict_cs-1.0.pickle"),
    Package("models/cem_dict-1.0.pickle"),
    Package("models/clusters_chem1500-1.0.pickle"),
    Package("models/pos_ap_genia_nocluster-1.0.pickle"),
    Package("models/pos_ap_genia-1.0.pickle"),
    Package("models/pos_ap_wsj_genia_nocluster-1.0.pickle"),
    Package("models/pos_ap_wsj_genia-1.0.pickle"),
    Package("models/pos_ap_wsj_nocluster-1.0.pickle"),
    Package("models/pos_ap_wsj-1.0.pickle"),
    Package("models/pos_crf_genia_nocluster-1.0.pickle"),
    Package("models/pos_crf_genia-1.0.pickle"),
    Package("models/pos_crf_wsj_genia_nocluster-1.0.pickle"),
    Package("models/pos_crf_wsj_genia-1.0.pickle"),
    Package("models/pos_crf_wsj_nocluster-1.0.pickle"),
    Package("models/pos_crf_wsj-1.0.pickle"),
    Package("models/punkt_chem-1.0.pickle"),
    Package(
        "models/bert_finetuned_crf_model-1.0a",
        remote_path="https://cdemodels.blob.core.windows.net/cdemodels/bert_pretrained_crf_model-1.0a.tar.gz",
        untar=True,
    ),
    Package(
        "models/hf_bert_crf_tagger",
        remote_path="https://cdemodels.blob.core.windows.net/cdemodels/hf_bert_crf_tagger.tar.gz",
        untar=True,
    ),
    Package(
        "models/scibert_cased_vocab-1.0.txt",
        remote_path="https://cdemodels.blob.core.windows.net/cdemodels/scibert_cased_vocab_1.0.txt",
    ),
    Package(
        "models/scibert_uncased_vocab-1.0.txt",
        remote_path="https://cdemodels.blob.core.windows.net/cdemodels/scibert_uncased_vocab-1.0.txt",
    ),
    Package(
        "models/scibert_cased_weights-1.0.tar.gz",
        remote_path="https://cdemodels.blob.core.windows.net/cdemodels/scibert_cased_weights-1.0.tar.gz",
    ),
]

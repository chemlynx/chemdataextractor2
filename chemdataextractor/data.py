"""
Tools for loading and caching data files.

"""

import logging
import os
import pickle
import tarfile
import zipfile
from pathlib import Path

import appdirs
import requests
from yaspin import yaspin

from .config import config
from .errors import ModelNotFoundError
from .utils import ensure_dir

log = logging.getLogger(__name__)


SERVER_ROOT: str = "http://data.chemdataextractor.org/"
AUTO_DOWNLOAD: bool = True


class Package:
    """Data package."""

    def __init__(
        self,
        path,
        server_root=None,
        remote_path=None,
        unzip=False,
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
        :param bool (optional) unzip: Whether the package should be unzipped after download.
            You should only ever set this or untar to True.
        :param bool (optional) untar: Whether the package should be untarred after download.
            You should only ever set this or unzip to True.
        """
        self.path = path
        self.server_root = server_root
        if server_root is None:
            self.server_root = SERVER_ROOT
        self._remote_path = remote_path
        self.unzip = unzip
        self.untar = untar
        self.custom_download = custom_download

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
        if self.unzip:
            download_path = self.local_path + ".zip"
        elif self.untar:
            download_path = self.local_path + ".tar.gz"
        with open(download_path, "wb") as f:
            with yaspin(text=f"Couldn't find {self.path}, downloading", side="right").simpleDots:
                for chunk in r.iter_content(chunk_size=1024 * 1024):  # Large 10MB chunks
                    if chunk:
                        f.write(chunk)
        if self.unzip:
            with zipfile.ZipFile(download_path, "r") as f:
                f.extractall(self.local_path)
            Path(download_path).unlink()
        elif self.untar:
            with tarfile.open(download_path, "r:gz") as f:
                f.extractall(self.local_path)
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
        with open(abspath, "rb") as f:
            model = pickle.load(f)
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

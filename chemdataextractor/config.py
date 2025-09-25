"""
Config file reader/writer.

"""

import os
from collections.abc import Iterator
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import appdirs
import yaml
from yaml import SafeLoader


def construct_yaml_str(self: SafeLoader, node: yaml.Node) -> str:
    """Override the default string handling function to always return unicode objects."""
    return self.construct_scalar(node)


SafeLoader.add_constructor("tag:yaml.org,2002:str", construct_yaml_str)


class Config(MutableMapping[str, Any]):
    """Read and write to config file.

    A config object is essentially a string key-value store that can be treated like a dictionary::

        c = Config()
        c['foo'] = 'bar'
        print c['foo']

    The file location may be specified::

        c = Config('~/matt/anotherconfig.yml')
        c['where'] = 'in a different file'

    If no location is specified, the environment variable CHEMDATAEXTRACTOR_CONFIG is checked and used if available.
    Otherwise, a standard config location is used, which varies depending on the operating system. You can check the
    location using the ``path`` property. For more information see https://github.com/ActiveState/appdirs

    It is possible to edit the file by hand with a text editor. It is in YAML format.

    Warning: multiple instances of Config() pointing to the same file will not see each others' changes, and will
    overwrite the entire file when any key is changed.

    """

    def __init__(self, path: str | None = None) -> None:
        """

        :param string path: (Optional) Path to config file location.
        """
        self._path: str | None = path
        self._data: dict[str, Any] = {}

        # Use CHEMDATAEXTRACTOR_CONFIG environment variable if set
        if not self._path:
            self._path = os.environ.get("CHEMDATAEXTRACTOR_CONFIG")
        # Use OS-dependent config directory given by appdirs
        if not self._path:
            self._path = str(
                Path(appdirs.user_config_dir("ChemDataExtractor")) / "chemdataextractor.yml"
            )
        if Path(self.path).is_file():
            with open(self.path, encoding="utf8") as f:
                self._data = yaml.safe_load(f) or {}

    @property
    def path(self) -> str:
        """The path to the config file."""
        if self._path is None:
            raise ValueError("Config path not set")
        return self._path

    def _flush(self) -> None:
        """Save the contents of data to the file on disk. You should not need to call this manually."""
        path_obj = Path(self.path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf8") as f:
            yaml.safe_dump(self._data, f, default_flow_style=False, encoding=None)

    def __contains__(self, k: object) -> bool:
        return k in self._data

    def __getitem__(self, k: str) -> Any:
        return self._data[k]

    def __setitem__(self, k: str, v: Any) -> None:
        self._data[k] = v
        self._flush()

    def __delitem__(self, k: str) -> None:
        del self._data[k]
        self._flush()

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"<Config: {self.path}>"

    def clear(self) -> None:
        """Clear all values from config."""
        self._data = {}
        self._flush()


#: Global config instance.
config = Config()

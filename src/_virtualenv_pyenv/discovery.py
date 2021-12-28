from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from pyenv_inspect.exceptions import SpecParseError
from pyenv_inspect.path import (
    get_pyenv_python_bin_path, get_pyenv_versions_directory,
)
from pyenv_inspect.spec import Implementation, PyenvPythonSpec
from pyenv_inspect.version import Version
from virtualenv.discovery.discover import Discover
from virtualenv.discovery.py_info import PythonInfo


class Pyenv(Discover):
    """pyenv discovery mechanism"""

    def __init__(self, options) -> None:
        super().__init__(options)
        self._string_specs: List[str] = options.python
        self._app_data = options.app_data

    def __str__(self) -> str:
        if len(self._string_specs) == 1:
            spec = self._string_specs[0]
        else:
            spec = self._string_specs
        return f'{self.__class__.__name__} discover of spec={spec!r}'

    @classmethod
    def add_parser_arguments(cls, parser) -> None:
        parser.add_argument(
            '-p',
            '--python',
            metavar='py',
            type=str,
            action='append',
            required=True,
            help='interpreter based on what to create environment',
        )

    def run(self) -> Optional[PythonInfo]:
        for string_spec in self._string_specs:
            result = self._get_interpreter(string_spec)
            if result is not None:
                return result
        return None

    def _get_interpreter(self, string_spec: str) -> Optional[PythonInfo]:
        try:
            spec = PyenvPythonSpec.from_string_spec(string_spec)
        except SpecParseError:
            logging.error('failed to parse spec %s', string_spec)
            return None
        if spec.implementation != Implementation.CPYTHON:
            logging.error('only CPython is currently supported')
            return None
        logging.debug('find interpreter for spec %s', string_spec)
        requested_version = Version.from_string_version(spec.version)
        if requested_version is None:
            logging.error('failed to parse requested version %s', spec.version)
            return None
        best_match_version: Optional[Version] = None
        best_match_dir: Optional[Path] = None
        for version_dir in get_pyenv_versions_directory().iterdir():
            version = Version.from_string_version(version_dir.name)
            if version is None:
                logging.error('failed to parse pyenv version %s', version)
                continue
            if version in requested_version:
                logging.debug('proposed %s', version)
                if not best_match_version or version > best_match_version:
                    best_match_version = version
                    best_match_dir = version_dir
        if not best_match_version:
            return None
        logging.debug('accepted %s', best_match_version)
        bin_path = get_pyenv_python_bin_path(best_match_dir)
        return PythonInfo.from_exe(
            str(bin_path), app_data=self._app_data, env=self._env)

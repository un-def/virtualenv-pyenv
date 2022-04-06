from __future__ import annotations

import logging
from typing import List, Optional

from pyenv_inspect import find_pyenv_python_executable
from pyenv_inspect.exceptions import SpecParseError, UnsupportedImplementation
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
        logging.debug('find interpreter for spec %s', string_spec)
        try:
            exec_path = find_pyenv_python_executable(string_spec)
        except SpecParseError:
            logging.error('failed to parse spec %s', string_spec)
            return None
        except UnsupportedImplementation:
            logging.error('only CPython is currently supported')
            return None
        if exec_path is None:
            return None
        return PythonInfo.from_exe(
            str(exec_path), app_data=self._app_data, env=self._env)

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Union

from pyenv_inspect import find_pyenv_python_executable
from pyenv_inspect.exceptions import SpecParseError, UnsupportedImplementation
from pyenv_inspect.spec import Implementation, PyenvPythonSpec
from virtualenv.discovery.discover import Discover
from virtualenv.discovery.py_info import PythonInfo
from virtualenv.discovery.py_spec import PythonSpec


if TYPE_CHECKING:
    from pathlib import Path


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
            # an empty list as a default value is required for env var support,
            # see VirtualEnvConfigParser._fix_default() -> get_type()
            default=[],
            help='interpreter based on what to create environment',
        )

    def run(self) -> Optional[PythonInfo]:
        string_specs = self._string_specs
        if not string_specs:
            logging.error(
                'interpreter is not specified, use either -p/--python option '
                'or VIRTUALENV_PYTHON environment variable'
            )
            return None
        for string_spec in string_specs:
            result = self._get_interpreter(string_spec)
            if result is not None:
                return result
        return None

    def _get_interpreter(self, string_spec: str) -> Optional[PythonInfo]:
        logging.debug('find interpreter for spec %s', string_spec)
        pyenv_spec: Optional[PythonSpec] = None

        # first, we try to parse the spec as a pyenv-style spec (e.g., 3.7,
        # 3.7.1, 3.7-dev)
        try:
            pyenv_spec = PyenvPythonSpec.from_string_spec(string_spec)
            pyenv_spec.is_supported(raise_exception=True)
        except (SpecParseError, UnsupportedImplementation):
            pyenv_spec = None
        if pyenv_spec is not None:
            return self._find_interpreter(pyenv_spec)

        # if it is not in the pyenv format (or it is, but we do not yet support
        # that implementation), we parse it using virtualenv built-in machinery
        builtin_spec: PythonSpec = PythonSpec.from_string_spec(string_spec)

        # if it looks like a path, assume it points to the Python executable
        if builtin_spec.path is not None:
            return self._build_python_info(builtin_spec.path)

        # otherwise, we check if it is a CPython version
        impl: Optional[str] = builtin_spec.implementation
        # PythonSpec.from_string_spec() replaces 'py' and 'python', but not
        # 'cpython', with None
        if impl is not None and impl != 'cpython':
            logging.error('only CPython is currently supported')
            return None

        # finally, we build a pyenv-style spec
        major, minor = builtin_spec.major, builtin_spec.minor
        # pyenv-inspect does not allow major-only version specifiers,
        # but this constraint could be relaxed in the future
        if major is None or minor is None:
            logging.error('major and minor version components are required')
            return None
        version = f'{major}.{minor}'
        patch = builtin_spec.micro
        if patch is not None:
            version = f'{version}.{patch}'
        pyenv_spec = PyenvPythonSpec(
            string_spec=version,
            implementation=Implementation.CPYTHON, version=version,
        )
        return self._find_interpreter(pyenv_spec)

    def _find_interpreter(self, spec: PyenvPythonSpec) -> Optional[PythonInfo]:
        exec_path = find_pyenv_python_executable(spec)
        if exec_path is None:
            return None
        return self._build_python_info(exec_path)

    def _build_python_info(self, exec_path: Union[Path, str]) -> PythonInfo:
        return PythonInfo.from_exe(
            str(exec_path), app_data=self._app_data, env=self._env)

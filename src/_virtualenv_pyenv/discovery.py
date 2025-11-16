import copy
import logging
import sys
from typing import TYPE_CHECKING, ClassVar, List, Optional, Union

from pyenv_inspect import find_pyenv_python_executable
from pyenv_inspect.exceptions import (
    SpecParseError, UnsupportedImplementation, VersionParseError,
)
from pyenv_inspect.spec import Implementation, PyenvPythonSpec
from virtualenv.discovery.builtin import Builtin
from virtualenv.discovery.discover import Discover
from virtualenv.discovery.py_info import PythonInfo
from virtualenv.discovery.py_spec import PythonSpec


if TYPE_CHECKING:
    from pathlib import Path


class _Error(Exception):
    pass


class _Pyenv(Discover):
    """pyenv discovery mechanism"""

    allow_default_interpreter: ClassVar[bool]
    allow_path: ClassVar[bool]
    fall_back_to_builtin: ClassVar[bool]

    def __init__(self, options) -> None:
        super().__init__(options)
        self._options = options
        self._string_specs: List[str] = options.python

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
        try:
            return self._run()
        except _Error as err:
            logging.error(str(err))
        return None

    def _run(self) -> Optional[PythonInfo]:
        string_specs = self._string_specs
        if not string_specs:
            if not self.allow_default_interpreter:
                raise _Error(
                    'interpreter is not specified, use either -p/--python '
                    'option or VIRTUALENV_PYTHON environment variable'
                )
            python_info = self._get_default_interpreter()
            if python_info is not None:
                return python_info
            raise _Error(
                'failed to discover the default interpreter, '
                'specify an interpreter using either -p/--python option '
                'or VIRTUALENV_PYTHON environment variable'
            )
        for string_spec in string_specs:
            python_info = self._get_interpreter(string_spec)
            if python_info is not None:
                return python_info
        if self.fall_back_to_builtin:
            return self._run_builtin_discovery()
        return None

    def _run_builtin_discovery(self) -> Optional[PythonInfo]:
        logging.debug('run builtin discovery')
        options = copy.deepcopy(self._options)
        # we don't support this option intentionally
        options.try_first_with = []
        return Builtin(options).run()

    def _get_default_interpreter(self) -> Optional[PythonInfo]:
        logging.debug('use default interpreter')
        # > If Python is unable to retrieve the real path to its
        # > executable, sys.executable will be an empty string or None.
        if sys.executable:
            return self._build_python_info(sys.executable)
        return None

    def _get_interpreter(self, string_spec: str) -> Optional[PythonInfo]:
        logging.debug('find interpreter for spec %s', string_spec)
        pyenv_spec: Optional[PyenvPythonSpec] = None

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
            if self.allow_path:
                return self._build_python_info(builtin_spec.path)
            raise _Error('paths are not allowed')

        # otherwise, we check if it is a CPython version
        impl: Optional[str] = builtin_spec.implementation
        # PythonSpec.from_string_spec() replaces 'py' and 'python', but not
        # 'cpython', with None
        if impl is not None and impl != 'cpython':
            raise _Error('only CPython is currently supported')

        # finally, we build a pyenv-style spec
        version_components: List[str] = []
        for version_component_field in ('major', 'minor', 'micro'):
            version_component = getattr(builtin_spec, version_component_field)
            if version_component is None:
                break
            version_components.append(str(version_component))
        if not version_components:
            raise _Error('major version component is required')
        version = '.'.join(version_components)
        if builtin_spec.free_threaded:
            version = f'{version}t'
        pyenv_spec = PyenvPythonSpec(
            string_spec=version,
            implementation=Implementation.CPYTHON, version=version,
        )
        return self._find_interpreter(pyenv_spec)

    def _find_interpreter(self, spec: PyenvPythonSpec) -> Optional[PythonInfo]:
        try:
            exec_path = find_pyenv_python_executable(spec)
        except VersionParseError:
            raise _Error(f'failed to parse version: {spec.version}')
        if exec_path is None:
            return None
        return self._build_python_info(exec_path)

    def _build_python_info(
        self, exec_path: Union["Path", str],
    ) -> Optional[PythonInfo]:
        return PythonInfo.from_exe(
            str(exec_path),
            app_data=self._options.app_data, env=self._options.env,
        )


class PyenvCompat(_Pyenv):
    allow_default_interpreter = True
    allow_path = True
    fall_back_to_builtin = False


class PyenvFallback(_Pyenv):
    allow_default_interpreter = True
    allow_path = True
    fall_back_to_builtin = True


class PyenvStrict(_Pyenv):
    allow_default_interpreter = False
    allow_path = False
    fall_back_to_builtin = False

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from virtualenv.discovery.discover import Discover
from virtualenv.discovery.py_info import PythonInfo
from virtualenv.discovery.py_spec import PythonSpec


_pyenv_root: Optional[Path] = None


def get_pyenv_root() -> Path:
    global _pyenv_root
    if _pyenv_root:
        return _pyenv_root
    try:
        pyenv_root = Path(os.environ['PYENV_ROOT']).resolve()
    except KeyError:
        pyenv_root = Path.home() / '.pyenv'
    if not pyenv_root.exists():
        raise PyenvDiscoverError(f'pyenv root does not exist: {pyenv_root}')
    if not pyenv_root.is_dir():
        raise PyenvDiscoverError(
            f'pyenv root is not a directory: {pyenv_root}')
    _pyenv_root = pyenv_root
    return pyenv_root


def get_pyenv_versions_directory() -> Path:
    pyenv_root = get_pyenv_root()
    versions_dir = (pyenv_root / 'versions').resolve()
    if not versions_dir.exists():
        raise PyenvDiscoverError(
            f'pyenv versions path does not exist: {versions_dir}')
    if not versions_dir.is_dir():
        raise PyenvDiscoverError(
            f'pyenv versions path is not a directory: {versions_dir}')
    return versions_dir


def get_pyenv_python_bin_path(version_dir: Path) -> Path:
    bin_path = (version_dir / 'bin' / 'python').resolve()
    if not bin_path.exists():
        raise PyenvDiscoverError(
            f'pyenv python executable does not exist: {bin_path}')
    if not bin_path.is_file():
        raise PyenvDiscoverError(
            f'pyenv python executable is not a file: {bin_path}')
    return bin_path


class PyenvDiscoverError(Exception):
    pass


class Pyenv(Discover):
    """pyenv discovery mechanism"""

    def __init__(self, options) -> None:
        super().__init__(options)
        self.python_specs = options.python
        self.app_data = options.app_data

    def __str__(self) -> str:
        if len(self.python_specs) == 1:
            spec = self.python_specs[0]
        else:
            spec = self.python_specs
        return f'{self.__class__.__name__} discover of python_spec={spec!r}'

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
        for python_spec in self.python_specs:
            result = get_interpreter(python_spec, self.app_data, self._env)
            if result is not None:
                return result
        return None


def get_interpreter(python_spec, app_data, env) -> Optional[PythonInfo]:
    spec = PythonSpec.from_string_spec(python_spec)
    logging.info('find interpreter for spec %r', spec)
    proposed_paths = set()
    for interpreter in propose_interpreters(spec, app_data, env):
        if interpreter.system_executable in proposed_paths:
            continue
        logging.info('proposed %s', interpreter)
        if interpreter.satisfies(spec, impl_must_match=True):
            logging.debug('accepted %s', interpreter)
            return interpreter
        proposed_paths.add(interpreter.system_executable)
    return None


def propose_interpreters(spec, app_data, env):
    versions_dir = get_pyenv_versions_directory()
    for version_dir in versions_dir.iterdir():
        bin_path = get_pyenv_python_bin_path(version_dir)
        yield PythonInfo.from_exe(str(bin_path), app_data, env=env)

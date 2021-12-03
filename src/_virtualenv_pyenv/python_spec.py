from __future__ import annotations

import enum
import re
from typing import NamedTuple, Optional

from .version import VERSION_PATTERN


class Implementation(enum.Enum):
    CPYTHON = 'cpython'
    UNSUPPORTED = 'unsupported'


CPYTHON_SPEC_REGEX = re.compile(
    rf'(?P<version>{VERSION_PATTERN})'
)


class PyenvPythonSpec(NamedTuple):
    """Contains specification about a Python Interpreter"""
    string_spec: str
    implementation: Implementation
    version: Optional[str]

    @classmethod
    def from_string_spec(cls, string_spec: str) -> Optional[PyenvPythonSpec]:
        is_cpython = string_spec[0].isdigit()
        if is_cpython:
            implementation = Implementation.CPYTHON
            match = CPYTHON_SPEC_REGEX.fullmatch(string_spec)
            if not match:
                return None
            version = match.group('version')
        else:
            implementation = Implementation.UNSUPPORTED
            version = None
        return cls(string_spec, implementation, version)

    def to_dict(self) -> dict:
        return {
            'string_spec': self.string_spec,
            'implementation': self.implementation.value,
            'version': self.version,
        }

from __future__ import annotations

import re
from typing import NamedTuple, Optional


VERSION_PATTERN = (
    r'(?P<version>[0-9][0-9a-z]*(?:\.[0-9][0-9a-z]*)*(?:-[0-9a-z]+)?'
    r'|latest|dev)'
)
CPYTHON_SPEC_REGEX = re.compile(
    rf'{VERSION_PATTERN}'
)
MINICONDA3_SPEC_REGEX = re.compile(
    r'(?P<implementation>miniconda3(?:-[0-9]\.[0-9]{1,2})?)'
    rf'-{VERSION_PATTERN}'
)
OTHER_SPEC_REGEX = re.compile(
    r'(?P<implementation>[a-z][a-z0-9.]*(?:-[a-z0-9]+)*)'
    rf'-{VERSION_PATTERN}'
)


class PyenvPythonSpec(NamedTuple):
    """Contains specification about a Python Interpreter"""

    string_spec: str
    implementation: str
    version: str
    variant: Optional[str]

    @classmethod
    def from_string_spec(cls, string_spec: str) -> Optional[PyenvPythonSpec]:
        is_cpython = string_spec[0].isdigit()
        is_miniconda3 = string_spec.startswith('miniconda3-')
        is_src = string_spec.endswith('-src')
        if is_cpython:
            regex = CPYTHON_SPEC_REGEX
        elif is_miniconda3:
            regex = MINICONDA3_SPEC_REGEX
        else:
            regex = OTHER_SPEC_REGEX
        match = regex.fullmatch(string_spec[:-4] if is_src else string_spec)
        if not match:
            return None
        fields = match.groupdict()
        fields['string_spec'] = string_spec
        if is_cpython:
            fields['implementation'] = 'cpython'
        if is_src:
            fields['variant'] = 'src'
        else:
            fields['variant'] = None
        return cls(**fields)

    def to_dict(self) -> dict:
        return self._asdict()

import json
from pathlib import Path

import pytest

from _virtualenv_pyenv.python_spec import PyenvPythonSpec


FIXTURE_PATH = Path(__file__).parent / 'python_spec_fixture.json'


with open(FIXTURE_PATH) as fobj:
    fixture = json.load(fobj)


@pytest.mark.parametrize('actual,expected', [(
    PyenvPythonSpec.from_string_spec(spec_dict['string_spec']),
    PyenvPythonSpec(**spec_dict),
) for spec_dict in fixture['specs']])
def test_python_spec(actual, expected):
    assert actual == expected

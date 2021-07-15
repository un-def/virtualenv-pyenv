import pytest

from _virtualenv_pyenv.python_spec import PyenvPythonSpec

from tests.testlib import python_spec_fixture


@pytest.mark.parametrize('actual,expected', [(
    PyenvPythonSpec.from_string_spec(spec_dict['string_spec']),
    PyenvPythonSpec(**spec_dict),
) for spec_dict in python_spec_fixture['specs']])
def test_python_spec(actual, expected):
    assert actual == expected

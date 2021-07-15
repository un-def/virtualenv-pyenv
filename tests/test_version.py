import pytest

from _virtualenv_pyenv.version import Version

from tests.testlib import python_spec_fixture


@pytest.mark.parametrize('string_version', [
    spec_dict['version']
    for spec_dict in python_spec_fixture['specs']
    if spec_dict['implementation'] == 'cpython'
])
def test_parse_fixture_specs(string_version):
    version = Version.from_string_version(string_version)

    assert version is not None


@pytest.mark.parametrize('str_v1,str_v2,expected', [
    ('2.0', '2.0.0', True),
    ('2.0-dev', '2.0.0-dev', True),
    ('2.0a1', '2.0.0a1', True),
    ('2.0.1', '2.0', False),
    ('2.0', '2.0.0-dev', False),
    ('2.0a1', '2.0', False),
    ('2.0a1', '2.0a2', False),
    ('2.0a1', '2.0b1', False),
])
def test_eq_ne(str_v1, str_v2, expected):
    v1 = Version.from_string_version(str_v1)
    v2 = Version.from_string_version(str_v2)

    eq_result = v1 == v2
    ne_result = v1 != v2

    assert eq_result is expected
    assert ne_result is not expected


@pytest.mark.parametrize('str_v1,str_v2,expected', [
    ('2.0', '2.0.0', False),
    ('2.0.0', '2.0.1', True),
    ('2.0', '2.0.1', True),
    ('2.0.1', '2.0.0', False),
    ('2.0-dev', '2.0', True),
    ('2.1-dev', '2.0', False),
    ('2.0a3', '2.0', True),
    ('2.0a4', '2.0a5', True),
    ('2.0a10', '2.0a2', False),
    ('2.0.1b3', '2.0.0', False),
    ('2.0b3', '2.0a7', False),
    ('2.0a7', '2.0b3', True),
])
def test_lt_ge(str_v1, str_v2, expected):
    v1 = Version.from_string_version(str_v1)
    v2 = Version.from_string_version(str_v2)

    lt_result = v1 < v2
    ge_result = v1 >= v2

    assert lt_result is expected
    assert ge_result is not expected


@pytest.mark.parametrize('str_v1,str_v2,expected', [
    ('2.0', '2.0.0', False),
    ('2.0.0', '2.0.1', False),
    ('2.0', '2.0.1', False),
    ('2.0.1', '2.0.0', True),
    ('2.0-dev', '2.0', False),
    ('2.1-dev', '2.0', True),
    ('2.0a3', '2.0', False),
    ('2.0a4', '2.0a5', False),
    ('2.0a10', '2.0a2', True),
    ('2.0.1b3', '2.0.0', True),
    ('2.0b3', '2.0a7', True),
    ('2.0a7', '2.0b3', False),
])
def test_gt_le(str_v1, str_v2, expected):
    v1 = Version.from_string_version(str_v1)
    v2 = Version.from_string_version(str_v2)

    gt_result = v1 > v2
    le_result = v1 <= v2

    assert gt_result is expected
    assert le_result is not expected

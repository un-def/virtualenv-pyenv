import logging
import os
import re

import pytest
from virtualenv.config.cli.parser import VirtualEnvOptions

from _virtualenv_pyenv.discovery import PyenvCompat, PyenvFallback, PyenvStrict


if os.name == 'nt':
    PYTHON_EXECUTABLE = 'python.exe'
    BIN_DIR = ''
else:
    PYTHON_EXECUTABLE = 'python'
    BIN_DIR = 'bin'


discovery_class = pytest.mark.discovery_class.with_args


def pytest_generate_tests(metafunc):
    if 'discovery_class' not in metafunc.fixturenames:
        return
    if marker := metafunc.definition.get_closest_marker('discovery_class'):
        discovery_classes = marker.args
    else:
        discovery_classes = (PyenvCompat, PyenvFallback, PyenvStrict)
    metafunc.parametrize('discovery_class', discovery_classes)


@pytest.fixture
def pyenv_root(mocker, tmp_path):
    mocker.patch('pyenv_inspect.path.get_pyenv_root', return_value=tmp_path)
    (tmp_path / 'versions').mkdir()
    return tmp_path


@pytest.fixture
def options(mocker):
    _options = VirtualEnvOptions()
    _options.env = mocker.Mock(name='env')
    _options.app_data = mocker.Mock(name='app_data')
    return _options


@pytest.fixture
def python_info_mock(mocker):
    return mocker.Mock(name='python_info')


@pytest.fixture
def from_exe_mock(mocker, python_info_mock):
    return mocker.patch(
        'virtualenv.discovery.py_info.PythonInfo.from_exe',
        return_value=python_info_mock,
    )


@pytest.fixture
def builtin_python_info_mock(mocker):
    return mocker.Mock(name='builtin_python_info')


@pytest.fixture
def builtin_get_interpreter_mock(mocker, builtin_python_info_mock):
    return mocker.patch(
        'virtualenv.discovery.builtin.get_interpreter',
        return_value=builtin_python_info_mock,
    )


@pytest.fixture
def error_log(caplog):
    caplog.set_level(logging.ERROR)
    return caplog


def _assert_no_error_message(error_log):
    assert not error_log.messages


def _assert_error_message(error_log, pattern):
    assert len(error_log.messages) == 1
    message = error_log.messages[0]
    assert re.search(pattern, message, flags=re.I) is not None, message


def _prepare_versions(pyenv_root, versions, expected_version=None):
    expected_bin_path = None
    for version in versions:
        bin_dir = pyenv_root / 'versions' / version / BIN_DIR
        bin_dir.mkdir(parents=True)
        bin_path = bin_dir / PYTHON_EXECUTABLE
        bin_path.touch(mode=0o777)
        if version == expected_version:
            expected_bin_path = bin_path
    return expected_bin_path


@discovery_class(PyenvCompat, PyenvFallback)
def test_no_specifier_ok_if_compat_or_fallback(
    monkeypatch, discovery_class, options, python_info_mock, from_exe_mock,
    builtin_get_interpreter_mock, error_log,
):
    monkeypatch.setattr('sys.executable', '/sys/executable/python')
    options.python = []
    discovery = discovery_class(options)

    result = discovery.run()

    assert result is python_info_mock
    from_exe_mock.assert_called_once_with(
        '/sys/executable/python',
        app_data=options.app_data,
        env=options.env,
    )
    builtin_get_interpreter_mock.assert_not_called()
    _assert_no_error_message(error_log)


@discovery_class(PyenvStrict)
def test_no_specifier_error_if_strict(
    monkeypatch, discovery_class, options, from_exe_mock,
    builtin_get_interpreter_mock, error_log,
):
    monkeypatch.setattr('sys.executable', '/sys/executable/python')
    options.python = []
    discovery = discovery_class(options)

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_not_called()
    _assert_error_message(error_log, r'interpreter is not specified')


@pytest.mark.parametrize('sys_executable', ['', None])
@discovery_class(PyenvCompat, PyenvFallback)
def test_no_specifier_error_if_no_sys_executable(
    monkeypatch, discovery_class, options, from_exe_mock,
    builtin_get_interpreter_mock, error_log, sys_executable,
):
    monkeypatch.setattr('sys.executable', sys_executable)
    options.python = []
    discovery = discovery_class(options)

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_not_called()
    _assert_error_message(
        error_log, r'failed to discover the default interpreter')


@pytest.mark.parametrize('requested_versions', [
    ['/path/to/bin/python3.7'],
    ['./python3.10'],
    ['bin/python3.10'],
    ['C:\\Path\\To\\Bin\\python.exe'],
    ['.\\python.exe'],
    ['/path/to/bin/python3.7', '/path/to/bin/python3.10'],
])
@discovery_class(PyenvCompat, PyenvFallback)
def test_file_path_ok_if_compat_or_fallback(
    discovery_class, options, python_info_mock, from_exe_mock,
    builtin_get_interpreter_mock, error_log, requested_versions,
):
    options.python = requested_versions
    discovery = discovery_class(options)

    result = discovery.run()

    assert result is python_info_mock
    from_exe_mock.assert_called_once_with(
        requested_versions[0],
        app_data=options.app_data,
        env=options.env,
    )
    builtin_get_interpreter_mock.assert_not_called()
    _assert_no_error_message(error_log)


@discovery_class(PyenvStrict)
def test_file_path_error_if_strict(
    discovery_class, options, from_exe_mock, builtin_get_interpreter_mock,
    error_log,
):
    options.python = ['/path/to/python']
    discovery = discovery_class(options)

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_not_called()
    _assert_error_message(error_log, r'paths are not allowed')


@pytest.mark.parametrize('versions,requested_versions,expected_version', [
    # pyenv-style, pre/dev-release
    (['3.12-dev', '3.12.0a3'], ['3.12-dev'], '3.12-dev'),
    (['3.12-dev', '3.12.0a3'], ['3.12.0a3'], '3.12.0a3'),
    (['3.15-dev', '3.15t-dev'], ['3.15-dev'], '3.15-dev'),
    (['3.15-dev', '3.15t-dev'], ['3.15t-dev'], '3.15t-dev'),
    (['3.15.0a1', '3.15.0a1t'], ['3.15.0a1'], '3.15.0a1'),
    (['3.15.0a1', '3.15.0a1t'], ['3.15.0a1t'], '3.15.0a1t'),
    # pyenv-style, final release
    (['3.7.2', '3.7.11', '3.8.1'], ['3'], '3.8.1'),
    (['3.7.2', '3.7.11', '3.8.1'], ['3.7'], '3.7.11'),
    (['3.6.1', '3.6.5', '3.7.2', '3.7.11'], ['3.7.8', '3.6'], '3.6.5'),
    (['3.6.1', '3.6.5', '3.7.2', '3.7.8'], ['3.7.8', '3.6'], '3.7.8'),
    (['3.13.5', '3.13.6t'], ['3.13'], '3.13.5'),
    (['3.13.5', '3.13.6t'], ['3.13t'], '3.13.6t'),
    (['3.13.5', '3.14.0t'], ['3'], '3.13.5'),
    (['3.13.5t', '3.14.0'], ['3t'], '3.13.5t'),
    # virtualenv, tox-style
    (['3.7.2', '3.7.11', '3.8.1'], ['py3'], '3.8.1'),
    (['3.7.2', '3.7.11', '3.8.1'], ['py37'], '3.7.11'),
    (['3.7.2', '3.7.11', '3.8.1'], ['py3.7'], '3.7.11'),
    (['3.7.2', '3.7.11', '3.8.1'], ['cpython3'], '3.8.1'),
    (['3.7.2', '3.7.11', '3.8.1'], ['cpython37'], '3.7.11'),
    (['3.7.2', '3.7.11', '3.8.1'], ['cpython3.7'], '3.7.11'),
    (['3.7.2', '3.11.1', '3.11.0'], ['py311'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['py3.11'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['cpython311'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['cpython3.11'], '3.11.1'),
    (['3.7.2', '3.14.1t', '3.14.0'], ['py314'], '3.14.0'),
    (['3.7.2', '3.14.1', '3.14.0t'], ['py314t'], '3.14.0t'),
    (['3.7.2', '3.14.1t', '3.14.0'], ['py3.14'], '3.14.0'),
    (['3.7.2', '3.14.1', '3.14.0t'], ['py3.14t'], '3.14.0t'),
    (['3.7.2', '3.14.1t', '3.14.0'], ['cpython314'], '3.14.0'),
    (['3.7.2', '3.14.1', '3.14.0t'], ['cpython314t'], '3.14.0t'),
    (['3.7.2', '3.14.1t', '3.14.0'], ['cpython3.14'], '3.14.0'),
    (['3.7.2', '3.14.1', '3.14.0t'], ['cpython3.14t'], '3.14.0t'),
    # virtualenv, other
    (['3.7.2', '3.11.1', '3.11.0'], ['311'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['311-32'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['py3.11.0'], '3.11.0'),
    (['3.7.2', '3.11.1', '3.11.0'], ['py3.11.0-64'], '3.11.0'),
    (['3.7.2', '3.11.1', '3.11.0'], ['python3'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['python3.11'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['python3.11.0'], '3.11.0'),
    (['3.7.2', '3.11.1', '3.11.0'], ['python311'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['python311-64'], '3.11.1'),
    (['3.7.2', '3.11.1', '3.11.0'], ['cpython3.11.0'], '3.11.0'),
    (['3.7.2', '3.11.1', '3.11.0'], ['cpython3.11.0-32'], '3.11.0'),
    (['3.7.2', '3.14.1t', '3.14.0'], ['python314'], '3.14.0'),
    (['3.7.2', '3.14.1', '3.14.0t'], ['python314t'], '3.14.0t'),
    (['3.7.2', '3.14.1t', '3.14.0'], ['python3.14'], '3.14.0'),
    (['3.7.2', '3.14.1', '3.14.0t'], ['python3.14t'], '3.14.0t'),
])
def test_cpython_ok(
    discovery_class, pyenv_root, options, python_info_mock, from_exe_mock,
    builtin_get_interpreter_mock, error_log, versions, requested_versions,
    expected_version,
):
    options.python = requested_versions
    discovery = discovery_class(options)
    expected_bin_path = _prepare_versions(
        pyenv_root, versions, expected_version)

    result = discovery.run()

    assert result is python_info_mock
    from_exe_mock.assert_called_once_with(
        str(expected_bin_path),
        app_data=options.app_data,
        env=options.env,
    )
    builtin_get_interpreter_mock.assert_not_called()
    _assert_no_error_message(error_log)


@pytest.mark.parametrize('versions,requested_versions', [
    (['3.6.2', '3.6.11', '3.8.1'], ['2']),
    (['3.6.2', '3.6.11', '3.8.1'], ['3.7']),
    (['3.6.1', '3.6.5', '3.7.2', '3.7.11'], ['3.7.8', '3.6.4']),
    # pre/dev releases require _exact_ match
    (['3.12-dev', '3.12.0a3'], ['3.12']),
    (['3.12-dev', '3.12.0a3'], ['3.12.0a2']),
])
@discovery_class(PyenvCompat, PyenvStrict)
def test_cpython_no_match_no_fallback_if_compat_or_strict(
    discovery_class, pyenv_root, options, from_exe_mock,
    builtin_get_interpreter_mock, error_log, versions, requested_versions,
):
    options.python = requested_versions
    discovery = discovery_class(options)
    _prepare_versions(pyenv_root, versions)

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_not_called()
    _assert_no_error_message(error_log)


@discovery_class(PyenvFallback)
def test_cpython_no_match_fall_back_to_builtin_if_fallback(
    discovery_class, pyenv_root, options, from_exe_mock,
    builtin_python_info_mock, builtin_get_interpreter_mock, error_log,
):
    options.python = ['3.7']
    discovery = discovery_class(options)
    _prepare_versions(pyenv_root, ['3.6.2', '3.6.11', '3.8.1'])

    result = discovery.run()

    assert result is builtin_python_info_mock
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_called()
    _assert_no_error_message(error_log)


def test_cpython_spec_parse_error(
    discovery_class, options, from_exe_mock, builtin_get_interpreter_mock,
    error_log,
):
    options.python = ['37.7']
    discovery = discovery_class(options)

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_not_called()
    _assert_error_message(error_log, r'failed to parse version: 37\.7')


@pytest.mark.parametrize('requested_version', ['py', 'python', 'cpython'])
def test_cpython_major_required(
    discovery_class, pyenv_root, options, from_exe_mock,
    builtin_get_interpreter_mock, error_log, requested_version,
):
    options.python = [requested_version]
    discovery = discovery_class(options)
    _prepare_versions(pyenv_root, ['3.11.0a1', '3.11.1', '3.11-dev'])

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_not_called()
    _assert_error_message(error_log, r'major .+ required')


@pytest.mark.parametrize('requested_version', [
    'pypy37', 'ironpython3.8', 'somefancyforkpython3.10',
])
def test_unsupported(
    discovery_class, pyenv_root, options, from_exe_mock,
    builtin_get_interpreter_mock, error_log, requested_version,
):
    options.python = [requested_version]
    discovery = discovery_class(options)
    _prepare_versions(pyenv_root, ['3.11.0a1', '3.11.1', '3.11-dev'])

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()
    builtin_get_interpreter_mock.assert_not_called()
    _assert_error_message(error_log, r'only cpython .+ supported')

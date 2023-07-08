import pytest

from _virtualenv_pyenv.discovery import Pyenv


@pytest.fixture
def pyenv_root(mocker, tmp_path):
    mocker.patch('pyenv_inspect.path.get_pyenv_root', return_value=tmp_path)
    (tmp_path / 'versions').mkdir()
    return tmp_path


@pytest.fixture
def options_mock(mocker):
    mock = mocker.Mock(name='options')
    mock.env = mocker.Mock(name='env')
    mock.app_data = mocker.Mock(name='app_data')
    return mock


@pytest.fixture
def python_info_mock(mocker):
    return mocker.Mock(name='python_info')


@pytest.fixture
def from_exe_mock(mocker, python_info_mock):
    return mocker.patch(
        'virtualenv.discovery.py_info.PythonInfo.from_exe',
        return_value=python_info_mock,
    )


def _prepare_versions(pyenv_root, versions, expected_version=None):
    expected_bin_path = None
    for version in versions:
        bin_dir = pyenv_root / 'versions' / version / 'bin'
        bin_dir.mkdir(parents=True)
        bin_path = bin_dir / 'python'
        bin_path.touch(mode=0o777)
        if version == expected_version:
            expected_bin_path = bin_path
    return expected_bin_path


@pytest.mark.parametrize('requested_versions', [
    ['/path/to/bin/python3.7'],
    ['./python3.10'],
    ['bin/python3.10'],
    ['C:\\Path\\To\\Bin\\python.exe'],
    ['.\\python.exe'],
    ['/path/to/bin/python3.7', '/path/to/bin/python3.10'],
])
def test_file_path(
    options_mock, python_info_mock, from_exe_mock, requested_versions,
):
    options_mock.python = requested_versions
    discovery = Pyenv(options_mock)

    result = discovery.run()

    assert result is python_info_mock
    from_exe_mock.assert_called_once_with(
        requested_versions[0],
        app_data=options_mock.app_data,
        env=options_mock.env,
    )


@pytest.mark.parametrize('versions,requested_versions,expected_version', [
    (['3.7.2', '3.7.11', '3.8.1'], ['3.7'], '3.7.11'),
    (['3.6.1', '3.6.5', '3.7.2', '3.7.11'], ['3.7.8', '3.6'], '3.6.5'),
    (['3.6.1', '3.6.5', '3.7.2', '3.7.8'], ['3.7.8', '3.6'], '3.7.8'),
])
def test_cpython_ok(
    pyenv_root, options_mock, python_info_mock, from_exe_mock,
    versions, requested_versions, expected_version,
):
    options_mock.python = requested_versions
    discovery = Pyenv(options_mock)
    expected_bin_path = _prepare_versions(
        pyenv_root, versions, expected_version)

    result = discovery.run()

    assert result is python_info_mock
    from_exe_mock.assert_called_once_with(
        str(expected_bin_path),
        app_data=options_mock.app_data,
        env=options_mock.env,
    )


@pytest.mark.parametrize('versions,requested_versions', [
    (['3.6.2', '3.6.11', '3.8.1'], ['3.7']),
    (['3.6.1', '3.6.5', '3.7.2', '3.7.11'], ['3.7.8', '3.6.4']),
])
def test_cpython_no_match(
    pyenv_root, options_mock, from_exe_mock, versions, requested_versions,
):
    options_mock.python = requested_versions
    discovery = Pyenv(options_mock)
    _prepare_versions(pyenv_root, versions)

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()


def test_cpython_spec_parse_error(options_mock, from_exe_mock):
    options_mock.python = '37.7'
    discovery = Pyenv(options_mock)

    result = discovery.run()

    assert result is None
    from_exe_mock.assert_not_called()

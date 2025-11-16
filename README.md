# virtualenv-pyenv

[![GitHub License](https://img.shields.io/github/license/un-def/virtualenv-pyenv?style=flat-square)](https://github.com/un-def/virtualenv-pyenv/blob/master/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/virtualenv-pyenv?style=flat-square)](https://pypi.org/project/virtualenv-pyenv/)
[![PyPI - Version](https://img.shields.io/pypi/v/virtualenv-pyenv?style=flat-square)](https://pypi.org/project/virtualenv-pyenv/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/virtualenv-pyenv?style=flat-square)](https://pypi.org/project/virtualenv-pyenv/)
[![GitHub Repo stars](https://img.shields.io/github/stars/un-def/virtualenv-pyenv?style=flat-square)](https://github.com/un-def/virtualenv-pyenv/stargazers)

A [virtualenv][virtualenv] Python discovery plugin for [pyenv][pyenv]–installed interpreters

## Installation

```shell
pip install virtualenv-pyenv
```

## Usage

The Python discovery mechanism can be specified by:

* the CLI option `--discovery`:
  ```shell
  virtualenv --discovery pyenv -p 3.10 testenv
  ```

* the environment variable `VIRTUALENV_DISCOVERY`:
  ```shell
  export VIRTUALENV_DISCOVERY=pyenv
  virtualenv -p 3.10 testenv
  ```

* the [config][virtualenv-docs-config-file] option `discovery`:
  ```ini
  [virtualenv]
  discovery = pyenv
  ```

  ```shell
  virtualenv -p 3.10 testenv
  ```

* the [virtualenvwrapper][virtualenvwrapper] environment variable `VIRTUALENVWRAPPER_VIRTUALENV_ARGS`:
  ```shell
  export VIRTUALENVWRAPPER_VIRTUALENV_ARGS='--discovery=pyenv'
  mkvirtualenv -p 3.10 testenv
  ```

## Operation Mode

The plugin supports several operation modes. The operation mode affects various aspects of the discovery process.

|mode      |specifier|path specifier|fallback to `builtin`|
|----------|---------|--------------|---------------------|
|`compat`  |optional |allowed       |no                   |
|`fallback`|optional |allowed       |yes                  |
|`strict`  |required |error         |no                   |

The mode is specified as a part of the discovery method name: `pyenv-{mode}`, e.g.,

```shell
virtualenv --discovery=pyenv-fallback -p 3.10 testenv
```

or

```shell
export VIRTUALENV_DISCOVERY=pyenv-strict
virtualenv -p 3.10 testenv
```

If no mode is specified, the `compat` mode is used, that is, `--discovery=pyenv` is the same as `--discovery=pyenv-compat`.

The `compat` mode is recommended for most cases. It mimics closely the `builtin` discovery plugin to maximize compatibility with existing tools (e.g., [build][build], [tox][tox]):

* if no specifier is provided, the plugin falls back to `sys.executable`, even if it is not installed by pyenv;
* if a path specifier (`-p /path/to/bin/python`) is provided, the path is used, even if it is not installed by pyenv;
* otherwise (`-p 3.7`, `-p py37`), only pyenv–installed interpreters are used.

The `fallback` mode is the same as `compat`, but in addition falls back to the `builtin` plugin if no interpreter was found. If multiple specifiers are provided, all of them are tried first before falling back to the `builtin` plugin as a last resort.

The `strict` mode, as its name suggests, ensures that only pyenv–installed interpreters are used:

* a specifier is required, `sys.executable` is never used as a fallback, even if it is installed by pyenv (may be relaxed in the future);
* a path specifier is not allowed, even if the path points to a pyenv–installed interpreter (may be relaxed in the future);
* no fallback to the `builtin` plugin.

## Python Specifier Format

The plugin supports two specifier formats informally called “pyenv-style” and “virtualenv-style”.

The version part of both specifier formats can contain one (`major`), two (`major.minor`), or three (`major.minor.patch`) components. When a one–component version is specified, the latest installed final minor release is selected, ignoring pre–/dev–release. When a two–component version is specified, the latest installed final patch release is selected, ignoring pre–/dev–releases. When a three–component version is specified, the exact final release is selected, ignoring pre–/dev–releases. The pre–/dev–release version is selected only if it is explicitly requested.

|installed                  |requested |selected  |
|---------------------------|----------|----------|
|`3.9.5`; `3.9.17`, `3.10.0`|`3`       |`3.10.0`  |
|`3.9.5`; `3.9.17`, `3.10.0`|`3.9`     |`3.9.17`  |
|`3.9.5`; `3.9.17`, `3.10.0`|`3.9.5`   |`3.9.5`   |
|`3.9.5`; `3.9.17`, `3.10.0`|`3.9.0`   |—         |
|`3.12-dev`; `3.12.0b3`     |`3.12`    |—         |
|`3.12-dev`; `3.12.0b3`     |`3.12.0`  |—         |
|`3.12-dev`; `3.12.0b3`     |`3.12-dev`|`3.12-dev`|
|`3.12-dev`; `3.12.0b3`     |`3.12.0b3`|`3.12.0b3`|

### pyenv–style

The same format as used by [pyenv][pyenv] (`pyenv install --list`).

* a final version with 1 version component: `3`, `3t`
* a final version with 2 version components: `3.11`, `3.14t`
* a final version with 3 version components: `3.11.2`, `3.14.1t`
* a pre–release version: `3.13.0a4`, `3.12.0b3`, `3.11.0rc1`, `3.15.0a1t`
* a dev version: `3.13-dev`, `3.15t-dev`

### virtualenv–style

The same format as used by [virtualenv][virtualenv] ([docs][virtualenv-docs-specifier-format]). A subset of this format is used by [tox][tox] ([docs][tox-docs-testenv-factors]).

* a relative or absolute path: `/path/to/bin/python` (it can be any Python interpreter, not only installed by pyenv)
* a final version with 1 version component: `py3`, `python3`, `cpython3`, `python3-32`, `py3-64`, `py3t`, `python3t`
* a final version with 2 version components: `311`, `py311`, `py3.11`, `python311`, `cpython3.11`, `python3.11-32`, `py311-64`, `314t`, `py314t`, `cpython3.14t`
* a final version with 3 version components: `py3.11.2`, `python3.11.2`, `cpython3.11.2`, `python3.11.2-32`, `py3.11.2-64`, `py3.14.0t`, `cpython3.14.0t`

## Limitations

* Only CPython is supported at the moment.
* The `architecture` part (`-32`/`-64`) of a specifier is ignored. For example, all of the following specifiers match any installed CPython 3.8.1 regardless of the architecture: `python3.8.1`, `python3.8.1-32`, `python3.8.1-64`.

## Internals

virtualenv-pyenv does not rely on pyenv to discover Python interpreters, that is, it never calls any pyenv command and does not require pyenv to be in `PATH`. Instead, the plugin uses [pyenv-inspect][pyenv-inspect] library, which, in turn, inspects `$PYENV_ROOT/versions` directory contents.


[virtualenv]: https://virtualenv.pypa.io/
[pyenv]: https://github.com/pyenv/pyenv
[virtualenvwrapper]: https://virtualenvwrapper.readthedocs.io/en/latest/
[tox]: https://tox.wiki/en/latest/
[pyenv-inspect]: https://github.com/un-def/pyenv-inspect
[build]: https://github.com/pypa/build
[virtualenv-docs-config-file]: https://virtualenv.pypa.io/en/latest/cli_interface.html#configuration-file
[virtualenv-docs-specifier-format]: https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery
[tox-docs-testenv-factors]: https://tox.wiki/en/latest/user_guide.html#test-environments

# virtualenv-pyenv

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

## Python Specifier Format

The plugin supports two specifier formats informally called “pyenv-style” and “virtualenv-style”.

The version part of both specifier formats can contain either two (`major.minor`) or three (`major.minor.patch`) components. When a two–component version is specified, the latest installed final patch release is selected, ignoring pre–/dev–releases. When a three–component version is specified, the exact final release is selected, ignoring pre–/dev–releases. The pre–/dev–release version is installed only if it is explicitly requested.

|installed             |requested |selected  |
|----------------------|----------|----------|
|`3.9.5`; `3.9.17`     |`3.9`     |`3.9.17`  |
|`3.9.5`; `3.9.17`     |`3.9.5`   |`3.9.5`   |
|`3.9.5`; `3.9.17`     |`3.9.0`   |—         |
|`3.12-dev`; `3.12.0b3`|`3.12`    |—         |
|`3.12-dev`; `3.12.0b3`|`3.12.0`  |—         |
|`3.12-dev`; `3.12.0b3`|`3.12-dev`|`3.12-dev`|
|`3.12-dev`; `3.12.0b3`|`3.12.0b3`|`3.12.0b3`|

### pyenv–style

The same format as used by [pyenv][pyenv] (`pyenv install --list`).

* a final version with 2 version components: `3.11`
* a final version with 3 version components: `3.11.2`
* a pre–release version: `3.13.0a4`, `3.12.0b3`, `3.11.0rc1`
* a dev version: `3.13-dev`

### virtualenv–style

The same format as used by [virtualenv][virtualenv] ([docs][virtualenv-docs-specifier-format]). A subset of this format is used by [tox][tox] ([docs][tox-docs-testenv-factors]).

* a relative or absolute path: `/path/to/bin/python` (it can be any Python interpreter, not only installed by pyenv)
* a final version with 2 version components: `311`, `py311`, `py3.11`, `python311`, `cpython3.11`, `python3.11-32`, `py311-64`
* a final version with 3 version components: `py3.11.2`, `python3.11.2`, `cpython3.11.2`, `python3.11.2-32`, `py3.11.2-64`

## Limitations

* Only CPython is supported at the moment.
* The `architecture` part (`-32`/`-64`) of a specifier is ignored. For example, all of the following specifiers match any installed CPython 3.8.1 regardless of the architecture: `python3.8.1`, `python3.8.1-32`, `python3.8.1-64`.
* [pyenv-win][pyenv-win] is not supported.

## Internals

virtualenv-pyenv does not rely on pyenv to discover Python interpreters, that is, it never calls any pyenv command and does not require pyenv to be in `PATH`. Instead, the plugin uses [pyenv-inspect][pyenv-inspect] library, which, in turn, inspects `$PYENV_ROOT/versions` directory contents.


[virtualenv]: https://virtualenv.pypa.io/
[pyenv]: https://github.com/pyenv/pyenv
[virtualenvwrapper]: https://virtualenvwrapper.readthedocs.io/en/latest/
[tox]: https://tox.wiki/en/latest/
[pyenv-inspect]: https://github.com/un-def/pyenv-inspect
[pyenv-win]: https://github.com/pyenv-win/pyenv-win
[virtualenv-docs-config-file]: https://virtualenv.pypa.io/en/latest/cli_interface.html#configuration-file
[virtualenv-docs-specifier-format]: https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery
[tox-docs-testenv-factors]: https://tox.wiki/en/latest/user_guide.html#test-environments

# virtualenv-pyenv

A [virtualenv][virtualenv] Python discovery plugin using [pyenv][pyenv]

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
  virtualenv pyenv -p 3.10 testenv
  ```

The Python version can be expressed using either 2 or 3 version segments:

* `-p 3.9`
* `-p 3.9.3`

In the former case, the latest version found will be used.

## Limitations

Only CPython is supported at the moment.


[virtualenv]: https://virtualenv.pypa.io/
[pyenv]: https://github.com/pyenv/pyenv
[virtualenv-docs-config-file]: https://virtualenv.pypa.io/en/latest/cli_interface.html#configuration-file

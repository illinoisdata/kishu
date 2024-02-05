# Making a new release of kishuboard

The extension can be published to `PyPI` manually.

## Manual release

Before executing the following commands, make sure **you are in the same directory as this README file**.

### Python package

First, make sure you have npm installed, and then run the following command to build the frontend:

```bash
npm run build
```

This extension can be distributed as Python packages. All of the Python
packaging instructions are in the `pyproject.toml` file to wrap your extension in a
Python package. Before generating a package, you need to install some tools:

```bash
pip install build twine hatch 
```

Bump the version using `hatch`. By default this will create a tag.
See the docs on [hatch-nodejs-version](https://github.com/agoose77/hatch-nodejs-version#semver) for details.

```bash
hatch version <new-version>
```

Then build the server using the following command, which will package the frontend and backend together to dist directory:

```bash
python -m build
```

> `python setup.py sdist bdist_wheel` is deprecated and will not work for this package.

Then to upload the package to PyPI, do:

```bash
twine upload dist/*
```
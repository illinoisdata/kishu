# kishu

Intelligent checkpointing framework for Python-based machine learning and scientific computing.
Under development as part of a research project at the University of Illinois at Urbana-Champaign.

`kishu` contains core Kishu components: a Jupyter instrument and a library of Kishu commands. Main user interface is Kishu's command line interface (CLI): `kishu`.


# Installation

Install from PyPI.
```
pip install kishu
```

## Development

Installing Kishu in the editable mode.

```bash
make install
```

Formatting source code.

```bash
make fmt
```

Linting source code (e.g., definitions, type checking).

```bash
make lint
```

Running all unit tests. It generates a coverage report at `./htmlcov/index.html`.
```bash
make test
```

Running PyTest with benchmarks.
```bash
pytest --run-benchmark
```

## Versioning

See (Semantic Versioning)[https://semver.org] for a guideline on incrementing the version number in `pyproject.toml` and `kishu/__init__.py`.

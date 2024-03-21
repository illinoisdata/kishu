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
pip install -e kishu/[dev]
```

Running PyTest.
```bash
pytest
```

Running PyTest with benchmarks.
```bash
pytest --run-benchmark
```

Running PyTest with code coverage.
```bash
pytest --cov=kishu/ --cov-report=xml
head coverage.xml
```

Running formatting checker (flake8).
```bash
flake8 kishu/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 kishu/ tests/ --count --max-complexity=100 --max-line-length=127 --statistics
```

Running static analysis (e.g., type checks).
```bash
mypy kishu/*.py kishu/*/*.py tests/*.py tests/*/*.py
```

# Deployment

The following command will upload this project to pypi (https://pypi.org/project/kishu/).

```
bash upload2pypi.sh
```

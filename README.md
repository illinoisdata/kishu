# Elastic Notebook

Intelligent scaling of stateful Python applications (e.g. a Jupyter notebook using an IPython kernel) that optimizies the tradeoff between recomputation overhead and cold storage access latency.

## Getting Started

- Installing the package
```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

- Running Pytest
```
pytest -rP
```

## Links to Documents

- Dependency Graph Framework
  - https://docs.google.com/document/d/1a6UynGXZo3HIRpSWpqpjUcTtjy-1cByYe75zMG530Cw/edit

- Recomputation Examples
  - https://docs.google.com/presentation/d/1zLSgz4GHCYA8mXcJf9jEyUBp5VqQkWL7poH06dsDIyA/edit#slide=id.g11915a2d31c_1_53

## Tracker

| Status             | Last Updated | Description                    | 
| ------------------ | ------------ | ------------------------------ |
| :white_check_mark: |  2022-05-02  | Framework for dependency graph and recomputation search |
| :white_check_mark: |  2022-02-18  | Setup GitHub actions for tests |
| :white_check_mark: |  2022-04-04  | Setup experiment (storage adapter, object pickling, etc.) |

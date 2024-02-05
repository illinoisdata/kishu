[![build status](https://github.com/illinoisdata/kishu/actions/workflows/kishu.yml/badge.svg)](htps://github.com/illinoisdata/kishu)
[![codecov](https://codecov.io/gh/illinoisdata/kishu/graph/badge.svg?token=14WRVYQBZO)](https://codecov.io/gh/illinoisdata/kishu)
[![Python version](https://img.shields.io/pypi/pyversions/kishu)](https://pypi.org/project/kishu/)
[![PyPi version](https://img.shields.io/pypi/v/kishu)](https://pypi.org/project/kishu/)
<!---
[![commits last month](https://img.shields.io/github/commit-activity/m/illinoisdata/ElasticNotebook)](htps://github.com/illinoisdata/kishu)
[![GitHub stars](https://img.shields.io/github/stars/illinoisdata/ElasticNotebook)](htps://github.com/illinoisdata/kishu)
--->

# Kishu 

Kishu is a system for intelligent versioning of notebook session states on Jupyter-based platforms (e.g. JupyterLab, Jupyter Hub). It allows users to easily manage complex user-defined variables in sessions such as machine learning models, plots, and dataframes through a Git-like commit and checkout interface.

## Getting Started

- Installing the package
```
python3 -m venv .env
source .env/bin/activate
pip install -r kishu/requirements.txt
pip install kishu/
```

- Running PyTest
```
pytest -vv
```

## Using Kishu CLI

**Adding Kishu to your notebook:** Kishu can be added to any notebook through running the following command:

```
kishu init {{notebook name}}
```

**Cell execution tracking:** After adding Kishu to a notebook, it will begin tracking user cell executions and commit the session state to its database after each cell execution. Users can see their execution history with the following command:

```
kishu log {{notebook name}}
```

**Checking out:** The following command is used to restore to/checkout a previous session state. The commit IDs of states can be found via the above `kishu log` command.

```
kishu checkout {{commit id}}
```

**Manual commit:** In addition to automatically commiting session states, users can perform a manual commit with the following command:

```
kishu commit {{notebook name}} [-m {{message}}]
```

## Trying Kishu

`kishu/tests/notebooks` contains simple data science notebooks for trying Kishu on.

## Supported Libraries

- qiskit 0.45.0
- scikit-learn 1.1.3
- numpy 1.24.4
- scipy 1.3.2
- pandas 1.4.1
- matplotlib 3.7.3
- textblob 0.17.1
- nltk 3.8.1
- tqdm 4.66.1
- Seaborn 0.13.0

**To be added in the future**:
- Polars
- PyTorch
- Tensorflow
- Arrow
- Dask
- LigthGBM


## Learn More

Kishu's efficiency is enabled by its low-overhead session state monitoring, deduplicated variable storage, and optimized recomputation-assisted checkout. Our papers on Kishu can be found here; don't forget to star our repository and cite our papers if you like our work!

- [ElasticNotebook: Enabling Live Migration for Computational Notebooks](https://arxiv.org/abs/2309.11083)
- [Transactional Python for Durable Machine Learning: Vision, Challenges, and Feasibility](https://dl.acm.org/doi/abs/10.1145/3595360.3595855)

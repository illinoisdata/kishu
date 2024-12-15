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

Installing the package from PyPI. For development, see further instructions below.

```bash
pip install kishu kishuboard jupyterlab_kishu
```

## Using Kishu CLI

**Adding Kishu to your notebook:** Kishu can be added to any notebook through running the following command:

```bash
kishu init {{notebook name}}
```

**Cell execution tracking:** After adding Kishu to a notebook, it will begin tracking user cell executions and commit the session state to its database after each cell execution. Users can see their execution history with the following command:

```bash
kishu log {{notebook name}}
```

**Checking out:** The following command is used to restore to/checkout a previous session state. The commit IDs of states can be found via the above `kishu log` command.

```bash
kishu checkout {{commit id}}
```

**Manual commit:** In addition to automatically commiting session states, users can perform a manual commit with the following command:

```bash
kishu commit {{notebook name}} [-m {{message}}]
```

## Using Kishu inside JupyterLab and Jupyter Notebook 7

After installing `jupyterlab_kishu`, "Kishu" tab will appear on Jupyter's menu bar. Alternatively, Kishu commands are also listed in Jupyter's command palette with "Kishu:" prefix.

## Trying Kishu

`kishu/tests/notebooks` contains simple data science notebooks to try Kishu on.

## Migrating Checkpoints

Kishu's per-notebook checkpoint files are stored under the `~/.kishu/` directory. For example, Kishu will store the checkpoint files for notebook with name `Untitled` under `~/.kishu/Untitled`. These checkpoints can be copied, along with the notebook, to a new machine where Kishu is installed for elastic migration.

## Configuring Kishu

Kishu can be configured through editing the `~/.kishu/config.ini` file. A full list of configurable options can be found [here](https://github.com/illinoisdata/kishu/blob/main/docs/src/usage.rst).

## Coverage

The list of libraries that Kishi is compatible with can be found [here](https://github.com/illinoisdata/kishu/blob/main/docs/src/supported_libraries.rst).

## Limitations

There are certain objects and cases for which Kishu may fail to correctly checkpoint. You can learn more about them [here](https://github.com/illinoisdata/kishu/blob/main/docs/src/unsupported_cases.rst). 

## Learn More

Kishu's efficiency is enabled by its low-overhead session state monitoring, deduplicated variable storage, and optimized recomputation-assisted checkout. Our papers on Kishu can be found here; don't forget to star our repository and cite our papers if you like our work!

- [Kishu: Time-Traveling for Computational Notebooks](https://arxiv.org/abs/2406.13856)
- [ElasticNotebook: Enabling Live Migration for Computational Notebooks](https://arxiv.org/abs/2309.11083)
- [Transactional Python for Durable Machine Learning: Vision, Challenges, and Feasibility](https://dl.acm.org/doi/abs/10.1145/3595360.3595855)
- [Demonstration of ElasticNotebook: Migrating Live Computational Notebook States](https://dl.acm.org/doi/abs/10.1145/3626246.3654752)


```bash
(cd kishu && make install)
(cd kishuboard && make install)
(cd jupyterlab_kishu && make install)
```

Refer to development notes inside each module for further instructions.

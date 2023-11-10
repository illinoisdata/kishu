Intelligent checkpointing framework for Python-based machine learning and scientific computing. 
Under development as part of a research project at the University of Illinois at Urbana-Champaign.


# Installation

Run the following command in a [virtual environment](https://docs.python.org/3/library/venv.html).
```
python setup.py install
```


# Jupyter Integration

Run Jupyter after installing kishu. In your notebook, you can enable kishu with the following command.

## Basic Usage

```
from kishu import init_kishu
init_kishu()
```
Then, all the cell executions are recorded, and the result of each cell execution is checkpointed.


## Working with Kishu

`init_kishu()` adds a new variable `_kishu` (of type KishuJupyterExecHistory) to Jupyter's namespace.
The special variable can be used for kishu-related operations, as follows.

Browse the execution log.
```
_kishu.log()
```

See the database file.
```
_kishu.checkpoint_file()
```


Restore a state.
```
_kishu.checkout(commit_id)
```

## Checkpoint Backend

Deploy a restful server.
```
flask --app kishu/backend run
```

# Deployment

The following command will upload this project to pypi (https://pypi.org/project/kishu/).

```
bash upload2pypi.sh
```

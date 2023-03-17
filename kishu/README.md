Intelligent python checkpointing framework for machine learning and scientific computing. Under development as part of a research project at the University of Illinois at Urbana-Champaign.


# Installation

## Local Installation

No installation is needed. It is enough to enter `python` in this directory (the root of `kishu` project), then
one can use `import kishu` to import this module. Same goes for Jupyter use cases.


## System Installation

The following command will invoke `setup.py` for system-wide installation. If virtual env is in use, the module
will be installed inside the virtual environment.
```
bash install.sh
```



# Jupyter Integration

Run Jupyter after installing kishu. In your notebook, you can enable kishu with the following command.

```
%load_ext kishu
%kishu enable
```
Then, all cell executions are observed with kishu.

In order to automate this, you can add [startup scripts to your IPython configuration](https://ipython.org/ipython-doc/1/config/overview.html#startup-files).


To disable kishu, run
```
%kishu disable
```


# Deployment

The following command will upload this project to pypi (https://pypi.org/project/kishu/).

```
bash upload2pypi.sh
```

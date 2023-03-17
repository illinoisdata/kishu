Intelligent python checkpointing framework for machine learning and scientific computing. Under development as part of a research project at the University of Illinois at Urbana-Champaign.



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

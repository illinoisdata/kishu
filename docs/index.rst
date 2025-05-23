Kishu: Checkpointable and Undoable Notebook System
====================================================

`Kishu <https://github.com/illinoisdata/kishu>`_ is a system for versioning notebook session states in IPython-based notebooks (e.g. JupyterLab, Jupyter Hub). It efficiently and transparently checkpoints both variable and code states of notebook sessions, enabling users to undo cell executions and manage branching states containing objects such as ML models, plots, and dataframes via Git-like commits and checkouts.

This website is intended as a tutorial for using and configuring Kishu, as well as documenting an up-to-date list of Kishu's compatibility with and support for various Python Libraries.

.. autosummary::
   :toctree: _autosummary

.. toctree::
   :maxdepth: 1
   :caption: Using Kishu

   src/installation
   src/instructions
   src/usage

.. toctree::
   :maxdepth: 1
   :caption: Caveats

   src/supported_libraries
   src/unsupported_cases

.. toctree::
   :maxdepth: 1
   :caption: Development

   src/api

.. _GitHub: https://github.com/illinoisdata/kishu

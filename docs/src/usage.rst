Usage
=====

.. _installation:

Installation
------------

To use Kishu, first install it using pip:

.. code-block:: console

   $ pip install kishu

To use Kishu directly on JupyterLab or Jupyter Notebook 7+, install the notebook extension.

.. code-block:: console

   $ pip install jupyterlab_kishu

Getting Started
---------------


**Adding Kishu to your notebook**: Kishu can be added to any notebook through running the following command (:py:func:`kishu.cli.init`):

.. code-block:: console

   $ kishu init NOTEBOOK_PATH

**Cell execution tracking**: After adding Kishu to a notebook, it will begin tracking user cell executions and commit the session state to its database after each cell execution. Users can see their execution history with the following command:

.. code-block:: console

   $ kishu log NOTEBOOK_PATH

**Checking out**: The following command is used to restore to/checkout a previous session state. The commit IDs of states can be found via the above `kishu log` command.

.. code-block:: console

   $ kishu checkout NOTEBOOK_PATH ( COMMIT_ID | BRANCH_NAME )

**Manual commit**: In addition to automatically commiting session states, users can perform a manual commit with the following command:

.. code-block:: console

   $ kishu commit NOTEBOOK_PATH [-m MESSAGE]

**Help?**: Try `--help` to list all commands or a manual for each command.

.. code-block:: console

   $ kishu [COMMAND] --help

Configuring Kishu
---------------
Kishu can be configured through editing the `~/.kishu/config.ini` file with the below format:

.. code-block:: console

  [CATEGORY1]
  option1=value1
  option2=value2
  ...

  [CATEGORY2]
  option3=value3
  ...

The current list of available options are as follows:

Instructions
========================
Here is a video tutorial <https://youtu.be/LXg-q0yMCiw>_ for Kishu summarizing all the steps.

Step 1: Initializing Kishu on a Notebook
-----

To start protecting your notebook session, Kishu can be initialized and attached through the Kishu > Initialize/Re-attach option under the Kishu tab. Alternatively, you can use the shortcut Ctrl+K then Ctrl+I / ⌘+K then ⌘+I:

.. image:: ../images/init_clip.gif
:align: center
:width: 960

Step 2: Run Cells as Normal
-----

Once initialized, you can proceed to execute cells in the session as normal. Kishu will automatically and transparently checkpoint your variable state (imported libraries, loaded dataframes, drawn plots, fitted models, etc.) after each cell execution.

.. image:: docs/images/run_cells.gif
:align: center
:width: 960

Undoing cell executions
To undo your latest cell execution, you can use the Kishu > Undo Execution option under the Kishu tab:

.. image:: ../images/undo_clip.gif
:align: center
:width: 960

Undoing cell executions only affects the variable state. The code state (i.e., the cells you write) is untouched. This can be useful, for example, to 'un-drop' a dataframe column dropped by a cell while keeping the cell code itself intact.

Checkpointing and Checking out Notebook States
===========================

Kishu can also be used to manage branching code and variable states; it supports making checkpoints of the notebook and variable state at any point during a notebook session, which can be returned to later via a checkout.

Step 1: Committing to make a checkpoint
-----
  
Kishu can store the current state of your notebook, including both the variable state and your code state, with the Kishu > Commit option under the Kishu tab. Alternatively, you can use the shortcut Ctrl+K then Ctrl+C / ⌘+K then ⌘+C. You will be prompted to enter a commit message:

.. image:: ../images/checkpoint_clip.gif
:align: center
:width: 960

Step 2: Checkout to a checkpoint
-----

You can return to a commit with the Kishu > Checkout option under the Kishu tab. Alternatively, you can use the shortcut Ctrl+K then Ctrl+V / ⌘+K then ⌘+V. This will bring up a menu for you to select the appropriate commit:

.. image:: ../images/checkout_clip.gif
:align: center
:width: 960

Checking out will replace both the current variable and code state with that of the selected checkpoint. It will also overwrite your current variable and code state; commit to make a (second) checkpoint before checking out if you wish to keep your current notebook state.

Configuring Kishu
========================
Kishu can be configured through editing the `~/.kishu/config.ini` file with the below format:

.. code-block:: console

  [PLANNER]
  incremental_store=True
  ...

  [OPTIMIZER]
  always_migrate=True
  network_bandwidth=100000000
  ...

  [IDGRAPH]
  experimental_tracker=True
  ...

The current list of available options are as follows:

.. code-block:: console

  [PLANNER]
  incremental_store={True,False}  # Whether to enable incremental checkpointing. If enabled, Kishu only stores the changed data between subsequent checkpoints.

  [OPTIMIZER]
  always_migrate={True,False}  # Whether Kishu should always incrementally store all changed data for each checkpoint. Mutually exclusive with always_recompute.
  always_recompute={True,False}  # Whether Kishu should always recompute data (via replaying cells) for checking out (and store nothing). Mutually exclusive with always_migrate.
  network_bandwidth=(0,inf)  # Network bandwidth for Kishu to compute the optimal data to store for each checkpoint if the always_migrate and always_recompute flags are not enabled.
  ...

  [IDGRAPH]
  experimental_tracker={True,False}  # Whether to use the experimental tracker, which is faster for specific large objects (dataframes, arrays) but may incur minor loss of profiling correctness.

  [PROFILER]
  excluded_modules=[module1,module2,...]  # List of modules for Kishu to treat as unpickable.
  excluded_classes=[class1,class2,...]  # List of classes for Kishu to treat as unpickable.
  auto_add_unpicklable_object={True,False}  # Whether to automatically add unpicklable objects encountered during profiling to excluded_modules and excluded_classes.
  ...

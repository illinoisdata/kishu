import sys, os
sys.path.insert(0, os.path.abspath("../.."))
from run_experiment import run_experiment
from OptimizerType import OptimizerType

# For each notebook, run the experiment script once per optimizer.

run_experiment(notebook = "nfl.ipynb", optimizer = OptimizerType.EXACT.value)
run_experiment(notebook = "nfl.ipynb", optimizer = OptimizerType.GREEDY.value)
run_experiment(notebook = "nfl.ipynb", optimizer = OptimizerType.RANDOM.value)
run_experiment(notebook = "nfl.ipynb", optimizer = OptimizerType.MIGRATE_ALL.value)
run_experiment(notebook = "nfl.ipynb", optimizer = OptimizerType.RECOMPUTE_ALL.value)

# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.EXACT.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.GREEDY.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.RANDOM.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.MIGRATE_ALL.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.RECOMPUTE_ALL.value)

# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.EXACT.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.GREEDY.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.RANDOM.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.MIGRATE_ALL.value)
# run_experiment(notebook = "numpy.ipynb", optimizer = OptimizerType.RECOMPUTE_ALL.value)
from run_experiment import run_experiment


# For each notebook, run the experiment script once per optimizer.
# run_experiment(notebook = "nfl.ipynb", optimizer = "Baseline_Migrate")
# run_experiment(notebook = "nfl.ipynb", optimizer = "Baseline_Recompute")
# run_experiment(notebook = "nfl.ipynb", optimizer = "Baseline_Random")
run_experiment(notebook = "nfl.ipynb", optimizer = "Exact")
run_experiment(notebook = "nfl.ipynb", optimizer = "Greedy")

# run_experiment(notebook = "numpy.ipynb", optimizer = "Baseline_Migrate")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Baseline_Recompute")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Baseline_Random")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Exact")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Greedy")

# run_experiment(notebook = "numpy.ipynb", optimizer = "Baseline_Migrate")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Baseline_Recompute")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Baseline_Random")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Exact")
# run_experiment(notebook = "numpy.ipynb", optimizer = "Greedy")
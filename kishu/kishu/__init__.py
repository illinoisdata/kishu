__version__ = "0.1.0"

# This allows `%load_ext kishu` in Jupyter.
# Then, `%lsmagic` includes kishu functions.
# kishu can be enabled with `%kishu enable` to enable automatic tracing.
from kishu.jupyterint import load_ipython_extension

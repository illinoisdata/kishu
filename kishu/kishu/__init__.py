__version__ = "0.1.0"

# This allows `%load_ext kishu` in Jupyter.
# Then, `%lsmagic` includes kishu functions.
# kishu can be enabled with `%kishu enable` to enable automatic tracing.
from .jupyterint import load_ipython_extension
from .jupyter2 import register_kishu

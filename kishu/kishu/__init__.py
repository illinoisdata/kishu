__version__ = "0.1.0"

# This allows `%load_ext kishu` in Jupyter.
# Then, `%lsmagic` includes kishu functions.
# kishu can be enabled with `%kishu enable` to enable automatic tracing.
from .jupyterint import load_ipython_extension
from .jupyterint2 import load_kishu, init_kishu

__all__ = [
    'load_ipython_extension',
    'init_kishu',
    'load_kishu',
]

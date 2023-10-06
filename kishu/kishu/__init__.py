__app_name__ = "kishu"
__version__ = "0.1.0"

# This allows `%load_ext kishu` in Jupyter.
# Then, `%lsmagic` includes kishu functions.
# kishu can be enabled with `%kishu enable` to enable automatic tracing.
from .jupyterint import load_kishu, init_kishu

__all__ = [
    '__app_name__',
    '__version__',
    'init_kishu',
    'load_kishu',
]

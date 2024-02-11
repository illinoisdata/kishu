__app_name__ = "kishu"
__version__ = "0.2.0"

# This allows `%load_ext kishu` in Jupyter.
# Then, `%lsmagic` includes kishu functions.
# kishu can be enabled with `%kishu enable` to enable automatic tracing.
from .jupyterint import init_kishu, detach_kishu

__all__ = [
    '__app_name__',
    '__version__',
    'init_kishu',
    'detach_kishu',
]

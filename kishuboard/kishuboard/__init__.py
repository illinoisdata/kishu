try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode.
    import warnings
    warnings.warn("Importing 'kishuboard' outside a proper installation.")
    __version__ = "dev"
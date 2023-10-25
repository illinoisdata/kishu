# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, Extension


class get_numpy_include(object):
    """Defer numpy.get_include() until after numpy is installed."""
    def __str__(self):
        import numpy
        return numpy.get_include()


# Dynamic metadata in addition to static one in pyproject.toml
setup_args = dict(
    ext_modules=[
        Extension(
            "c_idgraph",
            sources=["lib/idgraphmodule.c", "lib/cJSON.c"],
            include_dirs=[get_numpy_include()],
        ),
    ],
)
setup(**setup_args)

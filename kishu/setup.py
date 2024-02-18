# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, Extension


class get_numpy_include(object):
    """Defer numpy.get_include() until after numpy is installed."""

    def __str__(self):
        import numpy
        return numpy.get_include()


visitor_module_extension = Extension(
    "VisitorModule",
    sources=["lib/idgraphmodule.c", "lib/cJSON.c",
             'lib/visitor_c.c',
             'lib/hash_visitor_c.c',
             'lib/xxhash.c'],
    include_dirs=[get_numpy_include()],
)

setup_args = dict(
    ext_modules=[visitor_module_extension],
)
setup(**setup_args)

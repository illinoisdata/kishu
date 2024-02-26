# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, Extension


class get_numpy_include(object):
    """Defer numpy.get_include() until after numpy is installed."""

    def __str__(self):
        import numpy
        return numpy.get_include()


c_idgraph_extension = Extension(
    "c_idgraph",
    sources=["lib/idgraphmodule.c", "lib/cJSON.c"],
    include_dirs=[get_numpy_include()],
)

visitor_module_extension = Extension(
    'VisitorModule',
    sources=[
        'lib/visitor_c.c',
        'lib/hash_visitor_c.c',
        'lib/xxhash.c'
    ],
    include_dirs=['/lib/'],
    extra_compile_args=['-g', '-O0']
)


setup_args = dict(
    ext_modules=[c_idgraph_extension, visitor_module_extension],
)
setup(**setup_args)

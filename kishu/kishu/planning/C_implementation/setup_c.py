from setuptools import setup, Extension

module = Extension('VisitorModule', sources=['visitor_c.c', 'hash_visitor_c.c', 'xxhash.c'], include_dirs=[
                   '/xxhash.h'], extra_compile_args=['-g', '-O0'])

setup(
    name='ObjectState',
    version='1.0',
    description='This is a package for providing hash implementation to visitor pattern',
    ext_modules=[module]
)

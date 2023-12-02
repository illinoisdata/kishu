from setuptools import setup, Extension

module = Extension('VisitorModule', sources=['visitor_c.c', 'hash_visitor_c.c'])

setup(
    name='ObjectState',
    version='1.0',
    description='This is a package for providing hash implementation to visitor pattern',
    ext_modules=[module]
)
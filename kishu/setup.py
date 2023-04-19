# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages, Extension

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()


setup(
    name='kishu',
    version='0.1.0',
    description='Intelligent Python Checkpointing',
    long_description=readme,
    author='Yongjoo Park',
    author_email='yongjoo@g.illinois.edu',
    url='https://github.com/illinoisdata/kishu',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    ext_modules=[Extension("c_idgraph", 
                    sources = ["change/idgraphmodule.c","change/cJSON.c"])]
)

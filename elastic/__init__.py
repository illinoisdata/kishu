# -*- coding: utf-8 -*-
#
# Copyright 2021-2022 University of Illinois

"""
Elastic Notebook is the project for offering durability and easy elasticity to Jupyter notebooks
via manual and automated state persistence.

Subpackages:
1. parse: Converts user-written Python scripts into our internal representation for identifying
    accessed variables.
2. graph: Classes and functions for constructing and mantaining an Application History Graph.
3. replicate: Identifies the variables to migrate and perform recomputation.
4. io: Offers serialization and deserialization capabilities.
"""

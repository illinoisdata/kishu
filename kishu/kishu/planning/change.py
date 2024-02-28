import ast
import inspect

from IPython.core.inputtransformer2 import TransformerManager
from collections import deque
from typing import Any, Deque, Dict, Set, Tuple


def find_created_and_deleted_vars(pre_execution: Set[str], post_execution: Set[str]) -> Tuple[Set[str], Set[str]]:
    """
        Find created and deleted variables through computing a difference of the user namespace pre and post execution.
    """
    created_variables = set()
    deleted_variables = set()

    # New variables
    for varname in post_execution.difference(pre_execution):
        if not varname.startswith('_'):
            created_variables.add(varname)

    # Deleted variables
    for varname in pre_execution.difference(post_execution):
        if not varname.startswith('_'):
            deleted_variables.add(varname)

    return created_variables, deleted_variables

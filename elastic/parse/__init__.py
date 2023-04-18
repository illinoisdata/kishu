"""
Extracts accessed variables in Python scripts.
"""

from elastic.parse.var import Var
import dis
from typing import List, Tuple
import ast
import inspect
from collections import deque
from ipykernel.zmqshell import ZMQInteractiveShell

def identify_vars(code_block: str, shell: ZMQInteractiveShell, shell_udfs: set) -> set:
    """
    Given a code block (see examples below), identify all the variables appearing in it.

    # Example Code Blocks

    ## Example 1:

    ```
    a = 1
    b = 3
    c = a + b
    ```

    set([a, b, c]) must be identified.


    ## Example 2:

    ```
    import numpy as np

    a = np.zeros((2,2))
    b = a + 1
    ```

    set([np, a, b]) must be identified.


    ## Example 3:

    ```
    def foo(item):
        mylist.append(item)     # accessing a global variable "mylist"
    item = 3
    foo(item)
    ```

    set([mylist, item]) must be identified. If "item = 3" is inlined and foo(3) is called without
    creating the "item" variable, "item" won't be included in the identified set.

    We inspect the definition of the "foo" because it is a function defined in the global scope,
    not in any module/package. (We consider all the functions listed in dir() as the global-scope
    functions. We won't allow the from-import pattern, preventing dir() from including the functions
    defined inside modules.)


    ## Example 4:

    ```
    def goo(item):
        mylist2.append(item)     # accessing a global variable "mylist2"

    def foo(item):
        mylist.append(item)     # accessing a global variable "mylist"
        goo(item)

    foo(3)
    ```

    set([mylist, mylist2]) must be identified. 


    ## Example 5:

    ```
    def foo(item):
        if random.random() < 0.5:
            mylist.append(item)     # accessing a global variable "mylist"
            return
        foo(item)

    foo(3)
    ```

    set([mylist]) must be identified. The "foo" function appears again inside the function itself,
    which must not result in an infinite loop during our analysis.


    # Future Goals

    1. We want to distinguish regular variables and modules.

    2. We want to identify *related* variables, where related variables mean the variables sharing
    references (to other objects). For example, two variables --- a and b --- created as follows 
    `a = [c] and b = [c]` are related because they share the reference to the same object (c).

    3. We will identify the "from module import *" pattern.
    """
    """
        Captures the input variables of the cell.
        Args:
            cell (str): Raw cell cell.
            existing_variables (set): Set of user-defined variables in the current session.
    """
    # Initialize ast walker
    v1 = visitor(shell = shell, shell_udfs = shell_udfs)

    # Disassemble cell instructions
    instructions = ast.parse(code_block)

    variables = set()
    udf_calls = deque()
    udf_calls_visited = set()
    function_defs = set()

    v1.visit(instructions)

    variables = variables.union(v1.loads)
    variables = variables.union(v1.stores)
    function_defs = function_defs.union(v1.functiondefs)
    for udf in v1.udfcalls:
        if udf not in udf_calls_visited and udf in shell_udfs:
            udf_calls.append(udf)
            udf_calls_visited.add(udf)

    while udf_calls:
        v_nested = visitor(shell = shell, shell_udfs = shell_udfs)
        udf = udf_calls.popleft()
        instructions = ast.parse(inspect.getsource(shell.user_ns[udf]))
        v_nested.visit(instructions)

        # Update input variables and function definitions
        variables = variables.union(v_nested.loads)
        variables = variables.union(v_nested.stores)
        function_defs = function_defs.union(v_nested.functiondefs)
        for udf in v_nested.udfcalls:
            if udf not in udf_calls_visited and udf in shell_udfs:
                udf_calls.append(udf)
                udf_calls_visited.add(udf)
    return variables



# Node visitor for finding input variables.
class visitor(ast.NodeVisitor):
    def __init__(self, shell, shell_udfs):
        # Whether we are currently in local scope.
        self.is_local = False

        # Functions declared in 
        self.functiondefs = set()
        self.udfcalls = set()
        self.loads = set()
        self.stores = set()
        self.globals = set()
        self.functionargs = set()
        self.recargs = deque()
        self.shell = shell
        self.udfs = shell_udfs

    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            # Only add as input if variable exists in current scope
            if not (self.is_local and node.id not in self.globals and node.id in self.shell.user_ns and type(self.shell.user_ns[node.id]) in {int, bool, str, float}):
                if node.id not in self.functionargs:
                    self.loads.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            # Only add as input if variable exists in current scope
            if not (self.is_local and node.id not in self.globals and node.id in self.shell.user_ns and type(self.shell.user_ns[node.id]) in {int, bool, str, float}):
                if node.id not in self.functionargs:
                    self.stores.add(node.id)        
        ast.NodeVisitor.generic_visit(self, node)

    def visit_AugAssign(self, node):
        # Only add as input if variable exists in current scope
        if not (self.is_local and node.target.id not in self.globals and node.target.id in self.shell.user_ns and type(self.shell.user_ns[node.target.id]) in {int, bool, str, float}):
            if isinstance(node.target, ast.Name):
                self.loads.add(node.target.id)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Global(self, node):
        for name in node.names:
            self.globals.add(name)
        ast.NodeVisitor.generic_visit(self, node)
    
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.udfcalls.add(node.func.id)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_FunctionDef(self, node):
        # Only add as input if variable exists in current scope
        self.is_local = True
        self.functiondefs.add(node.name)
        self.functionargs = set(args.arg for args in node.args.args)
        self.recargs.append(self.functionargs)
        ast.NodeVisitor.generic_visit(self, node)
        if len(self.recargs) == 1:
            self.functionargs = set()
        else:
           self.functionargs = self.recargs[0]
           self.recargs.pop
        self.is_local = False

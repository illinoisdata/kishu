from typing import List, Tuple
import ast
import inspect
from collections import deque
from ipykernel.zmqshell import ZMQInteractiveShell

def identify_vars(code_block: str, shell: ZMQInteractiveShell, shell_udfs: set) -> set:
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

    # Take first pass through code string
    v1.visit(instructions)

    # Get list of all called user defined functions
    variables = variables.union(v1.loads)
    variables = variables.union(v1.stores)
    function_defs = function_defs.union(v1.functiondefs)
    for udf in v1.udfcalls:
        if udf not in udf_calls_visited and udf in shell_udfs:
            udf_calls.append(udf)
            udf_calls_visited.add(udf)

    # Go through each user defined function being called and get variables
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
        self.globals = set(name for name in shell.user_ns)
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
        # Get arguments for called function
        self.functionargs = set(args.arg for args in node.args.args)
        # Add args to queue of args for calls inside functions
        self.recargs.append(self.functionargs)
        # Visit function
        ast.NodeVisitor.generic_visit(self, node)
        if len(self.recargs) == 1:
            self.functionargs = set()
        else:
           self.functionargs = self.recargs[0]
           self.recargs.pop
        self.is_local = False
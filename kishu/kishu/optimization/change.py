from typing import Tuple
import ast
import inspect
from collections import deque
from ipykernel.zmqshell import ZMQInteractiveShell
from typing import Deque, Any

PRIMITIVES = {int, bool, str, float}


# Node visitor for finding input variables.
class Visitor(ast.NodeVisitor):
    def __init__(self, user_ns, shell_udfs):
        # Whether we are currently in local scope.
        self.is_local = False

        # Functions declared in 
        self.functiondefs = set()
        self.udfcalls = set()
        self.loads = set()
        self.globals = set()
        self.user_ns = user_ns
        self.udfs = shell_udfs

    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            # Only add as input if variable exists in current scope.
            if not (self.is_local and node.id not in self.globals and node.id in self.user_ns and
                    type(self.user_ns[node.id]) in PRIMITIVES):
                self.loads.add(node.id)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_AugAssign(self, node):
        # Only add as input if variable exists in current scope.
        if isinstance(node.target, ast.Name):
            if not (self.is_local and node.target.id not in self.globals and node.target.id in self.user_ns and
                    type(self.user_ns[node.target.id]) in PRIMITIVES):
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
        ast.NodeVisitor.generic_visit(self, node)
        self.is_local = False


def find_input_vars(cell: str, existing_variables: set, user_ns, shell_udfs: set) -> Tuple[
    set, dict]:
    """
        Capture the input variables of the cell via AST analysis.
        Args:
            cell (str): Raw cell cell.
            existing_variables (set): Set of user-defined variables in the current session.
            shell (ZMQInteractiveShell): Shell of current session. For inferring variable types.
            shell_udfs (set): Set of user-declared functions in the shell.
    """
    # Initialize AST walker.
    v1 = Visitor(user_ns=user_ns, shell_udfs=shell_udfs)

    # Parse the cell code.
    v1.visit(ast.parse(cell))

    # Find top-level input variables and function declarations.
    input_variables = v1.loads
    function_defs = v1.functiondefs

    # Recurse into accessed UDFs.
    udf_calls : Deque[Any] = deque()
    udf_calls_visited = set()

    for udf in v1.udfcalls:
        if udf not in udf_calls_visited and udf in shell_udfs:
            udf_calls.append(udf)
            udf_calls_visited.add(udf)

    while udf_calls:
        # Visit the next nested UDF call.
        v_nested = Visitor(user_ns=user_ns, shell_udfs=shell_udfs)
        udf = udf_calls.popleft()
        v_nested.visit(ast.parse(inspect.getsource(user_ns[udf])))

        # Update input variables and function definitions
        input_variables = input_variables.union(v_nested.loads)
        function_defs = function_defs.union(v_nested.functiondefs)
        for udf in v_nested.udfcalls:
            if udf not in udf_calls_visited and udf in shell_udfs:
                udf_calls.append(udf)
                udf_calls_visited.add(udf)

    # A variable is an input only if it is in the shell before cell execution.
    input_variables = input_variables.intersection(existing_variables)

    return input_variables, function_defs


def find_created_and_deleted_vars(pre_execution, post_execution):
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

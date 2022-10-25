import dis

from IPython.core.interactiveshell import ExecutionResult


def find_input_output_vars(cell: str, existing_variables: set, cell_output: ExecutionResult) -> (set, dict):
    """
        Captures the input and output variables of the cell.
        Args:
            cell (str): Raw cell cell.
            existing_variables (set): Set of user-defined variables in the current session.
            cell_output (ExecutionResult): Output from running the cell. The cell stopping halfway due to a runtime
                error means we should skip reading the rest of the lines as they were not run.
    """
    # Disassemble cell instructions
    instructions = dis.get_instructions(cell)

    input_variables = set()

    # Capture output variables. Keys are variables and values are 2-item lists representing
    #   (order the variables were accessed / created in this cell, variable is deleted at end of cell execution.)
    # i.e. 'del x' -> output_variable: {('x', (0, True))}
    output_variables = {}

    output_idx = 0
    for instruction in instructions:
        """
        TODO: Handle one remaining edge case. See examples/numpy.ipynb:
            np.set_seed(0)
            list.reverse()
        For simplicity, we assume all class methods (i.e. list.sort()) will modify the class instance when called.
        In this case, 'np' should be both an input and output variable of the cell.
        The cell below currently only identifies np as an input variable of the cell.
        
        function(x)
        
        Check if variable is a primitive.
        """
        # Input variable
        if instruction.opname == "LOAD_NAME" and (instruction.argrepr not in input_variables) and \
                (instruction.argrepr not in output_variables):

            # Handles the case where argrepr is a builtin (i.e. 'len()'). We don't want to identify an argrepr
            # as an input variable if it wasn't created/imported by the user.
            if instruction.argrepr in existing_variables:
                input_variables.add(instruction.argrepr)

        # Output variable
        elif instruction.opname == "STORE_NAME" or instruction.opname == "DELETE_NAME":
            if instruction.argrepr not in output_variables:
                output_variables[instruction.argrepr] = [output_idx, False]
                output_idx += 1

            # Handles the case where a variable may be deleted (i.e. del x). We want to capture whether a variable
            # Exists at the end of cell execution; if it doesn't, it should not be identified as an active variable.
            if instruction.opname == "STORE_NAME":
                output_variables[instruction.argrepr][1] = False
            elif instruction.opname == "DELETE_NAME":
                output_variables[instruction.argrepr][1] = True

    return input_variables, output_variables

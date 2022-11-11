from ast import Str
import dis
import re
import string
from typing import List, Tuple

from ipykernel.zmqshell import ZMQInteractiveShell
from pyparsing import line_end


def find_input_output_vars(cell: str, existing_variables: set, shell: ZMQInteractiveShell,
                           traceback_list: List) -> Tuple[set, dict]:
    """
        Captures the input and output variables of the cell.
        Args:
            cell (str): Raw cell cell.
            existing_variables (set): Set of user-defined variables in the current session.
            shell (ZMQInteractiveShell): interactive Jupyter shell storing the state of the current session.
            traceback_list (List(str)): Potential error from running the cell. The cell stopping halfway due to a
                runtime error means we should skip reading the rest of the lines as they were not run.
    """
    # Find first line where execution fails in given list and assign to break_line
    line_numbers = []
    for str in traceback_list:
        line_numbers.append(int(re.findall("line (\d+)", str)[0]))
    break_line = min(line_numbers) if len(traceback_list) != 0 else -1
    last_variables = []

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
        TODO: Handle edge cases related to:
            (1) Class method call: np.set_seed(0), list.reverse()
            (2) Pass to function: modify(x)
        For simplicity, we assume both cases will modify the variable., i.e. 'np', 'list', and 'x' should be both an 
        input and output variables of the cell.
        The cell below currently only identifies them as an input variable of the cell.
        
        TODO: Handle error during execution:
            y = x
            print(nonexistent_variable)
            z = x
        In this case, only y should be an output of the cell - we never got to execute 'z = x'.
        """
        # Check if current instruction is at or past break line and breaks for loop if true
        if instruction.starts_line == break_line and break_line >= 0:
            break
        # Input variable
        if instruction.opname == "LOAD_NAME" and (instruction.argrepr not in input_variables) and \
                (instruction.argrepr not in output_variables):
            # Keeps track of last variable that was loaded as an input
            last_variables.append(instruction.argrepr)
            # Handles the case where argrepr is a builtin (i.e. 'len()'). We don't want to identify an argrepr
            # as an input variable if it wasn't created/imported by the user.
            if instruction.argrepr in existing_variables:
                input_variables.add(instruction.argrepr)

        # Checks to see if an input was not a primitive type and was used in the input of a function
        elif instruction.opname == "CALL_FUNCTION" or instruction.opname == "CALL_FUNCTION_KW" or instruction.opname == "CALL_METHOD":
            for last_variable in last_variables:
                if last_variable in shell.user_ns and \
                        type(shell.user_ns[last_variable]) not in (int, float, type(""), bool):
                    if last_variable in existing_variables:
                        output_variables[last_variable] = [output_idx, False]
                        output_idx += 1
            last_variables = []

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

            last_variables = []

    return input_variables, output_variables

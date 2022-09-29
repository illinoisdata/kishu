import dis
from gettext import install
from tracemalloc import start
import nbformat as nbf
from glob import glob
import datetime

# Collect a list of all notebooks in the content folder
# notebooks = glob("../disassembler/*.ipynb", recursive=True)

output_vars = []
input_vars = []

ntbk = nbf.read("/Users/rah/Documents/elastic-notebook/elastic/core/notebook/disassembler/test_cell.ipynb", nbf.NO_CONVERT)
for cell in ntbk.cells:
    start_time = datetime.datetime.now()
    source_code = cell.get('source')
    instruction_lines = dis.Bytecode(source_code)
    iter = dis.get_instructions(source_code)
    #print(cell.get('source'))

    for instruc in iter:
        if instruc.opname == "LOAD_NAME" and (instruc.argrepr not in input_vars):
            input_vars.append(instruc.argrepr)

        elif instruc.opname == "STORE_NAME" and instruc.argrepr not in output_vars:
            output_vars.append(instruc.argrepr)
    #input_vars = list(set(input_vars).difference(set(output_vars)))

    print("Input Vars: ")
    for input in input_vars:
        print(input + " ")
    print("\n")
    print("Output Vars: ")
    for output in output_vars:
        print(output + " ")
    print("\n")

    input_vars.clear()
    output_vars.clear()
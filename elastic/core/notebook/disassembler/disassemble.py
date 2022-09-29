import dis
from gettext import install
from tracemalloc import start
from importlib_metadata import version
import nbformat as nbf
from glob import glob
import datetime
from core.notebook.variable_snapshot import VariableSnapshot
from core.notebook.operation_event import OperationEvent
from core.globals import variable_snapshots, operation_events, variable_version, variable_snapshot_accesses

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
    print(cell.get('source'))

    for instruc in iter:
        if instruc.opname == "LOAD_NAME" and (instruc.argrepr not in input_vars) and (variable_version[instruc.argrepr] != 0):
            input_vars.append(instruc.argrepr)
            variable_version[instruc.argrepr] += 1
            vs = VariableSnapshot(instruc.argrepr, variable_version[instruc.argrepr], item.get_item())
            variable_snapshots.append(vs)
            variable_snapshot_accesses.append(vs)

        elif instruc.opname == "STORE_NAME" and instruc.argrepr not in output_vars:
            output_vars.append(instruc.argrepr)

    for input in input_vars:
        print(input + " ")
    print("\n")
    for output in output_vars:
        print(output + " ")

    end_time = datetime.datetime.now()
    exec_uuid = len(operation_events)
    oe = OperationEvent(exec_uuid=exec_uuid, 
                        start=start_time, 
                        end=end_time, 
                        duration=(end_time - start_time).total_seconds(),
                        cell_func_name=cell.get('metadata').get('cell_id'),
                        cell_func_code=cell.get('source'),
                        cell_func_obj=cell.get('metadata')['name'],
                        input_variable_snapshots=variable_snapshot_accesses)
    operation_events.append(oe)

    for output_var in output_vars:
        variable_version[output_var] += 1
        vs = VariableSnapshot(output_var, variable_version[output_var], item.get_item(), oe)
        variable_snapshots.append(vs)

    variable_snapshot_accesses.clear()
    input_vars.clear()
    output_vars.clear()
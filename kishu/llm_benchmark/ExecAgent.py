from IPython.utils import io
import os
import re
import shutil
from pathlib import Path
import ast
from typing import Generator, TextIO, Optional

from kishu.commands import KishuCommand
from kishu.jupyter.runtime import JupyterRuntimeEnv
from kishu.notebook_id import NotebookId
from llm_benchmark.utils import create_tmp_ipynb_in_current_dir
from tests.conftest import tmp_nb_path, jupyter_server
from tests.helpers.nbexec import KISHU_INIT_STR
from tests.helpers.serverexec import JupyterServerRunner
import concurrent.futures
from IPython.core.interactiveshell import InteractiveShell

import time


class KishuExecAgent(object):
    def __init__(self):
        self.step2commit_id = {}
        self.tmp_nb_path = Path(create_tmp_ipynb_in_current_dir())
        self.real_nb_path = Path("./empty.ipynb")
        shutil.copy(self.real_nb_path, self.tmp_nb_path)
        os.environ["TEST_NOTEBOOK_PATH"] = str(self.tmp_nb_path)
        self.shell = InteractiveShell()
        self.shell.run_cell(KISHU_INIT_STR, silent=True)

    def execute(self, code, step_id):
        output = traceback = None
        if code == "":
            traceback = "No code111 to execute"
        else:
            start_time = time.time()
            with io.capture_output() as captured:
                result = self.shell.run_cell(code)
            if not result.success:
                traceback = str(result.error_before_exec) + str(result.error_in_exec)
            else:
                output = captured.stdout
            # stream_output, data_output, traceback = self.notebook_session.run_code(code111)
            duration = time.time() - start_time
            # self.step2commit_id[step_id] = KishuCommand.log(
            #     NotebookId.parse_key_from_path(self.tmp_nb_path)).head.commit_id
            self.step2commit_id[step_id] = KishuCommand.log(
                self.tmp_nb_path).head.commit_id
            # self.step2commit_id[step_id] = KishuBranch()
        return output, traceback, duration

    def checkout(self, step):
        target_commit_id = self.step2commit_id[step]
        checkout_code = f"_kishu.checkout('{target_commit_id}', skip_notebook={True})"
        start_time = time.time()
        # KishuCommand.checkout(NotebookId.parse_key_from_path(self.tmp_nb_path), target_commit_id)
        self.shell.run_cell(checkout_code)
        return time.time() - start_time

    def num_variables(self):
        return len(self.shell.user_ns)


class NBGroupExecAgent(object):
    def __init__(self, group_name: str, mode: str, branch_num: int):
        self.group_name = group_name
        self.mode = mode
        self.branch_num = branch_num

    def _init_runner(self, nb_path: Path, init_kishu: bool = False):
        os.environ["TEST_NOTEBOOK_PATH"] = str(nb_path)
        self.shell = InteractiveShell()
        if init_kishu:
            self.shell.run_cell(KISHU_INIT_STR, silent=True)

    def e2e_execute(self, log_file_handler: TextIO, data_collect_log: Optional[TextIO]):
        if self.mode == "non_kishu_start_over":
            return self.non_kishu_e2e_execute_start_over(log_file_handler)
        elif self.mode == "non_kishu_start_middle":
            return self.non_kishu_e2e_execute_start_middle(data_collect_log, log_file_handler)
        elif self.mode == "kishu":
            return self.kishu_e2e_execute(data_collect_log,log_file_handler)
        elif self.mode == "test_semantic_error":
            # Although it's running non_kishu_start_middle again
            # But this time with kishu to analyze semantic errors
            # the result is how many error_branches are there
            return self.test_semantic_error(data_collect_log, log_file_handler)
        else:
            raise ValueError("Invalid mode")

    def non_kishu_e2e_execute_start_over(self, log_file_handler: TextIO):
        e2e_time = 0
        final_run_steps = 0
        max_num_variables = 0
        for i in range(self.branch_num):
            # restart the runner
            real_nb_path = Path(
                "/home/hanxif2/exp1/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_" + str(i) + ".ipynb")
            tmp_nb_path = Path(create_tmp_ipynb_in_current_dir())
            shutil.copy(real_nb_path, tmp_nb_path)
            self._init_runner(tmp_nb_path)
            print("begin execution: " + self.group_name + "_" + str(i) + ".ipynb")
            log_file_handler.write("begin execution: " + self.group_name + "_" + str(i) + ".ipynb\n")
            log_file_handler.flush()
            # Get the contents of the test notebook.
            contents = JupyterRuntimeEnv.read_notebook_cell_source(tmp_nb_path)
            # Start the notebook session.
            for i in range(len(contents)):
                start_time = time.time()
                with io.capture_output() as captured:
                    self.shell.run_cell(contents[i])
                duration = (time.time() - start_time)
                final_run_steps += 1
                print(f"exec step {i}. Time: {duration}")
                log_file_handler.write(f"exec step {i}. Time: {duration}\n")
                log_file_handler.flush()
                e2e_time += duration
            print(i)
            print(self.num_variables())
            print(self.shell.user_ns.keys())
            max_num_variables = max(max_num_variables, self.num_variables())
            print(max_num_variables)
        return e2e_time, final_run_steps, max_num_variables

    def non_kishu_e2e_execute_start_middle(self, data_collect_log: TextIO, log_file_handler: TextIO):
        e2e_time = 0
        final_run_steps = 0
        final_compile_error_step = 0
        final_cells_in_nb = 0

        # Regular expression to find numbers after "checkout to step"
        pattern = r"checkout to step (\d+)"

        # Extract all matches and convert them to a list of integers
        start_from = [int(match) + 1 for match in re.findall(pattern, data_collect_log.read())]
        start_from.insert(0, 0)

        real_nb_path = Path("/home/hanxif2/exp1/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_0" + ".ipynb")
        tmp_nb_path = Path(create_tmp_ipynb_in_current_dir())
        shutil.copy(real_nb_path, tmp_nb_path)
        self._init_runner(tmp_nb_path)

        largest_var_num = 0

        for i in range(self.branch_num):
            # restart the runner
            real_nb_path = Path(
                "/home/hanxif2/exp1/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_" + str(i) + ".ipynb")
            print("begin execution: " + self.group_name + "_" + str(i) + ".ipynb")
            log_file_handler.write("begin execution: " + self.group_name + "_" + str(i) + ".ipynb\n")
            log_file_handler.flush()
            # Get the contents of the test notebook.
            contents = JupyterRuntimeEnv.read_notebook_cell_source(real_nb_path)
            # update final cell numnber
            final_cells_in_nb += len(contents) - start_from[i]

            run_into_error = False
            for j in range(start_from[i], len(contents)):
                start_time = time.time()
                result = self.shell.run_cell(contents[j])
                duration = (time.time() - start_time)
                final_run_steps += 1
                print(f"exec step {j}. Time: {duration}")
                log_file_handler.write(f"exec step {j}. Time: {duration}\n")
                log_file_handler.flush()
                e2e_time += duration
                if not result.success:
                    final_compile_error_step += 1
                    print("Compile Error in step " + str(j))
                    log_file_handler.write("Error in step " + str(j) + " : " + str(result.error_before_exec) + str(
                        result.error_in_exec) + "\n")
                    log_file_handler.flush()
                    run_into_error = True
                    break

            if run_into_error:
                # restart runner and rerun all the contents
                largest_var_num = max(largest_var_num,self.num_variables())
                self.shell.cleanup()
                tmp_nb_path = Path(create_tmp_ipynb_in_current_dir())
                shutil.copy(real_nb_path, tmp_nb_path)
                start_time = time.time()
                self._init_runner(tmp_nb_path)
                duration = (time.time() - start_time)
                print(f"restart kernel. Time: {duration}")
                log_file_handler.write(f"restart kernel. Time: {duration}")
                log_file_handler.flush()
                e2e_time += duration

                for j in range(0, len(contents)):
                    start_time = time.time()
                    result = self.shell.run_cell(contents[j])
                    duration = (time.time() - start_time)
                    final_run_steps += 1
                    print(f"exec step {j}. Time: {duration}")
                    log_file_handler.write(f"exec step {j}. Time: {duration}\n")
                    log_file_handler.flush()
                    e2e_time += duration
            if largest_var_num < self.num_variables():
                print(i)
                print(largest_var_num)
                print(self.shell.user_ns.keys())
            largest_var_num = max(largest_var_num, self.num_variables())
        return e2e_time, final_run_steps, largest_var_num

    def kishu_e2e_execute(self, data_collect_log: TextIO, log_file_handler: TextIO):
        e2e_time = 0
        max_num_vars = 0

        # Regular expression to find numbers after "checkout to step"
        pattern = r"checkout to step (\d+)"

        # Extract all matches and convert them to a list of integers
        start_from = [int(match) + 1 for match in re.findall(pattern, data_collect_log.read())]
        start_from.insert(0, 0)

        agent = KishuExecAgent()

        for i in range(self.branch_num):
            # restart the runner
            real_nb_path = Path("/home/hanxif2/exp1/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_" + str(i) + ".ipynb")
            # real_nb_path = Path(
            #     "/Users/hanxi/Kishu-be/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_" + str(i) + ".ipynb")
            print("begin execution: " + self.group_name + "_" + str(i) + ".ipynb")
            log_file_handler.write("begin execution: " + self.group_name + "_" + str(i) + ".ipynb\n")
            log_file_handler.flush()
            # Get the contents of the test notebook.
            contents = JupyterRuntimeEnv.read_notebook_cell_source(real_nb_path)

            for step in range(start_from[i], len(contents)):
                log_file_handler.write("execute step " + str(step) + "\n")
                log_file_handler.flush()
                # get accessed variables
                with io.capture_output() as captured:
                    start_time = time.time()
                    result = agent.execute(contents[step],step)
                    e2e_time += (time.time() - start_time)
            print(i)
            print(len(agent.shell.user_ns))
            print(agent.shell.user_ns.keys())
            max_num_vars = max(max_num_vars, len(agent.shell.user_ns))
            # checkout and calculate variables
            if i + 1 < self.branch_num:
                start_time = time.time()
                agent.checkout(start_from[i + 1] - 1)
                e2e_time += (time.time() - start_time)


        return e2e_time, max_num_vars

    def test_semantic_error(self, data_collect_log: TextIO, log_file_handler: TextIO):
        num_all_error_branch = 0
        num_compile_error_branch = 0
        var2step = {}  # variable version map. variable_name to last step that updated it.
        var2code = {}
        var2nb = {}

        # Regular expression to find numbers after "checkout to step"
        pattern = r"checkout to step (\d+)"

        # Extract all matches and convert them to a list of integers
        start_from = [int(match) + 1 for match in re.findall(pattern, data_collect_log.read())]
        start_from.insert(0, 0)

        real_nb_path = Path("/home/hanxif2/exp1/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_0" + ".ipynb")
        # real_nb_path = Path(
        #     "/Users/hanxi/Kishu-be/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_0" + ".ipynb")
        tmp_nb_path = Path(create_tmp_ipynb_in_current_dir())
        shutil.copy(real_nb_path, tmp_nb_path)
        self._init_runner(tmp_nb_path, init_kishu=True)
        nb_conflict_var_set = set()

        for i in range(self.branch_num):
            # restart the runner
            real_nb_path = Path("/home/hanxif2/exp1/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_" + str(i) + ".ipynb")
            # real_nb_path = Path(
            #     "/Users/hanxi/Kishu-be/kishu/kishu/llm_benchmark/notebooks/" + self.group_name + "_" + str(i) + ".ipynb")
            print("begin execution: " + self.group_name + "_" + str(i) + ".ipynb")
            log_file_handler.write("begin execution: " + self.group_name + "_" + str(i) + ".ipynb\n")
            log_file_handler.flush()
            # Get the contents of the test notebook.
            contents = JupyterRuntimeEnv.read_notebook_cell_source(real_nb_path)
            # Start the notebook session.
            valid_branch = True

            run_into_error = False
            nb_confilict_vars = []
            for step in range(start_from[i], len(contents)):
                log_file_handler.write("execute step " + str(step) + "\n")
                log_file_handler.flush()
                # get accessed variables
                with io.capture_output() as captured:
                    result = self.shell.run_cell(contents[step])
                print(f"captured:{captured}")

                if not result.success:
                    print("Compile Error in step " + str(step))
                    log_file_handler.write(
                        "Compile Error in step " + str(step) + "\n")
                    start_from[i] = 0  # run into explicit error, has to run from scratch for the current branch
                    run_into_error = True
                    valid_branch = False
                    break

                accessed_variables = self._get_accessed_vars(captured.stdout, contents[step])
                for var in accessed_variables:
                    last_modified_step = var2step.get(var, None)
                    if last_modified_step is not None and last_modified_step >= step:
                        valid_branch = False
                        print(f"{var} modified in step {last_modified_step} but current branch is in step {step}")
                        print(f"previously modified nb: {var2nb[var]}")
                        print(f"previously modified step: {var2step[var]}")
                        print(f"previously modified code:\n {var2code[var]}")
                        print(f"current code:\n {contents[step]}")
                        nb_confilict_vars.append(var)
                        nb_conflict_var_set.add(var)
                        log_file_handler.write(
                            f"Variable {var} modified in step {last_modified_step} but current branch is in step {step}\n")
                        log_file_handler.write(
                            f"previously modified nb: {var2nb[var]}\n"
                        )
                        log_file_handler.write(
                            f"previously modified code:\n {var2code[var]}\n"
                        )
                        log_file_handler.write(
                            f"current code:\n {contents[step]}\n"
                        )
                        log_file_handler.flush()
                modified_variables = self._get_modified_vars(captured.stdout,contents[step])
                for var in modified_variables:
                    var2step[var] = step
                    var2code[var] = contents[step]
                    var2nb[var] = i

            if run_into_error:
                #restart runner and rerun all the contents
                var2step = {}
                tmp_nb_path = Path(create_tmp_ipynb_in_current_dir())
                shutil.copy(real_nb_path, tmp_nb_path)
                self._init_runner(tmp_nb_path, init_kishu=True)
                for step in range(0, len(contents)):
                    log_file_handler.write("make up execute step " + str(step) + "\n")
                    # get accessed variables
                    with io.capture_output() as captured:
                        result = self.shell.run_cell(contents[step])
                        if not result.success:
                            print("Compile Error still not solved in step" + str(step))
                            log_file_handler.write(
                                "Compile Error still not solved in step " + str(step) + "\n")
                            valid_branch = True
                    modified_variables = self._get_modified_vars(captured.stdout,contents[step])
                    for var in modified_variables:
                        var2step[var] = step
                if not valid_branch:
                    num_compile_error_branch += 1
            if not valid_branch:
                num_all_error_branch += 1
                log_file_handler.write(f"nb {i} branch {step} conflict vars:{nb_confilict_vars}\n")

        log_file_handler.write(f"nb {i} conflict vars:{nb_conflict_var_set}\n")

        return num_all_error_branch,num_compile_error_branch

    def num_variables(self):
        return len(self.shell.user_ns)
    
        
    def _extract_variables_from_code(self,code):
        # Parse the code into an AST (Abstract Syntax Tree)
        tree = ast.parse(code)
        
        # Collect all variable names
        defined_variables = set()  # Variables that are defined (assigned to)
        used_variables = set()     # Variables that are used (referenced)

        for node in ast.walk(tree):
            # Handle variable usage
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Load):  # Variable is being used
                    used_variables.add(node.id)

        return used_variables

    def _get_accessed_vars(self, captured_output: str, cell_code: str):
        # Extract the sets using regular expressions
        accessed_vars_match = re.search(r"accessed_vars:\s*({.*?})", captured_output)

        # Convert the string inside the curly braces to a set of strings
        if accessed_vars_match:
            accessed_vars_match = set(accessed_vars_match.group(1).strip("{}").split(","))
            # Remove empty strings due to extra spaces
            accessed_vars_match = {var.strip().strip("'") for var in accessed_vars_match if var.strip()}
        else:
            accessed_vars_match = set()

        remove_set = set()
        variables_in_code = self._extract_variables_from_code(cell_code)
        # deal with falsely detected accessed variables
        for var in accessed_vars_match:
            # if var not in cell_code:
            if var not in variables_in_code:
                print(f"code is:{cell_code}")
                print(f"accessed {var} not in {variables_in_code}")
                remove_set.add(var)
                continue
            for line in cell_code.split("\n"):
                line = line.split("#")[0]
                # type 1: newly created again
                if (len(line.split("=")) > 1 and
                        var in [x.strip() for x in line.split("=")[0].replace(",", " ").replace("(","").replace(")","").split()] and
                        var not in [x.strip() for x in line.split("=")[1].replace(",", " ").replace("."," ").replace("("," ").replace(")"," ").replace("["," ").replace("]"," ").replace(";"," ").split()]):
                    # for (a, b) = split(c)
                    remove_set.add(var)
                    break
                if (len(line.split(" in ")) > 1 and
                        var in [x.strip() for x in line.split(" in ")[0].replace(",", " ").split()] and
                        var not in [x.strip() for x in line.split(" in ")[1].replace(",", " ").replace("."," ").replace("("," ").replace(")"," ").replace("["," ").replace("]"," ").replace(";"," ").split()]):
                    # for a, b in c: a is a new variable, not an accessed old variable.
                    remove_set.add(var)
                    break

                # type 2: newly imported again
                if var in [x.strip() for x in line.replace(","," ").split()] and "import" in line.split():
                    remove_set.add(var)
                    break

                #type 3: function redefinition
                try:
                    if "def" == line.replace("("," ").split()[0].strip() and var == line.replace("("," ").split()[1]:
                        remove_set.add(var)
                        break
                except:
                    pass

        accessed_vars_match = accessed_vars_match - remove_set

        return accessed_vars_match

    def _get_modified_vars(self, captured_output: str, cell_code:str):
        exempt_types = ["module", "builtin_function_or_method", "type", "method", "method-wrapper"]
        # Extract the sets using regular expressions
        modified_vars_match = re.search(r"modified_vars_value:\s*({.*?})", captured_output)
        modified_vars_types_match = re.search(r"modified_vars_value_types:\s*\[(.*?)\]", captured_output)
        # Convert the string inside the curly braces to a set of strings
        if modified_vars_match:
            modified_vars_match = modified_vars_match.group(1).strip("{}").split(",")
            modified_vars_type_match = modified_vars_types_match.group(1).strip("{}").split(",")
            modified_vars_type_match = [item.split("'")[1] for item in modified_vars_type_match]
            modified_vars_match = set(
                [var.strip().strip("'") for var, type in zip(modified_vars_match, modified_vars_type_match) if
                 var.strip() and type.strip() not in exempt_types])
        else:
            modified_vars_match = set()

        deleted_vars_match = re.search(r"deleted_vars:\s*({.*?})", captured_output)
        deleted_vars_types_match = re.search(r"deleted_vars_types:\s*\[(.*?)\]", captured_output)
        if deleted_vars_match:
            deleted_vars_match = deleted_vars_match.group(1).strip("{}").split(",")
            deleted_vars_type_match = deleted_vars_types_match.group(1).strip("{}").split(",")
            deleted_vars_type_match = [item.split("'")[1] for item in deleted_vars_type_match]
            deleted_vars_match = set(
                [var.strip().strip("'") for var, type in zip(deleted_vars_match, deleted_vars_type_match) if
                 var.strip() and type.strip() not in exempt_types])
        else:
            deleted_vars_match = set()

        created_vars_match = re.search(r"created_vars:\s*({.*?})", captured_output)
        # created_vars_types_match = re.search(r"created_vars_types:\s*([.*?])", captured_output)
        created_vars_types_match = re.search(r"created_vars_types:\s*\[(.*?)\]", captured_output)

        if created_vars_match:
            created_vars_match = created_vars_match.group(1).strip("{}").split(",")
            created_vars_type_match = created_vars_types_match.group(1).strip("[]").split(",")
            created_vars_type_match = [item.split("'")[1] for item in created_vars_type_match]
            created_vars_match = set(
                [var.strip().strip("'") for var, type in zip(created_vars_match, created_vars_type_match) if
                 var.strip() and type.strip() not in exempt_types])
        else:
            created_vars_match = set()

        # return modified_vars_match.union(created_vars_match).union(deleted_vars_match)
        candidate_set =  modified_vars_match.union(created_vars_match).union(deleted_vars_match)

        remove_set = set()
        variables_in_code = self._extract_variables_from_code(cell_code)
        for var in candidate_set:
            if var not in variables_in_code:
                remove_set.add(var)

        return candidate_set - remove_set


def jupyter_server() -> Generator[JupyterServerRunner, None, None]:
    with JupyterServerRunner() as jupyter_server:
        yield jupyter_server

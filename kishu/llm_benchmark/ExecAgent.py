import shutil
from pathlib import Path

from typing import Generator, TextIO

from kishu.commands import KishuCommand
from kishu.jupyter.runtime import JupyterRuntimeEnv
from kishu.notebook_id import NotebookId
from llm_benchmark.utils import create_tmp_ipynb_in_current_dir
from tests.conftest import tmp_nb_path, jupyter_server
from tests.helpers.nbexec import KISHU_INIT_STR
from tests.helpers.serverexec import JupyterServerRunner
import concurrent.futures

import time


class KishuExecAgent(object):
    def __init__(self):
        self.step2commit_id = {}
        self.tmp_nb_path = Path(create_tmp_ipynb_in_current_dir())
        self.real_nb_path = Path("llm_benchmark/empty.ipynb")
        shutil.copy(self.real_nb_path, self.tmp_nb_path)
        self.jupyter_server = JupyterServerRunner()
        self.jupyter_server.__enter__()
        self.notebook_session = self.jupyter_server.start_session(self.tmp_nb_path)
        self.notebook_session.__enter__()
        self.notebook_session.run_code(KISHU_INIT_STR, silent=True)

    def execute(self, code, step_id):
        if code == "":
            traceback = "No code to execute"
        else:
            start_time = time.time()
            stream_output, data_output, traceback = self.notebook_session.run_code(code)
            duration = time.time() - start_time
            self.step2commit_id[step_id] = KishuCommand.log(
                NotebookId.parse_key_from_path(self.tmp_nb_path)).head.commit_id
        return stream_output + data_output, traceback, duration

    def checkout(self, step):
        target_commit_id = self.step2commit_id[step]
        start_time = time.time()
        KishuCommand.checkout(NotebookId.parse_key_from_path(self.tmp_nb_path), target_commit_id)
        return time.time() - start_time

    def closeAgent(self):
        self.notebook_session.__exit__(None, None, None)
        self.jupyter_server.__exit__(None, None, None)


class NBGroupExecAgent(object):
    def __init__(self, group_name: str, is_kishu: bool, start_over: bool = True):
        self.group_name = group_name
        self.is_kishu = is_kishu
        self.start_over = start_over

    def _init_runner(self, nb_path: Path):
        self.jupyter_server = JupyterServerRunner()
        self.jupyter_server.__enter__()
        self.notebook_session = self.jupyter_server.start_session(nb_path)
        self.notebook_session.__enter__()

    def _close_runner(self):
        self.notebook_session.__exit__(None, None, None)
        self.jupyter_server.__exit__(None, None, None)

    def e2e_execute(self, log_file_handler: TextIO):
        if not self.is_kishu and self.start_over:
            return self.non_kishu_e2e_execute_start_over(log_file_handler)

    def non_kishu_e2e_execute_start_over(self, log_file_handler: TextIO):
        e2e_time = 0
        final_run_steps = 0
        for i in range(5):
            # restart the runner
            real_nb_path = Path("/Users/hanxi/Kishu-be/kishu/kishu/" + self.group_name + "_" + str(i) + ".ipynb")
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
                self.notebook_session.run_code(contents[i])
                duration = (time.time() - start_time)
                final_run_steps += 1
                print(f"exec step {i}. Time: {duration}")
                log_file_handler.write(f"exec step {i}. Time: {duration}\n")
                log_file_handler.flush()
                e2e_time += duration
            self._close_runner()
        return e2e_time, final_run_steps

    def kishu_e2e_execute(self):
        pass


def jupyter_server() -> Generator[JupyterServerRunner, None, None]:
    with JupyterServerRunner() as jupyter_server:
        yield jupyter_server

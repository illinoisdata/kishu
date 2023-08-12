'''
Provides Jupyter integration.

# Basics

Usage:
```
%load_ext kishu
%kishu enable
```

Once enabled, kishu starts to observe all cell executions.


# References:

Writing a custom handler:
https://ipython.readthedocs.io/en/stable/config/custommagics.html

Registering custom handler:
https://jupyter-notebook.readthedocs.io/en/stable/extending/handlers.html

IPython code modification:
https://ipython.readthedocs.io/en/stable/config/inputtransforms.html
'''

from IPython.core.magic import (
    Magics,
    magics_class,
    line_magic,
    cell_magic,
)
from IPython import get_ipython
from ipylab import JupyterFrontEnd
import dill
import ipynbname
import os
import shutil
import time


IPYTHON_EXECUTION_COUNT = 'ipython.execution_count'

CMD_CHECKPOINT = 'checkpoint'

CMD_RESTORE = 'restore'


# The class MUST call this class decorator at creation time
@magics_class
class KishuMagics(Magics):

    @cell_magic
    def kishucapture(self, line, cell):
        "my cell magic"
        return line, cell

    @line_magic
    def kishu(self, line):
        cmd_args = line.strip().split(' ')
        cmd = cmd_args[0]
        args = cmd_args[1:]
        msg = ''
        if cmd == 'enable':
            self.cmd_enable()
            msg = 'kishu is enabled.'
        elif cmd == 'disable':
            self.cmd_disable()
            msg = 'kishu is disabled.'
        elif cmd == 'status':
            status = 'enabled' if self.is_enabled() else 'disabled'
            msg = f'kishu status: {status}'
        elif cmd == CMD_CHECKPOINT:
            if len(args) < 1:
                raise ValueError('A filename must be passed in the first argument.')
            filename = args[0]
            self.cmd_checkpoint(filename)
        elif cmd == CMD_RESTORE:
            if len(args) < 1:
                raise ValueError('A filename must be passed in the first argument.')
            filename = args[0]
            self.cmd_restore(filename)
        else:
            msg = 'Unknown option: ' + cmd
        return msg

    def is_enabled(self):
        return hasattr(self, '_enabled') and self._enabled

    def cmd_enable(self):
        if self.is_enabled():
            return
        self._enabled = True
        ip = get_ipython()
        ip.input_transformers_cleanup.append(_append_kishu_capture)

    def cmd_disable(self):
        ip = get_ipython()
        _remove_kishu_functions(ip.input_transformers_cleanup)
        self._enabled = False

    def cmd_checkpoint(self, filename):
        '''
        The following operations are performed:
        1. The current notebook is saved and copied to filename.ipynb
        2. Save IPython history to filename.ipyhist
        3. Save all the objects to filename.dill
        4. Save the other metadata to filename.meta
        '''
        # 1. The current notebook is saved and copied to filename.ipynb
        self._save_current_nb()
        current_file = ipynbname.path()
        chk_nb_file = self._get_nb_file(filename)
        shutil.copy2(current_file, chk_nb_file)

        # 3. Save all the objects to filename.dill
        objects = self._collect_non_jupyter_objects()
        chk_dill_file = self._get_dill_file(filename)
        _save_dill_into(objects, chk_dill_file)

        # 4. Save other metadata
        ip = get_ipython()
        meta = {
            IPYTHON_EXECUTION_COUNT: ip.execution_count
        }
        chk_meta_file = self._get_meta_file(filename)
        _save_dill_into(meta, chk_meta_file)

    def cmd_restore(self, filename):
        '''
        The following operations are performed:
        1. The current notebook is restored from filename.ipynb
        2. Load/Overwrite the IPython history from filename.ipyhist
        3. Load all the objects from filename.dill
        4. Advance Jupyter's index for the latest executed cell
        '''
        # 1. Restore notebook cells
        # TODO: cell index should be advanced appropriately, allowing subsequent cell execution
        # not start from 1.
        self._save_current_nb()  # saving the current file prevents reload dialog
        current_file = ipynbname.path()
        chk_nb_file = self._get_nb_file(filename)
        shutil.copy2(chk_nb_file, current_file)
        app = JupyterFrontEnd()
        app.commands.execute('docmanager:reload')

        # 3. Restore all the pickled objects from filename.dill
        chk_dill_file = self._get_dill_file(filename)
        objects = _read_dill_from(chk_dill_file)
        self._set_objects_to_global(objects)

        # 4. Restore other metadata
        ip = get_ipython()
        chk_meta_file = self._get_meta_file(filename)
        meta = _read_dill_from(chk_meta_file)
        ip.execution_count = meta[IPYTHON_EXECUTION_COUNT]

    def _get_meta_file(self, filename):
        return filename + '.meta'

    def _set_objects_to_global(self, objects):
        '''
        @param objects A dictionary with (name, value) mappings.
        '''
        ip = get_ipython()
        for name, value in objects.items():
            ip.user_ns[name] = value

    def _collect_non_jupyter_objects(self):
        name2val = {}
        ip = get_ipython()
        for name, value in ip.user_ns.items():
            if name.startswith('_'):
                continue
            if getattr(value, '__module__', '').startswith('IPython'):
                continue
            name2val[name] = value
        return name2val

    def _extract_ipython_history(sefl):
        '''
        Extract the following fields from `HistoryManager` in `IPython.core.history`
        1. input_hist_parsed
        2. input_hist_raw
        3. dir_hist
        4. output_hist
        5. output_hist_reprs

        In order to achieve this, we can rely on existing methods such as
        1. store_inputs(line_num, source, source_raw)
        2. store_output(line_num)
        3. get_range_by_str(rangestr='')    -> returns both inputs and outputs
        '''
        manager = get_ipython().history_manager  # HistoryManager class
        inputs = []    # will have (line_no, source) tuples
        for entry in manager.get_range_by_str(''):  # extracts all
            line_no = entry[1]
            source = entry[2]
            # raw_source = None if len(entry) <= 3 else entry[3]
            inputs.append((line_no, source))

    def _get_nb_file(self, filename):
        return filename + '.ipynb'

    def _get_dill_file(self, filename):
        return filename + '.dill'

    def _save_current_nb(self):
        '''
        Save the current file in a blocking fashion. A small functionality is added on top of
        a JavaScript wrapper to wait until the save is complete.
        '''
        filepath = ipynbname.path()
        last_mtime = os.path.getmtime(filepath)
        app = JupyterFrontEnd()
        # If the current notebook has never been saved, this command triggers a dialog.
        # Ideally, we want to force-save
        app.commands.execute('docmanager:save')
        current_mtime = last_mtime
        while current_mtime == last_mtime:
            time.sleep(0.5)
            current_mtime = os.path.getmtime(filepath)


def _save_dill_into(object, filename):
    with open(filename, 'wb') as file:
        dill.dump(object, file)


def _read_dill_from(filename):
    with open(filename, 'rb') as file:
        obj = dill.load(file)
        return obj


def _remove_kishu_functions(func_list):
    to_remove = [f for f in func_list if _is_kishu_function(f)]
    for f in to_remove:
        func_list.remove(f)


def _is_kishu_function(func):
    if not (callable(func) and hasattr(func, '__module__')):
        return False
    # if the function's module name is identical to this module name
    # we consider it is a kishu function.
    return func.__module__ == __name__


def _append_kishu_capture(lines):
    '''
    If the lines represent non-kishu commands, append %%kishucapture to its
    content as its first line, which will later be processed accordingly by
    the IPython kernel.

    Otherwise --- if the cell content includes kishu commands (starting
    with '%kishu') --- bypass this preprocessing so nothing is captured.

    Note:

    IPython already stores execution history, which we can access via
    `IPython.get_ipython().history_manager.get_range_by_str('')`. Thus, this functionality
    is redundant, and may get removed in the future.
    '''
    def includes_kishu_commands(lines):
        for line in lines:
            if line.strip().startswith('%kishu '):
                return True
        return False

    if includes_kishu_commands(lines):
        return lines

    lines.insert(0, '%%kishucapture\n')
    return lines


# In order to actually use these magics, you must register them with a
# running IPython.
def load_ipython_extension(ipython):
    """
    Any module file that define a function named `load_ipython_extension`
    can be loaded via `%load_ext module.path` or be configured to be
    autoloaded by IPython at startup time.
    """
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.
    ipython.register_magics(KishuMagics)

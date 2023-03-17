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

from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)
from IPython import get_ipython


# The class MUST call this class decorator at creation time
@magics_class
class KishuMagics(Magics):

    @cell_magic
    def kishucapture(self, line, cell):
        "my cell magic"
        return line, cell

    @line_magic
    def kishu(self, line):
        cmd = line.strip()
        msg = ''
        if cmd == 'enable':
            self._enable()
            msg = 'kishu is enabled.'
        elif cmd == 'disable':
            self._disable()
            msg = 'kishu is disabled.'
        elif cmd == 'status':
            status = 'enabled' if self.is_enabled() else 'disabled'
            msg = f'kishu status: {status}'
        else:
            msg = 'Unknown option: ' + cmd
        return msg

    def is_enabled(self):
        return hasattr(self, '_enabled') and self._enabled

    def _enable(self):
        if self.is_enabled():
            return
        self._enabled = True
        ip = get_ipython()
        ip.input_transformers_cleanup.append(_append_kishu_capture)

    def _disable(self):
        ip = get_ipython()
        _remove_kishu_functions(ip.input_transformers_cleanup)
        self._enabled = False


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

"""
Raised by state
"""


class TypeNotSupportedError(Exception):
    def __init__(self, type_name, var_name, var_value):
        super().__init__(f'{type_name} not yet supported ({var_name, var_value}).')


"""
Raised by jupyterint2
"""


class JupyterConnectionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class MissingConnectionInfoError(JupyterConnectionError):
    def __init__(self):
        super().__init__("Missing kernel connection information.")


class KernelNotAliveError(JupyterConnectionError):
    def __init__(self):
        super().__init__("Kernel is not alive.")


class StartChannelError(JupyterConnectionError):
    def __init__(self):
        super().__init__("Failed to start a channel to kernel.")


class NoChannelError(JupyterConnectionError):
    def __init__(self):
        super().__init__("No channel is connected.")

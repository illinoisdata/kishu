"""
Raised by state
"""


class TypeNotSupportedError(Exception):
    def __init__(self, type_name, var_name, var_value):
        super().__init__(f'{type_name} not yet supported ({var_name, var_value}).')

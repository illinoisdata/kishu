from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple


class UserNsWrapper(dict):
    """
        Wrapper class for monkey-patching Jupyter namespace to monitor variable accesses.
    """
    def __init__(self, *args, **kwargs) -> None:
        dict.__init__(self, *args, **kwargs)
        self.accessed_vars: Set[str] = set()

    def __getitem__(self, name: str) -> Any:
        self.accessed_vars.add(name)
        return dict.__getitem__(self, name)

    def __setitem__(self, name: str, obj: Any) -> None:
        return dict.__setitem__(self, name, obj)

    def __delitem__(self, name: str):
        return dict.__delitem__(self, name)

    def __iter__(self):
        self.accessed_vars = set(self.keys())  # TODO: Use enum for this.
        return dict.__iter__(self)

    def to_dict(self):
        return dict(self.items())

    def my_items(self):  # Deliberately named differently to avoid infinite recursion.
        return self.items()

    def get_accessed_vars(self) -> Set[str]:
        return self.accessed_vars

    def reset_accessed_vars(self) -> None:
        self.accessed_vars = set()


class Namespace:
    """
        Wrapper class around the kernel namespace.
    """
    IPYTHON_VARS = set(['In', 'Out', 'get_ipython', 'exit', 'quit', 'open'])
    KISHU_VARS: Set[str] = set()

    @staticmethod
    def register_kishu_vars(kishu_vars: Set[str]) -> None:
        Namespace.KISHU_VARS.update(kishu_vars)

    def __init__(self, user_ns: Dict[str, Any] = {}):
        self._ns_wrapper = UserNsWrapper(user_ns)

    def __contains__(self, key) -> bool:
        return key in self._ns_wrapper.to_dict()

    def __getitem__(self, key) -> Any:
        return self._ns_wrapper.to_dict()[key]

    def __delitem__(self, key) -> Any:
        del self._ns_wrapper[key]

    def __setitem__(self, key, value) -> Any:
        self._ns_wrapper[key] = value

    def __eq__(self, other) -> bool:
        return self._ns_wrapper.to_dict() == self._ns_wrapper.to_dict()

    def get_wrapper(self) -> UserNsWrapper:
        return self._ns_wrapper

    def keyset(self) -> Set[str]:
        return set(varname for varname, _ in filter(Namespace.no_ipython_var, self._ns_wrapper.my_items()))

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in filter(Namespace.no_ipython_var, self._ns_wrapper.my_items())}

    def update(self, other: Namespace):
        # Need to filter with other.to_dict() to not replace ipython variables.
        self._ns_wrapper.update(other.to_dict())

    def get_accessed_vars(self) -> Set[str]:
        return set(name for name in self._ns_wrapper.get_accessed_vars() if Namespace.no_ipython_var((name, None)))

    def reset_accessed_vars(self) -> None:
        self._ns_wrapper.reset_accessed_vars()

    def ipython_in(self) -> Optional[List[str]]:
        return self._ns_wrapper["In"] if "In" in self._ns_wrapper else None

    @staticmethod
    def no_ipython_var(name_obj: Tuple[str, Any]) -> bool:
        """
        @param name  The variable name.
        @param value  The associated object.
        @return  True if name is not an IPython-specific variable.
        """
        name, obj = name_obj
        if name.startswith('_'):
            return False
        if name in Namespace.IPYTHON_VARS:
            return False
        if name in Namespace.KISHU_VARS:
            return False
        if getattr(obj, '__module__', '').startswith('IPython'):
            return False
        return True

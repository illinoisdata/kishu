from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple


class TrackedNamespace(dict):
    """
    Wrapper class for monkey-patching Jupyter namespace to monitor variable accesses.
    """

    def __init__(self, *args, **kwargs) -> None:
        dict.__init__(self, *args, **kwargs)
        self._accessed_vars: Set[str] = set()
        self._assigned_vars: Set[str] = set()

    def __getitem__(self, name: str) -> Any:
        self._accessed_vars.add(name)
        return dict.__getitem__(self, name)

    def __setitem__(self, name: str, value: Any) -> None:
        self._assigned_vars.add(name)
        dict.__setitem__(self, name, value)

    def __iter__(self):
        self._accessed_vars = set(self.keys())  # TODO: Use enum for this.
        return dict.__iter__(self)

    def accessed_vars(self) -> Set[str]:
        return self._accessed_vars

    def reset_accessed_vars(self) -> None:
        self._accessed_vars = set()

    def assigned_vars(self) -> Set[str]:
        return self._assigned_vars

    def reset_assigned_vars(self) -> None:
        self._assigned_vars = set()


class Namespace:
    """
    Wrapper class around the kernel namespace.
    """

    IPYTHON_VARS = set(["In", "Out", "get_ipython", "exit", "quit", "open"])
    KISHU_VARS: Set[str] = set()

    @staticmethod
    def register_kishu_vars(kishu_vars: Set[str]) -> None:
        Namespace.KISHU_VARS.update(kishu_vars)

    def __init__(self, user_ns: Dict[str, Any] = {}):
        self._tracked_namespace = TrackedNamespace(user_ns)

    def __contains__(self, key) -> bool:
        return key in self._tracked_namespace

    def __getitem__(self, key) -> Any:
        return self._tracked_namespace[key]

    def __delitem__(self, key) -> Any:
        del self._tracked_namespace[key]

    def __setitem__(self, key, value) -> Any:
        self._tracked_namespace[key] = value

    def __eq__(self, other) -> bool:
        return dict(self._tracked_namespace) == dict(self._tracked_namespace)

    def get_tracked_namespace(self) -> TrackedNamespace:
        return self._tracked_namespace

    def keyset(self) -> Set[str]:
        return set(varname for varname, _ in filter(Namespace.no_ipython_var, self._tracked_namespace.items()))

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in filter(Namespace.no_ipython_var, self._tracked_namespace.items())}

    def update(self, other: Namespace):
        # Need to filter with other.to_dict() to not replace ipython variables.
        self._tracked_namespace.update(other.to_dict())

    def accessed_vars(self) -> Set[str]:
        return set(name for name in self._tracked_namespace.accessed_vars() if Namespace.no_ipython_var((name, None)))

    def reset_accessed_vars(self) -> None:
        self._tracked_namespace.reset_accessed_vars()

    def assigned_vars(self) -> Set[str]:
        return set(name for name in self._tracked_namespace.assigned_vars() if Namespace.no_ipython_var((name, None)))

    def reset_assigned_vars(self) -> None:
        self._tracked_namespace.reset_assigned_vars()

    def ipython_in(self) -> Optional[List[str]]:
        return self._tracked_namespace["In"] if "In" in self._tracked_namespace else None

    def ipython_out(self) -> Optional[Dict[int, Any]]:
        return self._tracked_namespace["Out"] if "Out" in self._tracked_namespace else None

    def subset(self, varnames: Set[str]) -> Namespace:
        return Namespace({k: self._tracked_namespace[k] for k in varnames if k in self})

    @staticmethod
    def no_ipython_var(name_obj: Tuple[str, Any]) -> bool:
        """
        @param name  The variable name.
        @param value  The associated object.
        @return  True if name is not an IPython-specific variable.
        """
        name, obj = name_obj
        if name.startswith("_"):
            return False
        if name in Namespace.IPYTHON_VARS:
            return False
        if name in Namespace.KISHU_VARS:
            return False
        if getattr(obj, "__module__", "").startswith("IPython"):
            return False
        return True

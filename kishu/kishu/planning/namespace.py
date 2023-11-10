from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple


class Namespace:
    """
        Wrapper class around the kernel namespace.
    """
    IPYTHON_VARS = set(['In', 'Out', 'get_ipython', 'exit', 'quit', 'open'])
    KISHU_INSTRUMENT = '_kishu'
    KISHU_VARS = set(['kishu', 'load_kishu', 'init_kishu', KISHU_INSTRUMENT])

    def __init__(self, user_ns: Dict[str, Any] = {}):
        self._user_ns = user_ns

    def __contains__(self, key) -> bool:
        return key in self._user_ns

    def __getitem__(self, key) -> Any:
        return self._user_ns[key]

    def __delitem__(self, key) -> Any:
        del self._user_ns[key]

    def __setitem__(self, key, value) -> Any:
        self._user_ns[key] = value

    def keys(self) -> Set[str]:
        return set(varname for varname, _ in filter(Namespace.no_ipython_var, self._user_ns.items()))

    def items(self) -> Dict[str, Any]:
        return {k: v for k, v in filter(Namespace.no_ipython_var, self._user_ns.items())}

    def update(self, other: Namespace):
        self._user_ns.update(other._user_ns)

    def ipython_in(self) -> Optional[List[str]]:
        return self._user_ns["In"] if "In" in self._user_ns else None

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

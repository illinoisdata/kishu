from __future__ import annotations

import dill

from dataclasses import dataclass, field
from IPython.core.interactiveshell import InteractiveShell
from typing import Any, Dict, List, Optional

from kishu.jupyter.namespace import Namespace
from kishu.storage.checkpoint import KishuCheckpoint


@dataclass
class RestoreActionContext:
    shell: InteractiveShell
    checkpoint_file: str
    exec_id: str


@dataclass
class VarNamesToObjects:
    """
    Convenient wrapper for serializing variables.
    """
    object_dict: Dict[str, Any] = field(default_factory=lambda: {})

    def dumps(self) -> bytes:
        return dill.dumps(self.object_dict)

    @staticmethod
    def loads(data: bytes) -> VarNamesToObjects:
        object_dict = dill.loads(data)
        res = VarNamesToObjects()
        for key, obj in object_dict.items():
            res[key] = obj
        return res

    def __setitem__(self, key, value) -> None:
        self.object_dict[key] = value

    def __getitem__(self, key) -> Any:
        return self.object_dict[key]

    def items(self):
        return self.object_dict.items()

    def keys(self):
        return self.object_dict.keys()


class CheckpointAction:
    def run(self, user_ns: Namespace):
        raise NotImplementedError("Must be extended by inherited classes.")


class SaveVariablesCheckpointAction(CheckpointAction):
    """
    Stores VarNamesToObjects into database.
    """
    def __init__(self) -> None:
        self.variable_names: List[str] = []
        self.filename: Optional[str] = None
        self.exec_id: Optional[str] = None

    def run(self, user_ns: Namespace):
        if self.filename is None:
            raise ValueError("filename is not set.")
        if self.exec_id is None:
            raise ValueError("exec_id is not set.")
        vars: VarNamesToObjects = VarNamesToObjects()
        for name in self.variable_names:
            vars[name] = user_ns[name]
        KishuCheckpoint(self.filename).store_checkpoint(self.exec_id, vars.dumps())


class CheckpointPlan:
    """
    Checkpoint select variables to the database.
    """
    def __init__(self) -> None:
        """
        @param checkpoint_file  The file to which data will be saved.
        """
        super().__init__()
        self.checkpoint_file: Optional[str] = None
        self.actions: List[CheckpointAction] = []

    @classmethod
    def create(cls, user_ns: Namespace, checkpoint_file: str, exec_id: str,
               var_names: Optional[List[str]] = None):
        """
        @param user_ns  A dictionary representing a target variable namespace. In Jupyter, this
                can be optained by `get_ipython().user_ns`.
        @param checkpoint_file  A file where checkpointed data will be stored to.
        """
        actions = cls.set_up_actions(user_ns, checkpoint_file, exec_id, var_names)
        plan = cls()
        plan.actions = actions
        plan.checkpoint_file = checkpoint_file
        return plan

    @classmethod
    def set_up_actions(cls, user_ns: Namespace, checkpoint_file: str,
                       exec_id: str, var_names: Optional[List[str]]) -> List[CheckpointAction]:
        if user_ns is None or checkpoint_file is None:
            raise ValueError("Fields are not properly initialized.")
        actions: List[CheckpointAction] = []
        vars: List[str] = cls.vars_to_checkpoint(user_ns, var_names)
        action = SaveVariablesCheckpointAction()
        action.variable_names = vars
        action.filename = checkpoint_file
        action.exec_id = exec_id
        actions.append(action)
        return actions

    @classmethod
    def vars_to_checkpoint(cls, user_ns: Namespace, var_names=None) -> List[str]:
        if user_ns is None:
            return []
        if var_names is None:
            return list(user_ns.keyset())
        key_set = set(user_ns.keyset())
        for name in var_names:
            if name not in key_set:
                raise ValueError("Checkpointing a non-existenting var: {}".format(name))
        return var_names

    def run(self, user_ns: Namespace) -> None:
        for action in self.actions:
            action.run(user_ns)


class RestoreAction:
    """
    A base class for any action.
    """
    def run(self, ctx: RestoreActionContext):
        """
        @param shell  A target space where restored variables will be set.
        """
        raise NotImplementedError("This base class must be extended.")


class LoadVariableRestoreAction(RestoreAction):
    """
    Load variables from a pickled file (using the dill module).
    """
    def __init__(self, var_names: Optional[List[str]] = None):
        """
        variable_names: The variables to restore.
        """
        if (var_names is not None) and (not isinstance(var_names, list)):
            raise ValueError("Unexpected type for var_names: {}".format(type(var_names)))
        self.variable_names: Optional[List[str]] = var_names

    def run(self, ctx: RestoreActionContext):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        data: bytes = KishuCheckpoint(ctx.checkpoint_file).get_checkpoint(ctx.exec_id)
        vars: VarNamesToObjects = VarNamesToObjects.loads(data)
        for key, obj in vars.items():
            # if self.variable_names is set, limit the restoration only to those variables.
            if self.variable_names is not None:
                if key not in self.variable_names:
                    continue
            ctx.shell.user_ns[key] = obj

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(var_names={self.variable_names})"

    def __str__(self) -> str:
        return self.__repr__()


class RerunCellRestoreAction(RestoreAction):
    """
    Load variables from a pickled file (using the dill module).
    """
    def __init__(self, cell_code: str = ""):
        """
        cell_code: cell code to rerun.
        """
        if (cell_code is not None) and (not isinstance(cell_code, str)):
            raise ValueError("Unexpected type for cell_code: {}".format(type(cell_code)))
        self.cell_code: Optional[str] = cell_code

    def run(self, ctx: RestoreActionContext):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        try:
            ctx.shell.run_cell(self.cell_code)
        except Exception:
            # We don't want to raise exceptions during code rerunning as the code can contain errors.
            pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(var_names={self.cell_code})"

    def __str__(self) -> str:
        return self.__repr__()


@dataclass
class RestorePlan:
    """
    TODO: In the future, we will combine recomputation and data loading.

    @param actions  A series of actions for restoring a state.
    """
    actions: List[RestoreAction] = field(default_factory=lambda: [])

    def add_rerun_cell_restore_action(self, cell_code: str):
        self.actions.append(RerunCellRestoreAction(cell_code))

    def add_load_variable_restore_action(self, variable_names: List[str]):
        self.actions.append(LoadVariableRestoreAction(variable_names))

    def run(self, checkpoint_file: str, exec_id: str) -> Namespace:
        """
        Performs a series of actions as specified in self.actions.

        @param user_ns  A target space where restored variables will be set.
        @param checkpoint_file  The file where information is stored.
        """
        ctx = RestoreActionContext(InteractiveShell(), checkpoint_file, exec_id)
        for action in self.actions:
            action.run(ctx)

        return Namespace(ctx.shell.user_ns)

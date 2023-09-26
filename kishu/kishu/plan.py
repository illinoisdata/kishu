from __future__ import annotations
import dataclasses
import dill
import json
import shortuuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from kishu.checkpoint_io import (
    get_checkpoint,
    get_log,
    get_log_item,
    get_log_items,
    store_checkpoint,
    store_log_item,
)


CommitId = str


@dataclass
class UnitExecution:
    """
    Represents a transactional execution. Everything is executed or nothing is executed.

    Note: This class must have sufficient fields for optimization. Thus, add new fields as needed.
    Note: For default list, default_factory is used instead of "default=list" to assign an actual
          list, instead of something that is instantiated on demand. This concrete list instance
          makes the json conversion possible.

    @param exec_id  A unique identifier of this transaction. Must be safe for file names.
    """
    exec_id: str = shortuuid.uuid()[:5]
    code_block: Optional[str] = None
    runtime_ms: Optional[int] = None
    accessed_resources: List[str] = field(default_factory=lambda: [])
    modified_resources: List[str] = field(default_factory=lambda: [])

    def save_into_db(self, checkpoint_file: str) -> None:
        data: bytes = dill.dumps(self)
        store_log_item(checkpoint_file, self.exec_id, data)

    @staticmethod
    def get_from_db(checkpoint_file: str, commit_id: str) -> Optional[UnitExecution]:
        data: bytes = get_log_item(checkpoint_file, commit_id)
        if len(data) == 0:
            return None
        return dill.loads(data)

    @staticmethod
    def get_commits(checkpoint_file: str, commit_ids: List[str]) -> Dict[str, UnitExecution]:
        return {
            commit_id: dill.loads(raw_exec_info)
            for commit_id, raw_exec_info in get_log_items(checkpoint_file, commit_ids).items()
        }


class ExecutionHistory:
    def __init__(self, checkpoint_file: str) -> None:
        self.history: Dict[str, UnitExecution] = {}
        self.checkpoint_file: str = checkpoint_file

    def _refresh(self) -> None:
        """
        Refresh log entries from db.
        """
        self.history.clear()
        entries: Dict[str, bytes] = get_log(self.checkpoint_file)
        for key, data in entries.items():
            self.history[key] = dill.loads(data)

    def append(self, exec_info: UnitExecution) -> None:
        """
        Appends a log entry to the database.
        """
        data: bytes = dill.dumps(exec_info)
        store_log_item(self.checkpoint_file, exec_info.exec_id, data)

    @classmethod
    def _clean_history(cls, history: Dict[str, UnitExecution]) -> Dict[str, Any]:
        cell_info_dict = {}
        for key, exec_info in history.items():
            obj = dataclasses.asdict(exec_info)
            null_value_keys = ['restore_plan']
            for k, v in obj.items():
                if v is None:
                    null_value_keys.append(k)
                elif isinstance(v, list) and len(v) == 0:
                    null_value_keys.append(k)
            for k in null_value_keys:
                if k in obj:
                    obj.pop(k)
            cell_info_dict[key] = obj
        return cell_info_dict

    def get_history(self) -> Dict[str, UnitExecution]:
        self._refresh()
        return self.history

    def __repr__(self) -> str:
        self._refresh()
        history = ExecutionHistory._clean_history(self.history)
        return json.dumps(history, sort_keys=True, indent=2)


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
    def run(self, user_ns: dict):
        raise NotImplementedError("Must be extended by inherited classes.")


class SaveVariablesCheckpointAction(CheckpointAction):
    """
    Stores VarNamesToObjects into database.
    """
    def __init__(self) -> None:
        self.variable_names: List[str] = []
        self.filename: Optional[str] = None
        self.exec_id: Optional[str] = None

    def run(self, user_ns: dict):
        if self.filename is None:
            raise ValueError("filename is not set.")
        if self.exec_id is None:
            raise ValueError("exec_id is not set.")
        vars: VarNamesToObjects = VarNamesToObjects()
        for name in self.variable_names:
            vars[name] = user_ns[name]
        store_checkpoint(self.filename, self.exec_id, vars.dumps())


class CheckpointPlan:

    def __init__(self) -> None:
        self.actions: List[CheckpointAction] = []

    def run(self, user_ns: dict) -> None:
        for action in self.actions:
            action.run(user_ns)

    def restore_plan(self) -> RestorePlan:
        raise NotImplementedError("Each inherited class must extend this method.")


class StoreEverythingCheckpointPlan(CheckpointPlan):
    """
    Checkpoint all the variables without any optimization.

    A dumb approach to checkpointing. This is useful as a baseline approach. This class must
    not be subclassed.
    """
    def __init__(self) -> None:
        """
        @param checkpoint_file  The file to which data will be saved.
        """
        super().__init__()
        self.checkpoint_file: Optional[str] = None

    @classmethod
    def create(cls, user_ns: dict, checkpoint_file: str, exec_id: str,
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
    def set_up_actions(cls, user_ns, checkpoint_file, exec_id, var_names) -> List[CheckpointAction]:
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
    def vars_to_checkpoint(cls, user_ns: dict, var_names=None) -> List[str]:
        if user_ns is None:
            return []
        if var_names is None:
            return list(user_ns.keys())
        key_set = set(user_ns.keys())
        for name in var_names:
            if name not in key_set:
                raise ValueError("Checkpointing a non-existenting var: {}".format(name))
        return var_names

    def restore_plan(self) -> RestorePlan:
        action = LoadVariableRestoreAction()
        return RestorePlan([action])


class RestoreAction:
    """
    A base class for any action.
    """
    def run(self, user_ns: dict, checkpoint_file: str, exec_id: str):
        """
        @param user_ns  A target space where restored variables will be set.
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

    def run(self, user_ns: dict, checkpoint_file: str, exec_id: str):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        data: bytes = get_checkpoint(checkpoint_file, exec_id)
        vars: VarNamesToObjects = VarNamesToObjects.loads(data)
        for key, obj in vars.items():
            # if self.variable_names is set, limit the restoration only to those variables.
            if self.variable_names is not None:
                if key not in self.variable_names:
                    continue
            user_ns[key] = obj

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

    def run(self, user_ns: dict, checkpoint_file: str, exec_id: str):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        # TODO: implement this when recomputation is required.
        raise Exception("Restoration via cell rerunning is not supported yet.")

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

    @classmethod
    def create(cls, cell_code_list: List[str], vss_to_migrate: Set[str], ces_to_recompute: Set[int]):
        # Sort variables to migrate based on cells they were created in.
        ce_to_vs_map = defaultdict(list)
        for vs_name in vss_to_migrate:
            ce_to_vs_map[ahg.variable_snapshots[vs_name][-1].output_ce.cell_num].append(vs_name)

        actions: List[RestoreAction] = []
        for cell_num in len(cell_code_list):
            if cell_num in ces_to_recompute:
                actions.append(RerunCellRestoreAction(cell_code_list[cell_num]))
            if len(ce_to_vs_map[cell_num]) > 0:
                actions.append(LoadVariableRestoreAction(
                    [vs_name for vs_name in ce_to_vs_map[cell_num]]))

        return cls(actions)

    def run(self, user_ns: dict, checkpoint_file: str, exec_id: str):
        """
        Performs a series of actions as specified in self.actions.

        @param user_ns  A target space where restored variables will be set.
        @param checkpoint_file  The file where information is stored.
        """
        for action in self.actions:
            action.run(user_ns, checkpoint_file, exec_id)


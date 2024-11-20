from __future__ import annotations

import atexit
import enum
from dataclasses import dataclass, field
from pathlib import Path
from queue import LifoQueue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import dill
from IPython.core.interactiveshell import InteractiveShell
from traitlets.config import Config

from kishu.exceptions import CommitIdNotExistError
from kishu.jupyter.namespace import Namespace
from kishu.storage.checkpoint import KishuCheckpoint
from kishu.storage.disk_ahg import VariableSnapshot


def no_history_interactive_shell():
    """
    Spawns an IPython InteractiveShell with no history tracking. This stops the shell from opening a file handler to a
    SQLite database that tracks history, which is not properly closed when the shell is destructed and causes a "too
    many files open" bug if many RestorePlans are run.
    """
    config = Config()
    config.HistoryManager.enabled = False
    return InteractiveShell(config=config)


class RestoreActionOrder(str, enum.Enum):
    """
    Order for performing restore actions; lower means higher priority within the cell execution.
    It doesn't matter whether LOAD_VARIABLE or INCREMENTAL_LOAD comes first,
    they will not coexist in the same RestorePlan nor do they interfere with each other.
    """

    RERUN_CELL = "rerun cell"
    LOAD_VARIABLE = "load variable"
    INCREMENTAL_LOAD = "incremental load"
    MOVE_VARIABLE = "move variable"


@dataclass(frozen=True, order=True)
class StepOrder:
    cell_num: int
    restore_action_order: RestoreActionOrder

    @staticmethod
    def new_rerun_cell(cell_num):
        return StepOrder(cell_num, RestoreActionOrder.RERUN_CELL)

    @staticmethod
    def new_load_variable(cell_num):
        return StepOrder(cell_num, RestoreActionOrder.LOAD_VARIABLE)

    @staticmethod
    def new_incremental_load(cell_num):
        return StepOrder(cell_num, RestoreActionOrder.INCREMENTAL_LOAD)

    @staticmethod
    def new_move_variable(cell_num):
        return StepOrder(cell_num, RestoreActionOrder.MOVE_VARIABLE)


@dataclass
class RestoreActionContext:
    shell: InteractiveShell
    database_path: Path
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
        self.database_path: Optional[Path] = None
        self.exec_id: Optional[str] = None

    def run(self, user_ns: Namespace):
        if self.database_path is None:
            raise ValueError("database_path is not set.")
        if self.exec_id is None:
            raise ValueError("exec_id is not set.")
        namespace: VarNamesToObjects = VarNamesToObjects()
        for name in self.variable_names:
            namespace[name] = user_ns[name]
        KishuCheckpoint(self.database_path).store_checkpoint(self.exec_id, namespace.dumps())


class IncrementalWriteCheckpointAction(CheckpointAction):
    """
    Stores VarNamesToObjects into database incrementally.
    """

    def __init__(self, vses_to_store: List[VariableSnapshot], database_path: Path, exec_id: str) -> None:
        self.vses_to_store = vses_to_store
        self.database_path = database_path
        self.exec_id = exec_id

    def run(self, user_ns: Namespace):
        KishuCheckpoint(self.database_path).store_variable_snapshots(self.exec_id, self.vses_to_store, user_ns)


class CheckpointPlan:
    """
    Checkpoint select variables to the database.
    """

    def __init__(self) -> None:
        """
        @param database_path  The file to which data will be saved.
        """
        super().__init__()
        self.database_path: Optional[Path] = None
        self.actions: List[CheckpointAction] = []

    @classmethod
    def create(cls, user_ns: Namespace, database_path: Path, exec_id: str, var_names: Optional[List[str]] = None):
        """
        @param user_ns  A dictionary representing a target variable namespace. In Jupyter, this
                can be optained by `get_ipython().user_ns`.
        @param database_path  A file where checkpointed data will be stored to.
        """
        actions = cls.set_up_actions(user_ns, database_path, exec_id, var_names)
        plan = cls()
        plan.actions = actions
        plan.database_path = database_path
        return plan

    @classmethod
    def set_up_actions(
        cls, user_ns: Namespace, database_path: Path, exec_id: str, var_names: Optional[List[str]]
    ) -> List[CheckpointAction]:
        if user_ns is None or database_path is None:
            raise ValueError("Fields are not properly initialized.")
        actions: List[CheckpointAction] = []
        variable_names: List[str] = cls.namespace_to_checkpoint(user_ns, var_names)
        action = SaveVariablesCheckpointAction()
        action.variable_names = variable_names
        action.database_path = database_path
        action.exec_id = exec_id
        actions.append(action)
        return actions

    @classmethod
    def namespace_to_checkpoint(cls, user_ns: Namespace, var_names=None) -> List[str]:
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


class IncrementalCheckpointPlan:
    """
    Checkpoint select variables to the database.
    """

    def __init__(self, database_path: Path, actions: List[CheckpointAction]) -> None:
        """
        @param database_path  The file to which data will be saved.
        """
        super().__init__()
        self.database_path = database_path
        self.actions = actions

    @staticmethod
    def create(user_ns: Namespace, database_path: Path, exec_id: str, vses_to_store: List[VariableSnapshot]):
        """
        @param user_ns  A dictionary representing a target variable namespace. In Jupyter, this
                can be optained by `get_ipython().user_ns`.
        @param database_path  A file where checkpointed data will be stored to.
        """
        actions = IncrementalCheckpointPlan.set_up_actions(user_ns, database_path, exec_id, vses_to_store)
        return IncrementalCheckpointPlan(database_path, actions)

    @classmethod
    def set_up_actions(
        cls, user_ns: Namespace, database_path: Path, exec_id: str, vses_to_store: List[VariableSnapshot]
    ) -> List[CheckpointAction]:
        if user_ns is None or database_path is None:
            raise ValueError("Fields are not properly initialized.")

        # Check all variables to checkpoint exist in the namespace.
        key_set = user_ns.keyset()
        for vs in vses_to_store:
            for var_name in vs.name:
                if var_name not in key_set:
                    raise ValueError("Checkpointing a non-existenting var: {}".format(var_name))

        return [
            IncrementalWriteCheckpointAction(
                vses_to_store,
                database_path,
                exec_id,
            )
        ]

    def run(self, user_ns: Namespace) -> None:
        for action in self.actions:
            action.run(user_ns)


@dataclass
class RestoreAction:
    """
    A base class for any action.
    """

    def run(self, ctx: RestoreActionContext):
        """
        @param shell  A target space where restored variables will be set.
        """
        raise NotImplementedError("This base class must be extended.")


@dataclass
class LoadVariableRestoreAction(RestoreAction):
    """
    Load variables from a pickled file (using the dill module).

    @param step_order: the order (i.e., when to run) of this restore action.
    @param var_names: The variables to load from storage.
    @param fallback_recomputation: List of cell reruns to perform to recompute the
        variables loaded by this action. Required when variable loading fails
        for fallback recomputation.
    """

    step_order: StepOrder
    variable_names: Set[str]
    fallback_recomputation: List[RerunCellRestoreAction]

    def run(self, ctx: RestoreActionContext):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        data: bytes = KishuCheckpoint(Path(ctx.database_path)).get_checkpoint(ctx.exec_id)
        namespace: VarNamesToObjects = VarNamesToObjects.loads(data)
        for key, obj in namespace.items():
            # if self.variable_names is set, limit the restoration only to those variables.
            if key in self.variable_names:
                ctx.shell.user_ns[key] = obj


@dataclass
class IncrementalLoadRestoreAction(RestoreAction):
    """
    Load select variables (incrementally) from the database.

    @param step_order: the order (i.e., when to run) of this restore action.
    @param var_names: The variables to load from storage.
    @param fallback_recomputation: List of cell reruns to perform to recompute the
        variables loaded by this action. Required when variable loading fails
        for fallback recomputation.
    """

    step_order: StepOrder
    variable_snapshots: Set[VariableSnapshot]
    fallbacl_recomputation: List[RerunCellRestoreAction]

    def run(self, ctx: RestoreActionContext):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        # Each dictionary contains the data for a VS in the form of its variable name-to-data mappings.
        snapshots: List[bytes] = KishuCheckpoint(ctx.database_path).get_variable_snapshots(self.variable_snapshots)
        for snapshot in snapshots:
            vs_dict = dill.loads(snapshot)
            if not isinstance(vs_dict, dict):
                raise ValueError(f"loaded snapshot is of type {type(vs_dict)}, expected type dict")
            for k, v in vs_dict.items():
                ctx.shell.user_ns[k] = v


@dataclass
class MoveVariableRestoreAction(RestoreAction):
    """
    Move a variable currently in the namespace to the new namespace.

    @param step_order: the order (i.e., when to run) of this restore action.
    @param vars_to_move: Variables to move to the new namespace.
    """

    step_order: StepOrder
    vars_to_move: Namespace

    def run(self, ctx: RestoreActionContext):
        """
        @param user_ns  A target space where the existing variable will be moved to.
        """
        for k, v in self.vars_to_move.to_dict().items():
            ctx.shell.user_ns[k] = v


@dataclass
class RerunCellRestoreAction(RestoreAction):
    """
    Rerun a cell execution and update the shell with the results.

    @param step_order: the order (i.e., when to run) of this restore action.
    @param cell_code: Cell code to rerun.
    """

    step_order: StepOrder
    cell_code: str

    def run(self, ctx: RestoreActionContext):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        try:
            ctx.shell.run_cell(self.cell_code)
        except Exception:
            # We don't want to raise exceptions during code rerunning as the code can contain errors.
            pass


# Idea from https://stackoverflow.com/questions/57633815/atexit-how-does-one-trigger-it-manually
class AtExitContext:

    def __init__(self) -> None:
        self._original_atexit_register: Optional[Callable] = None
        self._atexit_queue: LifoQueue = LifoQueue()

    def __enter__(self) -> AtExitContext:
        self._original_atexit_register = atexit.register
        atexit.register = self.intercepted_register  # type: ignore
        return self

    def intercepted_register(self, func, *args, **kwargs) -> None:
        if self._original_atexit_register is not None:
            self._original_atexit_register(func, *args, **kwargs)
            self._atexit_queue.put((func, args, kwargs))  # Intercept atexit function in this context.

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Recover previous registry.
        if self._original_atexit_register is not None:
            atexit.register = self._original_atexit_register  # type: ignore
            self._original_atexit_register = None

            # Call all registed atexit function within this context.
            while self._atexit_queue.qsize():
                func, args, kwargs = self._atexit_queue.get()
                atexit.unregister(func)
                try:
                    func(*args, **kwargs)
                except Exception:
                    pass


@dataclass
class RestorePlan:
    """
    TODO: In the future, we will combine recomputation and data loading.

    @param actions  A series of actions for restoring a state.
    """

    actions: Dict[StepOrder, RestoreAction] = field(default_factory=lambda: {})

    # TODO: add the undeserializable variables which caused fallback computation to config list.
    fallbacked_actions: List[LoadVariableRestoreAction] = field(default_factory=lambda: [])

    def add_rerun_cell_restore_action(self, cell_num: int, cell_code: str):
        step_order = StepOrder.new_rerun_cell(cell_num)
        assert step_order not in self.actions

        self.actions[step_order] = RerunCellRestoreAction(step_order, cell_code)

    def add_load_variable_restore_action(
        self, cell_num: int, variable_names: List[str], fallback_recomputation: List[Tuple[int, str]]
    ):
        step_order = StepOrder.new_load_variable(cell_num)
        assert step_order not in self.actions

        self.actions[step_order] = LoadVariableRestoreAction(
            step_order,
            set(variable_names),
            [RerunCellRestoreAction(StepOrder.new_rerun_cell(cell_num), code) for cell_num, code in fallback_recomputation],
        )

    def add_incremental_load_restore_action(
        self, cell_num: int, variable_snapshots: Set[VariableSnapshot], fallback_recomputation: List[Tuple[int, str]]
    ):
        step_order = StepOrder.new_incremental_load(cell_num)
        assert step_order not in self.actions

        self.actions[step_order] = IncrementalLoadRestoreAction(
            step_order,
            variable_snapshots,
            [RerunCellRestoreAction(StepOrder.new_rerun_cell(cell_num), code) for cell_num, code in fallback_recomputation],
        )

    def add_move_variable_restore_action(self, cell_num: int, vars_to_move: Namespace):
        step_order = StepOrder.new_move_variable(cell_num)
        assert step_order not in self.actions

        self.actions[step_order] = MoveVariableRestoreAction(step_order, vars_to_move)

    def run(self, database_path: Path, exec_id: str) -> Namespace:
        """
        Performs a series of actions as specified in self.actions.

        @param user_ns  A target space where restored variables will be set.
        @param database_path  The file where information is stored.
        """
        while True:
            with AtExitContext():  # Intercept and trigger all atexit functions.
                ctx = RestoreActionContext(no_history_interactive_shell(), database_path, exec_id)

                # Run restore actions sorted by cell number, then rerun cells before loading variables.
                for _, action in sorted(self.actions.items(), key=lambda k: k[0]):
                    try:
                        action.run(ctx)
                    except CommitIdNotExistError as e:
                        # Problem was caused by Kishu itself (specifically, missing file for commit ID).
                        raise e
                    except Exception as e:
                        if not isinstance(action, LoadVariableRestoreAction):
                            raise e

                        # If action is load variable, replace action with fallback recomputation plan
                        self.fallbacked_actions.append(action)
                        del self.actions[action.step_order]
                        for rerun_cell_action in action.fallback_recomputation:
                            self.actions[rerun_cell_action.step_order] = rerun_cell_action
                        break
                else:
                    return Namespace(ctx.shell.user_ns.copy())

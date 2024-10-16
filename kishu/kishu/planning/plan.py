from __future__ import annotations

import atexit
import functools
from dataclasses import dataclass, field
from pathlib import Path
from queue import LifoQueue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import dill
from IPython.core.interactiveshell import InteractiveShell

from kishu.exceptions import CommitIdNotExistError, DuplicateRestoreActionError
from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import VsConnectedComponents
from kishu.storage.checkpoint import KishuCheckpoint


@functools.total_ordering
@dataclass(frozen=True)
class StepOrder:
    cell_num: int
    is_load_var: bool

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cell_num={self.cell_num}, is_load_var={self.is_load_var})"

    def __eq__(self, other):
        return self.cell_num == other.cell_num and self.is_load_var == other.is_load_var

    def __lt__(self, other):
        # For the same cell number, the recomputation should be performed before variable loading.
        if self.cell_num == other.cell_num:
            return int(self.is_load_var) < int(other.is_load_var)
        return self.cell_num < other.cell_num


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
        namespace: VarNamesToObjects = VarNamesToObjects()
        for name in self.variable_names:
            namespace[name] = user_ns[name]
        KishuCheckpoint(Path(self.filename)).store_checkpoint(self.exec_id, namespace.dumps())


class IncrementalWriteCheckpointAction(CheckpointAction):
    """
    Stores VarNamesToObjects into database incrementally.
    """

    def __init__(self, vs_connected_components: VsConnectedComponents, filename: str, exec_id: str) -> None:
        self.vs_connected_components = vs_connected_components
        self.filename = filename
        self.exec_id = exec_id

    def run(self, user_ns: Namespace):
        KishuCheckpoint(Path(self.filename)).store_variable_kv(self.exec_id, self.vs_connected_components, user_ns)


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
    def create(cls, user_ns: Namespace, checkpoint_file: str, exec_id: str, var_names: Optional[List[str]] = None):
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
    def set_up_actions(
        cls, user_ns: Namespace, checkpoint_file: str, exec_id: str, var_names: Optional[List[str]]
    ) -> List[CheckpointAction]:
        if user_ns is None or checkpoint_file is None:
            raise ValueError("Fields are not properly initialized.")
        actions: List[CheckpointAction] = []
        variable_names: List[str] = cls.namespace_to_checkpoint(user_ns, var_names)
        action = SaveVariablesCheckpointAction()
        action.variable_names = variable_names
        action.filename = checkpoint_file
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

    def __init__(self, checkpoint_file: str, actions: List[CheckpointAction]) -> None:
        """
        @param checkpoint_file  The file to which data will be saved.
        """
        super().__init__()
        self.checkpoint_file = checkpoint_file
        self.actions = actions

    @staticmethod
    def create(user_ns: Namespace, checkpoint_file: str, exec_id: str, vs_connected_components: VsConnectedComponents):
        """
        @param user_ns  A dictionary representing a target variable namespace. In Jupyter, this
                can be optained by `get_ipython().user_ns`.
        @param checkpoint_file  A file where checkpointed data will be stored to.
        """
        actions = IncrementalCheckpointPlan.set_up_actions(user_ns, checkpoint_file, exec_id, vs_connected_components)
        return IncrementalCheckpointPlan(checkpoint_file, actions)

    @classmethod
    def set_up_actions(
        cls, user_ns: Namespace, checkpoint_file: str, exec_id: str, vs_connected_components: VsConnectedComponents
    ) -> List[CheckpointAction]:
        if user_ns is None or checkpoint_file is None:
            raise ValueError("Fields are not properly initialized.")

        # Check all variables to checkpoint exist in the namespace.
        key_set = user_ns.keyset()
        for var_name in vs_connected_components.get_variable_names():
            if var_name not in key_set:
                raise ValueError("Checkpointing a non-existenting var: {}".format(var_name))

        return [
            IncrementalWriteCheckpointAction(
                vs_connected_components,
                checkpoint_file,
                exec_id,
            )
        ]

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

    def __init__(
        self, step_order: StepOrder, var_names: List[str] = [], fallback_recomputation: List[RerunCellRestoreAction] = []
    ):
        """
        @param step_order: the order (i.e., when to run) of this restore action.
        @param var_names: The variables to load from storage.
        @param fallback_recomputation: List of cell reruns to perform to recompute the
            variables loaded by this action. Required when variable loading fails
            for fallback recomputation.
        """
        self.step_order = step_order
        self.variable_names: Set[str] = set(var_names)
        self.fallback_recomputation: List[RerunCellRestoreAction] = fallback_recomputation

    def run(self, ctx: RestoreActionContext):
        """
        @param user_ns  A target space where restored variables will be set.
        """
        data: bytes = KishuCheckpoint(Path(ctx.checkpoint_file)).get_checkpoint(ctx.exec_id)
        namespace: VarNamesToObjects = VarNamesToObjects.loads(data)
        for key, obj in namespace.items():
            # if self.variable_names is set, limit the restoration only to those variables.
            if key in self.variable_names:
                ctx.shell.user_ns[key] = obj

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(step_order={self.step_order}, \
        var_names={self.variable_names}, \
        fallback recomputation cells={[i.step_order.cell_num for i in self.fallback_recomputation]})"

    def __str__(self) -> str:
        return self.__repr__()


class RerunCellRestoreAction(RestoreAction):
    """
    Load variables from a pickled file (using the dill module).
    """

    def __init__(self, step_order: StepOrder, cell_code: str = ""):
        """
        cell_num: cell number of the executed cell code.
        cell_code: cell code to rerun.
        """
        self.step_order = step_order
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
        return f"{self.__class__.__name__}(step_order={self.step_order}, cell_code={self.cell_code})"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other):
        return self.step_order == other.step_order and self.cell_code == other.cell_code


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
        step_order = StepOrder(cell_num, False)
        if step_order in self.actions:
            raise DuplicateRestoreActionError(step_order.cell_num, step_order.is_load_var)
        self.actions[step_order] = RerunCellRestoreAction(step_order, cell_code)

    def add_load_variable_restore_action(
        self, cell_num: int, variable_names: List[str], fallback_recomputation: List[Tuple[int, str]]
    ):
        step_order = StepOrder(cell_num, True)
        if step_order in self.actions:
            raise DuplicateRestoreActionError(step_order.cell_num, step_order.is_load_var)

        self.actions[step_order] = LoadVariableRestoreAction(
            step_order, variable_names, [RerunCellRestoreAction(StepOrder(i[0], False), i[1]) for i in fallback_recomputation]
        )

    def run(self, checkpoint_file: str, exec_id: str) -> Namespace:
        """
        Performs a series of actions as specified in self.actions.

        @param user_ns  A target space where restored variables will be set.
        @param checkpoint_file  The file where information is stored.
        """
        while True:
            with AtExitContext():  # Intercept and trigger all atexit functions.
                ctx = RestoreActionContext(InteractiveShell(), checkpoint_file, exec_id)

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

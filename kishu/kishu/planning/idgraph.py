from __future__ import annotations

try:
    import dill as kishu_pickle
except ImportError:
    import pickle as kishu_pickle

import enum
import io
from dataclasses import dataclass
from types import BuiltinFunctionType
from typing import Any, Set, Type

import numpy
import pandas
import xxhash

from kishu.storage.config import Config

BINARRAY = b"array"


@dataclass(frozen=True)
class ClassInstance:
    name: str
    module: str

    @staticmethod
    def from_object(obj: Any) -> ClassInstance:
        return ClassInstance(type(obj).__name__, type(obj).__module__)


KISHU_DEFAULT_ARRAYTYPES = {
    ClassInstance("ndarray", "numpy"),
    ClassInstance("Tensor", "torch"),
    ClassInstance("csr_matrix", "scipy.sparse"),
    ClassInstance("csc_matrix", "scipy.sparse"),
    ClassInstance("lil_matrix", "scipy.sparse"),
}


class TrackOpcode(str, enum.Enum):
    IMMUTABLE = "immutable"
    DEFINITELY_CHANGED = "definitely_changed"
    SKIP_WRITE = "skip_write"
    DEFAULT = "default"


class TrackedPickler(kishu_pickle.Pickler):
    def __init__(self, *args, **kwargs):
        kishu_pickle.Pickler.__init__(self, *args, **kwargs)
        self.definitely_changed: bool = False

    def _memoize(self, obj: Any, save_persistent_id: bool) -> None:
        self.framer.commit_frame()

        # Check for persistent id (defined by a subclass)
        if save_persistent_id:
            pid = self.persistent_id(obj)
            if pid is not None:
                self.save_pers(pid)
                return

        # Check the memo
        x = self.memo.get(id(obj))
        if x is not None:
            self.write(self.get(x[0]))
            return

        self.memoize(obj)

    def track_opcode(self, obj: Any) -> TrackOpcode:
        return TrackOpcode.DEFAULT

    def save(self, obj: Any, save_persistent_id=True) -> None:
        opcode = self.track_opcode(obj)
        if opcode == TrackOpcode.IMMUTABLE:
            self.write(kishu_pickle.dumps(obj))

        elif opcode == TrackOpcode.DEFINITELY_CHANGED:
            self.definitely_changed = True
            self._memoize(obj, save_persistent_id)

        elif opcode == TrackOpcode.SKIP_WRITE:
            self._memoize(obj, save_persistent_id)

        elif opcode == TrackOpcode.DEFAULT:
            try:
                return kishu_pickle.Pickler.save(self, obj, save_persistent_id)
            except (kishu_pickle.PickleError, ValueError, AttributeError, TypeError):
                self.definitely_changed = True
                self._memoize(obj, save_persistent_id)

        else:
            raise NotImplementedError("Unknown opcode")


# Faster ID graph implementation that has potential accuracy losses. Use at your own discretion.
class ExperimentalTrackedPickler(TrackedPickler):
    def __init__(self, *args, **kwargs):
        TrackedPickler.__init__(self, *args, **kwargs)

    def track_opcode(self, obj: Any) -> TrackOpcode:
        if isinstance(obj, pandas.DataFrame):
            # Pandas dataframe dirty bit speedup. We can use the writeable flag as a dirty bit to check for updates
            # (as any Pandas operation will flip the bit back to True).
            # Notably, this may prevent the usage of certain slicing operations; however, they are rare compared
            # to boolean indexing, hence this tradeoff is acceptable.
            definitely_changed = False
            for _, col in obj.items():
                if col.__array__().flags.writeable:
                    definitely_changed = True
                col.__array__().flags.writeable = False

            if definitely_changed:
                return TrackOpcode.DEFINITELY_CHANGED
            else:
                return TrackOpcode.SKIP_WRITE

        elif ClassInstance.from_object(obj) in KISHU_DEFAULT_ARRAYTYPES:
            # Hash speedup for arraytypes. They are hashed instead of recursing into the array themselves.
            # Like the pandas dataframe hack, this may incur correctness loss if a field inside the array is assigned
            # to another variable (and causing an overlap); however, this is rare in notebooks and the speedup this brings
            # is significant.
            h = xxhash.xxh3_128()

            # xxhash's update works with arbitrary arrays, even object arrays
            h.update(numpy.ascontiguousarray(obj.data))  # type: ignore
            self.write(BINARRAY + h.digest())
            return TrackOpcode.SKIP_WRITE

        elif isinstance(obj, (str, bytes, type, BuiltinFunctionType)):
            return TrackOpcode.IMMUTABLE

        elif issubclass(type(obj), numpy.dtype):
            return TrackOpcode.IMMUTABLE

        return TrackOpcode.DEFAULT


@dataclass
class IdGraph:
    root_id: int
    root_type: Type
    serialized_hash: bytes
    addresses: Set[int]
    definitely_changed: bool

    @staticmethod
    def from_object(obj: Any) -> IdGraph:
        f = io.BytesIO()
        if Config.get("IDGRAPH", "experimental_tracker", False):
            pickler = ExperimentalTrackedPickler(f, kishu_pickle.HIGHEST_PROTOCOL, recurse=True)
        else:
            pickler = TrackedPickler(f, kishu_pickle.HIGHEST_PROTOCOL, recurse=True)
        pickler.dump(obj)
        h = xxhash.xxh3_128()
        h.update(f.getvalue())
        return IdGraph(
            root_id=id(obj),
            root_type=type(obj),
            serialized_hash=h.digest(),
            addresses=set(pickler.memo.keys()),
            definitely_changed=pickler.definitely_changed,
        )

    def is_overlap(self, other: IdGraph) -> bool:
        return bool(self.addresses.intersection(other.addresses))

    def is_root_id_and_type_equals(self, other: IdGraph):
        """
        Compare only the ID and type fields of root nodes of 2 ID graphs.
        Used for detecting non-overwrite modifications.
        """
        return self.root_id == other.root_id and self.root_type == other.root_type

    def __eq__(self, other: Any):
        if not isinstance(other, IdGraph):
            raise NotImplementedError("Comparisons between ID Graphs and non-ID Graphs are not supported.")
        return not other.definitely_changed and self.serialized_hash == other.serialized_hash

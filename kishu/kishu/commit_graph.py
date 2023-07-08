from __future__ import annotations

import json
import os
import pickle

from typing import Any, Dict, Iterator, List, Literal, Optional, Set, Tuple, Union
from typing_extensions import TypeAlias

"""
Common types.
"""
CommitId = str
BlockPosition: TypeAlias = Tuple[int, int]  # (rank, position)

"""
Block size in number of nodes. Tail block has MAX_BASE_SIZE nodes where each upper rank block is
MUL_SIZE times larger than its lower rank block (exponential sizes).
"""
MAX_BASE_SIZE: int = 128
MUL_SIZE: int = 2

"""
Node byte format: [ header | serialzied node | padding ] where header contains the serialized node
size in bytes. Header is an integer encoded in little endian. This assumes each node fits in 200 B.
"""
NODE_SIZE = 200  # bytes
NODE_HEADER_SIZE = 1  # bytes
NODE_DATA_SIZE = NODE_SIZE - NODE_HEADER_SIZE
NODE_HEADER_BYTEORDER: Literal['little', 'big'] = 'little'
assert 2 ** (8 * NODE_HEADER_SIZE) >= NODE_DATA_SIZE

"""
Useful constants.
"""
ABSOLUTE_PAST: CommitId = ""  # Logically first commit (e.g., commit graph's root).
UNSET_POSITION = (-99, -99)  # Position of a node that has not been persisted.


def MAX_BLOCK_SIZE(rank):
    return MAX_BASE_SIZE * (MUL_SIZE ** (rank + 1))


class CommitInfo:

    def __init__(self, commit_id: CommitId, parent_id: CommitId):
        self._commit_id = commit_id
        self._parent_id = parent_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CommitInfo):
            return False
        return (
            self._commit_id == other._commit_id and
            self._parent_id == other._parent_id
        )

    def __repr__(self) -> str:
        return f"CommitInfo(\"{self._commit_id}\", \"{self._parent_id}\")"

    def __str__(self) -> str:
        return f"Commit({self._commit_id})"


class CommitNode:

    def __init__(self, commit_id: CommitId, parent_id: CommitId, commit_info: CommitInfo):
        self._commit_id = commit_id
        self._parent_id = parent_id
        self._info = commit_info
        self._position = UNSET_POSITION
        self._parent_position = UNSET_POSITION

    def commit_id(self) -> CommitId:
        return self._commit_id

    def parent_id(self) -> CommitId:
        return self._parent_id

    def info(self) -> CommitInfo:
        return self._info

    def position(self) -> BlockPosition:
        return self._position

    def parent_position(self) -> BlockPosition:
        return self._parent_position

    def set_position(self, position: BlockPosition) -> None:
        self._position = position

    def set_parent_position(self, position: BlockPosition) -> None:
        self._parent_position = position

    def serialize(self) -> bytes:
        self_bytes = pickle.dumps(self)
        self_bytes_len = len(self_bytes)
        if self_bytes_len > NODE_DATA_SIZE:
            raise ValueError(f"CommitNode is too large ({self_bytes_len} > {NODE_DATA_SIZE})")
        header = self_bytes_len.to_bytes(NODE_HEADER_SIZE, NODE_HEADER_BYTEORDER)
        padding = bytes(NODE_DATA_SIZE - self_bytes_len)
        return header + self_bytes + padding

    @staticmethod
    def deserialize(buffer: bytes) -> CommitNode:
        self_bytes_len = int.from_bytes(buffer[:NODE_HEADER_SIZE], NODE_HEADER_BYTEORDER)
        self_bytes = buffer[NODE_HEADER_SIZE:NODE_HEADER_SIZE + self_bytes_len]
        return pickle.loads(self_bytes)


class CommitInfoIterator(Iterator[CommitInfo]):
    pass


class CommitGraphBlockTail:

    def __init__(self, root_path):
        # Create new empty block.
        self._root_path = root_path
        self._size = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size": self._size,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any], root_path: str):
        self = CommitGraphBlockTail(root_path)
        self._size = d["size"]
        return self

    def size(self):
        return self._size

    def read(self, position: BlockPosition) -> CommitNode:
        rank, offset = position
        assert rank == -1
        with open(self._file_path(), "rb") as f:
            f.seek(NODE_SIZE * offset)
            node_bytes = f.read(NODE_SIZE)
        return CommitNode.deserialize(node_bytes)

    def read_all(self) -> List[CommitNode]:
        try:
            with open(self._file_path(), "rb") as f:
                nodes = [CommitNode.deserialize(f.read(NODE_SIZE)) for idx in range(self._size)]
            return nodes
        except FileNotFoundError:
            return []

    def find_and_read(self, commit_id: CommitId) -> Optional[CommitNode]:
        # Linear search.
        try:
            with open(self._file_path(), "rb") as f:
                for idx in range(self._size):
                    node = CommitNode.deserialize(f.read(NODE_SIZE))
                    if node.commit_id() == commit_id:
                        return node
        except FileNotFoundError:
            pass
        return None

    def insert(self, node: CommitNode) -> None:
        node.set_position((-1, self._size))
        with open(self._file_path(), "a+b") as f:
            node_bytes = node.serialize()
            assert len(node_bytes) == NODE_SIZE, f"{len(node_bytes)} != {NODE_SIZE}"
            f.write(node_bytes)
        self._size += 1

    def clear(self) -> None:
        self._size = 0
        try:
            os.remove(self._file_path())
        except FileNotFoundError:
            pass

    def _file_path(self) -> str:
        return os.path.join(self._root_path, "commit_block_tail")


class CommitGraphBlockSorted:

    def __init__(self, rank, root_path):
        # Create new empty block.
        self._root_path = root_path
        self._rank = rank
        self._gen = 0  # Increment when merge.
        self._size = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self._rank,
            "gen": self._gen,
            "size": self._size,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any], root_path: str):
        self = CommitGraphBlockSorted(d["rank"], root_path)
        self._gen = d["gen"]
        self._size = d["size"]
        return self

    def size(self):
        return self._size

    def read(self, position: BlockPosition) -> CommitNode:
        rank, offset = position
        assert rank == self._rank
        with open(self._file_path(), "rb") as f:
            f.seek(NODE_SIZE * offset)
            node_bytes = f.read(NODE_SIZE)
        return CommitNode.deserialize(node_bytes)

    def read_all(self) -> List[CommitNode]:
        try:
            with open(self._file_path(), "rb") as f:
                nodes = [CommitNode.deserialize(f.read(NODE_SIZE)) for idx in range(self._size)]
            return nodes
        except FileNotFoundError:
            return []

    def find_and_read(self, commit_id: CommitId) -> Optional[CommitNode]:
        # TODO: binary search.
        try:
            with open(self._file_path(), "rb") as f:
                for idx in range(self._size):
                    node = CommitNode.deserialize(f.read(NODE_SIZE))
                    if node.commit_id() == commit_id:
                        return node
        except FileNotFoundError:
            pass
        return None

    def merge(self, other: CommitGraphBlockSorted) -> CommitGraphBlockSorted:
        # TODO: merge sort?
        return self.merge_with_nodes(other.read_all(), other._rank)

    def merge_tail(self, other: CommitGraphBlockTail) -> CommitGraphBlockSorted:
        return self.merge_with_nodes(other.read_all(), -1)

    def merge_with_nodes(self, other_nodes: List[CommitNode], other_rank: int) -> CommitGraphBlockSorted:
        # Read all nodes from both sides.
        nodes = self.read_all()
        nodes.extend(other_nodes)

        # Draft new block properties.
        new_block = CommitGraphBlockSorted(self._rank, self._root_path)
        new_block._gen = self._gen + 1
        new_block._size = len(nodes)

        # Sort and translate position.
        new_node_offsets = sorted(range(len(nodes)), key=lambda idx: nodes[idx].commit_id())
        new_other_offset = {
            old_offset: new_offset for new_offset, old_offset in enumerate(new_node_offsets)
        }
        for node in nodes:
            rank, offset = node.parent_position()
            if rank == self._rank:
                node.set_parent_position((self._rank, new_other_offset[offset]))
            elif rank == other_rank:
                node.set_parent_position((self._rank, new_other_offset[offset + self._size]))
        nodes = [nodes[idx] for idx in new_other_offset]
        for offset, node in enumerate(nodes):
            node.set_position((self._rank, offset))

        # Write to next-generation block.
        with open(new_block._file_path(), "wb") as f:
            for node in nodes:
                node_bytes = node.serialize()
                assert len(node_bytes) == NODE_SIZE, f"{len(node_bytes)} != {NODE_SIZE}"
                f.write(node_bytes)

        return new_block

    def clear(self) -> None:
        self._size = 0
        try:
            os.remove(self._file_path())
        except FileNotFoundError:
            pass

    def _file_path(self, gen=None) -> str:
        return os.path.join(self._root_path, f"commit_block_{self._rank}_{self._gen}")


class CommitGraphWalker(CommitInfoIterator):
    def __init__(self, store: CommitGraphStore, current_node: Optional[CommitNode]):
        self._store = store
        self._current_node = current_node

    def __iter__(self) -> CommitGraphWalker:
        return self

    def __next__(self) -> CommitInfo:
        if self._current_node is None:
            raise StopIteration
        current_node = self._current_node
        next_position = self._current_node.parent_position()
        if next_position == UNSET_POSITION:
            self._current_node = None
        else:
            self._current_node = self._store._read(next_position)
        return current_node.info()


class CommitGraphStore:

    def __init__(self, root_path: str):
        self._root_path = root_path
        self._sorted_blocks: List[CommitGraphBlockSorted] = []
        self._tail_block: CommitGraphBlockTail = CommitGraphBlockTail(self._root_path)

        try:
            self._load_meta()
        except FileNotFoundError:
            pass

    def begin_read(self, commit_id: CommitId) -> CommitInfoIterator:
        return CommitGraphWalker(self, self._find_and_read(commit_id))

    def insert(self, commit_id: CommitId, parent_id: CommitId, commit_info: CommitInfo):
        parent_node = self._find_and_read(parent_id)
        node = CommitNode(commit_id, parent_id, commit_info)
        if parent_node is not None:
            node.set_parent_position(parent_node.position())
        self._insert(node)

    """
    Commit graph chain: management over collection of blocks.
    """

    def _read(self, position: BlockPosition) -> CommitNode:
        rank, offset = position
        if rank < -1 or rank >= len(self._sorted_blocks):
            raise IndexError(
                f"Rank {position} out of range ({len(self._sorted_blocks)} sorted blocks)."
            )
        if offset >= MAX_BLOCK_SIZE(rank):
            raise IndexError(f"Offset {offset} out of range for rank {rank}.")
        if rank == -1:
            return self._tail_block.read(position)
        return self._sorted_blocks[rank].read(position)

    def _find_and_read(self, commit_id: CommitId) -> Optional[CommitNode]:
        # Find in tail first, then lower-rank to higher-rank sorted blocks.
        # Assuming most commit_id is skewed towards newer commits.
        if commit_id == ABSOLUTE_PAST:
            return None
        node = self._tail_block.find_and_read(commit_id)
        if node is not None:
            return node
        for sorted_block in self._sorted_blocks:
            node = sorted_block.find_and_read(commit_id)
            if node is not None:
                return node
        return None

    def _insert(self, node: CommitNode) -> None:
        self._tail_block.insert(node)
        if self._tail_block.size() >= MAX_BLOCK_SIZE(-1):
            # Tail block is full; merging into the first sorted block.
            new_sorted_block = self._get_sorted_block(0).merge_tail(self._tail_block)

            # Merge until size is under capacity by rank.
            rank = 0
            while new_sorted_block.size() >= MAX_BLOCK_SIZE(rank):
                rank += 1
                next_sorted_block = self._get_sorted_block(rank).merge(new_sorted_block)
                new_sorted_block.clear()
                new_sorted_block = next_sorted_block

            # Clear tail.
            self._tail_block.clear()

            # Clear merged blocks.
            for sorted_block in self._sorted_blocks[:rank + 1]:
                sorted_block.clear()

            # Assign new sorted block.
            self._sorted_blocks[rank] = new_sorted_block

        # Update metadata.
        self._save_meta()

    def _get_sorted_block(self, rank):
        while rank >= len(self._sorted_blocks):
            self._sorted_blocks.append(CommitGraphBlockSorted(rank, self._root_path))
        return self._sorted_blocks[rank]

    def _save_meta(self):
        with open(self._meta_path(), "w") as f:
            meta = {}
            meta["sorted_blocks"] = [
                sorted_block.to_dict() for sorted_block in self._sorted_blocks
            ]
            meta["tail_block"] = self._tail_block.to_dict()
            json.dump(meta, f)

    def _load_meta(self):
        with open(self._meta_path(), "r") as f:
            meta = json.load(f)
            self._sorted_blocks = [
                CommitGraphBlockSorted.from_dict(d, self._root_path)
                for d in meta["sorted_blocks"]
            ]
            self._tail_block = CommitGraphBlockTail.from_dict(
                meta["tail_block"], self._root_path
            )

    def _meta_path(self):
        return os.path.join(self._root_path, "meta.json")


class InMemoryCommitGraphWalker(CommitInfoIterator):

    def __init__(self, graph: InMemoryCommitGraphStore, commit_id: CommitId):
        super().__init__()
        self._graph = graph
        self._commit_id_queue: Set[CommitId] = set()
        self._visited_id: Set[CommitId] = set()
        if commit_id in self._graph._infos:
            self._commit_id_queue.add(commit_id)

    def __iter__(self) -> CommitInfoIterator:
        return self

    def __next__(self) -> CommitInfo:
        if len(self._commit_id_queue) == 0:
            raise StopIteration
        current_commit_id = self._commit_id_queue.pop()
        for commit_id in self._graph._edge_lists[current_commit_id]:
            if commit_id in self._graph._infos and commit_id not in self._visited_id:
                self._commit_id_queue.add(commit_id)
                self._visited_id.add(commit_id)
        return self._graph._infos[current_commit_id]


class InMemoryCommitGraphStore:

    def __init__(self) -> None:
        self._edge_lists: Dict[CommitId, List[CommitId]] = {}
        self._infos: Dict[CommitId, CommitInfo] = {}

    def begin_read(self, commit_id: CommitId) -> CommitInfoIterator:
        return InMemoryCommitGraphWalker(self, commit_id)

    def insert(self, commit_id: CommitId, parent_id: CommitId, commit_info: CommitInfo):
        self._edge_lists.setdefault(commit_id, []).append(parent_id)
        self._infos[commit_id] = commit_info


class KishuCommitGraph:

    def __init__(self, store: Union[InMemoryCommitGraphStore, CommitGraphStore]):
        self._store = store
        self._current_commit_id: CommitId = ABSOLUTE_PAST

    @staticmethod
    def new_in_memory() -> KishuCommitGraph:
        return KishuCommitGraph(InMemoryCommitGraphStore())

    @staticmethod
    def new_on_file(root_path: str) -> KishuCommitGraph:
        return KishuCommitGraph(CommitGraphStore(root_path))

    def list_history(self, commit_id: Optional[CommitId] = None) -> List[CommitInfo]:
        """
        Lists past commit(s) leading to the given commit.
        """
        if commit_id is None:
            commit_id = self._current_commit_id
        return list(self._store.begin_read(commit_id))

    def step(self, commit_id: CommitId) -> None:
        """
        Steps forward to the commit, associating the current commit as its past.
        """
        self._store.insert(
            commit_id,
            self._current_commit_id,
            CommitInfo(commit_id, self._current_commit_id),
        )
        self._current_commit_id = commit_id

    def jump(self, commit_id: CommitId) -> None:
        """
        Jumps to the given commit without associating the current commit.

        Associate with ABSOLUTE_PAST if the commit not exist before (first time seeing).
        """
        commit_info = next(self._store.begin_read(commit_id), None)
        if commit_info is None:
            self._store.insert(
                commit_id,
                ABSOLUTE_PAST,
                CommitInfo(commit_id, ABSOLUTE_PAST),
            )
        self._current_commit_id = commit_id


"""
Example usage:

    import time
    prefix = str((int(time.time_ns()) // 1000) % 1000)
    print(f"Prefix= {prefix}")

    # graph = KishuCommitGraph.new_in_memory()
    graph = KishuCommitGraph.new_on_file("/tmp/kishu/commit_graph")
    print(graph.list_history())

    graph.step(f"{prefix}_1")
    graph.step(f"{prefix}_2")
    graph.step(f"{prefix}_3")
    print(graph.list_history())

    graph.step(f"{prefix}_4")
    graph.step(f"{prefix}_5")
    print(graph.list_history())

    graph.jump(f"{prefix}_3")
    print(graph.list_history())
    print(graph.list_history(f"{prefix}_5"))

    graph.step(f"{prefix}_3_1")
    graph.step(f"{prefix}_3_2")
    graph.step(f"{prefix}_3_3")
    graph.step(f"{prefix}_3_4")
    print(graph.list_history())

    graph.jump(f"{prefix}_A")
    print(graph.list_history())

    graph.step(f"{prefix}_A_A")
    graph.step(f"{prefix}_A_B")
    print(graph.list_history())
    print(graph.list_history(f"{prefix}_5"))
"""

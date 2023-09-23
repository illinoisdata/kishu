import pytest

from kishu.commit_graph import (
    NODE_SIZE,
    UNSET_POSITION,
    CommitNodeInfo,
    CommitNode,
    KishuCommitGraph,
)


class TestCommitNode:

    @pytest.mark.parametrize(
        "commit_id,parent_id,position,parent_position",
        [
            ["1", "0", (0, 1), (0, 0)],
            ["1030", "1001", (0, 1), (1, 20)],
            ["40000", "1001", (0, 1), (200, 2000)],
            ["123456789", "123456789", (100, 1000), (200, 2000)],
        ],
    )
    def test_common(self, commit_id, parent_id, position, parent_position):
        """
        Tests all methods in CommitNode.
        """
        info = CommitNodeInfo(commit_id, parent_id)
        node = CommitNode(info)
        assert node.commit_id() == commit_id
        assert node.parent_id() == parent_id
        assert node.info() == info
        assert node.position() == UNSET_POSITION
        assert node.parent_position() == UNSET_POSITION

        # Tests before-after position assignments
        node.set_position(position)
        assert node.position() == position
        assert node.parent_position() == UNSET_POSITION

        node.set_parent_position(parent_position)
        assert node.position() == position
        assert node.parent_position() == parent_position

        # Tests serialization and deserialization.
        node_bytes = node.serialize()
        assert len(node_bytes) == NODE_SIZE

        new_node = CommitNode.deserialize(node_bytes)
        assert new_node.commit_id() == commit_id
        assert new_node.parent_id() == parent_id
        assert new_node.info() == info
        assert new_node.position() == position
        assert new_node.parent_position() == parent_position

    def test_too_large(self):
        large_id = "large_commit_" * NODE_SIZE
        node = CommitNode(CommitNodeInfo(large_id, ""))
        with pytest.raises(ValueError, match=r"CommitNode .* is too large (.* > .*)"):
            node.serialize()  # Expect fail


class TestKishuCommitGraph:

    @pytest.mark.parametrize(
        "mode",
        [
            "in_memory",
            "on_file",
        ],
    )
    def test_common(self, tmp_path, mode):
        if mode == "in_memory":
            graph = KishuCommitGraph.new_in_memory()
        elif mode == "on_file":
            graph = KishuCommitGraph.new_on_file(str(tmp_path))
        else:
            raise ValueError(f"Invalid mode= {mode}")
        assert graph.list_history() == []

        graph.step("1")
        graph.step("2")
        graph.step("3")
        assert graph.list_history() == [
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.head() == "3"

        graph.step("4")
        graph.step("5")
        assert graph.list_history() == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.head() == "5"

        graph.jump("3")
        assert graph.list_history() == [
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.head() == "3"

        graph.step("3_1")
        graph.step("3_2")
        graph.step("3_3")
        graph.step("3_4")
        assert graph.list_history() == [
            CommitNodeInfo("3_4", "3_3"),
            CommitNodeInfo("3_3", "3_2"),
            CommitNodeInfo("3_2", "3_1"),
            CommitNodeInfo("3_1", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.head() == "3_4"

        # Jumps to non-existent commit, creating a new commit from empty state.
        graph.jump("A")
        assert graph.list_history() == [
            CommitNodeInfo("A", "")
        ]
        assert graph.head() == "A"

        graph.step("A_A")
        graph.step("A_B")
        assert graph.list_history() == [
            CommitNodeInfo("A_B", "A_A"),
            CommitNodeInfo("A_A", "A"),
            CommitNodeInfo("A", "")
        ]
        assert graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.head() == "A_B"

    def test_persist_on_file_after_reload(self, tmp_path):
        graph = KishuCommitGraph.new_on_file(str(tmp_path))
        assert graph.list_history() == []

        graph.step("1")
        graph.step("2")
        graph.step("3")
        graph.step("4")
        graph.step("5")
        graph.jump("3")
        graph.step("3_1")
        graph.step("3_2")
        graph.step("3_3")
        graph.step("3_4")
        graph.jump("A")
        graph.step("A_A")
        graph.step("A_B")

        del graph

        # Create new graph. This should load existing commit graph.

        graph = KishuCommitGraph.new_on_file(str(tmp_path))
        assert graph.list_history("3") == [
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.list_history("3") == [
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.list_history("3_4") == [
            CommitNodeInfo("3_4", "3_3"),
            CommitNodeInfo("3_3", "3_2"),
            CommitNodeInfo("3_2", "3_1"),
            CommitNodeInfo("3_1", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.list_history("A") == [
            CommitNodeInfo("A", "")
        ]

        assert graph.list_history("A_B") == [
            CommitNodeInfo("A_B", "A_A"),
            CommitNodeInfo("A_A", "A"),
            CommitNodeInfo("A", "")
        ]
        assert graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", "")
        ]
        assert graph.head() == "A_B"

    @pytest.mark.parametrize(
        "mode",
        [
            "in_memory",
            "on_file",
        ],
    )
    def test_many_steps(self, tmp_path, mode):
        if mode == "in_memory":
            graph = KishuCommitGraph.new_in_memory()
        elif mode == "on_file":
            graph = KishuCommitGraph.new_on_file(str(tmp_path))
        else:
            raise ValueError(f"Invalid mode= {mode}")

        NUM_STEP = 10000
        for idx in range(NUM_STEP):
            graph.step(str(idx))

        assert len(graph.list_history(str(NUM_STEP - 1))) == NUM_STEP

        # Test persistence for file-based store.
        if mode == "on_file":
            del graph
            graph = KishuCommitGraph.new_on_file(str(tmp_path))
            assert len(graph.list_history(str(NUM_STEP - 1))) == NUM_STEP

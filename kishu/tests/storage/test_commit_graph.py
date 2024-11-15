import pytest

from kishu.storage.commit_graph import ABSOLUTE_PAST, CommitNodeInfo, KishuCommitGraph
from kishu.storage.path import KishuPath


class TestCommitNodeInfo:

    def test_equality(self):
        """Test equality between two CommitNodeInfo objects."""
        commit1 = CommitNodeInfo(commit_id="c1", parent_id="p1")
        commit2 = CommitNodeInfo(commit_id="c1", parent_id="p1")

        assert commit1 == commit2, "CommitNodeInfo objects with the same commit_id and parent_id should be equal"

    def test_inequality_different_commit_id(self):
        """Test inequality when commit_ids are different."""
        commit1 = CommitNodeInfo(commit_id="c1", parent_id="p1")
        commit2 = CommitNodeInfo(commit_id="c2", parent_id="p1")

        assert commit1 != commit2, "CommitNodeInfo objects with different commit_ids should not be equal"

    def test_inequality_different_parent_id(self):
        """Test inequality when parent_ids are different."""
        commit1 = CommitNodeInfo(commit_id="c1", parent_id="p1")
        commit2 = CommitNodeInfo(commit_id="c1", parent_id="p2")

        assert commit1 != commit2, "CommitNodeInfo objects with different parent_ids should not be equal"

    def test_inequality_different_type(self):
        """Test inequality when compared to a different type."""
        commit1 = CommitNodeInfo(commit_id="c1", parent_id="p1")
        not_commit = "Not a CommitNodeInfo object"

        assert commit1 != not_commit, "CommitNodeInfo should not be equal to an object of a different type"

    def test_repr(self):
        """Test the __repr__ method of CommitNodeInfo."""
        commit = CommitNodeInfo(commit_id="c1", parent_id="p1")

        expected_repr = 'CommitNodeInfo("c1", "p1")'
        assert repr(commit) == expected_repr, f"Expected __repr__ to be {expected_repr}, but got {repr(commit)}"

    def test_str(self):
        """Test the __str__ method of CommitNodeInfo."""
        commit = CommitNodeInfo(commit_id="c1", parent_id="p1")

        expected_str = "Commit(c1)"
        assert str(commit) == expected_str, f"Expected __str__ to be {expected_str}, but got {str(commit)}"


class TestKishuCommitGraph:

    @pytest.fixture
    def database_path(self, nb_simple_path):
        return KishuPath.database_path(nb_simple_path)

    @pytest.fixture
    def graph_name(self):
        return "test_graph"

    @pytest.fixture
    def kishu_graph(self, database_path, graph_name):
        """Fixture for initializing a KishuBranch instance."""
        kishu_graph = KishuCommitGraph(database_path, graph_name)
        kishu_graph.init_database()
        yield kishu_graph
        kishu_graph.drop_database()

    def test_common(self, kishu_graph):
        """Test stepping and jumpping through commit graph.

        The commit graph looks like:

             |-- 1 -- 2 -- 3 -- 4 -- 5
             |             |
        ~ -- +             | -- 3_1 -- 3_2 -- 3_3 -- 3_4
             |
             |-- A -- A_A -- A_B
        """
        assert kishu_graph.list_history() == []

        kishu_graph.step("1")
        kishu_graph.step("2")
        kishu_graph.step("3")
        assert kishu_graph.get_commit() == CommitNodeInfo("3", "2")
        assert kishu_graph.get_commit("3") == CommitNodeInfo("3", "2")
        assert kishu_graph.get_commit("non_existent_commit_id") is None
        assert kishu_graph.list_history() == [CommitNodeInfo("3", "2"), CommitNodeInfo("2", "1"), CommitNodeInfo("1", "")]
        assert kishu_graph.head() == "3"

        kishu_graph.step("4")
        kishu_graph.step("5")
        assert kishu_graph.list_history() == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.head() == "5"

        kishu_graph.jump("3")
        assert kishu_graph.list_history() == [CommitNodeInfo("3", "2"), CommitNodeInfo("2", "1"), CommitNodeInfo("1", "")]
        assert kishu_graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.head() == "3"

        kishu_graph.step("3_1")
        kishu_graph.step("3_2")
        kishu_graph.step("3_3")
        kishu_graph.step("3_4")
        assert kishu_graph.list_history() == [
            CommitNodeInfo("3_4", "3_3"),
            CommitNodeInfo("3_3", "3_2"),
            CommitNodeInfo("3_2", "3_1"),
            CommitNodeInfo("3_1", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.head() == "3_4"

        # Jumps to non-existent commit, creating a new commit from empty state.
        kishu_graph.jump("A")
        assert kishu_graph.list_history() == [CommitNodeInfo("A", "")]
        assert kishu_graph.head() == "A"

        kishu_graph.step("A_A")
        kishu_graph.step("A_B")
        assert kishu_graph.list_history() == [
            CommitNodeInfo("A_B", "A_A"),
            CommitNodeInfo("A_A", "A"),
            CommitNodeInfo("A", ""),
        ]
        assert kishu_graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.list_ancestor_commit_ids() == ["A_B", "A_A", "A"]
        assert kishu_graph.list_ancestor_commit_ids("5") == ["5", "4", "3", "2", "1"]
        assert kishu_graph.head() == "A_B"

        # Test listing all history.
        assert set(kishu_graph.list_all_history()) == {
            CommitNodeInfo("1", ""),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("3_1", "3"),
            CommitNodeInfo("3_2", "3_1"),
            CommitNodeInfo("3_3", "3_2"),
            CommitNodeInfo("3_4", "3_3"),
            CommitNodeInfo("A", ""),
            CommitNodeInfo("A_A", "A"),
            CommitNodeInfo("A_B", "A_A"),
        }

    def test_persist_on_file_after_reload(self, kishu_graph, database_path, graph_name):
        """Test persistence by creating a graph, deleting the graph store and reconstructing the store.

        The commit graph looks like:

             |-- 1 -- 2 -- 3 -- 4 -- 5
             |             |
        ~ -- +             | -- 3_1 -- 3_2 -- 3_3 -- 3_4
             |
             |-- A -- A_A -- A_B
        """
        assert kishu_graph.list_history() == []

        kishu_graph.step("1")
        kishu_graph.step("2")
        kishu_graph.step("3")
        kishu_graph.step("4")
        kishu_graph.step("5")
        kishu_graph.jump("3")
        kishu_graph.step("3_1")
        kishu_graph.step("3_2")
        kishu_graph.step("3_3")
        kishu_graph.step("3_4")
        kishu_graph.jump("A")
        kishu_graph.step("A_A")
        kishu_graph.step("A_B")

        # Create new graph. This should load existing commit graph.

        del kishu_graph
        kishu_graph = KishuCommitGraph(database_path, graph_name)
        assert kishu_graph.get_commit() == CommitNodeInfo("A_B", "A_A")
        assert kishu_graph.get_commit("3") == CommitNodeInfo("3", "2")
        assert kishu_graph.get_commit("non_existent_commit_id") is None
        assert kishu_graph.list_history("3") == [CommitNodeInfo("3", "2"), CommitNodeInfo("2", "1"), CommitNodeInfo("1", "")]
        assert kishu_graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.list_history("3") == [CommitNodeInfo("3", "2"), CommitNodeInfo("2", "1"), CommitNodeInfo("1", "")]
        assert kishu_graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.list_history("3_4") == [
            CommitNodeInfo("3_4", "3_3"),
            CommitNodeInfo("3_3", "3_2"),
            CommitNodeInfo("3_2", "3_1"),
            CommitNodeInfo("3_1", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.list_history("A") == [CommitNodeInfo("A", "")]

        assert kishu_graph.list_history("A_B") == [
            CommitNodeInfo("A_B", "A_A"),
            CommitNodeInfo("A_A", "A"),
            CommitNodeInfo("A", ""),
        ]
        assert kishu_graph.list_history("5") == [
            CommitNodeInfo("5", "4"),
            CommitNodeInfo("4", "3"),
            CommitNodeInfo("3", "2"),
            CommitNodeInfo("2", "1"),
            CommitNodeInfo("1", ""),
        ]
        assert kishu_graph.head() == "A_B"

    def test_lowest_common_ancestor(self, kishu_graph, database_path, graph_name):
        """
        Tests the lowest commit ancestor algorithm.

        The commit graph looks like:

             |-- 1 -- 2 -- 3 -- 4 -- 5
             |             |
        ~ -- +             | -- 3_1 -- 3_2 -- 3_3 -- 3_4
             |
             |-- A -- A_A -- A_B
        """
        assert kishu_graph.list_history() == []

        kishu_graph.step("1")
        kishu_graph.step("2")
        kishu_graph.step("3")
        kishu_graph.step("4")
        kishu_graph.step("5")
        kishu_graph.jump("3")
        kishu_graph.step("3_1")
        kishu_graph.step("3_2")
        kishu_graph.step("3_3")
        kishu_graph.step("3_4")
        kishu_graph.jump("A")
        kishu_graph.step("A_A")
        kishu_graph.step("A_B")

        # 5 and 3_4 are on two different branches.
        assert kishu_graph.get_lowest_common_ancestor_id("5", "3_4") == "3"

        # LCA of ancestor and descendant returns the ancestor.
        assert kishu_graph.get_lowest_common_ancestor_id("5", "3") == "3"

        # LCA of 2 identical commits returns the commit(s).
        assert kishu_graph.get_lowest_common_ancestor_id("2", "2") == "2"

        # LCA of 2 commits with no common ancestor returns ABSOLUTE_PAST.
        assert kishu_graph.get_lowest_common_ancestor_id("A", "2") == ABSOLUTE_PAST

    def test_many_steps(self, kishu_graph, database_path, graph_name):
        """Test persistence after many steps."""
        NUM_STEP = 1000
        for idx in range(NUM_STEP):
            kishu_graph.step(str(idx))

        assert len(kishu_graph.list_history(str(NUM_STEP - 1))) == NUM_STEP

        # Test persistence.
        del kishu_graph
        kishu_graph = KishuCommitGraph(database_path, graph_name)
        assert len(kishu_graph.list_history(str(NUM_STEP - 1))) == NUM_STEP

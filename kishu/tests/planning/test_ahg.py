import pytest

from kishu.jupyter.namespace import Namespace
from kishu.planning.ahg import AHG, AHGUpdateInfo
from kishu.storage.commit_graph import ABSOLUTE_PAST
from kishu.storage.disk_ahg import KishuDiskAHG
from kishu.storage.path import KishuPath


class TestDiskAHG:
    @pytest.fixture
    def db_path_name(self, nb_simple_path):
        return KishuPath.database_path(nb_simple_path)

    @pytest.fixture
    def kishu_disk_ahg(self, db_path_name):
        """Fixture for initializing a KishuBranch instance."""
        kishu_disk_ahg = KishuDiskAHG(db_path_name)
        kishu_disk_ahg.init_database()
        yield kishu_disk_ahg
        kishu_disk_ahg.drop_database()

    def test_update_graph(self, kishu_disk_ahg):
        ahg = AHG(kishu_disk_ahg)

        namespace = Namespace({"x": 1, "y": 2})
        # x and y are created
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id=ABSOLUTE_PAST,
                commit_id="1:1",
                user_ns=namespace,
                version=1,
                cell_runtime_s=1.0,
                current_variables={"x", "y"},
            )
        )

        # Check CE and VS counts are correct
        assert len(ahg.get_all_variable_snapshots()) == 2  # x and y
        assert len(ahg.get_all_cell_executions()) == 1  # 1 cell

        # Check links are correct
        ce1 = ahg.get_ce_by_cell_num(1)
        assert set(vs.name for vs in ahg.get_ce_output_vses(ce1)) == {frozenset("x"), frozenset("y")}
        assert set(ahg.get_vs_input_ce(vs).cell_num for vs in ahg.get_ce_output_vses(ce1)) == {1}

        # Check active VSes are correct
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:1")) == {frozenset("x"), frozenset("y")}
        assert ahg.get_active_variable_names("1:1") == {"x", "y"}

        # x is read and modified, z is created, y is deleted
        namespace["x"] = 3
        namespace["z"] = 5
        del namespace["y"]
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id="1:1",
                commit_id="1:2",
                user_ns=namespace,
                version=2,
                cell_runtime_s=1.0,
                accessed_variables={"x"},
                current_variables={"x", "z"},
                modified_variables={"x"},
                deleted_variables={"y"},
            )
        )

        # Check CE and VS counts are correct
        assert len(ahg.get_all_variable_snapshots()) == 5  # 2 versions of x + 2 versions of y + 1 version of z
        assert len(ahg.get_all_cell_executions()) == 2  # 2 cells

        # Check links are correct
        ce2 = ahg.get_ce_by_cell_num(2)
        assert set(vs.name for vs in ahg.get_ce_input_vses(ce2)) == {frozenset("x")}
        assert set(vs.name for vs in ahg.get_ce_output_vses(ce2)) == {frozenset("x"), frozenset("y"), frozenset("z")}

        # Check active VSes are correct
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:2")) == {frozenset("x"), frozenset("z")}
        assert ahg.get_active_variable_names("1:2") == {"x", "z"}

    def test_from_db(self, kishu_disk_ahg):
        # First cell is untracked and creates variable a with a=3
        ns_with_existing_cells = Namespace({"In": ["a=3"], "a": 3})
        ahg = AHG.from_db(kishu_disk_ahg, ns_with_existing_cells.ipython_in())

        ns_with_existing_cells["b"] = 4

        # second cell creates b with b=4.
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id=ABSOLUTE_PAST,
                commit_id="1:1",
                user_ns=ns_with_existing_cells,
                version=1,
                cell="b=4",
                cell_runtime_s=1.0,
                current_variables={"a", "b"},
            )
        )

        assert len(ahg.get_all_variable_snapshots()) == 2  # x, y
        assert len(ahg.get_all_cell_executions()) == 1  # 1 cell
        ce1 = ahg.get_ce_by_cell_num(1)
        assert ce1.cell == "a=3\nb=4"  # The untracked cell and the second cell are concatenated

        ns_with_existing_cells["c"] = 5

        # third cell creates c with c=4.
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id="1:1",
                commit_id="1:2",
                user_ns=ns_with_existing_cells,
                version=2,
                cell="c=5",
                cell_runtime_s=1.0,
                current_variables={"a", "b", "c"},
            )
        )

        assert len(ahg.get_all_variable_snapshots()) == 3  # x, y, z
        assert len(ahg.get_all_cell_executions()) == 2  # 2 cells
        ce2 = ahg.get_ce_by_cell_num(2)
        assert ce2.cell == "c=5"  # The third cell is unaltered.

    def test_update_graph_with_connected_components(self, kishu_disk_ahg):
        """
        Connected components:
        a---b---c  d---e  f
        """
        ahg = AHG(kishu_disk_ahg)

        ls_abc = []
        ls_de = []
        ls_f = []
        namespace = Namespace({"a": ls_abc, "b": ls_abc, "c": ls_abc, "d": ls_de, "e": ls_de, "f": ls_f})

        current_variables = {"a", "b", "c", "d", "e", "f"}
        linked_variable_pairs = [("a", "b"), ("b", "c"), ("d", "e")]
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id=ABSOLUTE_PAST,
                commit_id="1:1",
                user_ns=namespace,
                version=1,
                cell_runtime_s=1.0,
                current_variables=current_variables,
                linked_variable_pairs=linked_variable_pairs,
            )
        )

        # Check CE and VS counts are correct
        assert len(ahg.get_all_variable_snapshots()) == 3  # abc, de, f
        assert len(ahg.get_all_cell_executions()) == 1  # 1 cell

        # Check links are correct
        ce1 = ahg.get_ce_by_cell_num(1)
        assert set(vs.name for vs in ahg.get_ce_output_vses(ce1)) == {
            frozenset({"a", "b", "c"}),
            frozenset({"d", "e"}),
            frozenset("f"),
        }
        assert set(ahg.get_vs_input_ce(vs).cell_num for vs in ahg.get_ce_output_vses(ce1)) == {1}

        # 6 variables in total
        assert ahg.get_active_variable_names("1:1") == {"a", "b", "c", "d", "e", "f"}

    def test_create_vs_merge_connected_components(self, kishu_disk_ahg):
        """
        Connected components:
           a--d
          /|  |
         / |  |
        b--c  e--f
        """
        ahg = AHG(kishu_disk_ahg)

        ls_abcdef = []
        namespace = Namespace({"a": ls_abcdef, "b": ls_abcdef, "c": ls_abcdef, "d": ls_abcdef, "e": ls_abcdef, "f": ls_abcdef})

        current_variables = {"a", "b", "c", "d", "e", "f"}
        linked_variable_pairs = [("a", "b"), ("b", "c"), ("a", "c"), ("d", "e"), ("f", "e"), ("a", "f")]

        # components 'abc' and 'def' are merged.
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id=ABSOLUTE_PAST,
                commit_id="1:1",
                user_ns=namespace,
                version=1,
                cell_runtime_s=1.0,
                current_variables=current_variables,
                linked_variable_pairs=linked_variable_pairs,
            )
        )

        # 1 variable snapshot
        assert len(ahg.get_all_variable_snapshots()) == 1  # abcdef

        # 1 active VS
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:1")) == {frozenset({"a", "b", "c", "d", "e", "f"})}

        # 6 variables in total
        assert ahg.get_active_variable_names("1:1") == {"a", "b", "c", "d", "e", "f"}

    def test_create_vs_split_connected_component(self, kishu_disk_ahg):
        """
        Test modification detection for splitting comoponents:

        a---b

        split

        a   b
        """
        ahg = AHG(kishu_disk_ahg)

        current_variables = {"a", "b"}
        linked_variable_pairs = [("a", "b")]

        ls_ab = []
        namespace = Namespace({"a": ls_ab, "b": ls_ab})

        # 'ab' is in 1 component.
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id=ABSOLUTE_PAST,
                commit_id="1:1",
                user_ns=namespace,
                version=1,
                cell_runtime_s=1.0,
                current_variables=current_variables,
                linked_variable_pairs=linked_variable_pairs,
            )
        )

        # 1 variable snapshot
        assert len(ahg.get_all_variable_snapshots()) == 1  # ab

        # 1 active VS
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:1")) == {frozenset({"a", "b"})}

        # 'ab' is split into 2 components.
        namespace["b"] = []  # split b
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id="1:1",
                commit_id="1:2",
                user_ns=namespace,
                version=2,
                cell_runtime_s=1.0,
                current_variables=current_variables,
                modified_variables={"b"},
            )
        )

        # 3 VSes
        assert len(ahg.get_all_variable_snapshots()) == 3  # ab, a, b

        # 2 active variable snapshots. Even though 'a' was not modified directly, we still count
        # it as modified as b was split from it.
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:2")) == {frozenset("a"), frozenset("b")}

    def test_create_vs_modify_connected_component(self, kishu_disk_ahg):
        """
        Test modification detection for splitting comoponents:

        a---b   c

        split

        a   b---c
        """
        ahg = AHG(kishu_disk_ahg)

        current_variables = {"a", "b", "c"}
        linked_variable_pairs = [("a", "b")]

        ls_ab = []
        ls_c = []
        namespace = Namespace({"a": ls_ab, "b": ls_ab, "c": ls_c})

        # 2 components: 'ab' and 'c'.
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id=ABSOLUTE_PAST,
                commit_id="1:1",
                user_ns=namespace,
                version=1,
                cell_runtime_s=1.0,
                current_variables=current_variables,
                linked_variable_pairs=linked_variable_pairs,
            )
        )

        # 2 active variable snapshots: ab and c.
        assert len(ahg.get_all_variable_snapshots()) == 2

        # 2 connected components
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:1")) == {frozenset({"a", "b"}), frozenset("c")}

        # 'ab' is split into 2 components; 'bc' is merged.
        namespace["b"] = ls_c

        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id="1:1",
                commit_id="1:2",
                user_ns=namespace,
                version=2,
                cell_runtime_s=1.0,
                current_variables=current_variables,
                linked_variable_pairs=[("c", "b")],
                modified_variables={"b"},
            )
        )

        assert len(ahg.get_all_variable_snapshots()) == 4  # ab, c, a, bc

        # 2 connected components
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:2")) == {frozenset("a"), frozenset({"b", "c"})}

    def test_active_vses_different_commits(self, kishu_disk_ahg):
        ahg = AHG(kishu_disk_ahg)

        namespace = Namespace({"x": 1, "y": 2})
        # x and y are created
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id=ABSOLUTE_PAST,
                commit_id="1:1",
                user_ns=namespace,
                version=1,
                cell_runtime_s=1.0,
                current_variables={"x", "y"},
            )
        )

        # x is read and modified, z is created, y is deleted
        namespace["x"] = 3
        namespace["z"] = 5
        del namespace["y"]
        ahg.update_graph(
            AHGUpdateInfo(
                parent_commit_id="1:1",
                commit_id="1:2",
                user_ns=namespace,
                version=2,
                cell_runtime_s=1.0,
                accessed_variables={"x"},
                current_variables={"x", "z"},
                modified_variables={"x"},
                deleted_variables={"y"},
            )
        )

        # State of active VSes after 1nd cell execution: x and y are active
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:1")) == {frozenset("x"), frozenset("y")}

        # State of active VSes after 2st cell execution: x and z are active
        assert set(vs.name for vs in ahg.get_active_variable_snapshots("1:2")) == {frozenset("x"), frozenset("z")}

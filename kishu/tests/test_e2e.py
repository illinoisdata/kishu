import pytest

from tests.helpers.nbexec import KISHU_INIT_STR, NB_DIR

from kishu.commands import KishuCommand


@pytest.mark.parametrize(
    ("notebook_name", "cell_num_to_restore", "var_to_compare"),
    [
        ('numpy.ipynb', 4, "iris_X_train"),
        ('simple.ipynb', 4, "b")
    ]
)
def test_end_to_end_checkout(jupyter_server, notebook_name: str, cell_num_to_restore: int, var_to_compare: str):
    # Get the contents of the test notebook.
    contents = jupyter_server.get_notebook_contents(NB_DIR, notebook_name)
    assert cell_num_to_restore >= 1 and cell_num_to_restore <= len(contents) - 1

    # Start the notebook session.
    with jupyter_server.start_session(NB_DIR, notebook_name) as notebook_session:
        # Run the kishu init cell.
        notebook_session.run_code(KISHU_INIT_STR)

        # Run some notebook cells.
        for i in range(cell_num_to_restore):
            notebook_session.run_code(contents[i])

        # Get the variable value before checkout.
        var_value_before = notebook_session.run_code(f"print({var_to_compare})")

        # Run the rest of the notebook cells.
        for i in range(cell_num_to_restore, len(contents)):
            notebook_session.run_code(contents[i])

        # Get the notebook key of the session.
        list_result = KishuCommand.list()
        assert len(list_result.sessions) == 1
        assert list_result.sessions[0].notebook_path is not None
        assert list_result.sessions[0].notebook_path.split("/")[-1] == notebook_name
        notebook_key = list_result.sessions[0].notebook_key

        # Get commit id of commit which we want to restore
        log_result = KishuCommand.log_all(notebook_key)
        assert len(log_result.commit_graph) == len(contents) + 2  # all cells + init cell + print variable cell
        commit_id = log_result.commit_graph[cell_num_to_restore].commit_id

        # Restore to that commit
        KishuCommand.checkout(notebook_key, commit_id)

        # Get the variable value after checkout.
        var_value_after = notebook_session.run_code(f"print({var_to_compare})")
        assert var_value_before == var_value_after

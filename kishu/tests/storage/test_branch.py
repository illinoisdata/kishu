import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from kishu.exceptions import BranchConflictError, BranchNotFoundError
from kishu.storage.branch import KishuBranch
from kishu.storage.path import KishuPath


class TestBranch:

    @pytest.fixture
    def branch(self, nb_simple_path, tmp_path):
        """Fixture for initializing a KishuBranch instance."""
        branch = KishuBranch(KishuPath.database_path(nb_simple_path))
        branch.init_database()
        yield branch
        branch.drop_database()

    def test_init_database(self, branch):
        """Test that the database is initialized correctly."""
        con = sqlite3.connect(branch.database_path)
        cur = con.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cur.fetchall()]
        assert "branch" in tables
        assert "head_branch" in tables

    def test_get_head_no_head(self, branch):
        """Test getting the head branch when no head exists."""
        head = branch.get_head()
        assert head.branch_name is None
        assert head.commit_id is None

    def test_update_head_no_existing_head(self, branch):
        """Test updating head when no head exists."""
        # Ensure there's no head in the database
        head = branch.get_head()
        assert head.branch_name is None
        assert head.commit_id is None

        # Now update the head and check
        branch.update_head(branch_name="main", commit_id="commit1")
        head = branch.get_head()
        assert head.branch_name == "main"
        assert head.commit_id == "commit1"

    def test_update_head_with_existing_head(self, branch):
        """Test updating the head when a head already exists."""
        branch.update_head(branch_name="main", commit_id="commit1")
        branch.update_head(branch_name="dev", commit_id="commit2")
        head = branch.get_head()
        assert head.branch_name == "dev"
        assert head.commit_id == "commit2"

    def test_update_head_detach(self, branch):
        """Test updating the head in detach mode."""
        updated_head = branch.update_head(branch_name="main", commit_id="commit1", is_detach=True)
        assert updated_head.branch_name is None
        assert updated_head.commit_id == "commit1"

        head = branch.get_head()
        assert head.branch_name is None
        assert head.commit_id == "commit1"

    def test_upsert_branch(self, branch):
        """Test inserting or updating a branch."""
        branch.upsert_branch("main", "commit1")
        branches = branch.list_branch()
        assert len(branches) == 1
        assert branches[0].branch_name == "main"
        assert branches[0].commit_id == "commit1"

        # Update the branch
        branch.upsert_branch("main", "commit2")
        branches = branch.list_branch()
        assert len(branches) == 1
        assert branches[0].commit_id == "commit2"

    def test_list_branch(self, branch):
        """Test listing branches."""
        branch.upsert_branch("main", "commit1")
        branch.upsert_branch("dev", "commit2")
        branches = branch.list_branch()
        assert len(branches) == 2
        branch_names = {b.branch_name for b in branches}
        assert branch_names == {"main", "dev"}

    def test_get_branch(self, branch):
        """Test getting a branch by its name."""
        branch.upsert_branch("main", "commit1")
        result = branch.get_branch("main")
        assert len(result) == 1
        assert result[0].branch_name == "main"
        assert result[0].commit_id == "commit1"

    def test_branches_for_commit(self, branch):
        """Test getting branches for a specific commit."""
        branch.upsert_branch("main", "commit1")
        branch.upsert_branch("dev", "commit2")
        result = branch.branches_for_commit("commit1")
        assert len(result) == 1
        assert result[0].branch_name == "main"

    def test_branches_for_many_commits(self, branch):
        """Test getting branches for multiple commits."""
        branch.upsert_branch("main", "commit1")
        branch.upsert_branch("dev", "commit2")
        result = branch.branches_for_many_commits(["commit1", "commit2"])
        assert "commit1" in result
        assert "commit2" in result
        assert len(result["commit1"]) == 1
        assert result["commit1"][0].branch_name == "main"
        assert result["commit2"][0].branch_name == "dev"

    def test_delete_branch(self, branch):
        """Test deleting a branch."""
        branch.upsert_branch("main", "commit1")
        branch.delete_branch("main")
        branches = branch.list_branch()
        assert len(branches) == 0

    def test_delete_current_head_branch(self, branch):
        """Test that deleting the current head branch raises an error."""
        branch.upsert_branch("main", "commit1")
        branch.update_head(branch_name="main")
        with pytest.raises(BranchConflictError):
            branch.delete_branch("main")

    def test_rename_branch(self, branch):
        """Test renaming a branch."""
        branch.upsert_branch("main", "commit1")
        branch.rename_branch("main", "primary")
        branches = branch.list_branch()
        assert len(branches) == 1
        assert branches[0].branch_name == "primary"

    def test_rename_nonexistent_branch(self, branch):
        """Test renaming a branch that doesn't exist raises an error."""
        with pytest.raises(BranchNotFoundError):
            branch.rename_branch("nonexistent", "new_name")

    def test_rename_into_existing_branch(self, branch):
        """Test renaming a branch into an existing branch."""
        branch.upsert_branch("dev1", "commit1")
        branch.upsert_branch("dev2", "commit2")
        with pytest.raises(BranchConflictError):
            branch.rename_branch("dev2", "dev1")

    def test_rename_head_branch(self, branch):
        """Test renaming a branch into an existing branch."""
        branch.upsert_branch("dev", "commit1")
        branch.update_head(branch_name="dev", commit_id="commit1")
        head = branch.get_head()
        assert head.branch_name == "dev"
        assert head.commit_id == "commit1"

        # Renaming head branch should affect where head points to.
        branch.rename_branch("dev", "main")
        head = branch.get_head()
        assert head.branch_name == "main"
        assert head.commit_id == "commit1"

    def test_delete_nonexistent_branch(self, branch):
        """Test deleting a non-existent branch raises an error."""
        with pytest.raises(BranchNotFoundError):
            branch.delete_branch("nonexistent")

    def test_random_branch_name(self):
        """Test that random branch name generates a name."""
        with patch("kishu.storage.branch.BRANCH_NAME_ADJECTIVES", ["quick", "lazy"]), patch(
            "kishu.storage.branch.BRANCH_NAME_NOUNS", ["fox", "dog"]
        ):
            name = KishuBranch.random_branch_name()
            assert name in ["quick_fox", "quick_dog", "lazy_fox", "lazy_dog"]

    def test_sqlite3_operational_error_list_branch(self, branch):
        """Test OperationalError during list_branch."""
        with patch("sqlite3.connect") as mock_connect:
            mock_con = MagicMock()
            mock_connect.return_value = mock_con
            mock_cur = mock_con.cursor.return_value
            mock_cur.execute.side_effect = sqlite3.OperationalError()

            result = branch.list_branch()
            assert result == []  # Should return an empty list

    def test_sqlite3_operational_error_get_branch(self, branch):
        """Test OperationalError during get_branch."""
        with patch("sqlite3.connect") as mock_connect:
            mock_con = MagicMock()
            mock_connect.return_value = mock_con
            mock_cur = mock_con.cursor.return_value
            mock_cur.execute.side_effect = sqlite3.OperationalError()

            result = branch.get_branch("main")
            assert result == []  # Should return an empty list

    def test_sqlite3_operational_error_branches_for_commit(self, branch):
        """Test OperationalError during branches_for_commit."""
        with patch("sqlite3.connect") as mock_connect:
            mock_con = MagicMock()
            mock_connect.return_value = mock_con
            mock_cur = mock_con.cursor.return_value
            mock_cur.execute.side_effect = sqlite3.OperationalError()

            result = branch.branches_for_commit("commit1")
            assert result == []  # Should return an empty list

    def test_sqlite3_operational_error_branches_for_many_commits(self, branch):
        """Test OperationalError during branches_for_many_commits."""
        with patch("sqlite3.connect") as mock_connect:
            mock_con = MagicMock()
            mock_connect.return_value = mock_con
            mock_cur = mock_con.cursor.return_value
            mock_cur.execute.side_effect = sqlite3.OperationalError()

            result = branch.branches_for_many_commits(["commit1", "commit2"])
            assert result == {}  # Should return an empty dictionary

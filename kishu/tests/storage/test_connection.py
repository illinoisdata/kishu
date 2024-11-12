import sqlite3
from unittest.mock import patch

import pytest

from kishu.notebook_id import NotebookId
from kishu.storage.connection import CONNECTION_TABLE, KishuConnection
from kishu.storage.path import KishuPath


class TestKishuConnection:

    @pytest.fixture
    def notebook_id(self, nb_simple_path):
        """Fixture for a mock notebook_id object."""
        return NotebookId(
            key="test_key",
            path=nb_simple_path,
            kernel_id="test_kernel_1",
        )

    @pytest.fixture
    def connection(self, notebook_id):
        """Fixture for initializing a KishuConnection instance."""
        connection = KishuConnection(
            key=notebook_id.key(),
            path=notebook_id.path(),
            kernel_id=notebook_id.kernel_id(),
        )
        connection.init_database()
        yield connection
        connection.drop_database()

    def test_init_database(self, connection, notebook_id):
        """Test initializing the database."""
        # Check if the table is correctly created
        con = sqlite3.connect(KishuPath.database_path(notebook_id.path()))
        cur = con.cursor()
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{CONNECTION_TABLE}'")
        table_exists = cur.fetchone()
        con.close()

        assert table_exists is not None

    def test_drop_database(self, connection, notebook_id):
        """Test dropping the database."""
        connection.drop_database()

        # Verify that the table no longer exists
        con = sqlite3.connect(KishuPath.database_path(notebook_id.path()))
        cur = con.cursor()
        cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{CONNECTION_TABLE}'")
        table_exists = cur.fetchone()
        con.close()

        assert table_exists is None

    def test_record_connection(self, connection, notebook_id):
        """Test recording a connection and verifying it in the database."""
        connection.record_connection()

        # Verify the connection record
        conn_info = KishuConnection.try_retrieve_connection(notebook_id.path())

        assert conn_info is not None
        assert conn_info.kernel_id == notebook_id.kernel_id()
        assert conn_info.notebook_path == notebook_id.path()

    def test_try_retrieve_connection_none(self, notebook_id):
        """Test retrieving a connection when none exists in the database."""
        conn_info = KishuConnection.try_retrieve_connection(notebook_id.path())
        assert conn_info is None

    def test_try_retrieve_connection_no_record(self, connection, notebook_id):
        """Test retrieving a connection when none exists in the database."""
        conn_info = KishuConnection.try_retrieve_connection(notebook_id.path())
        assert conn_info is None

    def test_sqlite3_operational_error_init_database(self, connection, notebook_id):
        """Test sqlite3.OperationalError during init_database."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError):
            with pytest.raises(sqlite3.OperationalError):
                connection.init_database()

    def test_sqlite3_operational_error_drop_database(self, connection, notebook_id):
        """Test sqlite3.OperationalError during drop_database."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError):
            with pytest.raises(sqlite3.OperationalError):
                connection.drop_database()

    def test_sqlite3_operational_error_record_connection(self, connection, notebook_id):
        """Test sqlite3.OperationalError during record_connection."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError):
            with pytest.raises(sqlite3.OperationalError):
                connection.record_connection()

    def test_sqlite3_operational_error_try_retrieve_connection(self, notebook_id):
        """Test sqlite3.OperationalError during try_retrieve_connection."""
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError):
            with pytest.raises(sqlite3.OperationalError):
                KishuConnection.try_retrieve_connection(notebook_id.path())

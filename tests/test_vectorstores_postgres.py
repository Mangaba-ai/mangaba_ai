"""Testes para PostgresVectorStore"""

import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.unit


def _make_mock_pg_connection():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = {"count": 0}
    return conn, cursor


class TestPostgresVectorStoreInit:
    def test_raises_import_error_when_psycopg_unavailable(self):
        import importlib
        import sys

        psycopg_mod = sys.modules.get("psycopg")
        sys.modules["psycopg"] = None

        try:
            from mangaba.vectorstores import postgres as pg_vs

            importlib.reload(pg_vs)

            with pytest.raises(ImportError, match="psycopg package is required"):
                pg_vs.PostgresVectorStore(url="postgresql://localhost/test")
        finally:
            if psycopg_mod is not None:
                sys.modules["psycopg"] = psycopg_mod
            importlib.reload(pg_vs)

    def test_raises_error_without_url(self):
        mock_conn, _ = _make_mock_pg_connection()

        with patch("mangaba.vectorstores.postgres.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn

            from mangaba.vectorstores.postgres import PostgresVectorStore

            with pytest.raises(
                ValueError, match="PostgreSQL connection URL is required"
            ):
                PostgresVectorStore()

    def test_creates_table_on_init(self):
        mock_conn, mock_cursor = _make_mock_pg_connection()

        with patch("mangaba.vectorstores.postgres.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            mock_psycopg.rows.dict_row = MagicMock()

            from mangaba.vectorstores.postgres import PostgresVectorStore

            PostgresVectorStore(
                url="postgresql://user:pass@localhost:5432/test",
                table_name="test_vectors",
                vector_dimensions=3,
            )

            assert mock_cursor.execute.call_count >= 3

    def test_uses_env_var_url(self, monkeypatch):
        mock_conn, _ = _make_mock_pg_connection()

        with patch("mangaba.vectorstores.postgres.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            mock_psycopg.rows.dict_row = MagicMock()

            monkeypatch.setenv(
                "MANGABA_VECTORSTORE_URL", "postgresql://env:pass@envhost:5432/envdb"
            )

            from mangaba.vectorstores.postgres import PostgresVectorStore

            PostgresVectorStore()

            connect_call = mock_psycopg.connect.call_args
            assert connect_call[0][0] == "postgresql://env:pass@envhost:5432/envdb"

    def test_uses_database_url_env_var(self, monkeypatch):
        mock_conn, _ = _make_mock_pg_connection()

        with patch("mangaba.vectorstores.postgres.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            mock_psycopg.rows.dict_row = MagicMock()

            monkeypatch.setenv(
                "DATABASE_URL", "postgresql://fallback:pass@fallback:5432/fallback"
            )

            from mangaba.vectorstores.postgres import PostgresVectorStore

            PostgresVectorStore()

            connect_call = mock_psycopg.connect.call_args
            assert (
                connect_call[0][0]
                == "postgresql://fallback:pass@fallback:5432/fallback"
            )

    def test_url_param_takes_precedence_over_env(self, monkeypatch):
        mock_conn, _ = _make_mock_pg_connection()

        with patch("mangaba.vectorstores.postgres.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            mock_psycopg.rows.dict_row = MagicMock()

            monkeypatch.setenv(
                "DATABASE_URL", "postgresql://env:pass@envhost:5432/envdb"
            )

            from mangaba.vectorstores.postgres import PostgresVectorStore

            PostgresVectorStore(url="postgresql://explicit:pass@explicit:5432/explicit")

            connect_call = mock_psycopg.connect.call_args
            assert (
                connect_call[0][0]
                == "postgresql://explicit:pass@explicit:5432/explicit"
            )


@pytest.fixture
def postgres_store():
    mock_conn, mock_cursor = _make_mock_pg_connection()

    with patch("mangaba.vectorstores.postgres.psycopg") as mock_psycopg:
        mock_psycopg.connect.return_value = mock_conn
        mock_psycopg.rows.dict_row = MagicMock()

        from mangaba.vectorstores.postgres import PostgresVectorStore

        store = PostgresVectorStore(
            url="postgresql://user:pass@localhost:5432/test",
            table_name="test_vectors",
            vector_dimensions=3,
        )
        yield store, mock_conn, mock_cursor


class TestPostgresVectorStoreAdd:
    def test_add_stores_documents(self, postgres_store):
        store, mock_conn, mock_cursor = postgres_store
        texts = ["hello world", "foo bar"]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        metadatas = [{"source": "test"}, {"source": "test2"}]

        ids = store.add(texts, embeddings, metadatas)

        assert len(ids) == 2
        assert all(len(eid) == 12 for eid in ids)
        assert mock_conn.commit.called

    def test_add_without_metadatas(self, postgres_store):
        store, mock_conn, mock_cursor = postgres_store
        texts = ["hello"]
        embeddings = [[0.1, 0.2, 0.3]]

        ids = store.add(texts, embeddings)

        assert len(ids) == 1

    def test_add_generates_unique_ids(self, postgres_store):
        store, _, _ = postgres_store
        ids1 = store.add(["a"], [[0.1, 0.2, 0.3]])
        ids2 = store.add(["b"], [[0.4, 0.5, 0.6]])

        assert ids1[0] != ids2[0]


class TestPostgresVectorStoreSearch:
    def test_search_returns_results(self, postgres_store):
        store, mock_conn, mock_cursor = postgres_store
        mock_cursor.fetchall.return_value = [
            {
                "id": "abc123",
                "text": "hello world",
                "metadata": {"source": "test"},
                "score": 0.92,
            }
        ]

        results = store.search([0.1, 0.2, 0.3], top_k=3)

        assert len(results) == 1
        assert results[0]["content"] == "hello world"
        assert results[0]["score"] == pytest.approx(0.92)
        assert results[0]["metadata"] == {"source": "test"}

    def test_search_handles_empty_results(self, postgres_store):
        store, mock_conn, mock_cursor = postgres_store
        mock_cursor.fetchall.return_value = []

        results = store.search([0.1, 0.2, 0.3])

        assert results == []

    def test_search_handles_non_dict_metadata(self, postgres_store):
        store, mock_conn, mock_cursor = postgres_store
        mock_cursor.fetchall.return_value = [
            {
                "id": "abc123",
                "text": "test",
                "metadata": "string_metadata",
                "score": 0.5,
            }
        ]

        results = store.search([0.1, 0.2, 0.3])

        assert results[0]["metadata"] == {}


class TestPostgresVectorStoreDelete:
    def test_delete_removes_documents(self, postgres_store):
        store, mock_conn, _ = postgres_store
        store.delete(["id1", "id2"])

        mock_conn.commit.assert_called()

    def test_delete_empty_list(self, postgres_store):
        store, mock_conn, _ = postgres_store
        store.delete([])

        mock_conn.commit.assert_called()


class TestPostgresVectorStoreClear:
    def test_clear_removes_all(self, postgres_store):
        store, mock_conn, _ = postgres_store
        store.clear()

        mock_conn.commit.assert_called()


class TestPostgresVectorStoreCount:
    def test_count_returns_total(self, postgres_store):
        store, mock_conn, mock_cursor = postgres_store
        mock_cursor.fetchone.return_value = {"count": 42}

        assert store.count == 42

    def test_count_zero(self, postgres_store):
        store, mock_conn, mock_cursor = postgres_store
        mock_cursor.fetchone.return_value = {"count": 0}

        assert store.count == 0


class TestPostgresVectorStoreClose:
    def test_close_closes_connection(self, postgres_store):
        store, mock_conn, _ = postgres_store
        store.close()
        mock_conn.close.assert_called_once()

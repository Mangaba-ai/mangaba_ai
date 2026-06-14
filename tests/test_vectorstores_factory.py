"""Testes para fábrica de armazenamento de vetores"""

import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.unit


class TestVectorStoreFactory:
    def test_create_inmemory_store(self):
        from mangaba.vectorstores.factory import create_vectorstore
        from mangaba.vectorstores.in_memory import InMemoryVectorStore

        store = create_vectorstore("inmemory")
        assert isinstance(store, InMemoryVectorStore)

    def test_create_inmemory_case_insensitive(self):
        from mangaba.vectorstores.factory import create_vectorstore

        store = create_vectorstore("INMEMORY")
        from mangaba.vectorstores.in_memory import InMemoryVectorStore

        assert isinstance(store, InMemoryVectorStore)

    def test_get_supported_stores_includes_inmemory(self):
        from mangaba.vectorstores.factory import get_supported_stores

        stores = get_supported_stores()
        assert "inmemory" in stores

    def test_unsupported_store_type(self):
        from mangaba.vectorstores.factory import create_vectorstore

        with pytest.raises(ValueError, match="Unsupported vector store type"):
            create_vectorstore("nonexistent")

    def test_register_custom_store(self):
        from mangaba.vectorstores.factory import (
            register_store,
            create_vectorstore,
            STORE_REGISTRY,
        )

        class DummyStore:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        try:
            register_store("dummy", DummyStore)
            store = create_vectorstore("dummy", foo="bar")
            assert isinstance(store, DummyStore)
            assert store.kwargs["foo"] == "bar"
        finally:
            STORE_REGISTRY.pop("dummy", None)

    def test_redis_registered_when_available(self):
        from mangaba.vectorstores.factory import get_supported_stores

        stores = get_supported_stores()
        assert "redis" in stores

    def test_postgres_registered_when_available(self):
        from mangaba.vectorstores.factory import get_supported_stores

        stores = get_supported_stores()
        assert "postgres" in stores

    def test_create_redis_with_kwargs(self):
        from mangaba.vectorstores.factory import create_vectorstore, STORE_REGISTRY

        mock_client = MagicMock()
        mock_ft = MagicMock()
        mock_client.ft.return_value = mock_ft
        mock_ft.info.return_value = {"index_name": "test"}

        mock_fields = (
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        with (
            patch("mangaba.vectorstores.redis.redis") as mock_redis,
            patch("mangaba.vectorstores.redis.REDIS_AVAILABLE", True),
            patch(
                "mangaba.vectorstores.redis._get_search_classes",
                return_value=mock_fields,
            ),
        ):
            mock_redis.Redis.from_url.return_value = mock_client

            # Re-register to ensure we get the current class identity
            from mangaba.vectorstores.redis import RedisVectorStore

            STORE_REGISTRY["redis"] = RedisVectorStore

            store = create_vectorstore(
                "redis",
                url="redis://localhost:6379",
                index_name="factory_test",
                vector_dimensions=768,
            )

            assert isinstance(store, RedisVectorStore)
            assert store._index_name == "factory_test"
            assert store._vector_dimensions == 768

    def test_create_postgres_with_kwargs(self):
        from mangaba.vectorstores.factory import create_vectorstore, STORE_REGISTRY
        from mangaba.vectorstores.postgres import PostgresVectorStore

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with (
            patch("mangaba.vectorstores.postgres.psycopg") as mock_psycopg,
            patch("mangaba.vectorstores.postgres.POSTGRES_AVAILABLE", True),
        ):
            mock_psycopg.connect.return_value = mock_conn
            mock_psycopg.rows.dict_row.return_value = dict

            STORE_REGISTRY["postgres"] = PostgresVectorStore

            store = create_vectorstore(
                "postgres",
                url="postgresql://user:pass@localhost:5432/testdb",
                table_name="factory_table",
                vector_dimensions=512,
            )

            assert isinstance(store, PostgresVectorStore)
            assert store._table_name == "factory_table"
            assert store._vector_dimensions == 512

    def test_chroma_registered_when_available(self):
        from mangaba.vectorstores.factory import get_supported_stores
        from mangaba.vectorstores.chroma_db import CHROMA_AVAILABLE

        if CHROMA_AVAILABLE:
            stores = get_supported_stores()
            assert "chroma" in stores

    def test_sqlite_registered(self):
        from mangaba.vectorstores.factory import get_supported_stores

        stores = get_supported_stores()
        assert "sqlite" in stores

    def test_create_chroma_with_kwargs(self, tmp_path):
        from mangaba.vectorstores.factory import create_vectorstore, STORE_REGISTRY
        from mangaba.vectorstores.chroma_db import ChromaVectorStore

        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_collection.name = "test_collection"

        with (
            patch("mangaba.vectorstores.chroma_db.chromadb") as mock_chroma_module,
            patch("mangaba.vectorstores.chroma_db.CHROMA_AVAILABLE", True),
        ):
            mock_chroma_module.PersistentClient.return_value = mock_client

            STORE_REGISTRY["chroma"] = ChromaVectorStore

            chroma_path = tmp_path / "chroma_test"
            store = create_vectorstore(
                "chroma",
                path=str(chroma_path),
                collection_name="test_collection",
            )

            assert isinstance(store, ChromaVectorStore)
            assert store.collection.name == "test_collection"

    def test_create_sqlite_with_kwargs(self, tmp_path):
        from mangaba.vectorstores.factory import create_vectorstore, STORE_REGISTRY
        from mangaba.vectorstores.sqlite import SQLiteVectorStore

        db_path = tmp_path / "test.db"
        STORE_REGISTRY["sqlite"] = SQLiteVectorStore

        store = create_vectorstore(
            "sqlite",
            db_path=str(db_path),
        )

        assert isinstance(store, SQLiteVectorStore)

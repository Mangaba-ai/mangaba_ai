"""Testes para RedisVectorStore"""

import json
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.unit


def _make_mock_redis_client():
    client = MagicMock()
    ft_mock = MagicMock()
    client.ft.return_value = ft_mock
    ft_mock.info.return_value = {"index_name": "test"}
    return client


def _mock_search_classes():
    return (
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )


class TestRedisVectorStoreInit:
    def test_raises_import_error_when_redis_unavailable(self):
        import importlib
        import sys

        redis_mod = sys.modules.get("redis")
        sys.modules["redis"] = None

        try:
            from mangaba.vectorstores import redis as redis_vs

            importlib.reload(redis_vs)

            with pytest.raises(ImportError, match="redis package is required"):
                redis_vs.RedisVectorStore()
        finally:
            if redis_mod is not None:
                sys.modules["redis"] = redis_mod
            importlib.reload(redis_vs)

    def test_creates_index_on_init(self):
        mock_client = _make_mock_redis_client()
        mock_client.ft.return_value.info.side_effect = Exception("Index does not exist")

        with (
            patch("mangaba.vectorstores.redis.redis") as mock_redis,
            patch("mangaba.vectorstores.redis.REDIS_AVAILABLE", True),
            patch(
                "mangaba.vectorstores.redis._get_search_classes",
                side_effect=_mock_search_classes,
            ),
        ):
            mock_redis.Redis.from_url.return_value = mock_client

            from mangaba.vectorstores.redis import RedisVectorStore

            store = RedisVectorStore(
                url="redis://localhost:6379", index_name="test", vector_dimensions=3
            )

            mock_client.ft.return_value.create_index.assert_called_once()

    def test_skips_index_creation_if_exists(self):
        mock_client = _make_mock_redis_client()

        with (
            patch("mangaba.vectorstores.redis.redis") as mock_redis,
            patch("mangaba.vectorstores.redis.REDIS_AVAILABLE", True),
            patch(
                "mangaba.vectorstores.redis._get_search_classes",
                side_effect=_mock_search_classes,
            ),
        ):
            mock_redis.Redis.from_url.return_value = mock_client

            from mangaba.vectorstores.redis import RedisVectorStore

            RedisVectorStore(
                url="redis://localhost:6379", index_name="test", vector_dimensions=3
            )

            mock_client.ft.return_value.create_index.assert_not_called()

    def test_uses_env_var_url(self, monkeypatch):
        mock_client = _make_mock_redis_client()

        with (
            patch("mangaba.vectorstores.redis.redis") as mock_redis,
            patch("mangaba.vectorstores.redis.REDIS_AVAILABLE", True),
            patch(
                "mangaba.vectorstores.redis._get_search_classes",
                side_effect=_mock_search_classes,
            ),
        ):
            mock_redis.Redis.from_url.return_value = mock_client

            monkeypatch.setenv("MANGABA_REDIS_URL", "redis://custom-host:9999")

            from mangaba.vectorstores.redis import RedisVectorStore

            RedisVectorStore()

            call_args = mock_redis.Redis.from_url.call_args
            assert call_args[0][0] == "redis://custom-host:9999"

    def test_defaults_to_localhost_when_no_url(self):
        mock_client = _make_mock_redis_client()

        with (
            patch("mangaba.vectorstores.redis.redis") as mock_redis,
            patch("mangaba.vectorstores.redis.REDIS_AVAILABLE", True),
            patch(
                "mangaba.vectorstores.redis._get_search_classes",
                side_effect=_mock_search_classes,
            ),
        ):
            mock_redis.Redis.from_url.return_value = mock_client

            from mangaba.vectorstores.redis import RedisVectorStore

            RedisVectorStore()

            call_args = mock_redis.Redis.from_url.call_args
            assert call_args[0][0] == "redis://localhost:6379"


@pytest.fixture
def redis_store():
    mock_client = _make_mock_redis_client()

    with (
        patch("mangaba.vectorstores.redis.redis") as mock_redis,
        patch("mangaba.vectorstores.redis.REDIS_AVAILABLE", True),
        patch(
            "mangaba.vectorstores.redis._get_search_classes",
            side_effect=_mock_search_classes,
        ),
    ):
        mock_redis.Redis.from_url.return_value = mock_client

        from mangaba.vectorstores.redis import RedisVectorStore

        store = RedisVectorStore(
            url="redis://localhost:6379", index_name="test_vectors", vector_dimensions=3
        )
        yield store, mock_client


class TestRedisVectorStoreAdd:
    def test_add_stores_documents(self, redis_store):
        store, mock_client = redis_store
        texts = ["hello world", "foo bar"]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        metadatas = [{"source": "test"}, {"source": "test2"}]

        ids = store.add(texts, embeddings, metadatas)

        assert len(ids) == 2
        assert all(len(eid) == 12 for eid in ids)
        assert mock_client.pipeline.called

    def test_add_without_metadatas(self, redis_store):
        store, mock_client = redis_store
        texts = ["hello"]
        embeddings = [[0.1, 0.2, 0.3]]

        ids = store.add(texts, embeddings)

        assert len(ids) == 1

    def test_add_generates_unique_ids(self, redis_store):
        store, _ = redis_store
        ids1 = store.add(["a"], [[0.1, 0.2, 0.3]])
        ids2 = store.add(["b"], [[0.4, 0.5, 0.6]])

        assert ids1[0] != ids2[0]


class TestRedisVectorStoreSearch:
    def test_search_returns_results(self, redis_store):
        store, mock_client = redis_store

        mock_results = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "mangaba:test_vectors:abc123"
        mock_doc.text = "hello world"
        mock_doc.metadata = json.dumps({"source": "test"})
        mock_doc.score = 0.2
        mock_results.docs = [mock_doc]

        mock_client.ft.return_value.search.return_value = mock_results

        results = store.search([0.1, 0.2, 0.3], top_k=3)

        assert len(results) == 1
        assert results[0]["content"] == "hello world"
        assert results[0]["score"] == pytest.approx(0.9, abs=0.01)
        assert results[0]["metadata"] == {"source": "test"}

    def test_search_converts_cosine_distance_to_similarity(self, redis_store):
        store, mock_client = redis_store

        mock_results = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "doc1"
        mock_doc.text = "test"
        mock_doc.metadata = "{}"
        mock_doc.score = 0.0
        mock_results.docs = [mock_doc]

        mock_client.ft.return_value.search.return_value = mock_results

        results = store.search([0.1, 0.2, 0.3])

        assert results[0]["score"] == pytest.approx(1.0, abs=0.01)

    def test_search_handles_empty_results(self, redis_store):
        store, mock_client = redis_store

        mock_results = MagicMock()
        mock_results.docs = []
        mock_client.ft.return_value.search.return_value = mock_results

        results = store.search([0.1, 0.2, 0.3])

        assert results == []

    def test_search_handles_invalid_metadata_json(self, redis_store):
        store, mock_client = redis_store

        mock_results = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "doc1"
        mock_doc.text = "test"
        mock_doc.metadata = "not valid json"
        mock_doc.score = 0.2
        mock_results.docs = [mock_doc]

        mock_client.ft.return_value.search.return_value = mock_results

        results = store.search([0.1, 0.2, 0.3])

        assert results[0]["metadata"] == {}


class TestRedisVectorStoreDelete:
    def test_delete_removes_documents(self, redis_store):
        store, mock_client = redis_store
        store.delete(["id1", "id2"])

        pipe = mock_client.pipeline.return_value
        assert pipe.delete.call_count == 2

    def test_delete_empty_list(self, redis_store):
        store, mock_client = redis_store
        store.delete([])

        pipe = mock_client.pipeline.return_value
        pipe.delete.assert_not_called()


class TestRedisVectorStoreClear:
    def test_clear_removes_all(self, redis_store):
        store, mock_client = redis_store
        mock_client.scan.return_value = (0, ["key1", "key2"])

        store.clear()

        mock_client.delete.assert_called_with("key1", "key2")

    def test_clear_handles_pagination(self, redis_store):
        store, mock_client = redis_store
        mock_client.scan.side_effect = [
            (1, ["key1"]),
            (0, ["key2"]),
        ]

        store.clear()

        assert mock_client.delete.call_count == 2


class TestRedisVectorStoreCount:
    def test_count_returns_total(self, redis_store):
        store, mock_client = redis_store
        mock_client.scan.return_value = (0, ["key1", "key2", "key3"])

        assert store.count == 3

    def test_count_handles_pagination(self, redis_store):
        store, mock_client = redis_store
        mock_client.scan.side_effect = [
            (1, ["key1", "key2"]),
            (0, ["key3"]),
        ]

        assert store.count == 3

    def test_count_empty_store(self, redis_store):
        store, mock_client = redis_store
        mock_client.scan.return_value = (0, [])

        assert store.count == 0


class TestRedisVectorStoreClose:
    def test_close_closes_connection(self, redis_store):
        store, mock_client = redis_store
        store.close()
        mock_client.close.assert_called_once()

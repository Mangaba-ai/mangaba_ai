"""Testes para InMemoryVectorStore"""

import pytest

pytestmark = pytest.mark.unit

from mangaba.vectorstores.in_memory import InMemoryVectorStore


@pytest.fixture
def store():
    return InMemoryVectorStore()


class TestInMemoryVectorStoreAdd:
    def test_add_single_document(self, store):
        ids = store.add(["hello"], [[0.1, 0.2, 0.3]])
        assert len(ids) == 1
        assert len(ids[0]) == 12

    def test_add_multiple_documents(self, store):
        ids = store.add(
            ["hello", "world"],
            [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            [{"a": 1}, {"b": 2}],
        )
        assert len(ids) == 2

    def test_add_without_metadatas(self, store):
        ids = store.add(["hello"], [[0.1, 0.2, 0.3]])
        assert len(ids) == 1

    def test_add_generates_unique_ids(self, store):
        ids1 = store.add(["a"], [[0.1]])
        ids2 = store.add(["b"], [[0.2]])
        assert ids1[0] != ids2[0]


class TestInMemoryVectorStoreSearch:
    def test_search_identical_vector(self, store):
        store.add(["hello"], [[0.1, 0.2, 0.3]])
        results = store.search([0.1, 0.2, 0.3], top_k=1)
        assert len(results) == 1
        assert results[0]["content"] == "hello"
        assert results[0]["score"] == pytest.approx(1.0, abs=0.001)

    def test_search_orthogonal_vector(self, store):
        store.add(["hello"], [[1.0, 0.0, 0.0]])
        results = store.search([0.0, 1.0, 0.0], top_k=1)
        assert results[0]["score"] == pytest.approx(0.0, abs=0.001)

    def test_search_top_k_limit(self, store):
        store.add(
            ["a", "b", "c"],
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        )
        results = store.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2

    def test_search_empty_store(self, store):
        results = store.search([0.1, 0.2, 0.3])
        assert results == []

    def test_search_returns_metadata(self, store):
        store.add(["hello"], [[0.1, 0.2, 0.3]], [{"source": "test"}])
        results = store.search([0.1, 0.2, 0.3])
        assert results[0]["metadata"] == {"source": "test"}


class TestInMemoryVectorStoreDelete:
    def test_delete_existing_id(self, store):
        ids = store.add(["hello"], [[0.1, 0.2, 0.3]])
        store.delete(ids)
        assert store.count == 0

    def test_delete_nonexistent_id(self, store):
        store.delete(["nonexistent"])
        assert store.count == 0

    def test_delete_partial(self, store):
        ids = store.add(["a", "b"], [[0.1, 0.2], [0.3, 0.4]])
        store.delete([ids[0]])
        assert store.count == 1


class TestInMemoryVectorStoreClear:
    def test_clear_removes_all(self, store):
        store.add(["a", "b"], [[0.1, 0.2], [0.3, 0.4]])
        store.clear()
        assert store.count == 0

    def test_clear_empty_store(self, store):
        store.clear()
        assert store.count == 0


class TestInMemoryVectorStoreCount:
    def test_count_zero(self, store):
        assert store.count == 0

    def test_count_after_add(self, store):
        store.add(["a", "b", "c"], [[0.1], [0.2], [0.3]])
        assert store.count == 3

    def test_count_after_delete(self, store):
        ids = store.add(["a", "b"], [[0.1], [0.2]])
        store.delete([ids[0]])
        assert store.count == 1

    def test_count_after_clear(self, store):
        store.add(["a"], [[0.1]])
        store.clear()
        assert store.count == 0

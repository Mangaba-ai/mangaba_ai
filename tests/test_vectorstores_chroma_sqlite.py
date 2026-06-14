import pytest
from mangaba.vectorstores import create_vectorstore
from mangaba.vectorstores.chroma_db import CHROMA_AVAILABLE

pytestmark = pytest.mark.unit


def chroma_only():
    return pytest.mark.skipif(not CHROMA_AVAILABLE, reason="chromadb not installed")


@pytest.fixture(
    params=[
        pytest.param("sqlite", id="sqlite"),
        pytest.param(
            "chroma",
            id="chroma",
            marks=pytest.mark.skipif(
                not CHROMA_AVAILABLE, reason="chromadb not installed"
            ),
        ),
    ]
)
def vector_store(request, tmp_path):
    if request.param == "sqlite":
        db_path = tmp_path / "test.db"
        store = create_vectorstore("sqlite", db_path=str(db_path))
    else:
        chroma_dir = tmp_path / "chroma_test"
        store = create_vectorstore("chroma", path=str(chroma_dir))

    yield store
    store.clear()


def test_add_and_count(vector_store):
    texts = ["Sistema de Detecção", "Logs de Firewall"]
    embeddings = [[0.1, 0.2, 0.3], [0.8, 0.9, 0.1]]

    ids = vector_store.add(texts, embeddings)

    assert len(ids) == 2
    assert vector_store.count == 2


def test_search_similarity(vector_store):
    texts = ["Acesso negado", "Acesso permitido"]
    embeddings = [[-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]]
    vector_store.add(texts, embeddings)

    query_vector = [0.9, 0.9, 0.9]
    results = vector_store.search(query_vector, top_k=1)

    assert len(results) == 1
    assert results[0]["content"] == "Acesso permitido"


def test_delete_item(vector_store):
    ids = vector_store.add(["Dado temporário"], [[0.5, 0.5, 0.5]])
    assert vector_store.count == 1

    vector_store.delete(ids)
    assert vector_store.count == 0


def test_metadata_persistence(vector_store):
    meta = {"severidade": "alta", "origem": "zeek"}
    vector_store.add(["Ataque detectado"], [[0.1, 0.1, 0.1]], metadatas=[meta])

    results = vector_store.search([0.1, 0.1, 0.1], top_k=1)
    assert results[0]["metadata"]["severidade"] == "alta"

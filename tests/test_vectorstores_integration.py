"""
Integration tests for vector stores against real Docker containers.

Prerequisites:
    docker run -d --name mangaba-redis -p 6379:6379 redis/redis-stack:latest
    docker run -d --name mangaba-postgres -e POSTGRES_PASSWORD=minhasenha -p 5432:5432 ankane/pgvector:latest

Run:
    pytest tests/test_vectorstores_integration.py -v -o "addopts=" --tb=short
"""

import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.slow]

REDIS_URL = os.getenv("MANGABA_REDIS_URL", "redis://localhost:6379")
POSTGRES_URL = os.getenv(
    "MANGABA_VECTORSTORE_URL",
    os.getenv(
        "DATABASE_URL", "postgresql://postgres:minhasenha@localhost:5432/mangaba"
    ),
)


def redis_available() -> bool:
    try:
        import redis

        client = redis.Redis.from_url(REDIS_URL)
        client.ping()
        client.close()
        return True
    except Exception:
        return False


def postgres_available() -> bool:
    try:
        import psycopg

        conn = psycopg.connect(POSTGRES_URL)
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture
def redis_store():
    if not redis_available():
        pytest.skip("Redis not available")

    from mangaba.vectorstores.redis import RedisVectorStore

    store = RedisVectorStore(
        url=REDIS_URL,
        index_name="integration_test",
        vector_dimensions=3,
    )
    store.clear()
    yield store
    store.clear()
    store.close()


@pytest.fixture
def postgres_store():
    if not postgres_available():
        pytest.skip("PostgreSQL not available")

    from mangaba.vectorstores.postgres import PostgresVectorStore

    store = PostgresVectorStore(
        url=POSTGRES_URL,
        table_name="integration_test",
        vector_dimensions=3,
    )
    store.clear()
    yield store
    store.clear()
    store.close()


class TestRedisIntegration:
    def test_full_lifecycle(self, redis_store):
        assert redis_store.count == 0

        ids = redis_store.add(
            texts=["hello world", "foo bar", "machine learning"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            metadatas=[{"source": "test1"}, {"source": "test2"}, {"source": "test3"}],
        )
        assert len(ids) == 3
        assert redis_store.count == 3

        results = redis_store.search([0.9, 0.1, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0]["content"] == "hello world"
        assert results[0]["score"] > results[1]["score"]

        redis_store.delete([ids[0]])
        assert redis_store.count == 2

        redis_store.clear()
        assert redis_store.count == 0


class TestPostgresIntegration:
    def test_full_lifecycle(self, postgres_store):
        assert postgres_store.count == 0

        ids = postgres_store.add(
            texts=["hello world", "foo bar", "machine learning"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            metadatas=[{"source": "test1"}, {"source": "test2"}, {"source": "test3"}],
        )
        assert len(ids) == 3
        assert postgres_store.count == 3

        results = postgres_store.search([0.9, 0.1, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0]["content"] == "hello world"
        assert results[0]["score"] > results[1]["score"]

        postgres_store.delete([ids[0]])
        assert postgres_store.count == 2

        postgres_store.clear()
        assert postgres_store.count == 0

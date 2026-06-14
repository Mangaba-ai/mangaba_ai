"""
Example: Using Redis and PostgreSQL vector stores with Mangaba AI.

Prerequisites:
    Redis:    docker run -d --name mangaba-redis -p 6379:6379 redis/redis-stack:latest
    Postgres: docker run -d --name mangaba-postgres -e POSTGRES_PASSWORD=minhasenha -p 5432:5432 ankane/pgvector:latest

Install:
    pip install mangaba[redis,postgres]
"""

import os
from dotenv import load_dotenv

load_dotenv()

from mangaba.vectorstores import create_vectorstore, get_supported_stores

print("=" * 60)
print("Supported vector stores:", get_supported_stores())
print("=" * 60)

# ── Example 1: Factory-based creation ──────────────────────────────────

print("\n1. Creating stores via factory")

inmemory = create_vectorstore("inmemory")
print(f"  InMemory store created (count={inmemory.count})")

redis_url = os.getenv("MANGABA_REDIS_URL", "redis://localhost:6379")
postgres_url = os.getenv("MANGABA_VECTORSTORE_URL", os.getenv("DATABASE_URL"))

if postgres_url:
    pg_store = create_vectorstore("postgres", url=postgres_url, vector_dimensions=3)
    print(f"  Postgres store created (count={pg_store.count})")

# ── Example 2: Direct Redis usage ──────────────────────────────────────

try:
    from mangaba.vectorstores.redis import RedisVectorStore

    print("\n2. Redis direct usage")

    redis_store = RedisVectorStore(
        url=redis_url,
        index_name="example_docs",
        vector_dimensions=3,
    )

    ids = redis_store.add(
        texts=["Redis is fast", "Vectors are cool"],
        embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        metadatas=[{"topic": "database"}, {"topic": "ml"}],
    )
    print(f"  Added {len(ids)} documents: {ids}")
    print(f"  Store count: {redis_store.count}")

    results = redis_store.search([0.9, 0.1, 0.0], top_k=1)
    print(f"  Search result: {results[0]['content']} (score={results[0]['score']:.3f})")

    redis_store.clear()
    print(f"  After clear: count={redis_store.count}")
    redis_store.close()

except Exception as e:
    print(f"\n2. Redis skipped (unavailable): {e}")

# ── Example 3: Direct PostgreSQL usage ─────────────────────────────────

if postgres_url:
    try:
        from mangaba.vectorstores.postgres import PostgresVectorStore

        print("\n3. PostgreSQL direct usage")

        pg_store = PostgresVectorStore(
            url=postgres_url,
            table_name="example_docs",
            vector_dimensions=3,
        )

        ids = pg_store.add(
            texts=["PostgreSQL is powerful", "pgvector enables similarity search"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            metadatas=[{"topic": "database"}, {"topic": "ml"}],
        )
        print(f"  Added {len(ids)} documents: {ids}")
        print(f"  Store count: {pg_store.count}")

        results = pg_store.search([0.9, 0.1, 0.0], top_k=1)
        print(
            f"  Search result: {results[0]['content']} (score={results[0]['score']:.3f})"
        )

        pg_store.clear()
        print(f"  After clear: count={pg_store.count}")
        pg_store.close()

    except Exception as e:
        print(f"\n3. PostgreSQL skipped (unavailable): {e}")

print("\nDone!")

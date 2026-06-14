"""Armazenamentos de vetores para Mangaba AI v3.0"""

from mangaba.vectorstores.base import BaseVectorStore
from mangaba.vectorstores.in_memory import InMemoryVectorStore
from mangaba.vectorstores.factory import (
    create_vectorstore,
    get_supported_stores,
    register_store,
)

__all__ = [
    "BaseVectorStore",
    "InMemoryVectorStore",
    "create_vectorstore",
    "get_supported_stores",
    "register_store",
]


def __getattr__(name: str):
    if name == "RedisVectorStore":
        from mangaba.vectorstores.redis import RedisVectorStore

        return RedisVectorStore
    if name == "PostgresVectorStore":
        from mangaba.vectorstores.postgres import PostgresVectorStore

        return PostgresVectorStore
    if name == "ChromaVectorStore":
        from mangaba.vectorstores.chroma_db import ChromaVectorStore

        return ChromaVectorStore
    if name == "SQLiteVectorStore":
        from mangaba.vectorstores.sqlite import SQLiteVectorStore

        return SQLiteVectorStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(__all__) + [
        "RedisVectorStore",
        "PostgresVectorStore",
        "ChromaVectorStore",
        "SQLiteVectorStore",
    ]

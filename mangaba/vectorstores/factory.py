"""
Funções de fábrica para criar armazenamentos de vetores em Mangaba AI v3.0
"""

from __future__ import annotations

from typing import Any, Dict, Type

from mangaba.vectorstores.base import BaseVectorStore
from mangaba.vectorstores.in_memory import InMemoryVectorStore

STORE_REGISTRY: Dict[str, Type[BaseVectorStore]] = {
    "inmemory": InMemoryVectorStore,
}


def register_store(name: str, cls: Type[BaseVectorStore]) -> None:
    """Registra uma classe de armazenamento de vetores sob um nome específico.

    Args:
        name: O nome para registrar o armazenamento.
        cls: A classe de armazenamento de vetores para registrar.
    """
    STORE_REGISTRY[name.lower()] = cls


def create_vectorstore(store_type: str, **kwargs: Any) -> BaseVectorStore:
    """Cria um armazenamento de vetores por nome de tipo.

    Args:
        store_type: Tipo de armazenamento ("inmemory", "redis", "postgres", "chroma", "sqlite").
        **kwargs: Argumentos adicionais passados para o construtor do armazenamento.

    Returns:
        Uma instância do armazenamento de vetores solicitado.

    Raises:
        ValueError: Se o tipo de armazenamento não for suportado.
        ImportError: Se as dependências necessárias estiverem faltando.

    Example:
        store = create_vectorstore("redis", url="redis://localhost:6379", vector_dimensions=1536)
        store = create_vectorstore("postgres", url="postgresql://user:pass@localhost/db")
        store = create_vectorstore("inmemory")
        store = create_vectorstore("chroma", path="./chroma_db", collection_name="my_collection")
        store = create_vectorstore("sqlite", db_path="mangaba_memory.db")
    """
    store_type = store_type.lower()

    if store_type not in STORE_REGISTRY:
        raise ValueError(
            f"Unsupported vector store type: {store_type!r}. "
            f"Supported types: {', '.join(sorted(STORE_REGISTRY.keys()))}"
        )

    return STORE_REGISTRY[store_type](**kwargs)


def get_supported_stores() -> tuple[str, ...]:
    """Retorna tupla de nomes de tipos de armazenamento de vetores suportados.

    Returns:
        Uma tupla de nomes de tipos de armazenamento suportados.
    """
    return tuple(sorted(STORE_REGISTRY.keys()))


def _try_register(name: str, module_path: str, class_name: str) -> None:
    """Registra preguiçosamente um armazenamento de vetores se suas dependências estiverem disponíveis.

    Args:
        name: O nome para registrar o armazenamento.
        module_path: O caminho do módulo para importar.
        class_name: O nome da classe para registrar.
    """
    try:
        module = __import__(module_path, fromlist=[class_name])
        cls = getattr(module, class_name)
        register_store(name, cls)
    except ImportError:
        pass


# Lazy register external stores
_try_register("redis", "mangaba.vectorstores.redis", "RedisVectorStore")
_try_register("postgres", "mangaba.vectorstores.postgres", "PostgresVectorStore")
_try_register("chroma", "mangaba.vectorstores.chroma_db", "ChromaVectorStore")
_try_register("sqlite", "mangaba.vectorstores.sqlite", "SQLiteVectorStore")

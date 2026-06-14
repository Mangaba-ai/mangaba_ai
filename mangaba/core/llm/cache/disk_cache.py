"""
Cache de resposta LLM baseado em disco usando SQLite.
"""

from .base import LLMCache
from typing import Optional
import sqlite3
import threading
import time


class DiskCache(LLMCache):
    """Cache persistente baseado em SQLite."""

    def __init__(
        self, path: str = ".mangaba_cache.db", default_ttl: Optional[int] = None
    ) -> None:
        """Inicializa o cache SQLite baseado em disco.

        Args:
            path: Caminho para o arquivo de banco de dados SQLite (padrão: ".mangaba_cache.db").
            default_ttl: Time-to-live padrão em segundos para todas as entradas. None significa
                sem expiração (padrão: None).

        Attributes:
            _path: Caminho para o arquivo de banco de dados SQLite.
            _default_ttl: TTL padrão para entradas de cache.
            _lock: Lock de threading para operações thread-safe.
        """
        self._path = path
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Inicializa o esquema do banco de dados SQLite.

        Cria a tabela de cache se ela não existir.
        """
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(key TEXT PRIMARY KEY, value TEXT, expires_at REAL)"
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        """Cria uma nova conexão SQLite.

        Returns:
            Um objeto sqlite3.Connection para o banco de dados.
        """
        return sqlite3.connect(self._path)

    def get(self, key: str) -> Optional[str]:
        """Recupera um valor do cache de disco.

        Entradas expiradas são automaticamente excluídas do banco de dados.

        Args:
            key: A chave de cache para procurar.

        Returns:
            O valor em cache se encontrado e não expirado, None caso contrário.
        """
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None
            value, expires_at = row
            if expires_at is not None and time.time() > expires_at:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None
            return value

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Armazena um valor no cache de disco.

        Args:
            key: A chave de cache para armazenar sob.
            value: O valor para cachear.
            ttl: Time-to-live em segundos. Usa default_ttl se None (padrão: None).
        """
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + actual_ttl if actual_ttl else None
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value, expires_at),
            )
            conn.commit()

    def invalidate(self, key: str) -> None:
        """Remove uma entrada específica do cache de disco.

        Args:
            key: A chave de cache para invalidar.
        """
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()

    def clear(self) -> None:
        """Remove todas as entradas do cache de disco."""
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()

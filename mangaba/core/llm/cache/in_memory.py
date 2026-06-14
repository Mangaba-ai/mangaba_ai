"""
Implementação de cache de resposta LLM em memória.
"""

from .base import LLMCache
from typing import Optional
from collections import OrderedDict
import threading
import time


class InMemoryCache(LLMCache):
    """Cache LRU em memória thread-safe com TTL opcional (segundos)."""

    def __init__(self, max_size: int = 256, default_ttl: Optional[int] = None) -> None:
        """Inicializa o cache LRU em memória.

        Args:
            max_size: Número máximo de entradas para armazenar. Entradas mais antigas são
                removidas quando este limite é excedido (padrão: 256).
            default_ttl: Time-to-live padrão em segundos para todas as entradas. None significa
                sem expiração (padrão: None).

        Attributes:
            _max_size: Número máximo de entradas no cache.
            _default_ttl: TTL padrão para entradas de cache.
            _cache: OrderedDict armazenando chave -> tuplas (value, expires_at).
            _lock: Lock de threading para operações thread-safe.
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[str, Optional[float]]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        """Recupera um valor do cache.

        Se a entrada existe e não está expirada, ela é movida para o final do
        OrderedDict para marcá-la como usada recentemente (comportamento LRU).

        Args:
            key: A chave de cache para procurar.

        Returns:
            O valor em cache se encontrado e não expirado, None caso contrário.
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Armazena um valor no cache.

        Se o cache estiver cheio, a entrada mais antiga é removida (comportamento LRU).
        Se a chave já existe, ela é atualizada e movida para o final.

        Args:
            key: A chave de cache para armazenar sob.
            value: O valor para cachear.
            ttl: Time-to-live em segundos. Usa default_ttl se None (padrão: None).
        """
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + actual_ttl if actual_ttl else None
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expires_at)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """Remove uma entrada específica do cache.

        Args:
            key: A chave de cache para invalidar.
        """
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Remove todas as entradas do cache."""
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        """Retorna o número de entradas atualmente no cache.

        Returns:
            O número de entradas em cache.
        """
        return len(self._cache)

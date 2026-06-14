"""
Módulo Base de Cache LLM

Este módulo define a classe base abstrata para implementações de cache de resposta LLM.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import hashlib
import json


class LLMCache(ABC):
    """Classe base abstrata para implementações de cache de resposta LLM."""

    @staticmethod
    def _cache_key(prompt: str, config: Dict[str, Any]) -> str:
        """Gera uma chave de cache determinística a partir do prompt e configuração.

        Args:
            prompt: A string do prompt de entrada.
            config: Dicionário de configuração incluindo modelo, temperatura, etc.

        Returns:
            Uma string de hash SHA256 que identifica exclusivamente a combinação prompt+config.
        """
        serialised = json.dumps(
            {"prompt": prompt, **config}, sort_keys=True, default=str
        )
        return hashlib.sha256(serialised.encode()).hexdigest()

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Recupera um valor em cache por chave.

        Args:
            key: A chave de cache para procurar.

        Returns:
            O valor em cache se encontrado e não expirado, None caso contrário.

        Raises:
            NotImplementedError: Este método deve ser implementado por subclasses.
        """
        raise NotImplementedError("get() must be implemented by subclass")

    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Armazena um valor no cache com um TTL opcional.

        Args:
            key: A chave de cache para armazenar sob.
            value: O valor para cachear.
            ttl: Time-to-live em segundos. None significa sem expiração.

        Raises:
            NotImplementedError: Este método deve ser implementado por subclasses.
        """
        raise NotImplementedError("set() must be implemented by subclass")

    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Remove uma entrada específica do cache.

        Args:
            key: A chave de cache para invalidar.

        Raises:
            NotImplementedError: Este método deve ser implementado por subclasses.
        """
        raise NotImplementedError("invalidate() must be implemented by subclass")

    @abstractmethod
    def clear(self) -> None:
        """Limpa todas as entradas do cache.

        Raises:
            NotImplementedError: Este método deve ser implementado por subclasses.
        """
        raise NotImplementedError("clear() must be implemented by subclass")

    # Conveniência ---------------------------------------------------------

    def get_or_none(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Obtém uma resposta em cache por prompt e configuração.

        Método de conveniência que gera a chave de cache a partir do prompt e config.

        Args:
            prompt: A string do prompt de entrada.
            config: Dicionário de configuração incluindo modelo, temperatura, etc.

        Returns:
            A resposta em cache se encontrada e não expirada, None caso contrário.
        """
        return self.get(self._cache_key(prompt, config))

    def store(
        self, prompt: str, config: Dict[str, Any], value: str, ttl: Optional[int] = None
    ) -> None:
        """Armazena uma resposta no cache por prompt e configuração.

        Método de conveniência que gera a chave de cache a partir do prompt e config.

        Args:
            prompt: A string do prompt de entrada.
            config: Dicionário de configuração incluindo modelo, temperatura, etc.
            value: O valor de resposta para cachear.
            ttl: Time-to-live em segundos. None significa sem expiração.
        """
        self.set(self._cache_key(prompt, config), value, ttl)
